"""
Sistema de memória afetiva para relacionamento evolutivo e inteligência emocional.
"""

import sqlite3
import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np

from config.settings import EVAConfig
from utils.logging_system import EVALogger

@dataclass
class AffectiveEntry:
    """Entrada na memória afetiva"""
    id: int
    session_id: str
    emotional_state: Dict[str, float]
    user_input: str
    eva_response: str
    timestamp: float
    emotional_intensity: float
    relationship_impact: float
    metadata: Dict[str, Any]

@dataclass
class RelationshipSummary:
    """Resumo do relacionamento com o usuário"""
    total_interactions: int
    avg_emotional_intensity: float
    dominant_emotions: Dict[str, float]
    relationship_quality: float
    trust_level: float
    communication_style: str
    preferences: Dict[str, Any]
    last_updated: float

class AffectiveMemory:
    """
    Sistema de memória afetiva que armazena e analisa aspectos emocionais
    das interações para construir um relacionamento evolutivo.
    """
    
    def __init__(self, config: EVAConfig):
        self.config = config
        self.logger = EVALogger.get_logger("AffectiveMemory")
        
        # Caminhos de arquivos
        self.db_path = config.memory.affective_db_path
        
        # Componentes
        self.db_connection: Optional[sqlite3.Connection] = None
        
        # Cache de relacionamento
        self.relationship_cache: Dict[str, RelationshipSummary] = {}
        self.cache_expiry = 3600  # 1 hora
        
        # Estatísticas
        self.total_entries = 0
        self.reflection_count = 0
        
    async def initialize(self):
        """Inicializa o sistema de memória afetiva"""
        try:
            self.logger.info("Inicializando memória afetiva...")
            
            # Criar diretórios necessários
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Inicializar banco de dados
            await self._initialize_database()
            
            # Carregar estatísticas
            await self._load_stats()
            
            self.logger.info(f"Memória afetiva inicializada ({self.total_entries} entradas)")
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização da memória afetiva: {e}")
            raise
    
    async def _initialize_database(self):
        """Inicializa o banco de dados SQLite"""
        self.db_connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db_connection.row_factory = sqlite3.Row
        
        cursor = self.db_connection.cursor()
        
        # Tabela principal de entradas afetivas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS affective_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                emotional_state TEXT NOT NULL,
                user_input TEXT NOT NULL,
                eva_response TEXT NOT NULL,
                timestamp REAL NOT NULL,
                emotional_intensity REAL NOT NULL,
                relationship_impact REAL NOT NULL,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de resumos de relacionamento
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationship_summaries (
                session_id TEXT PRIMARY KEY,
                total_interactions INTEGER NOT NULL,
                avg_emotional_intensity REAL NOT NULL,
                dominant_emotions TEXT NOT NULL,
                relationship_quality REAL NOT NULL,
                trust_level REAL NOT NULL,
                communication_style TEXT NOT NULL,
                preferences TEXT NOT NULL,
                last_updated REAL NOT NULL
            )
        """)
        
        # Tabela de reflexões
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                reflection_text TEXT NOT NULL,
                insights TEXT,
                timestamp REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Criar índices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_affective_session ON affective_entries(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_affective_timestamp ON affective_entries(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reflections_session ON reflections(session_id)")
        
        self.db_connection.commit()
        self.logger.debug("Banco de dados de memória afetiva inicializado")
    
    async def _load_stats(self):
        """Carrega estatísticas da memória"""
        try:
            cursor = self.db_connection.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM affective_entries")
            self.total_entries = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM reflections")
            self.reflection_count = cursor.fetchone()[0]
            
        except Exception as e:
            self.logger.warning(f"Erro ao carregar estatísticas: {e}")
            self.total_entries = 0
            self.reflection_count = 0
    
    async def store_interaction(
        self,
        session_id: str,
        emotional_state: Dict[str, float],
        user_input: str,
        eva_response: str,
        timestamp: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Armazena uma interação com análise afetiva.
        
        Returns:
            ID da entrada armazenada
        """
        try:
            # Calcular intensidade emocional
            emotional_intensity = self._calculate_emotional_intensity(emotional_state)
            
            # Calcular impacto no relacionamento
            relationship_impact = await self._calculate_relationship_impact(
                session_id, emotional_state, user_input, eva_response
            )
            
            # Preparar dados
            emotional_state_json = json.dumps(emotional_state)
            metadata_json = json.dumps(metadata or {})
            
            # Inserir no banco de dados
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO affective_entries 
                (session_id, emotional_state, user_input, eva_response, 
                 timestamp, emotional_intensity, relationship_impact, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, emotional_state_json, user_input, eva_response,
                  timestamp, emotional_intensity, relationship_impact, metadata_json))
            
            entry_id = cursor.lastrowid
            self.db_connection.commit()
            
            self.total_entries += 1
            
            # Atualizar resumo do relacionamento
            await self._update_relationship_summary(session_id)
            
            self.logger.debug(f"Interação afetiva armazenada (ID: {entry_id}, "
                            f"Intensidade: {emotional_intensity:.2f}, "
                            f"Impacto: {relationship_impact:.2f})")
            
            # Verificar limite de entradas
            if self.total_entries > self.config.memory.max_affective_entries:
                await self._cleanup_old_entries()
            
            return entry_id
            
        except Exception as e:
            self.logger.error(f"Erro ao armazenar interação afetiva: {e}")
            raise
    
    def _calculate_emotional_intensity(self, emotional_state: Dict[str, float]) -> float:
        """Calcula a intensidade emocional geral"""
        if not emotional_state:
            return 0.0
        
        # Usar a soma ponderada das emoções
        weights = {
            'alegria': 1.0,
            'tristeza': 1.2,
            'raiva': 1.5,
            'medo': 1.3,
            'surpresa': 0.8,
            'confianca': 0.9,
            'energia': 0.7,
            'calma': 0.5
        }
        
        total_intensity = 0.0
        total_weight = 0.0
        
        for emotion, value in emotional_state.items():
            weight = weights.get(emotion, 1.0)
            total_intensity += value * weight
            total_weight += weight
        
        return total_intensity / total_weight if total_weight > 0 else 0.0
    
    async def _calculate_relationship_impact(
        self,
        session_id: str,
        emotional_state: Dict[str, float],
        user_input: str,
        eva_response: str
    ) -> float:
        """Calcula o impacto da interação no relacionamento"""
        
        impact = 0.0
        
        # Impacto baseado em emoções positivas vs negativas
        positive_emotions = ['alegria', 'confianca', 'energia', 'calma']
        negative_emotions = ['tristeza', 'raiva', 'medo']
        
        positive_score = sum(emotional_state.get(emotion, 0) for emotion in positive_emotions)
        negative_score = sum(emotional_state.get(emotion, 0) for emotion in negative_emotions)
        
        impact += (positive_score - negative_score) * 0.5
        
        # Impacto baseado no comprimento e qualidade da resposta
        response_quality = min(len(eva_response.split()) / 50, 1.0)  # Normalizar
        impact += response_quality * 0.2
        
        # Impacto baseado em palavras-chave positivas/negativas na entrada
        positive_keywords = ['obrigado', 'gosto', 'amo', 'perfeito', 'excelente', 'maravilhoso']
        negative_keywords = ['não gosto', 'ruim', 'terrível', 'odeio', 'péssimo']
        
        user_input_lower = user_input.lower()
        for keyword in positive_keywords:
            if keyword in user_input_lower:
                impact += 0.3
        
        for keyword in negative_keywords:
            if keyword in user_input_lower:
                impact -= 0.3
        
        # Normalizar entre -1 e 1
        return max(-1.0, min(1.0, impact))
    
    async def _update_relationship_summary(self, session_id: str):
        """Atualiza o resumo do relacionamento para uma sessão"""
        try:
            # Recuperar todas as interações da sessão
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT emotional_state, emotional_intensity, relationship_impact, timestamp
                FROM affective_entries 
                WHERE session_id = ?
                ORDER BY timestamp
            """, (session_id,))
            
            rows = cursor.fetchall()
            
            if not rows:
                return
            
            # Calcular métricas do relacionamento
            total_interactions = len(rows)
            avg_emotional_intensity = sum(row['emotional_intensity'] for row in rows) / total_interactions
            avg_relationship_impact = sum(row['relationship_impact'] for row in rows) / total_interactions
            
            # Analisar emoções dominantes
            emotion_totals = {}
            for row in rows:
                emotional_state = json.loads(row['emotional_state'])
                for emotion, value in emotional_state.items():
                    emotion_totals[emotion] = emotion_totals.get(emotion, 0) + value
            
            # Normalizar emoções dominantes
            if emotion_totals:
                max_emotion_total = max(emotion_totals.values())
                dominant_emotions = {
                    emotion: total / max_emotion_total 
                    for emotion, total in emotion_totals.items()
                }
            else:
                dominant_emotions = {}
            
            # Calcular qualidade do relacionamento
            relationship_quality = self._calculate_relationship_quality(
                avg_relationship_impact, avg_emotional_intensity, total_interactions
            )
            
            # Calcular nível de confiança
            trust_level = self._calculate_trust_level(rows)
            
            # Determinar estilo de comunicação
            communication_style = self._determine_communication_style(rows)
            
            # Extrair preferências (implementação simplificada)
            preferences = self._extract_preferences(rows)
            
            # Criar resumo
            summary = RelationshipSummary(
                total_interactions=total_interactions,
                avg_emotional_intensity=avg_emotional_intensity,
                dominant_emotions=dominant_emotions,
                relationship_quality=relationship_quality,
                trust_level=trust_level,
                communication_style=communication_style,
                preferences=preferences,
                last_updated=time.time()
            )
            
            # Salvar no banco de dados
            await self._save_relationship_summary(session_id, summary)
            
            # Atualizar cache
            self.relationship_cache[session_id] = summary
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar resumo do relacionamento: {e}")
    
    def _calculate_relationship_quality(
        self, 
        avg_impact: float, 
        avg_intensity: float, 
        total_interactions: int
    ) -> float:
        """Calcula a qualidade geral do relacionamento"""
        
        # Base na média de impacto (normalizada para 0-1)
        impact_score = (avg_impact + 1) / 2
        
        # Bônus por consistência (mais interações = mais estável)
        consistency_bonus = min(total_interactions / 100, 0.2)
        
        # Penalidade por intensidade emocional muito alta (instabilidade)
        intensity_penalty = max(0, (avg_intensity - 0.7) * 0.3)
        
        quality = impact_score + consistency_bonus - intensity_penalty
        
        return max(0.0, min(1.0, quality))
    
    def _calculate_trust_level(self, interaction_rows: List) -> float:
        """Calcula o nível de confiança baseado no histórico"""
        
        if not interaction_rows:
            return 0.5
        
        # Analisar tendência dos impactos no relacionamento
        impacts = [row['relationship_impact'] for row in interaction_rows]
        
        # Calcular tendência (últimas interações têm mais peso)
        weighted_impacts = []
        for i, impact in enumerate(impacts):
            weight = (i + 1) / len(impacts)  # Peso crescente
            weighted_impacts.append(impact * weight)
        
        avg_weighted_impact = sum(weighted_impacts) / len(weighted_impacts)
        
        # Normalizar para 0-1
        trust_level = (avg_weighted_impact + 1) / 2
        
        # Bônus por estabilidade (baixa variância)
        if len(impacts) > 1:
            variance = np.var(impacts)
            stability_bonus = max(0, (0.5 - variance) * 0.2)
            trust_level += stability_bonus
        
        return max(0.0, min(1.0, trust_level))
    
    def _determine_communication_style(self, interaction_rows: List) -> str:
        """Determina o estilo de comunicação preferido"""
        
        if not interaction_rows:
            return "neutral"
        
        # Analisar intensidade emocional média
        avg_intensity = sum(row['emotional_intensity'] for row in interaction_rows) / len(interaction_rows)
        
        # Analisar impacto médio
        avg_impact = sum(row['relationship_impact'] for row in interaction_rows) / len(interaction_rows)
        
        if avg_intensity > 0.7 and avg_impact > 0.3:
            return "expressive"
        elif avg_intensity < 0.3 and avg_impact > 0:
            return "calm"
        elif avg_impact > 0.5:
            return "supportive"
        elif avg_impact < -0.2:
            return "cautious"
        else:
            return "balanced"
    
    def _extract_preferences(self, interaction_rows: List) -> Dict[str, Any]:
        """Extrai preferências do usuário (implementação simplificada)"""
        
        preferences = {
            'prefers_detailed_responses': False,
            'prefers_emotional_support': False,
            'prefers_creative_content': False,
            'prefers_analytical_approach': False
        }
        
        # Análise baseada em padrões simples
        # (Em uma implementação completa, isso seria mais sofisticado)
        
        if len(interaction_rows) > 5:
            avg_intensity = sum(row['emotional_intensity'] for row in interaction_rows) / len(interaction_rows)
            
            if avg_intensity > 0.6:
                preferences['prefers_emotional_support'] = True
            
            # Mais análises poderiam ser adicionadas aqui
        
        return preferences
    
    async def _save_relationship_summary(self, session_id: str, summary: RelationshipSummary):
        """Salva resumo do relacionamento no banco de dados"""
        try:
            cursor = self.db_connection.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO relationship_summaries
                (session_id, total_interactions, avg_emotional_intensity, 
                 dominant_emotions, relationship_quality, trust_level, 
                 communication_style, preferences, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                summary.total_interactions,
                summary.avg_emotional_intensity,
                json.dumps(summary.dominant_emotions),
                summary.relationship_quality,
                summary.trust_level,
                summary.communication_style,
                json.dumps(summary.preferences),
                summary.last_updated
            ))
            
            self.db_connection.commit()
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar resumo do relacionamento: {e}")
    
    async def get_relationship_summary(self, session_id: str) -> Optional[RelationshipSummary]:
        """Recupera resumo do relacionamento para uma sessão"""
        try:
            # Verificar cache primeiro
            if session_id in self.relationship_cache:
                cached_summary = self.relationship_cache[session_id]
                if time.time() - cached_summary.last_updated < self.cache_expiry:
                    return cached_summary
            
            # Buscar no banco de dados
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT * FROM relationship_summaries WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            summary = RelationshipSummary(
                total_interactions=row['total_interactions'],
                avg_emotional_intensity=row['avg_emotional_intensity'],
                dominant_emotions=json.loads(row['dominant_emotions']),
                relationship_quality=row['relationship_quality'],
                trust_level=row['trust_level'],
                communication_style=row['communication_style'],
                preferences=json.loads(row['preferences']),
                last_updated=row['last_updated']
            )
            
            # Atualizar cache
            self.relationship_cache[session_id] = summary
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar resumo do relacionamento: {e}")
            return None
    
    async def get_relevant_memories(
        self,
        emotional_state: Dict[str, float],
        user_input: str,
        limit: int = 3
    ) -> List[str]:
        """Recupera memórias afetivas relevantes para o contexto atual"""
        try:
            # Calcular intensidade emocional atual
            current_intensity = self._calculate_emotional_intensity(emotional_state)
            
            # Buscar entradas com intensidade emocional similar
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT user_input, eva_response, emotional_intensity, relationship_impact
                FROM affective_entries
                WHERE ABS(emotional_intensity - ?) < 0.3
                ORDER BY timestamp DESC
                LIMIT ?
            """, (current_intensity, limit * 2))
            
            rows = cursor.fetchall()
            
            # Filtrar e formatar memórias relevantes
            memories = []
            for row in rows:
                if len(memories) >= limit:
                    break
                
                # Criar descrição da memória
                memory_desc = f"Interação anterior (intensidade: {row['emotional_intensity']:.2f}): "
                memory_desc += f"'{row['user_input'][:100]}...' -> "
                memory_desc += f"'{row['eva_response'][:100]}...'"
                
                memories.append(memory_desc)
            
            return memories
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar memórias relevantes: {e}")
            return []
    
    async def store_reflection(
        self,
        reflection_text: str,
        timestamp: float,
        session_id: str,
        insights: Optional[Dict[str, Any]] = None
    ) -> int:
        """Armazena uma reflexão pós-interação"""
        try:
            insights_json = json.dumps(insights or {})
            
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO reflections (session_id, reflection_text, insights, timestamp)
                VALUES (?, ?, ?, ?)
            """, (session_id, reflection_text, insights_json, timestamp))
            
            reflection_id = cursor.lastrowid
            self.db_connection.commit()
            
            self.reflection_count += 1
            
            self.logger.debug(f"Reflexão armazenada (ID: {reflection_id})")
            
            return reflection_id
            
        except Exception as e:
            self.logger.error(f"Erro ao armazenar reflexão: {e}")
            raise
    
    async def get_recent_reflections(self, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Recupera reflexões recentes de uma sessão"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT reflection_text, insights, timestamp
                FROM reflections
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, limit))
            
            rows = cursor.fetchall()
            
            reflections = []
            for row in rows:
                reflections.append({
                    'text': row['reflection_text'],
                    'insights': json.loads(row['insights']) if row['insights'] else {},
                    'timestamp': row['timestamp']
                })
            
            return reflections
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar reflexões: {e}")
            return []
    
    async def _cleanup_old_entries(self):
        """Remove entradas antigas quando o limite é excedido"""
        try:
            entries_to_remove = self.total_entries - self.config.memory.max_affective_entries
            
            if entries_to_remove > 0:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    DELETE FROM affective_entries 
                    WHERE id IN (
                        SELECT id FROM affective_entries 
                        ORDER BY timestamp ASC 
                        LIMIT ?
                    )
                """, (entries_to_remove,))
                
                self.db_connection.commit()
                self.total_entries = self.config.memory.max_affective_entries
                
                self.logger.info(f"Removidas {entries_to_remove} entradas afetivas antigas")
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza de entradas antigas: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da memória afetiva"""
        try:
            cursor = self.db_connection.cursor()
            
            # Estatísticas básicas
            cursor.execute("SELECT COUNT(*) FROM affective_entries")
            total_entries = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT session_id) FROM affective_entries")
            unique_sessions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM reflections")
            total_reflections = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT AVG(emotional_intensity), AVG(relationship_impact)
                FROM affective_entries
            """)
            averages = cursor.fetchone()
            
            stats = {
                'total_entries': total_entries,
                'unique_sessions': unique_sessions,
                'total_reflections': total_reflections,
                'avg_emotional_intensity': averages[0] if averages[0] else 0,
                'avg_relationship_impact': averages[1] if averages[1] else 0,
                'cached_summaries': len(self.relationship_cache)
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return {'error': str(e)}
    
    async def close(self):
        """Fecha conexões e salva estado"""
        try:
            # Fechar conexão do banco
            if self.db_connection:
                self.db_connection.close()
            
            self.logger.info("Memória afetiva fechada")
            
        except Exception as e:
            self.logger.error(f"Erro ao fechar memória afetiva: {e}")
