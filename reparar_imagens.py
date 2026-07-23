import os
import requests
from publicador_wp import PublicadorWordPress
from gerador_imagens import GeradorImagens

def reparar_posts_sem_imagem():
    p = PublicadorWordPress()
    gi = GeradorImagens()
    
    headers = p._obter_headers_auth()
    headers_json = {**headers, "Content-Type": "application/json"}
    
    url = f"{p.api_url}/posts?per_page=15"
    resposta = requests.get(url, headers=headers)
    if resposta.status_code != 200:
        print("Erro ao buscar posts:", resposta.text)
        return
        
    posts = resposta.json()
    for pt in posts:
        post_id = pt["id"]
        media_id = pt["featured_media"]
        titulo = pt["title"]["rendered"]
        
        if media_id == 0:
            print(f"\n🔧 Reparando capa do Post {post_id}: '{titulo[:50]}...'")
            caminho_img = gi.obter_imagem_destaque({"titulo_original": titulo})
            if caminho_img and os.path.exists(caminho_img):
                mid = p.enviar_imagem(caminho_img, titulo)
                if mid:
                    resp_up = requests.post(f"{p.api_url}/posts/{post_id}", headers=headers_json, json={"featured_media": mid})
                    if resp_up.status_code in [200, 201]:
                        print(f"✅ Sucesso total! Post {post_id} agora tem a imagem de capa ID {mid}!")
                    else:
                        print(f"❌ Erro ao vincular media no post {post_id}: {resp_up.text}")

if __name__ == "__main__":
    reparar_posts_sem_imagem()
