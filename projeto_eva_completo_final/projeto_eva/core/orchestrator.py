"""
Orquestrador central do sistema EVA.
Coordena todos os componentes e gerencia o fluxo principal de conversação.
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from core.model_manager import ModelManager
from core.consciousness import ConsciousnessSystem
from core.attention_system import AttentionSystem
from modules.memory.episodic_memory import EpisodicMemory
from modules.memory.affective_memory import AffectiveMemory
from config.settings import EVAConfig
from config.prompts import REFLECTION_PROMPT
from utils.logging_system import EVALogger, ConversationLogger, PerformanceLogger

class ConversationState(Enum):
    """Estados possíveis da conversa"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    REFLECTING = "reflecting"

@dataclass
class ConversationContext:
    """Contexto de uma conversa"""
    user_input: str
    conversation_history: List[Dict[str, str]]
    emotional_state: Dict[str, float]
    active_modules: List[str]
    session_id: str
    timestamp: float

class EVAOrchestrator:
    """
    Orquestrador central do sistema EVA.
    
    Gerencia a coordenação entre todos os componentes:
    - Gerenciamento de modelos
    - Sistema de consciência distribuída
    - Sistema de atenção cognitiva
    - Sistemas de memória
    - Ciclos de reflexão
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        # Carregar configuração
        self.config = EVAConfig.load(config_path)
        
        # Inicializar logging
        from utils.logging_system import EVALogger
        EVALogger.initialize(self.config.log_level)
        
        self.logger = EVALogger.get_logger("EVAOrchestrator")
        self.conv_logger = ConversationLogger()
        self.perf_logger = PerformanceLogger()
        
        # Componentes principais
        self.model_manager: Optional[ModelManager] = None
        self.consciousness: Optional[ConsciousnessSystem] = None
        self.attention_system: Optional[AttentionSystem] = None
        self.episodic_memory: Optional[EpisodicMemory] = None
        self.affective_memory: Optional[AffectiveMemory] = None
        
        # Estado da conversa
        self.conversation_state = ConversationState.IDLE
        self.session_id = self._generate_session_id()
        self.interaction_count = 0
        self.last_reflection_count = 0
        
        # Estatísticas
        self.total_response_time = 0.0
        self.successful_interactions = 0
        
        self.logger.info(f"EVAOrchestrator inicializado (sessão: {self.session_id})")
    
    async def initialize(self):
        """Inicializa todos os componentes do sistema"""
        try:
            self.logger.info("Inicializando componentes do sistema EVA...")
            
            # Validar configuração
            config_errors = self.config.validate()
            if config_errors:
                for error in config_errors:
                    self.logger.error(f"Erro de configuração: {error}")
                raise ValueError("Configuração inválida")
            
            # Inicializar gerenciador de modelos
            self.model_manager = ModelManager(self.config)
            await self.model_manager.initialize()
            
            # Inicializar sistema de consciência
            self.consciousness = ConsciousnessSystem(self.config)
            self.consciousness.set_model_manager(self.model_manager)
            
            # Inicializar sistema de atenção
            self.attention_system = AttentionSystem(self.config)
            
            # Inicializar sistemas de memória
            self.episodic_memory = EpisodicMemory(self.config)
            await self.episodic_memory.initialize()
            
            self.affective_memory = AffectiveMemory(self.config)
            await self.affective_memory.initialize()
            
            self.logger.info("Todos os componentes inicializados com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização: {e}")
            raise
    
    async def process_conversation(self, user_input: str) -> str:
        """
        Processa uma entrada de conversa completa.
        
        Args:
            user_input: Entrada do usuário
            
        Returns:
            Resposta da EVA
        """
        start_time = time.time()
        
        try:
            self.conversation_state = ConversationState.PROCESSING
            self.interaction_count += 1
            
            # Log da entrada do usuário
            self.conv_logger.log_user_input(self.session_id, user_input)
            
            # 1. Criar contexto da conversa
            context = await self._create_conversation_context(user_input)
            
            # 2. Analisar entrada com sistema de atenção
            attention_analysis = await self.attention_system.analyze_input(context)
            
            # 3. Recuperar memórias relevantes
            memories = await self._retrieve_relevant_memories(context, attention_analysis)
            
            # 4. Processar através do sistema de consciência
            self.conversation_state = ConversationState.RESPONDING
            response = await self.consciousness.process_with_modules(
                context, memories, attention_analysis
            )
            
            # 5. Armazenar interação na memória
            await self._store_interaction(context, response, attention_analysis)
            
            # 6. Log da resposta
            modules_used = attention_analysis.required_modules
            self.conv_logger.log_eva_response(self.session_id, response, modules_used)
            
            # 7. Reflexão pós-interação (se habilitada)
            if self.config.enable_reflection and self._should_reflect():
                asyncio.create_task(self._post_interaction_reflection(context, response))
            
            # Atualizar estatísticas
            response_time = time.time() - start_time
            self.total_response_time += response_time
            self.successful_interactions += 1
            
            # Log de performance
            self.perf_logger.log_conversation_metrics(
                self.session_id,
                self.interaction_count,
                self.total_response_time / self.successful_interactions
            )
            
            self.conversation_state = ConversationState.IDLE
            return response
            
        except Exception as e:
            self.logger.error(f"Erro no processamento da conversa: {e}")
            self.conversation_state = ConversationState.IDLE
            return await self._generate_error_response(user_input, str(e))
    
    async def _create_conversation_context(self, user_input: str) -> ConversationContext:
        """Cria contexto da conversa atual"""
        
        # Recuperar histórico de conversa
        conversation_history = await self.episodic_memory.get_session_history(
            self.session_id, 
            limit=self.config.max_conversation_history
        )
        
        # Analisar estado emocional
        emotional_state = await self.consciousness.analyze_emotional_state(user_input)
        
        # Log do estado emocional
        self.conv_logger.log_emotional_state(self.session_id, emotional_state)
        
        context = ConversationContext(
            user_input=user_input,
            conversation_history=conversation_history,
            emotional_state=emotional_state,
            active_modules=[],  # Será preenchido pelo sistema de atenção
            session_id=self.session_id,
            timestamp=time.time()
        )
        
        return context
    
    async def _retrieve_relevant_memories(self, context: ConversationContext, attention_analysis) -> Dict[str, Any]:
        """Recupera memórias relevantes para o contexto atual"""
        
        memories = {}
        
        try:
            # Memórias episódicas (histórico factual)
            episodic_memories = await self.episodic_memory.search_similar(
                context.user_input, limit=5
            )
            memories['episodic'] = episodic_memories
            
            # Memórias afetivas (relacionamento e emoções)
            affective_memories = await self.affective_memory.get_relevant_memories(
                context.emotional_state, context.user_input, limit=3
            )
            memories['affective'] = affective_memories
            
            # Memórias específicas baseadas na intenção
            if attention_analysis.primary_intent.value == 'creative_request':
                creative_memories = await self.episodic_memory.search_by_category(
                    'creative', limit=3
                )
                memories['creative'] = creative_memories
            
            elif attention_analysis.primary_intent.value == 'task':
                task_memories = await self.episodic_memory.search_by_category(
                    'task', limit=3
                )
                memories['tasks'] = task_memories
            
        except Exception as e:
            self.logger.warning(f"Erro ao recuperar memórias: {e}")
            # Continuar sem memórias se houver erro
        
        return memories
    
    async def _store_interaction(
        self, 
        context: ConversationContext, 
        response: str, 
        attention_analysis
    ):
        """Armazena a interação atual na memória"""
        
        try:
            # Armazenar na memória episódica
            await self.episodic_memory.store_interaction(
                session_id=context.session_id,
                user_input=context.user_input,
                eva_response=response,
                timestamp=context.timestamp,
                metadata={
                    'intent': attention_analysis.primary_intent.value,
                    'modules_used': attention_analysis.required_modules,
                    'complexity': attention_analysis.complexity_level,
                    'emotional_intensity': attention_analysis.emotional_intensity
                }
            )
            
            # Armazenar na memória afetiva
            await self.affective_memory.store_interaction(
                session_id=context.session_id,
                emotional_state=context.emotional_state,
                user_input=context.user_input,
                eva_response=response,
                timestamp=context.timestamp
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao armazenar interação: {e}")
    
    def _should_reflect(self) -> bool:
        """Determina se deve executar reflexão pós-interação"""
        interactions_since_reflection = self.interaction_count - self.last_reflection_count
        return interactions_since_reflection >= self.config.reflection_interval
    
    async def _post_interaction_reflection(self, context: ConversationContext, response: str):
        """Processo de reflexão pós-interação para aprendizado"""
        try:
            self.conversation_state = ConversationState.REFLECTING
            self.logger.debug("Iniciando reflexão pós-interação")
            
            # Construir prompt de reflexão
            reflection_prompt = self._build_reflection_prompt(context, response)
            
            # Executar reflexão
            reflection = await self.consciousness.invoke_reflective_module(
                reflection_prompt, context
            )
            
            # Armazenar insights da reflexão
            await self.affective_memory.store_reflection(
                reflection, context.timestamp, context.session_id
            )
            
            # Log da reflexão
            self.conv_logger.log_reflection(self.session_id, reflection)
            
            self.last_reflection_count = self.interaction_count
            self.logger.debug("Reflexão pós-interação concluída")
            
        except Exception as e:
            self.logger.error(f"Erro na reflexão pós-interação: {e}")
        finally:
            self.conversation_state = ConversationState.IDLE
    
    def _build_reflection_prompt(self, context: ConversationContext, response: str) -> str:
        """Constrói prompt para reflexão pós-interação"""
        return f"""{REFLECTION_PROMPT}

