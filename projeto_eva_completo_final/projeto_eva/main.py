#!/usr/bin/env python3
"""
EVA - Assistente de IA Pessoal
Ponto de entrada principal do sistema
"""

import asyncio
import argparse
import signal
import sys
import os
from pathlib import Path

# Adicionar o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from core.orchestrator import EVAOrchestrator, create_eva_instance
from utils.logging_system import EVALogger
from config.settings import EVAConfig

class EVAInterface:
    """Interface principal para interação com a EVA"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.eva: EVAOrchestrator = None
        self.logger = None
        self.running = False
    
    async def initialize(self):
        """Inicializa o sistema EVA"""
        try:
            print("🤖 Inicializando EVA...")
            
            # Validar configuração
            config = EVAConfig.load(self.config_path)
            errors = config.validate()
            
            if errors:
                print("❌ Erros de configuração encontrados:")
                for error in errors:
                    print(f"   - {error}")
                return False
            
            # Criar instância da EVA
            self.eva = await create_eva_instance(self.config_path)
            self.logger = EVALogger.get_logger("EVAInterface")
            
            print("✅ EVA inicializada com sucesso!")
            print("💬 Digite 'sair' para encerrar ou 'ajuda' para ver comandos disponíveis.\n")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na inicialização: {e}")
            if self.logger:
                self.logger.error(f"Erro na inicialização: {e}")
            return False
    
    async def run_interactive(self):
        """Executa modo interativo via terminal"""
        self.running = True
        
        print(f"🎯 Sessão iniciada: {self.eva.get_session_id()}")
        print("=" * 50)
        
        while self.running:
            try:
                # Obter entrada do usuário
                user_input = input("\n👤 Você: ").strip()
                
                if not user_input:
                    continue
                
                # Comandos especiais
                if user_input.lower() in ['sair', 'exit', 'quit']:
                    print("\n👋 Encerrando EVA...")
                    break
                elif user_input.lower() in ['ajuda', 'help']:
                    self._show_help()
                    continue
                elif user_input.lower() == 'status':
                    await self._show_status()
                    continue
                elif user_input.lower() == 'limpar':
                    self._clear_screen()
                    continue
                elif user_input.lower() == 'stats':
                    await self._show_detailed_stats()
                    continue
                
                # Processar entrada
                print("🤖 EVA: ", end="", flush=True)
                
                try:
                    response = await self.eva.process_conversation(user_input)
                    print(response)
                except Exception as e:
                    print(f"Desculpe, ocorreu um erro: {e}")
                    if self.logger:
                        self.logger.error(f"Erro no processamento: {e}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Encerrando EVA...")
                break
            except EOFError:
                print("\n\n👋 Encerrando EVA...")
                break
            except Exception as e:
                print(f"❌ Erro inesperado: {e}")
                if self.logger:
                    self.logger.error(f"Erro inesperado: {e}")
    
    async def run_voice_mode(self):
        """Executa modo de voz (implementação futura)"""
        print("🎤 Modo de voz ainda não implementado")
        print("📝 Esta funcionalidade será adicionada em versões futuras")
        
        # TODO: Implementar interface de voz com Whisper e Piper/Coqui
        # - Captura de áudio do microfone
        # - Processamento STT com Whisper
        # - Processamento da resposta
        # - Síntese TTS com Piper/Coqui
        # - Reprodução de áudio
    
    async def run_web_interface(self, port: int = 7860):
        """Executa interface web usando Gradio"""
        try:
            import gradio as gr
            
            async def chat_function(message, history):
                if not message.strip():
                    return history, ""
                
                try:
                    response = await self.eva.process_conversation(message)
                    history.append((message, response))
                except Exception as e:
                    error_msg = f"Erro: {str(e)}"
                    history.append((message, error_msg))
                
                return history, ""
            
            def sync_chat_function(message, history):
                """Wrapper síncrono para o Gradio"""
                return asyncio.run(chat_function(message, history))
            
            # Criar interface Gradio
            with gr.Blocks(
                title="EVA - Assistente Pessoal",
                theme=gr.themes.Soft(),
                css="""
                .gradio-container {
                    max-width: 800px !important;
                    margin: auto !important;
                }
                """
            ) as interface:
                
                gr.Markdown("""
                # 🤖 EVA - Sua Assistente Pessoal
                
                Converse naturalmente com a EVA. Ela possui diferentes módulos cognitivos 
                especializados e memória evolutiva para um relacionamento mais profundo.
                """)
                
                with gr.Row():
                    with gr.Column(scale=4):
                        chatbot = gr.Chatbot(
                            label="Conversa com EVA",
                            height=500,
                            show_label=True
                        )
                        
                        with gr.Row():
                            msg = gr.Textbox(
                                label="Sua mensagem",
                                placeholder="Digite sua mensagem aqui...",
                                lines=2,
                                scale=4
                            )
                            send_btn = gr.Button("Enviar", scale=1, variant="primary")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### ℹ️ Informações")
                        
                        session_info = gr.Textbox(
                            label="Sessão",
                            value=f"ID: {self.eva.get_session_id()}",
                            interactive=False
                        )
                        
                        interaction_count = gr.Number(
                            label="Interações",
                            value=0,
                            interactive=False
                        )
                        
                        status_btn = gr.Button("Atualizar Status")
                
                # Configurar eventos
                msg.submit(
                    sync_chat_function,
                    inputs=[msg, chatbot],
                    outputs=[chatbot, msg]
                )
                
                send_btn.click(
                    sync_chat_function,
                    inputs=[msg, chatbot],
                    outputs=[chatbot, msg]
                )
                
                def update_status():
                    return (
                        f"ID: {self.eva.get_session_id()}",
                        self.eva.get_interaction_count()
                    )
                
                status_btn.click(
                    update_status,
                    outputs=[session_info, interaction_count]
                )
            
            print(f"🌐 Interface web iniciada em: http://localhost:{port}")
            print("📱 Acesse pelo navegador para usar a interface gráfica")
            print("⏹️  Pressione Ctrl+C para parar o servidor")
            
            interface.launch(
                server_port=port,
                share=False,
                show_error=True,
                quiet=False
            )
            
        except ImportError:
            print("❌ Gradio não instalado. Execute: pip install gradio")
            print("💡 Ou use o modo interativo: python main.py --mode interactive")
        except Exception as e:
            print(f"❌ Erro na interface web: {e}")
            if self.logger:
                self.logger.error(f"Erro na interface web: {e}")
    
    async def shutdown(self):
        """Encerra o sistema de forma limpa"""
        if self.eva:
            await self.eva.shutdown()
        print("👋 EVA encerrada. Até logo!")
    
    def _show_help(self):
        """Mostra comandos disponíveis"""
        print("""
