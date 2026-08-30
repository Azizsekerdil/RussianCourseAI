# -*- coding: utf-8 -*-
"""AI Ogretmen sekmesi.

Gorevine gore model yonlendirme (aciklama / ceviri / duzeltme / gorsel-OCR)
ve yazi duzeltici. Model yoksa arayuz calisir, yalnizca sakin bir uyari gosterir.
"""
from __future__ import annotations

import base64
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import rca_common as C
from rca.ui_util import LazyTab, style_text

TASKS = [
    ("explain", "Dilbilgisi acikla"),
    ("translate_ru2tr", "Ceviri RU -> TR"),
    ("translate_tr2ru", "Ceviri TR -> RU"),
    ("correct", "Yazi duzelt"),
    ("free", "Serbest soru"),
]


class AITab(LazyTab):
    """Yerel LM Studio modeliyle calisan ogretmen paneli."""

    def build(self) -> None:
        p = self.palette()
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        bar = ttk.Frame(root)
        bar.pack(fill="x")
        ttk.Label(bar, text="Gorev:").pack(side="left")
        self.task = tk.StringVar(value=TASKS[0][1])
        ttk.Combobox(bar, textvariable=self.task, state="readonly", width=22,
                     values=[t[1] for t in TASKS]).pack(side="left", padx=6)
        ttk.Label(bar, text="Model:").pack(side="left", padx=(16, 4))
        self.model = tk.StringVar(value="(otomatik)")
        self.model_box = ttk.Combobox(bar, textvariable=self.model, state="readonly",
                                      width=32, values=["(otomatik)"])
        self.model_box.pack(side="left")
        ttk.Button(bar, text="Modelleri tara",
                   command=self.scan_models).pack(side="left", padx=6)
        ttk.Button(bar, text="🖼 Gorsel / OCR",
                   command=self.ask_image).pack(side="right")
        ttk.Button(bar, text="Temizle", command=self.clear).pack(side="right", padx=6)

        self.warn = ttk.Label(root, text="", style="Warn.TLabel", wraplength=1000,
                              justify="left")
        self.warn.pack(anchor="w", pady=(8, 0))

        pane = ttk.PanedWindow(root, orient="vertical")
        pane.pack(fill="both", expand=True, pady=8)

        top = ttk.Frame(pane)
        ttk.Label(top, text="Soru / metin (Ctrl+Enter = gonder)",
                  style="TLabel", font=C.FONT_UI_BOLD).pack(anchor="w")
        self.inp = tk.Text(top, height=7, wrap="word")
        style_text(self.inp, p)
        self.inp.pack(fill="both", expand=True)
        self.inp.bind("<Control-Return>", lambda _e: self.send())
        row = ttk.Frame(top)
        row.pack(fill="x", pady=6)
        self.send_btn = ttk.Button(row, text="▶ " + self.t("ai.ask"),
                                   style="Accent.TButton", command=self.send)
        self.send_btn.pack(side="left")
        ttk.Button(row, text="PDF'teki secimi al",
                   command=self.pull_pdf_selection).pack(side="left", padx=6)
        ttk.Button(row, text="🔊 Yaniti oku", command=self.speak_out).pack(side="left")
        pane.add(top, weight=1)

        bottom = ttk.Frame(pane)
        ttk.Label(bottom, text="Yanit", style="TLabel",
                  font=C.FONT_UI_BOLD).pack(anchor="w")
        self.out = tk.Text(bottom, height=18, wrap="word")
        style_text(self.out, p)
        self.out.pack(fill="both", expand=True)
        self.out.configure(state="disabled")
        pane.add(bottom, weight=2)

        self.scan_models()

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        """Sekmeye donuste model listesini tazele."""
        if getattr(self, "model_box", None) is not None:
            self.scan_models()

    def scan_models(self) -> None:
        """Kurulu modelleri arka planda listele."""
        def job():
            return self.app.ai.models(force=True)

        def done(models):
            p = self.palette()
            if models:
                self.model_box["values"] = ["(otomatik)"] + models
                self.warn.configure(text=f"{len(models)} model bulundu.",
                                    foreground=p["ok"])
                self.send_btn.state(["!disabled"])
            else:
                self.model_box["values"] = ["(otomatik)"]
                self.warn.configure(
                    text=f"{self.t('ai.offline')}\n"
                         f"LM Studio'yu acip 'Local Server'i {self.app.ai.base} "
                         f"adresinde baslatin. Program bu olmadan da calisir; "
                         f"yalnizca AI ozellikleri kapali kalir.",
                    foreground=p["warn"])
        self.app.worker.run(job, done, lambda e: None)

    def _write(self, text: str) -> None:
        self.out.configure(state="normal")
        self.out.delete("1.0", "end")
        self.out.insert("1.0", text)
        self.out.configure(state="disabled")

    def clear(self) -> None:
        """Giris ve cikisi temizle."""
        self.inp.delete("1.0", "end")
        self._write("")

    def speak_out(self) -> None:
        """Yaniti seslendir."""
        self.app.speak(self.out.get("1.0", "end").strip()[:400])

    def pull_pdf_selection(self) -> None:
        """PDF okuyucudaki secili metni giris kutusuna al."""
        widget = self.app._tabs.get("tab.pdf")
        text = ""
        if widget is not None and hasattr(widget, "sel_box"):
            try:
                text = widget.sel_box.get("1.0", "end").strip()
            except Exception:
                text = ""
        if not text:
            messagebox.showinfo(C.APP_NAME,
                                "PDF Okuyucuda once 'Metin sec' araciyla bir parca secin.")
            return
        self.inp.delete("1.0", "end")
        self.inp.insert("1.0", text)

    # ------------------------------------------------------------------
    def send(self) -> str:
        """Secili goreve gore modele istek gonder."""
        text = self.inp.get("1.0", "end").strip()
        if not text:
            return "break"
        label = self.task.get()
        code = next((c for c, l in TASKS if l == label), "free")
        model = None if self.model.get() == "(otomatik)" else self.model.get()
        lang = self.app.ui_lang()
        self._write(self.t("ai.thinking"))
        self.send_btn.state(["disabled"])

        def job():
            ai = self.app.ai
            if code == "explain":
                return ai.explain(text, lang)
            if code == "translate_ru2tr":
                return ai.translate(text, "ru2tr", lang)
            if code == "translate_tr2ru":
                return ai.translate(text, "tr2ru", lang)
            if code == "correct":
                return ai.correct(text, lang)
            from rca.i18n import SYSTEM_PROMPTS
            return ai.chat([{"role": "system", "content": SYSTEM_PROMPTS.get(lang)},
                            {"role": "user", "content": text}],
                           task="chat", model=model)

        def done(answer: str):
            self.send_btn.state(["!disabled"])
            self._write(answer or "(bos yanit)")
            if code == "correct":
                self._highlight_correction()

        def fail(err: Exception):
            self.send_btn.state(["!disabled"])
            self._write(f"{self.t('ai.offline')}\n\nAyrinti: {err}\n\n"
                        f"Kontrol listesi:\n"
                        f"1) LM Studio acik mi?\n"
                        f"2) 'Local Server' {self.app.ai.base} adresinde calisiyor mu?\n"
                        f"3) En az bir model yuklu mu?")
        self.app.worker.run(job, done, fail)
        return "break"

    def _highlight_correction(self) -> None:
        """Duzeltme ciktisindaki HATA/KURAL/DOGRU satirlarini renklendir."""
        p = self.palette()
        self.out.configure(state="normal")
        self.out.tag_configure("hata", foreground=p["err"])
        self.out.tag_configure("kural", foreground=p["warn"])
        self.out.tag_configure("dogru", foreground=p["ok"])
        for i, line in enumerate(self.out.get("1.0", "end").splitlines(), start=1):
            up = line.strip().upper()
            for prefix, tag in (("HATA", "hata"), ("КУРАЛ", "kural"),
                                ("KURAL", "kural"), ("DOGRU", "dogru"),
                                ("DOĞRU", "dogru")):
                if up.startswith(prefix):
                    self.out.tag_add(tag, f"{i}.0", f"{i}.end")
                    break
        self.out.configure(state="disabled")

    # ------------------------------------------------------------------
    def ask_image(self) -> None:
        """Gorsel sec ve vision modeline OCR/aciklama sor."""
        path = filedialog.askopenfilename(
            title="Gorsel sec",
            filetypes=[("Gorsel", "*.png *.jpg *.jpeg *.bmp"), ("Tumu", "*.*")])
        if not path:
            return
        prompt = self.inp.get("1.0", "end").strip() or (
            "Bu gorseldeki Rusca metni oku ve Turkceye cevir. "
            "Once metni oldugu gibi yaz, sonra cevirisini ver.")
        self._write(self.t("ai.thinking"))

        def job():
            data = Path(path).read_bytes()
            b64 = base64.b64encode(data).decode("ascii")
            return self.app.ai.describe_image(b64, prompt, self.app.ui_lang())

        def fail(err: Exception):
            msg = str(err)
            if "vision-model-yok" in msg:
                self._write("Gorsel destekli model bulunamadi.\n\n"
                            "LM Studio'ya bir vision modeli yukleyin "
                            "(orn. qwen2-vl-7b-instruct veya llava).\n"
                            "Alternatif: Tesseract OCR kurup metni elle yapistirin.")
            else:
                self._write(f"{self.t('ai.offline')}\n\n{err}")
        self.app.worker.run(job, self._write, fail)
