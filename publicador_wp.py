import requests
import json
import os
import sys
import base64

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

class PublicadorWordPress:
    def __init__(self, config_path="config.json"):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Arquivo de configuração '{config_path}' não encontrado.")
            
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
            
        self.wp_config = self.config.get("wordpress", {})
        self.api_url = self.wp_config.get("url_api", "https://noticias.riosministerio.com/wp-json/wp/v2").rstrip("/")
        self.usuario = self.wp_config.get("usuario", "")
        self.senha = self.wp_config.get("senha_aplicativo", "").strip()
        
    def _obter_headers_auth(self):
        if not self.usuario or not self.senha or self.senha == "xxxx xxxx xxxx xxxx":
            print("⚠️ AVISO: Senha de Aplicativo ou Usuário do WordPress não configurados no config.json.")
            return {}
        credenciais = f"{self.usuario}:{self.senha}"
        token = base64.b64encode(credenciais.encode()).decode("utf-8")
        return {"Authorization": f"Basic {token}"}

    def verificar_post_existente(self, termo_busca):
        """
        Verifica no WordPress via REST API se já existe algum post publicado ou em rascunho com o termo/URL/título.
        """
        headers = self._obter_headers_auth()
        url = f"{self.api_url}/posts"
        params = {
            "search": termo_busca,
            "status": "publish,draft,future",
            "per_page": 5
        }
        try:
            resposta = requests.get(url, headers=headers, params=params, timeout=15)
            if resposta.status_code == 200:
                posts = resposta.json()
                for p in posts:
                    # Verifica se o termo está no título ou no conteúdo
                    titulo = p.get("title", {}).get("rendered", "").lower()
                    conteudo = p.get("content", {}).get("rendered", "").lower()
                    termo_low = termo_busca.lower()
                    if termo_low in titulo or termo_low in conteudo:
                        return True
            return False
        except Exception as e:
            print(f"⚠️ Erro ao verificar post existente: {e}")
            return False

    def enviar_imagem(self, caminho_arquivo_local, titulo_imagem="Imagem Destaque"):
        """
        Envia uma imagem para a Biblioteca de Mídia do WordPress (`/wp-json/wp/v2/media`) e retorna o ID da imagem.
        """
        if not os.path.exists(caminho_arquivo_local):
            print(f"❌ Arquivo de imagem não encontrado: {caminho_arquivo_local}")
            return None
            
        headers = self._obter_headers_auth()
        if not headers:
            print("❌ Autenticação necessária para envio de imagem.")
            return None
            
        nome_arquivo = os.path.basename(caminho_arquivo_local)
        ext = os.path.splitext(nome_arquivo)[1].lower()
        content_type = "image/png" if ext == ".png" else "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/webp"
        
        headers["Content-Disposition"] = f'attachment; filename="{nome_arquivo}"'
        headers["Content-Type"] = content_type
        
        url = f"{self.api_url}/media"
        try:
            with open(caminho_arquivo_local, "rb") as img_file:
                resposta = requests.post(url, headers=headers, data=img_file, timeout=60)
                
            if resposta.status_code in [200, 201]:
                dados_media = resposta.json()
                media_id = dados_media.get("id")
                url_media = dados_media.get("source_url")
                print(f"✅ Imagem enviada com sucesso! ID: {media_id} ({url_media})")
                return media_id
            else:
                print(f"❌ Erro ao enviar imagem ao WordPress ({resposta.status_code}): {resposta.text}")
                return None
        except Exception as e:
            print(f"❌ Exceção ao enviar imagem: {e}")
            return None

    def _converter_tags_para_ids(self, tags_list):
        if not tags_list or not isinstance(tags_list, list):
            return []
        headers = self._obter_headers_auth()
        headers["Content-Type"] = "application/json"
        tag_ids = []
        url_tags = f"{self.api_url}/tags"
        for t in tags_list[:5]: # limita a 5 tags para ser super rápido
            if isinstance(t, int):
                tag_ids.append(t)
                continue
            nome = str(t).strip()
            if not nome:
                continue
            try:
                # Busca tag existente
                resp = requests.get(url_tags, headers=headers, params={"search": nome}, timeout=10)
                if resp.status_code == 200:
                    encontradas = resp.json()
                    id_achado = None
                    for en in encontradas:
                        if en.get("name", "").lower() == nome.lower():
                            id_achado = en.get("id")
                            break
                    if not id_achado and encontradas:
                        id_achado = encontradas[0].get("id")
                    if id_achado:
                        tag_ids.append(id_achado)
                        continue
                # Se não encontrou, cria a tag no WordPress
                resp_c = requests.post(url_tags, headers=headers, json={"name": nome}, timeout=10)
                if resp_c.status_code in [200, 201]:
                    tag_ids.append(resp_c.json().get("id"))
            except Exception as e:
                print(f"⚠️ Erro ao converter tag '{nome}': {e}")
        return tag_ids

    def publicar_post(self, titulo, conteudo_html, categoria_ids, media_id=None, status="draft", tags=None):
        """
        Cria e publica/salva o post no WordPress.
        """
        headers = self._obter_headers_auth()
        headers["Content-Type"] = "application/json"
        
        if not headers.get("Authorization"):
            print("❌ Impossível publicar sem credenciais válidas.")
            return None
            
        if not isinstance(categoria_ids, list):
            categoria_ids = [categoria_ids] if categoria_ids else [1] # 1 = Uncategorized
            
        url = f"{self.api_url}/posts"
        payload = {
            "title": titulo,
            "content": conteudo_html,
            "status": status,
            "categories": categoria_ids,
            "author": self.wp_config.get("autor_id", 1)
        }
        
        if media_id:
            payload["featured_media"] = media_id
        if tags:
            tag_ids = self._converter_tags_para_ids(tags)
            if tag_ids:
                payload["tags"] = tag_ids
            
        try:
            resposta = requests.post(url, headers=headers, json=payload, timeout=30)
            if resposta.status_code in [200, 201]:
                dados_post = resposta.json()
                post_id = dados_post.get("id")
                link_post = dados_post.get("link")
                print(f"🚀 Post criado com sucesso! ID: {post_id} | Status: {status.upper()}")
                print(f"🔗 Link do Post: {link_post}")
                return dados_post
            else:
                print(f"❌ Erro ao criar post no WordPress ({resposta.status_code}): {resposta.text}")
                return None
        except Exception as e:
            print(f"❌ Exceção ao publicar post: {e}")
            return None
