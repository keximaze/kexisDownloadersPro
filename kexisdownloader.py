#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
kexi's Downloader Pro v2.0 - macOS Native Design

A beautiful, full-featured YouTube downloader with native macOS design. 
All original features preserved + enhanced UX. 
"""

__title__ = "kexi's Downloader Pro"
__version__ = "2.0.0"
__author__ = "mark keximaze"
__license__ = "MIT"

import os
import sys
import re
import shutil
import queue
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import webbrowser

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext
import yt_dlp

# Try to import darkdetect for system theme detection
try:
    import darkdetect
    HAS_DARKDETECT = True
except ImportError:
    HAS_DARKDETECT = False
# ----------------------------------------------------------------------
# Global settings
# ----------------------------------------------------------------------
os.environ["TK_SILENCE_DEPRECATION"] = "1"

# Set appearance mode
ctk.set_appearance_mode("System")  # "System", "Dark", "Light"
ctk.set_default_color_theme("blue")

# ----------------------------------------------------------------------
# Thread-safe log queue
# ----------------------------------------------------------------------
log_queue:  queue.Queue[tuple[str, Any]] = queue.Queue()


def ui_append(tag: str, msg: str | float) -> None:
    """Push a log line / progress value onto the queue."""
    log_queue.put((tag, msg))


# ----------------------------------------------------------------------
# Video / audio format dictionaries
# ----------------------------------------------------------------------
VIDEO_IDS: Dict[str, str] = {
     "Best Quality (Auto)": "best",
    "8K – AV01 – 403": "403",  "8K – AV1 – 416": "416", "8K – AV1 – 417": "417",
    "8K – VP9 – 571": "571", "8K – VP9 – 272": "272",
    "8K – AV1 – 402": "402", "8K – AV1 – 701": "701", "8K – AV1 – 700": "700",
    "4K – AV01 – 401": "401", "4K – VP9 – 315": "315", "4K – VP9 – 337": "337",
    "4K – AV01 – 400": "400", "4K – AV1 – 399": "399",
    "4K – AV01 – 398": "398", "4K – VP9 – 313": "313",
    "1440p – VP9 – 308": "308", "1440p – VP9 – 271": "271", "1440p – VP9 – 336": "336",
    "1440p – AV1 – 302": "302", "1440p – AVC1 – 264": "264",
    "1080p – VP9 – 303": "303", "1080p – VP9 – 248": "248", "1080p – VP9 – 335": "335",
    "1080p – AV1 – 301": "301", "1080p – AVC1 – 137": "137",
    "720p – AVC1 – 136": "136",  "720p – VP9 – 247": "247"
}


AUDIO_IDS_LEFT = {
    "Best Audio (Opus)": "251",
    "High Audio (Opus)": "250",
    "Medium Audio (Opus)": "249",
    "AAC Audio (M4A)": "140",
    "Low Audio (AAC)": "139",
}

AUDIO_CODECS_RIGHT = ["mp3", "flac", "alac", "wav", "m4a", "opus", "ogg"]


# ----------------------------------------------------------------------
# Find yt-dlp binary
# ----------------------------------------------------------------------
def find_yt_dlp() -> str:
    """Return the absolute path to the yt-dlp executable."""
    if getattr(sys, "frozen", False):
        bundle_dir = Path(
            sys._MEIPASS if hasattr(sys, "_MEIPASS") else sys.executable
        ).parent
        candidate = bundle_dir. parent / "Resources" / "bin" / "yt-dlp"
        if candidate.exists():
            return str(candidate)
        candidate = bundle_dir / "bin" / "yt-dlp"
        if candidate.exists():
            return str(candidate)

    venv_path = Path(__file__).parent / "venv" / "bin" / "yt-dlp"
    if venv_path.exists():
        return str(venv_path)

    exe = shutil.which("yt-dlp") or shutil.which("yt_dlp. exe")
    if not exe:
        raise FileNotFoundError(
            "yt-dlp not found. Install it with `pip install yt-dlp`."
        )
    return exe


YTDLP_EXE = find_yt_dlp()


# ----------------------------------------------------------------------
# URL validation
# ----------------------------------------------------------------------
URL_RE = re.compile(r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$")


def clean_list(text: str) -> list[str]:
    """Extract YouTube URLs from multi-line string."""
    raw = [x.strip() for x in text.splitlines() if x.strip()]
    urls:  list[str] = []
    ignored:  list[str] = []

    for line in raw:
        if (
            line.startswith("=")
            or line.startswith("-")
            or "DOWNLOAD" in line. upper()
            or "RUNNING" in line.upper()
            or "COMMAND:" in line. upper()
            or line.startswith("Paste")
            or line.startswith("[")
            or "✅" in line
            or "❌" in line
        ):
            continue

        if URL_RE.match(line):
            urls.append(line)
        else:
            ignored.append(line)

    if ignored:
        messagebox.showwarning(
            "Invalid URLs",
            "These lines were ignored:\n"
            + "\n".join(ignored[: 5])
            + (f"\n… and {len(ignored)-5} more" if len(ignored) > 5 else ""),
        )
    return urls


# ----------------------------------------------------------------------
# Core download routine
# ----------------------------------------------------------------------
def run_download(
    url: str,
    out:  Path,
    *,
    audio:  bool = False,
    audio_id: str | None = None,
    video_id: str | None = None,
    right_codec: str | None = None,
    cookies_path: str | None = None,
    tag: str = "Job",
    proc_ref: Optional["DownloadWorker"] = None,
) -> bool:
    """Build the yt-dlp command and run it."""
    out_tpl = str(out / "%(title)s.%(ext)s")

    if audio:
        fmt = "bestaudio"
        cmd = [
            YTDLP_EXE,
            "--remote-components", "ejs: github",
            "-f", fmt,
            "--extract-audio",
            "--audio-format", right_codec or "mp3",
            "--audio-quality", "0",
            "--newline",
            "-o", out_tpl,
            url,
        ]
    else:
        if video_id and video_id != "best":
            if audio_id:
                fmt = f"{video_id}+{audio_id}/bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
            else:
                fmt = f"{video_id}+bestaudio/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best"
        else:
            fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"

        cmd = [
            YTDLP_EXE,
            "--remote-components", "ejs:github",
            "-f", fmt,
            "--merge-output-format", "mp4",
            "--newline",
            "-o", out_tpl,
            url,
        ]

    if cookies_path:
        cp = Path(cookies_path).expanduser()
        if cp.is_file():
            cmd.extend(["--cookies", str(cp)])
        else:
            cmd.extend(["--cookies-from-browser", "chrome"])

    ui_append(tag, f"Running command:\n{' '.join(cmd)}\n")

    creation_flags = 0
    if os.name == "nt": 
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    proc = None
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess. PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=creation_flags,
        )
        if proc_ref:
            proc_ref. current_proc = proc

        if proc.stdout:
            for line in proc.stdout:
                line = line.rstrip()
                if "[download]" in line and "%" in line:
                    try:
                        percent = float(line.split("%")[0].split()[-1])
                        ui_append("progress", percent)
                    except Exception:
                        pass
                ui_append(tag, line)

                if proc_ref and proc_ref.stop_flag:
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                    break

        proc.wait()
        return proc.returncode == 0

    except Exception as exc:
        ui_append(tag, f"[EXCEPTION] {exc}")
        return False
    finally:
        if proc_ref:
            proc_ref. current_proc = None
        if proc and proc.stdout:
            try:
                proc.stdout.close()
            except Exception:
                pass


# ----------------------------------------------------------------------
# Worker thread
# ----------------------------------------------------------------------
class DownloadWorker(threading.Thread):
    """Thread that processes download jobs."""

    def __init__(self, jobs: List[Tuple[str, dict]], *, tag: str) -> None:
        super().__init__(daemon=True)
        self.jobs = jobs
        self.tag = tag
        self.stop_flag = False
        self.current_proc:  Optional[subprocess.Popen] = None

    def stop(self) -> None:
        """Stop the worker."""
        self.stop_flag = True
        if self.current_proc:
            try:
                self.current_proc.terminate()
            except Exception:
                try:
                    self.current_proc.kill()
                except Exception:
                    pass

    def run(self) -> None:
        for url, opts in self.jobs:
            if self.stop_flag:
                ui_append(self.tag, "\n=== CANCELLED ===\n")
                return
            ok = run_download(url, **opts, tag=self.tag, proc_ref=self)
            ui_append(self.tag, f"\n{'✅' if ok else '❌'} Finished:  {url}\n")
        ui_append(self.tag, "\n=== ALL DONE ===\n")


# ----------------------------------------------------------------------
# Main Application
# ----------------------------------------------------------------------
class kexisdownloader(ctk.CTk):
    """Main application with beautiful macOS design."""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("⚡ kexi's Downloader Pro")
        self.geometry("1100x800")
        self.minsize(900, 700)

        # Colors
        self.accent_color = "#5A524A"
        self.last_download_folder = None

        # Worker references
        self.video_workers = []
        self.audio_workers = []

        # Log widgets
        self._log_widgets:  Dict[str, tk.Text] = {}

        # Setup UI
        self._setup_menu()
        self._setup_ui()

        # Start log polling
        self._poll_log()

        # Bind keyboard shortcuts
        self. bind("<Command-d>", lambda e: self._start_current_download())
        self.bind("<Command-k>", lambda e: self._show_format_checker())
        self.bind("<Command-comma>", lambda e: self._show_preferences())
        self.bind("<Command-q>", lambda e: self. quit())

        print("✅ kexi's Downloader Pro v2.0 initialized")

    # ------------------------------------------------------------------
    def _setup_menu(self):
        """Setup macOS-style menu bar."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Downloads Folder", command=self._open_downloads_folder, accelerator="⌘O")
        file_menu.add_separator()
        file_menu.add_command(label="Preferences.. .", command=self._show_preferences, accelerator="⌘,")
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.quit, accelerator="⌘Q")

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Clear Logs", command=self._clear_logs)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Dark Mode", command=self._toggle_dark_mode)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Check Formats", command=self._show_format_checker, accelerator="⌘K")

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About kexi's Downloader", command=self._show_about)

        # Bind menu shortcuts
        self.bind("<Command-o>", lambda e: self._open_downloads_folder())

    # ------------------------------------------------------------------
    def _setup_ui(self):
        """Setup the main UI."""
        # Header with title
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ctk. CTkLabel(
            header,
            text="⚡ kexi's Downloader Pro",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(side="left")

        # Dark mode toggle
        self.dark_mode_switch = ctk.CTkSwitch(
            header,
            text="🌓 Dark Mode",
            command=self._toggle_dark_mode,
            font=ctk.CTkFont(size=12)
        )
        self.dark_mode_switch.pack(side="right", padx=10)
        if ctk.get_appearance_mode() == "Dark":
            self. dark_mode_switch.select()

        # Tabview
        self.tabview = ctk.CTkTabview(self, corner_radius=15)
        self.tabview. pack(fill="both", expand=True, padx=20, pady=10)

        # Add tabs
        self.tabview.add("📹 Video")
        self.tabview.add("🎵 Audio")

        # Build tabs
        self._build_video_tab()
        self._build_audio_tab()

        # Progress bar at bottom
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame. pack(fill="x", padx=20, pady=(0, 20))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            variable=self.progress_var,
            mode="determinate",
            height=20,
            corner_radius=10
        )
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to download",
            font=ctk.CTkFont(size=11)
        )
        self.progress_label.pack()

    # ------------------------------------------------------------------
    def _build_video_tab(self):
        """Build the video download tab."""
        tab = self.tabview.tab("📹 Video")

        # URL section
        url_frame = ctk.CTkFrame(tab, corner_radius=15)
        url_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            url_frame,
            text="📝 Paste YouTube URLs (one per line):",
            font=ctk. CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))

        # Log text box with terminal style
        self.video_log_text = tk.Text(
            url_frame,
            wrap="word",
            height=10,
            font=("SF Mono", 11),
            bg="#1E1E1E" if ctk.get_appearance_mode() == "Dark" else "#F5F5F5",
            fg="#A8FF60" if ctk.get_appearance_mode() == "Dark" else "#2E7D32",
            relief="flat",
            borderwidth=0,
            insertbackground="#A8FF60",
            selectbackground="#3A3A3A",
            padx=10,
            pady=10
        )
        self.video_log_text.pack(fill="both", expand=True, padx=15, pady=(5, 10))
        self.video_log_text.insert("1.0", "Paste YouTube URLs here, one per line.\n\n")
        self._log_widgets["VIDEO"] = self.video_log_text

        # Right-click menu for log
        self._add_log_context_menu(self.video_log_text)

        # Controls frame
        controls_frame = ctk.CTkFrame(tab, corner_radius=15)
        controls_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Output folder
        ctk.CTkLabel(
            controls_frame,
            text="📁 Output Folder:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))

        folder_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        folder_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.video_folder_entry = ctk. CTkEntry(
            folder_frame,
            placeholder_text=str(Path.home() / "Downloads"),
            height=35,
            corner_radius=8
        )
        self.video_folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.video_folder_entry.insert(0, str(Path.home() / "Downloads"))

        ctk.CTkButton(
            folder_frame,
            text="Browse",
            width=100,
            height=35,
            corner_radius=8,
            command=lambda: self._browse_folder(self.video_folder_entry)
        ).pack(side="left")

        # Quality settings in a grid
        quality_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        quality_frame.pack(fill="x", padx=15, pady=(0, 15))

        # Video quality
        ctk.CTkLabel(
            quality_frame,
            text="🎬 Video Quality:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.video_quality_var = ctk.StringVar(value=list(VIDEO_IDS.keys())[0])
        video_quality_menu = ctk. CTkOptionMenu(
            quality_frame,
            variable=self.video_quality_var,
            values=list(VIDEO_IDS.keys()),
            width=250,
            height=35,
            corner_radius=8
        )
        video_quality_menu.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        # Audio quality
        ctk.CTkLabel(
            quality_frame,
            text="🎵 Audio Quality:",
            font=ctk. CTkFont(size=12, weight="bold")
        ).grid(row=0, column=1, sticky="w", pady=(0, 5))

        self.video_audio_var = ctk. StringVar(value=list(AUDIO_IDS_LEFT.keys())[0])
        audio_quality_menu = ctk.CTkOptionMenu(
            quality_frame,
            variable=self.video_audio_var,
            values=list(AUDIO_IDS_LEFT.keys()),
            width=250,
            height=35,
            corner_radius=8
        )
        audio_quality_menu.grid(row=1, column=1, sticky="ew")

        quality_frame.columnconfigure(0, weight=1)
        quality_frame.columnconfigure(1, weight=1)

        # Buttons
        button_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            button_frame,
            text="🔍 Check Formats",
            height=40,
            corner_radius=10,
            fg_color="#4A90E2",
            hover_color="#357ABD",
            command=self._show_format_checker
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            height=40,
            corner_radius=10,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self._cancel_video
        ).pack(side="left", fill="x", expand=True, padx=5)

        ctk.CTkButton(
            button_frame,
            text="⚡ Download Video",
            height=40,
            corner_radius=10,
            fg_color="#27AE60",
            hover_color="#229954",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start_video
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))

    # ------------------------------------------------------------------
    def _build_audio_tab(self):
        """Build the audio download tab."""
        tab = self.tabview. tab("🎵 Audio")

        # URL section
        url_frame = ctk.CTkFrame(tab, corner_radius=15)
        url_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            url_frame,
            text="📝 Paste YouTube URLs (one per line):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))

        # Log text box
        self.audio_log_text = tk.Text(
            url_frame,
            wrap="word",
            height=10,
            font=("SF Mono", 11),
            bg="#1E1E1E" if ctk.get_appearance_mode() == "Dark" else "#F5F5F5",
            fg="#A8FF60" if ctk.get_appearance_mode() == "Dark" else "#2E7D32",
            relief="flat",
            borderwidth=0,
            insertbackground="#A8FF60",
            selectbackground="#3A3A3A",
            padx=10,
            pady=10
        )
        self.audio_log_text.pack(fill="both", expand=True, padx=15, pady=(5, 10))
        self.audio_log_text.insert("1.0", "Paste YouTube URLs here, one per line.\n\n")
        self._log_widgets["AUDIO"] = self.audio_log_text

        # Right-click menu
        self._add_log_context_menu(self.audio_log_text)

        # Controls
        controls_frame = ctk. CTkFrame(tab, corner_radius=15)
        controls_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Output folder
        ctk.CTkLabel(
            controls_frame,
            text="📁 Output Folder:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))

        folder_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        folder_frame. pack(fill="x", padx=15, pady=(0, 10))

        self.audio_folder_entry = ctk.CTkEntry(
            folder_frame,
            placeholder_text=str(Path.home() / "Downloads"),
            height=35,
            corner_radius=8
        )
        self.audio_folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.audio_folder_entry.insert(0, str(Path.home() / "Downloads"))

        ctk.CTkButton(
            folder_frame,
            text="Browse",
            width=100,
            height=35,
            corner_radius=8,
            command=lambda:  self._browse_folder(self. audio_folder_entry)
        ).pack(side="left")

        # Audio codec
        ctk.CTkLabel(
            controls_frame,
            text="🎧 Audio Format:",
            font=ctk. CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.audio_codec_var = ctk.StringVar(value=AUDIO_CODECS_RIGHT[0])
        codec_menu = ctk.CTkOptionMenu(
            controls_frame,
            variable=self.audio_codec_var,
            values=AUDIO_CODECS_RIGHT,
            width=250,
            height=35,
            corner_radius=8
        )
        codec_menu.pack(anchor="w", padx=15, pady=(0, 15))

        # Buttons
        button_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            height=40,
            corner_radius=10,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            command=self._cancel_audio
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(
            button_frame,
            text="⚡ Download Audio",
            height=40,
            corner_radius=10,
            fg_color="#27AE60",
            hover_color="#229954",
            font=ctk. CTkFont(size=14, weight="bold"),
            command=self._start_audio
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))

    # ------------------------------------------------------------------
    def _add_log_context_menu(self, text_widget):
        """Add right-click context menu to log widget."""
        menu = tk.Menu(text_widget, tearoff=0)
        menu.add_command(label="Copy All", command=lambda: self._copy_log(text_widget))
        menu.add_command(label="Clear Log", command=lambda: self._clear_single_log(text_widget))
        menu.add_separator()
        menu.add_command(label="Select All", command=lambda: text_widget.tag_add("sel", "1.0", "end"))

        def show_menu(event):
            menu.tk_popup(event.x_root, event.y_root)

        text_widget.bind("<Button-2>", show_menu)  # Right-click on Mac
        text_widget.bind("<Control-Button-1>", show_menu)  # Ctrl+click

    # ------------------------------------------------------------------
    def _copy_log(self, widget):
        """Copy log contents to clipboard."""
        content = widget.get("1.0", "end-1c")
        self. clipboard_clear()
        self.clipboard_append(content)
        self.progress_label.configure(text="✅ Log copied to clipboard!")
        self.after(2000, lambda: self.progress_label.configure(text="Ready to download"))

    # ------------------------------------------------------------------
    def _clear_single_log(self, widget):
        """Clear a single log widget."""
        widget.delete("1.0", "end")
        widget.insert("1.0", "Paste YouTube URLs here, one per line.\n\n")

    # ------------------------------------------------------------------
    def _clear_logs(self):
        """Clear all logs."""
        for widget in self._log_widgets.values():
            widget.delete("1.0", "end")
            widget.insert("1.0", "Paste YouTube URLs here, one per line.\n\n")

    # ------------------------------------------------------------------
    def _browse_folder(self, entry_widget):
        """Browse for output folder."""
        folder = filedialog.askdirectory()
        if folder:
            entry_widget.delete(0, "end")
            entry_widget. insert(0, folder)

    # ------------------------------------------------------------------
    def _toggle_dark_mode(self):
        """Toggle between light and dark mode."""
        current = ctk.get_appearance_mode()
        new_mode = "Light" if current == "Dark" else "Dark"
        ctk. set_appearance_mode(new_mode)

        # Update log colors
        bg = "#1E1E1E" if new_mode == "Dark" else "#F5F5F5"
        fg = "#A8FF60" if new_mode == "Dark" else "#2E7D32"

        for widget in self._log_widgets. values():
            widget.configure(bg=bg, fg=fg)

    # ------------------------------------------------------------------
    def _poll_log(self):
        """Poll the log queue and update UI."""
        try:
            while True:
                tag, line = log_queue.get_nowait()
                widget = self._log_widgets. get(tag)

                if tag == "progress":
                    self.progress_var.set(line / 100)
                    self.progress_label.configure(text=f"Downloading...  {int(line)}%")
                    continue

                if widget: 
                    widget.insert("end", line + "\n")
                    widget. see("end")
        except queue.Empty:
            pass
        self.after(100, self._poll_log)

    # ------------------------------------------------------------------
    def _find_cookies_file(self) -> Optional[str]:
        """Search for cookies. txt file."""
        for p in (
            Path.home() / "Downloads" / "cookies.txt",
            Path.cwd() / "cookies.txt",
            Path.home() / "cookies.txt",
        ):
            if p.is_file():
                return str(p)
        return None

    # ------------------------------------------------------------------
    def _ensure_folder(self, path_str: str) -> Path:
        """Ensure output folder exists."""
        if not path_str: 
            path_str = str(Path.home() / "Downloads")
        p = Path(path_str).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        self.last_download_folder = p
        return p

    # ------------------------------------------------------------------
    def _start_video(self):
        """Start video download."""
        content = self.video_log_text.get("1.0", "end-1c")
        urls = clean_list(content)
        if not urls:
            messagebox.showerror("Error", "No video URLs entered.")
            return

        out_folder = self._ensure_folder(self.video_folder_entry.get())
        cookies_path = self._find_cookies_file()

        self.video_log_text.insert("end", "\n" + "=" * 60 + "\n")
        self.video_log_text.insert("end", "DOWNLOAD STARTED\n")
        self.video_log_text.insert("end", "=" * 60 + "\n")
        self.video_log_text.see("end")

        jobs:  List[Tuple[str, dict]] = []
        for u in urls:
            jobs.append(
                (
                    u,
                    dict(
                        out=out_folder,
                        audio=False,
                        video_id=VIDEO_IDS[self.video_quality_var.get()],
                        audio_id=AUDIO_IDS_LEFT[self.video_audio_var.get()],
                        cookies_path=cookies_path,
                    ),
                )
            )

        w = DownloadWorker(jobs, tag="VIDEO")
        self.video_workers = [w]
        w.start()

        # Show open folder button after completion
        self.after(2000, self._check_download_complete)

    # ------------------------------------------------------------------
    def _start_audio(self):
        """Start audio download."""
        content = self.audio_log_text. get("1.0", "end-1c")
        urls = clean_list(content)
        if not urls:
            messagebox.showerror("Error", "No audio URLs entered.")
            return

        out_folder = self._ensure_folder(self.audio_folder_entry.get())
        cookies_path = self._find_cookies_file()

        self.audio_log_text.insert("end", "\n" + "=" * 60 + "\n")
        self.audio_log_text.insert("end", "DOWNLOAD STARTED\n")
        self.audio_log_text. insert("end", "=" * 60 + "\n")
        self.audio_log_text. see("end")

        jobs: List[Tuple[str, dict]] = []
        for u in urls:
            jobs.append(
                (
                    u,
                    dict(
                        out=out_folder,
                        audio=True,
                        right_codec=self.audio_codec_var.get(),
                        cookies_path=cookies_path,
                    ),
                )
            )

        w = DownloadWorker(jobs, tag="AUDIO")
        self.audio_workers = [w]
        w. start()

        self.after(2000, self._check_download_complete)

    # ------------------------------------------------------------------
    def _check_download_complete(self):
        """Check if downloads are complete and show open folder button."""
        active_workers = [w for w in (self.video_workers + self. audio_workers) if w.is_alive()]
        if not active_workers and self.last_download_folder:
            result = messagebox.askyesno(
                "Download Complete! ",
                "Downloads finished!  Open the folder?"
            )
            if result: 
                self._open_specific_folder(self.last_download_folder)

    # ------------------------------------------------------------------
    def _cancel_video(self):
        """Cancel video download."""
        if self.video_workers:
            self.video_workers[-1].stop()
            messagebox.showinfo("Cancelled", "Video download cancelled.")
        else:
            messagebox.showinfo("Info", "No active video download.")

    # ------------------------------------------------------------------
    def _cancel_audio(self):
        """Cancel audio download."""
        if self.audio_workers:
            self.audio_workers[-1].stop()
            messagebox.showinfo("Cancelled", "Audio download cancelled.")
        else:
            messagebox.showinfo("Info", "No active audio download.")

    # ------------------------------------------------------------------
    def _start_current_download(self):
        """Start download for current tab (keyboard shortcut)."""
        current_tab = self.tabview. get()
        if "Video" in current_tab:
            self._start_video()
        else:
            self._start_audio()

    # ------------------------------------------------------------------
    def _show_format_checker(self):
        """Show the format checker window."""
        # Get URL from current tab
        current_tab = self.tabview. get()
        if "Video" in current_tab: 
            content = self.video_log_text.get("1.0", "end-1c")
        else:
            content = self. audio_log_text.get("1.0", "end-1c")

        urls = [line.strip() for line in content. splitlines() if line.strip() and URL_RE.match(line. strip())]
        url = urls[0] if urls else ""

        FormatCheckerWindow(self, url)

    # ------------------------------------------------------------------
    def _open_downloads_folder(self):
        """Open the default downloads folder."""
        folder = Path.home() / "Downloads"
        self._open_specific_folder(folder)

    # ------------------------------------------------------------------
    def _open_specific_folder(self, folder: Path):
        """Open a specific folder in Finder/Explorer."""
        if sys.platform == "darwin": 
            subprocess.run(["open", str(folder)])
        elif sys.platform == "win32":
            os.startfile(str(folder))
        else:
            subprocess.run(["xdg-open", str(folder)])

    # ------------------------------------------------------------------
    def _show_preferences(self):
        """Show preferences window."""
        PreferencesWindow(self)

    # ------------------------------------------------------------------
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About kexi's Downloader Pro",
            f"{__title__} v{__version__}\n\n"
            f"A beautiful, full-featured YouTube downloader\n"
            f"with native macOS design.\n\n"
            f"Created by {__author__}\n"
            f"License: {__license__}"
        )


