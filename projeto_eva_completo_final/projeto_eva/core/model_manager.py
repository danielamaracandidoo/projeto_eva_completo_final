"""
Gerenciador de modelos com carregamento sequencial otimizado para VRAM limitada.
"""

import asyncio
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

from llama_cpp import Llama
import torch

from config.settings import EVAConfig, ModelConfig
from utils.logging_system import EVALogger, PerformanceLogger
from utils.hardware_monitor import HardwareMonitor, VRAMManager

class ModelState(Enum):
    """Estados possíveis de um modelo"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    UNLOADING = "unloading"
    ERROR = "error"

@dataclass
class LoadedModel:
    """Informações sobre um modelo carregado"""
    name: str
    model: Llama
    config: ModelConfig
    load_time: float
    last_used: float
    state: ModelState

class ModelManager:
    """
    Gerenciador de modelos com carregamento sequencial otimizado.
    
    Garante que apenas um modelo esteja carregado na VRAM por vez,
    implementando troca eficiente entre modelos.
    """
    
    def __init__(self, config: EVAConfig):
        self.config = config
        self.logger = EVALogger.get_logger("ModelManager")
        self.perf_logger = PerformanceLogger()
        
        # Estado interno
        self.loaded_models: Dict[str, LoadedModel] = {}
        self.current_model: Optional[str] = None
        self._loading_lock = asyncio.Lock()
        
        # Monitoramento de hardware
        self.hardware_monitor = HardwareMonitor(config)
        self.vram_manager = VRAMManager(self.hardware_monitor)
        
        # Estatísticas
        self.model_switches = 0
        self.total_inference_time = 0.0
        self.total_tokens_generated = 0
        
        self.logger.info("ModelManager inicializado")
    
    async def initialize(self):
        """Inicializa o gerenciador de modelos"""
        try:
            # Iniciar monitoramento de hardware
            self.hardware_monitor.start_monitoring()
            
            # Verificar disponibilidade de GPU
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(self.config.hardware.gpu_device)
                vram_total = torch.cuda.get_device_properties(self.config.hardware.gpu_device).total_memory / (1024**3)
                self.logger.info(f"GPU detectada: {gpu_name} ({vram_total:.1f}GB VRAM)")
            else:
                self.logger.warning("CUDA não disponível - modelos serão executados na CPU")
            
            # Validar modelos configurados
            await self._validate_models()
            
            self.logger.info("ModelManager inicializado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização do ModelManager: {e}")
            raise
    
    async def _validate_models(self):
        """Valida se todos os modelos configurados existem"""
        for name, model_config in self.config.models.items():
            if not os.path.exists(model_config.path):
                raise FileNotFoundError(f"Modelo {name} não encontrado em {model_config.path}")
            
            self.logger.debug(f"Modelo {name} validado: {model_config.path}")
    
    async def load_model(self, model_name: str) -> Llama:
        """
        Carrega um modelo específico, descarregando outros se necessário.
        """
        async with self._loading_lock:
            return await self._load_model_internal(model_name)
    
    async def _load_model_internal(self, model_name: str) -> Llama:
        """Implementação interna do carregamento de modelo"""
        if model_name not in self.config.models:
            raise ValueError(f"Modelo {model_name} não configurado")
        
        # Se o modelo já está carregado, apenas atualizar timestamp
        if model_name in self.loaded_models and self.loaded_models[model_name].state == ModelState.LOADED:
            self.loaded_models[model_name].last_used = time.time()
            self.current_model = model_name
            self.logger.debug(f"Modelo {model_name} já carregado")
            return self.loaded_models[model_name].model
        
        start_time = time.time()
        model_config = self.config.models[model_name]
        
        try:
            # Descarregar modelo atual se existir
            if self.current_model and self.current_model != model_name:
                await self._unload_model(self.current_model)
            
            self.logger.info(f"Carregando modelo {model_name}...")
            
            # Verificar VRAM disponível e otimizar parâmetros
            if not self.vram_manager.can_load_model(model_name):
                self.logger.warning(f"VRAM insuficiente para {model_name}, forçando limpeza...")
                self.vram_manager.force_cleanup()
            
            # Otimizar número de camadas GPU
            optimal_layers = self.vram_manager.get_optimal_gpu_layers(
                model_name, model_config.gpu_layers
            )
            
            if optimal_layers != model_config.gpu_layers:
                self.logger.info(f"Otimizando camadas GPU: {model_config.gpu_layers} -> {optimal_layers}")
            
            # Configurar parâmetros de carregamento
            load_params = {
                'model_path': model_config.path,
                'n_ctx': model_config.context_length,
                'n_gpu_layers': optimal_layers,
                'verbose': self.config.debug_mode,
                'n_threads': self.config.hardware.cpu_threads,
                'use_mmap': True,
                'use_mlock': False,  # Evitar travamento de memória
            }
            
            # Carregar modelo
            model = Llama(**load_params)
            
            load_time = time.time() - start_time
            
            # Armazenar informações do modelo carregado
            loaded_model = LoadedModel(
                name=model_name,
                model=model,
                config=model_config,
                load_time=load_time,
                last_used=time.time(),
                state=ModelState.LOADED
            )
            
            self.loaded_models[model_name] = loaded_model
            self.current_model = model_name
            
            # Log de performance
            self.perf_logger.log_model_switch("none", model_name, load_time)
            self.vram_manager.log_vram_status()
            
            self.logger.info(f"Modelo {model_name} carregado em {load_time:.2f}s")
            
            return model
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo {model_name}: {e}")
            
            # Marcar modelo como erro
            if model_name in self.loaded_models:
                self.loaded_models[model_name].state = ModelState.ERROR
            
            raise
    
    async def _unload_model(self, model_name: str):
        """Descarrega um modelo específico"""
        if model_name not in self.loaded_models:
            return
        
        try:
            self.logger.info(f"Descarregando modelo {model_name}...")
            
            loaded_model = self.loaded_models[model_name]
            loaded_model.state = ModelState.UNLOADING
            
            # Liberar recursos do modelo
            del loaded_model.model
            
            # Forçar garbage collection
            import gc
            gc.collect()
            
            # Limpar cache CUDA se disponível
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Remover do dicionário
            del self.loaded_models[model_name]
            
            if self.current_model == model_name:
                self.current_model = None
            
            self.logger.info(f"Modelo {model_name} descarregado")
            
        except Exception as e:
            self.logger.error(f"Erro ao descarregar modelo {model_name}: {e}")
    
    async def switch_to_model(self, model_name: str) -> Llama:
        """
        Troca para um modelo específico, otimizando a transição.
        """
        if self.current_model == model_name:
            # Modelo já ativo, apenas retornar
            return self.loaded_models[model_name].model
        
        start_time = time.time()
        old_model = self.current_model
        
        try:
            model = await self.load_model(model_name)
            
            switch_time = time.time() - start_time
            self.model_switches += 1
            
            # Log da troca
            self.perf_logger.log_model_switch(old_model or "none", model_name, switch_time)
            
            return model
            
        except Exception as e:
            self.logger.error(f"Erro na troca para modelo {model_name}: {e}")
            raise
    
    async def generate_text(
        self, 
        model_name: str, 
        prompt: str, 
        max_tokens: int = 512,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stop: Optional[list] = None
    ) -> str:
        """
        Gera texto usando um modelo específico.
        """
        try:
            # Trocar para o modelo necessário
            model = await self.switch_to_model(model_name)
            model_config = self.config.models[model_name]
            
            # Usar parâmetros do modelo se não especificados
            generation_params = {
                'prompt': prompt,
                'max_tokens': max_tokens,
                'temperature': temperature or model_config.temperature,
                'top_p': top_p or model_config.top_p,
                'top_k': top_k or model_config.top_k,
                'stop': stop or [],
                'echo': False
            }
            
            start_time = time.time()
            
            # Gerar texto
            response = model(**generation_params)
            
            generation_time = time.time() - start_time
            generated_text = response['choices'][0]['text']
            tokens_generated = len(generated_text.split())  # Estimativa simples
            
            # Atualizar estatísticas
            self.total_inference_time += generation_time
            self.total_tokens_generated += tokens_generated
            
            # Log de performance
            self.perf_logger.log_inference_time(model_name, tokens_generated, generation_time)
            
            # Atualizar timestamp de uso
            self.loaded_models[model_name].last_used = time.time()
            
            return generated_text.strip()
            
        except Exception as e:
            self.logger.error(f"Erro na geração de texto com {model_name}: {e}")
            raise
    
    async def generate_streaming(
        self,
        model_name: str,
        prompt: str,
        max_tokens: int = 512,
        temperature: Optional[float] = None,
        **kwargs
    ):
        """
        Gera texto em streaming (para futuras implementações de interface).
        """
        try:
            model = await self.switch_to_model(model_name)
            model_config = self.config.models[model_name]
            
            generation_params = {
                'prompt': prompt,
                'max_tokens': max_tokens,
                'temperature': temperature or model_config.temperature,
                'stream': True,
                **kwargs
            }
            
            start_time = time.time()
            tokens_generated = 0
            
            for chunk in model(**generation_params):
                if chunk['choices'][0]['text']:
                    tokens_generated += 1
                    yield chunk['choices'][0]['text']
            
            generation_time = time.time() - start_time
            self.perf_logger.log_inference_time(model_name, tokens_generated, generation_time)
            
        except Exception as e:
            self.logger.error(f"Erro na geração streaming com {model_name}: {e}")
            raise
    
    def get_current_model(self) -> Optional[str]:
        """Retorna o nome do modelo atualmente carregado"""
        return self.current_model
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas dos modelos"""
        stats = {
            'current_model': self.current_model,
            'loaded_models': list(self.loaded_models.keys()),
            'model_switches': self.model_switches,
            'total_inference_time': self.total_inference_time,
            'total_tokens_generated': self.total_tokens_generated,
            'avg_tokens_per_second': (
                self.total_tokens_generated / self.total_inference_time 
                if self.total_inference_time > 0 else 0
            )
        }
        
        # Adicionar informações de hardware
        hardware_stats = self.hardware_monitor.get_stats_summary()
        stats['hardware'] = hardware_stats
        
        return stats
    
    async def cleanup(self):
        """Limpa todos os recursos"""
        try:
            self.logger.info("Iniciando cleanup do ModelManager...")
            
            # Descarregar todos os modelos
            for model_name in list(self.loaded_models.keys()):
                await self._unload_model(model_name)
            
            # Parar monitoramento de hardware
            self.hardware_monitor.stop_monitoring()
            
            # Limpeza final de memória
            import gc
            gc.collect()
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.logger.info("Cleanup do ModelManager concluído")
            
        except Exception as e:
            self.logger.error(f"Erro durante cleanup: {e}")
    
    def __del__(self):
        """Destrutor para limpeza automática"""
        try:
            # Tentar cleanup síncrono básico
            for model_name in list(self.loaded_models.keys()):
                try:
                    del self.loaded_models[model_name].model
                except:
                    pass
            
            self.loaded_models.clear()
            
        except:
            pass
