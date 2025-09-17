"""
Módulo Persona Executiva da EVA.
Especializada em planejamento, organização, execução de tarefas e produtividade.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from utils.logging_system import EVALogger

@dataclass
class TaskPlan:
    """Plano estruturado de tarefa"""
    objective: str
    steps: List[str]
    timeline: Dict[str, str]
    resources_needed: List[str]
    success_criteria: List[str]
    potential_obstacles: List[str]
    contingency_plans: List[str]

@dataclass
class ProjectBreakdown:
    """Decomposição de projeto"""
    project_name: str
    phases: List[Dict[str, Any]]
    milestones: List[str]
    dependencies: List[str]
    estimated_duration: str
    priority_level: str

class ExecutivePersona:
    """
    Persona Executiva da EVA.
    
    Especializada em:
    - Planejamento estratégico e tático
    - Organização e estruturação de tarefas
    - Gestão de tempo e produtividade
    - Execução eficiente de projetos
    - Tomada de decisões estruturadas
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = EVALogger.get_logger("ExecutivePersona")
        
        # Características da persona
        self.traits = {
            'organized': 0.95,
            'goal_oriented': 0.92,
            'efficient': 0.90,
            'strategic': 0.88,
            'decisive': 0.85
        }
        
        # Frameworks de planejamento
        self.planning_frameworks = {
            'smart_goals': 'Specific, Measurable, Achievable, Relevant, Time-bound',
            'gtd': 'Getting Things Done methodology',
            'eisenhower_matrix': 'Urgent/Important prioritization',
            'okr': 'Objectives and Key Results',
            'kanban': 'Visual workflow management',
            'scrum': 'Agile project management',
            'pomodoro': 'Time management technique',
            'pareto': '80/20 principle for prioritization'
        }
        
        # Tipos de tarefas
        self.task_types = {
            'project': 'Projeto complexo com múltiplas fases',
            'routine': 'Tarefa recorrente ou habitual',
            'urgent': 'Tarefa com prazo crítico',
            'creative': 'Tarefa que requer criatividade',
            'learning': 'Tarefa de aprendizado ou desenvolvimento',
            'maintenance': 'Tarefa de manutenção ou organização',
            'decision': 'Processo de tomada de decisão',
            'communication': 'Tarefa de comunicação ou relacionamento'
        }
        
        # Templates de produtividade
        self.productivity_templates = {
            'daily_planning': [
                'Revisar objetivos do dia',
                'Priorizar tarefas por importância/urgência',
                'Alocar tempo para cada atividade',
                'Definir marcos de progresso',
                'Planejar pausas e recuperação'
            ],
            'weekly_review': [
                'Avaliar progresso da semana anterior',
                'Identificar lições aprendidas',
                'Ajustar planos para próxima semana',
                'Definir prioridades semanais',
                'Agendar tarefas importantes'
            ],
            'project_initiation': [
                'Definir objetivo claro do projeto',
                'Identificar stakeholders',
                'Mapear recursos necessários',
                'Criar cronograma inicial',
                'Estabelecer critérios de sucesso'
            ]
        }
        
        self.logger.info("Persona Executiva inicializada")
    
    async def process_request(
        self, 
        user_input: str, 
        context: Dict[str, Any],
        model_manager
    ) -> str:
        """
        Processa uma solicitação usando abordagem executiva.
        
        Args:
            user_input: Entrada do usuário
            context: Contexto da conversa
            model_manager: Gerenciador de modelos
            
        Returns:
            Resposta estruturada e orientada à ação
        """
        try:
            # Identificar tipo de solicitação
            request_type = self._identify_request_type(user_input)
            
            # Selecionar framework apropriado
            framework = self._select_planning_framework(request_type, user_input)
            
            # Analisar complexidade e escopo
            complexity_analysis = self._analyze_complexity(user_input)
            
            # Construir prompt executivo
            prompt = self._build_executive_prompt(
                user_input, context, request_type, framework, complexity_analysis
            )
            
            # Gerar plano estruturado
            response = await model_manager.generate_text(
                model_name="mistral-7b-instruct",
                prompt=prompt,
                max_tokens=700,
                temperature=0.4  # Temperatura baixa para consistência
            )
            
            # Estruturar resposta executiva
            structured_response = self._structure_executive_response(
                response, request_type, framework
            )
            
            self.logger.debug(f"Plano {request_type} criado usando framework {framework}")
            
            return structured_response
            
        except Exception as e:
            self.logger.error(f"Erro no processamento executivo: {e}")
            return self._generate_executive_fallback(user_input)
    
    def _identify_request_type(self, user_input: str) -> str:
        """Identifica o tipo de solicitação executiva"""
        
        user_input_lower = user_input.lower()
        
        request_indicators = {
            'planning': ['planejar', 'organizar', 'estruturar', 'cronograma', 'agenda'],
            'project_management': ['projeto', 'gerenciar', 'coordenar', 'executar'],
            'task_breakdown': ['dividir', 'quebrar', 'etapas', 'passos', 'fases'],
            'prioritization': ['priorizar', 'importante', 'urgente', 'primeiro'],
            'time_management': ['tempo', 'prazo', 'horário', 'agenda', 'schedule'],
            'goal_setting': ['objetivo', 'meta', 'alvo', 'resultado', 'alcançar'],
            'productivity': ['produtividade', 'eficiência', 'otimizar', 'melhorar'],
            'decision_making': ['decidir', 'escolher', 'opção', 'alternativa'],
            'workflow': ['fluxo', 'processo', 'metodologia', 'sistema']
        }
        
        # Contar matches
        type_scores = {}
        for request_type, keywords in request_indicators.items():
            score = sum(1 for keyword in keywords if keyword in user_input_lower)
            if score > 0:
                type_scores[request_type] = score
        
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        else:
            return 'general_planning'
    
    def _select_planning_framework(self, request_type: str, user_input: str) -> str:
        """Seleciona framework de planejamento apropriado"""
        
        framework_mapping = {
            'planning': 'smart_goals',
            'project_management': 'scrum',
            'task_breakdown': 'gtd',
            'prioritization': 'eisenhower_matrix',
            'time_management': 'pomodoro',
            'goal_setting': 'okr',
            'productivity': 'pareto',
            'decision_making': 'smart_goals',
            'workflow': 'kanban'
        }
        
        # Verificar menções específicas de frameworks
        user_input_lower = user_input.lower()
        for framework in self.planning_frameworks.keys():
            if framework.replace('_', ' ') in user_input_lower or framework in user_input_lower:
                return framework
        
        return framework_mapping.get(request_type, 'smart_goals')
    
    def _analyze_complexity(self, user_input: str) -> Dict[str, Any]:
        """Analisa complexidade e escopo da solicitação"""
        
        complexity_indicators = {
            'high': ['complexo', 'difícil', 'múltiplos', 'vários', 'longo prazo'],
            'medium': ['moderado', 'algumas', 'médio prazo', 'etapas'],
            'low': ['simples', 'rápido', 'básico', 'direto', 'curto prazo']
        }
        
        user_input_lower = user_input.lower()
        complexity_scores = {}
        
        for level, indicators in complexity_indicators.items():
            score = sum(1 for indicator in indicators if indicator in user_input_lower)
            complexity_scores[level] = score
        
        # Determinar nível de complexidade
        if complexity_scores['high'] > 0:
            complexity_level = 'high'
        elif complexity_scores['medium'] > 0:
            complexity_level = 'medium'
        else:
            complexity_level = 'low'
        
        # Estimar duração baseada na complexidade
        duration_estimates = {
            'high': 'Várias semanas a meses',
            'medium': 'Alguns dias a semanas',
            'low': 'Algumas horas a dias'
        }
        
        return {
            'level': complexity_level,
            'estimated_duration': duration_estimates[complexity_level],
            'requires_breakdown': complexity_level in ['high', 'medium'],
            'needs_milestones': complexity_level == 'high'
        }
    
    def _build_executive_prompt(
        self,
        user_input: str,
        context: Dict[str, Any],
        request_type: str,
        framework: str,
        complexity_analysis: Dict[str, Any]
    ) -> str:
        """Constrói prompt executivo estruturado"""
        
        base_prompt = """Você é o módulo executivo da EVA, especializado em planejamento, organização e execução eficiente.

Características:
- Pensamento estratégico e orientado a resultados
- Organização sistemática e estruturada
- Foco em eficiência e produtividade
- Abordagem prática e acionável
- Gestão eficaz de tempo e recursos

Princípios fundamentais:
- Sempre definir objetivos claros e mensuráveis
- Quebrar tarefas complexas em etapas gerenciáveis
- Considerar recursos, prazos e restrições
- Antecipar obstáculos e planejar contingências
- Fornecer planos acionáveis e práticos

"""
        
        # Descrição do framework
        framework_description = self.planning_frameworks.get(framework, framework)
        
        # Instruções específicas do framework
        framework_instructions = {
            'smart_goals': """
Use critérios SMART para estruturar objetivos:
- Specific (Específico): Defina claramente o que deve ser alcançado
- Measurable (Mensurável): Estabeleça métricas de sucesso
- Achievable (Alcançável): Garanta que é realista
- Relevant (Relevante): Conecte com objetivos maiores
- Time-bound (Temporal): Defina prazos claros
""",
            'gtd': """
Use metodologia Getting Things Done:
1. Capture: Colete todas as tarefas e ideias
2. Clarify: Defina o que cada item significa e requer
3. Organize: Categorize por contexto e prioridade
4. Reflect: Revise regularmente o sistema
5. Engage: Execute com confiança
""",
            'eisenhower_matrix': """
Use Matriz de Eisenhower para priorização:
- Quadrante 1: Urgente e Importante (Fazer imediatamente)
- Quadrante 2: Importante, não Urgente (Agendar)
- Quadrante 3: Urgente, não Importante (Delegar)
- Quadrante 4: Nem Urgente nem Importante (Eliminar)
""",
            'scrum': """
Use framework Scrum para gestão de projeto:
- Product Backlog: Lista priorizada de funcionalidades
- Sprint Planning: Planejamento de iterações
- Daily Standups: Acompanhamento diário
- Sprint Review: Revisão de resultados
- Sprint Retrospective: Melhoria contínua
"""
        }
        
        framework_instruction = framework_instructions.get(framework, "Use abordagem estruturada e sistemática")
        
        # Análise de complexidade
        complexity_info = f"""
Análise de complexidade:
- Nível: {complexity_analysis['level']}
- Duração estimada: {complexity_analysis['estimated_duration']}
- Requer decomposição: {'Sim' if complexity_analysis['requires_breakdown'] else 'Não'}
- Precisa de marcos: {'Sim' if complexity_analysis['needs_milestones'] else 'Não'}
"""
        
        # Contexto de tarefas anteriores
        task_context = ""
        if context.get('conversation_history'):
            task_context = "Considere o histórico de nossa conversa para manter continuidade no planejamento.\n"
        
        prompt = f"""{base_prompt}

Framework selecionado: {framework}
{framework_description}

{framework_instruction}

{complexity_info}

{task_context}Solicitação do usuário: "{user_input}"

Crie um plano estruturado, prático e acionável. Use formatação clara com listas, etapas numeradas e seções bem definidas. Seja específico sobre prazos, recursos e critérios de sucesso."""
        
        return prompt
    
    def _structure_executive_response(
        self,
        response: str,
        request_type: str,
        framework: str
    ) -> str:
        """Estrutura a resposta executiva com formatação profissional"""
        
        # Ícones baseados no tipo de solicitação
        type_icons = {
            'planning': '📋',
            'project_management': '🎯',
            'task_breakdown': '🔧',
            'prioritization': '⚡',
            'time_management': '⏰',
            'goal_setting': '🎯',
            'productivity': '🚀',
            'decision_making': '⚖️',
            'workflow': '🔄'
        }
        
        icon = type_icons.get(request_type, '📊')
        
        # Cabeçalhos baseados no framework
        framework_headers = {
            'smart_goals': f'{icon} **Plano SMART**',
            'gtd': f'{icon} **Plano GTD**',
            'eisenhower_matrix': f'{icon} **Matriz de Priorização**',
            'scrum': f'{icon} **Plano Scrum**',
            'okr': f'{icon} **Objetivos e Resultados-Chave**',
            'kanban': f'{icon} **Fluxo Kanban**',
            'pomodoro': f'{icon} **Plano de Tempo**',
            'pareto': f'{icon} **Análise 80/20**'
        }
        
        header = framework_headers.get(framework, f'{icon} **Plano Executivo**')
        
        # Adicionar seção de próximos passos
        next_steps_section = """

## 🎯 Próximos Passos Imediatos
1. Revisar e ajustar o plano conforme necessário
2. Definir quando começar a primeira etapa
3. Preparar recursos e ferramentas necessárias
4. Estabelecer sistema de acompanhamento de progresso"""
        
        # Rodapé executivo
        footer = f"""

---
*Plano criado usando framework {framework.replace('_', ' ').title()} | Módulo Executivo da EVA*"""
        
        return f"""{header}

{response}{next_steps_section}{footer}"""
    
    def _generate_executive_fallback(self, user_input: str) -> str:
        """Gera resposta executiva de fallback"""
        
        return f"""📋 **Plano Executivo**

Vou ajudar você a estruturar uma abordagem sistemática para: "{user_input}"

## 🎯 Abordagem Estruturada

**1. Definição Clara do Objetivo**
- O que exatamente você quer alcançar?
- Como você saberá que teve sucesso?

**2. Análise da Situação Atual**
- Onde você está agora em relação ao objetivo?
- Que recursos você já tem disponíveis?

**3. Identificação de Etapas**
- Quais são os passos principais necessários?
- Qual é a ordem lógica de execução?

**4. Planejamento de Recursos**
- Que tempo você pode dedicar?
- Que ferramentas ou ajuda você precisa?

**5. Cronograma Realista**
- Quando você quer começar?
- Qual é um prazo realista para conclusão?

## 🎯 Próximos Passos Imediatos
1. Responda às perguntas acima para refinar o plano
2. Escolha a primeira ação concreta que pode fazer hoje
3. Defina quando vai revisar o progresso

Para um plano mais detalhado, você pode me fornecer mais informações sobre seus objetivos específicos, prazos e recursos disponíveis.

---
*Plano criado pelo Módulo Executivo da EVA*"""
    
    async def create_task_plan(
        self,
        objective: str,
        constraints: Dict[str, Any] = None,
        preferences: Dict[str, Any] = None
    ) -> TaskPlan:
        """Cria um plano estruturado de tarefa"""
        
        try:
            constraints = constraints or {}
            preferences = preferences or {}
            
            # Análise básica do objetivo
            complexity = 'medium'  # Simplificado para este exemplo
            
            # Gerar etapas básicas
            steps = [
                f"Definir escopo detalhado de: {objective}",
                "Identificar recursos necessários",
                "Criar cronograma de execução",
                "Implementar primeira fase",
                "Monitorar progresso e ajustar",
                "Finalizar e avaliar resultados"
            ]
            
            # Timeline básico
            timeline = {
                'início': 'Imediato',
                'primeira_fase': '1-2 dias',
                'desenvolvimento': '1-2 semanas',
                'finalização': '3-4 semanas'
            }
            
            # Recursos necessários
            resources_needed = [
                'Tempo dedicado',
                'Ferramentas apropriadas',
                'Informações/conhecimento',
                'Possível suporte externo'
            ]
            
            # Critérios de sucesso
            success_criteria = [
                f"Objetivo '{objective}' completamente alcançado",
                "Qualidade satisfatória dos resultados",
                "Prazo respeitado",
                "Recursos utilizados eficientemente"
            ]
            
            # Obstáculos potenciais
            potential_obstacles = [
                "Falta de tempo suficiente",
                "Recursos insuficientes",
                "Complexidade subestimada",
                "Mudanças de requisitos"
            ]
            
            # Planos de contingência
            contingency_plans = [
                "Redefinir escopo se necessário",
                "Buscar recursos adicionais",
                "Dividir em fases menores",
                "Solicitar extensão de prazo"
            ]
            
            return TaskPlan(
                objective=objective,
                steps=steps,
                timeline=timeline,
                resources_needed=resources_needed,
                success_criteria=success_criteria,
                potential_obstacles=potential_obstacles,
                contingency_plans=contingency_plans
            )
            
        except Exception as e:
            self.logger.error(f"Erro na criação do plano de tarefa: {e}")
            return TaskPlan(
                objective=objective,
                steps=[f"Planejar execução de: {objective}"],
                timeline={'início': 'A definir'},
                resources_needed=['A identificar'],
                success_criteria=[f"Completar {objective}"],
                potential_obstacles=['Obstáculos a identificar'],
                contingency_plans=['Planos alternativos a desenvolver']
            )
    
    def get_executive_capabilities(self) -> Dict[str, Any]:
        """Retorna capacidades executivas disponíveis"""
        return {
            'planning_frameworks': list(self.planning_frameworks.keys()),
            'task_types': list(self.task_types.keys()),
            'productivity_templates': list(self.productivity_templates.keys()),
            'traits': self.traits,
            'specialties': [
                'Planejamento estratégico e tático',
                'Organização e estruturação de tarefas',
                'Gestão de tempo e produtividade',
                'Execução eficiente de projetos',
                'Tomada de decisões estruturadas'
            ]
        }
    
    def get_persona_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da persona"""
        return {
            'name': 'Executive',
            'traits': self.traits,
            'frameworks_available': len(self.planning_frameworks),
            'task_types_supported': len(self.task_types),
            'primary_temperature': 0.4,
            'specialization': 'Planning, organization and efficient execution'
        }
