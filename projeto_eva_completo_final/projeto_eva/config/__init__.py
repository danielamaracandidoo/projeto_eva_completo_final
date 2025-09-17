"""
Configurações do sistema EVA.

Este módulo contém:
- settings: Configurações centralizadas do sistema
- prompts: Galeria de prompts para diferentes contextos
"""

from .settings import EVAConfig, ModelConfig, MemoryConfig, VoiceConfig, HardwareConfig
from .prompts import SYSTEM_PROMPTS, SYNTHESIS_PROMPT, REFLECTION_PROMPT, EMOTIONAL_ANALYSIS_PROMPT

__all__ = [
    'EVAConfig',
    'ModelConfig',
    'MemoryConfig', 
    'VoiceConfig',
    'HardwareConfig',
    'SYSTEM_PROMPTS',
    'SYNTHESIS_PROMPT',
    'REFLECTION_PROMPT',
    'EMOTIONAL_ANALYSIS_PROMPT'
]
