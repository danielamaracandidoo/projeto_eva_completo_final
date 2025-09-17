"""
Módulo de processamento de voz da EVA.

Este módulo contém:
- speech_to_text: Conversão de fala para texto (STT)
- text_to_speech: Conversão de texto para fala (TTS)
- voice_interface: Interface de voz completa
"""

from .speech_to_text import SpeechToTextProcessor
from .text_to_speech import TextToSpeechProcessor
from .voice_interface import VoiceInterface

__all__ = [
    'SpeechToTextProcessor',
    'TextToSpeechProcessor',
    'VoiceInterface'
]
