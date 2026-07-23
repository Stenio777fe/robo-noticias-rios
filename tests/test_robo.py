import json
from pathlib import Path
from unittest.mock import Mock

from configuracao import carregar_config
from gerador_artigos import GeradorArtigos
from gerador_imagens import GeradorImagens
from publicador_wp import PublicadorWordPress


def config_minima(tmp_path: Path):
    caminho = tmp_path / "config.json"
    caminho.write_text(json.dumps({
        "wordpress": {"url_api": "https://example.com/wp-json/wp/v2", "status_padrao": "draft"},
        "inteligencia_artificial": {"provedor": "gemini"},
    }), encoding="utf-8")
    return caminho


def test_config_aceita_variavel_de_ambiente(tmp_path, monkeypatch):
    caminho = config_minima(tmp_path)
    monkeypatch.setenv("WORDPRESS_USUARIO", "usuario-teste")
    assert carregar_config(caminho)["wordpress"]["usuario"] == "usuario-teste"


def test_config_rejeita_status_invalido(tmp_path, monkeypatch):
    caminho = config_minima(tmp_path)
    monkeypatch.setenv("WORDPRESS_STATUS", "qualquer")
    try:
        carregar_config(caminho)
        assert False, "deveria rejeitar status"
    except ValueError:
        pass


def test_saida_ia_remove_script_e_limita_tags():
    gerador = GeradorArtigos.__new__(GeradorArtigos)
    resposta = "TITULO: Título seguro\nCONTEUDO:\n<p>" + ("texto " * 40) + "</p><script>alert(1)</script>\nTAGS_SEO: a,b,c,d,e,f"
    titulo, html, tags = gerador._processar_saida_ia(resposta, "fallback")
    assert titulo == "Título seguro"
    assert "<script" not in html
    assert len(tags) == 5


def test_valida_imagem_real():
    from io import BytesIO
    from PIL import Image
    buffer = BytesIO()
    Image.new("RGB", (10, 10)).save(buffer, "JPEG")
    assert GeradorImagens._imagem_valida(buffer.getvalue())
    assert not GeradorImagens._imagem_valida(b"not-an-image")


def test_publicacao_sem_credencial_nao_faz_requisicao(tmp_path):
    publicador = PublicadorWordPress(config_minima(tmp_path))
    publicador.session.post = Mock()
    assert publicador.publicar_post("Título", "<p>Conteúdo</p>", [1]) is None
    publicador.session.post.assert_not_called()