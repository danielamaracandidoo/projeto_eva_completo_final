"""
Planejador de ações da EVA.
Responsável por criar planos de ação para alcançar objetivos.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

from utils.logging_system import EVALogger

class ActionType(Enum):
    """Tipos de ação"""
    INFORMATION_GATHERING = "information_gathering"
    ANALYSIS = "analysis"
    COMMUNICATION = "communication"
    TASK_EXECUTION = "task_execution"
    DECISION_MAKING = "decision_making"
    MONITORING = "monitoring"
    LEARNING = "learning"
    CREATIVE = "creative"

class ActionPriority(Enum):
    """Prioridade de ação"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

@dataclass
class Action:
    """Representação de uma ação"""
    id: str
    name: str
    description: str
    action_type: ActionType
    priority: ActionPriority
    estimated_duration: int  # minutos
    prerequisites: List[str]
    resources_needed: List[str]
    expected_outcome: str
    success_metrics: List[str]
    created_at: datetime
    parameters: Dict[str, Any] = None

@dataclass
class ActionPlan:
    """Plano de ação completo"""
    id: str
    name: str
    objective: str
    actions: List[Action]
    total_estimated_duration: int
    created_at: datetime
    dependencies: Dict[str, List[str]]  # action_id -> [prerequisite_ids]
    parallel_groups: List[List[str]]  # grupos de ações que podem ser executadas em paralelo

