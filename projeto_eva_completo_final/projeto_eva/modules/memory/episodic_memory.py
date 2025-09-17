"""
Sistema de memória episódica para armazenar histórico de conversas e eventos.
"""

import sqlite3
import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

from config.settings import EVAConfig
from utils.logging_system import EVALogger

@dataclass
class EpisodicEntry:
    """Entrada na memória episódica"""
    id: int
    session_id: str
    user_input: str
    eva_response: str
    timestamp: float
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None

class EpisodicMemory:
    """
    Sistema de memória episódica que armazena e recupera histórico de conversas.
    
    Utiliza SQLite para persistência e FAISS para busca semântica eficiente.
    """
    
    def __init__(self, config: EVAConfig):
        self.config = config
        self.logger = EVALogger.get_logger("EpisodicMemory")
        
        # Caminhos de arquivos
        self.db_path = config.memory.episodic_db_path
        self.vector_db_path = config.memory.vector_db_path
        
        # Componentes
        self.db_connection: Optional[sqlite3.Connection] = None
        self.embedding_model: Optional[SentenceTransformer] = None
        self.vector_index: Optional[faiss.IndexFlatIP] = None
        
        # Cache
        self.embedding_cache: Dict[str, np.ndarray] = {}
        self.max_cache_size = 1000
        
        # Estatísticas
        self.total_entries = 0
        self.search_count = 0
        
    async def initialize(self):
        """Inicializa o sistema de memória episódica"""
        try:
            self.logger.info("Inicializando memória episódica...")
            
            # Criar diretórios necessários
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            Path(self.vector_db_path).mkdir(parents=True, exist_ok=True)
            
            # Inicializar banco de dados SQLite
            await self._initialize_database()
            
            # Carregar modelo de embeddings
            await self._load_embedding_model()
            
            # Inicializar índice vetorial
            await self._initialize_vector_index()
            
            # Carregar estatísticas
            await self._load_stats()
            
            self.logger.info(f"Memória episódica inicializada ({self.total_entries} entradas)")
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização da memória episódica: {e}")
            raise
    
    async def _initialize_database(self):
        """Inicializa o banco de dados SQLite"""
        self.db_connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db_connection.row_factory = sqlite3.Row
        
        # Criar tabelas
        cursor = self.db_connection.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodic_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_input TEXT NOT NULL,
                eva_response TEXT NOT NULL,
                timestamp REAL NOT NULL,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_stats (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Criar índices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON episodic_entries(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON episodic_entries(timestamp)")
        
        self.db_connection.commit()
        self.logger.debug("Banco de dados SQLite inicializado")
    
    async def _load_embedding_model(self):
        """Carrega o modelo de embeddings"""
        try:
            model_name = self.config.memory.embedding_model
            self.logger.info(f"Carregando modelo de embeddings: {model_name}")
            
            # Executar em thread separada para não bloquear
            loop = asyncio.get_event_loop()
            self.embedding_model = await loop.run_in_executor(
                None, SentenceTransformer, model_name
            )
            
            self.logger.debug("Modelo de embeddings carregado")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo de embeddings: {e}")
            raise
    
    async def _initialize_vector_index(self):
        """Inicializa o índice vetorial FAISS"""
        try:
            # Dimensão dos embeddings (384 para all-MiniLM-L6-v2)
            embedding_dim = 384
            
            # Criar índice FAISS (Inner Product para similaridade de cosseno)
            self.vector_index = faiss.IndexFlatIP(embedding_dim)
            
            # Tentar carregar índice existente
            index_file = Path(self.vector_db_path) / "episodic_index.faiss"
            if index_file.exists():
                self.vector_index = faiss.read_index(str(index_file))
                self.logger.debug(f"Índice vetorial carregado ({self.vector_index.ntotal} vetores)")
            else:
                self.logger.debug("Novo índice vetorial criado")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar índice vetorial: {e}")
            raise
    
    async def _load_stats(self):
        """Carrega estatísticas da memória"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM episodic_entries")
            self.total_entries = cursor.fetchone()[0]
            
        except Exception as e:
            self.logger.warning(f"Erro ao carregar estatísticas: {e}")
            self.total_entries = 0
    
    async def store_interaction(
        self,
        session_id: str,
        user_input: str,
        eva_response: str,
        timestamp: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Armazena uma interação na memória episódica.
        
        Returns:
            ID da entrada armazenada
        """
        try:
            # Preparar dados
            metadata_json = json.dumps(metadata or {})
            
            # Inserir no banco de dados
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO episodic_entries 
                (session_id, user_input, eva_response, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, user_input, eva_response, timestamp, metadata_json))
            
            entry_id = cursor.lastrowid
            self.db_connection.commit()
            
            # Gerar embedding e adicionar ao índice vetorial
            await self._add_to_vector_index(entry_id, user_input, eva_response)
            
            self.total_entries += 1
            
            self.logger.debug(f"Interação armazenada (ID: {entry_id})")
            
            # Verificar limite de entradas
            if self.total_entries > self.config.memory.max_episodic_entries:
                await self._cleanup_old_entries()
            
            return entry_id
            
        except Exception as e:
            self.logger.error(f"Erro ao armazenar interação: {e}")
            raise
    
    async def _add_to_vector_index(self, entry_id: int, user_input: str, eva_response: str):
        """Adiciona entrada ao índice vetorial"""
        try:
            # Combinar entrada do usuário e resposta para embedding
            combined_text = f"{user_input} {eva_response}"
            
            # Gerar embedding
            embedding = await self._get_embedding(combined_text)
            
            # Normalizar para similaridade de cosseno
            embedding = embedding / np.linalg.norm(embedding)
            
            # Adicionar ao índice
            self.vector_index.add(embedding.reshape(1, -1))
            
            # Salvar índice periodicamente
            if self.vector_index.ntotal % 100 == 0:
                await self._save_vector_index()
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar ao índice vetorial: {e}")
    
    async def _get_embedding(self, text: str) -> np.ndarray:
        """Gera embedding para um texto"""
        # Verificar cache
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        
        # Gerar embedding
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, self.embedding_model.encode, text
        )
        
        # Adicionar ao cache
        if len(self.embedding_cache) < self.max_cache_size:
            self.embedding_cache[text] = embedding
        
        return embedding
    
    async def search_similar(
        self, 
        query: str, 
        limit: int = 5,
        min_similarity: float = 0.3
    ) -> List[EpisodicEntry]:
        """
        Busca entradas similares à query.
        
        Args:
            query: Texto de busca
            limit: Número máximo de resultados
            min_similarity: Similaridade mínima (0-1)
            
        Returns:
            Lista de entradas similares ordenadas por relevância
        """
        try:
            if self.vector_index.ntotal == 0:
                return []
            
            # Gerar embedding da query
            query_embedding = await self._get_embedding(query)
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            
            # Buscar no índice vetorial
            similarities, indices = self.vector_index.search(
                query_embedding.reshape(1, -1), 
                min(limit * 2, self.vector_index.ntotal)  # Buscar mais para filtrar
            )
            
            # Filtrar por similaridade mínima
            valid_results = [
                (idx, sim) for idx, sim in zip(indices[0], similarities[0])
                if sim >= min_similarity and idx != -1
            ]
            
            # Recuperar entradas do banco de dados
            entries = []
            for idx, similarity in valid_results[:limit]:
                entry = await self._get_entry_by_index(idx)
                if entry:
                    entries.append(entry)
            
            self.search_count += 1
            self.logger.debug(f"Busca realizada: {len(entries)} resultados para '{query[:50]}...'")
            
            return entries
            
        except Exception as e:
            self.logger.error(f"Erro na busca similar: {e}")
            return []
    
    async def _get_entry_by_index(self, index: int) -> Optional[EpisodicEntry]:
        """Recupera entrada pelo índice vetorial"""
        try:
            # O índice corresponde à ordem de inserção (entry_id)
            entry_id = index + 1  # IDs começam em 1
            
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT id, session_id, user_input, eva_response, timestamp, metadata
                FROM episodic_entries WHERE id = ?
            """, (entry_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            metadata = json.loads(row['metadata']) if row['metadata'] else {}
            
            return EpisodicEntry(
                id=row['id'],
                session_id=row['session_id'],
                user_input=row['user_input'],
                eva_response=row['eva_response'],
                timestamp=row['timestamp'],
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar entrada por índice: {e}")
            return None
    
    async def get_session_history(
        self, 
        session_id: str, 
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Recupera histórico de uma sessão específica.
        
        Returns:
            Lista de dicionários com 'user' e 'eva' keys
        """
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT user_input, eva_response, timestamp
                FROM episodic_entries 
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, limit))
            
            rows = cursor.fetchall()
            
            # Converter para formato esperado (ordem cronológica)
            history = []
            for row in reversed(rows):
                history.append({
                    'user': row['user_input'],
                    'eva': row['eva_response'],
                    'timestamp': row['timestamp']
                })
            
            return history
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar histórico da sessão: {e}")
            return []
    
    async def search_by_category(
        self, 
        category: str, 
        limit: int = 5
    ) -> List[EpisodicEntry]:
        """Busca entradas por categoria nos metadados"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT id, session_id, user_input, eva_response, timestamp, metadata
                FROM episodic_entries 
                WHERE metadata LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f'%"{category}"%', limit))
            
            rows = cursor.fetchall()
            entries = []
            
            for row in rows:
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                
                entry = EpisodicEntry(
                    id=row['id'],
                    session_id=row['session_id'],
                    user_input=row['user_input'],
                    eva_response=row['eva_response'],
                    timestamp=row['timestamp'],
                    metadata=metadata
                )
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            self.logger.error(f"Erro na busca por categoria: {e}")
            return []
    
    async def get_recent_entries(self, limit: int = 10) -> List[EpisodicEntry]:
        """Recupera entradas mais recentes"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT id, session_id, user_input, eva_response, timestamp, metadata
                FROM episodic_entries 
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            entries = []
            
            for row in rows:
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                
                entry = EpisodicEntry(
                    id=row['id'],
                    session_id=row['session_id'],
                    user_input=row['user_input'],
                    eva_response=row['eva_response'],
                    timestamp=row['timestamp'],
                    metadata=metadata
                )
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            self.logger.error(f"Erro ao recuperar entradas recentes: {e}")
            return []
    
    async def _cleanup_old_entries(self):
        """Remove entradas antigas quando o limite é excedido"""
        try:
            entries_to_remove = self.total_entries - self.config.memory.max_episodic_entries
            
            if entries_to_remove > 0:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    DELETE FROM episodic_entries 
                    WHERE id IN (
                        SELECT id FROM episodic_entries 
                        ORDER BY timestamp ASC 
                        LIMIT ?
                    )
                """, (entries_to_remove,))
                
                self.db_connection.commit()
                self.total_entries = self.config.memory.max_episodic_entries
                
                self.logger.info(f"Removidas {entries_to_remove} entradas antigas")
                
                # Reconstruir índice vetorial
                await self._rebuild_vector_index()
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza de entradas antigas: {e}")
    
    async def _rebuild_vector_index(self):
        """Reconstrói o índice vetorial após limpeza"""
        try:
            self.logger.info("Reconstruindo índice vetorial...")
            
            # Criar novo índice
            embedding_dim = 384
            self.vector_index = faiss.IndexFlatIP(embedding_dim)
            
            # Recuperar todas as entradas restantes
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT id, user_input, eva_response
                FROM episodic_entries 
                ORDER BY id
            """)
            
            rows = cursor.fetchall()
            
            # Adicionar ao novo índice
            for row in rows:
                combined_text = f"{row['user_input']} {row['eva_response']}"
                embedding = await self._get_embedding(combined_text)
                embedding = embedding / np.linalg.norm(embedding)
                self.vector_index.add(embedding.reshape(1, -1))
            
            # Salvar índice reconstruído
            await self._save_vector_index()
            
            self.logger.info("Índice vetorial reconstruído")
            
        except Exception as e:
            self.logger.error(f"Erro na reconstrução do índice vetorial: {e}")
    
    async def _save_vector_index(self):
        """Salva o índice vetorial em disco"""
        try:
            index_file = Path(self.vector_db_path) / "episodic_index.faiss"
            faiss.write_index(self.vector_index, str(index_file))
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar índice vetorial: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da memória episódica"""
        try:
            cursor = self.db_connection.cursor()
            
            # Estatísticas básicas
            cursor.execute("SELECT COUNT(*) FROM episodic_entries")
            total_entries = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT session_id) FROM episodic_entries")
            unique_sessions = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT MIN(timestamp), MAX(timestamp) 
                FROM episodic_entries
            """)
            time_range = cursor.fetchone()
            
            stats = {
                'total_entries': total_entries,
                'unique_sessions': unique_sessions,
                'search_count': self.search_count,
                'vector_index_size': self.vector_index.ntotal if self.vector_index else 0,
                'cache_size': len(self.embedding_cache),
                'earliest_entry': time_range[0] if time_range[0] else None,
                'latest_entry': time_range[1] if time_range[1] else None
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return {'error': str(e)}
    
    async def close(self):
        """Fecha conexões e salva estado"""
        try:
            # Salvar índice vetorial
            if self.vector_index:
                await self._save_vector_index()
            
            # Fechar conexão do banco
            if self.db_connection:
                self.db_connection.close()
            
            self.logger.info("Memória episódica fechada")
            
        except Exception as e:
            self.logger.error(f"Erro ao fechar memória episódica: {e}")
