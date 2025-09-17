"""
Executor de tarefas da EVA.
Responsável por executar ações e tarefas de forma autônoma.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

from utils.logging_system import EVALogger

class TaskStatus(Enum):
    """Status de execução de tarefa"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class TaskPriority(Enum):
    """Prioridade de tarefa"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class Task:
    """Representação de uma tarefa"""
    id: str
    name: str
    description: str
    action_type: str
    parameters: Dict[str, Any]
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: float = 0.0
    dependencies: List[str] = None
    timeout: Optional[int] = None

class TaskExecutor:
    """
    Executor de tarefas da EVA.
    
    Funcionalidades:
    - Execução assíncrona de tarefas
    - Gerenciamento de fila de tarefas
    - Controle de prioridades
    - Monitoramento de progresso
    - Tratamento de dependências
    - Sistema de timeout
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = EVALogger.get_logger("TaskExecutor")
        
        # Fila de tarefas
        self.task_queue: List[Task] = []
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        
        # Configurações
        self.max_concurrent_tasks = config.agency.max_concurrent_tasks
        self.default_timeout = config.agency.task_timeout
        
        # Executores de ação
        self.action_executors: Dict[str, Callable] = {}
        
        # Estado
        self.is_running = False
        self.executor_task: Optional[asyncio.Task] = None
        
        # Estatísticas
        self.stats = {
            'tasks_executed': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_execution_time': 0.0
        }
        
        self._register_default_actions()
        
        self.logger.info("TaskExecutor inicializado")
    
    def _register_default_actions(self):
        """Registra ações padrão do executor"""
        self.action_executors.update({
            'send_message': self._execute_send_message,
            'web_search': self._execute_web_search,
            'file_operation': self._execute_file_operation,
            'calculation': self._execute_calculation,
            'reminder': self._execute_reminder,
            'system_command': self._execute_system_command,
            'api_call': self._execute_api_call,
            'data_analysis': self._execute_data_analysis
        })
    
    async def start(self):
        """Inicia o executor de tarefas"""
        try:
            if self.is_running:
                self.logger.warning("TaskExecutor já está rodando")
                return
            
            self.is_running = True
            self.executor_task = asyncio.create_task(self._execution_loop())
            
            self.logger.info("TaskExecutor iniciado")
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar TaskExecutor: {e}")
            raise
    
    async def stop(self):
        """Para o executor de tarefas"""
        try:
            self.is_running = False
            
            # Cancelar tarefas em execução
            for task in self.running_tasks.values():
                task.status = TaskStatus.CANCELLED
            
            # Cancelar loop de execução
            if self.executor_task:
                self.executor_task.cancel()
                try:
                    await self.executor_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("TaskExecutor parado")
            
        except Exception as e:
            self.logger.error(f"Erro ao parar TaskExecutor: {e}")
    
    async def _execution_loop(self):
        """Loop principal de execução de tarefas"""
        try:
            while self.is_running:
                # Processar fila de tarefas
                await self._process_task_queue()
                
                # Verificar tarefas em execução
                await self._check_running_tasks()
                
                # Aguardar antes da próxima iteração
                await asyncio.sleep(0.5)
                
        except asyncio.CancelledError:
            self.logger.info("Loop de execução cancelado")
        except Exception as e:
            self.logger.error(f"Erro no loop de execução: {e}")
    
    async def _process_task_queue(self):
        """Processa fila de tarefas"""
        try:
            # Verificar se pode executar mais tarefas
            if len(self.running_tasks) >= self.max_concurrent_tasks:
                return
            
            # Ordenar por prioridade
            self.task_queue.sort(key=lambda t: t.priority.value, reverse=True)
            
            # Executar tarefas prontas
            tasks_to_remove = []
            
            for task in self.task_queue:
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    break
                
                # Verificar dependências
                if self._check_dependencies(task):
                    await self._start_task_execution(task)
                    tasks_to_remove.append(task)
            
            # Remover tarefas iniciadas da fila
            for task in tasks_to_remove:
                self.task_queue.remove(task)
                
        except Exception as e:
            self.logger.error(f"Erro ao processar fila de tarefas: {e}")
    
    def _check_dependencies(self, task: Task) -> bool:
        """Verifica se dependências da tarefa foram satisfeitas"""
        if not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
            
            dep_task = self.completed_tasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    async def _start_task_execution(self, task: Task):
        """Inicia execução de uma tarefa"""
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            self.running_tasks[task.id] = task
            
            self.logger.debug(f"Iniciando execução da tarefa: {task.name}")
            
            # Criar task assíncrona para execução
            execution_task = asyncio.create_task(self._execute_task(task))
            
            # Não aguardar aqui para permitir execução paralela
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar execução da tarefa {task.name}: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
    
    async def _execute_task(self, task: Task):
        """Executa uma tarefa específica"""
        try:
            # Verificar timeout
            timeout = task.timeout or self.default_timeout
            
            # Executar com timeout
            result = await asyncio.wait_for(
                self._run_task_action(task),
                timeout=timeout
            )
            
            # Tarefa completada com sucesso
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            task.progress = 1.0
            
            # Mover para tarefas completadas
            self.running_tasks.pop(task.id, None)
            self.completed_tasks[task.id] = task
            
            # Atualizar estatísticas
            self.stats['tasks_completed'] += 1
            self.stats['tasks_executed'] += 1
            
            if task.started_at:
                execution_time = (task.completed_at - task.started_at).total_seconds()
                self.stats['total_execution_time'] += execution_time
            
            self.logger.debug(f"Tarefa completada: {task.name}")
            
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout na execução da tarefa: {task.name}")
            task.status = TaskStatus.FAILED
            task.error = "Timeout"
            self._handle_task_failure(task)
            
        except Exception as e:
            self.logger.error(f"Erro na execução da tarefa {task.name}: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self._handle_task_failure(task)
    
    async def _run_task_action(self, task: Task) -> Any:
        """Executa a ação específica da tarefa"""
        action_type = task.action_type
        
        if action_type not in self.action_executors:
            raise ValueError(f"Tipo de ação não suportado: {action_type}")
        
        executor = self.action_executors[action_type]
        return await executor(task.parameters)
    
    def _handle_task_failure(self, task: Task):
        """Manipula falha na execução de tarefa"""
        self.running_tasks.pop(task.id, None)
        self.completed_tasks[task.id] = task
        self.stats['tasks_failed'] += 1
        self.stats['tasks_executed'] += 1
    
    async def _check_running_tasks(self):
        """Verifica status de tarefas em execução"""
        try:
            # Verificar se alguma tarefa travou ou precisa de atenção
            current_time = datetime.now()
            
            for task in list(self.running_tasks.values()):
                if task.started_at:
                    elapsed = (current_time - task.started_at).total_seconds()
                    
                    # Verificar se excedeu timeout
                    timeout = task.timeout or self.default_timeout
                    if elapsed > timeout * 1.5:  # 50% de margem
                        self.logger.warning(f"Tarefa possivelmente travada: {task.name}")
                        
        except Exception as e:
            self.logger.error(f"Erro ao verificar tarefas em execução: {e}")
    
    # Executores de ação específicos
    
    async def _execute_send_message(self, params: Dict[str, Any]) -> str:
        """Executa ação de envio de mensagem"""
        try:
            recipient = params.get('recipient', 'user')
            message = params.get('message', '')
            
            # Simular envio de mensagem
            await asyncio.sleep(0.1)
            
            self.logger.info(f"Mensagem enviada para {recipient}: {message}")
            return f"Mensagem enviada com sucesso para {recipient}"
            
        except Exception as e:
            raise Exception(f"Erro ao enviar mensagem: {e}")
    
    async def _execute_web_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa ação de busca na web"""
        try:
            query = params.get('query', '')
            max_results = params.get('max_results', 5)
            
            # Simular busca na web
            await asyncio.sleep(1.0)
            
            results = {
                'query': query,
                'results': [
                    {'title': f'Resultado {i+1} para {query}', 'url': f'https://example.com/{i+1}'}
                    for i in range(max_results)
                ]
            }
            
            self.logger.debug(f"Busca realizada: {query}")
            return results
            
        except Exception as e:
            raise Exception(f"Erro na busca web: {e}")
    
    async def _execute_file_operation(self, params: Dict[str, Any]) -> str:
        """Executa operação de arquivo"""
        try:
            operation = params.get('operation', 'read')
            file_path = params.get('file_path', '')
            
            # Simular operação de arquivo
            await asyncio.sleep(0.5)
            
            if operation == 'read':
                result = f"Conteúdo lido de {file_path}"
            elif operation == 'write':
                content = params.get('content', '')
                result = f"Conteúdo escrito em {file_path}"
            elif operation == 'delete':
                result = f"Arquivo {file_path} deletado"
            else:
                result = f"Operação {operation} executada em {file_path}"
            
            self.logger.debug(f"Operação de arquivo: {operation} em {file_path}")
            return result
            
        except Exception as e:
            raise Exception(f"Erro na operação de arquivo: {e}")
    
    async def _execute_calculation(self, params: Dict[str, Any]) -> float:
        """Executa cálculo matemático"""
        try:
            expression = params.get('expression', '0')
            
            # Simular cálculo
            await asyncio.sleep(0.1)
            
            # Avaliação segura de expressão matemática básica
            allowed_chars = set('0123456789+-*/.() ')
            if all(c in allowed_chars for c in expression):
                result = eval(expression)
            else:
                raise ValueError("Expressão matemática inválida")
            
            self.logger.debug(f"Cálculo executado: {expression} = {result}")
            return result
            
        except Exception as e:
            raise Exception(f"Erro no cálculo: {e}")
    
    async def _execute_reminder(self, params: Dict[str, Any]) -> str:
        """Executa lembrete"""
        try:
            message = params.get('message', '')
            delay = params.get('delay', 0)  # segundos
            
            if delay > 0:
                await asyncio.sleep(delay)
            
            result = f"Lembrete: {message}"
            self.logger.info(result)
            return result
            
        except Exception as e:
            raise Exception(f"Erro no lembrete: {e}")
    
    async def _execute_system_command(self, params: Dict[str, Any]) -> str:
        """Executa comando do sistema"""
        try:
            command = params.get('command', '')
            
            # Por segurança, apenas simular
            await asyncio.sleep(0.5)
            
            result = f"Comando simulado: {command}"
            self.logger.debug(result)
            return result
            
        except Exception as e:
            raise Exception(f"Erro no comando do sistema: {e}")
    
    async def _execute_api_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa chamada de API"""
        try:
            url = params.get('url', '')
            method = params.get('method', 'GET')
            
            # Simular chamada de API
            await asyncio.sleep(1.0)
            
            result = {
                'status': 200,
                'url': url,
                'method': method,
                'response': 'Resposta simulada da API'
            }
            
            self.logger.debug(f"API chamada: {method} {url}")
            return result
            
        except Exception as e:
            raise Exception(f"Erro na chamada de API: {e}")
    
    async def _execute_data_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa análise de dados"""
        try:
            data_source = params.get('data_source', '')
            analysis_type = params.get('analysis_type', 'basic')
            
            # Simular análise de dados
            await asyncio.sleep(2.0)
            
            result = {
                'data_source': data_source,
                'analysis_type': analysis_type,
                'summary': 'Análise concluída com sucesso',
                'insights': ['Insight 1', 'Insight 2', 'Insight 3']
            }
            
            self.logger.debug(f"Análise de dados: {analysis_type} em {data_source}")
            return result
            
        except Exception as e:
            raise Exception(f"Erro na análise de dados: {e}")
    
    # Métodos públicos para gerenciamento de tarefas
    
    async def add_task(
        self,
        name: str,
        description: str,
        action_type: str,
        parameters: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: Optional[List[str]] = None,
        timeout: Optional[int] = None
    ) -> str:
        """Adiciona nova tarefa à fila"""
        try:
            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            task = Task(
                id=task_id,
                name=name,
                description=description,
                action_type=action_type,
                parameters=parameters,
                priority=priority,
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                dependencies=dependencies or [],
                timeout=timeout
            )
            
            self.task_queue.append(task)
            
            self.logger.debug(f"Tarefa adicionada: {name} (ID: {task_id})")
            return task_id
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar tarefa: {e}")
            raise
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Retorna status de uma tarefa"""
        # Verificar tarefas em execução
        if task_id in self.running_tasks:
            return self.running_tasks[task_id].status
        
        # Verificar tarefas completadas
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id].status
        
        # Verificar fila
        for task in self.task_queue:
            if task.id == task_id:
                return task.status
        
        return None
    
    def get_task_result(self, task_id: str) -> Optional[Any]:
        """Retorna resultado de uma tarefa completada"""
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            if task.status == TaskStatus.COMPLETED:
                return task.result
        
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancela uma tarefa"""
        try:
            # Verificar fila
            for task in self.task_queue:
                if task.id == task_id:
                    task.status = TaskStatus.CANCELLED
                    self.task_queue.remove(task)
                    self.completed_tasks[task_id] = task
                    return True
            
            # Verificar tarefas em execução
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                task.status = TaskStatus.CANCELLED
                # Nota: tarefa assíncrona continuará, mas será marcada como cancelada
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao cancelar tarefa: {e}")
            return False
    
    def register_action_executor(self, action_type: str, executor: Callable):
        """Registra novo executor de ação"""
        self.action_executors[action_type] = executor
        self.logger.debug(f"Executor registrado para ação: {action_type}")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Retorna status da fila de tarefas"""
        return {
            'pending_tasks': len(self.task_queue),
            'running_tasks': len(self.running_tasks),
            'completed_tasks': len(self.completed_tasks),
            'max_concurrent': self.max_concurrent_tasks,
            'is_running': self.is_running
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do executor"""
        return {
            **self.stats,
            'queue_status': self.get_queue_status(),
            'average_execution_time': (
                self.stats['total_execution_time'] / max(1, self.stats['tasks_executed'])
            ),
            'success_rate': (
                self.stats['tasks_completed'] / max(1, self.stats['tasks_executed'])
            ) * 100
        }
