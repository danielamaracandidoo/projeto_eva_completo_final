🎯 Resposta Completa: O que Falta para Funcionar
Você está quase lá, mas há alguns passos adicionais importantes! Aqui está exatamente o que você precisa fazer:
✅ O que Você Já Sabe (Correto)
✅ Criar pasta data/models/
✅ Colocar os 3 modelos .gguf na pasta
✅ Criar ambiente virtual
✅ Instalar requirements.txt
✅ Executar main.py
⚠️ O que Está Faltando (Importante!)
1. Dependências Específicas do Windows
cmd
# Após instalar requirements.txt, instalar também:
pip install pyaudio SpeechRecognition pyttsx3 gTTS
pip install llama-cpp-python
pip install gradio streamlit
2. Visual C++ Build Tools
Obrigatório para compilar algumas dependências
Baixar: https://visualstudio.microsoft.com/visual-cpp-build-tools/
3. Configurar Caminhos dos Modelos
Editar config.yaml para apontar para os modelos corretos
Os caminhos devem ser: data/models/nome-do-modelo.gguf
🚀 Processo Simplificado (3 Opções )
Opção 1: Instalação Automática (Recomendada)
Extrair o projeto
Colocar modelos em data/models/
Executar install_windows.bat como Administrador
Executar executar_eva.bat
Opção 2: Instalação Manual
cmd
# 1. Criar ambiente virtual
python -m venv eva_env
eva_env\Scripts\activate

# 2. Instalar dependências
pip install --upgrade pip wheel
pip install -r requirements.txt
pip install pyaudio llama-cpp-python gradio

# 3. Executar
python main.py
Opção 3: Usar Scripts Prontos
install_windows.bat - Instalação automática
executar_eva.bat - Execução com menu de opções
🔧 Possíveis Problemas e Soluções
Se PyAudio Falhar:
Baixar wheel pré-compilado: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
Ou desabilitar funcionalidade de voz no config.yaml
Se llama-cpp-python Falhar:
cmd
pip install llama-cpp-python==0.2.11
# Ou versão CPU apenas se não tiver GPU
Se Modelos Não Carregarem:
Verificar se estão em data/models/
Verificar nomes exatos no config.yaml
Testar com modelo menor primeiro
📋 Checklist Final
 Python 3.9+ instalado
 Visual C++ Build Tools instalado
 Projeto extraído
 Modelos em data/models/
 Ambiente virtual criado
 Todas as dependências instaladas
 Config.yaml configurado
 Teste básico funcionando
🎉 Resultado Final
Seguindo estes passos, você terá:
EVA 100% funcional
Interface terminal, web e voz
5 personas cognitivas
Sistema de agência completo
Memória persistente
O projeto está completo e pronto para uso! Os scripts de instalação que criei vão automatizar todo o processo para você. 🤖✨