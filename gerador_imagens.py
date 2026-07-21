import sys
import os
import requests

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

class GeradorImagens:
    def __init__(self, pasta_temp="temp_imagens"):
        self.pasta_temp = os.path.join(os.path.dirname(os.path.abspath(__file__)), pasta_temp)
        os.makedirs(self.pasta_temp, exist_ok=True)
        
    def obter_imagem_destaque(self, dados_item):
        """
        Baixa a imagem ideal (thumbnail do YouTube em HD ou imagem royalty-free do Unsplash) e salva localmente.
        Retorna o caminho local do arquivo baixado.
        """
        origem = dados_item.get("origem")
        
        if origem == "youtube":
            return self._baixar_thumbnail_youtube(dados_item)
        else:
            return self._obter_imagem_unsplash(dados_item)

    def _baixar_thumbnail_youtube(self, item):
        video_id = item.get("video_id", "")
        titulo = item.get("titulo", "video")
        
        # Tenta maxresdefault primeiro (1280x720 ou mais), se falhar tenta hqdefault (480x360)
        urls_para_tentar = [
            f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
            f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        ]
        
        nome_arquivo = f"yt_{video_id}.jpg"
        caminho_local = os.path.join(self.pasta_temp, nome_arquivo)
        
        for url in urls_para_tentar:
            try:
                print(f"🖼️ Baixando capa do vídeo: {url}...")
                resp = requests.get(url, timeout=15)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    with open(caminho_local, "wb") as f:
                        f.write(resp.content)
                    print(f"✅ Capa do vídeo salva: {caminho_local}")
                    return caminho_local
            except Exception as e:
                print(f"⚠️ Erro ao tentar baixar {url}: {e}")
                
        print("❌ Não foi possível baixar nenhuma capa para o vídeo.")
        return None

    def _obter_imagem_unsplash(self, item):
        """
        Busca uma imagem livre de direitos autorais em alta definição no Unsplash.
        """
        titulo = item.get("titulo_original", item.get("titulo", ""))
        # Pega as primeiras 3 ou 4 palavras-chave do título para busca
        palavras = [p for p in titulo.split() if len(p) > 3][:3]
        termo_busca = " ".join(palavras) if palavras else "news"
        
        url_busca = f"https://source.unsplash.com/1280x720/?{termo_busca}"
        nome_arquivo = f"noticia_{abs(hash(termo_busca))}.jpg"
        caminho_local = os.path.join(self.pasta_temp, nome_arquivo)
        
        try:
            print(f"🖼️ Buscando imagem de alta definição no Unsplash para: '{termo_busca}'...")
            headers = {"User-Agent": "Mozilla/5.0"}
            # Para redirecionamento do Unsplash Source e baixa a imagem final
            resp = requests.get(url_busca, headers=headers, timeout=20, allow_redirects=True)
            if resp.status_code == 200 and len(resp.content) > 2000:
                with open(caminho_local, "wb") as f:
                    f.write(resp.content)
                print(f"✅ Imagem de notícia salva: {caminho_local}")
                return caminho_local
        except Exception as e:
            print(f"⚠️ Erro ao buscar imagem no Unsplash ({e}). Tentando imagem neutra de notícias...")
            
        # Fallback para imagem neutra de jornalismo/notícia
        try:
            url_fallback = "https://source.unsplash.com/1280x720/?journalism,news,media"
            resp = requests.get(url_fallback, timeout=20, allow_redirects=True)
            if resp.status_code == 200:
                with open(caminho_local, "wb") as f:
                    f.write(resp.content)
                return caminho_local
        except Exception:
            pass
            
        return None
