@echo off
title EVA - Assistente de IA Pessoal

:: Verificar se estamos na pasta correta
if not exist "main.py" (
    echo ❌ ERRO: Execute este script na pasta do projeto EVA
    pause
    exit /b 1
)

:: Verificar se ambiente virtual existe
if not exist "eva_env\Scripts\activate.bat" (
    echo ❌ ERRO: Ambiente virtual não encontrado!
    echo Execute primeiro o install_windows.bat
    pause
    exit /b 1
)

echo ========================================
echo      EVA - Assistente de IA Pessoal
echo ========================================
echo.

:: Ativar ambiente virtual
echo 🔧 Ativando ambiente virtual...
call eva_env\Scripts\activate.bat

:: Menu de opções
echo Escolha o modo de execução:
echo.
echo 1. Terminal (modo texto)
echo 2. Interface Web (navegador)
echo 3. Interface de Voz
echo 4. Modo Debug
echo.
set /p choice="Digite sua escolha (1-4): "

if "%choice%"=="1" (
    echo 🚀 Iniciando EVA no modo terminal...
    python main.py --mode terminal
) else if "%choice%"=="2" (
    echo 🚀 Iniciando EVA no modo web...
    echo Interface web será aberta no navegador
    python main.py --mode web
) else if "%choice%"=="3" (
    echo 🚀 Iniciando EVA no modo voz...
    echo Certifique-se de ter um microfone conectado
    python main.py --mode voice
) else if "%choice%"=="4" (
    echo 🚀 Iniciando EVA no modo debug...
    python main.py --debug --verbose
) else (
    echo ❌ Opção inválida! Iniciando modo padrão...
    python main.py
)

echo.
echo EVA encerrada. Pressione qualquer tecla para sair...
pause >nul
