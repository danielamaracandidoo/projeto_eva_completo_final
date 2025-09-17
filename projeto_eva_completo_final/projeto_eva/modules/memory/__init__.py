"""
Sistema de memória da EVA.

Este módulo contém os sistemas de memória:
- EpisodicMemory: Memória episódica para histórico de conversas
- AffectiveMemory: Memória afetiva para relacionamento evolutivo
"""

from .episodic_memory import EpisodicMemory, EpisodicEntry
from .affective_memory import AffectiveMemory, AffectiveEntry, RelationshipSummary

__all__ = [
    'EpisodicMemory',
    'EpisodicEntry', 
    'AffectiveMemory',
    'AffectiveEntry',
    'RelationshipSummary'
]
