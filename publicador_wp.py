import mimetypes
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from configuracao import carregar_config, valor_configurado

class PublicadorWordPress:
    def __init__(self, config_path="config.json"):
        self.config = carregar_config(config_path)
        self.wp_config = self.config.get("wordpress", {})
        self.api_url = self.wp_config.get("url_api", "").rstrip("/")
        self.usuario = self.wp_config.get("usuario", "").strip()
        self.senha = self.wp_config.get("senha_aplicativo", "").strip()
        if not self.api_url.startswith(("http://", "https://")):
            raise ValueError("URL da API WordPress inválida.")
        self.session = requests.Session()
        retry = Retry(total=3, connect=3, read=3, backoff_factor=1,
                      status_forcelist=(429, 500, 502, 503, 504),
                      allowed_methods=frozenset({"GET", "HEAD"}))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))

    def _auth(self):
        if not valor_configurado(self.usuario) or not valor_configurado(self.senha):
            return None
        return self.usuario, self.senha

    def _obter_headers_auth(self):
        """Mantido por compatibilidade com reparar_imagens.py."""
        if not self._auth():
            return {}
        from requests.auth import _basic_auth_str
        return {"Authorization": _basic_auth_str(self.usuario, self.senha)}

    @staticmethod
    def _erro_resposta(resposta):
        try:
            dados = resposta.json()
            return str(dados.get("message", dados))[:500]
        except Exception:
            return resposta.text[:500]

    def verificar_post_existente(self, termo_busca):
        termo = str(termo_busca or "").strip()
        if not termo:
            return False
        try:
            resposta = self.session.get(
                f"{self.api_url}/posts",
                auth=self._auth(),
                params={"search": termo, "status": "publish,draft,future,pending,private", "per_page": 10},
                timeout=(10, 20),
            )
            resposta.raise_for_status()
            termo_low = termo.casefold()
            for post in resposta.json():
                titulo = post.get("title", {}).get("rendered", "").casefold()
                conteudo = post.get("content", {}).get("rendered", "").casefold()
                if termo_low in titulo or termo_low in conteudo:
                    return True
        except requests.RequestException as exc:
            print(f"⚠️ Não foi possível verificar duplicidade: {exc}")
        return False

    def enviar_imagem(self, caminho_arquivo_local, titulo_imagem="Imagem de destaque"):
        if not self._auth():
            print("❌ Credenciais WordPress não configuradas.")
            return None
        if not os.path.isfile(caminho_arquivo_local):
            print(f"❌ Imagem não encontrada: {caminho_arquivo_local}")
            return None
        nome = os.path.basename(caminho_arquivo_local)
        tipo = mimetypes.guess_type(nome)[0] or "application/octet-stream"
        if not tipo.startswith("image/"):
            print(f"❌ Arquivo recusado porque não é imagem: {nome}")
            return None
        headers = {"Content-Disposition": f'attachment; filename="{nome}"', "Content-Type": tipo}
        try:
            with open(caminho_arquivo_local, "rb") as imagem:
                resposta = self.session.post(f"{self.api_url}/media", auth=self._auth(),
                                             headers=headers, data=imagem, timeout=(10, 90))
            if resposta.status_code not in (200, 201):
                print(f"❌ Upload recusado ({resposta.status_code}): {self._erro_resposta(resposta)}")
                return None
            media = resposta.json()
            print(f"✅ Imagem enviada. ID: {media.get('id')}")
            return media.get("id")
        except requests.RequestException as exc:
            print(f"❌ Falha de rede no upload: {exc}")
            return None

    def _converter_tags_para_ids(self, tags_list):
        if not tags_list or not self._auth():
            return []
        ids = []
        url = f"{self.api_url}/tags"
        for tag in tags_list[:5]:
            if isinstance(tag, int):
                ids.append(tag)
                continue
            nome = str(tag).strip()[:100]
            if not nome:
                continue
            try:
                resposta = self.session.get(url, auth=self._auth(), params={"search": nome, "per_page": 20}, timeout=(10, 20))
                if resposta.ok:
                    exata = next((t for t in resposta.json() if t.get("name", "").casefold() == nome.casefold()), None)
                    if exata:
                        ids.append(exata["id"])
                        continue
                criada = self.session.post(url, auth=self._auth(), json={"name": nome}, timeout=(10, 20))
                if criada.status_code in (200, 201):
                    ids.append(criada.json()["id"])
                elif criada.status_code == 400:
                    existente = criada.json().get("data", {}).get("term_id")
                    if existente:
                        ids.append(existente)
            except (requests.RequestException, ValueError, KeyError) as exc:
                print(f"⚠️ Tag '{nome}' não processada: {exc}")
        return ids

    def publicar_post(self, titulo, conteudo_html, categoria_ids, media_id=None, status="draft", tags=None):
        if not self._auth():
            print("❌ Credenciais WordPress não configuradas.")
            return None
        if status not in {"draft", "publish", "future", "pending", "private"}:
            raise ValueError(f"Status inválido: {status}")
        categorias = categoria_ids if isinstance(categoria_ids, list) else [categoria_ids or 1]
        payload = {"title": titulo, "content": conteudo_html, "status": status,
                   "categories": categorias, "author": self.wp_config.get("autor_id", 1)}
        if media_id:
            payload["featured_media"] = media_id
        tag_ids = self._converter_tags_para_ids(tags)
        if tag_ids:
            payload["tags"] = tag_ids
        try:
            resposta = self.session.post(f"{self.api_url}/posts", auth=self._auth(), json=payload, timeout=(10, 45))
            if resposta.status_code not in (200, 201):
                print(f"❌ Publicação recusada ({resposta.status_code}): {self._erro_resposta(resposta)}")
                return None
            post = resposta.json()
            print(f"✅ Post criado. ID: {post.get('id')} | Status: {status.upper()}")
            print(f"🔗 {post.get('link', '')}")
            return post
        except requests.RequestException as exc:
            print(f"❌ Falha de rede ao publicar: {exc}")
            return None