# ----------------------------------------------------------------------
# Format Checker Window (YOUR PRECIOUS FEATURE!)
# ----------------------------------------------------------------------
class FormatCheckerWindow(ctk.CTkToplevel):
    """Format checker window with all your original features + enhancements."""

    def __init__(self, parent, default_url=""):
        super().__init__(parent)

        self.title("🔍 Format Checker - kexi's Downloader Pro")
        self.geometry("1100x750")
        self.minsize(900, 600)

        # URL input
        url_frame = ctk.CTkFrame(self, corner_radius=15)
        url_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            url_frame,
            text="📺 YouTube URL:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))

        url_input_frame = ctk.CTkFrame(url_frame, fg_color="transparent")
        url_input_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.url_entry = ctk.CTkEntry(
            url_input_frame,
            placeholder_text="Paste YouTube URL here...",
            height=40,
            corner_radius=10
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        if default_url:
            self. url_entry.insert(0, default_url)

        ctk.CTkButton(
            url_input_frame,
            text="🔍 Check Formats",
            width=150,
            height=40,
            corner_radius=10,
            fg_color="#4A90E2",
            hover_color="#357ABD",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._fetch_formats
        ).pack(side="left")

        # Filter controls
        filter_frame = ctk.CTkFrame(self, corner_radius=15)
        filter_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            filter_frame,
            text="🔽 Filter:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=(15, 10))

        self.filter_var = ctk.StringVar(value="all")

        filters = [
            ("All Formats", "all"),
            ("Audio Only", "audio"),
            ("High Audio ≥256kbps", "high_audio"),
            ("Best Audio ≥480kbps", "highest_audio"),
            ("Video Only", "video"),
        ]

        for text, value in filters:
            ctk. CTkRadioButton(
                filter_frame,
                text=text,
                variable=self.filter_var,
                value=value,
                command=self._apply_filter
            ).pack(side="left", padx=5)

        # Info label
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20)

        ctk.CTkLabel(
            info_frame,
            text="💡 Tip: YouTube max audio bitrates - Stereo:  384kbps, 5.1: 512kbps",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w")

        # Results text box
        results_frame = ctk.CTkFrame(self, corner_radius=15)
        results_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        self.results_text = tk.Text(
            results_frame,
            wrap="none",
            font=("SF Mono", 10),
            bg="#1E1E1E" if ctk.get_appearance_mode() == "Dark" else "#F5F5F5",
            fg="#A8FF60" if ctk.get_appearance_mode() == "Dark" else "#2E7D32",
            relief="flat",
            borderwidth=0,
            padx=15,
            pady=15
        )
        self.results_text.pack(fill="both", expand=True, padx=2, pady=2)

        # Add context menu
        self._add_context_menu()

        self.raw_output = ""

    # ------------------------------------------------------------------
    def _add_context_menu(self):
        """Add right-click context menu."""
        menu = tk.Menu(self. results_text, tearoff=0)
        menu.add_command(label="Copy All", command=self._copy_all)
        menu.add_command(label="Copy Selected", command=self._copy_selected)
        menu.add_separator()
        menu.add_command(label="Clear", command=lambda: self. results_text.delete("1.0", "end"))

        def show_menu(event):
            menu.tk_popup(event.x_root, event. y_root)

        self.results_text.bind("<Button-2>", show_menu)
        self.results_text.bind("<Control-Button-1>", show_menu)

    # ------------------------------------------------------------------
    def _copy_all(self):
        """Copy all text to clipboard."""
        content = self.results_text.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(content)

    # ------------------------------------------------------------------
    def _copy_selected(self):
        """Copy selected text to clipboard."""
        try:
            content = self.results_text.get("sel.first", "sel.last")
            self.clipboard_clear()
            self.clipboard_append(content)
        except tk.TclError:
            pass

    # ------------------------------------------------------------------
    def _fetch_formats(self):
        """Fetch formats using yt-dlp."""
        url = self.url_entry.get().strip()
        if not url or not URL_RE.match(url):
            messagebox.showerror("Invalid URL", "Please enter a valid YouTube URL.")
            return

        self.results_text.delete("1.0", "end")
        self.results_text.insert("1.0", "⏳ Fetching formats from YouTube...\n\n")

        def worker():
            cmd = [YTDLP_EXE, "--remote-components", "ejs: github", "-F", url]

            try:
                creation_flags = 0
                if os.name == "nt": 
                    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=creation_flags,
                )

                raw_lines = []
                if proc.stdout:
                    for ln in proc.stdout:
                        raw_lines.append(ln. rstrip())

                self.raw_output = "\n".join(raw_lines)
                self.after(0, self._apply_filter)
                proc.wait()
            except Exception as exc:
                self.after(0, lambda: self.results_text.insert("end", f"\n❌ Error: {exc}\n"))

        threading.Thread(target=worker, daemon=True).start()

    # ------------------------------------------------------------------
    def _apply_filter(self):
        """Apply the selected filter to the results."""
        if not self.raw_output:
            return

        filtered = self._parse_and_filter(self.raw_output, self.filter_var.get())
        self.results_text. delete("1.0", "end")
        self.results_text.insert("1.0", filtered)

    # ------------------------------------------------------------------
    def _parse_and_filter(self, output: str, filter_type: str) -> str:
        """Parse and filter format output with quality indicators."""
        lines = output.split("\n")
        result = []
        audio_formats = []

        # Find header
        start = -1
        for i, line in enumerate(lines):
            if "ID" in line and "EXT" in line and "RESOLUTION" in line:
                start = i
                break
        if start == -1:
            return output

        result.extend(lines[: start + 2])

        # Process formats
        for line in lines[start + 2:]:
            if not line.strip():
                continue
            low = line.lower()
            bitrate = 0
            m = re.search(r"(\d+)k", low)
            if m:
                bitrate = int(m.group(1))

            is_audio = "audio only" in low
            is_video = ("video only" in low) or ("x" in low and not is_audio)

            # Add quality indicator
            indicator = ""
            if is_audio: 
                if bitrate >= 480:
                    indicator = " 🟢 EXCELLENT"
                elif bitrate >= 256:
                    indicator = " 🟡 VERY GOOD"
                elif bitrate >= 160:
                    indicator = " 🟠 GOOD"
                else:
                    indicator = " 🔴 MEDIUM"

            modified_line = line + indicator if indicator else line

            if filter_type == "all":
                result.append(modified_line)
            elif filter_type == "audio" and is_audio:
                result.append(modified_line)
                audio_formats.append((bitrate, line))
            elif filter_type == "high_audio" and is_audio and bitrate >= 256:
                result.append(modified_line)
                audio_formats.append((bitrate, line))
            elif filter_type == "highest_audio" and is_audio and bitrate >= 480:
                result. append(modified_line)
                audio_formats.append((bitrate, line))
            elif filter_type == "video" and is_video:
                result.append(modified_line)

        # Audio summary
        if filter_type in {"audio", "high_audio", "highest_audio"} and audio_formats:
            audio_formats.sort(reverse=True)
            result.append("\n" + "=" * 80)
            result.append("📊 AUDIO QUALITY SUMMARY:")
            result.append("=" * 80)

            max_br = audio_formats[0][0]
            result.append(f"🎵 Highest available bitrate: {max_br} kbps")
            if max_br >= 480:
                result.append("✅ EXCELLENT – near YouTube's max (512 kbps 5.1)")
            elif max_br >= 256:
                result.append("✅ VERY GOOD – high-quality stereo (max 384 kbps)")
            elif max_br >= 160:
                result.append("✓ GOOD – standard quality")
            else:
                result. append("⚠ MEDIUM – lower-quality audio")

            result.append(f"\n📋 Found {len(audio_formats)} audio format(s)")
            result.append("\n💡 Recommended:  Use format ID {audio_formats[0][1]. split()[0]} for best quality")

        return "\n".join(result)


