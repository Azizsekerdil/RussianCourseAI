# -*- coding: utf-8 -*-
"""Kaynak Merkezi sekmesi: acik lisansli e-kitap, ses, sozluk ve web kaynaklari."""
from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk

import rca_common as C
from rca import library as L
from rca.ui_util import Card, LazyTab, page_header, style_text

FILTERS = [("", "Tumu"), ("ebook", "E-kitap"), ("audio", "Ses"),
           ("data", "Sozluk / veri"), ("link", "Web"), ("video", "Video")]


class LibraryTab(LazyTab):
    """Katalogdan indirme, lisans gosterimi ve sozluk ice aktarma."""

    def build(self) -> None:
        p = self.palette()
        self.downloader = None
        self.current = None

        head = page_header(
            self, "Kaynak Merkezi",
            "Yalnizca lisansi dogrulanmis kaynaklar: kamu mali veya Creative Commons")
        head.pack(fill="x")
        ttk.Button(head, text="📂 Indirilenler klasoru",
                   command=self.open_folder).pack(side="right")
        ttk.Button(head, text=self.t("g.refresh"), style="Ghost.TButton",
                   command=self.reload).pack(side="right", padx=6)

        notice = Card(self, p, padding=12, fill=p["warn_soft"], outline=p["warn_soft"])
        notice.pack(fill="x", pady=(12, 10))
        notice.configure(height=64)
        tk.Label(notice.body, background=p["warn_soft"], foreground=p["warn"],
                 font=C.FONT_UI, justify="left", anchor="w",
                 text="Bu liste telifli materyal icermez. Her indirmenin yanina "
                      "lisans ve atif bilgisi LISANS.txt olarak yazilir; "
                      "CC BY-SA kaynaklarini paylasirken ayni lisansi korumalisiniz."
                 ).pack(anchor="w", fill="x")

        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 8))
        ttk.Label(bar, text="Tur:").pack(side="left")
        self.kind = tk.StringVar(value="Tumu")
        box = ttk.Combobox(bar, textvariable=self.kind, state="readonly", width=16,
                           values=[label for _c, label in FILTERS])
        box.pack(side="left", padx=6)
        box.bind("<<ComboboxSelected>>", lambda _e: self.reload())
        ttk.Label(bar, text="Ara:").pack(side="left", padx=(16, 4))
        self.q = tk.StringVar()
        e = ttk.Entry(bar, textvariable=self.q, width=26)
        e.pack(side="left")
        e.bind("<KeyRelease>", lambda _ev: self.reload())
        self.only_missing = tk.BooleanVar(value=False)
        ttk.Checkbutton(bar, text="Yalnizca indirilmemisler",
                        variable=self.only_missing,
                        command=self.reload).pack(side="left", padx=16)
        self.summary = ttk.Label(bar, text="", style="Dim.TLabel")
        self.summary.pack(side="right")

        pane = ttk.PanedWindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True)

        left = ttk.Frame(pane)
        cols = ("kind", "title", "level", "size", "lic", "state")
        self.tv = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        for c, w, t in (("kind", 110, "Tur"), ("title", 330, "Baslik"),
                        ("level", 80, "Seviye"), ("size", 80, "Boyut"),
                        ("lic", 150, "Lisans"), ("state", 90, "Durum")):
            self.tv.heading(c, text=t)
            self.tv.column(c, width=w, anchor="w")
        vs = ttk.Scrollbar(left, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=vs.set)
        self.tv.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")
        self.tv.bind("<<TreeviewSelect>>", self.on_select)
        self.tv.bind("<Double-1>", lambda _e: self.primary_action())
        pane.add(left, weight=3)

        right = ttk.Frame(pane, padding=(14, 0, 0, 0))
        self.d_title = ttk.Label(right, text="Bir kaynak secin", style="Title.TLabel",
                                 wraplength=340, justify="left")
        self.d_title.pack(anchor="w")
        self.d_meta = ttk.Label(right, text="", style="Dim.TLabel", wraplength=340,
                                justify="left")
        self.d_meta.pack(anchor="w", pady=(4, 0))
        self.d_note = ttk.Label(right, text="", style="TLabel", wraplength=340,
                                justify="left")
        self.d_note.pack(anchor="w", pady=(10, 0))

        lic = Card(right, p, padding=12)
        lic.pack(fill="x", pady=12)
        lic.configure(height=150)
        self.l_name = tk.Label(lic.body, text="", background=p["bg_alt"],
                               foreground=p["ok"], font=C.FONT_UI_BOLD, anchor="w")
        self.l_name.pack(anchor="w")
        self.l_note = tk.Label(lic.body, text="", background=p["bg_alt"],
                               foreground=p["fg_dim"], font=C.FONT_UI_SM,
                               wraplength=310, justify="left", anchor="w")
        self.l_note.pack(anchor="w", pady=(4, 0))
        self.l_attr = tk.Label(lic.body, text="", background=p["bg_alt"],
                               foreground=p["fg_mute"], font=C.FONT_UI_SM,
                               wraplength=310, justify="left", anchor="w")
        self.l_attr.pack(anchor="w", pady=(4, 0))

        self.btns = ttk.Frame(right)
        self.btns.pack(fill="x")
        self.btn_main = ttk.Button(self.btns, text=self.t("g.download"),
                                   style="Accent.TButton", command=self.primary_action)
        self.btn_main.pack(side="left")
        self.btn_open = ttk.Button(self.btns, text="Dosyayi ac", command=self.open_file)
        self.btn_open.pack(side="left", padx=6)
        self.btn_src = ttk.Button(self.btns, text="Kaynak sayfasi", style="Ghost.TButton",
                                  command=self.open_source)
        self.btn_src.pack(side="left")

        self.prog = ttk.Progressbar(right, mode="determinate")
        self.prog.pack(fill="x", pady=(12, 4))
        self.prog_lbl = ttk.Label(right, text="", style="Dim.TLabel")
        self.prog_lbl.pack(anchor="w")

        self.extra = ttk.Frame(right)
        self.extra.pack(fill="x", pady=(10, 0))
        pane.add(right, weight=2)

        self.reload()

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        """Sekmeye donuste indirilmis dosyalari yeniden isaretle."""
        if getattr(self, "tv", None) is not None:
            self.reload()

    def _filtered(self):
        """Filtrelere uyan kaynaklar."""
        label = self.kind.get()
        code = next((c for c, l in FILTERS if l == label), "")
        rows = L.by_kind(code)
        needle = self.q.get().strip().lower()
        if needle:
            rows = [r for r in rows
                    if needle in r.title.lower() or needle in r.provider.lower()
                    or needle in " ".join(r.tags).lower()]
        if self.only_missing.get():
            root = L.download_root()
            rows = [r for r in rows
                    if not (r.downloadable and r.target(root).exists())]
        return rows

    def reload(self) -> None:
        """Tabloyu doldur."""
        root = L.download_root()
        self.tv.delete(*self.tv.get_children())
        rows = self._filtered()
        have = 0
        for r in rows:
            if r.downloadable:
                exists = r.target(root).exists()
                have += 1 if exists else 0
                state = "✓ indirildi" if exists else f"{r.size_mb:.1f} MB"
                size = f"{r.size_mb:.1f} MB"
            else:
                state = "web"
                size = "-"
            self.tv.insert("", "end", iid=r.rid,
                           values=(L.KIND_LABELS.get(r.kind, r.kind), r.title,
                                   r.level or "-", size,
                                   r.license_info()["short"], state))
        dl = [r for r in rows if r.downloadable]
        self.summary.configure(
            text=f"{len(rows)} kaynak · indirilebilir {len(dl)} "
                 f"({L.total_size(dl):.0f} MB) · yerelde {have}")

    def on_select(self, _evt=None) -> None:
        """Sag paneli secili kaynaga gore doldur."""
        sel = self.tv.selection()
        if not sel:
            return
        r = L.get(sel[0])
        if not r:
            return
        self.current = r
        root = L.download_root()
        info = r.license_info()
        self.d_title.configure(text=r.title)
        bits = [r.provider, L.KIND_LABELS.get(r.kind, r.kind)]
        if r.level:
            bits.append(r.level)
        if r.downloadable:
            bits.append(f"{r.size_mb:.1f} MB")
        self.d_meta.configure(text="  ·  ".join(bits))
        self.d_note.configure(text=r.note)
        self.l_name.configure(text="Lisans: " + info["short"])
        self.l_note.configure(text=info.get("note", ""))
        self.l_attr.configure(text=("Atif: " + r.attribution) if r.attribution else "")

        exists = r.downloadable and r.target(root).exists()
        if r.downloadable:
            self.btn_main.configure(
                text="Yeniden indir" if exists else self.t("g.download"))
            self.btn_open.state(["!disabled"] if exists else ["disabled"])
        else:
            self.btn_main.configure(text="Tarayicida ac")
            self.btn_open.state(["disabled"])

        for c in self.extra.winfo_children():
            c.destroy()
        if exists and "iceaktarilabilir" in r.tags:
            self._build_import_box(r)
        elif exists and r.target(root).suffix.lower() == ".pdf":
            ttk.Button(self.extra, text="📕 PDF Okuyucuda ac", style="Accent.TButton",
                       command=lambda: self._open_in_reader(r)).pack(anchor="w")

    # ------------------------------------------------------------------
    def primary_action(self) -> None:
        """Indir veya tarayicida ac."""
        r = self.current
        if not r:
            return
        if not r.downloadable:
            self.open_source()
            return
        self.start_download(r)

    def start_download(self, r) -> None:
        """Kaynagi arka planda indir."""
        if self.downloader is not None:
            messagebox.showinfo(C.APP_NAME, "Zaten bir indirme suruyor.")
            return
        root = L.download_root()
        self.downloader = L.Downloader()
        self.prog.configure(value=0, maximum=100)
        self.prog_lbl.configure(text="Baglaniliyor...")
        self.btn_main.configure(text=self.t("g.cancel_dl"), command=self.cancel)

        def progress(done, total):
            def paint():
                if total:
                    self.prog.configure(value=100 * done / total)
                    self.prog_lbl.configure(
                        text=f"{done / 1048576:.1f} / {total / 1048576:.1f} MB")
                else:
                    self.prog_lbl.configure(text=f"{done / 1048576:.1f} MB")
            self.app.worker.post(paint)

        def job():
            return self.downloader.fetch(r, root, progress)

        def done(path):
            self.downloader = None
            self.prog.configure(value=100)
            self.prog_lbl.configure(text=f"Bitti: {Path(path).name}")
            self.btn_main.configure(text="Yeniden indir", command=self.primary_action)
            self.app.set_status(f"Indirildi: {Path(path).name}")
            self.reload()
            try:
                self.tv.selection_set(r.rid)
            except Exception:
                pass

        def fail(err):
            self.downloader = None
            self.prog.configure(value=0)
            self.btn_main.configure(text=self.t("g.download"),
                                    command=self.primary_action)
            if isinstance(err, InterruptedError):
                self.prog_lbl.configure(text="Durduruldu.")
                return
            self.prog_lbl.configure(text=f"Basarisiz: {err}")
            messagebox.showerror(C.APP_NAME,
                                 f"Indirilemedi:\n{err}\n\n"
                                 f"Adres: {r.url}\n"
                                 "Internet baglantinizi kontrol edin. "
                                 "Program indirme olmadan da tam calisir.")
        self.app.worker.run(job, done, fail)

    def cancel(self) -> None:
        """Suren indirmeyi durdur."""
        if self.downloader:
            self.downloader.cancel()
            self.prog_lbl.configure(text="Durduruluyor...")

    def open_source(self) -> None:
        """Kaynagin web sayfasini tarayicida ac."""
        if self.current:
            webbrowser.open(self.current.url)
            self.app.set_status("Tarayicida acildi")

    def open_file(self) -> None:
        """Indirilen dosyayi varsayilan programda ac."""
        r = self.current
        if not r or not r.downloadable:
            return
        path = r.target(L.download_root())
        if not path.exists():
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(path))              # noqa: S606
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as e:                        # noqa: BLE001
            messagebox.showerror(C.APP_NAME, str(e))

    def open_folder(self) -> None:
        """Indirilenler klasorunu ac."""
        root = L.download_root()
        root.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(root))              # noqa: S606
            else:
                subprocess.Popen(["xdg-open", str(root)])
        except Exception as e:                        # noqa: BLE001
            messagebox.showerror(C.APP_NAME, str(e))

    def _open_in_reader(self, r) -> None:
        """Indirilen PDF'i program icindeki okuyucuda ac."""
        path = r.target(L.download_root())
        widget = self.app.goto_tab("tab.pdf")
        if widget is not None and hasattr(widget, "load_pdf"):
            widget.load_pdf(str(path))

    # ------------------------------------------------------------------
    def _build_import_box(self, r) -> None:
        """OpenRussian TSV icin kelime bankasina aktarma kutusu."""
        p = self.palette()
        box = Card(self.extra, p, padding=12)
        box.pack(fill="x")
        box.configure(height=150)
        tk.Label(box.body, text="Kelime bankasina aktar", background=p["bg_alt"],
                 foreground=p["fg"], font=C.FONT_UI_BOLD, anchor="w").pack(anchor="w")
        tk.Label(box.body, background=p["bg_alt"], foreground=p["fg_dim"],
                 font=C.FONT_UI_SM, justify="left", wraplength=300, anchor="w",
                 text="Dosya siklik sirasindadir; en sik N kelime alinir. "
                      "Ceviriler INGILIZCEDIR - Turkce alani Ingilizce ile doldurulur, "
                      "sonradan duzenleyebilirsiniz.").pack(anchor="w", pady=(2, 8))
        row = tk.Frame(box.body, background=p["bg_alt"])
        row.pack(fill="x")
        tk.Label(row, text="Adet:", background=p["bg_alt"], foreground=p["fg"],
                 font=C.FONT_UI).pack(side="left")
        self.imp_count = tk.IntVar(value=500)
        ttk.Spinbox(row, from_=50, to=20000, increment=50, width=7,
                    textvariable=self.imp_count).pack(side="left", padx=6)
        ttk.Button(row, text="Aktar", style="OK.TButton",
                   command=lambda: self._do_import(r)).pack(side="left", padx=6)
        self.imp_lbl = tk.Label(box.body, text="", background=p["bg_alt"],
                                foreground=p["fg_dim"], font=C.FONT_UI_SM, anchor="w")
        self.imp_lbl.pack(anchor="w", pady=(6, 0))

    def _do_import(self, r) -> None:
        """Ice aktarmayi arka planda calistir."""
        path = r.target(L.download_root())
        limit = int(self.imp_count.get())
        deck = f"OpenRussian ({r.title.split('-')[-1].strip()})"
        self.imp_lbl.configure(text="Aktariliyor...")

        def job():
            return L.import_openrussian(path, self.repos, limit=limit, deck=deck)

        def done(stats):
            self.imp_lbl.configure(
                text=f"{stats['added']} kelime eklendi · {stats['skipped']} atlandi")
            self.app.set_status(f"{stats['added']} kelime bankaya aktarildi ({deck})")

        def fail(err):
            self.imp_lbl.configure(text=f"Basarisiz: {err}")
        self.app.worker.run(job, done, fail)
