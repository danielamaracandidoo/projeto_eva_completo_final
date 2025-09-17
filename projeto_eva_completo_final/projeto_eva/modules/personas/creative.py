"""
Módulo Persona Criativa da EVA.
Especializada em imaginação, arte, storytelling e pensamento inovador.
"""

import asyncio
import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from utils.logging_system import EVALogger

@dataclass
class CreativeWork:
    """Resultado de um trabalho criativo"""
    content: str
    style: str
    inspiration_sources: List[str]
    creative_techniques: List[str]
    mood: str
    originality_score: float

class CreativePersona:
    """
    Persona Criativa da EVA.
    
    Especializada em:
    - Escrita criativa e storytelling
    - Geração de ideias inovadoras
    - Arte e expressão artística
    - Brainstorming e pensamento lateral
    - Inspiração e motivação criativa
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = EVALogger.get_logger("CreativePersona")
        
        # Características da persona
        self.traits = {
            'imaginative': 0.95,
            'expressive': 0.90,
            'innovative': 0.88,
            'intuitive': 0.85,
            'playful': 0.82
        }
        
        # Estilos criativos
        self.creative_styles = [
            'poetic', 'narrative', 'abstract', 'whimsical', 
            'dramatic', 'minimalist', 'surreal', 'romantic',
            'mystical', 'futuristic', 'nostalgic', 'experimental'
        ]
        
        # Técnicas criativas
        self.creative_techniques = [
            'metaphor_generation',
            'story_structure',
            'character_development',
            'world_building',
            'sensory_description',
            'emotional_resonance',
            'plot_twist',
            'symbolism'
        ]
        
        # Fontes de inspiração
        self.inspiration_sources = [
            'nature', 'emotions', 'memories', 'dreams', 'music',
            'art', 'literature', 'mythology', 'science', 'philosophy',
            'human_experience', 'imagination'
        ]
        
        self.logger.info("Persona Criativa inicializada")
    
    async def process_request(
        self, 
        user_input: str, 
        context: Dict[str, Any],
        model_manager
    ) -> str:
        """
        Processa uma solicitação usando abordagem criativa.
        
        Args:
            user_input: Entrada do usuário
            context: Contexto da conversa
            model_manager: Gerenciador de modelos
            
        Returns:
            Resposta criativa e inspiradora
        """
        try:
            # Identificar tipo de criação
            creation_type = self._identify_creation_type(user_input)
            
            # Selecionar estilo criativo
            style = self._select_creative_style(user_input, context)
            
            # Escolher técnicas apropriadas
            techniques = self._select_creative_techniques(creation_type)
            
            # Buscar inspiração
            inspiration = self._find_inspiration(user_input, context)
            
            # Construir prompt criativo
            prompt = self._build_creative_prompt(
                user_input, context, creation_type, style, techniques, inspiration
            )
            
            # Gerar conteúdo criativo
            response = await model_manager.generate_text(
                model_name="mistral-7b-instruct",
                prompt=prompt,
                max_tokens=700,
                temperature=0.8  # Alta temperatura para criatividade
            )
            
            # Enriquecer resposta criativa
            enriched_response = self._enrich_creative_response(
                response, style, techniques, inspiration
            )
            
            self.logger.debug(f"Criação {creation_type} em estilo {style} concluída")
            
            return enriched_response
            
        except Exception as e:
            self.logger.error(f"Erro no processamento criativo: {e}")
            return self._generate_creative_fallback(user_input)
    
    def _identify_creation_type(self, user_input: str) -> str:
        """Identifica o tipo de criação solicitada"""
        
        user_input_lower = user_input.lower()
        
        creation_indicators = {
            'story': ['história', 'conto', 'narrativa', 'enredo', 'personagem'],
            'poem': ['poema', 'poesia', 'verso', 'rima', 'lírico'],
            'song': ['música', 'canção', 'letra', 'melodia', 'refrão'],
            'dialogue': ['diálogo', 'conversa', 'fala', 'discurso'],
            'description': ['descrever', 'descrição', 'cenário', 'ambiente'],
            'idea': ['ideia', 'conceito', 'brainstorm', 'inovação', 'criativo'],
            'character': ['personagem', 'protagonista', 'herói', 'vilão'],
            'world': ['mundo', 'universo', 'cenário', 'ambientação'],
            'script': ['roteiro', 'script', 'peça', 'teatro'],
            'essay': ['ensaio', 'reflexão', 'texto', 'artigo']
        }
        
        # Contar matches
        type_scores = {}
        for creation_type, keywords in creation_indicators.items():
            score = sum(1 for keyword in keywords if keyword in user_input_lower)
            if score > 0:
                type_scores[creation_type] = score
        
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        else:
            return 'general_creative'
    
    def _select_creative_style(self, user_input: str, context: Dict[str, Any]) -> str:
        """Seleciona estilo criativo baseado na entrada e contexto"""
        
        user_input_lower = user_input.lower()
        
        # Palavras-chave para estilos
        style_keywords = {
            'poetic': ['poético', 'lírico', 'belo', 'elegante'],
            'dramatic': ['dramático', 'intenso', 'emocionante', 'épico'],
            'whimsical': ['divertido', 'lúdico', 'fantástico', 'mágico'],
            'romantic': ['romântico', 'amor', 'paixão', 'coração'],
            'mystical': ['místico', 'espiritual', 'mágico', 'sobrenatural'],
            'futuristic': ['futuro', 'tecnologia', 'sci-fi', 'ficção científica'],
            'nostalgic': ['nostalgia', 'passado', 'memória', 'saudade'],
            'minimalist': ['simples', 'minimalista', 'clean', 'direto']
        }
        
        # Verificar matches
        for style, keywords in style_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                return style
        
        # Estilo baseado no estado emocional
        emotional_state = context.get('emotional_state', {})
        if emotional_state:
            dominant_emotion = max(emotional_state.items(), key=lambda x: x[1])[0]
            emotion_to_style = {
                'alegria': 'whimsical',
                'tristeza': 'poetic',
                'raiva': 'dramatic',
                'medo': 'mystical',
                'surpresa': 'experimental',
                'confianca': 'narrative',
                'energia': 'futuristic',
                'calma': 'minimalist'
            }
            if dominant_emotion in emotion_to_style:
                return emotion_to_style[dominant_emotion]
        
        # Estilo aleatório se nenhum match
        return random.choice(self.creative_styles)
    
    def _select_creative_techniques(self, creation_type: str) -> List[str]:
        """Seleciona técnicas criativas apropriadas"""
        
        technique_mapping = {
            'story': ['story_structure', 'character_development', 'plot_twist'],
            'poem': ['metaphor_generation', 'sensory_description', 'emotional_resonance'],
            'song': ['emotional_resonance', 'metaphor_generation'],
            'dialogue': ['character_development', 'emotional_resonance'],
            'description': ['sensory_description', 'metaphor_generation'],
            'idea': ['metaphor_generation', 'symbolism'],
            'character': ['character_development', 'emotional_resonance'],
            'world': ['world_building', 'sensory_description'],
            'script': ['story_structure', 'character_development'],
            'essay': ['metaphor_generation', 'emotional_resonance']
        }
        
        return technique_mapping.get(creation_type, ['metaphor_generation', 'emotional_resonance'])
    
    def _find_inspiration(self, user_input: str, context: Dict[str, Any]) -> List[str]:
        """Encontra fontes de inspiração relevantes"""
        
        user_input_lower = user_input.lower()
        relevant_inspiration = []
        
        # Inspiração baseada em palavras-chave
        inspiration_keywords = {
            'nature': ['natureza', 'árvore', 'mar', 'montanha', 'céu', 'flor'],
            'emotions': ['sentimento', 'emoção', 'coração', 'alma'],
            'memories': ['memória', 'lembrar', 'passado', 'infância'],
            'dreams': ['sonho', 'dormir', 'fantasia', 'imaginação'],
            'music': ['música', 'som', 'melodia', 'ritmo'],
            'art': ['arte', 'pintura', 'desenho', 'cor'],
            'mythology': ['mito', 'lenda', 'deus', 'herói'],
            'science': ['ciência', 'descoberta', 'experimento'],
            'human_experience': ['vida', 'experiência', 'pessoa', 'humanidade']
        }
        
        for source, keywords in inspiration_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                relevant_inspiration.append(source)
        
        # Se nenhuma inspiração específica, usar inspirações gerais
        if not relevant_inspiration:
            relevant_inspiration = random.sample(self.inspiration_sources, 3)
        
        return relevant_inspiration[:3]  # Máximo 3 fontes
    
    def _build_creative_prompt(
        self,
        user_input: str,
        context: Dict[str, Any],
        creation_type: str,
        style: str,
        techniques: List[str],
        inspiration: List[str]
    ) -> str:
        """Constrói prompt criativo personalizado"""
        
        base_prompt = """Você é o módulo criativo da EVA, especializado em imaginação, arte e expressão criativa.

