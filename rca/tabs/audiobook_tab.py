# -*- coding: utf-8 -*-
"""Sesli Kitap sayfasi: PDF kitaplari bolum / sayfa secerek dinle.

* Sol: kitabin icindekiler agaci (bolum -> alt bolum -> sayfa), her sayfanin
  secili motor icin uretilip uretilmedigi (✓) gorunur. Cift tik = oradan cal.
* Sag: calar (oynat/duraklat, ±10 sn, onceki/sonraki cumle, onceki/sonraki
  sayfa, hiz, ses, cumle tekrari, surekli calma) ve o anki cumlenin vurgulandigi
  metin paneli (tikla = o cumleye atla).
* Alt: motor secimi (Piper varsayilan / Edge), dile gore ses, konusma hizi,
  "varsayilan yap", secileni / tumunu uret, bolum MP3'lerini disa aktar,
  Whisper ile dogrulama.
"""
from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

import rca_common as C
from rca import audio_player as AP
from rca import audiobook as A
from rca.tabs.whisper_tab import open_path
from rca.ui_util import LazyTab, style_text


class AudiobookTab(LazyTab):
    """Bolum secmeli sesli kitap dinleyici + uretici."""

    # ------------------------------------------------------------------ kurulum
    def build(self) -> None:
        s = self.app.settings
        self.book: Optional[A.Book] = None
        self.player = AP.AudioPlayer()
        self.player.speed = float(s.get("ab_speed", 1.0) or 1.0)
        self.player.volume = float(s.get("ab_volume", 1.0) or 1.0)
        self.playlist: List[int] = []
        self.pl_index = -1
        self.page = 0
        self.timings: List[dict] = []
        self.cur_seg = -1
        self.repeat_seg = -1
        self.cancel = threading.Event()
        self.busy = False
        self._loading = False
        self._load_req = 0              # yalnizca en son sayfa yuklemesinin sonucu uygulanir

        root = ttk.Frame(self, padding=(2, 2))
        root.pack(fill="both", expand=True)

        # --- ust: kitap secimi ----------------------------------------------
        top = ttk.Frame(root)
        top.pack(fill="x")
        ttk.Label(top, text=self.t("ab.book")).pack(side="left")
        self.book_var = tk.StringVar()
        self.book_box = ttk.Combobox(top, textvariable=self.book_var, state="readonly", width=44)
        self.book_box.pack(side="left", padx=6)
        self.book_box.bind("<<ComboboxSelected>>", lambda _e: self._on_book_pick())
        ttk.Button(top, text=self.t("ab.new_book"), command=self.new_book).pack(side="left")
        ttk.Button(top, text="📂", width=3, command=self._open_book_dir).pack(side="left", padx=4)
        self.resume_btn = ttk.Button(top, text="⏯ " + self.t("ab.resume"), command=self.resume)
        self.resume_btn.pack(side="right")
        self.book_info = ttk.Label(root, text="", style="Dim.TLabel")
        self.book_info.pack(fill="x", pady=(4, 6))

        # Uretim paneli ONCE (altta) yerlestirilir: pencere kucukken bile gorunur
        # kalir, kalan alani agac + calar paylasir.
        gen = ttk.LabelFrame(root, text=self.t("ab.generation"), padding=8)
        gen.pack(side="bottom", fill="x", pady=(8, 0))

        pane = ttk.PanedWindow(root, orient="horizontal")
        pane.pack(fill="both", expand=True)

        # --- sol: icindekiler ------------------------------------------------
        left = ttk.Frame(pane)
        pane.add(left, weight=2)
        self.tree = ttk.Treeview(left, columns=("pages", "st"), show="tree headings", selectmode="extended",
                                 height=8)
        self.tree.heading("#0", text=self.t("ab.contents"))
        self.tree.heading("pages", text=self.t("ab.pages"))
        self.tree.heading("st", text="")
        self.tree.column("#0", width=290, minwidth=160, stretch=True)
        self.tree.column("pages", width=70, minwidth=50, anchor="center", stretch=False)
        self.tree.column("st", width=50, minwidth=40, anchor="center", stretch=False)
        ysb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ysb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        ysb.pack(side="left", fill="y")
        self.tree.bind("<Double-1>", lambda _e: self.play_selection())
        self.tree.bind("<Return>", lambda _e: self.play_selection())

        # --- sag: calar + metin ---------------------------------------------
        right = ttk.Frame(pane, padding=(10, 0, 0, 0))
        pane.add(right, weight=3)
        self.now_lbl = ttk.Label(right, text=self.t("ab.nothing"), style="Title.TLabel")
        self.now_lbl.pack(anchor="w")
        self.sub_lbl = ttk.Label(right, text="", style="Dim.TLabel")
        self.sub_lbl.pack(anchor="w")

        self.pos_var = tk.DoubleVar(value=0)
        self.scale = ttk.Scale(right, from_=0, to=1, variable=self.pos_var, orient="horizontal",
                               command=self._on_scrub)
        self.scale.pack(fill="x", pady=(8, 0))
        self.scale.bind("<ButtonRelease-1>", lambda _e: self._commit_scrub())
        self._scrubbing = False
        tl = ttk.Frame(right)
        tl.pack(fill="x")
        self.time_lbl = ttk.Label(tl, text="0:00 / 0:00", style="Mute.TLabel")
        self.time_lbl.pack(side="left")
        self.total_lbl = ttk.Label(tl, text="", style="Mute.TLabel")
        self.total_lbl.pack(side="right")

        ctl = ttk.Frame(right)
        ctl.pack(fill="x", pady=6)
        btn = lambda txt, cmd, **kw: ttk.Button(ctl, text=txt, command=cmd, width=kw.get("w", 4),
                                                style=kw.get("style", "TButton"))
        btn("⏮", lambda: self.step_page(-1)).pack(side="left")
        btn("⏪", lambda: self.step_seg(-1)).pack(side="left", padx=2)
        btn("−10", lambda: self.player.skip(-10)).pack(side="left")
        self.play_btn = btn("▶", self.toggle, w=5, style="Accent.TButton")
        self.play_btn.pack(side="left", padx=4)
        btn("+10", lambda: self.player.skip(10)).pack(side="left")
        btn("⏩", lambda: self.step_seg(1)).pack(side="left", padx=2)
        btn("⏭", lambda: self.step_page(1)).pack(side="left")
        btn("■", self.stop).pack(side="left", padx=(6, 0))

        ctl2 = ttk.Frame(right)
        ctl2.pack(fill="x")
        self.rep_var = tk.BooleanVar(value=False)
        self.cont_var = tk.BooleanVar(value=bool(self.app.settings.get("ab_continuous", True)))
        ttk.Label(ctl2, text=self.t("ab.speed")).pack(side="left")
        self.speed_var = tk.StringVar(value=f"{self.player.speed:g}x")
        sp = ttk.Combobox(ctl2, textvariable=self.speed_var, state="readonly", width=6,
                          values=[f"{x:g}x" for x in AP.SPEEDS])
        sp.pack(side="left", padx=(4, 14))
        sp.bind("<<ComboboxSelected>>", lambda _e: self._on_speed())
        ttk.Label(ctl2, text=self.t("ab.volume")).pack(side="left")
        self.vol_var = tk.DoubleVar(value=self.player.volume)
        ttk.Scale(ctl2, from_=0, to=1.5, variable=self.vol_var, orient="horizontal", length=140,
                  command=lambda v: (self.player.set_volume(float(v)), self._save_prefs())).pack(side="left", padx=4)
        ttk.Button(ctl2, text=self.t("ab.verify"), command=self.verify_current).pack(side="right")

        ctl3 = ttk.Frame(right)
        ctl3.pack(fill="x", pady=(4, 0))
        ttk.Checkbutton(ctl3, text=self.t("ab.repeat"), variable=self.rep_var,
                        command=self._on_repeat).pack(side="left")
        ttk.Checkbutton(ctl3, text=self.t("ab.continuous"), variable=self.cont_var,
                        command=self._save_prefs).pack(side="left", padx=12)

        # width kucuk tutulur: istenen genislik dusuk olunca PanedWindow agaca da yer birakir
        self.text = tk.Text(right, wrap="word", width=40, height=8, font=C.FONT_RU, cursor="hand2")
        style_text(self.text, self.palette())
        self.text.pack(fill="both", expand=True, pady=(8, 0))
        p = self.palette()
        self.text.tag_configure("cur", background=p["accent_soft"], foreground=p["fg"])
        self.text.tag_configure("ru", foreground=p["fg"])
        self.text.tag_configure("tr", foreground=p["ok"])
        self.text.tag_configure("en", foreground=p["fg_dim"])
        self.text.tag_configure("heading", font=(C.FONT_FAMILY, 13, "bold"))
        self.text.tag_configure("bad", underline=True, foreground=p["err"])
        self.text.bind("<Button-1>", self._on_text_click)
        self.text.configure(state="disabled")

        # --- alt: uretim (cerceve yukarida, altta yerlestirildi) ---------------
        r1 = ttk.Frame(gen)
        r1.pack(fill="x")
        ttk.Label(r1, text=self.t("ab.engine")).pack(side="left")
        self.engine_var = tk.StringVar(value=self.app.settings.get("ab_engine", "piper") or "piper")
        ttk.Radiobutton(r1, text="Piper (" + self.t("ab.offline") + ")", value="piper",
                        variable=self.engine_var, command=self._on_engine).pack(side="left", padx=(6, 0))
        ttk.Radiobutton(r1, text="Edge (" + self.t("ab.online") + ")", value="edge",
                        variable=self.engine_var, command=self._on_engine).pack(side="left", padx=6)
        self.default_btn = ttk.Button(r1, text=self.t("ab.make_default"), command=self.make_default)
        self.default_btn.pack(side="left", padx=6)
        self.default_lbl = ttk.Label(r1, text="", style="Mute.TLabel")
        self.default_lbl.pack(side="left")
        ttk.Label(r1, text=self.t("ab.rate")).pack(side="left", padx=(16, 4))
        self.rate_var = tk.StringVar(value=str(self.app.settings.get("ab_rate", 1.0) or 1.0))
        ttk.Spinbox(r1, from_=0.6, to=1.5, increment=0.05, width=5, textvariable=self.rate_var,
                    command=self._save_prefs).pack(side="left")

        r2 = ttk.Frame(gen)
        r2.pack(fill="x", pady=(6, 0))
        self.voice_vars = {}
        self.voice_boxes = {}
        for lang in A.LANGS:
            ttk.Label(r2, text=A.LANG_NAMES[lang] + ":").pack(side="left", padx=(0, 4))
            var = tk.StringVar()
            box = ttk.Combobox(r2, textvariable=var, state="readonly", width=22)
            box.pack(side="left", padx=(0, 12))
            box.bind("<<ComboboxSelected>>", lambda _e: self._save_prefs())
            self.voice_vars[lang], self.voice_boxes[lang] = var, box
        ttk.Button(r2, text=self.t("ab.try_voice"), command=self.try_voice).pack(side="left")

        r3 = ttk.Frame(gen)
        r3.pack(fill="x", pady=(6, 0))
        ttk.Button(r3, text=self.t("ab.gen_sel"), style="Accent.TButton",
                   command=lambda: self.generate(False)).pack(side="left")
        ttk.Button(r3, text=self.t("ab.gen_all"), command=lambda: self.generate(True)).pack(side="left", padx=4)
        ttk.Button(r3, text="■ " + self.t("wh.cancel"), command=self.cancel.set).pack(side="left")
        self.force_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(r3, text=self.t("ab.force"), variable=self.force_var).pack(side="left", padx=8)
        ttk.Button(r3, text=self.t("ab.export"), command=self.export).pack(side="right")
        self.gen_bar = ttk.Progressbar(gen, mode="determinate", maximum=1000)
        self.gen_bar.pack(fill="x", pady=(6, 0))
        self.gen_lbl = ttk.Label(gen, text="", style="Dim.TLabel")
        self.gen_lbl.pack(fill="x")

        ok, why = AP.available()
        if not ok:
            self.sub_lbl.configure(text=why, style="Warn.TLabel")
        self._pane = pane
        self.after(150, self._place_sash)
        self._on_engine(save=False)
        self._load_books()
        self._tick()

    def _place_sash(self) -> None:
        """Ayiriciyi %40'a koy (agacin sayfa / durum sutunlari gorunsun)."""
        try:
            w = self._pane.winfo_width()
            if w > 100:
                self._pane.sashpos(0, int(w * 0.4))
        except tk.TclError:
            pass

    # ================================================================ kitaplar
    def _load_books(self, select: str = "") -> None:
        books = A.list_books()
        self._books = {f"{b.title}  ({b.page_count} s.)": b.id for b in books}
        self.book_box["values"] = list(self._books)
        want = select or self.app.settings.get("ab_book", "")
        label = next((k for k, v in self._books.items() if v == want), None)
        if label is None and self._books:
            label = next(iter(self._books))
        if label:
            self.book_var.set(label)
            self._on_book_pick()
        else:
            self.book_info.configure(text=self.t("ab.no_books"))

    def _on_book_pick(self) -> None:
        bid = self._books.get(self.book_var.get())
        if not bid:
            return
        if self.book is not None and self.book.id != bid:
            # Kitap degisti: eski kitabin konumunu kaydet, calari ve durumu sifirla
            self._remember()
            self._unload()
        try:
            self.book = A.Book(A.AUDIOBOOK_DIR / bid)
        except Exception as e:                                  # noqa: BLE001
            self.book_info.configure(text=f"{self.t('g.error')}: {e}", style="Err.TLabel")
            return
        self.app.settings["ab_book"] = bid
        C.save_settings(self.app.settings)
        self._fill_tree()

    def _fill_tree(self) -> None:
        self.tree.delete(*self.tree.get_children())
        b = self.book
        if b is None:
            return
        eng = self.engine_var.get()
        made = sum(b.has_audio(eng, p) for p in range(1, b.page_count + 1))
        src = {"curated": self.t("ab.src_curated"), "mixed": self.t("ab.src_mixed")}.get(
            b.script_source(), self.t("ab.src_heuristic"))
        self.book_info.configure(text=self.t("ab.book_info").format(
            pages=b.page_count, made=made, eng=eng, src=src), style="Dim.TLabel")

        def mark(pages):
            n = sum(b.has_audio(eng, p) for p in pages)
            return "✓" if n == len(pages) else (f"{n}/{len(pages)}" if n else "")

        def add(parent, sec: A.Section):
            iid = f"s:{sec.first}:{sec.last}:{sec.index}"
            rng = f"{sec.first}" if sec.first == sec.last else f"{sec.first}–{sec.last}"
            self.tree.insert(parent, "end", iid=iid, text=sec.title, values=(rng, mark(sec.pages)))
            covered = set()
            for ch in sec.children:
                covered.update(ch.pages)

            def page_node(p):
                self.tree.insert(iid, "end", iid=f"p:{p}:{sec.index}", text=f"{self.t('ab.page')} {p}",
                                 values=(p, "✓" if b.has_audio(eng, p) else ""))
            first_child = sec.children[0].first if sec.children else sec.last + 1
            for p in sec.pages:                      # alt bolumlerden onceki sayfalar
                if p < first_child and p not in covered:
                    page_node(p)
            for ch in sec.children:
                add(iid, ch)
            for p in sec.pages:                      # alt bolumlerin arasinda / sonrasinda kalanlar
                if p >= first_child and p not in covered:
                    page_node(p)
        for sec in b.sections():
            add("", sec)

    def _selected_pages(self) -> List[int]:
        pages: List[int] = []
        for iid in self.tree.selection():
            parts = iid.split(":")
            if parts[0] == "p":
                pages.append(int(parts[1]))
            elif parts[0] == "s":
                pages += list(range(int(parts[1]), int(parts[2]) + 1))
        return sorted(dict.fromkeys(pages))

    def new_book(self) -> None:
        if self.busy:                    # baska bir is (uretim / disa aktarma) suruyor
            return
        pdf = filedialog.askopenfilename(parent=self, filetypes=[("PDF", "*.pdf")],
                                         initialdir=str(C.RESOURCES_DIR))
        if not pdf:
            return
        script = None
        if messagebox.askyesno(C.APP_NAME, self.t("ab.ask_script"), parent=self):
            script = filedialog.askdirectory(parent=self, title=self.t("ab.script_dir")) or None
        if self.busy:
            return
        title = Path(pdf).stem.replace("_", " ").replace("+", " ")
        self.busy = True
        self.gen_lbl.configure(text=self.t("ab.creating"))

        def prog(msg, frac):
            self.app.worker.post(lambda: (self.gen_bar.configure(value=int(frac * 1000)),
                                          self.gen_lbl.configure(text=msg)))

        def done(book):
            self.busy = False
            self.gen_lbl.configure(text=self.t("ab.created").format(title=book.title))
            self._load_books(select=book.id)

        def err(e):
            self.busy = False
            self.gen_lbl.configure(text=f"{self.t('g.error')}: {e}")
        self.app.worker.run(lambda: A.create_book(pdf, title, script, prog), done, err)

    def _open_book_dir(self) -> None:
        if self.book:
            open_path(self.book.root)
        else:
            A.AUDIOBOOK_DIR.mkdir(parents=True, exist_ok=True)
            open_path(A.AUDIOBOOK_DIR)

    # ================================================================ motor / ses
    def _engine(self):
        name = self.engine_var.get()
        voices = {lang: var.get() for lang, var in self.voice_vars.items() if var.get()}
        try:
            rate = float(self.rate_var.get())
        except ValueError:
            rate = 1.0
        return A.make_engine(name, voices, rate)

    def _on_engine(self, save: bool = True) -> None:
        name = self.engine_var.get()
        cat = A.PIPER_VOICES if name == "piper" else A.EDGE_VOICES
        saved = (self.app.settings.get("ab_voices") or {}).get(name, {})
        installed = set(A.PiperTTS.installed_voices()) if name == "piper" else None
        for lang, box in self.voice_boxes.items():
            vals = list(cat[lang])
            if installed is not None:
                vals += [v for v in sorted(installed) if v.startswith(lang) and v not in vals]
            box["values"] = vals
            self.voice_vars[lang].set(saved.get(lang) if saved.get(lang) in vals else vals[0])
        default = self.app.settings.get("ab_engine", "piper")
        self.default_lbl.configure(text=self.t("ab.default_is").format(name=default.capitalize()))
        ok, why = self._engine().status()
        self.gen_lbl.configure(text=why, style="Dim.TLabel" if ok else "Warn.TLabel")
        if save:
            self._save_prefs()
        if self.book is not None:
            self._fill_tree()
        # Calan sayfa varsa yeni motorun sesine gec; calma listesi yalnizca bu motorda
        # uretilmis sayfalardan olussun
        if self.page and self.book is not None:
            book, page = self.book, self.page
            if book.has_audio(name, page):
                self.playlist = [p for p in self.playlist if book.has_audio(name, p)]
                self.pl_index = sum(1 for p in self.playlist if p <= page) - 1
                self._load_page(page, start=self.player.position(), autoplay=self.player.playing)
            else:
                # Bu motorda sayfa yok: eski motorun sesi calmaya devam etmesin
                self._remember()
                self._unload(msg=f"{self.t('ab.page')} {page} · {name.capitalize()}: ✗")

    def make_default(self) -> None:
        self.app.settings["ab_engine"] = self.engine_var.get()
        C.save_settings(self.app.settings)
        self._on_engine(save=True)
        self.app.set_status(self.t("ab.default_saved").format(name=self.engine_var.get().capitalize()))

    def _save_prefs(self) -> None:
        s = self.app.settings
        voices = dict(s.get("ab_voices") or {})
        voices[self.engine_var.get()] = {lang: var.get() for lang, var in self.voice_vars.items()}
        s["ab_voices"] = voices
        try:
            s["ab_rate"] = round(float(self.rate_var.get()), 2)
        except ValueError:
            pass
        s["ab_speed"] = self.player.target_speed
        s["ab_volume"] = round(self.player.volume, 2)
        s["ab_continuous"] = bool(self.cont_var.get())
        C.save_settings(s)

    def try_voice(self) -> None:
        """Secili seslerle kisa bir ornek cal."""
        eng = self._engine()
        samples = [("ru", "Здравствуйте! Это пример русского голоса."),
                   ("tr", "Merhaba! Bu Türkçe sesin bir örneği."),
                   ("en", "Hello! This is a sample of the English voice.")]

        def job():
            import numpy as np
            parts = []
            for lang, text in samples:
                parts += [eng.synth(text, lang), A.silence(400, eng.sample_rate)]
            AP.play_pcm_blocking(np.concatenate(parts), eng.sample_rate)
        self.gen_lbl.configure(text=self.t("ab.trying"))
        self.app.worker.run(job, lambda _r: self.gen_lbl.configure(text=""),
                            lambda e: self.gen_lbl.configure(text=f"{self.t('g.error')}: {e}"))

    # ================================================================ uretim
    def generate(self, everything: bool) -> None:
        if self.book is None or self.busy:
            return
        pages = list(range(1, self.book.page_count + 1)) if everything else self._selected_pages()
        if not pages:
            messagebox.showinfo(C.APP_NAME, self.t("ab.select_first"), parent=self)
            return
        eng = self._engine()
        ok, why = eng.status()
        download: List[str] = []
        if not ok:
            if eng.name == "piper" and A.PiperTTS.installed() and \
                    messagebox.askyesno(C.APP_NAME, self.t("ab.dl_voices").format(v=why), parent=self):
                # Eksik sesler surec havuzu baslamadan ONCE, tek sefer indirilir; aksi halde
                # her surec ayni modeli indirip yarim yazilmis dosyayi yukleyebilir.
                download = list(eng.missing_voices())
            else:
                messagebox.showwarning(C.APP_NAME, why, parent=self)
                return
        if eng.name == "edge" and not self.app.settings.get("ab_edge_ok"):
            if not messagebox.askyesno(C.APP_NAME, self.t("ab.edge_privacy"), parent=self):
                return
            self.app.settings["ab_edge_ok"] = True
            C.save_settings(self.app.settings)
        self.busy = True
        self.cancel.clear()
        self.gen_bar["value"] = 0
        book, force = self.book, bool(self.force_var.get())
        workers = A.default_workers(eng)

        def prog(k, total, page, made):
            def ui():
                self.gen_bar["value"] = int(k / total * 1000)
                self.gen_lbl.configure(text=self.t("ab.gen_prog").format(k=k, total=total, page=page),
                                       style="Dim.TLabel")
                # Yalnizca gercekten sesi olan sayfa isaretlenir (hata / iptal degil) ve
                # yalnizca agac hala ayni kitap + motoru gosteriyorsa
                if self.book is book and self.engine_var.get() == eng.name and \
                        (made or book.has_audio(eng.name, page)):
                    for iid in self.tree.get_children(""):
                        self._mark_page(iid, page)
            self.app.worker.post(ui)

        def job():
            for v in download:
                if self.cancel.is_set():
                    break
                self.app.worker.post(lambda v=v: self.gen_lbl.configure(text=f"⬇ {v}", style="Dim.TLabel"))
                A.PiperTTS.download_voice(v)
            return A.render_pages(book, eng, pages, force=force, on_progress=prog,
                                  cancel=self.cancel, workers=workers)

        def done(res):
            self.busy = False
            msg = self.t("ab.gen_done").format(n=res["rendered"], skip=res["skipped"], fail=len(res["failed"]))
            if res["failed"]:
                msg += " · " + "; ".join(f"s.{p}: {e[:60]}" for p, e in res["failed"][:3])
            self.gen_lbl.configure(text=msg, style="Warn.TLabel" if res["failed"] else "OK.TLabel")
            self._fill_tree()

        def err(e):
            self.busy = False
            self.gen_lbl.configure(text=f"{self.t('g.error')}: {e}", style="Err.TLabel")
            self._fill_tree()                      # yarim kalan isaretleri diskteki duruma esitle
        self.app.worker.run(job, done, err)

    def _mark_page(self, parent: str, page: int) -> None:
        for iid in self.tree.get_children(parent):
            if iid.startswith(f"p:{page}:"):
                self.tree.set(iid, "st", "✓")
            self._mark_page(iid, page)

    def export(self) -> None:
        if self.book is None or self.busy:
            return
        eng = self.engine_var.get()
        out = filedialog.askdirectory(parent=self, title=self.t("ab.export_dir"),
                                      initialdir=str(self.book.export_dir(eng).parent))
        if not out:
            return
        self.busy = True
        book = self.book

        def prog(k, n, title):
            self.app.worker.post(lambda: (self.gen_bar.configure(value=int(k / n * 1000)),
                                          self.gen_lbl.configure(text=f"[{k}/{n}] {title}")))

        def done(path):
            self.busy = False
            self.gen_lbl.configure(text=f"{self.t('ab.exported')}: {path}", style="OK.TLabel")
            open_path(path)

        def err(e):
            self.busy = False
            self.gen_lbl.configure(text=f"{self.t('g.error')}: {e}", style="Err.TLabel")
        self.app.worker.run(lambda: A.export_sections(book, eng, Path(out), on_progress=prog), done, err)

    # ================================================================ calma
    def play_selection(self) -> None:
        pages = self._selected_pages()
        if not pages or self.book is None:
            return
        eng = self.engine_var.get()
        ready = [p for p in pages if self.book.has_audio(eng, p)]
        if not ready:
            if messagebox.askyesno(C.APP_NAME, self.t("ab.not_made"), parent=self):
                self.generate(False)
            return
        self.playlist = ready
        self.pl_index = 0
        self._load_page(ready[0], autoplay=True)

    def resume(self) -> None:
        last = self.app.settings.get("ab_last") or {}
        if not last or self.book is None:
            return
        if last.get("book") != self.book.id:
            if last.get("book") not in getattr(self, "_books", {}).values():
                # Kayitli kitap silinmis / yeniden adlandirilmis: baska kitabi calma
                self.sub_lbl.configure(text=f"{self.t('ab.resume')}: ✗ {last.get('book', '')}",
                                       style="Warn.TLabel")
                return
            self._load_books(select=last.get("book", ""))
            if self.book is None or self.book.id != last.get("book"):
                return
        page = int(last.get("page", 0) or 0)
        if page and self.book.has_audio(self.engine_var.get(), page):
            self.playlist = [page]
            self.pl_index = 0
            self._load_page(page, start=float(last.get("pos", 0)), autoplay=True)

    def _load_page(self, page: int, start: float = 0.0, autoplay: bool = True) -> bool:
        """Sayfayi yukle. Bu motorda sayfa sesi yoksa False (durum satirinda belirtilir)."""
        if self.book is None:
            return False
        eng = self.engine_var.get()
        if not self.book.has_audio(eng, page):
            self.sub_lbl.configure(text=f"{self.t('ab.page')} {page} · {eng.capitalize()}: ✗",
                                   style="Warn.TLabel")
            return False
        path = self.book.page_audio(eng, page)
        self.page = page
        try:
            self.timings = self.book.timings(eng, page)
        except (ValueError, OSError):              # yarim yazilmis / bozuk zamanlama dosyasi
            self.timings = []
        self.cur_seg = -1
        self.repeat_seg = -1                       # tekrar, yeni sayfada duyulan ilk cumleyi alir
        self._render_text()
        section = self.book.section_of(page)
        self.now_lbl.configure(text=f"{self.t('ab.page')} {page} · {section}")
        self.sub_lbl.configure(text=f"{self.book.title} · {eng.capitalize()}", style="Dim.TLabel")
        # Ust uste yuklemelerde yalnizca en son istegin sonucu uygulanir (sira Tk thread'inde)
        self._load_req += 1
        req = self._load_req
        gen = self.player.request_load()
        self._loading = True

        def job():
            return self.player.load(str(path), start=start, autoplay=autoplay, gen=gen)

        def done(dur):
            if req != self._load_req:
                return
            self._loading = False
            if dur is None:
                return
            self.scale.configure(to=max(1.0, dur))
            self.total_lbl.configure(text=self._fmt(dur))
            self._select_in_tree(page)

        def err(e):
            if req != self._load_req:
                return
            self._loading = False
            self.sub_lbl.configure(text=f"{self.t('g.error')}: {e}", style="Err.TLabel")
        self.app.worker.run(job, done, err)
        return True

    def _unload(self, msg: str = "") -> None:
        """Calari bosalt ve calma durumunu sifirla (kitap / motor degisince)."""
        self._load_req += 1                        # bekleyen yukleme sonuclari yok sayilir
        self._loading = False
        self.player.unload()
        self.page = 0
        self.playlist, self.pl_index = [], -1
        self.timings = []
        self.cur_seg = self.repeat_seg = -1
        self.rep_var.set(False)
        self._render_text()
        self.now_lbl.configure(text=self.t("ab.nothing"))
        self.sub_lbl.configure(text=msg, style="Warn.TLabel" if msg else "Dim.TLabel")
        self.pos_var.set(0)
        self.scale.configure(to=1)
        self.time_lbl.configure(text="0:00 / 0:00")
        self.total_lbl.configure(text="")

    def _select_in_tree(self, page: int) -> None:
        def find(parent):
            for iid in self.tree.get_children(parent):
                if iid.startswith(f"p:{page}:"):
                    return iid
                hit = find(iid)
                if hit:
                    return hit
            return None
        iid = find("")
        if iid:
            self.tree.see(iid)

    def toggle(self) -> None:
        if self.player.path is None:
            if self.tree.selection():
                self.play_selection()
            return
        self.player.toggle()

    def stop(self) -> None:
        self.player.stop()
        self._remember()

    def step_page(self, delta: int) -> None:
        if self.book is None or not self.page:
            return
        eng = self.engine_var.get()
        i = self.pl_index + delta
        while self.playlist and 0 <= i < len(self.playlist):
            if self._load_page(self.playlist[i], autoplay=True):
                self.pl_index = i
                return
            i += delta                                   # yuklenemeyen sayfayi atla
        p = self.page + delta
        while 1 <= p <= self.book.page_count and not self.book.has_audio(eng, p):
            p += delta
        if 1 <= p <= self.book.page_count:
            self.playlist, self.pl_index = [p], 0
            self._load_page(p, autoplay=True)

    def step_seg(self, delta: int) -> None:
        if not self.timings:
            return
        i = self.cur_seg                                 # -1: henuz cumle yok -> sonraki = ilk cumle
        pos = self.player.position()
        if delta < 0 and 0 <= i < len(self.timings) and pos - self.timings[i].get("start", 0.0) > 1.0:
            target = i                                   # once cumlenin basina don
        else:
            target = max(0, min(len(self.timings) - 1, i + delta))
        self.player.seek(self.timings[target].get("start", 0.0))
        if self.repeat_seg >= 0:
            self.repeat_seg = target

    def _on_repeat(self) -> None:
        self.repeat_seg = self.cur_seg if self.rep_var.get() and self.cur_seg >= 0 else -1

    def _on_speed(self) -> None:
        try:
            speed = float(self.speed_var.get().rstrip("x"))
        except ValueError:
            return
        pl = self.player
        gen = pl.request_speed(speed)
        if not gen:                                      # bekleyen sayfa yuklemesi yeni hizi kullanir
            self._save_prefs()
            return

        def err(e):
            if not pl.is_current(gen):
                return
            # Hiz uygulanamadi: kutu uygulanmis hizi gostersin
            self.speed_var.set(f"{pl.speed:g}x")
            self.sub_lbl.configure(text=f"{self.t('g.error')}: {e}", style="Err.TLabel")
        self.app.worker.run(lambda: pl.set_speed(speed, gen=gen), lambda _r: self._save_prefs(), err)

    def _on_scrub(self, _v) -> None:
        self._scrubbing = True

    def _commit_scrub(self) -> None:
        self.player.seek(float(self.pos_var.get()))
        self._scrubbing = False

    # -- metin paneli --------------------------------------------------------
    def _render_text(self) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        for seg in self.timings:
            tags = (f"s{seg['i']}", seg["lang"]) + (("heading",) if seg["kind"] == "heading" else ())
            sep = "\n" if seg["kind"] in ("heading", "text", "gloss", "example", "note") else "  —  "
            self.text.insert("end", seg["text"], tags)
            self.text.insert("end", sep)
        self.text.configure(state="disabled")

    def _on_text_click(self, evt) -> None:
        idx = self.text.index(f"@{evt.x},{evt.y}")
        for tag in self.text.tag_names(idx):
            if tag.startswith("s") and tag[1:].isdigit():
                i = int(tag[1:])
                if 0 <= i < len(self.timings):
                    self.player.seek(self.timings[i]["start"])
                    if not self.player.playing:
                        self.player.play()
                    if self.repeat_seg >= 0:
                        self.repeat_seg = i
                return

    def _highlight(self, i: int) -> None:
        self.text.tag_remove("cur", "1.0", "end")
        if i < 0:
            return
        rng = self.text.tag_ranges(f"s{i}")
        if rng:
            self.text.tag_add("cur", rng[0], rng[1])
            self.text.see(rng[0])

    # -- periyodik guncelleme ------------------------------------------------
    @staticmethod
    def _fmt(t: float) -> str:
        m, s = divmod(int(max(0, t)), 60)
        return f"{m}:{s:02d}"

    def _tick(self) -> None:
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        # Govdedeki tek bir hata dongunun kalici olarak durmasina yol acmasin
        try:
            self._tick_body()
        except Exception as e:                          # noqa: BLE001
            try:
                self.sub_lbl.configure(text=f"{self.t('g.error')}: {e}", style="Err.TLabel")
            except Exception:                           # noqa: BLE001
                pass
        finally:
            try:
                if self.winfo_exists():
                    self.after(120, self._tick)
            except tk.TclError:
                pass

    def _tick_body(self) -> None:
        pl = self.player
        self.play_btn.configure(text="⏸" if pl.playing else "▶")
        if pl.path and not self._loading:
            pos = pl.position()
            if not self._scrubbing:
                self.pos_var.set(pos)
            self.time_lbl.configure(text=f"{self._fmt(pos)} / {self._fmt(pl.duration)}"
                                         + (f" · {pl.speed:g}x" if pl.speed != 1 else ""))
            # o anki cumle
            cur = -1
            for seg in self.timings:
                if seg.get("start", 0.0) - 0.05 <= pos:
                    cur = seg.get("i", cur)
                else:
                    break
            # bayat tekrar indeksi (baska sayfadan kalmis) sayfa sonu ilerlemesini engellemesin
            if self.repeat_seg >= len(self.timings):
                self.repeat_seg = -1
            # cumle tekrari: cumlenin sonunu gectiyse basa don
            if self.repeat_seg >= 0:
                seg = self.timings[self.repeat_seg]
                start = seg.get("start", 0.0)
                if pos > seg.get("end", start) + 0.35 or pl.finished:
                    # seek() finished'i sifirlar: once oku, dosya sonuna geldiyse yeniden baslat
                    was_finished = pl.finished
                    pl.seek(start)
                    if was_finished:
                        pl.play()
                    cur = self.repeat_seg
            if cur != self.cur_seg:
                self.cur_seg = cur
                self._highlight(cur)
                if self.rep_var.get() and cur >= 0 and self.repeat_seg < 0:
                    self.repeat_seg = cur
            if pl.finished and self.repeat_seg < 0:
                pl.finished = False
                self._remember()
                self._advance()

    def _advance(self) -> None:
        """Sayfa bitti: calma listesinde / kitapta sonrakine gec."""
        i = self.pl_index + 1
        while self.playlist and 0 <= i < len(self.playlist):
            if self._load_page(self.playlist[i], autoplay=True):
                self.pl_index = i
                return
            i += 1                                       # bu motorda olmayan sayfayi atla
        if self.cont_var.get():
            self.step_page(1)

    def _remember(self) -> None:
        if self.book is None or not self.page:
            return
        self.app.settings["ab_last"] = {"book": self.book.id, "page": self.page,
                                        "pos": round(self.player.position(), 1)}
        C.save_settings(self.app.settings)

    # ================================================================ Whisper
    def verify_current(self) -> None:
        from rca import whisper_engine as W
        if self.book is None or not self.page or self.busy:
            return
        if not W.installed():
            messagebox.showwarning(C.APP_NAME, self.t("wh.not_installed"), parent=self)
            return
        book, eng, page = self.book, self.engine_var.get(), self.page
        opts = W.WhisperOptions.from_dict(self.app.settings.get("whisper") or {})
        self.busy = True
        self.gen_lbl.configure(text=self.t("ab.verifying").format(page=page), style="Dim.TLabel")

        def done(res):
            self.busy = False
            bad = [r for r in res if not r["ok"]]
            msg = self.t("ab.verified").format(n=len(res), bad=len(bad))
            if self.book is book and self.engine_var.get() == eng and self.page == page:
                self.text.tag_remove("bad", "1.0", "end")
                for r in bad:
                    rng = self.text.tag_ranges(f"s{r['i']}")
                    if rng:
                        self.text.tag_add("bad", rng[0], rng[1])
            else:
                # Bu arada baska sayfaya gecildi: isaretleme yanlis metne yapilmasin
                msg = f"{self.t('ab.page')} {page}: " + msg
            if bad:
                msg += " · " + "; ".join(f"«{r['text']}» → «{r['heard']}»" for r in bad[:4])
            self.gen_lbl.configure(text=msg, style="Warn.TLabel" if bad else "OK.TLabel")

        def err(e):
            self.busy = False
            self.gen_lbl.configure(text=f"{self.t('g.error')}: {e}", style="Err.TLabel")
        self.app.worker.run(lambda: A.verify_page(book, eng, page, opts), done, err)

    # ================================================================ yasam dongusu
    def on_show(self) -> None:
        if getattr(self, "tree", None) is not None and self.book is not None and not self.busy:
            self._fill_tree()

    def shutdown(self) -> None:
        """Pencere kapanirken suren uretimi iptal et, calari kapat ve konumu hatirla."""
        try:
            # Once iptal: aksi halde kapanista surec havuzu kalan tum sayfalari uretir
            self.cancel.set()
        except Exception:
            pass
        try:
            self._remember()
            self.player.close()
        except Exception:
            pass
