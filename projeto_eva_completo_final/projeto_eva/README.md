# EVA - Assistente de IA Pessoal Local

## Visão Geral

EVA (Enhanced Virtual Assistant) é um assistente de IA pessoal local projetado para ser uma companheira digital empática, inteligente e evolutiva. O sistema utiliza uma arquitetura de "consciência distribuída" com múltiplas personas cognitivas especializadas, otimizada para hardware limitado.

## Características Principais

- **Consciência Distribuída**: Sistema de múltiplas personas cognitivas (Analítica, Criativa, Empática, Executiva, Reflexiva)
- **Memória Evolutiva**: Sistema de memória afetiva que aprende e evolui com as interações
- **Agência no Mundo Real**: Capacidade de controlar mouse e teclado através do modelo UI-TARS
- **Interface de Voz**: Suporte completo para Speech-to-Text (Whisper) e Text-to-Speech (Piper/Coqui)
- **Otimização para Hardware Limitado**: Gerenciamento inteligente de VRAM com carregamento sequencial de modelos

## Requisitos de Hardware

### Hardware Alvo
- **CPU**: Intel Core i7-2600 (2011) ou superior
- **GPU**: NVIDIA GTX 1660 SUPER (6GB VRAM) ou superior
- **RAM**: 16GB
- **Armazenamento**: 20GB livres para modelos e dados

### Modelos Necessários
- `mistral-7b-instruct-Q4_K_M.gguf` (Cérebro principal)
- `UI-TARS-1.5-7B.i1-Q4_K_M.gguf` (Executor de ações)
- `mistral-3b-instruct-Q4_K_M.gguf` (Triagem rápida)

## Instalação

### 1. Preparação do Ambiente

```bash
# Clonar ou criar estrutura do projeto
git clone <repository-url> projeto_eva
cd projeto_eva

# Criar ambiente virtual
python -m venv eva_env

# Ativar ambiente virtual
# Linux/Mac:
source eva_env/bin/activate
# Windows:
eva_env\Scripts\activate
```

### 2. Instalação de Dependências

```bash
# Instalar dependências Python
pip install -r requirements.txt

# Instalar PyTorch com suporte CUDA (se disponível)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 3. Download dos Modelos

```bash
# Criar diretório para modelos
mkdir -p data/models

# Baixar Mistral 7B Instruct
wget -O data/models/mistral-7b-instruct-Q4_K_M.gguf \
  "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf"

# Baixar UI-TARS 7B
wget -O data/models/UI-TARS-1.5-7B.i1-Q4_K_M.gguf \
  "https://huggingface.co/TheBloke/UI-TARS-1.5-7B-GGUF/resolve/main/ui-tars-1.5-7b.i1-Q4_K_M.gguf"

# Baixar Mistral 3B
wget -O data/models/mistral-3b-instruct-Q4_K_M.gguf \
  "https://huggingface.co/TheBloke/Mistral-3B-Instruct-GGUF/resolve/main/mistral-3b-instruct.Q4_K_M.gguf"
```

### 4. Configuração Inicial

```bash
# Inicializar configuração padrão
python -c "from config.settings import EVAConfig; EVAConfig.create_default().save('config.yaml')"

# Criar estrutura de diretórios
mkdir -p data/{memory,logs}
mkdir -p tests
```

## Uso

### Modo Interativo (Terminal)

```bash
python main.py --mode interactive
```

### Interface Web

```bash
python main.py --mode web --port 7860
```

### Modo de Voz (Futuro)

```bash
python main.py --mode voice
```

## Arquitetura

### Componentes Principais

1. **Orquestrador Central** (`core/orchestrator.py`)
   - Gerencia o fluxo principal de conversação
   - Coordena a troca sequencial de modelos na VRAM
   - Implementa ciclos de reflexão pós-interação

2. **Gerenciador de Modelos** (`core/model_manager.py`)
   - Carregamento/descarregamento otimizado de modelos GGUF
   - Monitoramento de VRAM e otimizações de performance
   - Interface unificada para diferentes modelos

3. **Sistema de Consciência** (`core/consciousness.py`)
   - Coordena as diferentes personas cognitivas
   - Sintetiza respostas de múltiplos módulos
   - Mantém coerência da personalidade

4. **Sistema de Atenção** (`core/attention_system.py`)
   - Analisa entrada do usuário para determinar intenção
   - Decide quais módulos cognitivos ativar
   - Otimiza uso de recursos baseado no contexto

### Módulos Especializados

- **Memória** (`modules/memory/`)
  - Memória episódica para histórico de conversas
  - Memória afetiva para relacionamento evolutivo
  - Sistema de busca vetorial com FAISS

- **Personas** (`modules/personas/`)
  - Analítica: Raciocínio lógico e resolução de problemas
  - Criativa: Imaginação e pensamento inovador
  - Empática: Inteligência emocional e suporte
  - Executiva: Planejamento e execução de tarefas
  - Reflexiva: Auto-análise e aprendizado contínuo

- **Agência** (`modules/agency/`)
  - Interface com UI-TARS para controle de interface
  - Executor de ações no sistema operacional

- **Voz** (`modules/voice/`)
  - Speech-to-Text com Whisper
  - Text-to-Speech com Piper/Coqui

## Configuração

O arquivo `config.yaml` permite personalizar:

- Parâmetros dos modelos (temperatura, top_p, etc.)
- Configurações de memória e armazenamento
- Configurações de voz e áudio
- Otimizações de hardware
- Níveis de logging e debug

## Desenvolvimento

### Estrutura do Projeto

```
projeto_eva/
├── core/                    # Componentes centrais
├── modules/                 # Módulos especializados
├── config/                  # Configurações e prompts
├── data/                    # Modelos e dados
├── utils/                   # Utilitários e ferramentas
├── tests/                   # Testes automatizados
├── requirements.txt         # Dependências Python
├── config.yaml             # Configuração principal
└── main.py                 # Ponto de entrada
```

### Executando Testes

```bash
python -m pytest tests/ -v
```

### Contribuindo

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Suporte

Para suporte e dúvidas:
- Abra uma issue no GitHub
- Consulte a documentação técnica em `docs/`
- Verifique os logs em `data/logs/` para diagnóstico

## Roadmap

- [ ] Interface de voz completa
- [ ] Integração com APIs externas
- [ ] Sistema de plugins
- [ ] Interface móvel
- [ ] Suporte para múltiplos idiomas
- [ ] Modo de treinamento personalizado