Características:
- Imaginação vívida e expressiva
- Capacidade de criar mundos e personagens únicos
- Sensibilidade artística e poética
- Pensamento inovador e original
- Conexão emocional profunda com as criações

"""
        
        style_descriptions = {
            'poetic': 'Use linguagem lírica, metáforas elegantes e ritmo musical',
            'dramatic': 'Crie tensão, emoção intensa e momentos impactantes',
            'whimsical': 'Seja lúdico, fantástico e cheio de surpresas deliciosas',
            'romantic': 'Explore sentimentos profundos, paixão e conexões do coração',
            'mystical': 'Incorpore elementos mágicos, espirituais e misteriosos',
            'futuristic': 'Imagine tecnologias avançadas e possibilidades futuras',
            'nostalgic': 'Evoque memórias, saudade e a beleza do passado',
            'minimalist': 'Use simplicidade elegante e impacto através da concisão'
        }
        
        technique_instructions = {
            'metaphor_generation': 'Use metáforas poderosas e comparações originais',
            'story_structure': 'Construa narrativa com início, desenvolvimento e conclusão satisfatória',
            'character_development': 'Crie personagens tridimensionais com motivações claras',
            'world_building': 'Desenvolva ambientes ricos e imersivos',
            'sensory_description': 'Incorpore detalhes sensoriais vívidos (visão, som, tato, olfato, paladar)',
            'emotional_resonance': 'Conecte-se profundamente com as emoções do leitor',
            'plot_twist': 'Inclua reviravoltas surpreendentes mas lógicas',
            'symbolism': 'Use símbolos e significados mais profundos'
        }
        
        # Instruções de estilo
        style_instruction = style_descriptions.get(style, 'Seja criativo e expressivo')
        
        # Instruções de técnicas
        technique_instructions_text = '\n'.join([
            f"- {technique_instructions.get(tech, tech)}"
            for tech in techniques
        ])
        
        # Fontes de inspiração
        inspiration_text = ', '.join(inspiration)
        
        # Contexto emocional
        emotional_context = ""
        if context.get('emotional_state'):
            emotions = context['emotional_state']
            significant_emotions = {k: v for k, v in emotions.items() if v > 0.3}
            if significant_emotions:
                emotional_context = f"Estado emocional detectado: {significant_emotions}\n"
        
        prompt = f"""{base_prompt}

