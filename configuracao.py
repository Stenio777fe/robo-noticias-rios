"""Carregamento centralizado e seguro das configurações do robô."""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path

PASTA_PROJETO = Path(__file__).resolve().parent

def _mesclar(base: dict, sobrescrita: dict) -> dict:
    resultado = copy.deepcopy(base)
    for chave, valor in sobrescrita.items():
        if isinstance(valor, dict) and isinstance(resultado.get(chave), dict):
            resultado[chave] = _mesclar(resultado[chave], valor)
        else:
            resultado[chave] = valor
    return resultado

def carregar_config(config_path="config.json") -> dict:
    caminho = Path(config_path)
    if not caminho.is_absolute():
        caminho = PASTA_PROJETO / caminho
    if not caminho.exists():
        raise FileNotFoundError(f"Configuração não encontrada: {caminho}")
    with caminho.open("r", encoding="utf-8") as arquivo:
        config = json.load(arquivo)
    local = caminho.with_name("config.local.json")
    if local.exists() and local != caminho:
        with local.open("r", encoding="utf-8") as arquivo:
            config = _mesclar(config, json.load(arquivo))
    wp = config.setdefault("wordpress", {})
    ia = config.setdefault("inteligencia_artificial", {})
    variaveis = {
        "WORDPRESS_API_URL": (wp, "url_api"),
        "WORDPRESS_USUARIO": (wp, "usuario"),
        "WORDPRESS_APP_PASSWORD": (wp, "senha_aplicativo"),
        "WORDPRESS_STATUS": (wp, "status_padrao"),
        "GEMINI_API_KEY": (ia, "api_key_gemini"),
        "OPENAI_API_KEY": (ia, "api_key_openai"),
        "IA_PROVEDOR": (ia, "provedor"),
        "GEMINI_MODEL": (ia, "modelo_gemini"),
        "OPENAI_MODEL": (ia, "modelo_openai"),
    }
    for nome, (secao, chave) in variaveis.items():
        if os.environ.get(nome):
            secao[chave] = os.environ[nome]
    status = str(wp.get("status_padrao", "draft")).lower()
    if status not in {"draft", "publish", "future", "pending", "private"}:
        raise ValueError(f"Status WordPress inválido: {status}")
    wp["status_padrao"] = status
    return config

def valor_configurado(valor: str) -> bool:
    return bool(valor and "COLE_SUA_CHAVE" not in valor and "xxxx xxxx" not in valor)