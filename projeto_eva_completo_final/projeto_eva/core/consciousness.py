"""
Sistema de consciência distribuída que coordena diferentes módulos cognitivos.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from core.model_manager import ModelManager
from core.attention_system import AttentionAnalysis
from config.prompts import SYSTEM_PROMPTS, SYNTHESIS_PROMPT, EMOTIONAL_ANALYSIS_PROMPT
from utils.logging_system import EVALogger

class CognitiveModule(Enum):
    """Módulos cognitivos disponíveis"""
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    EMPATHETIC = "empathetic"
    EXECUTIVE = "executive"
    REFLECTIVE = "reflective"

@dataclass
class ModuleResponse:
    """Resposta de um módulo cognitivo"""
    module: CognitiveModule
    response: str
    confidence: float
    processing_time: float
    context_used: Dict[str, Any]

class ConsciousnessSystem:
    """
    Sistema de consciência distribuída que coordena diferentes módulos cognitivos.
    
    Funciona como uma "mente coletiva" onde diferentes aspectos da personalidade
    da EVA colaboram para gerar respostas mais ricas e empáticas.
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = EVALogger.get_logger("ConsciousnessSystem")
        self.model_manager: Optional[ModelManager] = None
        
        # Estado interno
        self.active_modules: List[CognitiveModule] = []
        self.module_states: Dict[CognitiveModule, Dict] = {}
        self.synthesis_history: List[Dict] = []
        
        # Mapeamento de módulos para modelos
        self.module_to_model = {
            CognitiveModule.ANALYTICAL: "mistral-7b-instruct",
            CognitiveModule.CREATIVE: "mistral-7b-instruct", 
            CognitiveModule.EMPATHETIC: "mistral-7b-instruct",
            CognitiveModule.EXECUTIVE: "mistral-7b-instruct",
            CognitiveModule.REFLECTIVE: "mistral-7b-instruct"
        }
        
        self.logger.info("Sistema de consciência inicializado")
    
    def set_model_manager(self, model_manager: ModelManager):
        """Define o gerenciador de modelos"""
        self.model_manager = model_manager
        self.logger.debug("ModelManager configurado no sistema de consciência")
    
    async def process_with_modules(
        self, 
        context, 
        memories: Dict[str, Any], 
        attention_analysis: AttentionAnalysis
    ) -> str:
        """
        Processa entrada através dos módulos cognitivos apropriados.
        
        Args:
            context: Contexto da conversa
            memories: Memórias relevantes recuperadas
            attention_analysis: Análise do sistema de atenção
            
        Returns:
            Resposta final sintetizada
        """
        try:
            # Determinar módulos a ativar
            modules_to_activate = [
                CognitiveModule(name) for name in attention_analysis.required_modules
            ]
            
            self.logger.info(f"Ativando módulos: {[m.value for m in modules_to_activate]}")
            
            # Processar através de cada módulo necessário
            module_responses = []
            
            for module in modules_to_activate:
                try:
                    response = await self._process_with_module(
                        module, context, memories, attention_analysis
                    )
                    module_responses.append(response)
                    
                except Exception as e:
                    self.logger.error(f"Erro no módulo {module.value}: {e}")
                    # Continuar com outros módulos mesmo se um falhar
                    continue
            
            if not module_responses:
                # Se nenhum módulo funcionou, usar resposta de emergência
                return await self._generate_emergency_response(context)
            
            # Sintetizar respostas dos módulos
            final_response = await self._synthesize_responses(
                module_responses, context, attention_analysis
            )
            
            # Armazenar no histórico de síntese
            self._store_synthesis_history(module_responses, final_response, attention_analysis)
            
            return final_response
            
        except Exception as e:
            self.logger.error(f"Erro no processamento dos módulos: {e}")
            return await self._generate_emergency_response(context)
    
    async def _process_with_module(
        self,
        module: CognitiveModule,
        context,
        memories: Dict[str, Any],
        attention_analysis: AttentionAnalysis
    ) -> ModuleResponse:
        """Processa entrada através de um módulo específico"""
        
        import time
        start_time = time.time()
        
        try:
            # Preparar contexto específico do módulo
            module_context = self._prepare_module_context(
                context, memories, module, attention_analysis
            )
            
            # Construir prompt para o módulo
            prompt = self._build_module_prompt(module, module_context)
            
            # Obter modelo apropriado
            model_name = self.module_to_model[module]
            
            # Gerar resposta
            response_text = await self.model_manager.generate_text(
                model_name=model_name,
                prompt=prompt,
                max_tokens=512,
                temperature=self._get_module_temperature(module)
            )
            
            processing_time = time.time() - start_time
            
            # Calcular confiança baseada na qualidade da resposta
            confidence = self._calculate_response_confidence(response_text, module)
            
            response = ModuleResponse(
                module=module,
                response=response_text,
                confidence=confidence,
                processing_time=processing_time,
                context_used=module_context
            )
            
            self.logger.debug(f"Módulo {module.value} processado em {processing_time:.2f}s "
                            f"(confiança: {confidence:.2f})")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Erro no processamento do módulo {module.value}: {e}")
            raise
    
    def _prepare_module_context(
        self, 
        context, 
        memories: Dict[str, Any], 
        module: CognitiveModule,
        attention_analysis: AttentionAnalysis
    ) -> Dict[str, Any]:
        """Prepara contexto específico para um módulo"""
        
        base_context = {
            'user_input': context.user_input,
            'conversation_history': getattr(context, 'conversation_history', []),
            'emotional_state': getattr(context, 'emotional_state', {}),
            'session_id': getattr(context, 'session_id', 'unknown'),
            'timestamp': getattr(context, 'timestamp', 0),
            'attention_analysis': attention_analysis
        }
        
        # Adicionar memórias relevantes para o módulo
        if module == CognitiveModule.EMPATHETIC:
            base_context['affective_memories'] = memories.get('affective', [])
            base_context['emotional_patterns'] = memories.get('emotional_patterns', {})
            
        elif module == CognitiveModule.ANALYTICAL:
            base_context['factual_memories'] = memories.get('episodic', [])
            base_context['knowledge_base'] = memories.get('knowledge', [])
            
        elif module == CognitiveModule.CREATIVE:
            base_context['creative_memories'] = memories.get('creative', [])
            base_context['inspiration_sources'] = memories.get('inspiration', [])
            
        elif module == CognitiveModule.EXECUTIVE:
            base_context['task_history'] = memories.get('tasks', [])
            base_context['planning_context'] = memories.get('planning', {})
            
        elif module == CognitiveModule.REFLECTIVE:
            base_context['reflection_history'] = memories.get('reflections', [])
            base_context['learning_insights'] = memories.get('insights', [])
        
        return base_context
    
    def _build_module_prompt(self, module: CognitiveModule, context: Dict[str, Any]) -> str:
        """Constrói prompt específico para um módulo"""
        
        # Prompt base do sistema para o módulo
        system_prompt = SYSTEM_PROMPTS.get(module.value, "")
        
        # Informações contextuais
        user_input = context['user_input']
        conversation_history = context.get('conversation_history', [])
        emotional_state = context.get('emotional_state', {})
        attention_analysis = context.get('attention_analysis')
        
        # Construir histórico de conversa
        history_text = ""
        if conversation_history:
            recent_history = conversation_history[-3:]  # Últimas 3 interações
            history_text = "\n".join([
                f"Usuário: {entry.get('user', '')}\nEVA: {entry.get('eva', '')}"
                for entry in recent_history
            ])
        
        # Informações sobre estado emocional
        emotional_context = ""
        if emotional_state:
            significant_emotions = {k: v for k, v in emotional_state.items() if v > 0.3}
            if significant_emotions:
                emotional_context = f"Estado emocional detectado: {significant_emotions}"
        
        # Informações sobre análise de atenção
        attention_context = ""
        if attention_analysis:
            attention_context = f"""
Análise de contexto:
- Intenção: {attention_analysis.primary_intent.value}
- Complexidade: {attention_analysis.complexity_level}/5
- Intensidade emocional: {attention_analysis.emotional_intensity:.2f}
- Urgência: {attention_analysis.urgency:.2f}
"""
        
        # Memórias específicas do módulo
        memory_context = self._format_module_memories(module, context)
        
        # Construir prompt final
        prompt = f"""{system_prompt}

{attention_context}

{emotional_context}

Histórico recente da conversa:
{history_text}

{memory_context}

Entrada atual do usuário: "{user_input}"

Responda de acordo com sua especialização, mantendo consistência com a personalidade da EVA e o contexto da conversa."""
        
        return prompt
    
    def _format_module_memories(self, module: CognitiveModule, context: Dict[str, Any]) -> str:
        """Formata memórias específicas do módulo para o prompt"""
        
        memory_text = ""
        
        if module == CognitiveModule.EMPATHETIC:
            affective_memories = context.get('affective_memories', [])
            if affective_memories:
                memory_text = "Memórias afetivas relevantes:\n" + "\n".join([
                    f"- {memory}" for memory in affective_memories[:3]
                ])
                
        elif module == CognitiveModule.ANALYTICAL:
            factual_memories = context.get('factual_memories', [])
            if factual_memories:
                memory_text = "Informações factuais relevantes:\n" + "\n".join([
                    f"- {memory}" for memory in factual_memories[:3]
                ])
                
        elif module == CognitiveModule.CREATIVE:
            creative_memories = context.get('creative_memories', [])
            if creative_memories:
                memory_text = "Inspirações criativas anteriores:\n" + "\n".join([
                    f"- {memory}" for memory in creative_memories[:3]
                ])
                
        elif module == CognitiveModule.EXECUTIVE:
            task_history = context.get('task_history', [])
            if task_history:
                memory_text = "Histórico de tarefas:\n" + "\n".join([
                    f"- {task}" for task in task_history[:3]
                ])
                
        elif module == CognitiveModule.REFLECTIVE:
            reflection_history = context.get('reflection_history', [])
            if reflection_history:
                memory_text = "Reflexões anteriores:\n" + "\n".join([
                    f"- {reflection}" for reflection in reflection_history[:3]
                ])
        
        return memory_text
    
    def _get_module_temperature(self, module: CognitiveModule) -> float:
        """Retorna temperatura apropriada para cada módulo"""
        temperatures = {
            CognitiveModule.ANALYTICAL: 0.3,  # Mais determinística
            CognitiveModule.CREATIVE: 0.8,    # Mais criativa
            CognitiveModule.EMPATHETIC: 0.6,  # Equilibrada
            CognitiveModule.EXECUTIVE: 0.4,   # Focada
            CognitiveModule.REFLECTIVE: 0.5   # Moderada
        }
        return temperatures.get(module, 0.7)
    
    def _calculate_response_confidence(self, response: str, module: CognitiveModule) -> float:
        """Calcula confiança da resposta baseada em heurísticas"""
        confidence = 0.5  # Base
        
        # Baseado no comprimento (respostas muito curtas ou muito longas são suspeitas)
        length = len(response.split())
        if 20 <= length <= 200:
            confidence += 0.2
        elif length < 5:
            confidence -= 0.3
        
        # Baseado na presença de estrutura
        if any(marker in response for marker in ['1.', '2.', '-', '*']):
            confidence += 0.1
        
        # Baseado na ausência de repetições excessivas
        words = response.split()
        unique_words = set(words)
        if len(unique_words) / len(words) > 0.7:
            confidence += 0.1
        
        # Baseado na presença de palavras-chave do módulo
        module_keywords = {
            CognitiveModule.ANALYTICAL: ['análise', 'dados', 'lógica', 'conclusão'],
            CognitiveModule.CREATIVE: ['imaginação', 'criativo', 'ideia', 'inspiração'],
            CognitiveModule.EMPATHETIC: ['sinto', 'compreendo', 'apoio', 'emoção'],
            CognitiveModule.EXECUTIVE: ['plano', 'ação', 'objetivo', 'estratégia'],
            CognitiveModule.REFLECTIVE: ['reflexão', 'aprendizado', 'insight', 'crescimento']
        }
        
        keywords = module_keywords.get(module, [])
        keyword_matches = sum(1 for keyword in keywords if keyword in response.lower())
        confidence += min(keyword_matches * 0.05, 0.2)
        
        return min(max(confidence, 0.1), 1.0)
    
    async def _synthesize_responses(
        self,
        module_responses: List[ModuleResponse],
        context,
        attention_analysis: AttentionAnalysis
    ) -> str:
        """Sintetiza as respostas de múltiplos módulos em uma resposta coerente"""
        
        if len(module_responses) == 1:
            # Se apenas um módulo foi ativado, retornar sua resposta
            return module_responses[0].response
        
        try:
            # Preparar contexto para síntese
            responses_text = "\n\n".join([
                f"**{response.module.value.title()}** (confiança: {response.confidence:.2f}):\n{response.response}"
                for response in module_responses
            ])
            
            # Construir prompt de síntese
            synthesis_prompt = f"""{SYNTHESIS_PROMPT}

Entrada do usuário: "{context.user_input}"

Análise de contexto:
- Intenção: {attention_analysis.primary_intent.value}
- Intensidade emocional: {attention_analysis.emotional_intensity:.2f}
- Urgência: {attention_analysis.urgency:.2f}

Respostas dos módulos cognitivos:
{responses_text}

Sintetize essas perspectivas em uma resposta única, natural e coerente que reflita a personalidade empática e inteligente da EVA."""
            
            # Usar o módulo empático para síntese (ele é bom em integração)
            synthesized_response = await self.model_manager.generate_text(
                model_name="mistral-7b-instruct",
                prompt=synthesis_prompt,
                max_tokens=600,
                temperature=0.6
            )
            
            return synthesized_response
            
        except Exception as e:
            self.logger.error(f"Erro na síntese de respostas: {e}")
            # Fallback: retornar resposta do módulo com maior confiança
            best_response = max(module_responses, key=lambda r: r.confidence)
            return best_response.response
    
    async def analyze_emotional_state(self, user_input: str) -> Dict[str, float]:
        """Analisa o estado emocional usando processamento de linguagem natural"""
        try:
            prompt = EMOTIONAL_ANALYSIS_PROMPT.format(user_input=user_input)
            
            response = await self.model_manager.generate_text(
                model_name="mistral-7b-instruct",
                prompt=prompt,
                max_tokens=200,
                temperature=0.3
            )
            
            # Tentar parsear JSON da resposta
            try:
                emotional_state = json.loads(response.strip())
                # Validar e normalizar valores
                normalized_state = {}
                for emotion, value in emotional_state.items():
                    if isinstance(value, (int, float)):
                        normalized_state[emotion] = max(0.0, min(1.0, float(value)))
                
                return normalized_state
                
            except json.JSONDecodeError:
                self.logger.warning("Não foi possível parsear análise emocional como JSON")
                return self._get_default_emotional_state()
                
        except Exception as e:
            self.logger.error(f"Erro na análise emocional: {e}")
            return self._get_default_emotional_state()
    
    def _get_default_emotional_state(self) -> Dict[str, float]:
        """Retorna estado emocional padrão"""
        return {
            'alegria': 0.3,
            'tristeza': 0.1,
            'raiva': 0.1,
            'medo': 0.1,
            'surpresa': 0.2,
            'confianca': 0.4,
            'energia': 0.3,
            'calma': 0.5
        }
    
    async def invoke_reflective_module(self, reflection_prompt: str, context) -> str:
        """Invoca especificamente o módulo reflexivo"""
        try:
            full_prompt = f"""{SYSTEM_PROMPTS['reflective']}

{reflection_prompt}

Contexto da sessão: {getattr(context, 'session_id', 'unknown')}
Timestamp: {getattr(context, 'timestamp', 0)}

Forneça uma reflexão estruturada e insights acionáveis."""
            
            reflection = await self.model_manager.generate_text(
                model_name="mistral-7b-instruct",
                prompt=full_prompt,
                max_tokens=400,
                temperature=0.5
            )
            
            return reflection
            
        except Exception as e:
            self.logger.error(f"Erro na invocação do módulo reflexivo: {e}")
            return "Reflexão não disponível devido a erro técnico."
    
    async def _generate_emergency_response(self, context) -> str:
        """Gera resposta de emergência quando todos os módulos falham"""
        emergency_responses = [
            "Desculpe, estou tendo algumas dificuldades técnicas no momento. Pode repetir sua pergunta?",
            "Parece que estou com um pequeno problema interno. Vamos tentar novamente?",
            "Estou passando por uma pequena instabilidade. Pode me dar um momento e tentar de novo?",
            "Algo não está funcionando como deveria. Pode reformular sua pergunta?"
        ]
        
        import random
        return random.choice(emergency_responses)
    
    def _store_synthesis_history(
        self,
        module_responses: List[ModuleResponse],
        final_response: str,
        attention_analysis: AttentionAnalysis
    ):
        """Armazena histórico de síntese para análise futura"""
        synthesis_record = {
            'timestamp': time.time(),
            'modules_used': [r.module.value for r in module_responses],
            'module_confidences': {r.module.value: r.confidence for r in module_responses},
            'attention_analysis': {
                'intent': attention_analysis.primary_intent.value,
                'complexity': attention_analysis.complexity_level,
                'emotional_intensity': attention_analysis.emotional_intensity,
                'urgency': attention_analysis.urgency
            },
            'final_response_length': len(final_response.split()),
            'synthesis_successful': True
        }
        
        self.synthesis_history.append(synthesis_record)
        
        # Manter apenas os últimos 100 registros
        if len(self.synthesis_history) > 100:
            self.synthesis_history.pop(0)
    
    def get_consciousness_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema de consciência"""
        if not self.synthesis_history:
            return {'no_data': True}
        
        recent_syntheses = self.synthesis_history[-20:]  # Últimas 20
        
        # Módulos mais utilizados
        module_usage = {}
        for record in recent_syntheses:
            for module in record['modules_used']:
                module_usage[module] = module_usage.get(module, 0) + 1
        
        # Complexidade média
        avg_complexity = sum(r['attention_analysis']['complexity'] for r in recent_syntheses) / len(recent_syntheses)
        
        # Intensidade emocional média
        avg_emotional_intensity = sum(r['attention_analysis']['emotional_intensity'] for r in recent_syntheses) / len(recent_syntheses)
        
        return {
            'total_syntheses': len(self.synthesis_history),
            'recent_syntheses': len(recent_syntheses),
            'module_usage': module_usage,
            'avg_complexity': avg_complexity,
            'avg_emotional_intensity': avg_emotional_intensity,
            'success_rate': sum(1 for r in recent_syntheses if r['synthesis_successful']) / len(recent_syntheses)
        }
