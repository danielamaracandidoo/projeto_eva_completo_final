"""
Monitor de hardware para otimizações de performance.
"""

import psutil
import time
import threading
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from utils.logging_system import EVALogger, PerformanceLogger

try:
    import pynvml
    NVIDIA_AVAILABLE = True
except ImportError:
    NVIDIA_AVAILABLE = False

@dataclass
class HardwareStats:
    """Estatísticas de hardware"""
    cpu_percent: float
    ram_used_gb: float
    ram_total_gb: float
    ram_percent: float
    vram_used_gb: float = 0.0
    vram_total_gb: float = 0.0
    vram_percent: float = 0.0
    gpu_temp: float = 0.0
    gpu_utilization: float = 0.0

class HardwareMonitor:
    """Monitor de hardware para otimização de performance"""
    
    def __init__(self, config):
        self.config = config
        self.logger = EVALogger.get_logger("HardwareMonitor")
        self.perf_logger = PerformanceLogger()
        
        self._monitoring = False
        self._monitor_thread = None
        self._stats_history = []
        self._max_history = 100
        
        # Inicializar NVIDIA ML se disponível
        self.nvidia_available = False
        if NVIDIA_AVAILABLE and config.hardware.enable_gpu_monitoring:
            try:
                pynvml.nvmlInit()
                self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(config.hardware.gpu_device)
                self.nvidia_available = True
                self.logger.info("NVIDIA GPU monitoring inicializado")
            except Exception as e:
                self.logger.warning(f"Não foi possível inicializar NVIDIA monitoring: {e}")
    
    def get_current_stats(self) -> HardwareStats:
        """Obtém estatísticas atuais do hardware"""
        # CPU e RAM
        cpu_percent = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        ram_used_gb = ram.used / (1024**3)
        ram_total_gb = ram.total / (1024**3)
        ram_percent = ram.percent
        
        # GPU (se disponível)
        vram_used_gb = 0.0
        vram_total_gb = 0.0
        vram_percent = 0.0
        gpu_temp = 0.0
        gpu_utilization = 0.0
        
        if self.nvidia_available:
            try:
                # Memória GPU
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
                vram_used_gb = mem_info.used / (1024**3)
                vram_total_gb = mem_info.total / (1024**3)
                vram_percent = (mem_info.used / mem_info.total) * 100
                
                # Temperatura GPU
                gpu_temp = pynvml.nvmlDeviceGetTemperature(self.gpu_handle, pynvml.NVML_TEMPERATURE_GPU)
                
                # Utilização GPU
                util = pynvml.nvmlDeviceGetUtilizationRates(self.gpu_handle)
                gpu_utilization = util.gpu
                
            except Exception as e:
                self.logger.warning(f"Erro ao obter estatísticas GPU: {e}")
        
        stats = HardwareStats(
            cpu_percent=cpu_percent,
            ram_used_gb=ram_used_gb,
            ram_total_gb=ram_total_gb,
            ram_percent=ram_percent,
            vram_used_gb=vram_used_gb,
            vram_total_gb=vram_total_gb,
            vram_percent=vram_percent,
            gpu_temp=gpu_temp,
            gpu_utilization=gpu_utilization
        )
        
        return stats
    
    def get_vram_info(self) -> Tuple[float, float, float]:
        """Retorna informações específicas de VRAM (usado, total, percentual)"""
        if not self.nvidia_available:
            return 0.0, 0.0, 0.0
        
        try:
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
            used_gb = mem_info.used / (1024**3)
            total_gb = mem_info.total / (1024**3)
            percent = (mem_info.used / mem_info.total) * 100
            return used_gb, total_gb, percent
        except Exception as e:
            self.logger.warning(f"Erro ao obter info VRAM: {e}")
            return 0.0, 0.0, 0.0
    
    def get_available_vram(self) -> float:
        """Retorna VRAM disponível em GB"""
        if not self.nvidia_available:
            return 0.0
        
        try:
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
            available_gb = (mem_info.total - mem_info.used) / (1024**3)
            return available_gb
        except Exception as e:
            self.logger.warning(f"Erro ao calcular VRAM disponível: {e}")
            return 0.0
    
    def is_vram_critical(self) -> bool:
        """Verifica se o uso de VRAM está crítico"""
        _, _, percent = self.get_vram_info()
        return percent > (self.config.hardware.memory_cleanup_threshold * 100)
    
    def is_memory_pressure(self) -> bool:
        """Verifica se há pressão de memória (RAM ou VRAM)"""
        stats = self.get_current_stats()
        
        ram_critical = stats.ram_percent > 85
        vram_critical = stats.vram_percent > (self.config.hardware.memory_cleanup_threshold * 100)
        
        return ram_critical or vram_critical
    
    def start_monitoring(self, interval: float = 5.0):
        """Inicia monitoramento contínuo"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info(f"Monitoramento de hardware iniciado (intervalo: {interval}s)")
    
    def stop_monitoring(self):
        """Para o monitoramento contínuo"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        self.logger.info("Monitoramento de hardware parado")
    
    def _monitor_loop(self, interval: float):
        """Loop principal de monitoramento"""
        while self._monitoring:
            try:
                stats = self.get_current_stats()
                
                # Adicionar ao histórico
                self._stats_history.append(stats)
                if len(self._stats_history) > self._max_history:
                    self._stats_history.pop(0)
                
                # Log periódico de métricas
                self.perf_logger.log_memory_usage(
                    stats.vram_used_gb,
                    stats.vram_total_gb,
                    stats.ram_used_gb
                )
                
                # Verificar condições críticas
                if stats.vram_percent > 90:
                    self.logger.warning(f"VRAM crítica: {stats.vram_percent:.1f}%")
                
                if stats.ram_percent > 90:
                    self.logger.warning(f"RAM crítica: {stats.ram_percent:.1f}%")
                
                if stats.gpu_temp > 80:
                    self.logger.warning(f"Temperatura GPU alta: {stats.gpu_temp}°C")
                
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Erro no loop de monitoramento: {e}")
                time.sleep(interval)
    
    def get_stats_summary(self) -> Dict:
        """Retorna resumo das estatísticas"""
        if not self._stats_history:
            return {}
        
        recent_stats = self._stats_history[-10:]  # Últimas 10 medições
        
        avg_cpu = sum(s.cpu_percent for s in recent_stats) / len(recent_stats)
        avg_ram = sum(s.ram_percent for s in recent_stats) / len(recent_stats)
        avg_vram = sum(s.vram_percent for s in recent_stats) / len(recent_stats)
        avg_gpu_util = sum(s.gpu_utilization for s in recent_stats) / len(recent_stats)
        
        current = recent_stats[-1]
        
        return {
            'current': {
                'cpu_percent': current.cpu_percent,
                'ram_percent': current.ram_percent,
                'vram_percent': current.vram_percent,
                'vram_used_gb': current.vram_used_gb,
                'vram_total_gb': current.vram_total_gb,
                'gpu_temp': current.gpu_temp,
                'gpu_utilization': current.gpu_utilization
            },
            'averages': {
                'cpu_percent': avg_cpu,
                'ram_percent': avg_ram,
                'vram_percent': avg_vram,
                'gpu_utilization': avg_gpu_util
            },
            'nvidia_available': self.nvidia_available
        }
    
    def optimize_for_model_loading(self, model_size_estimate: float) -> Dict:
        """Otimiza sistema para carregamento de modelo"""
        stats = self.get_current_stats()
        available_vram = self.get_available_vram()
        
        recommendations = {
            'can_load': available_vram >= model_size_estimate,
            'available_vram': available_vram,
            'required_vram': model_size_estimate,
            'cleanup_needed': False,
            'reduce_layers': False
        }
        
        if available_vram < model_size_estimate:
            recommendations['cleanup_needed'] = True
            
            # Se mesmo com cleanup não for suficiente, sugerir redução de camadas
            if available_vram < model_size_estimate * 0.8:
                recommendations['reduce_layers'] = True
        
        return recommendations
    
    def __del__(self):
        """Cleanup ao destruir o objeto"""
        self.stop_monitoring()
        if self.nvidia_available:
            try:
                pynvml.nvmlShutdown()
            except:
                pass

