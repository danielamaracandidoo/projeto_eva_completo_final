# 🚀 Guia Completo de Instalação - EVA no Windows 10

## ✅ **Pré-requisitos**

### 1. **Python 3.9+ (Recomendado: Python 3.11)**
```cmd
# Baixar do site oficial: https://www.python.org/downloads/
# ⚠️ IMPORTANTE: Marcar "Add Python to PATH" durante instalação
```

### 2. **Git (Opcional, mas recomendado)**
```cmd
# Baixar do site: https://git-scm.com/download/win
```

### 3. **Microsoft Visual C++ Build Tools**
```cmd
# Necessário para compilar algumas dependências
# Baixar: https://visualstudio.microsoft.com/visual-cpp-build-tools/
# Ou instalar Visual Studio Community
```

## 📁 **Estrutura de Pastas Necessária**

```
projeto_eva/
├── data/
│   ├── models/          # ← CRIAR ESTA PASTA
│   │   ├── mistral-3b-instruct-Q4_K_M.gguf
│   │   ├── mistral-7b-instruct-Q4_K_M.gguf
│   │   └── UI-TARS-1.5-7B.i1-Q4_K_M.gguf
│   ├── memory/          # ← Já existe (vazia)
│   └── logs/            # ← Já existe (vazia)
├── eva_env/             # ← Ambiente virtual (será criado)
├── config.yaml
├── main.py
└── ... (outros arquivos)
```

## 🔧 **Processo de Instalação Completo**

### **Passo 1: Preparar o Projeto**
```cmd
# 1. Extrair o projeto_eva_completo.zip
# 2. Abrir CMD como Administrador
# 3. Navegar até a pasta do projeto
cd C:\caminho\para\projeto_eva
```

### **Passo 2: Criar Pasta de Modelos**
```cmd
# Criar pasta para modelos
mkdir data\models

# Copiar seus modelos GGUF para data\models\
# - mistral-3b-instruct-Q4_K_M.gguf
# - mistral-7b-instruct-Q4_K_M.gguf  
# - UI-TARS-1.5-7B.i1-Q4_K_M.gguf
```

### **Passo 3: Criar Ambiente Virtual**
```cmd
# Criar ambiente virtual
python -m venv eva_env

# Ativar ambiente virtual
eva_env\Scripts\activate

# Verificar se está ativo (deve aparecer (eva_env) no prompt)
```

### **Passo 4: Atualizar pip e Instalar Dependências**
```cmd
# Atualizar pip
python -m pip install --upgrade pip

# Instalar wheel (evita problemas de compilação)
pip install wheel

# Instalar dependências básicas primeiro
pip install numpy scipy

# Instalar dependências do projeto
pip install -r requirements.txt
```

### **Passo 5: Instalar Dependências Específicas do Windows**

#### **Para Funcionalidade de Voz:**
```cmd
# Reconhecimento de voz
pip install SpeechRecognition pyaudio

# Se pyaudio falhar, baixar wheel pré-compilado:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
# pip install pyaudio-0.2.11-cp311-cp311-win_amd64.whl

# Text-to-Speech
pip install pyttsx3 gTTS
```

#### **Para Modelos GGUF (llama-cpp-python):**
```cmd
# Instalar com suporte CUDA (se tiver GPU NVIDIA)
pip install llama-cpp-python[cuda]

# OU instalar versão CPU apenas
pip install llama-cpp-python
```

#### **Para Interface Web:**
```cmd
pip install gradio streamlit
```

### **Passo 6: Configurar Caminhos dos Modelos**

Editar `config.yaml`:
```yaml
models:
  small_model:
    path: "data/models/mistral-3b-instruct-Q4_K_M.gguf"
    context_length: 4096
    
  medium_model:
    path: "data/models/mistral-7b-instruct-Q4_K_M.gguf"
    context_length: 8192
    
  large_model:
    path: "data/models/UI-TARS-1.5-7B.i1-Q4_K_M.gguf"
    context_length: 8192
```

## 🚀 **Executar o Sistema**

### **Método 1: Terminal Interativo**
```cmd
# Ativar ambiente virtual
eva_env\Scripts\activate

# Executar EVA
python main.py

# Ou com modo específico
python main.py --mode terminal
```

### **Método 2: Interface Web**
```cmd
# Ativar ambiente virtual
eva_env\Scripts\activate

# Executar com interface web
python main.py --mode web
```

### **Método 3: Interface de Voz**
```cmd
# Ativar ambiente virtual
eva_env\Scripts\activate

# Executar com interface de voz
python main.py --mode voice
```

## 🔍 **Verificação de Funcionamento**

### **Teste Básico:**
```cmd
python -c "
from core.orchestrator import EVAOrchestrator
from config.settings import load_config
config = load_config()
print('✅ EVA carregada com sucesso!')
"
```

### **Teste de Modelos:**
```cmd
python -c "
from core.model_manager import ModelManager
from config.settings import load_config
config = load_config()
manager = ModelManager(config)
print('✅ Modelos encontrados!')
"
```

## ⚠️ **Possíveis Problemas e Soluções**

### **Problema 1: Erro de Importação**
```cmd
# Solução: Instalar dependência específica
pip install [nome_da_dependencia]
```

### **Problema 2: Modelos não Encontrados**
```cmd
# Verificar caminhos no config.yaml
# Verificar se arquivos .gguf estão em data/models/
```

### **Problema 3: Erro de Memória**
```cmd
# Editar config.yaml para usar modelo menor primeiro:
default_model: "small_model"
```

### **Problema 4: PyAudio não Instala**
```cmd
# Baixar wheel pré-compilado:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
pip install pyaudio-0.2.11-cp311-cp311-win_amd64.whl
```

### **Problema 5: llama-cpp-python Falha**
```cmd
# Instalar versão específica
pip install llama-cpp-python==0.2.11

# Ou compilar do zero (requer Visual Studio)
pip install llama-cpp-python --force-reinstall --no-cache-dir
```

## 🎯 **Comandos de Exemplo para Testar**

Após iniciar a EVA:

```
# Teste básico
"Olá EVA, como você está?"

# Teste de persona analítica
"Analise os prós e contras de trabalhar remotamente"

# Teste de persona criativa
"Me ajude a criar uma história sobre um robô"

# Teste de agência
"Crie um plano para organizar minha agenda da semana"

# Teste de decisão
"Me ajude a escolher entre Python e JavaScript para meu projeto"
```

## 📋 **Checklist Final**

- [ ] Python 3.9+ instalado com PATH configurado
- [ ] Visual C++ Build Tools instalado
- [ ] Projeto extraído em pasta local
- [ ] Pasta `data/models/` criada
- [ ] 3 arquivos .gguf copiados para `data/models/`
- [ ] Ambiente virtual `eva_env` criado e ativado
- [ ] Todas as dependências instaladas sem erro
- [ ] `config.yaml` com caminhos corretos dos modelos
- [ ] Teste básico executado com sucesso

## 🎉 **Pronto para Usar!**

Se todos os passos foram seguidos, você terá:
- ✅ EVA totalmente funcional
- ✅ 5 personas cognitivas ativas
- ✅ Sistema de agência completo
- ✅ Interface de voz (opcional)
- ✅ Interface web (opcional)
- ✅ Memória episódica e afetiva
- ✅ Sistema de consciência distribuída

**Divirta-se conversando com a EVA! 🤖💬**
