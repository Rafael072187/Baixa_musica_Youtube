import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yt_dlp
import threading
import os

class MusicDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YT Downloader Pro")
        self.root.geometry("650x550") # Aumentei um pouco a altura para acomodar as novas opções
        self.root.configure(bg="#1e1e1e")

        # --- VARIÁVEIS DE CONTROLE ---
        self.mode_var = tk.StringVar(value="mp4")
        self.download_path = tk.StringVar(value=os.path.expanduser("~")) # Default: Pasta do Usuário

        self.status_text = "Pronto"
        self.is_downloading = False

        self.setup_ui()

    def setup_ui(self):
        """Cria os elementos visuais da interface."""
        main_frame = tk.Frame(self.root, bg="#1e1e1e")
        main_frame.pack(padx=30, pady=30, fill="both", expand=True)

        # Título
        tk.Label(main_frame, text="YT Downloader", font=("Arial", 20, "bold"),
                 bg="#1e1e1e", fg="#3498db").pack(pady=10)

        # Campo de URL
        tk.Label(main_frame, text="Cole o link do YouTube abaixo:",
                 bg="#1e1e1e", fg="white", font=("Arial", 11)).pack()
        self.url_entry = tk.Entry(main_frame, width=60, font=("Arial", 12),
                                   bg="#2d2d2d", fg="white", insertbackground="white")
        self.url_entry.pack(pady=10, ipady=10)

        # Seção de Escolha de Formato
        tk.Label(main_frame, text="Selecione o tipo de arquivo:",
                 bg="#1e1e1e", fg="#bdc3c7", font=("Arial", 10)).pack(pady=(10, 0))

        radio_frame = tk.Frame(main_frame, bg="#1e1e1e")
        radio_frame.pack()

        rb1 = tk.Radiobutton(radio_frame, text="Vídeo (MP4)", variable=self.mode_var,
                              value="mp4", bg="#1e1e1e", fg="white",
                              activeforeground="white", font=("Arial", 10),
                              padx=20)
        rb1.pack(side="left")

        rb2 = tk.Radiobutton(radio_frame, text="Música (MP3)", variable=self.mode_var,
                              value="mp3", bg="#1e1e1e", fg="white",
                              activeforeground="white", font=("Arial", 10),
                              padx=20)
        rb2.pack(side="left")

        # Seção de Escolha de Pasta
        tk.Label(main_frame, text="Onde salvar?",
                 bg="#1e1e1e", fg="#bdc3c7", font=("Arial", 10)).pack(pady=(20, 0))

        path_frame = tk.Frame(main_frame, bg="#1e1e1e")
        path_frame.pack()

        # Campo que exibe o caminho e o botão de selecionar lado a lado
        self.path_label = tk.Label(path_frame, textvariable=self.download_path,
                                    bg="#2d2d2d", fg="white", font=("Arial", 10),
                                    padx=10, pady=5, relief="flat")
        # No Tkinter, para colocar um botão ao lado de um label com texto variável,
        # usamos um frame interno ou apenas um botão estilizado.

        # Alternativa mais limpa para o usuário:
        self.path_entry = tk.Entry(path_frame, width=40, font=("Arial", 10),
                                    bg="#2d2d2d", fg="white", insertbackground="white")
        self.path_entry.insert(0, self.download_path.get())
        self.path_entry.pack(side="left", padx=5)

        btn_browse = tk.Button(path_frame, text="Selecionar Pasta",
                                command=self.browse_path,
                                bg="#3498db", fg="white", font=("Arial", 9, "bold"))
        btn_browse.pack(side="left")

        # Texto de Status
        self.status_label = tk.Label(main_frame, text="Aguardando...",
                                      bg="#1e1e1e", fg="#f1c40f",
                                      font=("Arial", 10, "bold"))
        self.status_label.pack(pady=20)

        # Botão de Ação
        self.download_btn = tk.Button(main_frame, text="INICIAR DOWNLOAD",
                                       command=self.start_thread,
                                       bg="#27ae60", fg="white",
                                       font=("Arial", 12, "bold"),
                                       padx=20, pady=10)
        self.download_btn.pack(pady=10)

    def browse_path(self):
        """Abre o explorador de arquivos para selecionar a pasta de destino."""
        selected_path = filedialog.askdirectory()
        if selected_path:
            self.download_path.set(selected_path)
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, selected_path)

    def start_thread(self):
        url = self.url_entry.get().strip()
        if not url or "youtube.com" not in url and "youtu.be" not in url:
            messagebox.showwarning("Erro", "Por favor, insira um link válido do YouTube.")
            return

        self.is_downloading = True
        self.status_label.config(text="Iniciando...")
        self.download_btn.config(state="disabled", bg="#7f8c8d")

        thread = threading.Thread(target=self.run_yt_dlp, args=(url,), daemon=True)
        thread.start()

    def run_yt_dlp(self, url):
        try:
            mode = self.mode_var.get()
            base_path = self.download_path.get()

            # O segredo está no 'outtmpl':
            # Ele vai criar uma pasta com o nome do vídeo e colocar o arquivo dentro.
            # Ex: C:/Downloads/Nome Do Video/Nome do Video.mp4
            path_template = os.path.join(base_path, "%(title)s")

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'outtmpl': f'{path_template}/%(title)s.%(ext)s',
            }

            if mode == "mp3":
                ydl_opts.update({
                    'format': 'bestaudio',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                })
            else:
                ydl_opts.update({'format': 'bestvideo+bestaudio/best'})

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            self.status_label.config(text="Concluído com Sucesso!")
        except Exception as e:
            self.status_label.config(text="Erro no download")
            print(f"Erro: {e}")
            messagebox.showerror("Erro", "Ocorreu um erro durante o processo.")
        finally:
            self.is_downloading = False
            self.download_btn.config(state="normal", bg="#27ae60")

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')

    app = MusicDownloader(root)
    root.mainloop()