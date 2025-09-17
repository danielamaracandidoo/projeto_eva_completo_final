@echo off
echo ========================================
echo    INSTALADOR AUTOMATICO EVA - WINDOWS
echo ========================================
echo.

:: Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Python não encontrado!
    echo Por favor, instale Python 3.9+ do site oficial:
    echo https://www.python.org/downloads/
    echo ⚠️  IMPORTANTE: Marque "Add Python to PATH" durante instalação
    pause
    exit /b 1
)

echo ✅ Python encontrado!
python --version

:: Verificar se estamos na pasta correta
if not exist "main.py" (
    echo ❌ ERRO: Execute este script na pasta do projeto EVA
    echo Certifique-se de estar na pasta que contém main.py
    pause
    exit /b 1
)

echo ✅ Pasta do projeto encontrada!

:: Criar pasta de modelos se não existir
if not exist "data\models" (
    echo 📁 Criando pasta data\models...
    mkdir data\models
    echo ✅ Pasta data\models criada!
) else (
    echo ✅ Pasta data\models já existe!
)

:: Verificar se modelos existem
set models_found=0
if exist "data\models\mistral-3b-instruct-Q4_K_M.gguf" set /a models_found+=1
if exist "data\models\mistral-7b-instruct-Q4_K_M.gguf" set /a models_found+=1
if exist "data\models\UI-TARS-1.5-7B.i1-Q4_K_M.gguf" set /a models_found+=1

if %models_found% LSS 3 (
    echo ⚠️  AVISO: Nem todos os modelos foram encontrados em data\models\
    echo Modelos necessários:
    echo - mistral-3b-instruct-Q4_K_M.gguf
    echo - mistral-7b-instruct-Q4_K_M.gguf
    echo - UI-TARS-1.5-7B.i1-Q4_K_M.gguf
    echo.
    echo Copie os arquivos .gguf para data\models\ antes de continuar
    set /p continue="Continuar mesmo assim? (s/N): "
    if /i not "%continue%"=="s" (
        echo Instalação cancelada.
        pause
        exit /b 1
    )
) else (
    echo ✅ Todos os modelos encontrados!
)

:: Criar ambiente virtual
if not exist "eva_env" (
    echo 🔧 Criando ambiente virtual...
    python -m venv eva_env
    if errorlevel 1 (
        echo ❌ ERRO: Falha ao criar ambiente virtual
        pause
        exit /b 1
    )
    echo ✅ Ambiente virtual criado!
) else (
    echo ✅ Ambiente virtual já existe!
)

:: Ativar ambiente virtual
echo 🔧 Ativando ambiente virtual...
call eva_env\Scripts\activate.bat

:: Atualizar pip
echo 🔧 Atualizando pip...
python -m pip install --upgrade pip

:: Instalar wheel
echo 🔧 Instalando wheel...
pip install wheel

:: Instalar dependências básicas
echo 🔧 Instalando dependências básicas...
pip install numpy scipy

:: Instalar dependências do projeto
echo 🔧 Instalando dependências do projeto...
pip install -r requirements.txt

:: Instalar dependências específicas do Windows
echo 🔧 Instalando dependências específicas do Windows...

:: Tentar instalar pyaudio
echo 🔧 Instalando pyaudio para funcionalidade de voz...
pip install pyaudio
if errorlevel 1 (
    echo ⚠️  pyaudio falhou - funcionalidade de voz pode não funcionar
    echo Você pode baixar wheel pré-compilado de:
    echo https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
)

:: Instalar outras dependências de voz
pip install SpeechRecognition pyttsx3 gTTS

:: Instalar llama-cpp-python
echo 🔧 Instalando llama-cpp-python para modelos GGUF...
pip install llama-cpp-python
if errorlevel 1 (
    echo ⚠️  llama-cpp-python falhou - tentando versão específica...
    pip install llama-cpp-python==0.2.11
)

:: Instalar interfaces opcionais
echo 🔧 Instalando interfaces web...
pip install gradio streamlit

:: Teste básico
echo 🧪 Executando teste básico...
python -c "
try:
    from config.settings import load_config
    config = load_config()
    print('✅ Configuração carregada com sucesso!')
    
    from core.model_manager import ModelManager
    manager = ModelManager(config)
    print('✅ ModelManager inicializado!')
    
    from core.orchestrator import EVAOrchestrator
    print('✅ EVAOrchestrator importado!')
    
    print('🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!')
    
except Exception as e:
    print(f'❌ ERRO no teste: {e}')
    print('Verifique as dependências e tente novamente')
"

if errorlevel 1 (
    echo.
    echo ❌ TESTE FALHOU - Verifique os erros acima
    echo.
    echo Soluções comuns:
    echo 1. Instalar Visual C++ Build Tools
    echo 2. Verificar se todos os modelos estão em data\models\
    echo 3. Executar como Administrador
    echo.
) else (
    echo.
    echo ========================================
    echo        INSTALAÇÃO CONCLUÍDA! 🎉
    echo ========================================
    echo.
    echo Para usar a EVA:
    echo.
    echo 1. Ativar ambiente virtual:
    echo    eva_env\Scripts\activate
    echo.
    echo 2. Executar EVA:
    echo    python main.py
    echo.
    echo 3. Ou com interface web:
    echo    python main.py --mode web
    echo.
    echo 4. Ou com interface de voz:
    echo    python main.py --mode voice
    echo.
    echo Divirta-se conversando com a EVA! 🤖💬
    echo.
)

pause
