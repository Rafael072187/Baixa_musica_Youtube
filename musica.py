import os
import subprocess
import json
import shutil
from collections import Counter
from tqdm import tqdm

desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

def artista_mais_frequente(url):
    info = subprocess.run(
        ["yt-dlp", "-j", url],
        capture_output=True, text=True
    )
    artistas = []
    for linha in info.stdout.splitlines():
        try:
            dados = json.loads(linha)
            artista = dados.get("artist") or "Desconhecido"
            artistas.append(artista)
        except Exception:
            artistas.append("Desconhecido")
    return Counter(artistas).most_common(1)[0][0] if artistas else "Desconhecido"


def ffmpeg_disponivel(ffmpeg_path):
    return shutil.which(ffmpeg_path) is not None or os.path.exists(ffmpeg_path)


def baixar_musica(url, ffmpeg_path):
    if "playlist" in url or "list=" in url:
        artista = artista_mais_frequente(url)
        output_template = os.path.join(desktop_path, artista, '%(title)s.%(ext)s')
    else:
        output_template = os.path.join(desktop_path, '%(artist,Desconhecido)s', '%(title)s.%(ext)s')

    comando = [
        "yt-dlp",
        "--no-part",
        "--extract-audio",
        "--audio-format", "mp3",
        "--output", output_template,
        "--no-abort-on-error",
        "--ignore-errors",
        "--newline",  # 🔹 Necessário para capturar progresso
        "--progress-template", "%(progress._percent_str)s %(progress._eta_str)s",
        url
    ]

    processo = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    progresso = tqdm(total=100, unit="%", desc="🎵 Baixando", colour="green", ncols=80)
    for linha in processo.stdout:
        if "%" in linha:
            try:
                porcentagem = float(linha.split("%")[0].strip())
                progresso.n = porcentagem
                progresso.refresh()
            except:
                pass

    processo.wait()
    progresso.close()

    if processo.returncode != 0:
        print("❌ Erro ao baixar. Verifique o link ou o FFmpeg.")
    else:
        print("\n✅ Download concluído com sucesso!")


def main():
    ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"
    if not ffmpeg_disponivel(ffmpeg_path):
        print("⚠️ FFmpeg não encontrado no caminho especificado. Verifique a instalação.")
        return

    while True:
        url = input("Cole o link do vídeo ou playlist do YouTube (ou 'sair' para encerrar): ").strip()
        if url.lower() == "sair":
            print("👋 Encerrando o programa.")
            break
        if not url.startswith("http"):
            print("⚠️ Link inválido. Tente novamente.")
            continue
        print("\n🔄 Iniciando download...\n")
        baixar_musica(url, ffmpeg_path)


if __name__ == "__main__":
    main()
