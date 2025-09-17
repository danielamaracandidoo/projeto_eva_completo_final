"""
Processador de Speech-to-Text (STT) usando Whisper.
"""

import asyncio
import os
import tempfile
import wave
from typing import Optional, Dict, Any
from pathlib import Path

import numpy as np
import torch
import whisper
import pyaudio

from utils.logging_system import EVALogger

class SpeechToTextProcessor:
    """
    Processador de Speech-to-Text usando OpenAI Whisper.
    
    Funcionalidades:
    - Transcrição de arquivos de áudio
    - Captura e transcrição em tempo real
    - Suporte a múltiplos formatos de áudio
    - Detecção de idioma automática
    - Processamento local (privacidade)
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = EVALogger.get_logger("SpeechToTextProcessor")
        
        # Configurações de áudio
        self.sample_rate = config.voice.sample_rate
        self.chunk_size = config.voice.chunk_size
        self.channels = config.voice.channels
        self.format = pyaudio.paInt16
        
        # Modelo Whisper
        self.model_name = config.voice.whisper_model
        self.model: Optional[whisper.Whisper] = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Estado de gravação
        self.is_recording = False
        self.audio_buffer = []
        
        # PyAudio
        self.pyaudio_instance: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        
        self.logger.info(f"SpeechToTextProcessor inicializado (device: {self.device})")
    
    async def initialize(self):
        """Inicializa o processador STT"""
        try:
            self.logger.info(f"Carregando modelo Whisper: {self.model_name}")
            
            # Carregar modelo Whisper em thread separada
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, whisper.load_model, self.model_name, self.device
            )
            
            # Inicializar PyAudio
            self.pyaudio_instance = pyaudio.PyAudio()
            
            self.logger.info("SpeechToTextProcessor inicializado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização do STT: {e}")
            raise
    
    async def transcribe_file(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Transcreve um arquivo de áudio.
        
        Args:
            audio_file_path: Caminho para o arquivo de áudio
            
        Returns:
            Dicionário com transcrição e metadados
        """
        try:
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {audio_file_path}")
            
            self.logger.debug(f"Transcrevendo arquivo: {audio_file_path}")
            
            # Transcrever em thread separada
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.model.transcribe, audio_file_path
            )
            
            # Extrair informações
            transcription = result["text"].strip()
            language = result.get("language", "unknown")
            
            # Calcular confiança média dos segmentos
            segments = result.get("segments", [])
            if segments:
                avg_confidence = sum(
                    segment.get("avg_logprob", 0) for segment in segments
                ) / len(segments)
                # Converter log prob para confiança (aproximação)
                confidence = min(1.0, max(0.0, (avg_confidence + 1.0) / 1.0))
            else:
                confidence = 0.8  # Padrão
            
            self.logger.debug(f"Transcrição concluída: {len(transcription)} caracteres")
            
            return {
                "text": transcription,
                "language": language,
                "confidence": confidence,
                "duration": result.get("duration", 0),
                "segments": segments
            }
            
        except Exception as e:
            self.logger.error(f"Erro na transcrição do arquivo: {e}")
            return {
                "text": "",
                "language": "unknown",
                "confidence": 0.0,
                "duration": 0,
                "segments": [],
                "error": str(e)
            }
    
    async def start_recording(self) -> bool:
        """
        Inicia gravação de áudio em tempo real.
        
        Returns:
            True se iniciou com sucesso, False caso contrário
        """
        try:
            if self.is_recording:
                self.logger.warning("Gravação já está em andamento")
                return False
            
            # Configurar stream de áudio
            self.stream = self.pyaudio_instance.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_recording = True
            self.audio_buffer = []
            
            self.stream.start_stream()
            
            self.logger.info("Gravação iniciada")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar gravação: {e}")
            return False
    
    async def stop_recording(self) -> Optional[str]:
        """
        Para gravação e transcreve o áudio capturado.
        
        Returns:
            Texto transcrito ou None se erro
        """
        try:
            if not self.is_recording:
                self.logger.warning("Nenhuma gravação em andamento")
                return None
            
            # Parar stream
            self.stream.stop_stream()
            self.stream.close()
            self.is_recording = False
            
            if not self.audio_buffer:
                self.logger.warning("Buffer de áudio vazio")
                return None
            
            # Converter buffer para arquivo temporário
            audio_data = b''.join(self.audio_buffer)
            temp_file = await self._save_audio_buffer(audio_data)
            
            try:
                # Transcrever áudio
                result = await self.transcribe_file(temp_file)
                return result.get("text", "")
                
            finally:
                # Limpar arquivo temporário
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            
        except Exception as e:
            self.logger.error(f"Erro ao parar gravação: {e}")
            return None
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback para captura de áudio em tempo real"""
        if self.is_recording:
            self.audio_buffer.append(in_data)
        return (in_data, pyaudio.paContinue)
    
    async def _save_audio_buffer(self, audio_data: bytes) -> str:
        """Salva buffer de áudio em arquivo temporário"""
        try:
            # Criar arquivo temporário
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Salvar como WAV
            with wave.open(temp_path, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.pyaudio_instance.get_sample_size(self.format))
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
            
            return temp_path
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar buffer de áudio: {e}")
            raise
    
    async def transcribe_realtime_chunk(self, audio_chunk: bytes) -> Optional[str]:
        """
        Transcreve um chunk de áudio em tempo real.
        
        Args:
            audio_chunk: Dados de áudio em bytes
            
        Returns:
            Texto transcrito ou None
        """
        try:
            # Salvar chunk temporariamente
            temp_file = await self._save_audio_buffer(audio_chunk)
            
            try:
                # Transcrever
                result = await self.transcribe_file(temp_file)
                text = result.get("text", "").strip()
                
                # Filtrar transcrições muito curtas ou vazias
                if len(text) < 3:
                    return None
                
                return text
                
            finally:
                # Limpar arquivo temporário
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except Exception as e:
            self.logger.error(f"Erro na transcrição em tempo real: {e}")
            return None
    
    def is_recording_active(self) -> bool:
        """Verifica se gravação está ativa"""
        return self.is_recording
    
    def get_supported_formats(self) -> list:
        """Retorna formatos de áudio suportados"""
        return ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.wma']
    
    async def detect_language(self, audio_file_path: str) -> str:
        """
        Detecta idioma de um arquivo de áudio.
        
        Args:
            audio_file_path: Caminho para arquivo de áudio
            
        Returns:
            Código do idioma detectado
        """
        try:
            # Carregar apenas uma pequena parte para detecção
            loop = asyncio.get_event_loop()
            
            # Usar função de detecção do Whisper
            audio = await loop.run_in_executor(
                None, whisper.load_audio, audio_file_path
            )
            
            # Detectar idioma
            audio_segment = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio_segment).to(self.device)
            
            _, probs = self.model.detect_language(mel)
            detected_language = max(probs, key=probs.get)
            
            self.logger.debug(f"Idioma detectado: {detected_language} (confiança: {probs[detected_language]:.2f})")
            
            return detected_language
            
        except Exception as e:
            self.logger.error(f"Erro na detecção de idioma: {e}")
            return "pt"  # Padrão português
    
    async def get_audio_info(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Obtém informações sobre um arquivo de áudio.
        
        Args:
            audio_file_path: Caminho para arquivo de áudio
            
        Returns:
            Dicionário com informações do áudio
        """
        try:
            # Carregar áudio
            loop = asyncio.get_event_loop()
            audio = await loop.run_in_executor(
                None, whisper.load_audio, audio_file_path
            )
            
            duration = len(audio) / whisper.audio.SAMPLE_RATE
            
            return {
                "duration": duration,
                "sample_rate": whisper.audio.SAMPLE_RATE,
                "channels": 1,  # Whisper sempre converte para mono
                "file_size": os.path.getsize(audio_file_path),
                "format": Path(audio_file_path).suffix.lower()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter informações do áudio: {e}")
            return {}
    
    def get_device_info(self) -> Dict[str, Any]:
        """Retorna informações sobre dispositivos de áudio"""
        try:
            if not self.pyaudio_instance:
                return {}
            
            device_count = self.pyaudio_instance.get_device_count()
            devices = []
            
            for i in range(device_count):
                device_info = self.pyaudio_instance.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:  # Dispositivos de entrada
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': device_info['defaultSampleRate']
                    })
            
            return {
                'available_devices': devices,
                'default_device': self.pyaudio_instance.get_default_input_device_info()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter informações de dispositivos: {e}")
            return {}
    
    async def cleanup(self):
        """Limpa recursos do processador STT"""
        try:
            # Parar gravação se ativa
            if self.is_recording:
                await self.stop_recording()
            
            # Fechar stream se aberto
            if self.stream:
                self.stream.close()
            
            # Terminar PyAudio
            if self.pyaudio_instance:
                self.pyaudio_instance.terminate()
            
            self.logger.info("SpeechToTextProcessor limpo")
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza do STT: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do processador STT"""
        return {
            'model_name': self.model_name,
            'device': self.device,
            'is_recording': self.is_recording,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'chunk_size': self.chunk_size,
            'buffer_size': len(self.audio_buffer) if self.audio_buffer else 0
        }
