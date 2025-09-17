"""
Sistema de logging centralizado para EVA.
"""

import logging
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

class EVALogger:
    """Sistema de logging centralizado para EVA"""
    
    _loggers = {}
    _initialized = False
    
    @classmethod
    def initialize(cls, log_level: str = "INFO", log_dir: str = "data/logs"):
        """Inicializa o sistema de logging"""
        if cls._initialized:
            return
        
        # Criar diretório de logs se não existir
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Configurar formato de log
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        
        # Configurar logging básico
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            datefmt=date_format
        )
        
        # Criar handler para arquivo principal
        main_log_file = os.path.join(log_dir, f"eva_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(main_log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        
        # Criar handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # Apenas warnings e erros no console
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        
        # Configurar logger raiz
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Obtém um logger específico"""
        if not cls._initialized:
            cls.initialize()
        
        if name not in cls._loggers:
            logger = logging.getLogger(f"EVA.{name}")
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def create_module_logger(cls, module_name: str, log_dir: str = "data/logs") -> logging.Logger:
        """Cria um logger específico para um módulo com arquivo próprio"""
        logger = cls.get_logger(module_name)
        
        # Criar handler específico para o módulo
        module_log_file = os.path.join(
            log_dir, 
            f"{module_name}_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        module_handler = logging.FileHandler(module_log_file, encoding='utf-8')
        module_handler.setLevel(logging.DEBUG)
        module_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s",
                "%Y-%m-%d %H:%M:%S"
            )
        )
        
        logger.addHandler(module_handler)
        return logger

class PerformanceLogger:
    """Logger especializado para métricas de performance"""
    
    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = log_dir
        self.logger = EVALogger.get_logger("Performance")
        
        # Criar arquivo específico para métricas
        perf_log_file = os.path.join(
            log_dir,
            f"performance_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        perf_handler = logging.FileHandler(perf_log_file, encoding='utf-8')
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - PERF - %(message)s",
                "%Y-%m-%d %H:%M:%S"
            )
        )
        
        self.logger.addHandler(perf_handler)
    
    def log_model_switch(self, from_model: str, to_model: str, duration: float):
        """Log de troca de modelo"""
        self.logger.info(f"MODEL_SWITCH: {from_model} -> {to_model} | Duration: {duration:.2f}s")
    
    def log_inference_time(self, model: str, tokens: int, duration: float):
        """Log de tempo de inferência"""
        tps = tokens / duration if duration > 0 else 0
        self.logger.info(f"INFERENCE: {model} | Tokens: {tokens} | Duration: {duration:.2f}s | TPS: {tps:.2f}")
    
    def log_memory_usage(self, vram_used: float, vram_total: float, ram_used: float):
        """Log de uso de memória"""
        vram_percent = (vram_used / vram_total) * 100 if vram_total > 0 else 0
        self.logger.info(f"MEMORY: VRAM: {vram_used:.1f}GB/{vram_total:.1f}GB ({vram_percent:.1f}%) | RAM: {ram_used:.1f}GB")
    
    def log_conversation_metrics(self, session_id: str, interaction_count: int, avg_response_time: float):
        """Log de métricas de conversa"""
        self.logger.info(f"CONVERSATION: Session: {session_id} | Interactions: {interaction_count} | Avg Response: {avg_response_time:.2f}s")

class ConversationLogger:
    """Logger especializado para conversas"""
    
    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = log_dir
        self.logger = EVALogger.get_logger("Conversation")
        
        # Criar arquivo específico para conversas
        conv_log_file = os.path.join(
            log_dir,
            f"conversations_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        conv_handler = logging.FileHandler(conv_log_file, encoding='utf-8')
        conv_handler.setLevel(logging.INFO)
        conv_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - CONV - %(message)s",
                "%Y-%m-%d %H:%M:%S"
            )
        )
        
        self.logger.addHandler(conv_handler)
    
    def log_user_input(self, session_id: str, user_input: str):
        """Log de entrada do usuário"""
        # Truncar entrada muito longa para o log
        truncated_input = user_input[:200] + "..." if len(user_input) > 200 else user_input
        self.logger.info(f"USER_INPUT: [{session_id}] {truncated_input}")
    
    def log_eva_response(self, session_id: str, response: str, modules_used: list):
        """Log de resposta da EVA"""
        # Truncar resposta muito longa para o log
        truncated_response = response[:200] + "..." if len(response) > 200 else response
        modules_str = ", ".join(modules_used)
        self.logger.info(f"EVA_RESPONSE: [{session_id}] Modules: [{modules_str}] {truncated_response}")
    
    def log_emotional_state(self, session_id: str, emotional_state: dict):
        """Log de estado emocional detectado"""
        # Pegar apenas as emoções mais significativas
        significant_emotions = {k: v for k, v in emotional_state.items() if v > 0.3}
        self.logger.info(f"EMOTIONAL_STATE: [{session_id}] {significant_emotions}")
    
    def log_reflection(self, session_id: str, reflection_summary: str):
        """Log de reflexão pós-interação"""
        self.logger.info(f"REFLECTION: [{session_id}] {reflection_summary}")

class ErrorLogger:
    """Logger especializado para erros e exceções"""
    
    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = log_dir
        self.logger = EVALogger.get_logger("Error")
        
        # Criar arquivo específico para erros
        error_log_file = os.path.join(
            log_dir,
            f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - ERROR - %(name)s - %(message)s\n%(exc_info)s",
                "%Y-%m-%d %H:%M:%S"
            )
        )
        
        self.logger.addHandler(error_handler)
    
    def log_model_error(self, model_name: str, error: Exception, context: str = ""):
        """Log de erro relacionado a modelo"""
        self.logger.error(f"MODEL_ERROR: {model_name} | Context: {context} | Error: {str(error)}", exc_info=True)
    
    def log_memory_error(self, error: Exception, vram_usage: float = None):
        """Log de erro de memória"""
        vram_info = f" | VRAM: {vram_usage:.1f}GB" if vram_usage else ""
        self.logger.error(f"MEMORY_ERROR{vram_info} | Error: {str(error)}", exc_info=True)
    
    def log_conversation_error(self, session_id: str, error: Exception, user_input: str = ""):
        """Log de erro durante conversa"""
        input_info = f" | Input: {user_input[:100]}..." if user_input else ""
        self.logger.error(f"CONVERSATION_ERROR: [{session_id}]{input_info} | Error: {str(error)}", exc_info=True)
    
    def log_system_error(self, component: str, error: Exception, context: str = ""):
        """Log de erro geral do sistema"""
        self.logger.error(f"SYSTEM_ERROR: {component} | Context: {context} | Error: {str(error)}", exc_info=True)
