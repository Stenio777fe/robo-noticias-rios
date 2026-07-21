import sys
import json
import os
import re
import requests

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

class GeradorArtigos:
    def __init__(self, config_path="config.json"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        self.ia_config = self.config.get("inteligencia_artificial", {})
        self.provedor = self.ia_config.get("provedor", "gemini").lower()
        self.api_key_gemini = self.ia_config.get("api_key_gemini", "")
        self.api_key_openai = self.ia_config.get("api_key_openai", "")
        self.modelo_gemini = self.ia_config.get("modelo_gemini", "gemini-2.5-flash")
        self.modelo_openai = self.ia_config.get("modelo_openai", "gpt-4o-mini")

    def _chamar_gemini(self, prompt):
        """
        Chama a API do Google Gemini via REST (100% confiável sem conflito de bibliotecas).
        """
        if not self.api_key_gemini or "COLE_SUA_CHAVE" in self.api_key_gemini:
            raise ValueError("Chave de API do Gemini não configurada em config.json.")
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.modelo_gemini}:generateContent?key={self.api_key_gemini}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95
            }
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=90)
        if resp.status_code == 200:
            dados = resp.json()
            try:
                return dados["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as e:
                raise ValueError(f"Resposta inesperada do Gemini: {dados}")
        else:
            raise RuntimeError(f"Erro na API do Gemini ({resp.status_code}): {resp.text}")

    def _chamar_openai(self, prompt):
        """
        Chama a API da OpenAI via REST.
        """
        if not self.api_key_openai or "COLE_SUA_CHAVE" in self.api_key_openai:
            raise ValueError("Chave de API da OpenAI não configurada em config.json.")
            
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key_openai}"
        }
        payload = {
            "model": self.modelo_openai,
            "messages": [
                {"role": "system", "content": "Você é o redator-chefe e jornalista sênior do portal de notícias cristão Rios Ministério."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=90)
        if resp.status_code == 200:
            dados = resp.json()
            return dados["choices"][0]["message"]["content"]
        else:
            raise RuntimeError(f"Erro na API da OpenAI ({resp.status_code}): {resp.text}")

    def _gerar_texto_ia(self, prompt):
        if self.provedor == "gemini":
            return self._chamar_gemini(prompt)
        elif self.provedor == "openai":
            return self._chamar_openai(prompt)
        else:
            raise ValueError(f"Provedor de IA desconhecido: {self.provedor}. Use 'gemini' ou 'openai'.")

    def gerar_artigo(self, dados_item):
        """
        Gera o título jornalístico e o conteúdo HTML do artigo baseado no item (vídeo do YouTube ou notícia em alta).
        Retorna: (titulo_otimizado, conteudo_html, tags_list)
        """
        origem = dados_item.get("origem")
        
        if origem == "youtube":
            return self._gerar_artigo_youtube(dados_item)
        else:
            return self._gerar_artigo_tendencia(dados_item)

    def _gerar_artigo_youtube(self, item):
        titulo_v = item.get("titulo", "")
        transcricao = item.get("transcricao", "")
        video_id = item.get("video_id", "")
        
        prompt = f"""
Você é o redator-chefe e jornalista sênior do portal de notícias cristão e conservador "noticias.riosministerio.com".
O seu papel é transformar vídeos relevantes do YouTube em artigos jornalísticos profundos, magnéticos e super ricos em conteúdo para os nossos leitores.

VÍDEO ORIGINAL:
Título: {titulo_v}
Transcrição/Resumo do que foi falado: {transcricao[:6000] if transcricao else 'Conteúdo baseado no título e tema do vídeo.'}

DIRETRIZES DE REDAÇÃO:
1. Crie um TÍTULO NOVO, chamativo, no estilo jornalístico impactante ("click-worthy" ético e magnético), sem parecer inteligência artificial.
2. Escreva um artigo completo de 550 a 900 palavras, com linguagem culta, envolvente, clara e alinhada aos valores cristãos, éticos e morais.
3. Divida o texto em subtítulos com tags `<h2>` e `<h3>`. Use parágrafos médios (`<p>`).
4. Inclua um bloco de citação relevante ou lição moral/espiritual/prática com a tag `<blockquote><p>...</p></blockquote>`.
5. IMPORTANTE: Logo após o segundo parágrafo ou o primeiro subtítulo `<h2>`, insira exatamente este código do player do vídeo do YouTube para que o leitor possa assistir diretamente no site:
<div class="video-container" style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;margin:25px 0;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.15);"><iframe src="https://www.youtube.com/embed/{video_id}" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" allowfullscreen></iframe></div>
6. Ao final, sugira 4 ou 5 tags de SEO separadas por vírgula no final da sua resposta, na última linha, no formato exato: TAGS_SEO: tag1, tag2, tag3, tag4.

FORMATO DE SAÍDA ESPERADO:
TITULO: [Seu título aqui]
CONTEUDO:
[Seu código HTML aqui contendo <h2>, <p>, <blockquote> e o player <iframe>]
TAGS_SEO: [tags separadas por vírgula]
"""
        print(f"🤖 Gerando artigo jornalístico com IA para o vídeo: {titulo_v[:40]}...")
        resposta = self._gerar_texto_ia(prompt)
        return self._processar_saida_ia(resposta, titulo_v)

    def _gerar_artigo_tendencia(self, item):
        titulo_orig = item.get("titulo_original", "")
        resumo = item.get("resumo", "")
        fonte = item.get("fonte_nome", "")
        
        prompt = f"""
Você é o redator-chefe e jornalista sênior do portal "noticias.riosministerio.com".
Sua missão é escrever uma matéria jornalística completa, original, aprofundada e magnética sobre o assunto que está em alta agora.

ASSUNTO EM ALTA:
Título/Tema: {titulo_orig}
Resumo ou Dados: {resumo}
Fonte de referência: {fonte}

DIRETRIZES DE REDAÇÃO:
1. Crie um TÍTULO original, marcante e jornalístico ("click-worthy" ético) que desperte forte curiosidade e valor no leitor.
2. Escreva uma matéria de 600 a 900 palavras, estruturada de forma impecável com subtítulos `<h2>` e `<h3>`, parágrafos bem divididos (`<p>`) e ao menos um bloco de destaque com `<blockquote><p>...</p></blockquote>`.
3. Mantenha um tom sério, confiável, analítico e, sempre que o tema permitir ou couber, traga uma reflexão edificante, ética ou alinhada à cosmovisão cristã e à família.
4. Ao final, sugira 4 ou 5 tags de SEO separadas por vírgula no formato exato: TAGS_SEO: tag1, tag2, tag3, tag4.

FORMATO DE SAÍDA ESPERADO:
TITULO: [Seu título aqui]
CONTEUDO:
[Seu código HTML aqui contendo <h2>, <p>, <blockquote>]
TAGS_SEO: [tags separadas por vírgula]
"""
        print(f"🤖 Gerando matéria jornalística com IA para a tendência: {titulo_orig[:40]}...")
        resposta = self._gerar_texto_ia(prompt)
        return self._processar_saida_ia(resposta, titulo_orig)

    def _processar_saida_ia(self, resposta_texto, titulo_fallback):
        titulo = titulo_fallback
        conteudo = resposta_texto
        tags = []
        
        # Extrai TÍTULO
        match_tit = re.search(r'TITULO:\s*(.+)', resposta_texto, re.IGNORECASE)
        if match_tit:
            titulo = match_tit.group(1).strip()
            
        # Extrai TAGS_SEO
        match_tags = re.search(r'TAGS_SEO:\s*(.+)', resposta_texto, re.IGNORECASE)
        if match_tags:
            tags_raw = match_tags.group(1).strip()
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
            
        # Extrai CONTEUDO HTML
        if "CONTEUDO:" in resposta_texto:
            partes = resposta_texto.split("CONTEUDO:")
            conteudo_bruto = partes[1]
            # Remove a linha TAGS_SEO do final
            if "TAGS_SEO:" in conteudo_bruto:
                conteudo_bruto = conteudo_bruto.split("TAGS_SEO:")[0]
            conteudo = conteudo_bruto.strip()
        elif match_tit:
            # Se não usou a palavra exata CONTEUDO, pega tudo depois do título
            pos = resposta_texto.find(match_tit.group(0)) + len(match_tit.group(0))
            conteudo = resposta_texto[pos:].strip()
            if "TAGS_SEO:" in conteudo:
                conteudo = conteudo.split("TAGS_SEO:")[0].strip()
                
        # Limpa eventuais marcações de markdown de código (```html ... ```)
        if conteudo.startswith("```html"):
            conteudo = conteudo[7:]
        elif conteudo.startswith("```"):
            conteudo = conteudo[3:]
        if conteudo.endswith("```"):
            conteudo = conteudo[:-3]
            
        return titulo.strip(), conteudo.strip(), tags
