"""
Configurações centralizadas do sistema EVA.
"""

import yaml
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path

@dataclass
class ModelConfig:
    """Configuração para um modelo específico"""
    name: str
    path: str
    context_length: int
    gpu_layers: int
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40

@dataclass
class MemoryConfig:
    """Configurações do sistema de memória"""
    episodic_db_path: str = "data/memory/episodic.db"
    affective_db_path: str = "data/memory/affective.db"
    vector_db_path: str = "data/memory/vectors"
    max_episodic_entries: int = 10000
    max_affective_entries: int = 5000
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    consolidation_interval: int = 86400  # 24 horas

@dataclass
class VoiceConfig:
    """Configurações do sistema de voz"""
    whisper_model: str = "base"
    tts_engine: str = "piper"  # ou "coqui"
    voice_model: str = "pt_BR-faber-medium"
    sample_rate: int = 22050
    enable_voice: bool = True
    voice_activation_threshold: float = 0.5
    silence_timeout: float = 2.0

@dataclass
class HardwareConfig:
    """Configurações de hardware e otimização"""
    target_vram_usage: float = 0.85  # 85% da VRAM disponível
    cpu_threads: int = 4
    gpu_device: int = 0
    enable_gpu_monitoring: bool = True
    memory_cleanup_threshold: float = 0.9
    model_switch_timeout: float = 30.0

@dataclass
class PersonaConfig:
    """Configuração para uma persona específica"""
    activation_threshold: float = 0.5
    specialization_weight: float = 1.0

@dataclass
class InterfaceConfig:
    """Configurações de interface"""
    web_port: int = 7860
    enable_web_interface: bool = True
    enable_cli_interface: bool = True
    cli_prompt: str = "Você: "
    eva_prompt: str = "EVA: "