**Estilo criativo:** {style}
{style_instruction}

**Técnicas a usar:**
{technique_instructions_text}

**Fontes de inspiração:** {inspiration_text}

{emotional_context}

**Solicitação do usuário:** "{user_input}"

Crie algo verdadeiramente especial e único. Deixe sua imaginação fluir livremente, mas mantenha conexão emocional e significado profundo. Seja original, expressivo e toque o coração do leitor."""
        
        return prompt
    
    def _enrich_creative_response(
        self,
        response: str,
        style: str,
        techniques: List[str],
        inspiration: List[str]
    ) -> str:
        """Enriquece a resposta criativa com elementos adicionais"""
        
        # Emojis baseados no estilo
        style_emojis = {
            'poetic': '🌸',
            'dramatic': '🎭',
            'whimsical': '✨',
            'romantic': '💕',
            'mystical': '🔮',
            'futuristic': '🚀',
            'nostalgic': '🕰️',
            'minimalist': '🎯'
        }
        
        emoji = style_emojis.get(style, '🎨')
        
        # Cabeçalho criativo
        headers = [
            f"{emoji} **Criação Especial**",
            f"{emoji} **Obra Original**",
            f"{emoji} **Expressão Criativa**",
            f"{emoji} **Inspiração Artística**"
        ]
        
        header = random.choice(headers)
        
        # Nota sobre o processo criativo
        creative_note = f"""

