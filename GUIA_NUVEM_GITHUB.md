# Rios News Bot no GitHub Actions

O robô executa a cada 6 horas e também pode ser iniciado manualmente pela aba **Actions**.

## 1. Repositório

Use um repositório privado e envie os arquivos do projeto. O `config.json` versionado não contém credenciais. O arquivo `config.local.json` é exclusivo desta máquina e está ignorado pelo Git — nunca o envie.

## 2. Credenciais seguras

No GitHub, abra **Settings → Secrets and variables → Actions** e crie estes *Repository secrets*:

- `WORDPRESS_API_URL`: URL terminada em `/wp-json/wp/v2`;
- `WORDPRESS_USUARIO`: usuário do WordPress;
- `WORDPRESS_APP_PASSWORD`: uma senha de aplicativo do WordPress, não a senha principal;
- `GEMINI_API_KEY`: chave do Google Gemini;
- `OPENAI_API_KEY`: opcional, somente se usar OpenAI.

Em **Variables**, podem ser criadas:

- `WORDPRESS_STATUS`: mantenha `draft` para revisão editorial;
- `IA_PROVEDOR`: `gemini` ou `openai`.

Use `WORDPRESS_STATUS=draft`. Os fluxos automáticos foram protegidos para criar rascunhos mesmo que uma configuração antiga ainda indique publicação direta.

## 3. Executar

Abra **Actions → Rios News Bot - Automação → Run workflow**. Selecione `ambos`, `youtube` ou `tendencias`. A execução automática usa `ambos`.

## Segurança

Se uma credencial já foi incluída em algum commit, removê-la do arquivo atual não basta. Revogue-a no provedor, gere outra e salve a nova somente nos Secrets do GitHub ou no `config.local.json` ignorado.
