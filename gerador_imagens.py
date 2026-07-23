import sys
import os
import requests
import urllib.parse
import hashlib
from io import BytesIO
from PIL import Image

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
        
        if origem == "manual" and dados_item.get("caminho_imagem"):
            caminho_custom = dados_item.get("caminho_imagem")
            if os.path.exists(caminho_custom):
                print(f"🖼️ Usando imagem manual local fornecida: {caminho_custom}")
                return caminho_custom
            else:
                print(f"⚠️ Imagem local '{caminho_custom}' não encontrada. Gerando imagem HD automática...")
                return self._obter_imagem_unsplash(dados_item)
        elif origem == "youtube":
            return self._baixar_thumbnail_youtube(dados_item)
        else:
            return self._obter_imagem_unsplash(dados_item)

    @staticmethod
    def _imagem_valida(conteudo):
        try:
            with Image.open(BytesIO(conteudo)) as imagem:
                imagem.verify()
            return True
        except Exception:
            return False
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
        Busca/Gera uma imagem livre de direitos autorais em alta definição (1280x720) baseada no tema.
        """
        titulo = item.get("titulo_original", item.get("titulo", ""))
        palavras = [p for p in titulo.split() if len(p) > 3][:4]
        termo_busca = " ".join(palavras) if palavras else "news journalism"
        termo_clean = urllib.parse.quote(termo_busca + " high quality photo realistic")
        
        identificador = hashlib.sha256(termo_busca.encode("utf-8")).hexdigest()[:16]
        nome_arquivo = f"noticia_{identificador}.jpg"
        caminho_local = os.path.join(self.pasta_temp, nome_arquivo)
        
        try:
            url_busca = f"https://image.pollinations.ai/prompt/{termo_clean}?width=1280&height=720&nologo=true"
            print(f"🖼️ Baixando imagem de alta definição para: '{termo_busca}'...")
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url_busca, headers=headers, timeout=25, allow_redirects=True)
            if resp.status_code == 200 and self._imagem_valida(resp.content):
                with open(caminho_local, "wb") as f:
                    f.write(resp.content)
                print(f"✅ Imagem salva: {caminho_local}")
                return caminho_local
        except Exception as e:
            print(f"⚠️ Erro ao obter imagem HD ({e}). Tentando imagem de fallback...")
            
        try:
            url_fallback = "https://picsum.photos/1280/720"
            resp = requests.get(url_fallback, timeout=20, allow_redirects=True)
            if resp.status_code == 200 and self._imagem_valida(resp.content):
                with open(caminho_local, "wb") as f:
                    f.write(resp.content)
                print(f"✅ Imagem salva (fallback): {caminho_local}")
                return caminho_local
        except Exception as ex_fb:
            print(f"❌ Falha em todos os provedores de imagem: {ex_fb}")
            
        return None