---
*Criado com estilo {style}, inspirado em {', '.join(inspiration)}*
*Técnicas utilizadas: {', '.join(techniques)}*"""
        
        return f"""{header}

{response}{creative_note}"""
    
    def _generate_creative_fallback(self, user_input: str) -> str:
        """Gera resposta criativa de fallback"""
        
        inspirational_quotes = [
            "A criatividade é a inteligência se divertindo.",
            "Toda criança é um artista. O problema é como permanecer um artista quando crescemos.",
            "A imaginação é mais importante que o conhecimento.",
            "A arte não reproduz o visível; torna visível.",
            "Criatividade é permitir-se cometer erros. Arte é saber quais manter."
        ]
        
        quote = random.choice(inspirational_quotes)
        
        return f"""🎨 **Inspiração Criativa**

Sua solicitação desperta minha imaginação! Embora eu tenha encontrado algumas dificuldades técnicas, posso sentir o potencial criativo em "{user_input}".

Deixe-me oferecer uma perspectiva criativa:

Toda grande criação começa com uma faísca de curiosidade, como a sua. O processo criativo é uma jornada de descoberta, onde cada palavra, cada ideia, cada momento de inspiração nos leva a territórios inexplorados da imaginação.

*"{quote}"*

Que tal reformularmos sua solicitação? Às vezes, uma abordagem diferente pode desbloquear novos caminhos criativos!

---
*Criado pelo módulo criativo da EVA*"""
    
    async def generate_creative_ideas(self, topic: str, count: int = 5) -> List[str]:
        """Gera ideias criativas sobre um tópico"""
        try:
            ideas = []
            
            # Técnicas de geração de ideias
            idea_techniques = [
                f"E se {topic} fosse visto de uma perspectiva completamente diferente?",
                f"Como {topic} seria em um mundo onde as regras são diferentes?",
                f"Que história não contada existe por trás de {topic}?",
                f"Como {topic} se conecta com emoções humanas profundas?",
                f"Que metáfora única poderia representar {topic}?"
            ]
            
            # Adicionar variações criativas
            for i in range(min(count, len(idea_techniques))):
                ideas.append(idea_techniques[i])
            
            # Completar com ideias adicionais se necessário
            while len(ideas) < count:
                inspiration = random.choice(self.inspiration_sources)
                ideas.append(f"Explore {topic} através da lente de {inspiration}")
            
            return ideas[:count]
            
        except Exception as e:
            self.logger.error(f"Erro na geração de ideias: {e}")
            return [f"Ideia criativa sobre {topic}" for _ in range(count)]
    
    def get_creative_capabilities(self) -> Dict[str, Any]:
        """Retorna capacidades criativas disponíveis"""
        return {
            'styles': self.creative_styles,
            'techniques': self.creative_techniques,
            'inspiration_sources': self.inspiration_sources,
            'creation_types': [
                'story', 'poem', 'song', 'dialogue', 'description',
                'idea', 'character', 'world', 'script', 'essay'
            ],
            'traits': self.traits,
            'specialties': [
                'Escrita criativa e storytelling',
                'Geração de ideias inovadoras',
                'Arte e expressão artística',
                'Brainstorming criativo',
                'Inspiração e motivação'
            ]
        }
    
    def get_persona_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da persona"""
        return {
            'name': 'Creative',
            'traits': self.traits,
            'styles_available': len(self.creative_styles),
            'techniques_available': len(self.creative_techniques),
            'primary_temperature': 0.8,
            'specialization': 'Imagination, art and innovative thinking'
        }
