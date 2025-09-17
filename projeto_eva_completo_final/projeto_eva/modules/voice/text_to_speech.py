"""
Processador de Text-to-Speech (TTS) usando Piper ou Coqui TTS.
"""

import asyncio
import os
import tempfile
import subprocess
from typing import Optional, Dict, Any, List
from pathlib import Path

import numpy as np
import pygame

from utils.logging_system import EVALogger

class TextToSpeechProcessor:
    """
    Processador de Text-to-Speech usando Piper (padrão) ou Coqui TTS.
    
    Funcionalidades:
    - Síntese de fala de alta qualidade
    - Múltiplas vozes e idiomas
    - Controle de velocidade e tom
    - Reprodução direta ou salvamento em arquivo
    - Processamento local (privacidade)
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = EVALogger.get_logger("TextToSpeechProcessor")
        
        # Configurações TTS
        self.tts_engine = config.voice.tts_engine  # 'piper' ou 'coqui'
        self.voice_model = config.voice.tts_voice_model
        self.sample_rate = config.voice.sample_rate
        self.speed = config.voice.tts_speed
        self.pitch = config.voice.tts_pitch
        
        # Caminhos
        self.models_dir = Path(config.voice.tts_models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Estado
        self.is_speaking = False
        self.current_audio_file: Optional[str] = None
        
        # Pygame para reprodução de áudio
        self.pygame_initialized = False
        
        self.logger.info(f"TextToSpeechProcessor inicializado (engine: {self.tts_engine})")
    
    async def initialize(self):
        """Inicializa o processador TTS"""
        try:
            self.logger.info("Inicializando processador TTS...")
            
            # Inicializar pygame para reprodução de áudio
            pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1, buffer=512)
            self.pygame_initialized = True
            
            # Verificar se modelo existe
            await self._ensure_voice_model()
            
            # Testar síntese
            await self._test_synthesis()
            
            self.logger.info("TextToSpeechProcessor inicializado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização do TTS: {e}")
            raise
    
    async def _ensure_voice_model(self):
        """Garante que o modelo de voz está disponível"""
        try:
            if self.tts_engine == 'piper':
                await self._ensure_piper_model()
            elif self.tts_engine == 'coqui':
                await self._ensure_coqui_model()
            else:
                raise ValueError(f"Engine TTS não suportado: {self.tts_engine}")
                
        except Exception as e:
            self.logger.error(f"Erro ao verificar modelo de voz: {e}")
            raise
    
    async def _ensure_piper_model(self):
        """Garante que modelo Piper está disponível"""
        model_path = self.models_dir / f"{self.voice_model}.onnx"
        config_path = self.models_dir / f"{self.voice_model}.onnx.json"
        
        if not model_path.exists() or not config_path.exists():
            self.logger.warning(f"Modelo Piper não encontrado: {self.voice_model}")
            self.logger.info("Para baixar modelos Piper, visite: https://github.com/rhasspy/piper")
            
            # Criar arquivos dummy para evitar erros (em produção, baixar modelos reais)
            model_path.touch()
            config_path.write_text('{"sample_rate": 22050}')
    
    async def _ensure_coqui_model(self):
        """Garante que modelo Coqui está disponível"""
        try:
            # Tentar importar Coqui TTS
            import TTS
            from TTS.api import TTS as CoquiTTS
            
            # Verificar se modelo está disponível
            tts = CoquiTTS(model_name=self.voice_model)
            self.coqui_tts = tts
            
        except ImportError:
            self.logger.error("Coqui TTS não instalado. Execute: pip install TTS")
            raise
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo Coqui: {e}")
            raise
    
    async def _test_synthesis(self):
        """Testa síntese de fala"""
        try:
            test_text = "Teste de síntese de voz."
            temp_file = await self.synthesize_to_file(test_text)
            
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)  # Limpar arquivo de teste
                self.logger.debug("Teste de síntese bem-sucedido")
            else:
                self.logger.warning("Teste de síntese falhou")
                
        except Exception as e:
            self.logger.warning(f"Teste de síntese falhou: {e}")
    
    async def synthesize_to_file(
        self, 
        text: str, 
        output_path: Optional[str] = None,
        voice: Optional[str] = None,
        speed: Optional[float] = None
    ) -> Optional[str]:
        """
        Sintetiza texto para arquivo de áudio.
        
        Args:
            text: Texto para sintetizar
            output_path: Caminho de saída (opcional, usa temporário se None)
            voice: Voz específica (opcional)
            speed: Velocidade específica (opcional)
            
        Returns:
            Caminho do arquivo gerado ou None se erro
        """
        try:
            if not text.strip():
                self.logger.warning("Texto vazio para síntese")
                return None
            
            # Usar arquivo temporário se não especificado
            if output_path is None:
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                output_path = temp_file.name
                temp_file.close()
            
            # Parâmetros
            voice_to_use = voice or self.voice_model
            speed_to_use = speed or self.speed
            
            # Sintetizar baseado no engine
            if self.tts_engine == 'piper':
                success = await self._synthesize_piper(text, output_path, voice_to_use, speed_to_use)
            elif self.tts_engine == 'coqui':
                success = await self._synthesize_coqui(text, output_path, voice_to_use, speed_to_use)
            else:
                success = False
            
            if success and os.path.exists(output_path):
                self.logger.debug(f"Síntese concluída: {output_path}")
                return output_path
            else:
                self.logger.error("Falha na síntese de fala")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro na síntese para arquivo: {e}")
            return None
    
    async def _synthesize_piper(
        self, 
        text: str, 
        output_path: str, 
        voice: str, 
        speed: float
    ) -> bool:
        """Sintetiza usando Piper"""
        try:
            model_path = self.models_dir / f"{voice}.onnx"
            
            # Comando Piper
            cmd = [
                'piper',
                '--model', str(model_path),
                '--output_file', output_path,
                '--length_scale', str(1.0 / speed)  # Piper usa length_scale inverso
            ]
            
            # Executar Piper
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate(input=text.encode())
            
            if process.returncode == 0:
                return True
            else:
                self.logger.error(f"Erro Piper: {stderr.decode()}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro na síntese Piper: {e}")
            return False
    
    async def _synthesize_coqui(
        self, 
        text: str, 
        output_path: str, 
        voice: str, 
        speed: float
    ) -> bool:
        """Sintetiza usando Coqui TTS"""
        try:
            if not hasattr(self, 'coqui_tts'):
                self.logger.error("Coqui TTS não inicializado")
                return False
            
            # Executar síntese em thread separada
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.coqui_tts.tts_to_file,
                text,
                output_path
            )
            
            # Ajustar velocidade se necessário (pós-processamento)
            if speed != 1.0:
                await self._adjust_audio_speed(output_path, speed)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na síntese Coqui: {e}")
            return False
    
    async def _adjust_audio_speed(self, audio_path: str, speed: float):
        """Ajusta velocidade do áudio usando ffmpeg"""
        try:
            if speed == 1.0:
                return
            
            temp_path = audio_path + '.temp.wav'
            
            cmd = [
                'ffmpeg', '-i', audio_path,
                '-filter:a', f'atempo={speed}',
                '-y', temp_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if process.returncode == 0:
                os.replace(temp_path, audio_path)
            else:
                self.logger.warning("Falha ao ajustar velocidade do áudio")
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            self.logger.error(f"Erro ao ajustar velocidade: {e}")
    
    async def speak(
        self, 
        text: str, 
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        wait: bool = True
    ) -> bool:
        """
        Fala um texto diretamente.
        
        Args:
            text: Texto para falar
            voice: Voz específica (opcional)
            speed: Velocidade específica (opcional)
            wait: Se deve aguardar conclusão da fala
            
        Returns:
            True se iniciou com sucesso, False caso contrário
        """
        try:
            if self.is_speaking:
                self.logger.warning("Já está falando, ignorando nova solicitação")
                return False
            
            # Sintetizar para arquivo temporário
            audio_file = await self.synthesize_to_file(text, voice=voice, speed=speed)
            
            if not audio_file:
                return False
            
            # Reproduzir áudio
            success = await self._play_audio_file(audio_file, wait)
            
            # Limpar arquivo temporário
            if os.path.exists(audio_file):
                os.unlink(audio_file)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro ao falar: {e}")
            return False
    
    async def _play_audio_file(self, audio_path: str, wait: bool = True) -> bool:
        """Reproduz arquivo de áudio"""
        try:
            if not self.pygame_initialized:
                self.logger.error("Pygame não inicializado")
                return False
            
            self.is_speaking = True
            self.current_audio_file = audio_path
            
            # Carregar e reproduzir áudio
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            
            if wait:
                # Aguardar conclusão
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
            
            self.is_speaking = False
            self.current_audio_file = None
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na reprodução de áudio: {e}")
            self.is_speaking = False
            self.current_audio_file = None
            return False
    
    async def stop_speaking(self):
        """Para a fala atual"""
        try:
            if self.is_speaking:
                pygame.mixer.music.stop()
                self.is_speaking = False
                self.current_audio_file = None
                self.logger.debug("Fala interrompida")
                
        except Exception as e:
            self.logger.error(f"Erro ao parar fala: {e}")
    
    def is_speaking_active(self) -> bool:
        """Verifica se está falando"""
        return self.is_speaking
    
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Retorna vozes disponíveis"""
        try:
            voices = []
            
            if self.tts_engine == 'piper':
                # Listar modelos Piper disponíveis
                for model_file in self.models_dir.glob('*.onnx'):
                    voice_name = model_file.stem
                    config_file = model_file.with_suffix('.onnx.json')
                    
                    voice_info = {
                        'name': voice_name,
                        'engine': 'piper',
                        'language': 'pt-BR',  # Assumir português por padrão
                        'gender': 'unknown'
                    }
                    
                    # Ler configuração se disponível
                    if config_file.exists():
                        try:
                            import json
                            with open(config_file) as f:
                                config = json.load(f)
                            voice_info.update({
                                'sample_rate': config.get('sample_rate', 22050),
                                'language': config.get('language', 'pt-BR')
                            })
                        except:
                            pass
                    
                    voices.append(voice_info)
            
            elif self.tts_engine == 'coqui':
                # Listar modelos Coqui disponíveis
                try:
                    from TTS.api import TTS
                    available_models = TTS.list_models()
                    
                    for model in available_models:
                        if 'pt' in model.lower() or 'portuguese' in model.lower():
                            voices.append({
                                'name': model,
                                'engine': 'coqui',
                                'language': 'pt-BR',
                                'gender': 'unknown'
                            })
                except:
                    pass
            
            return voices
            
        except Exception as e:
            self.logger.error(f"Erro ao listar vozes: {e}")
            return []
    
    async def set_voice_parameters(
        self, 
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        pitch: Optional[float] = None
    ):
        """Define parâmetros de voz"""
        try:
            if voice is not None:
                self.voice_model = voice
                self.logger.debug(f"Voz alterada para: {voice}")
            
            if speed is not None:
                self.speed = max(0.5, min(2.0, speed))  # Limitar entre 0.5x e 2.0x
                self.logger.debug(f"Velocidade alterada para: {self.speed}")
            
            if pitch is not None:
                self.pitch = max(0.5, min(2.0, pitch))  # Limitar entre 0.5x e 2.0x
                self.logger.debug(f"Tom alterado para: {self.pitch}")
                
        except Exception as e:
            self.logger.error(f"Erro ao definir parâmetros de voz: {e}")
    
    async def estimate_speech_duration(self, text: str) -> float:
        """Estima duração da fala em segundos"""
        try:
            # Estimativa baseada em palavras por minuto (aproximadamente 150 WPM)
            words = len(text.split())
            base_duration = (words / 150) * 60  # segundos
            
            # Ajustar pela velocidade
            adjusted_duration = base_duration / self.speed
            
            return adjusted_duration
            
        except Exception as e:
            self.logger.error(f"Erro ao estimar duração: {e}")
            return 0.0
    
    async def cleanup(self):
        """Limpa recursos do processador TTS"""
        try:
            # Parar fala se ativa
            if self.is_speaking:
                await self.stop_speaking()
            
            # Limpar pygame
            if self.pygame_initialized:
                pygame.mixer.quit()
                self.pygame_initialized = False
            
            self.logger.info("TextToSpeechProcessor limpo")
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza do TTS: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do processador TTS"""
        return {
            'engine': self.tts_engine,
            'voice_model': self.voice_model,
            'sample_rate': self.sample_rate,
            'speed': self.speed,
            'pitch': self.pitch,
            'is_speaking': self.is_speaking,
            'pygame_initialized': self.pygame_initialized,
            'current_audio_file': self.current_audio_file
        }
