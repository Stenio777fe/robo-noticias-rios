import sys
import re
import requests
import feedparser
from bs4 import BeautifulSoup
from publicador_wp import PublicadorWordPress

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

class BuscadorYouTube:
    def __init__(self, config_path="config.json"):
        self.publicador = PublicadorWordPress(config_path)
        self.config = self.publicador.config
        
    def _resolver_channel_id(self, url_ou_id):
        """
        Resolve uma URL (@handle, /c/, /channel/) ou ID de canal para o formato UC... (Channel ID)
        """
        url_ou_id = url_ou_id.strip()
        if url_ou_id.startswith("UC") and len(url_ou_id) == 24:
            return url_ou_id
            
        # Se for uma URL completa
        if "youtube.com" not in url_ou_id and "youtu.be" not in url_ou_id:
            url_ou_id = f"https://www.youtube.com/{url_ou_id}"
            
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(url_ou_id, headers=headers, timeout=10)
            if resp.status_code == 200:
                # Busca <meta itemprop="channelId" content="UC..."> ou "externalId":"UC..."
                match = re.search(r'itemprop="channelId"\s+content="(UC[^"]+)"', resp.text)
                if match:
                    return match.group(1)
                match2 = re.search(r'"externalId":"(UC[^"]+)"', resp.text)
                if match2:
                    return match2.group(1)
                # Tenta RSS alternativo no HTML
                soup = BeautifulSoup(resp.text, "html.parser")
                rss_link = soup.find("link", rel="alternate", type="application/rss+xml")
                if rss_link and "channel_id=" in rss_link.get("href", ""):
                    return rss_link["href"].split("channel_id=")[-1]
        except Exception as e:
            print(f"⚠️ Erro ao resolver ID do canal {url_ou_id}: {e}")
            
        return None

    def obter_videos_recentes(self, canal_info, max_videos=3):
        """
        Lê o feed RSS do canal do YouTube e retorna a lista de vídeos mais recentes.
        """
        canal_url = canal_info.get("channel_id_ou_url", "")
        if not canal_url or "SeuCanalOuParceiro" in canal_url:
            return []
            
        channel_id = self._resolver_channel_id(canal_url)
        if not channel_id:
            print(f"❌ Não foi possível identificar o Channel ID para: {canal_url}")
            return []
            
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        print(f"📡 Lendo feed RSS do canal: {canal_info.get('nome', channel_id)} ({rss_url})...")
        
        feed = feedparser.parse(rss_url)
        videos_encontrados = []
        
        for entry in feed.entries[:max_videos]:
            video_id = entry.get("yt_videoid", "")
            if not video_id and "v=" in entry.get("link", ""):
                video_id = entry["link"].split("v=")[-1].split("&")[0]
                
            titulo = entry.get("title", "")
            link = entry.get("link", f"https://www.youtube.com/watch?v={video_id}")
            data_pub = entry.get("published", "")
            
            # Verifica se já postamos esse vídeo no site para não repetir!
            if self.publicador.verificar_post_existente(video_id) or self.publicador.verificar_post_existente(titulo[:35]):
                print(f"⏭️ Vídeo já publicado anteriormente: '{titulo[:40]}...' (Ignorando)")
                continue
                
            # Obtém thumbnail em alta qualidade
            thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
            
            # Obtém transcrição / legendas com youtube-transcript-api
            transcrição = self._obter_transcricao(video_id)
            
            videos_encontrados.append({
                "video_id": video_id,
                "titulo": titulo,
                "link": link,
                "data_publicacao": data_pub,
                "thumbnail_url": thumbnail_url,
                "transcricao": transcrição,
                "categoria_id": canal_info.get("categoria_padrao_id", 4), # 4 = Mundo Cristão
                "origem": "youtube"
            })
            
        return videos_encontrados

    def _obter_transcricao(self, video_id):
        """
        Tenta extrair a transcrição completa do vídeo em português ou inglês.
        """
        if not YouTubeTranscriptApi:
            print("⚠️ youtube_transcript_api não instalado.")
            return ""
            
        try:
            print(f"🗣️ Extraindo fala/legenda do vídeo {video_id}...")
            api = YouTubeTranscriptApi()
            try:
                transcricao = api.fetch(video_id, languages=["pt", "pt-BR", "en", "es"])
            except Exception:
                lista = api.list(video_id)
                transcricao = lista.find_transcript(["pt", "pt-BR", "en", "es"]).fetch()
            trechos = []
            for item in transcricao:
                texto = item.text if hasattr(item, "text") else item.get("text", "")
                if texto:
                    trechos.append(texto)
            texto_completo = " ".join(trechos)
            print(f"✅ Transcrição obtida com sucesso ({len(texto_completo)} caracteres).")
            return texto_completo
        except Exception as e:
            print(f"ℹ️ Vídeo sem legenda automática disponível ou erro ao extrair ({e}). Usando dados do feed.")
            return ""
