"""
Core components of the EVA system.

This package contains the central orchestration and management components
that coordinate all aspects of the EVA assistant.
"""

from .orchestrator import EVAOrchestrator
from .model_manager import ModelManager
from .consciousness import ConsciousnessSystem
from .attention_system import AttentionSystem

__all__ = [
    'EVAOrchestrator',
    'ModelManager', 
    'ConsciousnessSystem',
    'AttentionSystem'
]