📋 Comandos disponíveis:
   • sair/exit/quit - Encerrar EVA
   • ajuda/help - Mostrar esta ajuda
   • status - Mostrar status básico do sistema
   • stats - Mostrar estatísticas detalhadas
   • limpar - Limpar tela
   
💬 Para conversar, simplesmente digite sua mensagem!

🧠 A EVA possui diferentes módulos cognitivos:
   • Analítico - Para raciocínio lógico e resolução de problemas
   • Criativo - Para imaginação e pensamento inovador
   • Empático - Para suporte emocional e relacionamento
   • Executivo - Para planejamento e execução de tarefas
   • Reflexivo - Para auto-análise e aprendizado contínuo
        """)
    
    async def _show_status(self):
        """Mostra status básico do sistema"""
        if not self.eva:
            print("❌ EVA não inicializada")
            return
        
        try:
            status = await self.eva.get_system_status()
            
            print(f"""
📊 Status do Sistema:
   • Estado: {status['conversation_state'].title()} ✅
   • Sessão: {status['session_id']}
   • Interações: {status['interaction_count']}
   • Interações bem-sucedidas: {status['successful_interactions']}
   • Tempo médio de resposta: {status['avg_response_time']:.2f}s
   • Modelo atual: {status.get('model_manager', {}).get('current_model', 'N/A')}
            """)
            
        except Exception as e:
            print(f"❌ Erro ao obter status: {e}")
    
    async def _show_detailed_stats(self):
        """Mostra estatísticas detalhadas"""
        if not self.eva:
            print("❌ EVA não inicializada")
            return
        
        try:
            status = await self.eva.get_system_status()
            
            print("\n" + "="*60)
            print("📈 ESTATÍSTICAS DETALHADAS DA EVA")
            print("="*60)
            
            # Status geral
            print(f"\n🎯 SESSÃO ATUAL:")
            print(f"   ID: {status['session_id']}")
            print(f"   Estado: {status['conversation_state']}")
            print(f"   Interações: {status['interaction_count']}")
            print(f"   Taxa de sucesso: {status['successful_interactions']}/{status['interaction_count']}")
            print(f"   Tempo médio: {status['avg_response_time']:.2f}s")
            
            # Status dos modelos
            if 'model_manager' in status:
                mm_stats = status['model_manager']
                print(f"\n🧠 MODELOS:")
                print(f"   Modelo atual: {mm_stats.get('current_model', 'N/A')}")
                print(f"   Modelos carregados: {mm_stats.get('loaded_models', [])}")
                print(f"   Trocas de modelo: {mm_stats.get('model_switches', 0)}")
                print(f"   Tokens gerados: {mm_stats.get('total_tokens_generated', 0)}")
                print(f"   TPS médio: {mm_stats.get('avg_tokens_per_second', 0):.2f}")
                
                if 'hardware' in mm_stats:
                    hw_stats = mm_stats['hardware']
                    if 'current' in hw_stats:
                        current = hw_stats['current']
                        print(f"\n💻 HARDWARE:")
                        print(f"   CPU: {current.get('cpu_percent', 0):.1f}%")
                        print(f"   RAM: {current.get('ram_percent', 0):.1f}%")
                        print(f"   VRAM: {current.get('vram_percent', 0):.1f}% "
                              f"({current.get('vram_used_gb', 0):.1f}GB/"
                              f"{current.get('vram_total_gb', 0):.1f}GB)")
                        print(f"   GPU Temp: {current.get('gpu_temp', 0):.0f}°C")
            
            # Status da consciência
            if 'consciousness' in status:
                cons_stats = status['consciousness']
                if not cons_stats.get('no_data', False):
                    print(f"\n🧩 CONSCIÊNCIA:")
                    print(f"   Sínteses realizadas: {cons_stats.get('total_syntheses', 0)}")
                    print(f"   Taxa de sucesso: {cons_stats.get('success_rate', 0):.2f}")
                    print(f"   Complexidade média: {cons_stats.get('avg_complexity', 0):.1f}/5")
                    print(f"   Intensidade emocional média: {cons_stats.get('avg_emotional_intensity', 0):.2f}")
                    
                    module_usage = cons_stats.get('module_usage', {})
                    if module_usage:
                        print(f"   Módulos mais usados:")
                        for module, count in sorted(module_usage.items(), key=lambda x: x[1], reverse=True):
                            print(f"     • {module.title()}: {count}")
            
            # Status das memórias
            if 'episodic_memory' in status:
                em_stats = status['episodic_memory']
                print(f"\n💭 MEMÓRIA EPISÓDICA:")
                print(f"   Entradas totais: {em_stats.get('total_entries', 0)}")
                print(f"   Sessões únicas: {em_stats.get('unique_sessions', 0)}")
                print(f"   Buscas realizadas: {em_stats.get('search_count', 0)}")
                print(f"   Índice vetorial: {em_stats.get('vector_index_size', 0)} vetores")
            
            if 'affective_memory' in status:
                am_stats = status['affective_memory']
                print(f"\n❤️  MEMÓRIA AFETIVA:")
                print(f"   Entradas totais: {am_stats.get('total_entries', 0)}")
                print(f"   Sessões únicas: {am_stats.get('unique_sessions', 0)}")
                print(f"   Reflexões: {am_stats.get('total_reflections', 0)}")
                print(f"   Intensidade emocional média: {am_stats.get('avg_emotional_intensity', 0):.2f}")
                print(f"   Impacto no relacionamento médio: {am_stats.get('avg_relationship_impact', 0):.2f}")
            
            print("\n" + "="*60)
            
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
            if self.logger:
                self.logger.error(f"Erro ao obter estatísticas: {e}")
    
    def _clear_screen(self):
        """Limpa a tela"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("🤖 EVA - Assistente de IA Pessoal")
        print("=" * 50)

