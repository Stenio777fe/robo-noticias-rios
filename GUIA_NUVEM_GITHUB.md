# ☁️ Guia Rápido: Como colocar o Rios News Bot na Nuvem (GitHub Actions)

O melhor e mais profissional sistema para rodar 24 horas por dia, 365 dias por ano na nuvem com o seu PC totalmente desligado é o **GitHub Actions** (plataforma em nuvem da Microsoft).

Nós já criamos o arquivo automático em:
`S:\steniobackup\Blogesite\robo-noticias\.github\workflows\robo_diario.yml`

---

## 🟢 Passo a Passo para ativar na Nuvem agora em 3 Minutos:

### 1º Passo: Criar uma conta no GitHub (se ainda não tiver)
1. Acesse: **https://github.com/signup**
2. Crie uma conta gratuita (só precisa do seu e-mail e uma senha).

### 2º Passo: Criar um Repositório Privado
1. No topo direito do GitHub, clique no ícone de **`+`** e escolha **`New repository`** (Novo repositório).
2. No nome do repositório, digite: `robo-noticias-rios`
3. **MUITO IMPORTANTE:** Marque a opção **`Private`** (Privado) para que apenas você tenha acesso ao seu robô e às suas chaves.
4. Clique no botão verde **`Create repository`**.

### 3º Passo: Enviar a pasta do robô para o GitHub
Você pode subir de duas formas super simples:

#### Opção A: Pelo próprio navegador (Arrestando e Soltando)
1. Na página do repositório que você acabou de criar no GitHub, clique no link **`uploading an existing file`** (enviar arquivo existente).
2. Abra a pasta `S:\steniobackup\Blogesite\robo-noticias\` no seu Windows Explorer.
3. Arraste todos os arquivos e pastas da dentro (incluindo a pasta `.github`, `robo_rios.py`, `config.json`, `requirements.txt`, etc.) para dentro da tela do navegador no GitHub.
4. Clique no botão verde **`Commit changes`**.

#### Opção B: Pelo Terminal / PowerShell (Mais rápido para desenvolvedores)
Abra o PowerShell na pasta do projeto e rode:
```powershell
cd S:\steniobackup\Blogesite\robo-noticias
git init
git add .
git commit -m "🚀 Subindo Rios News Bot para a Nuvem"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/robo-noticias-rios.git
git push -u origin main
```
*(Substitua `SEU_USUARIO` pelo seu nome de usuário do GitHub)*.

---

## 🏆 Pronto! O que acontece a partir de agora na Nuvem:

1. **⏰ Automático a cada 6 Horas:** Os servidores na nuvem da Microsoft vão ligar automaticamente 4 vezes ao dia (a cada 6 horas), rodar o robô e publicar as novas matérias no seu WordPress sem gastar 1 centavo da sua energia elétrica!
2. **📱 Botão Manual no Celular/PC:** Se você quiser rodar o robô na nuvem a qualquer hora fora do horário agendado:
   - Abra o seu repositório no GitHub pelo celular ou PC.
   - Clique na aba **`Actions`** lá no topo.
   - Clique em **`🤖 Rios News Bot - Automação 24h na Nuvem`** na barra lateral esquerda.
   - Clique no botão **`Run workflow` ➔ `Run workflow`**! O robô rodará instantaneamente na nuvem na frente dos seus olhos!

Se tiver qualquer dúvida ao subir no GitHub, me avise! 🚀☁️
