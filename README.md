<center>
  <h1 style="font-size:2.4em; margin-bottom:0.1em;">🎵 Baixa_musica_Youtube</h1>
  <p style="margin-top:0.2em; font-size:1.05em; color:#555;">
    Script em Python para baixar músicas do YouTube em formato MP4, criando pastas automaticamente na área de trabalho com o nome do artista ou música.
  </p>
  <p>
    <a href="https://github.com/Rafael072187/Baixa_musica_Youtube" style="background:#24292F;color:#fff;padding:8px 14px;border-radius:8px;text-decoration:none;font-weight:600;">
      🔗 Repositório no GitHub
    </a>
  </p>
</center>

<hr>

## 🧭 Tabela de Conteúdos
- Descrição  
- Instalação  
- Uso  
- Tecnologias  
- Como contribuir  
- Autor  
- Observações  

---

## 📘 Descrição
<details>
<summary><b>Resumo</b></summary>

O **Baixa_musica_Youtube** é um script prático em **Python** que permite **baixar o áudio de vídeos do YouTube** automaticamente no formato **MP4**.  
Durante o download, o sistema identifica o **título da música e/ou artista** e cria uma **pasta com o nome correspondente** na **área de trabalho**.  
Caso o título não possa ser identificado, uma pasta padrão chamada **"N/A"** é criada para armazenar o arquivo.

Essa automação é ideal para quem deseja organizar músicas localmente, criar coleções offline ou realizar estudos de automação com manipulação de arquivos e downloads via terminal.
</details>

---

## ⚙️ Instalação
<details>
<summary><b>Passo a passo (Linux / macOS / Windows)</b></summary>

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/Rafael072187/Baixa_musica_Youtube.git
   cd Baixa_musica_Youtube
Crie e ative um ambiente virtual:

bash
Copiar código
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
Instale as dependências:

bash
Copiar código
pip install yt-dlp
(Opcional) Instale FFmpeg se quiser compatibilidade com outros formatos:

Windows: Baixe em https://www.gyan.dev/ffmpeg/ e adicione ao PATH.

macOS:

bash
Copiar código
brew install ffmpeg
Linux (Debian/Ubuntu):

bash
Copiar código
sudo apt install ffmpeg
</details>
🖥️ Uso
<details> <summary><b>Como usar o projeto</b></summary>
Execute o script principal:

bash
Copiar código
python musica.py
Insira a URL do vídeo do YouTube quando o programa solicitar.
O sistema então:

Baixa o vídeo em formato MP4 (áudio extraído do vídeo).

Cria automaticamente uma pasta na área de trabalho com o nome da música ou do artista.

Caso o nome não possa ser identificado, a pasta criada terá o nome “N/A”.

O arquivo baixado será armazenado dentro dessa pasta.

Exemplo de resultado:

mathematica
Copiar código
C:\Users\SeuNome\Desktop\Coldplay - Yellow\Yellow.mp4
Se o nome não for extraído corretamente:

makefile
Copiar código
C:\Users\SeuNome\Desktop\N_A\video_001.mp4
O processo é automático e pode ser adaptado para playlists ou múltiplas URLs.

</details> <p align="center" style="margin-top:14px;"> <img src="https://cdn-icons-png.flaticon.com/512/727/727269.png" width="90" alt="ícone ilustrativo"><br> <i>Exemplo simbólico do processo de download e organização automática.</i> </p>
🛠️ Tecnologias
<details> <summary><b>Stack principal</b></summary>
Linguagem: Python

Biblioteca principal: yt-dlp — extração e download de vídeos/áudios do YouTube

Módulo padrão: os — manipulação de diretórios (criação de pastas e caminhos dinâmicos)

Sistema de arquivos: automatiza salvamento na área de trabalho do usuário

</details>
🤝 Como contribuir
<details> <summary><b>Guia rápido</b></summary>
Faça um fork do repositório

Crie uma branch:

bash
Copiar código
git checkout -b feature/novas-funcionalidades
Adicione melhorias, por exemplo:

Suporte a múltiplas URLs

Escolha de formato (MP3, WAV, FLAC)

Interface gráfica simples

Commit e push:

bash
Copiar código
git commit -m "feat: adiciona suporte a múltiplos downloads"
git push origin feature/novas-funcionalidades
Abra um Pull Request detalhando a mudança.

</details>
👤 Autor
<details> <summary><b>Contatos</b></summary> <p> <b>Rafael Bittencourt de Araújo</b> — desenvolvedor do projeto.<br> GitHub: <a href="https://github.com/Rafael072187" target="_blank">github.com/Rafael072187</a><br> </p> </details>
📝 Observações
✅ Projeto prático para automação de downloads com Python e organização local.
🔧 Melhorias sugeridas:

Adicionar suporte a listas de reprodução (playlists)

Permitir renomeação automática de arquivos via API de metadados

Implementar interface gráfica (Tkinter ou PySimpleGUI)
⚠️ Aviso legal: respeite os termos de uso do YouTube — utilize o programa apenas para conteúdo de domínio público ou com permissão do autor.

<p align="center" style="margin-top:18px;"> <a href="https://github.com/Rafael072187/Baixa_musica_Youtube" style="background:#0b5fff;color:#fff;padding:10px 18px;border-radius:8px;text-decoration:none;font-weight:600;"> Ver repositório </a> </p> <p align="center" style="margin-top:14px;color:#666;"> Estrutura gerada automaticamente com base no repositório e comportamento real do código. </p> ```
