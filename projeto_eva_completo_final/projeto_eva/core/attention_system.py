"""
Sistema de atenção cognitiva que analisa entrada do usuário e determina
quais módulos cognitivos ativar.
"""

import re
import json
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from utils.logging_system import EVALogger

class IntentType(Enum):
    """Tipos de intenção identificados na entrada do usuário"""
    QUESTION = "question"
    TASK = "task"
    EMOTIONAL_SUPPORT = "emotional_support"
    CREATIVE_REQUEST = "creative_request"
    CASUAL_CHAT = "casual_chat"
    SYSTEM_COMMAND = "system_command"
    REFLECTION = "reflection"

@dataclass
class AttentionAnalysis:
    """Resultado da análise de atenção"""
    primary_intent: IntentType
    confidence: float
    required_modules: List[str]
    complexity_level: int  # 1-5
    emotional_intensity: float  # 0-1
    urgency: float  # 0-1
    context_factors: Dict[str, Any]

class AttentionSystem:
    """
    Sistema que analisa a entrada do usuário e determina quais módulos cognitivos ativar.
    
    Funciona como um "diretor de orquestra" que decide qual combinação de personas
    deve ser ativada para responder de forma ótima à solicitação do usuário.
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = EVALogger.get_logger("AttentionSystem")
        
        # Padrões para classificação de intenção
        self.intent_patterns = {
            IntentType.QUESTION: [
                r'\b(o que|como|quando|onde|por que|qual|quem)\b',
                r'\?',
                r'\b(explique|me diga|você sabe|pode me dizer)\b',
                r'\b(qual é|como funciona|por que acontece)\b'
            ],
            IntentType.TASK: [
                r'\b(faça|crie|gere|escreva|calcule|analise|execute)\b',
                r'\b(preciso que|pode fazer|me ajude a|quero que)\b',
                r'\b(realize|complete|desenvolva|implemente)\b',
                r'\b(organize|planeje|estruture)\b'
            ],
            IntentType.EMOTIONAL_SUPPORT: [
                r'\b(triste|feliz|ansioso|preocupado|estressado|deprimido)\b',
                r'\b(me sinto|estou me sentindo|estou passando por)\b',
                r'\b(preciso de apoio|me ajude|estou sofrendo)\b',
                r'\b(não aguento mais|estou cansado|me sinto só)\b'
            ],
            IntentType.CREATIVE_REQUEST: [
                r'\b(imagine|invente|crie uma história|escreva um poema)\b',
                r'\b(seja criativo|use sua imaginação|invente algo)\b',
                r'\b(arte|música|poesia|história|desenho)\b',
                r'\b(inspiração|ideia criativa|brainstorm)\b'
            ],
            IntentType.CASUAL_CHAT: [
                r'\b(oi|olá|como vai|tudo bem|e aí)\b',
                r'\b(conversar|bater papo|falar sobre|vamos conversar)\b',
                r'\b(o que acha|sua opinião|o que pensa)\b',
                r'\b(como está|como você está|tudo certo)\b'
            ],
            IntentType.SYSTEM_COMMAND: [
                r'\b(configure|ajuste|mude|altere|defina)\b',
                r'\b(status|estado|informações do sistema)\b',
                r'\b(reinicie|pare|inicie|ative|desative)\b',
                r'\b(salve|carregue|exporte|importe)\b'
            ]
        }
        
        # Mapeamento de intenções para módulos cognitivos
        self.intent_to_modules = {
            IntentType.QUESTION: ['analytical', 'empathetic'],
            IntentType.TASK: ['executive', 'analytical'],
            IntentType.EMOTIONAL_SUPPORT: ['empathetic', 'reflective'],
            IntentType.CREATIVE_REQUEST: ['creative', 'empathetic'],
            IntentType.CASUAL_CHAT: ['empathetic', 'creative'],
            IntentType.SYSTEM_COMMAND: ['executive', 'analytical'],
            IntentType.REFLECTION: ['reflective', 'empathetic']
        }
        
        # Palavras-chave para análise de complexidade
        self.complexity_indicators = {
            'high': [
                'complexo', 'complicado', 'detalhado', 'profundo', 'análise',
                'múltiplos', 'vários', 'diferentes', 'comparar', 'avaliar'
            ],
            'medium': [
                'explicar', 'descrever', 'mostrar', 'exemplo', 'como fazer'
            ],
            'low': [
                'simples', 'rápido', 'básico', 'resumo', 'sim ou não'
            ]
        }
        
        # Indicadores de intensidade emocional
        self.emotional_intensity_words = {
            'high': [
                'muito', 'extremamente', 'totalmente', 'completamente',
                'desesperado', 'urgente', 'crítico', 'importante',
                'amo', 'odeio', 'adoro', 'detesto'
            ],
            'medium': [
                'bastante', 'bem', 'meio', 'um pouco',
                'gosto', 'não gosto', 'prefiro'
            ],
            'low': [
                'talvez', 'possivelmente', 'pode ser', 'acho que'
            ]
        }
        
        # Indicadores de urgência
        self.urgency_keywords = [
            'urgente', 'rápido', 'agora', 'imediatamente', 'já',
            'preciso agora', 'é urgente', 'rapidamente', 'depressa',
            'o quanto antes', 'com pressa'
        ]
    
    async def analyze_input(self, context) -> AttentionAnalysis:
        """
        Analisa a entrada do usuário e determina a estratégia de atenção.
        
        Args:
            context: Contexto da conversa contendo user_input, emotional_state, etc.
            
        Returns:
            AttentionAnalysis com a estratégia de atenção determinada
        """
        user_input = context.user_input.lower()
        
        try:
            # 1. Classificar intenção primária
            primary_intent, confidence = self._classify_intent(user_input)
            
            # 2. Determinar módulos necessários
            required_modules = self._determine_required_modules(
                primary_intent, user_input, context
            )
            
            # 3. Avaliar complexidade
            complexity_level = self._assess_complexity(user_input, context)
            
            # 4. Avaliar intensidade emocional
            emotional_intensity = self._assess_emotional_intensity(
                user_input, getattr(context, 'emotional_state', {})
            )
            
            # 5. Avaliar urgência
            urgency = self._assess_urgency(user_input)
            
            # 6. Identificar fatores contextuais
            context_factors = self._identify_context_factors(user_input, context)
            
            analysis = AttentionAnalysis(
                primary_intent=primary_intent,
                confidence=confidence,
                required_modules=required_modules,
                complexity_level=complexity_level,
                emotional_intensity=emotional_intensity,
                urgency=urgency,
                context_factors=context_factors
            )
            
            self.logger.debug(f"Análise de atenção: Intent={primary_intent.value}, "
                            f"Modules={required_modules}, Complexity={complexity_level}, "
                            f"Emotional={emotional_intensity:.2f}, Urgency={urgency:.2f}")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Erro na análise de atenção: {e}")
            # Retornar análise padrão em caso de erro
            return self._get_default_analysis()
    
    def _classify_intent(self, user_input: str) -> Tuple[IntentType, float]:
        """Classifica a intenção primária da entrada"""
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            matches = 0
            
            for pattern in patterns:
                pattern_matches = len(re.findall(pattern, user_input, re.IGNORECASE))
                if pattern_matches > 0:
                    matches += 1
                    score += pattern_matches
            
            if score > 0:
                # Normalizar score baseado no número de padrões
                normalized_score = (score + matches) / len(patterns)
                intent_scores[intent] = normalized_score
        
        if not intent_scores:
            return IntentType.CASUAL_CHAT, 0.5
        
        # Retornar intenção com maior score
        primary_intent = max(intent_scores, key=intent_scores.get)
        confidence = min(intent_scores[primary_intent], 1.0)
        
        return primary_intent, confidence
    
    def _determine_required_modules(
        self, 
        primary_intent: IntentType, 
        user_input: str, 
        context
    ) -> List[str]:
        """Determina quais módulos cognitivos ativar"""
        
        # Módulos base para a intenção
        base_modules = self.intent_to_modules.get(primary_intent, ['empathetic'])
        required_modules = base_modules.copy()
        
        # Módulos adicionais baseados no contexto
        emotional_state = getattr(context, 'emotional_state', {})
        
        # Se há alta intensidade emocional, sempre incluir empático
        if emotional_state and max(emotional_state.values(), default=0) > 0.6:
            if 'empathetic' not in required_modules:
                required_modules.append('empathetic')
        
        # Se há palavras criativas, incluir módulo criativo
        creative_words = ['criativo', 'imaginação', 'arte', 'poesia', 'história', 'inventar']
        if any(word in user_input for word in creative_words):
            if 'creative' not in required_modules:
                required_modules.append('creative')
        
        # Se há palavras analíticas, incluir módulo analítico
        analytical_words = ['analisar', 'comparar', 'avaliar', 'dados', 'estatística', 'lógica']
        if any(word in user_input for word in analytical_words):
            if 'analytical' not in required_modules:
                required_modules.append('analytical')
        
        # Se há palavras executivas, incluir módulo executivo
        executive_words = ['planejar', 'organizar', 'executar', 'implementar', 'gerenciar']
        if any(word in user_input for word in executive_words):
            if 'executive' not in required_modules:
                required_modules.append('executive')
        
        # Limitar número de módulos para eficiência
        max_modules = 3
        if len(required_modules) > max_modules:
            # Priorizar baseado na configuração das personas
            prioritized = self._prioritize_modules(required_modules, primary_intent)
            required_modules = prioritized[:max_modules]
        
        return required_modules
    
    def _prioritize_modules(self, modules: List[str], intent: IntentType) -> List[str]:
        """Prioriza módulos baseado na configuração e intenção"""
        if not hasattr(self.config, 'personas'):
            return modules
        
        # Ordenar por peso de especialização e threshold de ativação
        def module_priority(module_name):
            if module_name in self.config.personas:
                persona_config = self.config.personas[module_name]
                # Menor threshold = maior prioridade, maior peso = maior prioridade
                return (1 - persona_config.activation_threshold) * persona_config.specialization_weight
            return 0.5
        
        return sorted(modules, key=module_priority, reverse=True)
    
    def _assess_complexity(self, user_input: str, context) -> int:
        """Avalia a complexidade da solicitação (1-5)"""
        complexity_score = 2  # Base: complexidade média
        
        # Baseado em palavras-chave
        for level, words in self.complexity_indicators.items():
            matches = sum(1 for word in words if word in user_input)
            if level == 'high' and matches > 0:
                complexity_score += matches
            elif level == 'low' and matches > 0:
                complexity_score -= matches
        
        # Baseado no comprimento da entrada
        word_count = len(user_input.split())
        if word_count > 50:
            complexity_score += 1
        elif word_count < 10:
            complexity_score -= 1
        
        # Baseado em pontuação (múltiplas perguntas, etc.)
        question_marks = user_input.count('?')
        if question_marks > 1:
            complexity_score += 1
        
        # Baseado no histórico de conversa
        conversation_history = getattr(context, 'conversation_history', [])
        if len(conversation_history) > 5:
            # Conversas longas tendem a ser mais complexas
            complexity_score += 1
        
        # Limitar entre 1 e 5
        return max(1, min(5, complexity_score))
    
    def _assess_emotional_intensity(
        self, 
        user_input: str, 
        emotional_state: Dict[str, float]
    ) -> float:
        """Avalia a intensidade emocional (0-1)"""
        
        intensity_score = 0.0
        
        # Baseado em palavras-chave de intensidade
        for level, words in self.emotional_intensity_words.items():
            matches = sum(1 for word in words if word in user_input)
            if level == 'high':
                intensity_score += matches * 0.3
            elif level == 'medium':
                intensity_score += matches * 0.2
            elif level == 'low':
                intensity_score += matches * 0.1
        
        # Baseado no estado emocional detectado
        if emotional_state:
            max_emotion = max(emotional_state.values(), default=0)
            intensity_score += max_emotion * 0.4
        
        # Baseado em pontuação (exclamações, caps lock)
        exclamation_count = user_input.count('!')
        caps_ratio = sum(1 for c in user_input if c.isupper()) / len(user_input) if user_input else 0
        
        intensity_score += min(exclamation_count * 0.1, 0.3)
        intensity_score += min(caps_ratio * 0.5, 0.2)
        
        # Baseado em repetição de caracteres (ex: "muuuito")
        repeated_chars = len(re.findall(r'(.)\1{2,}', user_input))
        intensity_score += min(repeated_chars * 0.1, 0.2)
        
        return min(intensity_score, 1.0)
    
    def _assess_urgency(self, user_input: str) -> float:
        """Avalia a urgência da solicitação (0-1)"""
        
        urgency_score = 0.0
        
        # Baseado em palavras-chave de urgência
        for keyword in self.urgency_keywords:
            if keyword in user_input:
                urgency_score += 0.3
        
        # Baseado em pontuação múltipla
        multiple_exclamations = user_input.count('!!') + user_input.count('!!!')
        urgency_score += min(multiple_exclamations * 0.2, 0.4)
        
        # Baseado em caps lock excessivo
        caps_words = sum(1 for word in user_input.split() if word.isupper() and len(word) > 2)
        urgency_score += min(caps_words * 0.1, 0.3)
        
        return min(urgency_score, 1.0)
    
    def _identify_context_factors(self, user_input: str, context) -> Dict[str, Any]:
        """Identifica fatores contextuais relevantes"""
        factors = {}
        
        # Primeira interação
        conversation_history = getattr(context, 'conversation_history', [])
        factors['is_first_interaction'] = len(conversation_history) == 0
        
        # Continuação de tópico
        factors['is_follow_up'] = len(conversation_history) > 0
        
        # Presença de código ou elementos técnicos
        factors['has_code'] = bool(re.search(r'```|`[^`]+`|def |class |import ', user_input))
        
        # Presença de números ou dados
        factors['has_numbers'] = bool(re.search(r'\d+', user_input))
        
        # Presença de URLs ou referências
        factors['has_urls'] = bool(re.search(r'http[s]?://|www\.', user_input))
        
        # Linguagem formal vs informal
        formal_indicators = ['por favor', 'gostaria', 'poderia', 'solicito']
        informal_indicators = ['oi', 'e aí', 'cara', 'mano', 'tipo']
        
        formal_count = sum(1 for indicator in formal_indicators if indicator in user_input)
        informal_count = sum(1 for indicator in informal_indicators if indicator in user_input)
        
        if formal_count > informal_count:
            factors['tone'] = 'formal'
        elif informal_count > formal_count:
            factors['tone'] = 'informal'
        else:
            factors['tone'] = 'neutral'
        
        # Comprimento da entrada
        word_count = len(user_input.split())
        if word_count < 5:
            factors['length'] = 'short'
        elif word_count > 30:
            factors['length'] = 'long'
        else:
            factors['length'] = 'medium'
        
        return factors
    
    def _get_default_analysis(self) -> AttentionAnalysis:
        """Retorna análise padrão em caso de erro"""
        return AttentionAnalysis(
            primary_intent=IntentType.CASUAL_CHAT,
            confidence=0.5,
            required_modules=['empathetic'],
            complexity_level=2,
            emotional_intensity=0.3,
            urgency=0.1,
            context_factors={'is_default': True}
        )
    
    def get_attention_summary(self, analysis: AttentionAnalysis) -> str:
        """Gera resumo textual da análise de atenção"""
        summary_parts = [
            f"Intenção: {analysis.primary_intent.value} ({analysis.confidence:.2f})",
            f"Módulos: {', '.join(analysis.required_modules)}",
            f"Complexidade: {analysis.complexity_level}/5",
            f"Intensidade emocional: {analysis.emotional_intensity:.2f}",
            f"Urgência: {analysis.urgency:.2f}"
        ]
        
        return " | ".join(summary_parts)
