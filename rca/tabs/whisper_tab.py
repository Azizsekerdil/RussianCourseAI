# -*- coding: utf-8 -*-
"""Whisper Konusma Tanima sayfasi.

Ic sekmeler:
  * Dosya      - ses/video dosyasini (ya da bir klasoru) yaziya dok / Ingilizceye cevir,
                 dil algila, kelime guveni renklendirmesi, TXT/SRT/VTT/TSV/JSON/LRC disa aktar.
  * Mikrofon   - kaydet + yaziya dok, WAV kaydet, canli dikte.
  * Telaffuz   - hedef cumleyi soyle, kelime kelime karsilastirma ve puan.
  * Ayarlar    - Whisper'in tum kod cozme / VAD / toplu cikarim ayarlari.

Model ayni anda yalnizca bir kez yuklenir (rca.whisper_engine.shared_engine).
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import rca_common as C
from rca import whisper_engine as W
from rca.ui_util import LazyTab, ScrollFrame, style_text

AUDIO_TYPES = [("Ses / video", "*.mp3 *.wav *.m4a *.ogg *.opus *.flac *.aac *.wma *.webm *.mp4 *.mkv *.mov *.avi"),
               ("Tum dosyalar", "*.*")]
MEDIA_EXT = {".mp3", ".wav", ".m4a", ".ogg", ".opus", ".flac", ".aac", ".wma", ".webm",
             ".mp4", ".mkv", ".mov", ".avi"}


def open_path(path: Path) -> None:
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))                       # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass


def batch_targets(f: Path, files, taken: set) -> tuple:
    """Toplu islemde `f` icin (.srt, .txt) hedef yollari - hicbir dosyanin ustune yazmaz.

    Oncelik: "ders01.srt" (eski davranis); ayni klasorde ayni adli baska bir medya
    varsa (a.mp3 / a.mp4) ya da hedeflerden biri zaten varsa (or. dersin orijinal
    metni "ders01.txt") "ders01.mp3.srt", sonra "ders01.mp3.whisper.srt", ...
    `taken` bu calismada secilen yollari tutar ve guncellenir.
    """
    clash = any(o != f and o.parent == f.parent and o.stem.lower() == f.stem.lower() for o in files)
    bases = ([] if clash else [f.with_suffix("")]) + [f, f.with_name(f.name + ".whisper")]
    n = 2
    while True:
        for base in bases:
            srt, txt = base.with_name(base.name + ".srt"), base.with_name(base.name + ".txt")
            keys = {str(srt).lower(), str(txt).lower()}
            if not (keys & taken) and not srt.exists() and not txt.exists():
                taken.update(keys)
                return srt, txt
        bases = [f.with_name(f"{f.name}.whisper{n}")]
        n += 1


class WhisperTab(LazyTab):
    """Whisper (faster-whisper) ile cevrimdisi konusma tanima."""

    # ------------------------------------------------------------------ kurulum
    def build(self) -> None:
        self.engine = W.shared_engine()
        self.opts = W.WhisperOptions.from_dict(self.app.settings.get("whisper") or {})
        self.cancel = threading.Event()
        self.busy = False
        self.transcript = None
        self.rec = None
        self.live = None
        self.pron_tr = None

        root = ttk.Frame(self, padding=(4, 4))
        root.pack(fill="both", expand=True)

        # --- ust bar: model / aygit ------------------------------------------
        top = ttk.Frame(root)
        top.pack(fill="x")
        ttk.Label(top, text=self.t("wh.model")).pack(side="left")
        self.model_var = tk.StringVar(value=self.opts.model)
        self.model_box = ttk.Combobox(top, textvariable=self.model_var, state="readonly", width=20,
                                      values=W.available_models())
        self.model_box.pack(side="left", padx=(4, 10))
        self.model_box.bind("<<ComboboxSelected>>", lambda _e: self._on_model_pick())
        ttk.Label(top, text=self.t("wh.device")).pack(side="left")
        self.device_var = tk.StringVar(value=self.opts.device)
        ttk.Combobox(top, textvariable=self.device_var, state="readonly", width=6,
                     values=W.DEVICES).pack(side="left", padx=(4, 10))
        ttk.Label(top, text=self.t("wh.compute")).pack(side="left")
        self.compute_var = tk.StringVar(value=self.opts.compute_type)
        ttk.Combobox(top, textvariable=self.compute_var, state="readonly", width=12,
                     values=W.COMPUTE_TYPES).pack(side="left", padx=(4, 10))
        top2 = ttk.Frame(root)
        top2.pack(fill="x", pady=(6, 0))
        self.btn_dl = ttk.Button(top2, text=self.t("wh.download"), command=self.download_model)
        self.btn_dl.pack(side="left")
        ttk.Button(top2, text=self.t("wh.load"), command=self.preload).pack(side="left", padx=4)
        ttk.Button(top2, text=self.t("wh.unload"), command=self.unload).pack(side="left")
        ttk.Button(top2, text="📂", width=3, command=lambda: open_path(W.MODELS_DIR)).pack(side="left", padx=4)

        self.status_lbl = ttk.Label(root, text="", style="Dim.TLabel")
        self.status_lbl.pack(fill="x", pady=(6, 2))
        self.model_info = ttk.Label(root, text="", style="Mute.TLabel")
        self.model_info.pack(fill="x")

        ok, why = W.installed(), ""
        if not ok:
            ttk.Label(root, style="Warn.TLabel", justify="left",
                      text=self.t("wh.not_installed")).pack(anchor="w", pady=10)

        self.nb = ttk.Notebook(root)
        self.nb.pack(fill="both", expand=True, pady=(8, 0))
        self._build_file(ttk.Frame(self.nb, padding=8))
        self._build_mic(ttk.Frame(self.nb, padding=8))
        self._build_pron(ttk.Frame(self.nb, padding=8))
        self._build_settings(ttk.Frame(self.nb, padding=4))

        self._refresh_status()
        if not ok:
            for w in (self.btn_start, self.btn_detect, self.btn_rec, self.btn_live, self.btn_pron_rec):
                w.state(["disabled"])

    # ------------------------------------------------------------ ortak durum
    def _refresh_status(self) -> None:
        def job():
            return W.status()

        def done(res):
            ok, text = res
            loaded = self.engine.loaded_name()
            if loaded:
                text += f" · {self.t('wh.loaded')}: {loaded} ({self.engine.device}/{self.engine.compute_type})"
            self.status_lbl.configure(text=text, style="Dim.TLabel" if ok else "Warn.TLabel")
            self._on_model_pick(save=False)
        self.app.worker.run(job, done, lambda e: self.status_lbl.configure(text=str(e)))

    def _on_model_pick(self, save: bool = True) -> None:
        name = self.model_var.get()
        size, note = W.MODEL_INFO.get(name, (0, ""))
        have = W.is_downloaded(name)
        mark = self.t("wh.ready") if have else self.t("wh.not_downloaded")
        self.model_info.configure(text=f"{name}: ~{size} MB · {note} · {mark}")
        if save:
            self._save_opts()

    def _set_status(self, text: str) -> None:
        self.app.worker.post(lambda: self.status_lbl.configure(text=text, style="Dim.TLabel"))
        self.app.worker.post(lambda: self.app.set_status(text))

    def _collect_opts(self) -> W.WhisperOptions:
        """Ust bar + ayar formundan guncel WhisperOptions."""
        d = self.opts.to_dict()
        d.update(model=self.model_var.get(), device=self.device_var.get(),
                 compute_type=self.compute_var.get())
        for key, (var, kind) in getattr(self, "_fields", {}).items():
            raw = var.get()
            try:
                if kind == "bool":
                    d[key] = bool(raw)
                elif kind == "int":
                    d[key] = int(float(raw))
                elif kind == "float":
                    d[key] = float(raw)
                elif kind == "optfloat":
                    d[key] = None if str(raw).strip() in ("", "-", "None") else float(raw)
                elif kind == "optint":
                    d[key] = None if str(raw).strip() in ("", "-", "None", "0") else int(float(raw))
                elif kind == "temps":
                    d[key] = [float(x) for x in str(raw).replace(";", ",").split(",") if x.strip()] or [0.0]
                elif kind == "str":
                    d[key] = str(raw).strip() or None
                elif kind == "lang":
                    code = str(raw).split(" ")[0]
                    d[key] = None if code in ("", "auto") else code
                else:
                    d[key] = raw
            except (TypeError, ValueError):
                pass
        self.opts = W.WhisperOptions.from_dict(d)
        return self.opts

    def _save_opts(self) -> None:
        self.app.settings["whisper"] = self._collect_opts().to_dict()
        C.save_settings(self.app.settings)

    def _guard(self) -> bool:
        if not W.installed():
            messagebox.showwarning(C.APP_NAME, self.t("wh.not_installed"), parent=self)
            return False
        if self.busy:
            self.app.set_status(self.t("wh.busy"))
            return False
        return True

    # ------------------------------------------------------------ model isleri
    def download_model(self) -> None:
        if not self._guard():
            return
        name = self.model_var.get()
        if W.is_downloaded(name):
            self._on_model_pick(save=False)
            return
        size = W.MODEL_INFO.get(name, (0, ""))[0]
        if not messagebox.askyesno(C.APP_NAME, self.t("wh.confirm_dl").format(name=name, size=size), parent=self):
            return
        self.busy = True
        self.status_lbl.configure(text=self.t("wh.downloading").format(name=name))

        def done(_):
            self.busy = False
            self._refresh_status()

        def err(e):
            self.busy = False
            self.status_lbl.configure(text=f"{self.t('g.error')}: {e}", style="Err.TLabel")
        self.app.worker.run(lambda: W.download(name), done, err)

    def preload(self) -> None:
        if not self._guard():
            return
        opts = self._collect_opts()
        self.busy = True

        def done(_):
            self.busy = False
            self._refresh_status()

        def err(e):
            self.busy = False
            self.status_lbl.configure(text=f"{self.t('g.error')}: {e}", style="Err.TLabel")
        self.app.worker.run(lambda: self.engine.load(opts, self._set_status), done, err)

    def unload(self) -> None:
        if self.busy:
            return
        # unload motor kilidini alir; baska sekmenin uzun isi kilidi tutuyorsa
        # Tk thread'i donmasin diye arka planda calistir.
        self.busy = True

        def done(_):
            self.busy = False
            self._refresh_status()

        def err(e):
            self.busy = False
            self.status_lbl.configure(text=f"{self.t('g.error')}: {e}", style="Err.TLabel")
        self.app.worker.run(self.engine.unload, done, err)

    # ================================================================== DOSYA
    def _build_file(self, f: ttk.Frame) -> None:
        self.nb.add(f, text=self.t("wh.tab_file"))
        bar = ttk.Frame(f)
        bar.pack(fill="x")
        self.file_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self.file_var).pack(side="left", fill="x", expand=True)
        ttk.Button(bar, text=self.t("wh.pick_file"), command=self.pick_file).pack(side="left", padx=4)
        ttk.Button(bar, text=self.t("wh.pick_folder"), command=self.batch_folder).pack(side="left")

        row = ttk.Frame(f)
        row.pack(fill="x", pady=(8, 0))
        ttk.Label(row, text=self.t("wh.task")).pack(side="left")
        self.task_var = tk.StringVar(value=self.opts.task)
        ttk.Radiobutton(row, text=self.t("wh.transcribe"), value="transcribe",
                        variable=self.task_var).pack(side="left", padx=(4, 0))
        ttk.Radiobutton(row, text=self.t("wh.translate"), value="translate",
                        variable=self.task_var).pack(side="left", padx=(6, 14))
        ttk.Label(row, text=self.t("wh.language")).pack(side="left")
        self.lang_var = tk.StringVar(value=self._lang_label(self.opts.language))
        ttk.Combobox(row, textvariable=self.lang_var, state="readonly", width=16,
                     values=self._lang_values()).pack(side="left", padx=4)
        self.words_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(row, text=self.t("wh.color_words"), variable=self.words_var,
                        command=self._render_transcript).pack(side="left", padx=10)
        act = ttk.Frame(f)
        act.pack(fill="x", pady=(8, 0))
        self.btn_start = ttk.Button(act, text="▶ " + self.t("wh.start"), style="Accent.TButton",
                                    command=self.start_file)
        self.btn_start.pack(side="left")
        ttk.Button(act, text="■ " + self.t("wh.cancel"), command=self.cancel.set).pack(side="left", padx=4)
        self.btn_detect = ttk.Button(act, text=self.t("wh.detect"), command=self.detect_lang)
        self.btn_detect.pack(side="left")

        self.progress = ttk.Progressbar(f, mode="determinate", maximum=1000)
        self.progress.pack(fill="x", pady=(8, 2))
        self.info_lbl = ttk.Label(f, text="", style="Dim.TLabel")
        self.info_lbl.pack(fill="x")

        # Disa aktarim satiri metinden ONCE altta yerlestirilir: pencere kisa olsa da gorunur.
        ex = ttk.Frame(f)
        ex.pack(side="bottom", fill="x")
        self.out = tk.Text(f, wrap="word", height=8, font=C.FONT_RU)
        style_text(self.out, self.palette())
        self.out.pack(fill="both", expand=True, pady=6)
        p = self.palette()
        self.out.tag_configure("ts", foreground=p["fg_mute"], font=C.FONT_MONO)
        self.out.tag_configure("lo", foreground=p["err"])
        self.out.tag_configure("mid", foreground=p["warn"])
        ttk.Label(ex, text=self.t("wh.export")).pack(side="left")
        for fmt in W.EXPORT_FORMATS:
            ttk.Button(ex, text=fmt.upper(), command=lambda x=fmt: self.export(x)).pack(side="left", padx=2)
        ttk.Button(ex, text=self.t("wh.copy"), command=self.copy_text).pack(side="left", padx=(12, 0))
        ttk.Button(ex, text=self.t("wh.to_ai"), command=self.send_to_ai).pack(side="left", padx=4)

    def _lang_values(self):
        return ["auto"] + [f"{k} · {v}" for k, v in W.LANGUAGES.items()]

    @staticmethod
    def _lang_label(code):
        return "auto" if not code else f"{code} · {W.LANGUAGES.get(code, code)}"

    def pick_file(self) -> None:
        path = filedialog.askopenfilename(parent=self, filetypes=AUDIO_TYPES)
        if path:
            self.file_var.set(path)

    def _file_opts(self) -> W.WhisperOptions:
        opts = self._collect_opts()
        code = self.lang_var.get().split(" ")[0]
        opts.language = None if code == "auto" else code
        opts.task = self.task_var.get()
        self.opts = opts
        self._save_opts()
        return opts

    def start_file(self) -> None:
        path = self.file_var.get().strip()
        if not path:
            self.pick_file()
            path = self.file_var.get().strip()
        if not path or not Path(path).exists():
            return
        opts = self._file_opts()
        if opts.task == "translate" and not W.translation_capable(opts.model):
            if not messagebox.askyesno(C.APP_NAME, self.t("wh.no_translate").format(model=opts.model),
                                       parent=self):
                return
        self._run_transcription(path, opts)

    def _run_transcription(self, audio, opts, on_done=None) -> None:
        if not self._guard():
            return
        self.busy = True
        self.cancel.clear()
        self.progress["value"] = 0
        self.out.delete("1.0", "end")
        self.info_lbl.configure(text="")

        def on_seg(seg, frac):
            def ui():
                self.progress["value"] = int(frac * 1000)
                self.out.insert("end", f"[{W.fmt_clock(seg.start)} → {W.fmt_clock(seg.end)}] ", "ts")
                self.out.insert("end", seg.text.strip() + "\n")
                self.out.see("end")
            self.app.worker.post(ui)

        def job():
            return self.engine.transcribe(audio, opts, on_segment=on_seg,
                                          on_status=self._set_status, cancel=self.cancel)

        def done(tr):
            self.busy = False
            self.transcript = tr
            self.progress["value"] = 1000
            rtf = tr.elapsed / tr.duration if tr.duration else 0
            langs = ", ".join(f"{a} %{b * 100:.0f}" for a, b in tr.all_language_probs[:3])
            self.info_lbl.configure(text=self.t("wh.done_info").format(
                lang=tr.language, prob=tr.language_probability * 100, dur=W.fmt_clock(tr.duration),
                sec=tr.elapsed, rtf=rtf, dev=tr.device, n=len(tr.segments)) + (f" · {langs}" if langs else ""))
            self._render_transcript()
            self._refresh_status()
            if on_done:
                on_done(tr)

        def err(e):
            self.busy = False
            self.info_lbl.configure(text=f"{self.t('g.error')}: {e}", style="Err.TLabel")
        self.app.worker.run(job, done, err)

    def _render_transcript(self) -> None:
        tr = self.transcript
        if tr is None:
            return
        self.out.delete("1.0", "end")
        for s in tr.segments:
            self.out.insert("end", f"[{W.fmt_clock(s.start)} → {W.fmt_clock(s.end)}] ", "ts")
            if self.words_var.get() and s.words:
                for w in s.words:
                    tag = "lo" if w.probability < 0.5 else ("mid" if w.probability < 0.8 else "")
                    self.out.insert("end", w.word, tag)
                self.out.insert("end", "\n")
            else:
                self.out.insert("end", s.text.strip() + "\n")

    def detect_lang(self) -> None:
        path = self.file_var.get().strip()
        if not path or not Path(path).exists() or not self._guard():
            return
        opts = self._collect_opts()
        self.busy = True

        def done(probs):
            self.busy = False
            self.info_lbl.configure(text=self.t("wh.detected") + ": " + ", ".join(
                f"{W.LANGUAGES.get(a, a)} ({a}) %{b * 100:.1f}" for a, b in probs[:5]))
            if probs:
                self.lang_var.set(self._lang_label(probs[0][0]))

        def err(e):
            self.busy = False
            self.info_lbl.configure(text=f"{self.t('g.error')}: {e}")
        self.app.worker.run(lambda: self.engine.detect_language(path, opts, self._set_status), done, err)

    def batch_folder(self) -> None:
        folder = filedialog.askdirectory(parent=self)
        if not folder or not self._guard():
            return
        files = [p for p in sorted(Path(folder).rglob("*")) if p.suffix.lower() in MEDIA_EXT]
        if not files:
            messagebox.showinfo(C.APP_NAME, self.t("wh.no_media"), parent=self)
            return
        opts = self._file_opts()
        self.busy = True
        self.cancel.clear()

        def job():
            done_n = 0
            taken: set = set()
            for k, f in enumerate(files, 1):
                if self.cancel.is_set():
                    break
                self._set_status(f"[{k}/{len(files)}] {f.name}")
                self.app.worker.post(lambda v=k: self.progress.configure(value=int(v / len(files) * 1000)))
                tr = self.engine.transcribe(str(f), opts, cancel=self.cancel)
                if self.cancel.is_set():
                    break                       # yarim sonucu disa aktarma, sayma
                srt, txt = batch_targets(f, files, taken)
                W.export(tr, "srt", str(srt))
                W.export(tr, "txt", str(txt))
                done_n += 1
            return done_n

        def done(n):
            self.busy = False
            self.info_lbl.configure(text=self.t("wh.batch_done").format(n=n, total=len(files)))
            open_path(Path(folder))

        def err(e):
            self.busy = False
            self.info_lbl.configure(text=f"{self.t('g.error')}: {e}")
        self.app.worker.run(job, done, err)

    def export(self, fmt: str) -> None:
        if self.transcript is None:
            return
        base = Path(self.file_var.get() or "transkript").stem
        path = filedialog.asksaveasfilename(parent=self, defaultextension=f".{fmt}",
                                            initialdir=str(C.EXPORT_DIR), initialfile=f"{base}.{fmt}",
                                            filetypes=[(fmt.upper(), f"*.{fmt}")])
        if path:
            W.export(self.transcript, fmt, path)
            self.app.set_status(f"{self.t('wh.saved')}: {path}")

    def copy_text(self) -> None:
        text = self.transcript.text if self.transcript else self.out.get("1.0", "end").strip()
        self.clipboard_clear()
        self.clipboard_append(text)
        self.app.set_status(self.t("wh.copied"))

    def send_to_ai(self) -> None:
        """Transkripti AI Ogretmen sekmesine aktar (aciklama / ceviri icin)."""
        text = self.transcript.text if self.transcript else ""
        if not text:
            return
        tab = self.app.goto_tab("tab.ai")
        for name in ("inp", "input", "prompt", "q", "box"):
            w = getattr(tab, name, None)
            if isinstance(w, tk.Text):
                w.delete("1.0", "end")
                w.insert("1.0", text)
                return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.app.set_status(self.t("wh.copied"))

    # ================================================================ MIKROFON
    def _build_mic(self, f: ttk.Frame) -> None:
        self.nb.add(f, text=self.t("wh.tab_mic"))
        ok, name = W.mic_available()
        ttk.Label(f, text=(self.t("wh.mic") + ": " + name) if ok else name,
                  style="Dim.TLabel" if ok else "Warn.TLabel").pack(anchor="w")
        bar = ttk.Frame(f)
        bar.pack(fill="x", pady=8)
        self.btn_rec = ttk.Button(bar, text="● " + self.t("wh.record"), style="Err.TButton",
                                  command=self.toggle_record)
        self.btn_rec.pack(side="left")
        self.btn_live = ttk.Button(bar, text="🎙 " + self.t("wh.live"), command=self.toggle_live)
        self.btn_live.pack(side="left", padx=6)
        ttk.Button(bar, text=self.t("wh.save_wav"), command=self.save_recording).pack(side="left")
        ttk.Label(bar, text=self.t("wh.language")).pack(side="left", padx=(14, 4))
        self.mic_lang = tk.StringVar(value=self._lang_label("ru"))
        ttk.Combobox(bar, textvariable=self.mic_lang, state="readonly", width=16,
                     values=self._lang_values()).pack(side="left")
        self.vu = ttk.Progressbar(f, mode="determinate", maximum=100)
        self.vu.pack(fill="x")
        self.rec_lbl = ttk.Label(f, text="", style="Dim.TLabel")
        self.rec_lbl.pack(anchor="w", pady=4)
        self.mic_out = tk.Text(f, wrap="word", height=12, font=C.FONT_RU)
        style_text(self.mic_out, self.palette())
        self.mic_out.pack(fill="both", expand=True)
        self.mic_out.tag_configure("tmp", foreground=self.palette()["fg_mute"])
        self.last_audio = None
        if not ok:
            self.btn_rec.state(["disabled"])
            self.btn_live.state(["disabled"])

    def _mic_opts(self) -> W.WhisperOptions:
        opts = self._collect_opts()
        code = self.mic_lang.get().split(" ")[0]
        opts = W.WhisperOptions.from_dict(dict(opts.to_dict(), language=None if code == "auto" else code,
                                               task="transcribe", batched=False))
        return opts

    def _tick_vu(self) -> None:
        r = self.rec or (self.live.rec if self.live else None)
        if r is None or not r.recording:
            self.vu["value"] = 0
            return
        self.vu["value"] = int(r.level * 100)
        self.rec_lbl.configure(text=f"{self.t('wh.recording')} {W.fmt_clock(r.elapsed())}")
        self.after(80, self._tick_vu)

    def toggle_record(self) -> None:
        if self.live:
            return
        if self.rec is not None and getattr(self, "_pron_mode", False):
            return                              # kayit Telaffuz sekmesine ait
        if self.rec is None:
            if not self._guard():
                return
            try:
                self.rec = W.Recorder()
                self.rec.start()
            except Exception as e:                             # noqa: BLE001
                self.rec = None
                self.rec_lbl.configure(text=f"{self.t('g.error')}: {e}", style="Err.TLabel")
                return
            self.btn_rec.configure(text="■ " + self.t("wh.stop"))
            self._tick_vu()
            return
        audio = self.rec.stop()
        self.rec = None
        self.btn_rec.configure(text="● " + self.t("wh.record"))
        self.last_audio = audio
        if len(audio) < W.SAMPLE_RATE * 0.3:
            self.rec_lbl.configure(text=self.t("wh.too_short"))
            return
        opts = self._mic_opts()
        self.busy = True
        self.rec_lbl.configure(text=self.t("wh.working"))

        def done(tr):
            self.busy = False
            self.mic_out.insert("end", tr.text + "\n")
            self.mic_out.see("end")
            self.rec_lbl.configure(text=f"{tr.language} · {tr.elapsed:.1f} sn · {tr.device}")

        def err(e):
            self.busy = False
            self.rec_lbl.configure(text=f"{self.t('g.error')}: {e}")
        self.app.worker.run(lambda: self.engine.transcribe(audio, opts, on_status=self._set_status), done, err)

    def toggle_live(self) -> None:
        if self.rec is not None:
            return
        if self.live is None:
            if not self._guard():
                return
            opts = self._mic_opts()
            if not W.is_downloaded(opts.model):
                size = W.MODEL_INFO.get(opts.model, (0, ""))[0]
                if not messagebox.askyesno(C.APP_NAME, self.t("wh.confirm_dl").format(name=opts.model, size=size),
                                           parent=self):
                    return
            # Model yukleme (gerekirse indirme) uzun surer: arka planda, Tk thread'i donmasin.
            self.busy = True
            self.btn_live.state(["disabled"])
            self.rec_lbl.configure(text=self.t("wh.working"))

            def loaded(_):
                self.busy = False
                self.btn_live.state(["!disabled"])
                if self.live is not None or self.rec is not None:
                    return
                self._start_live(opts)

            def load_err(e):
                self.busy = False
                self.btn_live.state(["!disabled"])
                self.rec_lbl.configure(text=f"{self.t('g.error')}: {e}")
            self.app.worker.run(lambda: self.engine.load(opts, self._set_status), loaded, load_err)
            return
        self.last_audio = self.live.rec.snapshot()
        self.live.stop()
        self.live = None
        self.btn_live.configure(text="🎙 " + self.t("wh.live"))
        self.rec_lbl.configure(text=self.t("wh.live_stopped"))

    def _start_live(self, opts) -> None:
        """Model yuklendikten sonra (Tk thread'inde) canli dikteyi baslat."""
        self.mic_out.insert("end", "\n")
        mark = self._live_mark = self.mic_out.index("end-1c")
        live = None

        def on_text(committed, partial):
            def ui():
                # Durdurulmus / yerine yenisi gelmis oturumun gec gelen sonucu: yok say.
                if self.live is not live:
                    return
                self.mic_out.delete(mark, "end")
                self.mic_out.insert(mark, committed + " ")
                if partial:
                    self.mic_out.insert("end", partial, "tmp")
                self.mic_out.see("end")
            self.app.worker.post(ui)

        def on_err(e):
            self.app.worker.post(lambda: self.rec_lbl.configure(text=f"{self.t('g.error')}: {e}"))
        try:
            live = W.LiveDictation(self.engine, opts, on_text, on_err)
            self.live = live
            live.start()
        except Exception as e:                             # noqa: BLE001
            self.live = None
            self.rec_lbl.configure(text=f"{self.t('g.error')}: {e}")
            return
        self.btn_live.configure(text="■ " + self.t("wh.stop"))
        self._tick_vu()

    def save_recording(self) -> None:
        if self.last_audio is None or not len(self.last_audio):
            return
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".wav",
                                            initialdir=str(C.EXPORT_DIR), filetypes=[("WAV", "*.wav")])
        if path:
            W.save_wav(path, self.last_audio)
            self.app.set_status(f"{self.t('wh.saved')}: {path}")

    # ================================================================ TELAFFUZ
    def _build_pron(self, f: ttk.Frame) -> None:
        self.nb.add(f, text=self.t("wh.tab_pron"))
        ttk.Label(f, text=self.t("wh.pron_help"), style="Dim.TLabel", wraplength=900,
                  justify="left").pack(anchor="w")
        bar = ttk.Frame(f)
        bar.pack(fill="x", pady=8)
        self.pron_target = tk.StringVar(value="Я изучаю русский язык.")
        ttk.Entry(bar, textvariable=self.pron_target, font=C.FONT_RU).pack(side="left", fill="x", expand=True)
        ttk.Button(bar, text="🔊 " + self.t("g.listen"),
                   command=lambda: self.app.speak(self.pron_target.get())).pack(side="left", padx=4)
        ttk.Button(bar, text=self.t("wh.from_bank"), command=self._pron_pick).pack(side="left")
        self.btn_pron_rec = ttk.Button(bar, text="● " + self.t("wh.record"), style="Err.TButton",
                                       command=self.pron_record)
        self.btn_pron_rec.pack(side="left", padx=(8, 0))
        self.pron_score = ttk.Label(f, text="", style="Title.TLabel")
        self.pron_score.pack(anchor="w", pady=(6, 2))
        self.pron_out = tk.Text(f, wrap="word", height=6, font=(C.FONT_FAMILY, 18))
        style_text(self.pron_out, self.palette())
        self.pron_out.pack(fill="x")
        p = self.palette()
        self.pron_out.tag_configure("ok", foreground=p["ok"])
        self.pron_out.tag_configure("unsure", foreground=p["warn"])
        self.pron_out.tag_configure("wrong", foreground=p["err"], underline=True)
        self.pron_out.tag_configure("missing", foreground=p["fg_mute"], overstrike=True)
        self.pron_out.tag_configure("extra", foreground=p["accent"])
        self.pron_heard = ttk.Label(f, text="", style="Dim.TLabel", wraplength=900, justify="left")
        self.pron_heard.pack(anchor="w", pady=6)
        ttk.Label(f, text=self.t("wh.pron_legend"), style="Mute.TLabel").pack(anchor="w")

    def _pron_pick(self) -> None:
        import random
        rows = [r for r in self.repos.words.all() if (r.get("example") or "").strip() and C.has_cyrillic(r["example"])]
        rows = rows or self.repos.words.all()
        if rows:
            r = random.choice(rows)
            ex = (r.get("example") or "").strip()
            self.pron_target.set(ex if C.has_cyrillic(ex) else r["ru"])

    def pron_record(self) -> None:
        if self.rec is not None and getattr(self, "_pron_mode", False):
            audio = self.rec.stop()
            self.rec = None
            self._pron_mode = False
            self.btn_pron_rec.configure(text="● " + self.t("wh.record"))
            opts = W.WhisperOptions.from_dict(dict(self._collect_opts().to_dict(), language="ru",
                                                   task="transcribe", word_timestamps=True,
                                                   batched=False, vad_filter=True,
                                                   condition_on_previous_text=False))
            target = self.pron_target.get()
            self.busy = True
            self.pron_score.configure(text=self.t("wh.working"))

            def done(tr):
                self.busy = False
                self._show_pron(target, tr)

            def err(e):
                self.busy = False
                self.pron_score.configure(text=f"{self.t('g.error')}: {e}")
            self.app.worker.run(lambda: self.engine.transcribe(audio, opts, on_status=self._set_status),
                                done, err)
            return
        if not self._guard() or self.rec is not None:
            return
        try:
            self.rec = W.Recorder()
            self.rec.start()
        except Exception as e:                                 # noqa: BLE001
            self.rec = None
            self.pron_score.configure(text=f"{self.t('g.error')}: {e}")
            return
        self._pron_mode = True
        self.btn_pron_rec.configure(text="■ " + self.t("wh.stop"))
        self.pron_score.configure(text=self.t("wh.speak_now"))

    def _show_pron(self, target: str, tr) -> None:
        words, score = W.compare_pronunciation(target, tr)
        self.pron_out.delete("1.0", "end")
        for w in words:
            if w.status == "ok":
                tag = "ok" if w.probability >= 0.5 else "unsure"
                self.pron_out.insert("end", w.target + " ", tag)
            elif w.status == "wrong":
                self.pron_out.insert("end", f"{w.target} ", "wrong")
                self.pron_out.insert("end", f"({w.heard}) ", "extra")
            elif w.status == "missing":
                self.pron_out.insert("end", w.target + " ", "missing")
            else:
                self.pron_out.insert("end", f"+{w.heard} ", "extra")
        p = self.palette()
        tone = p["ok"] if score >= 85 else (p["warn"] if score >= 60 else p["err"])
        self.pron_score.configure(text=f"{self.t('wh.score')}: {score:.0f} / 100", foreground=tone)
        self.pron_heard.configure(text=f"{self.t('wh.heard')}: {tr.text}")
        try:
            good = score >= 85
            self.repos.study.log(self.pid, "pron", int(good), int(not good))
        except Exception:
            pass

    # ================================================================ AYARLAR
    def _build_settings(self, f: ttk.Frame) -> None:
        self.nb.add(f, text=self.t("wh.tab_settings"))
        sf = ScrollFrame(f)
        sf.paint(self.palette())
        sf.pack(fill="both", expand=True)
        body = sf.body
        o = self.opts
        self._fields = {}

        def group(title):
            lf = ttk.LabelFrame(body, text=title, padding=10)
            lf.pack(fill="x", pady=6, padx=4)
            lf.columnconfigure(1, weight=1)
            lf.columnconfigure(3, weight=1)
            return lf

        def field(g, r, c, key, label, kind, value, hint=""):
            ttk.Label(g, text=label).grid(row=r, column=c * 2, sticky="w", padx=(0, 6), pady=3)
            if kind == "bool":
                var = tk.BooleanVar(value=bool(value))
                ttk.Checkbutton(g, variable=var, text=hint).grid(row=r, column=c * 2 + 1, sticky="w")
            else:
                if kind == "temps":
                    value = ", ".join(str(x) for x in value)
                elif value is None:
                    value = ""
                elif value == float("inf"):
                    value = ""
                var = tk.StringVar(value=str(value))
                if kind == "lang":
                    ttk.Combobox(g, textvariable=var, state="readonly", values=self._lang_values(),
                                 width=18).grid(row=r, column=c * 2 + 1, sticky="w")
                    var.set(self._lang_label(value or None))
                else:
                    ttk.Entry(g, textvariable=var, width=26).grid(row=r, column=c * 2 + 1, sticky="we")
            self._fields[key] = (var, kind)

        g = group(self.t("wh.grp_decode"))
        field(g, 0, 0, "beam_size", "beam_size", "int", o.beam_size)
        field(g, 0, 1, "best_of", "best_of", "int", o.best_of)
        field(g, 1, 0, "patience", "patience", "float", o.patience)
        field(g, 1, 1, "length_penalty", "length_penalty", "float", o.length_penalty)
        field(g, 2, 0, "repetition_penalty", "repetition_penalty", "float", o.repetition_penalty)
        field(g, 2, 1, "no_repeat_ngram_size", "no_repeat_ngram_size", "int", o.no_repeat_ngram_size)
        field(g, 3, 0, "temperature", "temperature (" + self.t("wh.fallback") + ")", "temps", o.temperature)
        field(g, 3, 1, "prompt_reset_on_temperature", "prompt_reset_on_temperature", "float",
              o.prompt_reset_on_temperature)

        g = group(self.t("wh.grp_thresholds"))
        field(g, 0, 0, "compression_ratio_threshold", "compression_ratio_threshold", "optfloat",
              o.compression_ratio_threshold)
        field(g, 0, 1, "log_prob_threshold", "log_prob_threshold", "optfloat", o.log_prob_threshold)
        field(g, 1, 0, "no_speech_threshold", "no_speech_threshold", "optfloat", o.no_speech_threshold)
        field(g, 1, 1, "hallucination_silence_threshold", "hallucination_silence_threshold", "optfloat",
              o.hallucination_silence_threshold)
        field(g, 2, 0, "language_detection_threshold", "language_detection_threshold", "float",
              o.language_detection_threshold)
        field(g, 2, 1, "language_detection_segments", "language_detection_segments", "int",
              o.language_detection_segments)

        g = group(self.t("wh.grp_text"))
        field(g, 0, 0, "language", self.t("wh.default_lang"), "lang", o.language)
        field(g, 0, 1, "multilingual", "multilingual", "bool", o.multilingual, self.t("wh.multilingual"))
        field(g, 1, 0, "initial_prompt", "initial_prompt", "str", o.initial_prompt)
        field(g, 1, 1, "prefix", "prefix", "str", o.prefix)
        field(g, 2, 0, "hotwords", "hotwords", "str", o.hotwords)
        field(g, 2, 1, "condition_on_previous_text", "condition_on_previous_text", "bool",
              o.condition_on_previous_text)
        field(g, 3, 0, "suppress_blank", "suppress_blank", "bool", o.suppress_blank)
        field(g, 3, 1, "clip_timestamps", "clip_timestamps", "str", o.clip_timestamps)

        g = group(self.t("wh.grp_time"))
        field(g, 0, 0, "word_timestamps", "word_timestamps", "bool", o.word_timestamps, self.t("wh.word_ts"))
        field(g, 0, 1, "without_timestamps", "without_timestamps", "bool", o.without_timestamps)
        field(g, 1, 0, "max_initial_timestamp", "max_initial_timestamp", "float", o.max_initial_timestamp)
        field(g, 1, 1, "chunk_length", "chunk_length (sn)", "optint", o.chunk_length)

        g = group(self.t("wh.grp_vad"))
        field(g, 0, 0, "vad_filter", "vad_filter", "bool", o.vad_filter, self.t("wh.vad_hint"))
        field(g, 0, 1, "vad_threshold", "threshold", "float", o.vad_threshold)
        field(g, 1, 0, "vad_min_speech_duration_ms", "min_speech_duration_ms", "int", o.vad_min_speech_duration_ms)
        field(g, 1, 1, "vad_min_silence_duration_ms", "min_silence_duration_ms", "int",
              o.vad_min_silence_duration_ms)
        field(g, 2, 0, "vad_speech_pad_ms", "speech_pad_ms", "int", o.vad_speech_pad_ms)
        field(g, 2, 1, "vad_max_speech_duration_s", "max_speech_duration_s", "optfloat",
              None if o.vad_max_speech_duration_s == float("inf") else o.vad_max_speech_duration_s)

        g = group(self.t("wh.grp_perf"))
        field(g, 0, 0, "batched", "batched", "bool", o.batched, self.t("wh.batched_hint"))
        field(g, 0, 1, "batch_size", "batch_size", "int", o.batch_size)
        field(g, 1, 0, "cpu_threads", "cpu_threads (0 = auto)", "int", o.cpu_threads)

        btns = ttk.Frame(body)
        btns.pack(fill="x", pady=8, padx=4)
        ttk.Button(btns, text=self.t("wh.save_settings"), style="Accent.TButton",
                   command=self._save_and_note).pack(side="left")
        ttk.Button(btns, text=self.t("wh.reset"), command=self._reset).pack(side="left", padx=6)

    def _save_and_note(self) -> None:
        self._save_opts()
        self.app.set_status(self.t("wh.settings_saved"))

    def _reset(self) -> None:
        # Sekme yeniden kuruldugunda calisan is / kayit / canli dikte sahipsiz kalir
        # (durdurulamaz, iptal olayi kopar); bunlar surerken sifirlamayi reddet.
        if self.busy or self.rec is not None or self.live is not None:
            self.app.set_status(self.t("wh.busy"))
            return
        if not messagebox.askyesno(C.APP_NAME, self.t("wh.reset_confirm"), parent=self):
            return
        keep = {"model": self.model_var.get(), "device": self.device_var.get(),
                "compute_type": self.compute_var.get()}
        self.app.settings["whisper"] = W.WhisperOptions(**keep).to_dict()
        C.save_settings(self.app.settings)
        for child in self.winfo_children():
            child.destroy()
        self._built = False
        self.ensure_built()
        self.nb.select(3)

    def on_show(self) -> None:
        if getattr(self, "status_lbl", None) is not None and not self.busy:
            self._refresh_status()
