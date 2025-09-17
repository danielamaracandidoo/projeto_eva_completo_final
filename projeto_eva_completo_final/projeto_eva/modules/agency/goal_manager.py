"""
Gerenciador de objetivos da EVA.
Responsável por definir, acompanhar e gerenciar objetivos de longo prazo.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta

from utils.logging_system import EVALogger

class GoalStatus(Enum):
    """Status de um objetivo"""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    FAILED = "failed"

class GoalPriority(Enum):
    """Prioridade de um objetivo"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Milestone:
    """Marco de um objetivo"""
    id: str
    name: str
    description: str
    target_date: datetime
    completed: bool = False
    completed_date: Optional[datetime] = None
    progress: float = 0.0

@dataclass
class Goal:
    """Representação de um objetivo"""
    id: str
    name: str
    description: str
    category: str
    priority: GoalPriority
    status: GoalStatus
    created_at: datetime
    target_date: Optional[datetime]
    completed_date: Optional[datetime] = None
    progress: float = 0.0
    milestones: List[Milestone] = None
    success_criteria: List[str] = None
    resources_needed: List[str] = None
    dependencies: List[str] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None

class GoalManager:
    """
    Gerenciador de objetivos da EVA.
    
    Funcionalidades:
    - Definição e acompanhamento de objetivos
    - Gestão de marcos e progresso
    - Priorização automática
    - Análise de dependências
    - Relatórios de progresso
    - Sugestões de ações
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = EVALogger.get_logger("GoalManager")
        
        # Armazenamento de objetivos
        self.goals: Dict[str, Goal] = {}
        self.goal_categories = set()
        
        # Configurações
        self.max_active_goals = config.agency.max_active_goals
        self.progress_update_interval = config.agency.progress_update_interval
        
        # Estado
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Estatísticas
        self.stats = {
            'goals_created': 0,
            'goals_completed': 0,
            'goals_failed': 0,
            'total_progress': 0.0,
            'average_completion_time': 0.0
        }
        
        self.logger.info("GoalManager inicializado")
    
    async def start_monitoring(self):
        """Inicia monitoramento de objetivos"""
        try:
            if self.is_monitoring:
                self.logger.warning("Monitoramento já está ativo")
                return
            
            self.is_monitoring = True
            self.monitor_task = asyncio.create_task(self._monitoring_loop())
            
            self.logger.info("Monitoramento de objetivos iniciado")
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar monitoramento: {e}")
            raise
    
    async def stop_monitoring(self):
        """Para monitoramento de objetivos"""
        try:
            self.is_monitoring = False
            
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("Monitoramento de objetivos parado")
            
        except Exception as e:
            self.logger.error(f"Erro ao parar monitoramento: {e}")
    
    async def _monitoring_loop(self):
        """Loop de monitoramento de objetivos"""
        try:
            while self.is_monitoring:
                # Atualizar progresso dos objetivos
                await self._update_goals_progress()
                
                # Verificar prazos
                await self._check_deadlines()
                
                # Analisar dependências
                await self._analyze_dependencies()
                
                # Aguardar próxima iteração
                await asyncio.sleep(self.progress_update_interval)
                
        except asyncio.CancelledError:
            self.logger.info("Loop de monitoramento cancelado")
        except Exception as e:
            self.logger.error(f"Erro no loop de monitoramento: {e}")
    
    async def create_goal(
        self,
        name: str,
        description: str,
        category: str = "general",
        priority: GoalPriority = GoalPriority.MEDIUM,
        target_date: Optional[datetime] = None,
        success_criteria: Optional[List[str]] = None,
        resources_needed: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Cria um novo objetivo.
        
        Args:
            name: Nome do objetivo
            description: Descrição detalhada
            category: Categoria do objetivo
            priority: Prioridade
            target_date: Data alvo para conclusão
            success_criteria: Critérios de sucesso
            resources_needed: Recursos necessários
            dependencies: Dependências de outros objetivos
            tags: Tags para organização
            metadata: Metadados adicionais
            
        Returns:
            ID do objetivo criado
        """
        try:
            goal_id = f"goal_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            goal = Goal(
                id=goal_id,
                name=name,
                description=description,
                category=category,
                priority=priority,
                status=GoalStatus.ACTIVE,
                created_at=datetime.now(),
                target_date=target_date,
                milestones=[],
                success_criteria=success_criteria or [],
                resources_needed=resources_needed or [],
                dependencies=dependencies or [],
                tags=tags or [],
                metadata=metadata or {}
            )
            
            self.goals[goal_id] = goal
            self.goal_categories.add(category)
            self.stats['goals_created'] += 1
            
            self.logger.info(f"Objetivo criado: {name} (ID: {goal_id})")
            return goal_id
            
        except Exception as e:
            self.logger.error(f"Erro ao criar objetivo: {e}")
            raise
    
    async def add_milestone(
        self,
        goal_id: str,
        name: str,
        description: str,
        target_date: datetime
    ) -> str:
        """Adiciona marco a um objetivo"""
        try:
            if goal_id not in self.goals:
                raise ValueError(f"Objetivo não encontrado: {goal_id}")
            
            milestone_id = f"milestone_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            milestone = Milestone(
                id=milestone_id,
                name=name,
                description=description,
                target_date=target_date
            )
            
            goal = self.goals[goal_id]
            if goal.milestones is None:
                goal.milestones = []
            
            goal.milestones.append(milestone)
            
            self.logger.debug(f"Marco adicionado ao objetivo {goal_id}: {name}")
            return milestone_id
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar marco: {e}")
            raise
    
    async def update_goal_progress(self, goal_id: str, progress: float):
        """Atualiza progresso de um objetivo"""
        try:
            if goal_id not in self.goals:
                raise ValueError(f"Objetivo não encontrado: {goal_id}")
            
            goal = self.goals[goal_id]
            old_progress = goal.progress
            goal.progress = max(0.0, min(1.0, progress))
            
            # Verificar se objetivo foi completado
            if goal.progress >= 1.0 and goal.status == GoalStatus.ACTIVE:
                await self._complete_goal(goal_id)
            
            self.logger.debug(f"Progresso atualizado para objetivo {goal_id}: {old_progress:.2f} -> {goal.progress:.2f}")
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar progresso: {e}")
            raise
    
    async def complete_milestone(self, goal_id: str, milestone_id: str):
        """Marca marco como completado"""
        try:
            if goal_id not in self.goals:
                raise ValueError(f"Objetivo não encontrado: {goal_id}")
            
            goal = self.goals[goal_id]
            if not goal.milestones:
                raise ValueError("Objetivo não possui marcos")
            
            milestone = None
            for m in goal.milestones:
                if m.id == milestone_id:
                    milestone = m
                    break
            
            if not milestone:
                raise ValueError(f"Marco não encontrado: {milestone_id}")
            
            milestone.completed = True
            milestone.completed_date = datetime.now()
            milestone.progress = 1.0
            
            # Atualizar progresso do objetivo baseado nos marcos
            await self._update_goal_progress_from_milestones(goal_id)
            
            self.logger.info(f"Marco completado: {milestone.name} (Objetivo: {goal.name})")
            
        except Exception as e:
            self.logger.error(f"Erro ao completar marco: {e}")
            raise
    
    async def _complete_goal(self, goal_id: str):
        """Marca objetivo como completado"""
        try:
            goal = self.goals[goal_id]
            goal.status = GoalStatus.COMPLETED
            goal.completed_date = datetime.now()
            goal.progress = 1.0
            
            # Atualizar estatísticas
            self.stats['goals_completed'] += 1
            
            # Calcular tempo de conclusão
            if goal.created_at:
                completion_time = (goal.completed_date - goal.created_at).total_seconds()
                self._update_average_completion_time(completion_time)
            
            self.logger.info(f"Objetivo completado: {goal.name}")
            
        except Exception as e:
            self.logger.error(f"Erro ao completar objetivo: {e}")
    
    async def _update_goal_progress_from_milestones(self, goal_id: str):
        """Atualiza progresso do objetivo baseado nos marcos"""
        try:
            goal = self.goals[goal_id]
            
            if not goal.milestones:
                return
            
            completed_milestones = sum(1 for m in goal.milestones if m.completed)
            total_milestones = len(goal.milestones)
            
            if total_milestones > 0:
                milestone_progress = completed_milestones / total_milestones
                
                # Combinar com progresso manual (se houver)
                combined_progress = max(goal.progress, milestone_progress)
                
                await self.update_goal_progress(goal_id, combined_progress)
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar progresso por marcos: {e}")
    
    async def _update_goals_progress(self):
        """Atualiza progresso de todos os objetivos ativos"""
        try:
            active_goals = [g for g in self.goals.values() if g.status == GoalStatus.ACTIVE]
            
            for goal in active_goals:
                # Atualizar progresso baseado em marcos
                if goal.milestones:
                    await self._update_goal_progress_from_milestones(goal.id)
                
                # Verificar critérios de sucesso automaticamente
                await self._check_success_criteria(goal.id)
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar progresso dos objetivos: {e}")
    
    async def _check_success_criteria(self, goal_id: str):
        """Verifica critérios de sucesso de um objetivo"""
        try:
            goal = self.goals[goal_id]
            
            if not goal.success_criteria:
                return
            
            # Implementação simplificada - em produção, seria mais sofisticada
            # Por exemplo, integração com sistemas externos para verificar critérios
            
            # Simular verificação de critérios
            criteria_met = 0
            for criterion in goal.success_criteria:
                # Lógica de verificação específica seria implementada aqui
                # Por enquanto, assumir que critérios são atendidos gradualmente
                if goal.progress >= 0.8:  # 80% de progresso
                    criteria_met += 1
            
            if criteria_met == len(goal.success_criteria) and goal.progress < 1.0:
                await self.update_goal_progress(goal_id, 1.0)
                
        except Exception as e:
            self.logger.error(f"Erro ao verificar critérios de sucesso: {e}")
    
    async def _check_deadlines(self):
        """Verifica prazos dos objetivos"""
        try:
            current_time = datetime.now()
            
            for goal in self.goals.values():
                if goal.status != GoalStatus.ACTIVE or not goal.target_date:
                    continue
                
                time_remaining = goal.target_date - current_time
                
                # Alertas baseados no tempo restante
                if time_remaining.total_seconds() < 0:
                    # Prazo vencido
                    self.logger.warning(f"Objetivo com prazo vencido: {goal.name}")
                elif time_remaining.days <= 1:
                    # Prazo crítico (1 dia)
                    self.logger.warning(f"Objetivo com prazo crítico: {goal.name}")
                elif time_remaining.days <= 7:
                    # Prazo próximo (1 semana)
                    self.logger.info(f"Objetivo com prazo próximo: {goal.name}")
                
                # Verificar marcos com prazos
                if goal.milestones:
                    for milestone in goal.milestones:
                        if not milestone.completed and milestone.target_date:
                            milestone_time_remaining = milestone.target_date - current_time
                            
                            if milestone_time_remaining.total_seconds() < 0:
                                self.logger.warning(f"Marco com prazo vencido: {milestone.name} (Objetivo: {goal.name})")
                                
        except Exception as e:
            self.logger.error(f"Erro ao verificar prazos: {e}")
    
    async def _analyze_dependencies(self):
        """Analisa dependências entre objetivos"""
        try:
            for goal in self.goals.values():
                if goal.status != GoalStatus.ACTIVE or not goal.dependencies:
                    continue
                
                # Verificar se dependências foram satisfeitas
                dependencies_met = True
                for dep_id in goal.dependencies:
                    if dep_id in self.goals:
                        dep_goal = self.goals[dep_id]
                        if dep_goal.status != GoalStatus.COMPLETED:
                            dependencies_met = False
                            break
                    else:
                        # Dependência não encontrada
                        self.logger.warning(f"Dependência não encontrada: {dep_id} (Objetivo: {goal.name})")
                        dependencies_met = False
                
                # Pausar objetivo se dependências não foram atendidas
                if not dependencies_met and goal.status == GoalStatus.ACTIVE:
                    goal.status = GoalStatus.PAUSED
                    self.logger.info(f"Objetivo pausado por dependências: {goal.name}")
                
                # Reativar objetivo se dependências foram atendidas
                elif dependencies_met and goal.status == GoalStatus.PAUSED:
                    goal.status = GoalStatus.ACTIVE
                    self.logger.info(f"Objetivo reativado: {goal.name}")
                    
        except Exception as e:
            self.logger.error(f"Erro ao analisar dependências: {e}")
    
    def _update_average_completion_time(self, completion_time: float):
        """Atualiza tempo médio de conclusão"""
        current_avg = self.stats['average_completion_time']
        completed_count = self.stats['goals_completed']
        
        if completed_count == 1:
            self.stats['average_completion_time'] = completion_time
        else:
            # Média móvel
            self.stats['average_completion_time'] = (
                (current_avg * (completed_count - 1) + completion_time) / completed_count
            )
    
    # Métodos de consulta e relatórios
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Retorna objetivo por ID"""
        return self.goals.get(goal_id)
    
    def get_goals_by_category(self, category: str) -> List[Goal]:
        """Retorna objetivos por categoria"""
        return [g for g in self.goals.values() if g.category == category]
    
    def get_goals_by_status(self, status: GoalStatus) -> List[Goal]:
        """Retorna objetivos por status"""
        return [g for g in self.goals.values() if g.status == status]
    
    def get_goals_by_priority(self, priority: GoalPriority) -> List[Goal]:
        """Retorna objetivos por prioridade"""
        return [g for g in self.goals.values() if g.priority == priority]
    
    def get_overdue_goals(self) -> List[Goal]:
        """Retorna objetivos com prazo vencido"""
        current_time = datetime.now()
        return [
            g for g in self.goals.values()
            if g.status == GoalStatus.ACTIVE 
            and g.target_date 
            and g.target_date < current_time
        ]
    
    def get_goals_summary(self) -> Dict[str, Any]:
        """Retorna resumo dos objetivos"""
        total_goals = len(self.goals)
        active_goals = len(self.get_goals_by_status(GoalStatus.ACTIVE))
        completed_goals = len(self.get_goals_by_status(GoalStatus.COMPLETED))
        overdue_goals = len(self.get_overdue_goals())
        
        # Calcular progresso médio dos objetivos ativos
        active_goal_list = self.get_goals_by_status(GoalStatus.ACTIVE)
        avg_progress = 0.0
        if active_goal_list:
            avg_progress = sum(g.progress for g in active_goal_list) / len(active_goal_list)
        
        return {
            'total_goals': total_goals,
            'active_goals': active_goals,
            'completed_goals': completed_goals,
            'overdue_goals': overdue_goals,
            'categories': list(self.goal_categories),
            'average_progress': avg_progress,
            'completion_rate': (completed_goals / max(1, total_goals)) * 100
        }
    
    def get_progress_report(self, goal_id: str) -> Dict[str, Any]:
        """Gera relatório de progresso de um objetivo"""
        if goal_id not in self.goals:
            return {}
        
        goal = self.goals[goal_id]
        
        # Calcular estatísticas de marcos
        milestone_stats = {}
        if goal.milestones:
            completed_milestones = sum(1 for m in goal.milestones if m.completed)
            total_milestones = len(goal.milestones)
            
            milestone_stats = {
                'total_milestones': total_milestones,
                'completed_milestones': completed_milestones,
                'milestone_completion_rate': (completed_milestones / total_milestones) * 100,
                'next_milestone': next(
                    (m for m in goal.milestones if not m.completed),
                    None
                )
            }
        
        # Calcular tempo decorrido
        elapsed_time = datetime.now() - goal.created_at
        
        # Estimar tempo restante
        estimated_remaining = None
        if goal.target_date:
            estimated_remaining = goal.target_date - datetime.now()
        
        return {
            'goal': asdict(goal),
            'milestone_stats': milestone_stats,
            'elapsed_time_days': elapsed_time.days,
            'estimated_remaining_days': estimated_remaining.days if estimated_remaining else None,
            'progress_percentage': goal.progress * 100,
            'is_on_track': self._is_goal_on_track(goal)
        }
    
    def _is_goal_on_track(self, goal: Goal) -> bool:
        """Verifica se objetivo está no cronograma"""
        if not goal.target_date:
            return True  # Sem prazo definido
        
        total_time = goal.target_date - goal.created_at
        elapsed_time = datetime.now() - goal.created_at
        
        if total_time.total_seconds() <= 0:
            return goal.progress >= 1.0
        
        expected_progress = elapsed_time.total_seconds() / total_time.total_seconds()
        return goal.progress >= expected_progress * 0.8  # 80% do progresso esperado
    
    async def suggest_actions(self, goal_id: str) -> List[str]:
        """Sugere ações para um objetivo"""
        try:
            if goal_id not in self.goals:
                return []
            
            goal = self.goals[goal_id]
            suggestions = []
            
            # Sugestões baseadas no status
            if goal.status == GoalStatus.ACTIVE:
                if goal.progress < 0.1:
                    suggestions.append("Definir primeiros passos concretos")
                    suggestions.append("Quebrar objetivo em tarefas menores")
                elif goal.progress < 0.5:
                    suggestions.append("Revisar progresso e ajustar estratégia")
                    suggestions.append("Identificar obstáculos principais")
                elif goal.progress < 0.9:
                    suggestions.append("Focar nos últimos marcos")
                    suggestions.append("Preparar finalização do objetivo")
                
                # Sugestões baseadas em prazos
                if goal.target_date:
                    time_remaining = goal.target_date - datetime.now()
                    if time_remaining.days <= 7:
                        suggestions.append("Priorizar este objetivo - prazo próximo")
                    elif time_remaining.total_seconds() < 0:
                        suggestions.append("Reavaliar prazo ou escopo do objetivo")
                
                # Sugestões baseadas em marcos
                if goal.milestones:
                    next_milestone = next((m for m in goal.milestones if not m.completed), None)
                    if next_milestone:
                        suggestions.append(f"Focar no próximo marco: {next_milestone.name}")
            
            elif goal.status == GoalStatus.PAUSED:
                suggestions.append("Revisar dependências e reativar se possível")
                suggestions.append("Considerar ajustar escopo ou recursos")
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Erro ao sugerir ações: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do gerenciador"""
        return {
            **self.stats,
            'goals_summary': self.get_goals_summary(),
            'is_monitoring': self.is_monitoring,
            'categories_count': len(self.goal_categories)
        }
