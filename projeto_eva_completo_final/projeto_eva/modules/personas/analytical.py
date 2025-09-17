"""
Módulo Persona Analítica da EVA.
Especializada em raciocínio lógico, resolução de problemas e análise estruturada.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from utils.logging_system import EVALogger

@dataclass
class AnalysisResult:
    """Resultado de uma análise estruturada"""
    problem_breakdown: List[str]
    logical_steps: List[str]
    evidence: List[str]
    conclusion: str
    confidence_level: float
    assumptions: List[str]

class AnalyticalPersona:
    """
    Persona Analítica da EVA.
    
    Especializada em:
    - Decomposição de problemas complexos
    - Raciocínio lógico estruturado
    - Análise de dados e evidências
    - Pensamento crítico
    - Resolução sistemática de problemas
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = EVALogger.get_logger("AnalyticalPersona")
        
        # Características da persona
        self.traits = {
            'logical': 0.95,
            'systematic': 0.90,
            'detail_oriented': 0.85,
            'objective': 0.90,
            'methodical': 0.88
        }
        
        # Ferramentas analíticas
        self.analysis_frameworks = [
            'root_cause_analysis',
            'swot_analysis',
            'pros_cons_analysis',
            'step_by_step_breakdown',
            'evidence_evaluation'
        ]
        
        self.logger.info("Persona Analítica inicializada")
    
    async def process_request(
        self, 
        user_input: str, 
        context: Dict[str, Any],
        model_manager
    ) -> str:
        """
        Processa uma solicitação usando abordagem analítica.
        
        Args:
            user_input: Entrada do usuário
            context: Contexto da conversa
            model_manager: Gerenciador de modelos
            
        Returns:
            Resposta analítica estruturada
        """
        try:
            # Identificar tipo de problema
            problem_type = self._identify_problem_type(user_input)
            
            # Selecionar framework apropriado
            framework = self._select_analysis_framework(problem_type, user_input)
            
            # Construir prompt analítico
            prompt = self._build_analytical_prompt(user_input, context, framework)
            
            # Gerar análise
            response = await model_manager.generate_text(
                model_name="mistral-7b-instruct",
                prompt=prompt,
                max_tokens=600,
                temperature=0.3  # Baixa temperatura para consistência
            )
            
            # Estruturar resposta
            structured_response = self._structure_analytical_response(response, framework)
            
            self.logger.debug(f"Análise {framework} concluída para: {user_input[:50]}...")
            
            return structured_response
            
        except Exception as e:
            self.logger.error(f"Erro no processamento analítico: {e}")
            return self._generate_fallback_response(user_input)
    
    def _identify_problem_type(self, user_input: str) -> str:
        """Identifica o tipo de problema para análise apropriada"""
        
        user_input_lower = user_input.lower()
        
        # Palavras-chave para diferentes tipos de problemas
        problem_indicators = {
            'decision': ['decidir', 'escolher', 'opção', 'alternativa', 'melhor'],
            'troubleshooting': ['problema', 'erro', 'não funciona', 'falha', 'bug'],
            'analysis': ['analisar', 'avaliar', 'examinar', 'estudar', 'investigar'],
            'planning': ['planejar', 'organizar', 'estratégia', 'cronograma', 'etapas'],
            'comparison': ['comparar', 'diferença', 'versus', 'melhor que', 'vantagens'],
            'explanation': ['explicar', 'como', 'por que', 'razão', 'causa'],
            'calculation': ['calcular', 'matemática', 'número', 'resultado', 'fórmula']
        }
        
        # Contar matches para cada tipo
        type_scores = {}
        for problem_type, keywords in problem_indicators.items():
            score = sum(1 for keyword in keywords if keyword in user_input_lower)
            if score > 0:
                type_scores[problem_type] = score
        
        # Retornar tipo com maior score ou 'general' se nenhum match
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        else:
            return 'general'
    
    def _select_analysis_framework(self, problem_type: str, user_input: str) -> str:
        """Seleciona framework de análise baseado no tipo de problema"""
        
        framework_mapping = {
            'decision': 'pros_cons_analysis',
            'troubleshooting': 'root_cause_analysis',
            'analysis': 'evidence_evaluation',
            'planning': 'step_by_step_breakdown',
            'comparison': 'swot_analysis',
            'explanation': 'step_by_step_breakdown',
            'calculation': 'step_by_step_breakdown',
            'general': 'evidence_evaluation'
        }
        
        return framework_mapping.get(problem_type, 'evidence_evaluation')
    
    def _build_analytical_prompt(
        self, 
        user_input: str, 
        context: Dict[str, Any], 
        framework: str
    ) -> str:
        """Constrói prompt específico para análise"""
        
        base_prompt = """Você é o módulo analítico da EVA, especializado em raciocínio lógico e resolução estruturada de problemas.

Características:
- Pensamento sistemático e metodológico
- Análise baseada em evidências
- Decomposição de problemas complexos
- Objetividade e precisão
- Estruturação clara de informações

"""
        
        framework_prompts = {
            'root_cause_analysis': """
Use análise de causa raiz para investigar o problema:
1. Identifique os sintomas observados
2. Trace as possíveis causas imediatas
3. Investigue as causas fundamentais
4. Proponha soluções direcionadas às causas raiz
""",
            'pros_cons_analysis': """
Use análise de prós e contras para avaliar as opções:
1. Liste todas as alternativas disponíveis
2. Identifique vantagens de cada opção
3. Identifique desvantagens de cada opção
4. Avalie o peso relativo de cada fator
5. Forneça recomendação baseada na análise
""",
            'step_by_step_breakdown': """
Use decomposição passo a passo:
1. Divida o problema/tarefa em componentes menores
2. Ordene os passos logicamente
3. Identifique dependências entre passos
4. Forneça instruções claras para cada etapa
5. Antecipe possíveis obstáculos
""",
            'evidence_evaluation': """
Use avaliação de evidências:
1. Identifique as informações disponíveis
2. Avalie a qualidade e confiabilidade das fontes
3. Identifique lacunas de informação
4. Tire conclusões baseadas nas evidências
5. Indique nível de confiança na análise
""",
            'swot_analysis': """
Use análise SWOT (Forças, Fraquezas, Oportunidades, Ameaças):
1. Identifique pontos fortes internos
2. Identifique fraquezas internas
3. Identifique oportunidades externas
4. Identifique ameaças externas
5. Desenvolva estratégias baseadas na análise
"""
        }
        
        framework_instruction = framework_prompts.get(framework, framework_prompts['evidence_evaluation'])
        
        # Contexto da conversa
        conversation_context = ""
        if context.get('conversation_history'):
            recent_history = context['conversation_history'][-2:]
            conversation_context = "Contexto da conversa:\n" + "\n".join([
                f"Usuário: {entry.get('user', '')}\nEVA: {entry.get('eva', '')}"
                for entry in recent_history
            ]) + "\n\n"
        
        prompt = f"""{base_prompt}

{framework_instruction}

{conversation_context}Pergunta/Problema do usuário: "{user_input}"

Forneça uma análise estruturada, clara e objetiva. Use formatação com marcadores ou numeração para organizar sua resposta."""
        
        return prompt
    
    def _structure_analytical_response(self, response: str, framework: str) -> str:
        """Estrutura a resposta analítica com formatação apropriada"""
        
        # Adicionar cabeçalho baseado no framework
        framework_headers = {
            'root_cause_analysis': '🔍 **Análise de Causa Raiz**',
            'pros_cons_analysis': '⚖️ **Análise de Prós e Contras**',
            'step_by_step_breakdown': '📋 **Análise Passo a Passo**',
            'evidence_evaluation': '🧐 **Avaliação de Evidências**',
            'swot_analysis': '📊 **Análise SWOT**'
        }
        
        header = framework_headers.get(framework, '🧠 **Análise Estruturada**')
        
        # Estruturar resposta
        structured_response = f"""{header}

{response}

---
*Análise realizada pelo módulo analítico da EVA*"""
        
        return structured_response
    
    def _generate_fallback_response(self, user_input: str) -> str:
        """Gera resposta de fallback em caso de erro"""
        return f"""🧠 **Análise Estruturada**

Vou analisar sua questão de forma sistemática:

**Problema identificado:** {user_input}

**Abordagem sugerida:**
1. Primeiro, vamos definir claramente o objetivo
2. Identificar as informações disponíveis
3. Determinar que informações adicionais são necessárias
4. Desenvolver uma estratégia de resolução
5. Implementar e avaliar os resultados

Para uma análise mais detalhada, você poderia fornecer mais contexto sobre:
- Qual é o resultado desejado?
- Que recursos estão disponíveis?
- Existem restrições ou limitações?

---
*Análise realizada pelo módulo analítico da EVA*"""
    
    async def analyze_data_pattern(self, data: List[Dict[str, Any]]) -> AnalysisResult:
        """Analisa padrões em dados estruturados"""
        try:
            # Implementação simplificada de análise de padrões
            patterns = []
            evidence = []
            
            if data:
                # Analisar frequências
                keys = set()
                for item in data:
                    keys.update(item.keys())
                
                for key in keys:
                    values = [item.get(key) for item in data if key in item]
                    if values:
                        patterns.append(f"Campo '{key}': {len(values)} ocorrências")
                        
                        # Análise de tipos
                        types = set(type(v).__name__ for v in values if v is not None)
                        evidence.append(f"Tipos em '{key}': {', '.join(types)}")
            
            return AnalysisResult(
                problem_breakdown=["Análise de padrões em dados estruturados"],
                logical_steps=[
                    "1. Identificar campos disponíveis",
                    "2. Analisar frequência de ocorrência",
                    "3. Verificar tipos de dados",
                    "4. Identificar padrões e anomalias"
                ],
                evidence=evidence,
                conclusion=f"Analisados {len(data)} registros com {len(patterns)} padrões identificados",
                confidence_level=0.8,
                assumptions=["Dados fornecidos são representativos", "Estrutura é consistente"]
            )
            
        except Exception as e:
            self.logger.error(f"Erro na análise de padrões: {e}")
            return AnalysisResult(
                problem_breakdown=["Erro na análise"],
                logical_steps=["Verificar formato dos dados"],
                evidence=[f"Erro: {str(e)}"],
                conclusion="Análise não pôde ser completada",
                confidence_level=0.0,
                assumptions=[]
            )
    
    def get_analysis_capabilities(self) -> Dict[str, Any]:
        """Retorna capacidades analíticas disponíveis"""
        return {
            'frameworks': self.analysis_frameworks,
            'problem_types': [
                'decision_making',
                'troubleshooting', 
                'data_analysis',
                'planning',
                'comparison',
                'explanation',
                'calculation'
            ],
            'traits': self.traits,
            'specialties': [
                'Decomposição de problemas complexos',
                'Raciocínio lógico estruturado',
                'Análise baseada em evidências',
                'Pensamento crítico',
                'Resolução sistemática'
            ]
        }
    
    def get_persona_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da persona"""
        return {
            'name': 'Analytical',
            'traits': self.traits,
            'frameworks_available': len(self.analysis_frameworks),
            'primary_temperature': 0.3,
            'specialization': 'Logical reasoning and structured problem solving'
        }
