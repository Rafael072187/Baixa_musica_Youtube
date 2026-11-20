#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YT Downloader Pro — interface gráfica (Tkinter) para o yt-dlp.

Melhorias em relação à versão original:
  * a thread de download nunca mexe nos widgets: tudo passa por uma fila
    consumida pela thread principal via ``root.after``;
  * barra de progresso com porcentagem, velocidade, tamanho e tempo restante;
  * download cancelável sem travar a janela;
  * validação de link e de pasta antes de iniciar;
  * MP4 com escolha de resolução, MP3 com bitrate configurável e M4A;
  * playlist inteira em uma única pasta com o nome da playlist (itens avulsos
    continuam podendo ficar em pastas separadas);
  * itens indisponíveis em uma playlist são ignorados, sem abortar o restante;
  * aviso claro quando o FFmpeg não está disponível;
  * preferências (modo, qualidade, pasta) salvas entre execuções;
  * registro de mensagens do yt-dlp dentro da própria janela.
"""

from __future__ import annotations

import functools
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
from dataclasses import asdict, dataclass, field
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, cast
from urllib.parse import parse_qs, urlparse

import yt_dlp
from yt_dlp.postprocessor.ffmpeg import FFmpegPostProcessor
from yt_dlp.utils import DownloadCancelled, DownloadError

# --------------------------------------------------------------------------- #
# Constantes
# --------------------------------------------------------------------------- #

APP_NAME = "YT Downloader Pro"
APP_VERSION = "2.0"

COLORS = {
    "bg": "#1e1e1e",
    "card": "#252526",
    "input": "#2d2d2d",
    "border": "#3a3a3a",
    "fg": "#e8e8e8",
    "muted": "#9aa4ae",
    "accent": "#3498db",
    "accent_hover": "#4aa8e0",
    "green": "#27ae60",
    "green_hover": "#2ecc71",
    "red": "#c0392b",
    "red_hover": "#e74c3c",
    "yellow": "#f1c40f",
    "disabled": "#3f4a55",
}

MODES = (
    ("mp4", "Vídeo (MP4)"),
    ("mp3", "Música (MP3)"),
    ("m4a", "Áudio (M4A)"),
)

VIDEO_QUALITIES = ("Melhor disponível", "1080p", "720p", "480p", "360p")
QUALITY_HEIGHTS = {"1080p": 1080, "720p": 720, "480p": 480, "360p": 360}
AUDIO_BITRATES = ("320", "192", "128")

YOUTUBE_HOSTS = frozenset(
    {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "music.youtube.com",
        "youtu.be",
        "www.youtu.be",
        "youtube-nocookie.com",
        "www.youtube-nocookie.com",
    }
)

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
SCHEME_RE = re.compile(r"^https?://", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #


def config_path() -> Path:
    """Local do arquivo de preferências (por usuário)."""
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / "YTDownloaderPro" / "config.json"
    return Path.home() / ".config" / "yt-downloader-pro" / "config.json"


def normalize_url(raw: str) -> str | None:
    """Devolve a URL normalizada ou ``None`` se não for um link do YouTube."""
    raw = (raw or "").strip()
    if not raw:
        return None
    if not SCHEME_RE.match(raw):
        raw = f"https://{raw}"
    try:
        parsed = urlparse(raw)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    if host not in YOUTUBE_HOSTS:
        return None
    if host.endswith("youtu.be") and len(parsed.path.strip("/")) < 2:
        return None
    return raw


def ffmpeg_available() -> bool:
    """True se o yt-dlp conseguiu localizar um FFmpeg utilizável."""
    try:
        return bool(FFmpegPostProcessor().available)
    except Exception:  # noqa: BLE001 - qualquer falha aqui significa "sem ffmpeg"
        return shutil.which("ffmpeg") is not None


def is_playlist_url(url: str) -> bool:
    """True quando a URL aponta para uma playlist do YouTube."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parse_qs(parsed.query).get("list"):
        return True
    return parsed.path.rstrip("/").endswith("/playlist")


def human_bytes(value: float | None) -> str:
    if value is None:
        return "—"
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{int(size)} B" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return "—"


def human_speed(value: float | None) -> str:
    return f"{human_bytes(value)}/s" if value else "—"


def human_eta(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    seconds = int(seconds)
    if seconds < 0:
        return "—"
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def shorten(text: str, limit: int = 60) -> str:
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


def clean_error(message: str) -> str:
    """Remove códigos ANSI e prefixos ruidosos das mensagens do yt-dlp."""
    text = ANSI_RE.sub("", message or "").strip()
    for prefix in ("ERROR: ", "ERROR:", "[youtube] "):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    return text or "Erro desconhecido."


def open_in_file_manager(folder: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(str(folder))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(folder)])
    else:
        subprocess.Popen(["xdg-open", str(folder)])


