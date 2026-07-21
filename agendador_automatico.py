import time
import schedule
import subprocess
import sys
import os
import json

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def executar_robo():
    print("\n" + "="*70)
    print("🤖 [AGENDADOR] INICIANDO CICLO AUTOMÁTICO DO RIOS NEWS BOT...")
    print("="*70)
    caminho_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "robo_rios.py")
    try:
        # Executa no modo 'ambos' sem forçar rascunho (usa o status padrao de config.json)
        subprocess.run([sys.executable, caminho_script, "--modo", "ambos"], check=True)
    except Exception as e:
        print(f"❌ Erro durante a execução agendada: {e}")
    print("🤖 [AGENDADOR] CICLO CONCLUÍDO. AGUARDANDO PRÓXIMO HORÁRIO...\n")

def main():
    if "--instalar-windows" in sys.argv:
        instalar_agendador_windows()
        return

    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    intervalo = config.get("agendamento", {}).get("intervalo_horas", 6)
    
    print(f"⏰ Rios News Bot - Agendador Contínuo iniciado!")
    print(f"🔄 O robô executará automaticamente a cada {intervalo} horas.")
    print("👉 Pressione Ctrl+C para parar este processo em segundo plano.")
    
    # Roda uma vez imediatamente ao iniciar
    executar_robo()
    
    # Agenda as próximas execuções
    schedule.every(intervalo).hours.do(executar_robo)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def instalar_agendador_windows():
    """
    Cria uma tarefa no Agendador de Tarefas do Windows (Task Scheduler) para rodar o robô automaticamente mesmo se o terminal for fechado.
    """
    caminho_py = sys.executable
    caminho_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "robo_rios.py")
    nome_tarefa = "RiosNewsBot_AutoPost"
    
    comando = f'schtasks /create /tn "{nome_tarefa}" /tr "\"{caminho_py}\" \"{caminho_script}\" --modo ambos" /sc hourly /mo 6 /f'
    print(f"🔧 Registrando tarefa no Windows: {nome_tarefa}...")
    try:
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
        if resultado.returncode == 0:
            print("✅ Tarefa agendada com sucesso no Windows!")
            print("🚀 O robô agora rodará em segundo plano no Windows a cada 6 horas automaticamente.")
        else:
            print(f"⚠️ Não foi possível registrar no Windows (pode ser necessário rodar como Administrador):\n{resultado.stderr}")
    except Exception as e:
        print(f"❌ Erro ao registrar tarefa: {e}")

if __name__ == "__main__":
    main()
