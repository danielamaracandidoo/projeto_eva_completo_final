"""
Interface de voz completa da EVA.
Integra STT e TTS para comunicação por voz.
"""

import asyncio
from typing import Optional, Dict, Any, Callable
from enum import Enum

from .speech_to_text import SpeechToTextProcessor
from .text_to_speech import TextToSpeechProcessor
from utils.logging_system import EVALogger

class VoiceState(Enum):
    """Estados da interface de voz"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"

class VoiceInterface:
    """
    Interface de voz completa da EVA.
    
    Funcionalidades:
    - Comunicação bidirecional por voz
    - Detecção de ativação por voz
    - Controle de conversação
    - Integração com sistema de consciência
    - Feedback de estado em tempo real
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = EVALogger.get_logger("VoiceInterface")
        
        # Processadores
        self.stt_processor = SpeechToTextProcessor(config)
        self.tts_processor = TextToSpeechProcessor(config)
        
        # Estado da interface
        self.state = VoiceState.IDLE
        self.is_active = False
        
        # Configurações de ativação
        self.wake_words = config.voice.wake_words
        self.activation_threshold = config.voice.activation_threshold
        self.silence_timeout = config.voice.silence_timeout
        
        # Callbacks
        self.on_wake_word_detected: Optional[Callable] = None
        self.on_speech_recognized: Optional[Callable] = None
        self.on_response_ready: Optional[Callable] = None
        self.on_state_changed: Optional[Callable] = None
        
        # Controle de conversação
        self.conversation_active = False
        self.last_interaction_time = None
        
        self.logger.info("VoiceInterface inicializada")
    
    async def initialize(self):
        """Inicializa a interface de voz"""
        try:
            self.logger.info("Inicializando interface de voz...")
            
            # Inicializar processadores
            await self.stt_processor.initialize()
            await self.tts_processor.initialize()
            
            # Definir estado inicial
            await self._set_state(VoiceState.IDLE)
            
            self.logger.info("Interface de voz inicializada com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização da interface de voz: {e}")
            await self._set_state(VoiceState.ERROR)
            raise
    
    async def start_voice_interaction(self):
        """Inicia interação por voz"""
        try:
            if self.is_active:
                self.logger.warning("Interface de voz já está ativa")
                return
            
            self.is_active = True
            await self._set_state(VoiceState.LISTENING)
            
            # Iniciar loop de escuta
            asyncio.create_task(self._voice_interaction_loop())
            
            self.logger.info("Interação por voz iniciada")
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar interação por voz: {e}")
            await self._set_state(VoiceState.ERROR)
    
    async def stop_voice_interaction(self):
        """Para interação por voz"""
        try:
            self.is_active = False
            self.conversation_active = False
            
            # Parar processadores
            if self.stt_processor.is_recording_active():
                await self.stt_processor.stop_recording()
            
            if self.tts_processor.is_speaking_active():
                await self.tts_processor.stop_speaking()
            
            await self._set_state(VoiceState.IDLE)
            
            self.logger.info("Interação por voz parada")
            
        except Exception as e:
            self.logger.error(f"Erro ao parar interação por voz: {e}")
    
    async def _voice_interaction_loop(self):
        """Loop principal de interação por voz"""
        try:
            while self.is_active:
                if self.state == VoiceState.LISTENING:
                    await self._listen_for_input()
                elif self.state == VoiceState.PROCESSING:
                    await asyncio.sleep(0.1)  # Aguardar processamento
                elif self.state == VoiceState.SPEAKING:
                    await asyncio.sleep(0.1)  # Aguardar fala
                else:
                    await asyncio.sleep(0.5)  # Estado idle ou erro
                    
        except Exception as e:
            self.logger.error(f"Erro no loop de interação por voz: {e}")
            await self._set_state(VoiceState.ERROR)
    
    async def _listen_for_input(self):
        """Escuta entrada de voz"""
        try:
            # Iniciar gravação
            if not self.stt_processor.is_recording_active():
                success = await self.stt_processor.start_recording()
                if not success:
                    self.logger.error("Falha ao iniciar gravação")
                    return
            
            # Aguardar por um período ou até detectar fala
            await asyncio.sleep(2.0)  # Gravar por 2 segundos
            
            # Parar gravação e transcrever
            transcription = await self.stt_processor.stop_recording()
            
            if transcription and transcription.strip():
                await self._process_speech_input(transcription)
            else:
                # Nenhuma fala detectada, continuar escutando
                await asyncio.sleep(0.5)
                
        except Exception as e:
            self.logger.error(f"Erro ao escutar entrada: {e}")
    
    async def _process_speech_input(self, transcription: str):
        """Processa entrada de fala transcrita"""
        try:
            await self._set_state(VoiceState.PROCESSING)
            
            self.logger.debug(f"Fala transcrita: {transcription}")
            
            # Verificar wake words se não em conversação
            if not self.conversation_active:
                if await self._check_wake_words(transcription):
                    self.conversation_active = True
                    await self._handle_wake_word_detected(transcription)
                    return
                else:
                    # Não é wake word, voltar a escutar
                    await self._set_state(VoiceState.LISTENING)
                    return
            
            # Processar comando/pergunta
            await self._handle_speech_recognized(transcription)
            
        except Exception as e:
            self.logger.error(f"Erro ao processar entrada de fala: {e}")
            await self._set_state(VoiceState.LISTENING)
    
    async def _check_wake_words(self, text: str) -> bool:
        """Verifica se texto contém wake words"""
        try:
            text_lower = text.lower()
            
            for wake_word in self.wake_words:
                if wake_word.lower() in text_lower:
                    self.logger.debug(f"Wake word detectada: {wake_word}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar wake words: {e}")
            return False
    
    async def _handle_wake_word_detected(self, text: str):
        """Manipula detecção de wake word"""
        try:
            self.logger.info("Wake word detectada, ativando conversação")
            
            # Callback para wake word
            if self.on_wake_word_detected:
                await self.on_wake_word_detected(text)
            
            # Resposta de ativação
            activation_responses = [
                "Oi! Como posso ajudar?",
                "Olá! Estou aqui para você.",
                "Sim? Em que posso ajudar?",
                "Oi! O que você gostaria de saber?"
            ]
            
            import random
            response = random.choice(activation_responses)
            
            await self.speak_response(response)
            
        except Exception as e:
            self.logger.error(f"Erro ao manipular wake word: {e}")
    
    async def _handle_speech_recognized(self, text: str):
        """Manipula fala reconhecida"""
        try:
            # Callback para fala reconhecida
            if self.on_speech_recognized:
                response = await self.on_speech_recognized(text)
                
                if response:
                    await self.speak_response(response)
                else:
                    await self._set_state(VoiceState.LISTENING)
            else:
                # Sem callback, resposta padrão
                await self.speak_response("Desculpe, não consegui processar sua solicitação.")
                
        except Exception as e:
            self.logger.error(f"Erro ao manipular fala reconhecida: {e}")
            await self._set_state(VoiceState.LISTENING)
    
    async def speak_response(self, text: str, voice: Optional[str] = None):
        """Fala uma resposta"""
        try:
            await self._set_state(VoiceState.SPEAKING)
            
            # Callback para resposta pronta
            if self.on_response_ready:
                await self.on_response_ready(text)
            
            # Falar texto
            success = await self.tts_processor.speak(text, voice=voice, wait=True)
            
            if success:
                # Voltar a escutar após falar
                await self._set_state(VoiceState.LISTENING)
            else:
                self.logger.error("Falha na síntese de fala")
                await self._set_state(VoiceState.ERROR)
                
        except Exception as e:
            self.logger.error(f"Erro ao falar resposta: {e}")
            await self._set_state(VoiceState.ERROR)
    
    async def process_text_input(self, text: str) -> Optional[str]:
        """Processa entrada de texto (para modo híbrido)"""
        try:
            if self.on_speech_recognized:
                response = await self.on_speech_recognized(text)
                return response
            else:
                return "Processamento de texto não configurado."
                
        except Exception as e:
            self.logger.error(f"Erro ao processar entrada de texto: {e}")
            return "Erro no processamento."
    
    async def _set_state(self, new_state: VoiceState):
        """Define novo estado da interface"""
        try:
            if self.state != new_state:
                old_state = self.state
                self.state = new_state
                
                self.logger.debug(f"Estado alterado: {old_state.value} -> {new_state.value}")
                
                # Callback para mudança de estado
                if self.on_state_changed:
                    await self.on_state_changed(old_state, new_state)
                    
        except Exception as e:
            self.logger.error(f"Erro ao definir estado: {e}")
    
    def set_callbacks(
        self,
        on_wake_word_detected: Optional[Callable] = None,
        on_speech_recognized: Optional[Callable] = None,
        on_response_ready: Optional[Callable] = None,
        on_state_changed: Optional[Callable] = None
    ):
        """Define callbacks da interface"""
        self.on_wake_word_detected = on_wake_word_detected
        self.on_speech_recognized = on_speech_recognized
        self.on_response_ready = on_response_ready
        self.on_state_changed = on_state_changed
        
        self.logger.debug("Callbacks configurados")
    
    async def transcribe_audio_file(self, audio_file_path: str) -> Optional[str]:
        """Transcreve arquivo de áudio"""
        try:
            result = await self.stt_processor.transcribe_file(audio_file_path)
            return result.get("text")
            
        except Exception as e:
            self.logger.error(f"Erro ao transcrever arquivo: {e}")
            return None
    
    async def synthesize_to_file(self, text: str, output_path: str) -> bool:
        """Sintetiza texto para arquivo"""
        try:
            result_path = await self.tts_processor.synthesize_to_file(text, output_path)
            return result_path is not None
            
        except Exception as e:
            self.logger.error(f"Erro ao sintetizar para arquivo: {e}")
            return False
    
    async def get_voice_capabilities(self) -> Dict[str, Any]:
        """Retorna capacidades da interface de voz"""
        try:
            stt_devices = self.stt_processor.get_device_info()
            tts_voices = await self.tts_processor.get_available_voices()
            
            return {
                'stt': {
                    'supported_formats': self.stt_processor.get_supported_formats(),
                    'devices': stt_devices,
                    'model': self.stt_processor.model_name
                },
                'tts': {
                    'available_voices': tts_voices,
                    'engine': self.tts_processor.tts_engine,
                    'current_voice': self.tts_processor.voice_model
                },
                'interface': {
                    'wake_words': self.wake_words,
                    'current_state': self.state.value,
                    'conversation_active': self.conversation_active
                }
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter capacidades: {e}")
            return {}
    
    async def configure_voice_settings(
        self,
        wake_words: Optional[list] = None,
        tts_voice: Optional[str] = None,
        tts_speed: Optional[float] = None,
        activation_threshold: Optional[float] = None
    ):
        """Configura parâmetros da interface de voz"""
        try:
            if wake_words is not None:
                self.wake_words = wake_words
                self.logger.debug(f"Wake words atualizadas: {wake_words}")
            
            if tts_voice is not None or tts_speed is not None:
                await self.tts_processor.set_voice_parameters(
                    voice=tts_voice,
                    speed=tts_speed
                )
            
            if activation_threshold is not None:
                self.activation_threshold = activation_threshold
                self.logger.debug(f"Threshold de ativação: {activation_threshold}")
                
        except Exception as e:
            self.logger.error(f"Erro ao configurar interface de voz: {e}")
    
    def get_current_state(self) -> VoiceState:
        """Retorna estado atual da interface"""
        return self.state
    
    def is_conversation_active(self) -> bool:
        """Verifica se conversação está ativa"""
        return self.conversation_active
    
    async def end_conversation(self):
        """Encerra conversação atual"""
        try:
            self.conversation_active = False
            
            # Falar despedida
            farewell_messages = [
                "Até logo!",
                "Foi um prazer conversar com você!",
                "Estarei aqui quando precisar!",
                "Tchau! Volte sempre!"
            ]
            
            import random
            farewell = random.choice(farewell_messages)
            
            await self.speak_response(farewell)
            
            self.logger.info("Conversação encerrada")
            
        except Exception as e:
            self.logger.error(f"Erro ao encerrar conversação: {e}")
    
    async def cleanup(self):
        """Limpa recursos da interface de voz"""
        try:
            # Parar interação
            await self.stop_voice_interaction()
            
            # Limpar processadores
            await self.stt_processor.cleanup()
            await self.tts_processor.cleanup()
            
            self.logger.info("VoiceInterface limpa")
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza da interface de voz: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da interface de voz"""
        return {
            'state': self.state.value,
            'is_active': self.is_active,
            'conversation_active': self.conversation_active,
            'wake_words': self.wake_words,
            'stt_stats': self.stt_processor.get_stats(),
            'tts_stats': self.tts_processor.get_stats()
        }
