import argparse
import sys
import os
import json

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
from buscador_youtube import BuscadorYouTube
from buscador_tendencias import BuscadorTendencias
from gerador_artigos import GeradorArtigos
from gerador_imagens import GeradorImagens
from publicador_wp import PublicadorWordPress

class RoboRios:
    def __init__(self, config_path="config.json", teste_rascunho=False):
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_path)
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
            
        self.teste_rascunho = teste_rascunho
        self.status_publicacao = "draft" if teste_rascunho else self.config.get("wordpress", {}).get("status_padrao", "draft")
        
        self.buscador_yt = BuscadorYouTube(self.config_path)
        self.buscador_tend = BuscadorTendencias(self.config_path)
        self.gerador_art = GeradorArtigos(self.config_path)
        self.gerador_img = GeradorImagens()
        self.publicador = PublicadorWordPress(self.config_path)

    def executar_fluxo_youtube(self, max_por_canal=2):
        print("\n" + "="*60)
        print("📺 INICIANDO FLUXO: VÍDEOS DO YOUTUBE PARA ARTIGOS")
        print("="*60)
        
        canais = self.config.get("canais_youtube", [])
        total_processados = 0
        
        for canal in canais:
            videos = self.buscador_yt.obter_videos_recentes(canal, max_videos=max_por_canal)
            if not videos:
                continue
                
            for v in videos:
                print(f"\n🎬 Processando vídeo: {v['titulo'][:50]}...")
                if self._processar_e_publicar(v):
                    total_processados += 1
                
        print(f"\n✅ Fluxo YouTube concluído! Total de artigos publicados/salvos: {total_processados}")

    def executar_fluxo_tendencias(self, max_noticias=3):
        print("\n" + "="*60)
        print("🔥 INICIANDO FLUXO: TENDÊNCIAS EM ALTA & PESQUISA CRISTÃ")
        print("="*60)
        
        noticias = self.buscador_tend.obter_tendencias_recentes(max_por_fonte=max_noticias)
        pesquisas_cristas = self.buscador_tend.obter_pesquisas_cristas_autonomas(max_itens=max_noticias)
        
        itens_para_processar = noticias + pesquisas_cristas
        if not itens_para_processar:
            print("📭 Nenhuma tendência ou pesquisa cristã inédita encontrada no momento.")
            return
            
        total_processados = 0
        for n in itens_para_processar:
            print(f"\n📰 Processando matéria: {n['titulo_original'][:50]}...")
            if self._processar_e_publicar(n):
                total_processados += 1
            
        print(f"\n✅ Fluxo concluído! Total de artigos publicados/salvos: {total_processados}")

    def _processar_e_publicar(self, item):
        try:
            # 1. Gera texto e título com IA
            titulo, conteudo_html, tags = self.gerador_art.gerar_artigo(item)
            
            # 2. Obtém/Baixa imagem de destaque
            caminho_img = self.gerador_img.obter_imagem_destaque(item)
            
            # 3. Envia imagem para o WordPress
            media_id = None
            if caminho_img and os.path.exists(caminho_img):
                media_id = self.publicador.enviar_imagem(caminho_img, titulo)
                
            # 4. Publica ou salva como Rascunho
            cat_id = item.get("categoria_id", 1)
            post = self.publicador.publicar_post(
                titulo=titulo,
                conteudo_html=conteudo_html,
                categoria_ids=[cat_id],
                media_id=media_id,
                status=self.status_publicacao,
                tags=tags
            )
            return post is not None
        except Exception as e:
            print(f"❌ Erro ao processar item '{item.get('titulo', item.get('titulo_original', ''))}': {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Robô Autônomo Rios News Bot - AI & YouTube")
    parser.add_argument("--modo", choices=["youtube", "tendencias", "ambos"], default="ambos", help="Qual fluxo executar")
    parser.add_argument("--teste-rascunho", action="store_true", help="Força a publicação como Rascunho (draft) no WordPress")
    parser.add_argument("--max", type=int, default=2, help="Número máximo de itens por canal ou fonte")
    
    args = parser.parse_args()
    
    robo = RoboRios(teste_rascunho=args.teste_rascunho)
    
    if args.modo in ["youtube", "ambos"]:
        robo.executar_fluxo_youtube(max_por_canal=args.max)
    if args.modo in ["tendencias", "ambos"]:
        robo.executar_fluxo_tendencias(max_noticias=args.max)

if __name__ == "__main__":
    main()