class ActionPlanner:
    """
    Planejador de ações da EVA.
    
    Funcionalidades:
    - Criação de planos de ação estruturados
    - Análise de dependências entre ações
    - Otimização de sequência de execução
    - Identificação de ações paralelas
    - Estimativa de tempo e recursos
    - Adaptação dinâmica de planos
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = EVALogger.get_logger("ActionPlanner")
        
        # Armazenamento de planos
        self.action_plans: Dict[str, ActionPlan] = {}
        
        # Templates de ação
        self.action_templates = self._initialize_action_templates()
        
        # Estratégias de planejamento
        self.planning_strategies = {
            'sequential': self._plan_sequential,
            'parallel': self._plan_parallel,
            'hybrid': self._plan_hybrid,
            'adaptive': self._plan_adaptive
        }
        
        # Configurações
        self.max_parallel_actions = config.agency.max_parallel_actions
        self.default_action_duration = config.agency.default_action_duration
        
        # Estatísticas
        self.stats = {
            'plans_created': 0,
            'actions_planned': 0,
            'average_plan_duration': 0.0,
            'optimization_improvements': 0
        }
        
        self.logger.info("ActionPlanner inicializado")
    
    def _initialize_action_templates(self) -> Dict[str, Dict[str, Any]]:
        """Inicializa templates de ação"""
        return {
            'research_topic': {
                'action_type': ActionType.INFORMATION_GATHERING,
                'estimated_duration': 30,
                'resources_needed': ['internet_access', 'search_tools'],
                'success_metrics': ['information_quality', 'source_credibility']
            },
            'analyze_data': {
                'action_type': ActionType.ANALYSIS,
                'estimated_duration': 45,
                'resources_needed': ['data_analysis_tools', 'computational_power'],
                'success_metrics': ['insight_quality', 'accuracy']
            },
            'send_communication': {
                'action_type': ActionType.COMMUNICATION,
                'estimated_duration': 15,
                'resources_needed': ['communication_channel'],
                'success_metrics': ['message_clarity', 'recipient_understanding']
            },
            'execute_task': {
                'action_type': ActionType.TASK_EXECUTION,
                'estimated_duration': 60,
                'resources_needed': ['task_specific_tools'],
                'success_metrics': ['task_completion', 'quality_standards']
            },
            'make_decision': {
                'action_type': ActionType.DECISION_MAKING,
                'estimated_duration': 20,
                'resources_needed': ['decision_framework', 'relevant_information'],
                'success_metrics': ['decision_quality', 'stakeholder_satisfaction']
            },
            'monitor_progress': {
                'action_type': ActionType.MONITORING,
                'estimated_duration': 10,
                'resources_needed': ['monitoring_tools', 'progress_metrics'],
                'success_metrics': ['monitoring_accuracy', 'timely_alerts']
            },
            'learn_skill': {
                'action_type': ActionType.LEARNING,
                'estimated_duration': 120,
                'resources_needed': ['learning_materials', 'practice_environment'],
                'success_metrics': ['skill_acquisition', 'knowledge_retention']
            },
            'create_content': {
                'action_type': ActionType.CREATIVE,
                'estimated_duration': 90,
                'resources_needed': ['creative_tools', 'inspiration_sources'],
                'success_metrics': ['creativity_level', 'content_quality']
            }
        }
    
    async def create_action_plan(
        self,
        objective: str,
        context: Dict[str, Any] = None,
        strategy: str = 'hybrid',
        constraints: Dict[str, Any] = None
    ) -> str:
        """
        Cria um plano de ação para um objetivo.
        
        Args:
            objective: Objetivo a ser alcançado
            context: Contexto adicional
            strategy: Estratégia de planejamento
            constraints: Restrições (tempo, recursos, etc.)
            
        Returns:
            ID do plano criado
        """
        try:
            plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            self.logger.info(f"Criando plano de ação para: {objective}")
            
            # Analisar objetivo e contexto
            analysis = await self._analyze_objective(objective, context or {})
            
            # Gerar ações necessárias
            actions = await self._generate_actions(analysis, constraints or {})
            
            # Aplicar estratégia de planejamento
            if strategy in self.planning_strategies:
                optimized_plan = await self.planning_strategies[strategy](actions, constraints or {})
            else:
                optimized_plan = await self._plan_hybrid(actions, constraints or {})
            
            # Criar plano final
            action_plan = ActionPlan(
                id=plan_id,
                name=f"Plano para: {objective[:50]}...",
                objective=objective,
                actions=optimized_plan['actions'],
                total_estimated_duration=optimized_plan['total_duration'],
                created_at=datetime.now(),
                dependencies=optimized_plan['dependencies'],
                parallel_groups=optimized_plan['parallel_groups']
            )
            
            self.action_plans[plan_id] = action_plan
            
            # Atualizar estatísticas
            self.stats['plans_created'] += 1
            self.stats['actions_planned'] += len(actions)
            self._update_average_plan_duration(optimized_plan['total_duration'])
            
            self.logger.info(f"Plano criado: {plan_id} ({len(actions)} ações, {optimized_plan['total_duration']} min)")
            
            return plan_id
            
        except Exception as e:
            self.logger.error(f"Erro ao criar plano de ação: {e}")
            raise
    
    async def _analyze_objective(self, objective: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa objetivo para identificar ações necessárias"""
        try:
            analysis = {
                'objective': objective,
                'complexity': 'medium',
                'domain': 'general',
                'required_capabilities': [],
                'estimated_effort': 'medium',
                'key_challenges': [],
                'success_indicators': []
            }
            
            objective_lower = objective.lower()
            
            # Análise de complexidade
            complexity_indicators = {
                'high': ['complexo', 'múltiplos', 'integração', 'sistema', 'arquitetura'],
                'medium': ['analisar', 'criar', 'desenvolver', 'implementar'],
                'low': ['simples', 'básico', 'rápido', 'direto']
            }
            
            for level, indicators in complexity_indicators.items():
                if any(indicator in objective_lower for indicator in indicators):
                    analysis['complexity'] = level
                    break
            
            # Análise de domínio
            domain_keywords = {
                'technical': ['código', 'programação', 'sistema', 'software', 'api'],
                'creative': ['criar', 'design', 'arte', 'conteúdo', 'criativo'],
                'analytical': ['analisar', 'dados', 'estatística', 'pesquisa', 'estudo'],
                'communication': ['comunicar', 'apresentar', 'relatório', 'documento'],
                'learning': ['aprender', 'estudar', 'conhecimento', 'habilidade']
            }
            
            for domain, keywords in domain_keywords.items():
                if any(keyword in objective_lower for keyword in keywords):
                    analysis['domain'] = domain
                    break
            
            # Identificar capacidades necessárias
            capability_mapping = {
                'research': ['pesquisar', 'investigar', 'buscar', 'encontrar'],
                'analysis': ['analisar', 'avaliar', 'examinar', 'estudar'],
                'creation': ['criar', 'desenvolver', 'construir', 'gerar'],
                'communication': ['comunicar', 'apresentar', 'explicar', 'relatar'],
                'problem_solving': ['resolver', 'solucionar', 'corrigir', 'otimizar']
            }
            
            for capability, keywords in capability_mapping.items():
                if any(keyword in objective_lower for keyword in keywords):
                    analysis['required_capabilities'].append(capability)
            
            # Usar contexto para refinar análise
            if context:
                if 'urgency' in context:
                    analysis['urgency'] = context['urgency']
                if 'resources' in context:
                    analysis['available_resources'] = context['resources']
                if 'constraints' in context:
                    analysis['constraints'] = context['constraints']
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Erro na análise do objetivo: {e}")
            return {'objective': objective, 'complexity': 'medium', 'domain': 'general'}
    
    async def _generate_actions(self, analysis: Dict[str, Any], constraints: Dict[str, Any]) -> List[Action]:
        """Gera ações baseadas na análise do objetivo"""
        try:
            actions = []
            objective = analysis['objective']
            complexity = analysis['complexity']
            domain = analysis['domain']
            capabilities = analysis.get('required_capabilities', [])
            
            # Ações baseadas no domínio
            domain_actions = {
                'technical': [
                    ('research_requirements', 'Pesquisar requisitos técnicos'),
                    ('analyze_architecture', 'Analisar arquitetura necessária'),
                    ('implement_solution', 'Implementar solução'),
                    ('test_solution', 'Testar solução'),
                    ('document_solution', 'Documentar solução')
                ],
                'creative': [
                    ('gather_inspiration', 'Coletar inspiração'),
                    ('brainstorm_ideas', 'Fazer brainstorming'),
                    ('create_draft', 'Criar rascunho'),
                    ('refine_creation', 'Refinar criação'),
                    ('finalize_work', 'Finalizar trabalho')
                ],
                'analytical': [
                    ('collect_data', 'Coletar dados'),
                    ('clean_data', 'Limpar dados'),
                    ('analyze_patterns', 'Analisar padrões'),
                    ('generate_insights', 'Gerar insights'),
                    ('create_report', 'Criar relatório')
                ],
                'communication': [
                    ('define_audience', 'Definir audiência'),
                    ('structure_message', 'Estruturar mensagem'),
                    ('create_content', 'Criar conteúdo'),
                    ('review_content', 'Revisar conteúdo'),
                    ('deliver_message', 'Entregar mensagem')
                ],
                'learning': [
                    ('identify_resources', 'Identificar recursos'),
                    ('create_study_plan', 'Criar plano de estudos'),
                    ('study_material', 'Estudar material'),
                    ('practice_skills', 'Praticar habilidades'),
                    ('assess_progress', 'Avaliar progresso')
                ]
            }
            
            # Selecionar ações baseadas no domínio
            base_actions = domain_actions.get(domain, [
                ('understand_objective', 'Compreender objetivo'),
                ('plan_approach', 'Planejar abordagem'),
                ('execute_plan', 'Executar plano'),
                ('review_results', 'Revisar resultados')
            ])
            
            # Criar ações
            for i, (action_key, action_name) in enumerate(base_actions):
                action_id = f"action_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"
                
                # Determinar tipo de ação
                action_type = self._determine_action_type(action_key)
                
                # Determinar prioridade
                priority = ActionPriority.MEDIUM
                if i == 0:  # Primeira ação
                    priority = ActionPriority.HIGH
                elif i == len(base_actions) - 1:  # Última ação
                    priority = ActionPriority.HIGH
                
                # Estimar duração baseada na complexidade
                duration_multipliers = {
                    'low': 0.7,
                    'medium': 1.0,
                    'high': 1.5
                }
                
                base_duration = self.action_templates.get(action_key, {}).get(
                    'estimated_duration', self.default_action_duration
                )
                estimated_duration = int(base_duration * duration_multipliers[complexity])
                
                # Criar ação
                action = Action(
                    id=action_id,
                    name=action_name,
                    description=f"{action_name} para: {objective}",
                    action_type=action_type,
                    priority=priority,
                    estimated_duration=estimated_duration,
                    prerequisites=[],
                    resources_needed=self._get_resources_for_action(action_key),
                    expected_outcome=f"Resultado de {action_name.lower()}",
                    success_metrics=self._get_success_metrics_for_action(action_key),
                    created_at=datetime.now(),
                    parameters={'objective': objective, 'domain': domain}
                )
                
                actions.append(action)
            
            # Definir pré-requisitos (ações sequenciais)
            for i in range(1, len(actions)):
                actions[i].prerequisites = [actions[i-1].id]
            
            # Adicionar ações específicas baseadas nas capacidades
            for capability in capabilities:
                if capability not in [a.action_type.value for a in actions]:
                    additional_action = self._create_capability_action(capability, objective)
                    if additional_action:
                        actions.append(additional_action)
            
            return actions
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar ações: {e}")
            return []
    
    def _determine_action_type(self, action_key: str) -> ActionType:
        """Determina tipo de ação baseado na chave"""
        type_mapping = {
            'research': ActionType.INFORMATION_GATHERING,
            'analyze': ActionType.ANALYSIS,
            'communicate': ActionType.COMMUNICATION,
            'implement': ActionType.TASK_EXECUTION,
            'decide': ActionType.DECISION_MAKING,
            'monitor': ActionType.MONITORING,
            'learn': ActionType.LEARNING,
            'create': ActionType.CREATIVE
        }
        
        for key, action_type in type_mapping.items():
            if key in action_key:
                return action_type
        
        return ActionType.TASK_EXECUTION  # Padrão
    
    def _get_resources_for_action(self, action_key: str) -> List[str]:
        """Retorna recursos necessários para uma ação"""
        resource_mapping = {
            'research': ['internet_access', 'search_tools', 'databases'],
            'analyze': ['analysis_tools', 'computational_power', 'data_access'],
            'create': ['creative_tools', 'design_software', 'content_platforms'],
            'communicate': ['communication_channels', 'presentation_tools'],
            'implement': ['development_tools', 'testing_environment'],
            'monitor': ['monitoring_tools', 'dashboards', 'alerts']
        }
        
        for key, resources in resource_mapping.items():
            if key in action_key:
                return resources
        
        return ['basic_tools']
    
    def _get_success_metrics_for_action(self, action_key: str) -> List[str]:
        """Retorna métricas de sucesso para uma ação"""
        metrics_mapping = {
            'research': ['information_completeness', 'source_reliability'],
            'analyze': ['analysis_accuracy', 'insight_quality'],
            'create': ['creativity_level', 'quality_standards'],
            'communicate': ['message_clarity', 'audience_engagement'],
            'implement': ['functionality', 'performance', 'reliability'],
            'monitor': ['monitoring_coverage', 'alert_accuracy']
        }
        
        for key, metrics in metrics_mapping.items():
            if key in action_key:
                return metrics
        
        return ['completion_status', 'quality_level']
    
    def _create_capability_action(self, capability: str, objective: str) -> Optional[Action]:
        """Cria ação específica para uma capacidade"""
        try:
            capability_actions = {
                'research': ('Pesquisar informações relevantes', ActionType.INFORMATION_GATHERING),
                'analysis': ('Analisar dados e informações', ActionType.ANALYSIS),
                'creation': ('Criar solução ou conteúdo', ActionType.CREATIVE),
                'communication': ('Comunicar resultados', ActionType.COMMUNICATION),
                'problem_solving': ('Resolver problemas identificados', ActionType.TASK_EXECUTION)
            }
            
            if capability not in capability_actions:
                return None
            
            name, action_type = capability_actions[capability]
            action_id = f"action_{capability}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            return Action(
                id=action_id,
                name=name,
                description=f"{name} para: {objective}",
                action_type=action_type,
                priority=ActionPriority.MEDIUM,
                estimated_duration=self.default_action_duration,
                prerequisites=[],
                resources_needed=self._get_resources_for_action(capability),
                expected_outcome=f"Resultado de {name.lower()}",
                success_metrics=self._get_success_metrics_for_action(capability),
                created_at=datetime.now(),
                parameters={'capability': capability, 'objective': objective}
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao criar ação de capacidade: {e}")
            return None
    
    # Estratégias de planejamento
    
    async def _plan_sequential(self, actions: List[Action], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Estratégia de planejamento sequencial"""
        try:
            # Ordenar por prioridade
            sorted_actions = sorted(actions, key=lambda a: a.priority.value, reverse=True)
            
            # Criar dependências sequenciais
            dependencies = {}
            for i in range(1, len(sorted_actions)):
                dependencies[sorted_actions[i].id] = [sorted_actions[i-1].id]
            
            total_duration = sum(action.estimated_duration for action in sorted_actions)
            
            return {
                'actions': sorted_actions,
                'dependencies': dependencies,
                'parallel_groups': [],  # Nenhuma paralelização
                'total_duration': total_duration,
                'strategy': 'sequential'
            }
            
        except Exception as e:
            self.logger.error(f"Erro no planejamento sequencial: {e}")
            raise
    
    async def _plan_parallel(self, actions: List[Action], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Estratégia de planejamento paralelo"""
        try:
            # Identificar ações que podem ser executadas em paralelo
            parallel_groups = self._identify_parallel_groups(actions)
            
            # Calcular duração considerando paralelização
            total_duration = self._calculate_parallel_duration(actions, parallel_groups)
            
            # Dependências mínimas
            dependencies = {}
            for action in actions:
                if action.prerequisites:
                    dependencies[action.id] = action.prerequisites
            
            return {
                'actions': actions,
                'dependencies': dependencies,
                'parallel_groups': parallel_groups,
                'total_duration': total_duration,
                'strategy': 'parallel'
            }
            
        except Exception as e:
            self.logger.error(f"Erro no planejamento paralelo: {e}")
            raise
    
    async def _plan_hybrid(self, actions: List[Action], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Estratégia de planejamento híbrido (sequencial + paralelo)"""
        try:
            # Identificar fases do projeto
            phases = self._identify_project_phases(actions)
            
            # Dentro de cada fase, identificar ações paralelas
            parallel_groups = []
            dependencies = {}
            
            for i, phase in enumerate(phases):
                # Ações da fase podem ser paralelas entre si
                if len(phase) > 1:
                    parallel_groups.append([action.id for action in phase])
                
                # Dependências entre fases
                if i > 0:
                    previous_phase = phases[i-1]
                    for action in phase:
                        # Depende de todas as ações da fase anterior
                        dependencies[action.id] = [prev_action.id for prev_action in previous_phase]
            
            # Calcular duração considerando fases e paralelização
            total_duration = 0
            for phase in phases:
                if len(phase) == 1:
                    total_duration += phase[0].estimated_duration
                else:
                    # Duração da fase é a maior duração entre ações paralelas
                    total_duration += max(action.estimated_duration for action in phase)
            
            return {
                'actions': [action for phase in phases for action in phase],
                'dependencies': dependencies,
                'parallel_groups': parallel_groups,
                'total_duration': total_duration,
                'strategy': 'hybrid'
            }
            
        except Exception as e:
            self.logger.error(f"Erro no planejamento híbrido: {e}")
            raise
    
    async def _plan_adaptive(self, actions: List[Action], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Estratégia de planejamento adaptativo"""
        try:
            # Começar com planejamento híbrido
            base_plan = await self._plan_hybrid(actions, constraints)
            
            # Aplicar otimizações baseadas em restrições
            if 'time_limit' in constraints:
                base_plan = self._optimize_for_time(base_plan, constraints['time_limit'])
            
            if 'resource_limit' in constraints:
                base_plan = self._optimize_for_resources(base_plan, constraints['resource_limit'])
            
            if 'priority_focus' in constraints:
                base_plan = self._optimize_for_priority(base_plan, constraints['priority_focus'])
            
            base_plan['strategy'] = 'adaptive'
            return base_plan
            
        except Exception as e:
            self.logger.error(f"Erro no planejamento adaptativo: {e}")
            raise
    
    def _identify_parallel_groups(self, actions: List[Action]) -> List[List[str]]:
        """Identifica grupos de ações que podem ser executadas em paralelo"""
        try:
            parallel_groups = []
            
            # Agrupar por tipo de ação
            type_groups = {}
            for action in actions:
                action_type = action.action_type
                if action_type not in type_groups:
                    type_groups[action_type] = []
                type_groups[action_type].append(action)
            
            # Ações do mesmo tipo podem ser paralelas (com limitações)
            for action_type, type_actions in type_groups.items():
                if len(type_actions) > 1:
                    # Verificar se não há dependências entre elas
                    independent_actions = []
                    for action in type_actions:
                        has_dependencies = any(
                            prereq in [a.id for a in type_actions]
                            for prereq in action.prerequisites
                        )
                        if not has_dependencies:
                            independent_actions.append(action.id)
                    
                    if len(independent_actions) > 1:
                        # Limitar pelo número máximo de ações paralelas
                        max_parallel = min(len(independent_actions), self.max_parallel_actions)
                        parallel_groups.append(independent_actions[:max_parallel])
            
            return parallel_groups
            
        except Exception as e:
            self.logger.error(f"Erro ao identificar grupos paralelos: {e}")
            return []
    
    def _identify_project_phases(self, actions: List[Action]) -> List[List[Action]]:
        """Identifica fases do projeto baseado nos tipos de ação"""
        try:
            # Definir ordem típica de fases
            phase_order = [
                ActionType.INFORMATION_GATHERING,
                ActionType.ANALYSIS,
                ActionType.DECISION_MAKING,
                ActionType.TASK_EXECUTION,
                ActionType.CREATIVE,
                ActionType.COMMUNICATION,
                ActionType.MONITORING
            ]
            
            phases = []
            
            # Agrupar ações por tipo
            type_groups = {}
            for action in actions:
                action_type = action.action_type
                if action_type not in type_groups:
                    type_groups[action_type] = []
                type_groups[action_type].append(action)
            
            # Criar fases na ordem definida
            for phase_type in phase_order:
                if phase_type in type_groups:
                    phases.append(type_groups[phase_type])
            
            # Adicionar tipos não mapeados como fases separadas
            for action_type, type_actions in type_groups.items():
                if action_type not in phase_order:
                    phases.append(type_actions)
            
            return phases
            
        except Exception as e:
            self.logger.error(f"Erro ao identificar fases: {e}")
            return [actions]  # Fallback: uma única fase
    
    def _calculate_parallel_duration(self, actions: List[Action], parallel_groups: List[List[str]]) -> int:
        """Calcula duração considerando execução paralela"""
        try:
            # Mapear IDs para ações
            action_map = {action.id: action for action in actions}
            
            # Identificar ações que estão em grupos paralelos
            parallel_action_ids = set()
            for group in parallel_groups:
                parallel_action_ids.update(group)
            
            total_duration = 0
            
            # Calcular duração dos grupos paralelos
            for group in parallel_groups:
                group_actions = [action_map[action_id] for action_id in group]
                # Duração do grupo é a maior duração individual
                group_duration = max(action.estimated_duration for action in group_actions)
                total_duration += group_duration
            
            # Adicionar duração das ações sequenciais
            sequential_actions = [
                action for action in actions
                if action.id not in parallel_action_ids
            ]
            
            total_duration += sum(action.estimated_duration for action in sequential_actions)
            
            return total_duration
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular duração paralela: {e}")
            return sum(action.estimated_duration for action in actions)
    
    def _optimize_for_time(self, plan: Dict[str, Any], time_limit: int) -> Dict[str, Any]:
        """Otimiza plano para restrição de tempo"""
        try:
            if plan['total_duration'] <= time_limit:
                return plan  # Já dentro do limite
            
            # Estratégias de otimização
            actions = plan['actions']
            
            # 1. Aumentar paralelização
            additional_parallel = self._find_additional_parallel_opportunities(actions)
            if additional_parallel:
                plan['parallel_groups'].extend(additional_parallel)
                plan['total_duration'] = self._calculate_parallel_duration(
                    actions, plan['parallel_groups']
                )
            
            # 2. Reduzir escopo de ações menos críticas
            if plan['total_duration'] > time_limit:
                plan = self._reduce_action_scope(plan, time_limit)
            
            self.stats['optimization_improvements'] += 1
            return plan
            
        except Exception as e:
            self.logger.error(f"Erro na otimização por tempo: {e}")
            return plan
    
    def _optimize_for_resources(self, plan: Dict[str, Any], resource_limit: Dict[str, int]) -> Dict[str, Any]:
        """Otimiza plano para restrições de recursos"""
        try:
            # Verificar se recursos são suficientes
            resource_usage = self._calculate_resource_usage(plan['actions'])
            
            # Ajustar paralelização baseado em recursos
            optimized_parallel_groups = []
            for group in plan['parallel_groups']:
                # Verificar se grupo pode ser executado com recursos disponíveis
                group_actions = [a for a in plan['actions'] if a.id in group]
                group_resources = self._calculate_resource_usage(group_actions)
                
                if self._resources_within_limit(group_resources, resource_limit):
                    optimized_parallel_groups.append(group)
                else:
                    # Dividir grupo em subgrupos menores
                    subgroups = self._split_group_by_resources(group_actions, resource_limit)
                    optimized_parallel_groups.extend(subgroups)
            
            plan['parallel_groups'] = optimized_parallel_groups
            plan['total_duration'] = self._calculate_parallel_duration(
                plan['actions'], plan['parallel_groups']
            )
            
            return plan
            
        except Exception as e:
            self.logger.error(f"Erro na otimização por recursos: {e}")
            return plan
    
    def _optimize_for_priority(self, plan: Dict[str, Any], priority_focus: str) -> Dict[str, Any]:
        """Otimiza plano focando em prioridades específicas"""
        try:
            actions = plan['actions']
            
            if priority_focus == 'high_priority_first':
                # Reordenar para priorizar ações de alta prioridade
                high_priority = [a for a in actions if a.priority == ActionPriority.HIGH]
                other_actions = [a for a in actions if a.priority != ActionPriority.HIGH]
                
                plan['actions'] = high_priority + other_actions
                
            elif priority_focus == 'quick_wins':
                # Priorizar ações rápidas e de alto impacto
                quick_wins = sorted(
                    actions,
                    key=lambda a: (a.estimated_duration, -a.priority.value)
                )
                plan['actions'] = quick_wins
            
            return plan
            
        except Exception as e:
            self.logger.error(f"Erro na otimização por prioridade: {e}")
            return plan
    
    def _find_additional_parallel_opportunities(self, actions: List[Action]) -> List[List[str]]:
        """Encontra oportunidades adicionais de paralelização"""
        # Implementação simplificada
        return []
    
    def _reduce_action_scope(self, plan: Dict[str, Any], time_limit: int) -> Dict[str, Any]:
        """Reduz escopo de ações para caber no limite de tempo"""
        # Implementação simplificada - remover ações de menor prioridade
        actions = plan['actions']
        actions_by_priority = sorted(actions, key=lambda a: a.priority.value, reverse=True)
        
        cumulative_duration = 0
        selected_actions = []
        
        for action in actions_by_priority:
            if cumulative_duration + action.estimated_duration <= time_limit:
                selected_actions.append(action)
                cumulative_duration += action.estimated_duration
            else:
                break
        
        plan['actions'] = selected_actions
        plan['total_duration'] = cumulative_duration
        
        return plan
    
    def _calculate_resource_usage(self, actions: List[Action]) -> Dict[str, int]:
        """Calcula uso de recursos pelas ações"""
        resource_usage = {}
        
        for action in actions:
            for resource in action.resources_needed:
                resource_usage[resource] = resource_usage.get(resource, 0) + 1
        
        return resource_usage
    
    def _resources_within_limit(self, usage: Dict[str, int], limit: Dict[str, int]) -> bool:
        """Verifica se uso de recursos está dentro do limite"""
        for resource, used in usage.items():
            if resource in limit and used > limit[resource]:
                return False
        return True
    
    def _split_group_by_resources(self, actions: List[Action], resource_limit: Dict[str, int]) -> List[List[str]]:
        """Divide grupo de ações baseado em limites de recursos"""
        # Implementação simplificada
        subgroups = []
        current_group = []
        current_usage = {}
        
        for action in actions:
            # Calcular uso se adicionarmos esta ação
            temp_usage = current_usage.copy()
            for resource in action.resources_needed:
                temp_usage[resource] = temp_usage.get(resource, 0) + 1
            
            # Verificar se cabe no limite
            if self._resources_within_limit(temp_usage, resource_limit):
                current_group.append(action.id)
                current_usage = temp_usage
            else:
                # Iniciar novo grupo
                if current_group:
                    subgroups.append(current_group)
                current_group = [action.id]
                current_usage = {resource: 1 for resource in action.resources_needed}
        
        if current_group:
            subgroups.append(current_group)
        
        return subgroups
    
    def _update_average_plan_duration(self, duration: int):
        """Atualiza duração média dos planos"""
        current_avg = self.stats['average_plan_duration']
        plan_count = self.stats['plans_created']
        
        if plan_count == 1:
            self.stats['average_plan_duration'] = duration
        else:
            self.stats['average_plan_duration'] = (
                (current_avg * (plan_count - 1) + duration) / plan_count
            )
    
    # Métodos públicos
    
    def get_action_plan(self, plan_id: str) -> Optional[ActionPlan]:
        """Retorna plano de ação por ID"""
        return self.action_plans.get(plan_id)
    
    def get_plan_summary(self, plan_id: str) -> Dict[str, Any]:
        """Retorna resumo de um plano"""
        if plan_id not in self.action_plans:
            return {}
        
        plan = self.action_plans[plan_id]
        
        return {
            'id': plan.id,
            'name': plan.name,
            'objective': plan.objective,
            'total_actions': len(plan.actions),
            'estimated_duration': plan.total_estimated_duration,
            'parallel_groups': len(plan.parallel_groups),
            'created_at': plan.created_at.isoformat(),
            'action_types': list(set(a.action_type.value for a in plan.actions)),
            'priority_distribution': {
                priority.name: len([a for a in plan.actions if a.priority == priority])
                for priority in ActionPriority
            }
        }
    
    def get_next_actions(self, plan_id: str, completed_actions: List[str] = None) -> List[Action]:
        """Retorna próximas ações que podem ser executadas"""
        if plan_id not in self.action_plans:
            return []
        
        plan = self.action_plans[plan_id]
        completed_actions = completed_actions or []
        
        next_actions = []
        
        for action in plan.actions:
            if action.id in completed_actions:
                continue
            
            # Verificar se pré-requisitos foram atendidos
            prerequisites_met = all(
                prereq in completed_actions
                for prereq in action.prerequisites
            )
            
            if prerequisites_met:
                next_actions.append(action)
        
        return next_actions
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do planejador"""
        return {
            **self.stats,
            'active_plans': len(self.action_plans),
            'planning_strategies': list(self.planning_strategies.keys()),
            'action_templates': len(self.action_templates)
        }
