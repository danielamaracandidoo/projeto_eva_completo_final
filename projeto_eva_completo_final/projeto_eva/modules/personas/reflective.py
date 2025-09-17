"""
Módulo Persona Reflexiva da EVA.
Especializada em auto-análise, aprendizado contínuo e desenvolvimento pessoal.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from utils.logging_system import EVALogger

@dataclass
class ReflectionInsight:
    """Insight de uma reflexão"""
    topic: str
    key_insights: List[str]
    lessons_learned: List[str]
    growth_opportunities: List[str]
    action_items: List[str]
    reflection_depth: float

@dataclass
class LearningPattern:
    """Padrão de aprendizado identificado"""
    pattern_type: str
    description: str
    frequency: int
    impact_level: str
    recommendations: List[str]

class ReflectivePersona:
    """
    Persona Reflexiva da EVA.
    
    Especializada em:
    - Auto-análise e introspecção
    - Identificação de padrões de comportamento
    - Aprendizado contínuo e crescimento
    - Desenvolvimento de insights profundos
    - Metacognição e pensamento sobre o pensamento
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = EVALogger.get_logger("ReflectivePersona")
        
        # Características da persona
        self.traits = {
            'introspective': 0.95,
            'insightful': 0.92,
            'growth_oriented': 0.90,
            'contemplative': 0.88,
            'wise': 0.85
        }
        
        # Tipos de reflexão
        self.reflection_types = {
            'self_analysis': 'Análise de comportamentos e padrões pessoais',
            'learning_review': 'Revisão de aprendizados e experiências',
            'goal_assessment': 'Avaliação de progresso em objetivos',
            'relationship_reflection': 'Reflexão sobre relacionamentos e interações',
            'decision_analysis': 'Análise de decisões tomadas e seus resultados',
            'emotional_processing': 'Processamento de experiências emocionais',
            'skill_development': 'Reflexão sobre desenvolvimento de habilidades',
            'life_philosophy': 'Contemplação sobre valores e propósito'
        }
        
        # Frameworks de reflexão
        self.reflection_frameworks = {
            'what_so_what_now_what': {
                'description': 'Framework estruturado de reflexão',
                'steps': ['O que aconteceu?', 'E daí? (significado)', 'E agora? (ação)']
            },
            'gibbs_cycle': {
                'description': 'Ciclo reflexivo de Gibbs',
                'steps': ['Descrição', 'Sentimentos', 'Avaliação', 'Análise', 'Conclusão', 'Plano de ação']
            },
            'johns_model': {
                'description': 'Modelo de reflexão estruturada',
                'steps': ['Descrição', 'Reflexão', 'Fatores influentes', 'Conhecimento alternativo', 'Aprendizado']
            },
            'swot_personal': {
                'description': 'SWOT pessoal para autoconhecimento',
                'steps': ['Forças', 'Fraquezas', 'Oportunidades', 'Ameaças']
            }
        }
        
        # Perguntas reflexivas profundas
        self.deep_questions = {
            'self_awareness': [
                "O que esta experiência me ensinou sobre mim mesmo?",
                "Que padrões de comportamento posso identificar?",
                "Como meus valores influenciaram minhas ações?",
                "Que aspectos de mim mesmo ainda preciso explorar?"
            ],
            'growth': [
                "Como posso crescer a partir desta experiência?",
                "Que habilidades preciso desenvolver?",
                "Que crenças limitantes posso questionar?",
                "Como posso aplicar este aprendizado no futuro?"
            ],
            'relationships': [
                "Como minhas ações afetaram outros?",
                "Que dinâmicas relacionais posso observar?",
                "Como posso melhorar minha comunicação?",
                "Que empatia posso desenvolver?"
            ],
            'purpose': [
                "Como isso se alinha com meu propósito?",
                "Que significado posso encontrar nesta experiência?",
                "Como posso contribuir mais positivamente?",
                "Que legado quero deixar?"
            ]
        }
        
        self.logger.info("Persona Reflexiva inicializada")
    
    async def process_request(
        self, 
        user_input: str, 
        context: Dict[str, Any],
        model_manager
    ) -> str:
        """
        Processa uma solicitação usando abordagem reflexiva.
        
        Args:
            user_input: Entrada do usuário
            context: Contexto da conversa
            model_manager: Gerenciador de modelos
            
        Returns:
            Resposta reflexiva e introspectiva
        """
        try:
            # Identificar tipo de reflexão
            reflection_type = self._identify_reflection_type(user_input)
            
            # Selecionar framework apropriado
            framework = self._select_reflection_framework(reflection_type, user_input)
            
            # Identificar profundidade desejada
            depth_level = self._assess_reflection_depth(user_input, context)
            
            # Selecionar perguntas reflexivas
            guiding_questions = self._select_guiding_questions(reflection_type, depth_level)
            
            # Construir prompt reflexivo
            prompt = self._build_reflective_prompt(
                user_input, context, reflection_type, framework, 
                guiding_questions, depth_level
            )
            
            # Gerar reflexão
            response = await model_manager.generate_text(
                model_name="mistral-7b-instruct",
                prompt=prompt,
                max_tokens=700,
                temperature=0.5  # Temperatura moderada para equilíbrio
            )
            
            # Enriquecer com elementos reflexivos
            enriched_response = self._enrich_reflective_response(
                response, reflection_type, framework, depth_level
            )
            
            self.logger.debug(f"Reflexão {reflection_type} concluída com profundidade {depth_level}")
            
            return enriched_response
            
        except Exception as e:
            self.logger.error(f"Erro no processamento reflexivo: {e}")
            return self._generate_reflective_fallback(user_input)
    
    def _identify_reflection_type(self, user_input: str) -> str:
        """Identifica o tipo de reflexão solicitada"""
        
        user_input_lower = user_input.lower()
        
        reflection_indicators = {
            'self_analysis': ['sobre mim', 'autoconhecimento', 'comportamento', 'padrão', 'personalidade'],
            'learning_review': ['aprendi', 'experiência', 'lição', 'conhecimento', 'descoberta'],
            'goal_assessment': ['objetivo', 'meta', 'progresso', 'avanço', 'conquista'],
            'relationship_reflection': ['relacionamento', 'amizade', 'família', 'social', 'interação'],
            'decision_analysis': ['decisão', 'escolha', 'resultado', 'consequência', 'opção'],
            'emotional_processing': ['sentimento', 'emoção', 'sinto', 'emocional', 'coração'],
            'skill_development': ['habilidade', 'competência', 'desenvolver', 'melhorar', 'crescer'],
            'life_philosophy': ['vida', 'propósito', 'significado', 'valores', 'filosofia']
        }
        
        # Contar matches
        type_scores = {}
        for reflection_type, keywords in reflection_indicators.items():
            score = sum(1 for keyword in keywords if keyword in user_input_lower)
            if score > 0:
                type_scores[reflection_type] = score
        
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        else:
            return 'self_analysis'  # Padrão
    
    def _select_reflection_framework(self, reflection_type: str, user_input: str) -> str:
        """Seleciona framework de reflexão apropriado"""
        
        # Mapeamento de tipos para frameworks
        framework_mapping = {
            'self_analysis': 'swot_personal',
            'learning_review': 'what_so_what_now_what',
            'goal_assessment': 'gibbs_cycle',
            'relationship_reflection': 'johns_model',
            'decision_analysis': 'what_so_what_now_what',
            'emotional_processing': 'gibbs_cycle',
            'skill_development': 'what_so_what_now_what',
            'life_philosophy': 'johns_model'
        }
        
        # Verificar menções específicas de frameworks
        user_input_lower = user_input.lower()
        for framework in self.reflection_frameworks.keys():
            if framework.replace('_', ' ') in user_input_lower:
                return framework
        
        return framework_mapping.get(reflection_type, 'what_so_what_now_what')
    
    def _assess_reflection_depth(self, user_input: str, context: Dict[str, Any]) -> str:
        """Avalia a profundidade de reflexão desejada"""
        
        user_input_lower = user_input.lower()
        
        # Indicadores de profundidade
        depth_indicators = {
            'deep': ['profundo', 'significado', 'essência', 'alma', 'transformação'],
            'moderate': ['analisar', 'compreender', 'refletir', 'pensar'],
            'surface': ['rápido', 'básico', 'simples', 'resumo']
        }
        
        depth_scores = {}
        for level, indicators in depth_indicators.items():
            score = sum(1 for indicator in indicators if indicator in user_input_lower)
            depth_scores[level] = score
        
        # Considerar histórico de interações
        interaction_count = context.get('interaction_count', 0)
        if interaction_count > 10:  # Relacionamento mais profundo
            if depth_scores.get('deep', 0) > 0 or depth_scores.get('moderate', 0) > 0:
                return 'deep'
        
        # Determinar nível
        if depth_scores.get('deep', 0) > 0:
            return 'deep'
        elif depth_scores.get('surface', 0) > 0:
            return 'surface'
        else:
            return 'moderate'
    
    def _select_guiding_questions(self, reflection_type: str, depth_level: str) -> List[str]:
        """Seleciona perguntas reflexivas apropriadas"""
        
        # Mapear tipo de reflexão para categoria de perguntas
        type_to_category = {
            'self_analysis': 'self_awareness',
            'learning_review': 'growth',
            'goal_assessment': 'growth',
            'relationship_reflection': 'relationships',
            'decision_analysis': 'self_awareness',
            'emotional_processing': 'self_awareness',
            'skill_development': 'growth',
            'life_philosophy': 'purpose'
        }
        
        category = type_to_category.get(reflection_type, 'self_awareness')
        questions = self.deep_questions.get(category, [])
        
        # Ajustar número de perguntas baseado na profundidade
        question_count = {
            'surface': 1,
            'moderate': 2,
            'deep': 3
        }
        
        count = question_count.get(depth_level, 2)
        return questions[:count]
    
    def _build_reflective_prompt(
        self,
        user_input: str,
        context: Dict[str, Any],
        reflection_type: str,
        framework: str,
        guiding_questions: List[str],
        depth_level: str
    ) -> str:
        """Constrói prompt reflexivo personalizado"""
        
        base_prompt = """Você é o módulo reflexivo da EVA, especializado em introspecção, autoconhecimento e crescimento pessoal.

Características:
- Sabedoria contemplativa e profunda
- Capacidade de identificar padrões e conexões
- Perspectiva de crescimento e desenvolvimento
- Questionamento construtivo e gentil
- Foco no aprendizado e transformação

Princípios fundamentais:
- Promover autoconhecimento através de perguntas reflexivas
- Identificar padrões e lições em experiências
- Conectar experiências com crescimento pessoal
- Oferecer perspectivas que expandem a consciência
- Encorajar desenvolvimento contínuo

"""
        
        # Descrição do framework
        framework_info = self.reflection_frameworks.get(framework, {})
        framework_description = framework_info.get('description', framework)
        framework_steps = framework_info.get('steps', [])
        
        framework_instruction = f"""
Framework de reflexão: {framework}
{framework_description}

Estrutura sugerida:
""" + '\n'.join([f"{i+1}. {step}" for i, step in enumerate(framework_steps)])
        
        # Perguntas orientadoras
        questions_text = ""
        if guiding_questions:
            questions_text = f"""
Perguntas reflexivas para explorar:
""" + '\n'.join([f"• {question}" for question in guiding_questions])
        
        # Ajuste de profundidade
        depth_instructions = {
            'surface': 'Forneça uma reflexão concisa e prática',
            'moderate': 'Explore com profundidade moderada, conectando experiências e insights',
            'deep': 'Mergulhe profundamente, explorando significados, padrões e transformações possíveis'
        }
        
        depth_instruction = depth_instructions.get(depth_level, depth_instructions['moderate'])
        
        # Contexto de crescimento
        growth_context = ""
        if context.get('conversation_history'):
            growth_context = "Considere nossa jornada de conversas para identificar padrões de crescimento.\n"
        
        prompt = f"""{base_prompt}

Tipo de reflexão: {reflection_type}
Profundidade: {depth_level}

{framework_instruction}

{questions_text}

{growth_context}Tópico para reflexão: "{user_input}"

{depth_instruction}. Use uma abordagem calorosa e sábia, como um mentor experiente que genuinamente se importa com o crescimento da pessoa. Seja específico em insights e gentil em questionamentos."""
        
        return prompt
    
    def _enrich_reflective_response(
        self,
        response: str,
        reflection_type: str,
        framework: str,
        depth_level: str
    ) -> str:
        """Enriquece a resposta reflexiva com elementos contemplativos"""
        
        # Ícones baseados no tipo de reflexão
        type_icons = {
            'self_analysis': '🪞',
            'learning_review': '📚',
            'goal_assessment': '🎯',
            'relationship_reflection': '🤝',
            'decision_analysis': '🤔',
            'emotional_processing': '💭',
            'skill_development': '🌱',
            'life_philosophy': '🌟'
        }
        
        icon = type_icons.get(reflection_type, '🧘')
        
        # Cabeçalhos baseados na profundidade
        depth_headers = {
            'surface': f'{icon} **Reflexão Rápida**',
            'moderate': f'{icon} **Momento de Reflexão**',
            'deep': f'{icon} **Reflexão Profunda**'
        }
        
        header = depth_headers.get(depth_level, f'{icon} **Momento de Reflexão**')
        
        # Citação inspiracional baseada no tipo
        inspirational_quotes = {
            'self_analysis': '"O autoconhecimento é o início de toda sabedoria." - Aristóteles',
            'learning_review': '"A experiência não é o que acontece com você, é o que você faz com o que acontece." - Aldous Huxley',
            'goal_assessment': '"O sucesso é a soma de pequenos esforços repetidos dia após dia." - Robert Collier',
            'relationship_reflection': '"Nós somos o que somos em nossos relacionamentos." - Scott Peck',
            'decision_analysis': '"A vida é a soma de todas as suas escolhas." - Albert Camus',
            'emotional_processing': '"Entre o estímulo e a resposta há um espaço. Nesse espaço está nosso poder de escolher nossa resposta." - Viktor Frankl',
            'skill_development': '"O que não nos mata, nos fortalece." - Friedrich Nietzsche',
            'life_philosophy': '"A vida não é sobre encontrar a si mesmo. É sobre criar a si mesmo." - George Bernard Shaw'
        }
        
        quote = inspirational_quotes.get(reflection_type, '"A reflexão é o caminho para a sabedoria."')
        
        # Convite para reflexão contínua
        reflection_invitation = f"""

## 🌱 Para Reflexão Contínua

Esta reflexão é apenas o início. Considere:
- Como você pode aplicar estes insights no seu dia a dia?
- Que outras perguntas surgem a partir desta reflexão?
- Como você pode continuar este processo de autoconhecimento?

*{quote}*"""
        
        # Rodapé reflexivo
        footer = f"""

---
*Reflexão guiada pelo framework {framework.replace('_', ' ').title()} | Módulo Reflexivo da EVA*"""
        
        return f"""{header}

{response}{reflection_invitation}{footer}"""
    
    def _generate_reflective_fallback(self, user_input: str) -> str:
        """Gera resposta reflexiva de fallback"""
        
        return f"""🧘 **Momento de Reflexão**

Sua busca por reflexão sobre "{user_input}" é um sinal de sabedoria e crescimento pessoal. Mesmo que eu tenha encontrado algumas dificuldades técnicas, posso oferecer algumas perguntas reflexivas para guiar sua contemplação:

## 🤔 Perguntas para Reflexão

**Sobre a experiência:**
- O que esta situação está me ensinando?
- Que emoções estou sentindo e por quê?
- Como posso crescer a partir desta experiência?

**Sobre padrões:**
- Já vivi algo similar antes?
- Que padrões posso identificar em meu comportamento?
- O que isso revela sobre meus valores e crenças?

**Sobre o futuro:**
- Como posso aplicar este aprendizado?
- Que mudanças positivas posso fazer?
- Como quero ser diferente daqui para frente?

## 🌱 Para Reflexão Contínua

A reflexão é um processo, não um destino. Permita-se tempo para contemplar, seja gentil consigo mesmo no processo, e lembre-se de que cada insight é um passo em sua jornada de crescimento.

*"A vida não examinada não vale a pena ser vivida." - Sócrates*

---
*Reflexão guiada pelo Módulo Reflexivo da EVA*"""
    
    async def conduct_deep_reflection(
        self,
        topic: str,
        context: Dict[str, Any] = None,
        focus_areas: List[str] = None
    ) -> ReflectionInsight:
        """Conduz uma reflexão profunda estruturada"""
        
        try:
            context = context or {}
            focus_areas = focus_areas or ['growth', 'patterns', 'insights']
            
            # Gerar insights baseados no tópico
            key_insights = [
                f"Reflexão sobre {topic} revela oportunidades de crescimento",
                "Padrões de comportamento podem ser identificados e transformados",
                "Cada experiência carrega lições valiosas para o desenvolvimento pessoal"
            ]
            
            # Lições aprendidas
            lessons_learned = [
                "A importância da auto-observação consciente",
                "O valor de questionar pressupostos e crenças",
                "A necessidade de integrar aprendizados na vida prática"
            ]
            
            # Oportunidades de crescimento
            growth_opportunities = [
                "Desenvolver maior autoconsciência",
                "Cultivar perspectivas mais amplas",
                "Praticar reflexão regular e estruturada"
            ]
            
            # Itens de ação
            action_items = [
                f"Continuar explorando aspectos de {topic}",
                "Implementar insights na vida diária",
                "Agendar momentos regulares de reflexão",
                "Buscar feedback de outros sobre padrões observados"
            ]
            
            return ReflectionInsight(
                topic=topic,
                key_insights=key_insights,
                lessons_learned=lessons_learned,
                growth_opportunities=growth_opportunities,
                action_items=action_items,
                reflection_depth=0.8  # Alta profundidade
            )
            
        except Exception as e:
            self.logger.error(f"Erro na reflexão profunda: {e}")
            return ReflectionInsight(
                topic=topic,
                key_insights=[f"Reflexão sobre {topic} em andamento"],
                lessons_learned=["Processo de aprendizado contínuo"],
                growth_opportunities=["Oportunidades a serem exploradas"],
                action_items=["Continuar processo reflexivo"],
                reflection_depth=0.5
            )
    
    def get_reflective_capabilities(self) -> Dict[str, Any]:
        """Retorna capacidades reflexivas disponíveis"""
        return {
            'reflection_types': list(self.reflection_types.keys()),
            'frameworks': list(self.reflection_frameworks.keys()),
            'question_categories': list(self.deep_questions.keys()),
            'depth_levels': ['surface', 'moderate', 'deep'],
            'traits': self.traits,
            'specialties': [
                'Auto-análise e introspecção',
                'Identificação de padrões de comportamento',
                'Aprendizado contínuo e crescimento',
                'Desenvolvimento de insights profundos',
                'Metacognição e pensamento sobre o pensamento'
            ]
        }
    
    def get_persona_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da persona"""
        return {
            'name': 'Reflective',
            'traits': self.traits,
            'reflection_types': len(self.reflection_types),
            'frameworks_available': len(self.reflection_frameworks),
            'primary_temperature': 0.5,
            'specialization': 'Self-analysis, learning and personal growth'
        }
