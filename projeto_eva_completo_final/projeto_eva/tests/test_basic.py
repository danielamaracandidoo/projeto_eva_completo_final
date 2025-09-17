"""
Testes básicos para o sistema EVA.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path

# Adicionar o diretório do projeto ao path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import EVAConfig
from core.attention_system import AttentionSystem, IntentType
from utils.logging_system import EVALogger

class TestEVAConfig:
    """Testes para configuração do sistema"""
    
    def test_create_default_config(self):
        """Testa criação de configuração padrão"""
        config = EVAConfig.create_default()
        
        assert config is not None
        assert len(config.models) > 0
        assert 'mistral-7b-instruct' in config.models
        assert config.memory is not None
        assert config.voice is not None
        assert config.hardware is not None
    
    def test_config_validation(self):
        """Testa validação de configuração"""
        config = EVAConfig.create_default()
        
        # Configuração padrão deve ter erros (modelos não existem)
        errors = config.validate()
        assert len(errors) > 0  # Deve ter erros de modelos não encontrados
    
    def test_config_save_load(self):
        """Testa salvamento e carregamento de configuração"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = f.name
        
        try:
            # Criar e salvar configuração
            original_config = EVAConfig.create_default()
            original_config.debug_mode = True
            original_config.save(config_path)
            
            # Carregar configuração
            loaded_config = EVAConfig.load(config_path)
            
            assert loaded_config.debug_mode == True
            assert len(loaded_config.models) == len(original_config.models)
            
        finally:
            os.unlink(config_path)

class TestAttentionSystem:
    """Testes para sistema de atenção"""
    
    @pytest.fixture
    def attention_system(self):
        """Fixture para sistema de atenção"""
        config = EVAConfig.create_default()
        return AttentionSystem(config)
    
    def test_intent_classification(self, attention_system):
        """Testa classificação de intenções"""
        # Teste pergunta
        intent, confidence = attention_system._classify_intent("como você está?")
        assert intent == IntentType.QUESTION
        assert confidence > 0
        
        # Teste tarefa
        intent, confidence = attention_system._classify_intent("crie um texto sobre IA")
        assert intent == IntentType.TASK
        assert confidence > 0
        
        # Teste suporte emocional
        intent, confidence = attention_system._classify_intent("estou me sentindo triste")
        assert intent == IntentType.EMOTIONAL_SUPPORT
        assert confidence > 0
        
        # Teste criativo
        intent, confidence = attention_system._classify_intent("escreva um poema")
        assert intent == IntentType.CREATIVE_REQUEST
        assert confidence > 0
        
        # Teste conversa casual
        intent, confidence = attention_system._classify_intent("oi, tudo bem?")
        assert intent == IntentType.CASUAL_CHAT
        assert confidence > 0
    
    def test_complexity_assessment(self, attention_system):
        """Testa avaliação de complexidade"""
        # Entrada simples
        complexity = attention_system._assess_complexity("oi", type('MockContext', (), {})())
        assert 1 <= complexity <= 5
        
        # Entrada complexa
        complex_input = "analise detalhadamente os múltiplos aspectos da inteligência artificial"
        complexity = attention_system._assess_complexity(complex_input, type('MockContext', (), {})())
        assert complexity >= 2
    
    def test_emotional_intensity(self, attention_system):
        """Testa avaliação de intensidade emocional"""
        # Baixa intensidade
        intensity = attention_system._assess_emotional_intensity("talvez", {})
        assert intensity < 0.5
        
        # Alta intensidade
        intensity = attention_system._assess_emotional_intensity("estou MUITO feliz!!!", {'alegria': 0.9})
        assert intensity > 0.5
    
    def test_urgency_assessment(self, attention_system):
        """Testa avaliação de urgência"""
        # Baixa urgência
        urgency = attention_system._assess_urgency("quando você puder")
        assert urgency < 0.3
        
        # Alta urgência
        urgency = attention_system._assess_urgency("preciso URGENTE agora!!!")
        assert urgency > 0.5

class TestLoggingSystem:
    """Testes para sistema de logging"""
    
    def test_logger_initialization(self):
        """Testa inicialização do sistema de logging"""
        with tempfile.TemporaryDirectory() as temp_dir:
            EVALogger.initialize("DEBUG", temp_dir)
            
            logger = EVALogger.get_logger("TestLogger")
            assert logger is not None
            
            # Testar log
            logger.info("Teste de log")
            
            # Verificar se arquivo foi criado
            log_files = list(Path(temp_dir).glob("*.log"))
            assert len(log_files) > 0

class TestIntegration:
    """Testes de integração básicos"""
    
    @pytest.mark.asyncio
    async def test_basic_system_creation(self):
        """Testa criação básica do sistema sem modelos"""
        # Este teste verifica se as classes podem ser instanciadas
        # sem erros de importação ou sintaxe
        
        config = EVAConfig.create_default()
        attention_system = AttentionSystem(config)
        
        # Criar contexto mock
        mock_context = type('MockContext', (), {
            'user_input': 'teste',
            'conversation_history': [],
            'emotional_state': {},
            'session_id': 'test',
            'timestamp': 0
        })()
        
        # Testar análise de atenção
        analysis = await attention_system.analyze_input(mock_context)
        
        assert analysis is not None
        assert analysis.primary_intent is not None
        assert isinstance(analysis.required_modules, list)
        assert len(analysis.required_modules) > 0

if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v"])
