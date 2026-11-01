<center>
  <h1 style="font-size:2.4em; margin-bottom:0.1em;">🎵 YT Downloader Pro</h1>
  <p style="margin-top:0.2em; font-size:1.05em; color:#555;">
    Aplicação desktop em <b>Python + Tkinter</b> para baixar vídeos e músicas do YouTube
    com <b>yt-dlp</b> — com barra de progresso, cancelamento, escolha de formato e
    organização automática em pastas.
  </p>
  <p style="margin-top:0.1em; font-size:0.95em; color:#777;">
    Repositório <b>Baixa_musica_Youtube</b> · versão <b>2.0</b>
  </p>
  <p>
    <a href="https://github.com/Rafael072187/Baixa_musica_Youtube" style="background:#24292F;color:#fff;padding:8px 14px;border-radius:8px;text-decoration:none;font-weight:600;">
      🔗 Repositório no GitHub
    </a>
  </p>
</center>

<hr>

## 🧭 Tabela de Conteúdos

- [Descrição](#-descrição)
- [Funcionalidades](#-funcionalidades)
- [Requisitos](#-requisitos)
- [Instalação](#-instalação)
- [Como usar](#-como-usar)
- [Estrutura de arquivos gerada](#-estrutura-de-arquivos-gerada)
- [Preferências salvas](#-preferências-salvas)
- [Tecnologias](#-tecnologias)
- [Solução de problemas](#-solução-de-problemas)
- [Como contribuir](#-como-contribuir)
- [Autor](#-autor)
- [Observações](#-observações)

---

## 📘 Descrição

<details>
<summary><b>Resumo</b></summary>

O **YT Downloader Pro** é a evolução do script original `musica.py`: o que era um
programa de terminal virou uma **interface gráfica completa** construída com **Tkinter**,
usando o **yt-dlp** para extrair e baixar conteúdo do YouTube.

O aplicativo permite baixar **vídeo (MP4)** ou **áudio (MP3 / M4A)**, mostra o
**progresso em tempo real** (porcentagem, tamanho, velocidade e tempo restante),
permite **cancelar** o download a qualquer momento e organiza os arquivos
automaticamente em pastas.

A grande mudança de comportamento em relação à versão anterior:

- **Vídeo ou música avulsa** → pode ficar em uma pasta própria com o nome do item.
- **Playlist** → **todos os itens vão para uma única pasta com o nome da playlist**.

Todas as preferências (formato, qualidade, bitrate e pasta de destino) são salvas
entre execuções, então o programa abre já configurado do jeito que você deixou.

</details>

---

## ✨ Funcionalidades

<details open>
<summary><b>O que o programa faz</b></summary>

| Recurso                          | Descrição                                                                                                 |
| -------------------------------- | --------------------------------------------------------------------------------------------------------- |
| 🎬 **MP4**                       | Vídeo com áudio mesclado, com resolução selecionável: Melhor disponível, 1080p, 720p, 480p ou 360p.       |
| 🎧 **MP3**                       | Extração de áudio com bitrate configurável: 320, 192 ou 128 kbps.                                         |
| 🎼 **M4A**                       | Extração de áudio no formato M4A (AAC), sem reencode desnecessário.                                       |
| 🖼️ **Capa e metadados**          | Opção de embutir a thumbnail e as tags (título, artista, álbum) nos arquivos de áudio.                    |
| 📊 **Progresso real**            | Barra de progresso com porcentagem, bytes baixados, velocidade e ETA.                                     |
| ⏹️ **Cancelamento**              | Botão **Cancelar** que interrompe o download sem travar a janela.                                         |
| 📁 **Playlist em uma pasta**     | Com "Baixar playlist inteira" marcado, todos os itens ficam em uma pasta com o nome da playlist.          |
| 🗂️ **Pasta por vídeo**           | Para itens avulsos, opção de criar uma pasta com o nome do vídeo/música (ativada por padrão).             |
| 📂 **Pasta de destino**          | Campo editável, seletor de pasta e botão para abrir a pasta no explorador.                                |
| 💾 **Preferências persistentes** | Formato, qualidade, bitrate, pasta e opções são lembrados na próxima execução.                            |
| 🧾 **Registro na janela**        | Avisos e erros do yt-dlp aparecem no próprio app, não apenas no terminal.                                 |
| 🔗 **Validação de link**         | Aceita `youtube.com`, `youtu.be`, `m.youtube.com`, `music.youtube.com` e links sem `https://`.            |
| 🖥️ **Interface escura**          | Tema consistente, janela centralizada, redimensionável e com suporte a telas com escala (DPI) no Windows. |
| ⌨️ **Atalhos**                   | **Enter** no campo de link inicia o download; botões **Colar** e **Limpar**.                              |

</details>

<details>
<summary><b>O que mudou em relação à versão anterior</b></summary>

| Antes (`musica.py`)                                              | Agora (`yt_downloader_pro.py`)                    |
| ---------------------------------------------------------------- | ------------------------------------------------- |
| Script de terminal                                               | Interface gráfica Tkinter                         |
| Apenas MP4 (áudio extraído do vídeo)                             | MP4 (vídeo), MP3 e M4A                            |
| Sem feedback de progresso                                        | Barra de progresso com %, velocidade e ETA        |
| Sem como cancelar                                                | Botão Cancelar com cancelamento seguro            |
| Atualizava a interface pela thread de download (risco de travar) | Comunicação por fila + `root.after` (thread-safe) |
| Pasta fixa na área de trabalho                                   | Pasta configurável (padrão: `Downloads`)          |
| Playlist criava uma pasta por item                               | Playlist agrupa tudo em uma pasta com o nome dela |
| Erros genéricos                                                  | Mensagem real do yt-dlp no registro da janela     |
| Sem validação de link                                            | Validação e normalização de URLs do YouTube       |
| Sem checagem de FFmpeg                                           | Detecta o FFmpeg e avisa antes de começar         |

</details>

---

## 📦 Requisitos

| Requisito   | Versão / Observação                                                                                  |
| ----------- | ---------------------------------------------------------------------------------------------------- |
| **Python**  | 3.10 ou superior (testado no 3.14)                                                                   |
| **yt-dlp**  | Versão recente — instale/atualize com `pip install -U yt-dlp`                                        |
| **Tkinter** | Já incluído no instalador oficial do Python (Windows/macOS). No Linux: `sudo apt install python3-tk` |
| **FFmpeg**  | Necessário para **MP3**, **M4A** e para **mesclar vídeo + áudio** no MP4                             |

> Sem FFmpeg o app continua funcionando para MP4, mas usa apenas formatos
> progressivos (qualidade menor) e bloqueia a extração de áudio com um aviso claro.

---

## ⚙️ Instalação

<details>
<summary><b>Passo a passo (Windows / Linux / macOS)</b></summary>

### 1. Clone o repositório

```bash
git clone https://github.com/Rafael072187/Baixa_musica_Youtube.git
cd Baixa_musica_Youtube
```

### 2. Crie e ative um ambiente virtual

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -U yt-dlp
```

### 4. Instale o FFmpeg (recomendado)

**Windows**

```powershell
winget install Gyan.FFmpeg
```

Ou baixe em <https://www.gyan.dev/ffmpeg/builds/> e adicione a pasta `bin` ao `PATH`.

**macOS**

```bash
brew install ffmpeg
```

**Linux (Debian/Ubuntu)**

```bash
sudo apt install ffmpeg
```

Confirme a instalação:

```bash
ffmpeg -version
```

</details>

---

## 🖥️ Como usar

<details open>
<summary><b>Usando a interface</b></summary>

### 1. Execute o aplicativo

```bash
python yt_downloader_pro.py
```

> O script antigo `musica.py` foi substituído por `yt_downloader_pro.py`.

### 2. Cole o link

Cole a URL no campo **Link do vídeo** (ou use o botão **Colar**). São aceitos:

- `https://www.youtube.com/watch?v=...`
- `https://youtu.be/...`
- `https://www.youtube.com/shorts/...`
- `https://music.youtube.com/watch?v=...`
- `https://www.youtube.com/playlist?list=...`
- `https://www.youtube.com/watch?v=...&list=...`

### 3. Escolha o formato

| Opção            | Configuração disponível                               |
| ---------------- | ----------------------------------------------------- |
| **Vídeo (MP4)**  | Resolução: Melhor disponível, 1080p, 720p, 480p, 360p |
| **Música (MP3)** | Bitrate: 320, 192 ou 128 kbps                         |
| **Áudio (M4A)**  | Sem configuração extra                                |

### 4. Ajuste as opções

- **Criar uma pasta por vídeo** — para itens avulsos, cria uma pasta com o nome do vídeo.
- **Baixar playlist inteira** — baixa todos os itens do link. Ao marcar esta opção, o
  campo de pasta por vídeo é desativado e **todos os arquivos vão para uma pasta com o
  nome da playlist**.
- **Inserir capa e metadados** — embute thumbnail e tags nos arquivos de áudio
  (disponível para MP3/M4A).

### 5. Escolha a pasta de destino

O padrão é a pasta **Downloads** do usuário. Use **Selecionar…** para trocar e
**Abrir** para abrir a pasta no explorador de arquivos.

### 6. Inicie o download

Clique em **INICIAR DOWNLOAD** (ou pressione **Enter** no campo do link).

Durante o download você verá:

- barra de progresso e porcentagem;
- tamanho baixado / tamanho total;
- velocidade atual e tempo restante;
- nome do item em processamento;
- mensagens do yt-dlp no **Registro**.

Para interromper, clique em **Cancelar**.

### 7. Resultado

Ao terminar, o status mostra **Concluído com sucesso** e o caminho da pasta usada.
Use **Abrir** para acessar os arquivos.

</details>

---

## 📁 Estrutura de arquivos gerada

<details open>
<summary><b>Exemplos reais de saída</b></summary>

### Vídeo avulso em MP4 (com "Criar uma pasta por vídeo" marcado)

```
C:\Users\SeuNome\Downloads\
└── Me at the zoo [jNQXAC9IVRw]\
    └── Me at the zoo [jNQXAC9IVRw].mp4
```

### Música avulsa em MP3 (com capa e metadados)

```
C:\Users\SeuNome\Downloads\
└── Me at the zoo [jNQXAC9IVRw]\
    └── Me at the zoo [jNQXAC9IVRw].mp3
```

### Música avulsa sem pasta própria (opção desmarcada)

```
C:\Users\SeuNome\Downloads\
└── Me at the zoo [jNQXAC9IVRw].mp3
```

### Playlist em MP3 — todos os itens na mesma pasta

```
C:\Users\SeuNome\Downloads\
└── Google Search Stories\
    ├── Andrew Willis, Skatepark Engineer [GvgqDSnpRQM].mp3
    └── Outro vídeo da playlist [AbCdEfGhIjK].mp3
```

> O `[id]` no nome do arquivo evita que dois vídeos com o mesmo título se
> sobrescrevam. O nome da playlist é usado como nome da pasta; se ele não estiver
> disponível, o app usa o ID da playlist e, em último caso, `Playlist`.

</details>

---

## 🗂️ Preferências salvas

<details>
<summary><b>Onde ficam as configurações</b></summary>

O aplicativo salva suas preferências automaticamente ao iniciar um download e ao fechar:

| Sistema       | Caminho                                   |
| ------------- | ----------------------------------------- |
| Windows       | `%APPDATA%\YTDownloaderPro\config.json`   |
| Linux / macOS | `~/.config/yt-downloader-pro/config.json` |

Exemplo do arquivo:

```json
{
  "mode": "mp3",
  "video_quality": "Melhor disponível",
  "audio_bitrate": "192",
  "folder": "C:\\Users\\SeuNome\\Downloads",
  "per_video_folder": true,
  "playlist": false,
  "embed_thumbnail": true
}
```

Valores inválidos no arquivo (editado à mão ou corrompido) são corrigidos
automaticamente na abertura, sem travar o programa.

</details>

---

## 🛠️ Tecnologias

<details>
<summary><b>Stack principal</b></summary>

| Tecnologia         | Uso no projeto                                                 |
| ------------------ | -------------------------------------------------------------- |
| **Python**         | Linguagem principal                                            |
| **Tkinter / ttk**  | Interface gráfica, tema escuro e widgets estilizados           |
| **yt-dlp**         | Extração de metadados, download, conversão e pós-processamento |
| **FFmpeg**         | Extração de áudio (MP3/M4A) e mesclagem de vídeo + áudio       |
| **threading**      | Download em segundo plano sem congelar a interface             |
| **queue**          | Comunicação thread-safe entre o download e a interface         |
| **pathlib / json** | Manipulação de caminhos e persistência de preferências         |

</details>

---

## 🧯 Solução de problemas

<details>
<summary><b>Erros comuns</b></summary>

**"FFmpeg não encontrado" ao escolher MP3/M4A**
Instale o FFmpeg e garanta que ele esteja no `PATH`. Feche e abra o aplicativo
novamente. Verifique com `ffmpeg -version`.

**O MP4 saiu em qualidade baixa**
Sem FFmpeg o yt-dlp não consegue juntar vídeo e áudio separados, então o app usa
um formato progressivo. Instale o FFmpeg para liberar 1080p/720p e afins.

**Aviso: "No supported JavaScript runtime could be found"**
É um aviso do próprio yt-dlp. Opcionalmente instale o [Deno](https://deno.com/)
(`winget install DenoLand.Deno`) para liberar todos os formatos.

**"Link inválido"**
O app aceita apenas domínios do YouTube (`youtube.com`, `youtu.be`,
`music.youtube.com`, `youtube-nocookie.com`). Verifique se o link foi copiado inteiro.

**Download falha com 403 / "Sign in to confirm you're not a bot"**
Atualize o yt-dlp: `pip install -U yt-dlp`. Restrições de idade ou região podem
exigir cookies, recurso ainda não exposto na interface.

**A janela não abre / erro de Tkinter**
No Linux, instale o suporte: `sudo apt install python3-tk`.

</details>

---

## 🤝 Como contribuir

<details>
<summary><b>Guia rápido</b></summary>

1. Faça um fork do repositório.
2. Crie uma branch:

   ```bash
   git checkout -b feature/nova-funcionalidade
   ```

3. Implemente a melhoria. Algumas ideias que ainda faltam:
   - fila de downloads (vários links ao mesmo tempo);
   - download de legendas e capítulos;
   - suporte a cookies para conteúdo restrito;
   - agendamento e monitoramento de canais/playlists;
   - testes automatizados para validação de URL e templates de saída;
   - temas claro/escuro configuráveis.

4. Commit e push:

   ```bash
   git commit -m "feat: adiciona fila de downloads"
   git push origin feature/nova-funcionalidade
   ```

5. Abra um Pull Request detalhando a mudança.

</details>

---

## 👤 Autor

<details>
<summary><b>Contato</b></summary>

**Rafael Bittencourt de Araújo** — desenvolvedor do projeto.

- GitHub: [github.com/Rafael072187](https://github.com/Rafael072187)
- Repositório: [Baixa_musica_Youtube](https://github.com/Rafael072187/Baixa_musica_Youtube)

</details>

---

## 📝 Observações

- ✅ Projeto prático de automação de downloads com Python, `yt-dlp` e interface Tkinter.
- ✅ A organização em pastas é automática: playlist → uma pasta com o nome dela;
  item avulso → pasta própria (opcional).
- ⚠️ **Aviso legal:** respeite os Termos de Serviço do YouTube e os direitos autorais.
  Utilize o programa apenas para conteúdo de domínio público, com licença aberta ou
  com autorização do autor.

<p align="center" style="margin-top:18px;">
  <a href="https://github.com/Rafael072187/Baixa_musica_Youtube" style="background:#0b5fff;color:#fff;padding:10px 18px;border-radius:8px;text-decoration:none;font-weight:600;">
    Ver repositório
  </a>
</p>

<p align="center" style="margin-top:14px;color:#666;">
  README atualizado com base no comportamento real da versão <b>2.0</b> do aplicativo.
</p>
