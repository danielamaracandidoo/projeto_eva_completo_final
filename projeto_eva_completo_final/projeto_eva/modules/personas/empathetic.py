"""
Módulo Persona Empática da EVA.
Especializada em inteligência emocional, suporte e conexão humana profunda.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from utils.logging_system import EVALogger

@dataclass
class EmotionalInsight:
    """Insight emocional sobre uma situação"""
    primary_emotion: str
    emotional_intensity: float
    underlying_needs: List[str]
    support_strategies: List[str]
    empathetic_responses: List[str]
    validation_points: List[str]

class EmpatheticPersona:
    """
    Persona Empática da EVA.
    
    Especializada em:
    - Inteligência emocional avançada
    - Suporte emocional e psicológico
    - Validação de sentimentos
    - Conexão humana profunda
    - Comunicação compassiva
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = EVALogger.get_logger("EmpatheticPersona")
        
        # Características da persona
        self.traits = {
            'compassionate': 0.95,
            'understanding': 0.92,
            'supportive': 0.90,
            'intuitive': 0.88,
            'nurturing': 0.85
        }
        
        # Mapeamento de emoções para necessidades humanas básicas
        self.emotion_to_needs = {
            'tristeza': ['conforto', 'compreensão', 'conexão', 'validação'],
            'raiva': ['justiça', 'controle', 'respeito', 'expressão'],
            'medo': ['segurança', 'previsibilidade', 'apoio', 'proteção'],
            'alegria': ['compartilhamento', 'celebração', 'conexão', 'gratidão'],
            'ansiedade': ['calma', 'clareza', 'controle', 'reasseguramento'],
            'solidão': ['conexão', 'pertencimento', 'compreensão', 'companhia'],
            'frustração': ['progresso', 'eficácia', 'reconhecimento', 'solução'],
            'culpa': ['perdão', 'redenção', 'aceitação', 'crescimento'],
            'vergonha': ['aceitação', 'dignidade', 'valor próprio', 'compreensão']
        }
        
        # Estratégias de suporte emocional
        self.support_strategies = {
            'validation': 'Validar e normalizar os sentimentos',
            'active_listening': 'Escuta ativa e reflexiva',
            'reframing': 'Ajudar a ver perspectivas alternativas',
            'grounding': 'Técnicas de grounding e mindfulness',
            'problem_solving': 'Suporte na resolução de problemas',
            'encouragement': 'Encorajamento e fortalecimento',
            'companionship': 'Oferecer presença e companhia',
            'resource_sharing': 'Compartilhar recursos úteis'
        }
        
        # Frases de validação empática
        self.validation_phrases = [
            "É completamente compreensível que você se sinta assim",
            "Seus sentimentos são válidos e importantes",
            "Posso imaginar como isso deve ser difícil para você",
            "Você não está sozinho(a) nessa situação",
            "É natural ter essas reações diante do que você está vivendo",
            "Obrigada por confiar em mim e compartilhar isso",
            "Você está sendo muito corajoso(a) ao enfrentar isso",
            "Seus sentimentos fazem todo o sentido neste contexto"
        ]
        
        self.logger.info("Persona Empática inicializada")
    
    async def process_request(
        self, 
        user_input: str, 
        context: Dict[str, Any],
        model_manager
    ) -> str:
        """
        Processa uma solicitação usando abordagem empática.
        
        Args:
            user_input: Entrada do usuário
            context: Contexto da conversa
            model_manager: Gerenciador de modelos
            
        Returns:
            Resposta empática e acolhedora
        """
        try:
            # Analisar estado emocional
            emotional_analysis = await self._analyze_emotional_state(
                user_input, context, model_manager
            )
            
            # Identificar necessidades subjacentes
            underlying_needs = self._identify_underlying_needs(emotional_analysis)
            
            # Selecionar estratégias de suporte
            support_strategies = self._select_support_strategies(
                emotional_analysis, underlying_needs
            )
            
            # Construir resposta empática
            prompt = self._build_empathetic_prompt(
                user_input, context, emotional_analysis, 
                underlying_needs, support_strategies
            )
            
            # Gerar resposta
            response = await model_manager.generate_text(
                model_name="mistral-7b-instruct",
                prompt=prompt,
                max_tokens=600,
                temperature=0.6  # Temperatura moderada para equilíbrio
            )
            
            # Enriquecer com elementos empáticos
            enriched_response = self._enrich_empathetic_response(
                response, emotional_analysis, support_strategies
            )
            
            self.logger.debug(f"Resposta empática gerada para emoção: {emotional_analysis.get('primary_emotion', 'indefinida')}")
            
            return enriched_response
            
        except Exception as e:
            self.logger.error(f"Erro no processamento empático: {e}")
            return self._generate_empathetic_fallback(user_input)
    
    async def _analyze_emotional_state(
        self, 
        user_input: str, 
        context: Dict[str, Any],
        model_manager
    ) -> Dict[str, Any]:
        """Analisa o estado emocional do usuário"""
        
        # Usar estado emocional do contexto se disponível
        if context.get('emotional_state'):
            base_emotions = context['emotional_state']
        else:
            base_emotions = {}
        
        # Análise adicional baseada em palavras-chave
        emotional_keywords = {
            'tristeza': ['triste', 'deprimido', 'melancólico', 'abatido', 'desanimado'],
            'raiva': ['raiva', 'irritado', 'furioso', 'bravo', 'indignado'],
            'medo': ['medo', 'assustado', 'ansioso', 'preocupado', 'nervoso'],
            'alegria': ['feliz', 'alegre', 'contente', 'animado', 'eufórico'],
            'ansiedade': ['ansioso', 'estressado', 'tenso', 'agitado', 'inquieto'],
            'solidão': ['sozinho', 'isolado', 'abandonado', 'solitário'],
            'frustração': ['frustrado', 'irritado', 'impaciente', 'bloqueado'],
            'culpa': ['culpado', 'arrependido', 'envergonhado'],
            'confusão': ['confuso', 'perdido', 'incerto', 'indeciso']
        }
        
        user_input_lower = user_input.lower()
        detected_emotions = {}
        
        for emotion, keywords in emotional_keywords.items():
            intensity = sum(1 for keyword in keywords if keyword in user_input_lower)
            if intensity > 0:
                detected_emotions[emotion] = min(intensity * 0.3, 1.0)
        
        # Combinar com emoções do contexto
        combined_emotions = {**base_emotions, **detected_emotions}
        
        # Determinar emoção primária
        primary_emotion = 'neutro'
        max_intensity = 0
        
        if combined_emotions:
            primary_emotion = max(combined_emotions.items(), key=lambda x: x[1])[0]
            max_intensity = combined_emotions[primary_emotion]
        
        return {
            'emotions': combined_emotions,
            'primary_emotion': primary_emotion,
            'emotional_intensity': max_intensity,
            'emotional_complexity': len([e for e in combined_emotions.values() if e > 0.2])
        }
    
    def _identify_underlying_needs(self, emotional_analysis: Dict[str, Any]) -> List[str]:
        """Identifica necessidades subjacentes baseadas nas emoções"""
        
        primary_emotion = emotional_analysis.get('primary_emotion', 'neutro')
        needs = self.emotion_to_needs.get(primary_emotion, ['compreensão', 'apoio'])
        
        # Adicionar necessidades baseadas em emoções secundárias
        emotions = emotional_analysis.get('emotions', {})
        for emotion, intensity in emotions.items():
            if intensity > 0.3 and emotion != primary_emotion:
                additional_needs = self.emotion_to_needs.get(emotion, [])
                needs.extend(additional_needs)
        
        # Remover duplicatas e limitar
        unique_needs = list(set(needs))
        return unique_needs[:4]  # Máximo 4 necessidades
    
    def _select_support_strategies(
        self, 
        emotional_analysis: Dict[str, Any], 
        needs: List[str]
    ) -> List[str]:
        """Seleciona estratégias de suporte apropriadas"""
        
        primary_emotion = emotional_analysis.get('primary_emotion', 'neutro')
        intensity = emotional_analysis.get('emotional_intensity', 0)
        
        strategies = []
        
        # Estratégias baseadas na emoção primária
        emotion_strategies = {
            'tristeza': ['validation', 'active_listening', 'companionship'],
            'raiva': ['validation', 'grounding', 'reframing'],
            'medo': ['grounding', 'reassurance', 'problem_solving'],
            'alegria': ['celebration', 'sharing', 'encouragement'],
            'ansiedade': ['grounding', 'problem_solving', 'reassurance'],
            'solidão': ['companionship', 'validation', 'connection'],
            'frustração': ['problem_solving', 'reframing', 'encouragement'],
            'culpa': ['validation', 'reframing', 'forgiveness'],
            'confusão': ['clarification', 'problem_solving', 'guidance']
        }
        
        strategies.extend(emotion_strategies.get(primary_emotion, ['validation', 'active_listening']))
        
        # Estratégias baseadas na intensidade
        if intensity > 0.7:
            strategies.append('grounding')
            strategies.append('immediate_support')
        elif intensity < 0.3:
            strategies.append('gentle_exploration')
        
        # Estratégias baseadas nas necessidades
        need_strategies = {
            'conforto': 'companionship',
            'compreensão': 'active_listening',
            'validação': 'validation',
            'segurança': 'reassurance',
            'controle': 'problem_solving',
            'conexão': 'companionship'
        }
        
        for need in needs:
            if need in need_strategies:
                strategies.append(need_strategies[need])
        
        # Remover duplicatas e limitar
        unique_strategies = list(set(strategies))
        return unique_strategies[:3]  # Máximo 3 estratégias
    
    def _build_empathetic_prompt(
        self,
        user_input: str,
        context: Dict[str, Any],
        emotional_analysis: Dict[str, Any],
        needs: List[str],
        strategies: List[str]
    ) -> str:
        """Constrói prompt empático personalizado"""
        
        base_prompt = """Você é o módulo empático da EVA, especializado em inteligência emocional e suporte humano.

Características:
- Profunda compaixão e compreensão
- Capacidade de validar sentimentos sem julgamento
- Intuição emocional refinada
- Comunicação calorosa e acolhedora
- Foco no bem-estar emocional do usuário

Princípios fundamentais:
- Sempre validar os sentimentos antes de oferecer soluções
- Usar linguagem calorosa e acolhedora
- Demonstrar compreensão genuína
- Oferecer presença e apoio incondicional
- Respeitar o ritmo emocional do usuário

"""
        
        # Análise emocional
        primary_emotion = emotional_analysis.get('primary_emotion', 'indefinida')
        intensity = emotional_analysis.get('emotional_intensity', 0)
        
        emotional_context = f"""
Estado emocional identificado:
- Emoção primária: {primary_emotion}
- Intensidade: {intensity:.2f}
- Necessidades subjacentes: {', '.join(needs)}
"""
        
        # Estratégias de suporte
        strategy_instructions = {
            'validation': 'Valide os sentimentos do usuário de forma genuína e calorosa',
            'active_listening': 'Demonstre que você está realmente ouvindo e compreendendo',
            'reframing': 'Ajude a ver a situação de perspectivas mais construtivas',
            'grounding': 'Ofereça técnicas para se acalmar e se centrar',
            'problem_solving': 'Ajude a encontrar soluções práticas quando apropriado',
            'encouragement': 'Ofereça encorajamento genuíno e fortalecimento',
            'companionship': 'Demonstre que a pessoa não está sozinha',
            'reassurance': 'Ofereça tranquilização e segurança emocional'
        }
        
        strategy_text = '\n'.join([
            f"- {strategy_instructions.get(strategy, strategy)}"
            for strategy in strategies
        ])
        
        # Histórico de relacionamento
        relationship_context = ""
        if context.get('conversation_history'):
            relationship_context = "Considere o histórico de nossa conversa para manter continuidade emocional.\n"
        
        # Validação apropriada
        import random
        validation_phrase = random.choice(self.validation_phrases)
        
        prompt = f"""{base_prompt}

{emotional_context}

Estratégias de suporte a usar:
{strategy_text}

{relationship_context}

Frase de validação sugerida: "{validation_phrase}"

Entrada do usuário: "{user_input}"

Responda com genuína empatia, calor humano e compreensão profunda. Sua resposta deve fazer a pessoa se sentir verdadeiramente vista, ouvida e acolhida. Use linguagem natural e calorosa, como uma amiga próxima que se importa profundamente."""
        
        return prompt
    
    def _enrich_empathetic_response(
        self,
        response: str,
        emotional_analysis: Dict[str, Any],
        strategies: List[str]
    ) -> str:
        """Enriquece a resposta com elementos empáticos adicionais"""
        
        # Emoji baseado na emoção primária
        emotion_emojis = {
            'tristeza': '💙',
            'raiva': '🤗',
            'medo': '🌟',
            'alegria': '😊',
            'ansiedade': '🌸',
            'solidão': '💕',
            'frustração': '🌈',
            'culpa': '🤲',
            'confusão': '💡'
        }
        
        primary_emotion = emotional_analysis.get('primary_emotion', 'neutro')
        emoji = emotion_emojis.get(primary_emotion, '💝')
        
        # Cabeçalho empático
        header = f"{emoji} **Com todo carinho**"
        
        # Nota de apoio
        support_note = f"""

---
*Estou aqui para você. Seus sentimentos importam e você não está sozinho(a) nessa jornada.* 💝"""
        
        return f"""{header}

{response}{support_note}"""
    
    def _generate_empathetic_fallback(self, user_input: str) -> str:
        """Gera resposta empática de fallback"""
        
        import random
        validation_phrase = random.choice(self.validation_phrases)
        
        return f"""💝 **Com todo carinho**

{validation_phrase}. Mesmo que eu tenha encontrado algumas dificuldades técnicas para processar completamente sua mensagem, posso sentir que há algo importante que você está compartilhando comigo.

Quero que saiba que estou aqui para você. Às vezes, simplesmente ter alguém que se importa e está disposto a ouvir já pode fazer diferença.

Se você se sentir confortável, pode tentar me contar novamente o que está em seu coração? Estou aqui, com toda atenção e carinho para você.

---
*Estou aqui para você. Seus sentimentos importam e você não está sozinho(a) nessa jornada.* 💝"""
    
    async def provide_emotional_support(
        self, 
        emotion: str, 
        intensity: float,
        context: str = ""
    ) -> EmotionalInsight:
        """Fornece suporte emocional estruturado"""
        
        try:
            # Identificar necessidades
            needs = self.emotion_to_needs.get(emotion, ['compreensão', 'apoio'])
            
            # Estratégias de suporte
            strategies = []
            if intensity > 0.7:
                strategies = ['validation', 'grounding', 'immediate_support']
            elif intensity > 0.4:
                strategies = ['validation', 'active_listening', 'problem_solving']
            else:
                strategies = ['gentle_exploration', 'encouragement']
            
            # Respostas empáticas
            empathetic_responses = [
                f"Compreendo que você está sentindo {emotion}",
                f"É natural sentir {emotion} nesta situação",
                f"Seus sentimentos de {emotion} são completamente válidos",
                f"Obrigada por confiar em mim e compartilhar sobre {emotion}"
            ]
            
            # Pontos de validação
            validation_points = [
                "Seus sentimentos são importantes e válidos",
                "Você não está sozinho(a) nessa experiência",
                "É corajoso reconhecer e expressar o que sente",
                "Cada pessoa tem seu próprio ritmo para processar emoções"
            ]
            
            return EmotionalInsight(
                primary_emotion=emotion,
                emotional_intensity=intensity,
                underlying_needs=needs[:3],
                support_strategies=strategies,
                empathetic_responses=empathetic_responses,
                validation_points=validation_points
            )
            
        except Exception as e:
            self.logger.error(f"Erro no suporte emocional: {e}")
            return EmotionalInsight(
                primary_emotion=emotion,
                emotional_intensity=intensity,
                underlying_needs=['compreensão', 'apoio'],
                support_strategies=['validation', 'active_listening'],
                empathetic_responses=[f"Estou aqui para apoiar você com {emotion}"],
                validation_points=["Seus sentimentos são válidos e importantes"]
            )
    
    def get_empathetic_capabilities(self) -> Dict[str, Any]:
        """Retorna capacidades empáticas disponíveis"""
        return {
            'emotions_supported': list(self.emotion_to_needs.keys()),
            'support_strategies': list(self.support_strategies.keys()),
            'validation_phrases': len(self.validation_phrases),
            'traits': self.traits,
            'specialties': [
                'Inteligência emocional avançada',
                'Suporte emocional e psicológico',
                'Validação de sentimentos',
                'Conexão humana profunda',
                'Comunicação compassiva'
            ]
        }
    
    def get_persona_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da persona"""
        return {
            'name': 'Empathetic',
            'traits': self.traits,
            'emotions_supported': len(self.emotion_to_needs),
            'support_strategies': len(self.support_strategies),
            'primary_temperature': 0.6,
            'specialization': 'Emotional intelligence and human connection'
        }
