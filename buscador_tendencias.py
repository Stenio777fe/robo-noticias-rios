import sys
import feedparser
from publicador_wp import PublicadorWordPress

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

class BuscadorTendencias:
    def __init__(self, config_path="config.json"):
        self.publicador = PublicadorWordPress(config_path)
        self.config = self.publicador.config
        
    def obter_tendencias_recentes(self, max_por_fonte=2):
        """
        Percorre as fontes RSS configuradas (Google Trends, G1, portais cristãos) e seleciona notícias inéditas em alta.
        """
        fontes = self.config.get("fontes_rss_tendencias", [])
        noticias_selecionadas = []
        
        for fonte in fontes:
            nome_fonte = fonte.get("nome", "Fonte RSS")
            url_rss = fonte.get("url", "")
            cat_id = fonte.get("categoria_padrao_id", 3) # 3 = Brasil
            
            if not url_rss:
                continue
                
            print(f"🔥 Buscando tendências em: {nome_fonte}...")
            try:
                feed = feedparser.parse(url_rss)
                count = 0
                for entry in feed.entries:
                    if count >= max_por_fonte:
                        break
                        
                    titulo = entry.get("title", "").strip()
                    link = entry.get("link", "")
                    resumo = entry.get("summary", entry.get("description", ""))
                    
                    if not titulo:
                        continue
                        
                    # Verifica no WordPress se já foi postada notícia com esse título
                    if self.publicador.verificar_post_existente(titulo[:35]):
                        print(f"⏭️ Notícia já postada no site: '{titulo[:40]}...' (Ignorando)")
                        continue
                        
                    noticias_selecionadas.append({
                        "titulo_original": titulo,
                        "link_original": link,
                        "resumo": resumo,
                        "categoria_id": cat_id,
                        "origem": "tendencia",
                        "fonte_nome": nome_fonte
                    })
                    count += 1
        return noticias_selecionadas

    def obter_pesquisas_cristas_autonomas(self, max_itens=3):
        """
        Gera temas profundos de pesquisa para Mundo Cristão (4), Curiosidades Bíblicas (7) e Bíblia (24).
        """
        temas = self.config.get("pesquisa_autonoma_crista", [])
        selecionados = []
        for count, t in enumerate(temas):
            if count >= max_itens:
                break
            titulo = t.get("tema_geral", "Estudo Bíblico e Vida Cristã")
            if self.publicador.verificar_post_existente(titulo[:30]):
                continue
            selecionados.append({
                "titulo_original": titulo,
                "link_original": "https://www.biblia.com.br",
                "resumo": f"Artigo especial completo de pesquisa bíblica, teológica e edificação cristã evangélica sobre: {titulo}",
                "categoria_id": t.get("categoria_id", 4),
                "origem": "tendencia",
                "fonte_nome": "Pesquisa Autônoma Cristã & Evangélica",
                "palavra_chave_img": t.get("palavra_chave_imagem", "bible prayer cross")
            })
        return selecionados
