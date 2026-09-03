import argparse
import sys
import os
import html
from urllib.parse import urlparse
from datetime import datetime, timezone

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
from configuracao import carregar_config

class RoboRios:
    def __init__(self, config_path="config.json", teste_rascunho=False):
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_path)
        self.config = carregar_config(self.config_path)

        regras = self.config.get("publicacao", {})
        self.limite_total = max(1, int(regras.get("max_posts_por_ciclo", 1)))
        self.total_ciclo = 0
        self.sequencia_origens = regras.get("sequencia_origens", ["tendencias", "youtube"])

        self.teste_rascunho = teste_rascunho
        # Fluxos automáticos sempre criam rascunhos. A publicação ao vivo fica
        # reservada ao fluxo manual, depois da conferência editorial no WordPress.
        self.status_publicacao = "draft"

        self.buscador_yt = BuscadorYouTube(self.config_path)
        self.buscador_tend = BuscadorTendencias(self.config_path)
        self.gerador_art = GeradorArtigos(self.config_path)
        self.gerador_img = GeradorImagens()
        self.publicador = PublicadorWordPress(self.config_path)

    def tem_vaga_no_ciclo(self):
        return self.total_ciclo < self.limite_total

    def origem_do_ciclo(self):
        intervalo = max(1, int(self.config.get("agendamento", {}).get("intervalo_horas", 6)))
        indice = int(datetime.now(timezone.utc).timestamp() // (intervalo * 3600))
        return self.sequencia_origens[indice % len(self.sequencia_origens)]

    def executar_fluxo_youtube(self, max_por_canal=2):
        print("\n" + "="*60)
        print("📺 INICIANDO FLUXO: VÍDEOS DO YOUTUBE PARA ARTIGOS")
        print("="*60)

        canais = self.config.get("canais_youtube", [])
        total_processados = 0

        for canal in canais:
            if not self.tem_vaga_no_ciclo():
                break
            videos = self.buscador_yt.obter_videos_recentes(canal, max_videos=max_por_canal)
            if not videos:
                continue

            for v in videos:
                if not self.tem_vaga_no_ciclo():
                    break
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
            if not self.tem_vaga_no_ciclo():
                break
            print(f"\n📰 Processando matéria: {n['titulo_original'][:50]}...")
            if self._processar_e_publicar(n):
                total_processados += 1

        print(f"\n✅ Fluxo concluído! Total de artigos publicados/salvos: {total_processados}")

    def _processar_e_publicar(self, item):
        try:
            # 1. Gera texto e título com IA
            titulo, conteudo_html, tags = self.gerador_art.gerar_artigo(item)

            conteudo_html += self._bloco_transparencia(item)

            origem_id = item.get("video_id") or item.get("link_original") or item.get("link")
            if origem_id:
                conteudo_html += f"\n<!-- rios-news-source:{origem_id} -->"

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
            if post is not None:
                self.total_ciclo += 1
                return True
            return False
        except Exception as e:
            print(f"❌ Erro ao processar item '{item.get('titulo', item.get('titulo_original', ''))}': {e}")
            return False

    @staticmethod
    def _bloco_transparencia(item):
        """Acrescenta origem visível e transparência editorial a cada matéria automática."""
        origem = item.get("origem")
        if origem == "manual":
            return (
                '\n<section class="rios-noticia-transparencia" aria-label="Transparência editorial">'
                '<h2>Sobre esta publicação</h2>'
                '<p>Conteúdo autoral preparado para o Rios Notícias e revisado antes da publicação.</p>'
                '</section>'
            )

        url = str(item.get("link_original") or item.get("link") or "").strip()
        if not url and item.get("video_id"):
            url = f"https://www.youtube.com/watch?v={item['video_id']}"
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Não foi possível identificar uma fonte pública válida.")

        fonte = html.escape(str(item.get("fonte_nome") or "Conteúdo original consultado"))
        url_segura = html.escape(url, quote=True)
        return (
            '\n<section class="rios-noticia-transparencia" aria-label="Fontes e transparência editorial">'
            '<h2>Fonte e transparência</h2>'
            f'<p>Fonte consultada: <a href="{url_segura}" target="_blank" rel="noopener noreferrer nofollow">{fonte}</a>.</p>'
            '<p>O texto foi organizado com apoio de tecnologia e passa por revisão editorial do Rios Notícias. '
            'Informações podem ser atualizadas conforme novos dados se tornem públicos.</p>'
            '</section>'
        )
    def executar_fluxo_manual(self, tema, texto="", caminho_img=None, categoria_id=8):
        print("\n============================================================")
        print("✍️ INICIANDO FLUXO MANUAL DE REDAÇÃO E PUBLICAÇÃO")
        print("============================================================")
        print(f"📌 Tema/Título Base: {tema}")
        print(f"📌 Categoria Destino: ID {categoria_id}")
        if caminho_img:
            print(f"📌 Imagem Fornecida: {caminho_img}")

        item_manual = {
            "titulo_original": tema,
            "texto_usuario": texto if texto else tema,
            "origem": "manual",
            "categoria_id": categoria_id,
            "caminho_imagem": caminho_img
        }

        if self._processar_e_publicar(item_manual):
            print("\n🎉 Matéria manual gerada, ilustrada e publicada com sucesso!")
            return True
        else:
            print("\n❌ Falha ao processar ou publicar matéria manual.")
            return False

def main():
    parser = argparse.ArgumentParser(description="Robô Autônomo Rios News Bot - AI & YouTube & Manual")
    parser.add_argument("--modo", choices=["youtube", "tendencias", "ambos", "manual"], default="ambos", help="Qual fluxo executar")
    parser.add_argument("--teste-rascunho", action="store_true", help="Força a publicação como Rascunho (draft) no WordPress")
    parser.add_argument("--max", type=int, default=2, help="Número máximo de itens por canal ou fonte")

    # Parâmetros para modo manual
    parser.add_argument("--tema", type=str, help="Tema ou título base para matéria manual")
    parser.add_argument("--texto", type=str, default="", help="Texto base, reflexão ou anotações para a matéria manual")
    parser.add_argument("--img", type=str, default=None, help="Caminho local da imagem de capa (se omitido, gera IA HD automaticamente)")
    parser.add_argument("--cat", type=int, default=8, help="ID da Categoria no WordPress (Padrão: 8 = Mensagens)")

    args = parser.parse_args()

    robo = RoboRios(teste_rascunho=args.teste_rascunho)

    if args.modo == "manual":
        if not args.tema:
            print("❌ Para o modo manual, você precisa fornecer pelo menos o --tema \"Seu Título\"")
            return
        robo.executar_fluxo_manual(tema=args.tema, texto=args.texto, caminho_img=args.img, categoria_id=args.cat)
        return

    if args.modo == "ambos":
        preferida = robo.origem_do_ciclo()
        print(f"📅 Sequência editorial deste ciclo: {preferida}")
        if preferida == "youtube":
            robo.executar_fluxo_youtube(max_por_canal=args.max)
            robo.executar_fluxo_tendencias(max_noticias=args.max)
        else:
            robo.executar_fluxo_tendencias(max_noticias=args.max)
            robo.executar_fluxo_youtube(max_por_canal=args.max)
    elif args.modo == "youtube":
        robo.executar_fluxo_youtube(max_por_canal=args.max)
    elif args.modo == "tendencias":
        robo.executar_fluxo_tendencias(max_noticias=args.max)

if __name__ == "__main__":
    main()