async def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="EVA - Assistente de IA Pessoal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py                          # Modo interativo (padrão)
  python main.py --mode web               # Interface web
  python main.py --mode web --port 8080   # Interface web na porta 8080
  python main.py --config custom.yaml    # Usar configuração personalizada
        """
    )
    
    parser.add_argument(
        "--config", 
        default="config.yaml",
        help="Caminho para arquivo de configuração (padrão: config.yaml)"
    )
    parser.add_argument(
        "--mode",
        choices=["interactive", "web", "voice"],
        default="interactive",
        help="Modo de interface (padrão: interactive)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Porta para interface web (padrão: 7860)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Ativar modo debug"
    )
    
    args = parser.parse_args()
    
    # Verificar se arquivo de configuração existe
    if not os.path.exists(args.config):
        print(f"⚠️  Arquivo de configuração não encontrado: {args.config}")
        print("📝 Criando configuração padrão...")
        
        # Criar configuração padrão
        try:
            config = EVAConfig.create_default()
            config.save(args.config)
            print(f"✅ Configuração padrão criada em: {args.config}")
        except Exception as e:
            print(f"❌ Erro ao criar configuração padrão: {e}")
            return 1
    
    # Criar interface
    interface = EVAInterface(args.config)
    
    # Configurar handler para encerramento limpo
    def signal_handler(signum, frame):
        print("\n🛑 Sinal de interrupção recebido...")
        interface.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Inicializar sistema
        if not await interface.initialize():
            return 1
        
        # Executar modo apropriado
        if args.mode == "interactive":
            await interface.run_interactive()
        elif args.mode == "web":
            await interface.run_web_interface(args.port)
        elif args.mode == "voice":
            await interface.run_voice_mode()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário")
        return 0
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        return 1
    
    finally:
        # Encerramento limpo
        await interface.shutdown()

if __name__ == "__main__":
    # Configurar política de event loop para Windows
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Executar aplicação
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