class VRAMManager:
    """Gerenciador específico para VRAM"""
    
    def __init__(self, hardware_monitor: HardwareMonitor):
        self.monitor = hardware_monitor
        self.logger = EVALogger.get_logger("VRAMManager")
        
        # Estimativas de uso de VRAM por modelo (em GB)
        self.model_vram_estimates = {
            'mistral-7b-instruct': 4.2,
            'ui-tars': 4.2,
            'mistral-3b': 2.8
        }
    
    def can_load_model(self, model_name: str) -> bool:
        """Verifica se é possível carregar um modelo"""
        if model_name not in self.model_vram_estimates:
            self.logger.warning(f"Estimativa de VRAM não disponível para {model_name}")
            return True  # Assumir que sim se não soubermos
        
        required_vram = self.model_vram_estimates[model_name]
        available_vram = self.monitor.get_available_vram()
        
        can_load = available_vram >= required_vram
        
        self.logger.debug(f"Verificação de carregamento {model_name}: "
                         f"Necessário: {required_vram:.1f}GB, "
                         f"Disponível: {available_vram:.1f}GB, "
                         f"Pode carregar: {can_load}")
        
        return can_load
    
    def get_optimal_gpu_layers(self, model_name: str, base_layers: int) -> int:
        """Calcula número ótimo de camadas GPU baseado na VRAM disponível"""
        available_vram = self.monitor.get_available_vram()
        
        if available_vram < 3.0:  # Menos de 3GB
            return max(base_layers - 15, 0)
        elif available_vram < 4.0:  # Menos de 4GB
            return max(base_layers - 10, 0)
        elif available_vram < 5.0:  # Menos de 5GB
            return max(base_layers - 5, 0)
        else:
            return base_layers
    
    def force_cleanup(self):
        """Força limpeza de VRAM (placeholder para implementação futura)"""
        self.logger.info("Forçando limpeza de VRAM...")
        # Aqui seria implementada lógica específica de limpeza
        # Por exemplo, descarregar modelos não utilizados
    
    def log_vram_status(self):
        """Log do status atual da VRAM"""
        used, total, percent = self.monitor.get_vram_info()
        self.logger.info(f"VRAM Status: {used:.1f}GB/{total:.1f}GB ({percent:.1f}%)")
