import sys
import os
import argparse
from robo_rios import RoboRios

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def modo_interativo():
    print("============================================================")
    print("✍️  ASSISTENTE INTERATIVO DE REDAÇÃO - RIOS MINISTÉRIO  ✍️")
    print("============================================================")
    print("Digite os dados da sua matéria e deixe a Inteligência Artificial")
    print("organizar, formatar, ilustrar e publicar no seu site!\n")
    
    try:
        tema = input("👉 1. Digite o TEMA / TÍTULO da sua matéria: ").strip()
        if not tema:
            print("❌ O tema é obrigatório para prosseguir.")
            return
            
        print("\n👉 2. Digite ou cole o seu TEXTO / ANOTAÇÕES / REFLEXÃO:")
        print("   (Dica: Pressione Enter e digite 'FIM' na linha separada quando terminar de digitar/colar)")
        linhas_texto = []
        while True:
            linha = input()
            if linha.strip().upper() == "FIM":
                break
            linhas_texto.append(linha)
        texto_usuario = "\n".join(linhas_texto).strip()
        
        caminho_img = input("\n👉 3. Caminho da IMAGEM no seu computador (ou deixe VAZIO para a IA gerar foto HD): ").strip()
        if caminho_img and not os.path.exists(caminho_img):
            print(f"⚠️ Imagem '{caminho_img}' não encontrada. A IA irá gerar uma foto HD automática na capa.")
            caminho_img = None
            
        cat_str = input("\n👉 4. ID da Categoria no site (8=Mensagens, 11=Mundo Cristão, 1=Geral) [Padrão: 8]: ").strip()
        cat_id = int(cat_str) if cat_str.isdigit() else 8
        
        rascunho_str = input("\n👉 5. Deseja publicar AO VIVO agora ou salvar como RASCUNHO? [V=Ao Vivo / R=Rascunho, Padrão: R]: ").strip().upper()
        teste_rascunho = (rascunho_str != "V")
        
        print("\n------------------------------------------------------------")
        print("⏳ Iniciando redação inteligente, processamento visual e postagem...")
        print("------------------------------------------------------------")
        
        robo = RoboRios(teste_rascunho=teste_rascunho)
        robo.executar_fluxo_manual(tema=tema, texto=texto_usuario, caminho_img=caminho_img, categoria_id=cat_id)
        
    except KeyboardInterrupt:
        print("\n🚫 Operação cancelada pelo usuário.")

def main():
    parser = argparse.ArgumentParser(description="Publicador Manual Rios News Bot")
    parser.add_argument("--tema", type=str, help="Tema ou título base da matéria")
    parser.add_argument("--texto", type=str, default="", help="Texto ou anotações para expansão")
    parser.add_argument("--img", type=str, default=None, help="Caminho do arquivo local de imagem")
    parser.add_argument("--cat", type=int, default=8, help="ID da Categoria no WordPress (Padrão: 8 = Mensagens)")
    parser.add_argument("--rascunho", action="store_true", help="Salva como rascunho no WordPress")
    
    args = parser.parse_args()
    
    if args.tema:
        robo = RoboRios(teste_rascunho=args.rascunho)
        robo.executar_fluxo_manual(tema=args.tema, texto=args.texto, caminho_img=args.img, categoria_id=args.cat)
    else:
        modo_interativo()

if __name__ == "__main__":
    main()
