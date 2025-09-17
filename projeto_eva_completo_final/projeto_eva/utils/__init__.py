"""
Utilitários do sistema EVA.

Este módulo contém ferramentas auxiliares:
- logging_system: Sistema de logging centralizado
- hardware_monitor: Monitoramento de hardware e otimizações
"""

from .logging_system import EVALogger, PerformanceLogger, ConversationLogger, ErrorLogger
from .hardware_monitor import HardwareMonitor, VRAMManager, HardwareStats

__all__ = [
    'EVALogger',
    'PerformanceLogger',
    'ConversationLogger', 
    'ErrorLogger',
    'HardwareMonitor',
    'VRAMManager',
    'HardwareStats'
]
