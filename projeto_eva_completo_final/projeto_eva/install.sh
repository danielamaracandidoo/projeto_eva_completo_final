#!/bin/bash

# Script de instalação automatizada para EVA
# Este script configura o ambiente completo para executar a EVA

set -e  # Parar em caso de erro

echo "🤖 Instalador da EVA - Assistente de IA Pessoal"
echo "=============================================="

# Verificar Python
echo "🐍 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.8 ou superior."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION encontrado"

# Verificar se está no diretório correto
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    echo "❌ Execute este script no diretório raiz do projeto EVA"
    exit 1
fi

# Criar ambiente virtual
echo "📦 Criando ambiente virtual..."
if [ ! -d "eva_env" ]; then
    python3 -m venv eva_env
    echo "✅ Ambiente virtual criado"
else
    echo "ℹ️  Ambiente virtual já existe"
fi

# Ativar ambiente virtual
echo "🔄 Ativando ambiente virtual..."
source eva_env/bin/activate

# Atualizar pip
echo "⬆️  Atualizando pip..."
pip install --upgrade pip

# Instalar dependências
echo "📚 Instalando dependências..."
pip install -r requirements.txt

# Verificar se CUDA está disponível
echo "🔍 Verificando suporte CUDA..."
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detectada"
    echo "🚀 Instalando PyTorch com suporte CUDA..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    
    # Instalar monitoramento GPU
    pip install nvidia-ml-py3
else
    echo "⚠️  NVIDIA GPU não detectada. Usando versão CPU do PyTorch."
    echo "💡 Para melhor performance, considere usar uma GPU NVIDIA."
fi

# Criar estrutura de diretórios
echo "📁 Criando estrutura de diretórios..."
mkdir -p data/{models,memory,logs}
mkdir -p tests

# Inicializar configuração
echo "⚙️  Inicializando configuração..."
if [ ! -f "config.yaml" ]; then
    python3 -c "from config.settings import EVAConfig; EVAConfig.create_default().save('config.yaml')"
    echo "✅ Configuração padrão criada"
else
    echo "ℹ️  Arquivo de configuração já existe"
fi

# Verificar modelos
echo "🧠 Verificando modelos..."
MODELS_DIR="data/models"

download_model() {
    local model_name="$1"
    local model_url="$2"
    local model_file="$MODELS_DIR/$model_name"
    
    if [ ! -f "$model_file" ]; then
        echo "📥 Baixando $model_name..."
        echo "⚠️  ATENÇÃO: Este download pode ser grande (vários GB)"
        read -p "Deseja baixar $model_name agora? (s/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            wget -O "$model_file" "$model_url"
            echo "✅ $model_name baixado"
        else
            echo "⏭️  Pulando download de $model_name"
            echo "💡 Você pode baixar manualmente depois em: $model_url"
        fi
    else
        echo "✅ $model_name já existe"
    fi
}

# URLs dos modelos (estas são URLs de exemplo - substitua pelas URLs reais)
echo "📋 Modelos necessários:"
echo "   • mistral-7b-instruct-Q4_K_M.gguf (Cérebro principal)"
echo "   • UI-TARS-1.5-7B.i1-Q4_K_M.gguf (Executor de ações)"  
echo "   • mistral-3b-instruct-Q4_K_M.gguf (Triagem rápida)"
echo ""
echo "⚠️  IMPORTANTE: Os modelos são grandes (2-4GB cada)"
echo "💡 Você pode baixá-los manualmente de:"
echo "   • https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF"
echo "   • https://huggingface.co/TheBloke/UI-TARS-1.5-7B-GGUF"
echo "   • https://huggingface.co/TheBloke/Mistral-3B-Instruct-GGUF"

# Testar instalação
echo "🧪 Testando instalação..."
if python3 -c "import torch; import transformers; import llama_cpp; print('✅ Dependências principais OK')"; then
    echo "✅ Teste de dependências passou"
else
    echo "❌ Erro nas dependências"
    exit 1
fi

# Criar script de ativação
echo "📝 Criando script de ativação..."
cat > activate_eva.sh << 'EOF'
#!/bin/bash
# Script para ativar ambiente EVA
echo "🤖 Ativando ambiente EVA..."
source eva_env/bin/activate
echo "✅ Ambiente ativado!"
echo "💡 Execute: python main.py --help para ver opções"
echo "🚀 Execute: python main.py para iniciar EVA"
EOF

chmod +x activate_eva.sh

# Finalização
echo ""
echo "🎉 Instalação concluída!"
echo "=============================================="
echo ""
echo "📋 Próximos passos:"
echo "   1. Ative o ambiente: source activate_eva.sh"
echo "   2. Baixe os modelos necessários (se não fez ainda)"
echo "   3. Execute: python main.py --help para ver opções"
echo "   4. Execute: python main.py para iniciar EVA"
echo ""
echo "📚 Documentação completa no README.md"
echo "🐛 Problemas? Verifique os logs em data/logs/"
echo ""
echo "🤖 Bem-vindo à EVA!"