@dataclass
class EVAConfig:
    """Configuração principal do sistema EVA"""
    
    # Configurações de modelos
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    
    # Configurações de memória
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    
    # Configurações de voz
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    
    # Configurações de hardware
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    
    # Configurações de personas
    personas: Dict[str, PersonaConfig] = field(default_factory=dict)
    
    # Configurações de interface
    interface: InterfaceConfig = field(default_factory=InterfaceConfig)
    
    # Configurações gerais
    debug_mode: bool = False
    log_level: str = "INFO"
    session_timeout: int = 3600  # 1 hora
    auto_save_interval: int = 300  # 5 minutos
    max_conversation_history: int = 50
    enable_reflection: bool = True
    reflection_interval: int = 5  # A cada 5 interações
    
    @classmethod
    def load(cls, config_path: str) -> 'EVAConfig':
        """Carrega configuração de arquivo YAML"""
        if not os.path.exists(config_path):
            # Criar configuração padrão se não existir
            config = cls.create_default()
            config.save(config_path)
            return config
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def create_default(cls) -> 'EVAConfig':
        """Cria configuração padrão"""
        config = cls()
        
        # Configurar modelos padrão
        config.models = {
            'mistral-7b-instruct': ModelConfig(
                name='mistral-7b-instruct',
                path='data/models/mistral-7b-instruct-Q4_K_M.gguf',
                context_length=4096,
                gpu_layers=35,
                temperature=0.7
            ),
            'ui-tars': ModelConfig(
                name='ui-tars',
                path='data/models/UI-TARS-1.5-7B.i1-Q4_K_M.gguf',
                context_length=2048,
                gpu_layers=35,
                temperature=0.3
            ),
            'mistral-3b': ModelConfig(
                name='mistral-3b',
                path='data/models/mistral-3b-instruct-Q4_K_M.gguf',
                context_length=2048,
                gpu_layers=25,
                temperature=0.8
            )
        }
        
        # Configurar personas padrão
        config.personas = {
            'analytical': PersonaConfig(activation_threshold=0.6, specialization_weight=1.2),
            'creative': PersonaConfig(activation_threshold=0.5, specialization_weight=1.0),
            'empathetic': PersonaConfig(activation_threshold=0.4, specialization_weight=1.3),
            'executive': PersonaConfig(activation_threshold=0.7, specialization_weight=1.1),
            'reflective': PersonaConfig(activation_threshold=0.8, specialization_weight=1.0)
        }
        
        return config
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EVAConfig':
        """Cria configuração a partir de dicionário"""
        config = cls()
        
        # Carregar modelos
        if 'models' in data:
            config.models = {
                name: ModelConfig(**model_data)
                for name, model_data in data['models'].items()
            }
        
        # Carregar outras configurações
        if 'memory' in data:
            config.memory = MemoryConfig(**data['memory'])
        
        if 'voice' in data:
            config.voice = VoiceConfig(**data['voice'])
        
        if 'hardware' in data:
            config.hardware = HardwareConfig(**data['hardware'])
        
        if 'personas' in data:
            config.personas = {
                name: PersonaConfig(**persona_data)
                for name, persona_data in data['personas'].items()
            }
        
        if 'interface' in data:
            config.interface = InterfaceConfig(**data['interface'])
        
        # Configurações gerais
        general_keys = [
            'debug_mode', 'log_level', 'session_timeout', 'auto_save_interval',
            'max_conversation_history', 'enable_reflection', 'reflection_interval'
        ]
        
        for key in general_keys:
            if key in data:
                setattr(config, key, data[key])
        
        return config
    
    def save(self, config_path: str):
        """Salva configuração em arquivo YAML"""
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        data = self.to_dict()
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    
    def to_dict(self) -> Dict:
        """Converte configuração para dicionário"""
        return {
            'models': {
                name: {
                    'name': model.name,
                    'path': model.path,
                    'context_length': model.context_length,
                    'gpu_layers': model.gpu_layers,
                    'temperature': model.temperature,
                    'top_p': model.top_p,
                    'top_k': model.top_k
                }
                for name, model in self.models.items()
            },
            'memory': {
                'episodic_db_path': self.memory.episodic_db_path,
                'affective_db_path': self.memory.affective_db_path,
                'vector_db_path': self.memory.vector_db_path,
                'max_episodic_entries': self.memory.max_episodic_entries,
                'max_affective_entries': self.memory.max_affective_entries,
                'embedding_model': self.memory.embedding_model,
                'consolidation_interval': self.memory.consolidation_interval
            },
            'voice': {
                'whisper_model': self.voice.whisper_model,
                'tts_engine': self.voice.tts_engine,
                'voice_model': self.voice.voice_model,
                'sample_rate': self.voice.sample_rate,
                'enable_voice': self.voice.enable_voice,
                'voice_activation_threshold': self.voice.voice_activation_threshold,
                'silence_timeout': self.voice.silence_timeout
            },
            'hardware': {
                'target_vram_usage': self.hardware.target_vram_usage,
                'cpu_threads': self.hardware.cpu_threads,
                'gpu_device': self.hardware.gpu_device,
                'enable_gpu_monitoring': self.hardware.enable_gpu_monitoring,
                'memory_cleanup_threshold': self.hardware.memory_cleanup_threshold,
                'model_switch_timeout': self.hardware.model_switch_timeout
            },
            'personas': {
                name: {
                    'activation_threshold': persona.activation_threshold,
                    'specialization_weight': persona.specialization_weight
                }
                for name, persona in self.personas.items()
            },
            'interface': {
                'web_port': self.interface.web_port,
                'enable_web_interface': self.interface.enable_web_interface,
                'enable_cli_interface': self.interface.enable_cli_interface,
                'cli_prompt': self.interface.cli_prompt,
                'eva_prompt': self.interface.eva_prompt
            },
            'debug_mode': self.debug_mode,
            'log_level': self.log_level,
            'session_timeout': self.session_timeout,
            'auto_save_interval': self.auto_save_interval,
            'max_conversation_history': self.max_conversation_history,
            'enable_reflection': self.enable_reflection,
            'reflection_interval': self.reflection_interval
        }
    
    def validate(self) -> List[str]:
        """Valida a configuração e retorna lista de erros"""
        errors = []
        
        # Validar caminhos de modelos
        for name, model in self.models.items():
            if not os.path.exists(model.path):
                errors.append(f"Modelo {name} não encontrado em {model.path}")
        
        # Validar diretórios de memória
        memory_dirs = [
            os.path.dirname(self.memory.episodic_db_path),
            os.path.dirname(self.memory.affective_db_path),
            self.memory.vector_db_path
        ]
        
        for dir_path in memory_dirs:
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except Exception as e:
                    errors.append(f"Não foi possível criar diretório {dir_path}: {e}")
        
        # Validar configurações de hardware
        if self.hardware.target_vram_usage <= 0 or self.hardware.target_vram_usage > 1:
            errors.append("target_vram_usage deve estar entre 0 e 1")
        
        if self.hardware.cpu_threads <= 0:
            errors.append("cpu_threads deve ser maior que 0")
        
        return errors