# ----------------------------------------------------------------------
# Preferences Window
# ----------------------------------------------------------------------
class PreferencesWindow(ctk.CTkToplevel):
    """Preferences window."""

    def __init__(self, parent):
        super().__init__(parent)

        self.title("⚙️ Preferences")
        self.geometry("600x400")
        self.minsize(500, 300)

        # Title
        ctk.CTkLabel(
            self,
            text="⚙️ Preferences",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=20)

        # Settings frame
        settings_frame = ctk.CTkFrame(self, corner_radius=15)
        settings_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ctk.CTkLabel(
            settings_frame,
            text="🎨 Appearance",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            settings_frame,
            text="Theme:",
            font=ctk. CTkFont(size=13)
        ).pack(anchor="w", padx=20, pady=(10, 5))

        theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        theme_menu = ctk.CTkOptionMenu(
            settings_frame,
            variable=theme_var,
            values=["System", "Light", "Dark"],
            command=lambda choice: ctk.set_appearance_mode(choice),
            width=200,
            height=35,
            corner_radius=8
        )
        theme_menu.pack(anchor="w", padx=20, pady=(0, 20))

        # Info
        ctk.CTkLabel(
            settings_frame,
            text="More preferences coming soon!  🚀",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=20)


# ----------------------------------------------------------------------
# Run the app
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app = kexisdownloader()
    app.mainloop()