Interação analisada:
Entrada do usuário: "{context.user_input}"
Resposta da EVA: "{response}"
Estado emocional detectado: {context.emotional_state}
Módulos ativados: {context.active_modules}
Timestamp: {context.timestamp}
Número da interação: {self.interaction_count}

Forneça uma reflexão estruturada focando em:
1. Qualidade da resposta e adequação ao contexto
2. Percepção do estado emocional do usuário
3. Eficácia dos módulos ativados
4. Oportunidades de melhoria no relacionamento
5. Insights para futuras interações
"""
    
    async def _generate_error_response(self, user_input: str, error_msg: str) -> str:
        """Gera resposta de erro empática"""
        error_responses = [
            "Desculpe, estou tendo algumas dificuldades técnicas no momento. Pode tentar novamente?",
            "Parece que algo não funcionou como esperado. Vamos tentar de novo?",
            "Estou passando por um pequeno problema interno. Pode repetir sua pergunta?",
            "Algo deu errado do meu lado. Pode me dar mais uma chance?"
        ]
        
        import random
        response = random.choice(error_responses)
        
        # Log do erro
        self.logger.error(f"Erro na conversa - Input: {user_input[:100]}... | Erro: {error_msg}")
        
        return response
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Retorna status detalhado do sistema"""
        
        status = {
            'session_id': self.session_id,
            'conversation_state': self.conversation_state.value,
            'interaction_count': self.interaction_count,
            'successful_interactions': self.successful_interactions,
            'avg_response_time': (
                self.total_response_time / self.successful_interactions 
                if self.successful_interactions > 0 else 0
            ),
            'last_reflection_count': self.last_reflection_count
        }
        
        # Status dos componentes
        if self.model_manager:
            status['model_manager'] = self.model_manager.get_model_stats()
        
        if self.consciousness:
            status['consciousness'] = self.consciousness.get_consciousness_stats()
        
        # Status das memórias
        try:
            if self.episodic_memory:
                status['episodic_memory'] = await self.episodic_memory.get_stats()
            
            if self.affective_memory:
                status['affective_memory'] = await self.affective_memory.get_stats()
        except Exception as e:
            self.logger.warning(f"Erro ao obter status das memórias: {e}")
        
        return status
    
    async def save_session_state(self):
        """Salva o estado atual da sessão"""
        try:
            session_state = {
                'session_id': self.session_id,
                'interaction_count': self.interaction_count,
                'last_reflection_count': self.last_reflection_count,
                'total_response_time': self.total_response_time,
                'successful_interactions': self.successful_interactions,
                'timestamp': time.time()
            }
            
            # Salvar estado (implementação específica dependente do storage)
            # Por enquanto, apenas log
            self.logger.info(f"Estado da sessão salvo: {session_state}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar estado da sessão: {e}")
    
    async def load_session_state(self, session_id: str):
        """Carrega estado de uma sessão anterior"""
        try:
            # Implementação futura para carregar estado persistido
            self.session_id = session_id
            self.logger.info(f"Tentativa de carregar sessão: {session_id}")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar estado da sessão: {e}")
    
    async def shutdown(self):
        """Encerra o sistema de forma limpa"""
        try:
            self.logger.info("Iniciando shutdown do sistema EVA")
            
            # Salvar estado atual
            await self.save_session_state()
            
            # Executar reflexão final se necessário
            if self._should_reflect():
                self.logger.info("Executando reflexão final...")
                # Reflexão simplificada para shutdown
                
            # Limpar recursos dos componentes
            if self.model_manager:
                await self.model_manager.cleanup()
            
            if self.episodic_memory:
                await self.episodic_memory.close()
            
            if self.affective_memory:
                await self.affective_memory.close()
            
            self.logger.info("Shutdown concluído com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro durante shutdown: {e}")
    
    # Métodos auxiliares
    def _generate_session_id(self) -> str:
        """Gera ID único para a sessão"""
        return str(uuid.uuid4())[:8]
    
    def get_session_id(self) -> str:
        """Retorna ID da sessão atual"""
        return self.session_id
    
    def get_interaction_count(self) -> int:
        """Retorna número de interações na sessão"""
        return self.interaction_count
    
    def is_ready(self) -> bool:
        """Verifica se o sistema está pronto para processar conversas"""
        return (
            self.model_manager is not None and
            self.consciousness is not None and
            self.attention_system is not None and
            self.episodic_memory is not None and
            self.affective_memory is not None and
            self.conversation_state == ConversationState.IDLE
        )

# Função de conveniência para inicialização
async def create_eva_instance(config_path: str = "config.yaml") -> EVAOrchestrator:
    """Cria e inicializa uma instância da EVA"""
    eva = EVAOrchestrator(config_path)
    await eva.initialize()
    return eva