def enable_high_dpi() -> None:
    """Deixa a interface nítida em telas com escala > 100% (Windows)."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:  # noqa: BLE001 - recurso opcional
        pass


# --------------------------------------------------------------------------- #
# Preferências e configuração do download
# --------------------------------------------------------------------------- #


@dataclass
class Settings:
    mode: str = "mp4"
    video_quality: str = "Melhor disponível"
    audio_bitrate: str = "192"
    folder: str = field(default_factory=lambda: str(Path.home() / "Downloads"))
    per_video_folder: bool = True
    playlist: bool = False
    embed_thumbnail: bool = True

    @classmethod
    def load(cls, path: Path) -> "Settings":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        if not isinstance(data, dict):
            return cls()
        known = set(cls.__dataclass_fields__)
        settings = cls(**{key: value for key, value in data.items() if key in known})
        return settings.sanitized()

    def sanitized(self) -> "Settings":
        """Corrige valores inválidos vindos de um arquivo editado à mão."""
        if self.mode not in {value for value, _ in MODES}:
            self.mode = "mp4"
        if self.video_quality not in VIDEO_QUALITIES:
            self.video_quality = VIDEO_QUALITIES[0]
        if self.audio_bitrate not in AUDIO_BITRATES:
            self.audio_bitrate = "192"
        if not isinstance(self.folder, str) or not self.folder.strip():
            self.folder = str(Path.home() / "Downloads")
        self.per_video_folder = bool(self.per_video_folder)
        self.playlist = bool(self.playlist)
        self.embed_thumbnail = bool(self.embed_thumbnail)
        return self

    def save(self, path: Path) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(asdict(self), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass


@dataclass(frozen=True)
class DownloadConfig:
    url: str
    folder: str
    mode: str
    quality: str
    bitrate: str
    per_video_folder: bool
    playlist: bool
    embed_thumbnail: bool


@dataclass
class _DownloadReport:
    """Coleta falhas e itens concluídos durante um download em lote."""

    errors: list[str] = field(default_factory=list)
    finished_ids: set[str] = field(default_factory=set)


class _QueueLogger:
    """Envia avisos/erros do yt-dlp para a fila consumida pela interface."""

    def __init__(
        self, events: queue.Queue, report: _DownloadReport | None = None
    ) -> None:
        self._events = events
        self._report = report

    def debug(self, message: str) -> None:  # noqa: D401 - assinatura exigida pelo yt-dlp
        if message.startswith("[debug] "):
            return

    def info(self, message: str) -> None:
        pass

    def warning(self, message: str) -> None:
        self._events.put(("log", f"Aviso: {clean_error(message)}"))

    def error(self, message: str) -> None:
        text = clean_error(message)
        self._events.put(("log", f"Erro: {text}"))
        if self._report is not None:
            self._report.errors.append(text)


# --------------------------------------------------------------------------- #
# Interface
# --------------------------------------------------------------------------- #


class YTDownloaderApp:
    POLL_INTERVAL_MS = 80
    MAX_LOG_LINES = 400

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.settings = Settings.load(config_path())
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker: threading.Thread | None = None
        self._interactive: list[tk.Widget] = []
        self._busy = False
        self._indeterminate = False

        self.root.title(f"{APP_NAME} {APP_VERSION}")
        self.root.geometry("780x800")
        self.root.minsize(680, 660)
        self.root.configure(bg=COLORS["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._setup_style()
        self._build_ui()
        self._center_window()
        self._apply_mode_state()
        self._apply_playlist_state()
        self._poll_events()

    def _center_window(self) -> None:
        self.root.update_idletasks()
        width = max(self.root.winfo_width(), 780)
        height = max(self.root.winfo_height(), 800)
        x = max(0, (self.root.winfo_screenwidth() - width) // 2)
        y = max(0, (self.root.winfo_screenheight() - height) // 3)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    # ------------------------------------------------------------------ estilo

    def _setup_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(".", background=COLORS["bg"], foreground=COLORS["fg"])
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["fg"])
        style.configure(
            "TEntry",
            fieldbackground=COLORS["input"],
            foreground=COLORS["fg"],
            insertcolor=COLORS["fg"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["input"],
            darkcolor=COLORS["input"],
            padding=6,
        )
        style.map(
            "TEntry",
            fieldbackground=[("disabled", "#2a2a2a")],
            foreground=[("disabled", COLORS["disabled"])],
        )
        style.configure(
            "TCombobox",
            fieldbackground=COLORS["input"],
            background=COLORS["input"],
            foreground=COLORS["fg"],
            arrowcolor=COLORS["fg"],
            bordercolor=COLORS["border"],
            padding=4,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", COLORS["input"]), ("disabled", "#2a2a2a")],
            foreground=[("readonly", COLORS["fg"]), ("disabled", COLORS["disabled"])],
            selectbackground=[("readonly", COLORS["input"])],
            selectforeground=[("readonly", COLORS["fg"])],
        )
        style.configure(
            "TRadiobutton",
            background=COLORS["bg"],
            foreground=COLORS["fg"],
            indicatorcolor=COLORS["input"],
        )
        style.map(
            "TRadiobutton",
            background=[("active", COLORS["bg"])],
            foreground=[("active", COLORS["accent"]), ("disabled", COLORS["disabled"])],
        )
        style.configure(
            "TCheckbutton",
            background=COLORS["bg"],
            foreground=COLORS["fg"],
            indicatorcolor=COLORS["input"],
        )
        style.map(
            "TCheckbutton",
            background=[("active", COLORS["bg"])],
            foreground=[("active", COLORS["accent"]), ("disabled", COLORS["disabled"])],
        )
        style.configure(
            "Accent.TButton",
            background=COLORS["accent"],
            foreground="white",
            borderwidth=0,
            focusthickness=0,
            padding=(14, 7),
        )
        style.map(
            "Accent.TButton",
            background=[
                ("active", COLORS["accent_hover"]),
                ("disabled", COLORS["disabled"]),
            ],
            foreground=[("disabled", "#8a9aa8")],
        )
        style.configure(
            "Ghost.TButton",
            background=COLORS["input"],
            foreground=COLORS["fg"],
            borderwidth=0,
            focusthickness=0,
            padding=(12, 7),
        )
        style.map(
            "Ghost.TButton",
            background=[("active", "#3a3a3a"), ("disabled", "#2a2a2a")],
            foreground=[("disabled", COLORS["disabled"])],
        )
        style.configure(
            "Success.TButton",
            background=COLORS["green"],
            foreground="white",
            borderwidth=0,
            focusthickness=0,
            padding=(20, 12),
            font=("Segoe UI", 11, "bold"),
        )
        style.map(
            "Success.TButton",
            background=[
                ("active", COLORS["green_hover"]),
                ("disabled", COLORS["disabled"]),
            ],
            foreground=[("disabled", "#8a9aa8")],
        )
        style.configure(
            "Danger.TButton",
            background=COLORS["red"],
            foreground="white",
            borderwidth=0,
            focusthickness=0,
            padding=(20, 12),
            font=("Segoe UI", 11, "bold"),
        )
        style.map(
            "Danger.TButton",
            background=[("active", COLORS["red_hover"]), ("disabled", "#3a3a3a")],
            foreground=[("disabled", "#7f8f9f")],
        )
        style.configure(
            "Horizontal.TProgressbar",
            background=COLORS["green"],
            troughcolor=COLORS["input"],
            bordercolor=COLORS["input"],
            lightcolor=COLORS["green"],
            darkcolor=COLORS["green"],
            thickness=14,
        )
        self.root.option_add("*TCombobox*Listbox.background", COLORS["input"])
        self.root.option_add("*TCombobox*Listbox.foreground", COLORS["fg"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", COLORS["accent"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", "white")

    # ------------------------------------------------------------- construção

    def _build_ui(self) -> None:
        self.url_var = tk.StringVar()
        self.folder_var = tk.StringVar(value=self.settings.folder)
        self.mode_var = tk.StringVar(value=self.settings.mode)
        self.quality_var = tk.StringVar(value=self.settings.video_quality)
        self.bitrate_var = tk.StringVar(value=self.settings.audio_bitrate)
        self.per_video_var = tk.BooleanVar(value=self.settings.per_video_folder)
        self.playlist_var = tk.BooleanVar(value=self.settings.playlist)
        self.embed_var = tk.BooleanVar(value=self.settings.embed_thumbnail)
        self.status_var = tk.StringVar(value="Pronto")
        self.pct_var = tk.StringVar(value="0%")
        self.detail_var = tk.StringVar(value="Cole um link do YouTube para começar")

        outer = tk.Frame(self.root, bg=COLORS["bg"])
        outer.pack(fill="both", expand=True, padx=26, pady=20)

        self._build_header(outer)
        self._build_url_card(outer)
        self._build_options_card(outer)
        self._build_destination_card(outer)
        self._build_progress_card(outer)
        self._build_actions(outer)
        self._build_log(outer)

        self.mode_var.trace_add("write", lambda *_: self._apply_mode_state())
        self.playlist_var.trace_add("write", lambda *_: self._apply_playlist_state())
        self.url_var.trace_add("write", lambda *_: self._apply_playlist_state())

    def _build_header(self, parent: tk.Widget) -> None:
        header = tk.Frame(parent, bg=COLORS["bg"])
        header.pack(fill="x")
        tk.Label(
            header,
            text="YT Downloader",
            bg=COLORS["bg"],
            fg=COLORS["accent"],
            font=("Segoe UI Semibold", 22),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Vídeos e músicas do YouTube em alta qualidade",
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(2, 0))

    def _card(self, parent: tk.Widget, title: str, *, expand: bool = False) -> tk.Frame:
        fill = "both" if expand else "x"
        wrapper = tk.Frame(parent, bg=COLORS["bg"])
        wrapper.pack(fill=fill, expand=expand, pady=(14, 0))
        tk.Label(
            wrapper,
            text=title.upper(),
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", pady=(0, 5))
        body = tk.Frame(
            wrapper,
            bg=COLORS["card"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        body.pack(fill=fill, expand=expand)
        inner = tk.Frame(body, bg=COLORS["card"])
        inner.pack(fill=fill, expand=expand, padx=14, pady=12)
        return inner

    def _build_url_card(self, parent: tk.Widget) -> None:
        inner = self._card(parent, "Link do vídeo")

        row = tk.Frame(inner, bg=COLORS["card"])
        row.pack(fill="x")

        self.url_entry = tk.Entry(
            row,
            textvariable=self.url_var,
            font=("Segoe UI", 11),
            bg=COLORS["input"],
            fg=COLORS["fg"],
            insertbackground=COLORS["fg"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"],
        )
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.url_entry.bind("<Return>", lambda _event: self.start_download())

        paste_btn = ttk.Button(
            row, text="Colar", command=self._paste_url, style="Ghost.TButton"
        )
        paste_btn.pack(side="left", padx=(0, 6))
        clear_btn = ttk.Button(
            row, text="Limpar", command=self._clear_url, style="Ghost.TButton"
        )
        clear_btn.pack(side="left")

        self._interactive.extend([paste_btn, clear_btn])

    def _build_options_card(self, parent: tk.Widget) -> None:
        inner = self._card(parent, "Formato")

        modes_row = tk.Frame(inner, bg=COLORS["card"])
        modes_row.pack(fill="x")
        for value, label in MODES:
            radio = ttk.Radiobutton(
                modes_row,
                text=label,
                value=value,
                variable=self.mode_var,
                style="TRadiobutton",
            )
            radio.pack(side="left", padx=(0, 18))
            self._interactive.append(radio)

        params_row = tk.Frame(inner, bg=COLORS["card"])
        params_row.pack(fill="x", pady=(10, 0))

        tk.Label(
            params_row,
            text="Resolução:",
            bg=COLORS["card"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
        ).pack(side="left")
        self.quality_combo = ttk.Combobox(
            params_row,
            textvariable=self.quality_var,
            values=VIDEO_QUALITIES,
            state="readonly",
            width=18,
            font=("Segoe UI", 10),
        )
        self.quality_combo.pack(side="left", padx=(6, 18))

        tk.Label(
            params_row,
            text="Bitrate do MP3:",
            bg=COLORS["card"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
        ).pack(side="left")
        self.bitrate_combo = ttk.Combobox(
            params_row,
            textvariable=self.bitrate_var,
            values=AUDIO_BITRATES,
            state="readonly",
            width=6,
            font=("Segoe UI", 10),
        )
        self.bitrate_combo.pack(side="left", padx=(6, 0))

        flags_row = tk.Frame(inner, bg=COLORS["card"])
        flags_row.pack(fill="x", pady=(10, 0))

        self.per_video_check = ttk.Checkbutton(
            flags_row,
            text="Criar uma pasta por vídeo",
            variable=self.per_video_var,
            style="TCheckbutton",
        )
        self.per_video_check.pack(side="left", padx=(0, 18))

        playlist_check = ttk.Checkbutton(
            flags_row,
            text="Baixar playlist inteira",
            variable=self.playlist_var,
            style="TCheckbutton",
        )
        playlist_check.pack(side="left", padx=(0, 18))

        self.embed_check = ttk.Checkbutton(
            flags_row,
            text="Inserir capa e metadados",
            variable=self.embed_var,
            style="TCheckbutton",
        )
        self.embed_check.pack(side="left")

        self.playlist_hint = tk.Label(
            inner,
            text="",
            bg=COLORS["card"],
            fg=COLORS["accent"],
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
        )

        self._interactive.extend(
            [
                self.quality_combo,
                self.bitrate_combo,
                self.per_video_check,
                playlist_check,
                self.embed_check,
            ]
        )

    def _build_destination_card(self, parent: tk.Widget) -> None:
        inner = self._card(parent, "Pasta de destino")

        row = tk.Frame(inner, bg=COLORS["card"])
        row.pack(fill="x")

        self.folder_entry = tk.Entry(
            row,
            textvariable=self.folder_var,
            font=("Segoe UI", 10),
            bg=COLORS["input"],
            fg=COLORS["fg"],
            insertbackground=COLORS["fg"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"],
        )
        self.folder_entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 8))

        browse_btn = ttk.Button(
            row,
            text="Selecionar…",
            command=self._browse_folder,
            style="Accent.TButton",
        )
        browse_btn.pack(side="left", padx=(0, 6))
        open_btn = ttk.Button(
            row, text="Abrir", command=self._open_folder, style="Ghost.TButton"
        )
        open_btn.pack(side="left")

        self._interactive.extend([browse_btn, open_btn])

    def _build_progress_card(self, parent: tk.Widget) -> None:
        inner = self._card(parent, "Progresso")

        self.progress = ttk.Progressbar(
            inner,
            style="Horizontal.TProgressbar",
            mode="determinate",
            maximum=100,
            value=0,
        )
        self.progress.pack(fill="x")

        info_row = tk.Frame(inner, bg=COLORS["card"])
        info_row.pack(fill="x", pady=(8, 0))

        tk.Label(
            info_row,
            textvariable=self.pct_var,
            bg=COLORS["card"],
            fg=COLORS["fg"],
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left")

        tk.Label(
            info_row,
            textvariable=self.detail_var,
            bg=COLORS["card"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            anchor="e",
        ).pack(side="right", fill="x", expand=True, padx=(12, 0))

        tk.Label(
            inner,
            textvariable=self.status_var,
            bg=COLORS["card"],
            fg=COLORS["yellow"],
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(8, 0))

    def _build_actions(self, parent: tk.Widget) -> None:
        actions = tk.Frame(parent, bg=COLORS["bg"])
        actions.pack(fill="x", pady=(16, 0))

        self.download_btn = ttk.Button(
            actions,
            text="INICIAR DOWNLOAD",
            command=self.start_download,
            style="Success.TButton",
        )
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.cancel_btn = ttk.Button(
            actions,
            text="Cancelar",
            command=self.cancel_download,
            style="Danger.TButton",
            state="disabled",
        )
        self.cancel_btn.pack(side="left")

    def _build_log(self, parent: tk.Widget) -> None:
        inner = self._card(parent, "Registro", expand=True)

        wrapper = tk.Frame(inner, bg=COLORS["card"])
        wrapper.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            wrapper,
            height=7,
            wrap="word",
            bg=COLORS["input"],
            fg="#cfd8dc",
            insertbackground=COLORS["fg"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            font=("Consolas", 9),
            state="disabled",
        )
        self.log_text.pack(side="left", fill="both", expand=True)

    # ------------------------------------------------------------ preferências

    def _save_settings(self) -> None:
        self.settings = Settings(
            mode=self.mode_var.get(),
            video_quality=self.quality_var.get(),
            audio_bitrate=self.bitrate_var.get(),
            folder=self.folder_var.get().strip() or str(Path.home()),
            per_video_folder=self.per_video_var.get(),
            playlist=self.playlist_var.get(),
            embed_thumbnail=self.embed_var.get(),
        )
        self.settings.save(config_path())

    def _apply_mode_state(self) -> None:
        mode = self.mode_var.get()
        video = mode == "mp4"
        if not self._busy:
            self._set_enabled([self.quality_combo], video)
            self._set_enabled([self.bitrate_combo], mode == "mp3")
            self._set_enabled([self.embed_check], not video)

    def _apply_playlist_state(self) -> None:
        """Playlist ativa = uma pasta única; desativa a opção de pasta por vídeo."""
        playlist = self.playlist_var.get()
        if not self._busy:
            self._set_enabled([self.per_video_check], not playlist)

        if not playlist:
            self.playlist_hint.pack_forget()
            return

        url = self.url_var.get().strip()
        if not url or is_playlist_url(url):
            text = (
                "Playlist ativa: todos os itens serão salvos em uma única "
                "pasta com o nome da playlist."
            )
        else:
            text = (
                "Playlist ativa: cole um link com 'list=…' para baixar a "
                "playlist inteira. Links avulsos mantêm uma pasta por vídeo."
            )

        if self.playlist_hint.cget("text") != text:
            self.playlist_hint.configure(text=text)
        if not self.playlist_hint.winfo_manager():
            self.playlist_hint.pack(fill="x", pady=(8, 0))

    # -------------------------------------------------------------- utilidades

    @staticmethod
    def _set_enabled(widgets: list[tk.Widget], enabled: bool) -> None:
        for widget in widgets:
            try:
                if isinstance(widget, ttk.Widget):
                    widget.state(["!disabled"] if enabled else ["disabled"])
                else:
                    cast(Any, widget).configure(
                        state="normal" if enabled else "disabled"
                    )
            except tk.TclError:
                pass

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._set_enabled(self._interactive, not busy)
        self._set_enabled([self.url_entry, self.folder_entry], not busy)
        self.download_btn.state(["disabled"] if busy else ["!disabled"])
        self.cancel_btn.state(["!disabled"] if busy else ["disabled"])
        if not busy:
            self._apply_mode_state()
            self._apply_playlist_state()

    def _set_indeterminate(self, enabled: bool) -> None:
        if enabled == self._indeterminate:
            return
        self._indeterminate = enabled
        if enabled:
            self.progress.stop()
            self.progress.configure(mode="indeterminate")
            self.progress.start(15)
        else:
            self.progress.stop()
            self.progress.configure(mode="determinate")

    def _append_log(self, message: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{stamp}] {message}\n")
        lines = int(self.log_text.index("end-1c").split(".")[0])
        if lines > self.MAX_LOG_LINES:
            self.log_text.delete("1.0", f"{lines - self.MAX_LOG_LINES}.0")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # ------------------------------------------------------------- ações de UI

    def _paste_url(self) -> None:
        try:
            text = self.root.clipboard_get()
        except tk.TclError:
            return
        self.url_var.set(text.strip())
        self.url_entry.focus_set()

    def _clear_url(self) -> None:
        self.url_var.set("")
        self.url_entry.focus_set()

    def _browse_folder(self) -> None:
        initial = self.folder_var.get().strip()
        selected = filedialog.askdirectory(
            title="Escolha a pasta de destino",
            initialdir=initial if Path(initial).is_dir() else str(Path.home()),
        )
        if selected:
            self.folder_var.set(selected)

    def _open_folder(self) -> None:
        folder = Path(self.folder_var.get().strip() or str(Path.home()))
        if not folder.is_dir():
            messagebox.showinfo(
                "Pasta indisponível",
                "A pasta informada ainda não existe. Ela será criada no primeiro download.",
            )
            return
        try:
            open_in_file_manager(folder)
        except OSError as exc:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{exc}")

    def cancel_download(self) -> None:
        if not self._busy:
            return
        self.cancel_event.set()
        self.cancel_btn.state(["disabled"])
        self.status_var.set("Cancelando…")

    # --------------------------------------------------------------- download

    def start_download(self) -> None:
        if self._busy:
            return
        if self.worker and self.worker.is_alive():
            self.status_var.set("Aguarde o download anterior terminar…")
            return

        url = normalize_url(self.url_var.get())
        if not url:
            messagebox.showwarning(
                "Link inválido",
                "Informe um link válido do YouTube.\n"
                "Exemplos:\n"
                "  https://www.youtube.com/watch?v=…\n"
                "  https://youtu.be/…",
            )
            self.url_entry.focus_set()
            return

        folder = self.folder_var.get().strip()
        if not folder:
            messagebox.showwarning(
                "Pasta inválida", "Escolha onde o arquivo será salvo."
            )
            return
        try:
            Path(folder).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror(
                "Pasta inválida", f"Não foi possível usar esta pasta:\n{exc}"
            )
            return

        mode = self.mode_var.get()
        if mode != "mp4" and not ffmpeg_available():
            messagebox.showerror(
                "FFmpeg não encontrado",
                "Para extrair áudio é necessário ter o FFmpeg instalado e "
                "disponível no PATH.\n\nBaixe em https://ffmpeg.org/download.html "
                "e reinicie o aplicativo.",
            )
            return

        config = DownloadConfig(
            url=url,
            folder=folder,
            mode=mode,
            quality=self.quality_var.get(),
            bitrate=self.bitrate_var.get(),
            per_video_folder=self.per_video_var.get(),
            playlist=self.playlist_var.get(),
            embed_thumbnail=self.embed_var.get(),
        )

        self._save_settings()
        self.cancel_event.clear()
        self._set_busy(True)
        self._set_indeterminate(False)
        self.progress.configure(value=0)
        self.pct_var.set("0%")
        self.status_var.set("Obtendo informações do vídeo…")
        self.detail_var.set("—")
        self._append_log(f"Iniciando download: {url}")

        self.worker = threading.Thread(
            target=self._download_worker,
            args=(config,),
            name="yt-dlp-worker",
            daemon=True,
        )
        self.worker.start()

    def _download_worker(self, config: DownloadConfig) -> None:
        """Executa o yt-dlp fora da thread da interface."""
        report = _DownloadReport()
        try:
            options = self._build_options(config, report)
            with yt_dlp.YoutubeDL(cast(Any, options)) as ydl:
                retcode = ydl.download([config.url])
        except DownloadCancelled:
            self.events.put(("cancelled", None))
            return
        except DownloadError as exc:
            if self.cancel_event.is_set():
                self.events.put(("cancelled", None))
            else:
                self.events.put(("error", clean_error(str(exc))))
            return
        except Exception as exc:  # noqa: BLE001 - erro inesperado precisa chegar à UI
            self.events.put(("error", f"{type(exc).__name__}: {exc}"))
            return

        batch = config.playlist or is_playlist_url(config.url)
        if retcode == 0 and not report.errors:
            self.events.put(("done", None))
        elif batch and report.finished_ids:
            # Pelo menos um item foi baixado: os demais estavam indisponíveis.
            self.events.put(
                (
                    "partial",
                    {
                        "count": len(report.errors),
                        "first": report.errors[0],
                    },
                )
            )
        else:
            self.events.put(
                (
                    "error",
                    report.errors[0]
                    if report.errors
                    else "O yt-dlp retornou erro ao processar o link.",
                )
            )

    def _build_options(
        self, config: DownloadConfig, report: _DownloadReport | None = None
    ) -> dict:
        folder = Path(config.folder)
        outtmpl = self._output_template(config)

        has_ffmpeg = ffmpeg_available()
        postprocessors = self._postprocessors(config)
        batch = config.playlist or is_playlist_url(config.url)

        options: dict = {
            "paths": {"home": str(folder)},
            "outtmpl": {"default": outtmpl},
            "format": self._format_selector(config, has_ffmpeg),
            "noplaylist": not config.playlist,
            # Em lote, itens indisponíveis são ignorados em vez de abortar tudo.
            "ignoreerrors": batch,
            "retries": 3,
            "fragment_retries": 5,
            "concurrent_fragment_downloads": 4,
            "continuedl": True,
            "overwrites": False,
            "windowsfilenames": True,
            "noprogress": True,
            "quiet": True,
            "no_warnings": True,
            "consoletitle": False,
            "logger": _QueueLogger(self.events, report),
            "progress_hooks": [functools.partial(self._progress_hook, report=report)],
            "postprocessor_hooks": [self._postprocessor_hook],
        }

        if postprocessors:
            options["postprocessors"] = postprocessors
        if config.embed_thumbnail and config.mode != "mp4":
            options["writethumbnail"] = True
        if config.mode == "mp4":
            options["merge_output_format"] = "mp4"

        return options

    @staticmethod
    def _output_template(config: DownloadConfig) -> str:
        """Caminho relativo usado dentro da pasta escolhida pelo usuário.

        * playlist  -> uma única pasta com o nome da playlist;
        * item único -> uma pasta por vídeo (se a opção estiver marcada).
        """
        base = "%(title).120B [%(id)s].%(ext)s"
        if config.playlist and is_playlist_url(config.url):
            return f"%(playlist_title,playlist_id|Playlist).120B/{base}"
        if config.per_video_folder:
            return f"%(title).120B/{base}"
        return base

    @staticmethod
    def _format_selector(config: DownloadConfig, has_ffmpeg: bool) -> str:
        if config.mode != "mp4":
            return "ba[ext=m4a]/ba/b" if config.mode == "m4a" else "ba/b"

        height = QUALITY_HEIGHTS.get(config.quality)
        limit = f"[height<={height}]" if height else ""
        if has_ffmpeg:
            return f"bv*{limit}[ext=mp4]+ba[ext=m4a]/bv*{limit}+ba/b{limit}/b{limit}/b"
        # Sem FFmpeg não há como juntar vídeo + áudio: usa arquivo progressivo.
        return f"b{limit}[ext=mp4]/b{limit}/b"

    @staticmethod
    def _postprocessors(config: DownloadConfig) -> list[dict]:
        processors: list[dict[str, Any]] = []
        if config.mode == "mp3":
            processors = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": config.bitrate,
                }
            ]
        elif config.mode == "m4a":
            processors = [{"key": "FFmpegExtractAudio", "preferredcodec": "m4a"}]
        else:
            return []

        if config.embed_thumbnail:
            processors.extend(
                [
                    {"key": "FFmpegMetadata", "add_metadata": True},
                    {"key": "EmbedThumbnail", "already_have_thumbnail": False},
                ]
            )
        return processors

    def _progress_hook(self, data: dict, report: _DownloadReport | None = None) -> None:
        if self.cancel_event.is_set():
            raise DownloadCancelled("cancelado pelo usuário")

        status = data.get("status")
        info = data.get("info_dict") or {}

        if status == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            done = data.get("downloaded_bytes") or 0
            percent = min(100.0, done * 100 / total) if total else None
            self.events.put(
                (
                    "progress",
                    {
                        "percent": percent,
                        "speed": data.get("speed"),
                        "eta": data.get("eta"),
                        "total": total,
                        "done": done,
                        "title": info.get("title"),
                        "file": Path(data.get("filename") or "").name,
                    },
                )
            )
        elif status == "finished":
            if report is not None and info.get("id"):
                report.finished_ids.add(str(info["id"]))
            self.events.put(("progress_finished", info.get("title")))

    def _postprocessor_hook(self, data: dict) -> None:
        name = data.get("postprocessor") or ""
        if data.get("status") == "started":
            self.events.put(("postprocessing", name))
        elif data.get("status") == "finished":
            self.events.put(("status", "Finalizando arquivo…"))

    # ---------------------------------------------------------- fila de eventos

    def _poll_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                self._handle_event(kind, payload)
        except queue.Empty:
            pass
        try:
            self.root.after(self.POLL_INTERVAL_MS, self._poll_events)
        except tk.TclError:
            pass

    def _handle_event(self, kind: str, payload: object) -> None:
        if kind == "progress":
            self._render_progress(payload)  # type: ignore[arg-type]
        elif kind == "progress_finished":
            self.progress.configure(value=100)
            self.pct_var.set("100%")
        elif kind == "status":
            self.status_var.set(str(payload))
        elif kind == "postprocessing":
            self._set_indeterminate(True)
            self.status_var.set(f"Processando: {payload}…")
        elif kind == "log":
            self._append_log(str(payload))
        elif kind == "done":
            self._finish(success=True)
        elif kind == "partial":
            self._finish(success=True, partial=payload)  # type: ignore[arg-type]
        elif kind == "cancelled":
            self._finish(success=None)
        elif kind == "error":
            self._finish(success=False, message=str(payload))

    def _render_progress(self, data: dict) -> None:
        percent = data.get("percent")
        if percent is None:
            self._set_indeterminate(True)
        else:
            self._set_indeterminate(False)
            self.progress.configure(value=percent)
            self.pct_var.set(f"{percent:.0f}%")

        parts: list[str] = []
        if data.get("total"):
            parts.append(
                f"{human_bytes(data.get('done'))} de {human_bytes(data.get('total'))}"
            )
        if data.get("speed"):
            parts.append(human_speed(data.get("speed")))
        if data.get("eta") is not None:
            parts.append(f"faltam {human_eta(data.get('eta'))}")
        if not parts and data.get("file"):
            parts.append(str(data["file"]))
        self.detail_var.set("  •  ".join(parts) or "Baixando…")

        title = data.get("title")
        self.status_var.set(f"Baixando: {shorten(title)}" if title else "Baixando…")

    def _finish(
        self,
        success: bool | None,
        message: str = "",
        partial: dict | None = None,
    ) -> None:
        self._set_indeterminate(False)
        self._set_busy(False)

        if success is True and partial:
            count = int(partial.get("count") or 0)
            first = str(partial.get("first") or "")
            self.progress.configure(value=100)
            self.pct_var.set("100%")
            self.status_var.set(f"Concluído com {count} falha(s)")
            self.detail_var.set(
                "Itens indisponíveis foram ignorados — veja o registro."
            )
            self._append_log(
                f"Playlist finalizada com {count} item(ns) que não puderam ser baixados."
            )
            messagebox.showwarning(
                "Playlist concluída com avisos",
                f"{count} item(ns) não puderam ser baixados e foram ignorados.\n\n"
                f"Primeiro erro: {shorten(first, 180)}\n\n"
                "A lista completa está no registro da janela.",
            )
            return

        if success is True:
            self.progress.configure(value=100)
            self.pct_var.set("100%")
            self.status_var.set("Concluído com sucesso")
            self.detail_var.set(f"Salvo em: {self.folder_var.get()}")
            self._append_log("Download concluído.")
        elif success is None:
            self.progress.configure(value=0)
            self.pct_var.set("0%")
            self.status_var.set("Download cancelado")
            self.detail_var.set("Nenhum arquivo foi finalizado.")
            self._append_log("Download cancelado pelo usuário.")
        else:
            self.progress.configure(value=0)
            self.pct_var.set("0%")
            self.status_var.set("Falha no download")
            self.detail_var.set("Veja o registro abaixo para mais detalhes.")
            self._append_log(message)
            first_line = message.splitlines()[0] if message else "Erro inesperado."
            messagebox.showerror(
                "Erro no download",
                f"{shorten(first_line, 200)}\n\nDetalhes completos no registro da janela.",
            )

    # ------------------------------------------------------------------ janela

    def _on_close(self) -> None:
        if self.worker and self.worker.is_alive():
            if not messagebox.askyesno(
                "Sair", "Há um download em andamento.\nDeseja cancelar e sair?"
            ):
                return
            self.cancel_event.set()
            self.worker.join(timeout=2.0)
        self._save_settings()
        self.root.destroy()


def main() -> None:
    enable_high_dpi()
    root = tk.Tk()
    YTDownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
