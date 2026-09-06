# -*- coding: utf-8 -*-
"""Sozluk RU-EN sekmesi: cift yonlu Rusca <-> Ingilizce arama, TTS, AI, ice/disa aktarim."""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

import rca_common as C
from rca import dictionary as D
from rca.ui_util import LazyTab, style_text


class DictionaryTab(LazyTab):
    """Gomulu + kullanici + OpenRussian katmanlarini birlestiren sozluk sayfasi."""

    MAX_HISTORY = 12

    def build(self) -> None:
        p = self.palette()
        self.dict = D.build_dictionary(
            [(r["ru"], r["en"], r["pos"], r["extra"]) for r in self.repos.dictionary.all()])
        self.history: list = []
        self.results: list = []
        self._or_loaded = False

        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text=self.t("d.subtitle"), style="Dim.TLabel",
                  wraplength=1100, justify="left").pack(anchor="w", pady=(0, 8))

        # --- arama satiri -------------------------------------------------
        bar = ttk.Frame(root)
        bar.pack(fill="x")
        self.q = tk.StringVar()
        self.entry = ttk.Entry(bar, textvariable=self.q, width=36, font=C.FONT_RU)
        self.entry.pack(side="left")
        self.entry.bind("<Return>", lambda _e: self.search())
        self.entry.bind("<KeyRelease>", self._on_key)
        ttk.Button(bar, text=self.t("g.search"), style="Accent.TButton",
                   command=self.search).pack(side="left", padx=6)
        self.dir_lbl = ttk.Label(bar, text="", style="Dim.TLabel")
        self.dir_lbl.pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="🎲 " + self.t("d.random"), command=self.random_word).pack(side="left", padx=12)

        ttk.Button(bar, text="+ " + self.t("d.add_entry"), command=self.add_entry).pack(side="right")
        ttk.Button(bar, text=self.t("d.import"), command=self.import_file).pack(side="right", padx=4)
        ttk.Button(bar, text=self.t("d.export"), command=self.export_file).pack(side="right")
        self.btn_or = ttk.Button(bar, text=self.t("d.load_or"), command=self.load_openrussian)
        self.btn_or.pack(side="right", padx=4)

        # --- liste + detay ------------------------------------------------
        pane = ttk.PanedWindow(root, orient="horizontal")
        pane.pack(fill="both", expand=True, pady=(10, 0))

        left = ttk.Frame(pane)
        cols = ("ru", "en", "pos", "extra", "src")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        for c, w, txt, stretch in (("ru", 170, self.t("d.headword"), False),
                                   ("en", 260, self.t("d.trans"), True),
                                   ("pos", 60, self.t("d.pos"), False),
                                   ("extra", 90, self.t("d.extra"), False),
                                   ("src", 80, self.t("d.source"), False)):
            self.tree.heading(c, text=txt)
            self.tree.column(c, width=w, minwidth=40, anchor="w", stretch=stretch)
        vs = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vs.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", lambda _e: self.speak_selected())
        pane.add(left, weight=3)

        right = ttk.Frame(pane, padding=(12, 0))
        self.w_ru = ttk.Label(right, text="—", style="RU.TLabel", font=("Segoe UI", 26, "bold"))
        self.w_ru.pack(anchor="w")
        self.w_ipa = ttk.Label(right, text="", style="Dim.TLabel")
        self.w_ipa.pack(anchor="w")
        self.w_pos = ttk.Label(right, text="", style="Dim.TLabel")
        self.w_pos.pack(anchor="w", pady=(6, 0))
        self.w_en = ttk.Label(right, text="", style="TLabel", font=C.FONT_UI_BOLD,
                              wraplength=340, justify="left")
        self.w_en.pack(anchor="w", pady=(10, 0))
        self.w_bank = ttk.Label(right, text="", style="Warn.TLabel", wraplength=340, justify="left")
        self.w_bank.pack(anchor="w", pady=(8, 0))

        btns = ttk.Frame(right)
        btns.pack(anchor="w", pady=(12, 2))
        self.btn_listen = ttk.Button(btns, text="🔊 " + self.t("g.listen"), command=self.speak_selected)
        self.btn_listen.pack(side="left")
        if not self.app.can_speak():
            self.btn_listen.state(["disabled"])
        ttk.Button(btns, text="🤖 " + self.t("d.ask_ai"), command=self.ask_ai).pack(side="left", padx=4)
        ttk.Button(btns, text=self.t("d.copy"), command=self.copy_entry).pack(side="left")
        btns2 = ttk.Frame(right)
        btns2.pack(anchor="w", pady=(0, 10))
        ttk.Button(btns2, text="📚 " + self.t("d.to_bank"), style="Accent.TButton",
                   command=self.add_to_bank).pack(side="left")

        ttk.Label(right, text=self.t("d.history") + ":", style="Dim.TLabel").pack(anchor="w")
        self.hist_box = tk.Listbox(right, height=5, font=C.FONT_UI_SM, activestyle="none")
        self.hist_box.configure(background=p.get("card", p["bg"]), foreground=p["fg"],
                                highlightthickness=0, relief="flat")
        self.hist_box.pack(fill="x")
        self.hist_box.bind("<<ListboxSelect>>", self._pick_history)

        ttk.Label(right, text=self.t("d.ai_answer") + ":", style="Dim.TLabel").pack(anchor="w", pady=(10, 0))
        self.ai_out = tk.Text(right, height=9, wrap="word")
        style_text(self.ai_out, p)
        self.ai_out.pack(fill="both", expand=True)
        self.ai_out.configure(state="disabled")
        pane.add(right, weight=2)

        self.count_lbl = ttk.Label(root, text="", style="Dim.TLabel")
        self.count_lbl.pack(anchor="w", pady=(6, 0))
        self._update_count()

        if D.openrussian_dir().is_dir() and any(D.openrussian_dir().glob("openrussian_*.tsv")):
            self.after(300, self.load_openrussian)

        self.entry.focus_set()

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        if getattr(self, "entry", None) is not None:
            self.entry.focus_set()

    def _update_count(self) -> None:
        by = self.dict.count_by_source()
        parts = [f"{self.t('d.builtin')} {by.get(D.SOURCE_BUILTIN, 0)}",
                 f"{self.t('d.user')} {by.get(D.SOURCE_USER, 0)}"]
        if by.get(D.SOURCE_OPENRUSSIAN):
            parts.append(f"OpenRussian {C.human_int(by[D.SOURCE_OPENRUSSIAN])}")
        self.count_lbl.configure(text=f"{C.human_int(len(self.dict))} {self.t('d.entries')}  ·  " + "  ·  ".join(parts))

    def _on_key(self, evt) -> None:
        q = self.q.get().strip()
        if not q:
            self.dir_lbl.configure(text="")
            return
        self.dir_lbl.configure(text="RU → EN" if D.Dictionary.direction(q) == "ru2en" else "EN → RU")
        if len(q) >= 2 and evt.keysym not in ("Return", "Up", "Down"):
            self.search(quiet=True)

    # ------------------------------------------------------------------
    def search(self, quiet: bool = False) -> None:
        q = self.q.get().strip()
        if not q:
            self._fill([])
            return
        rows = self.dict.lookup(q)
        self._fill(rows)
        if not quiet:
            self._remember(q)
            if rows:
                self.tree.selection_set(self.tree.get_children()[0])
                self.tree.focus(self.tree.get_children()[0])
                self.on_select()
                self.app.set_status(f"'{q}': {len(rows)} {self.t('d.results')}")
            else:
                self.app.set_status(self.t("d.noresult"))
                self._ai_write(self.t("d.noresult"))

    def _fill(self, rows) -> None:
        self.tree.delete(*self.tree.get_children())
        self.results = rows
        lang = self.app.ui_lang()
        src_names = {D.SOURCE_BUILTIN: self.t("d.builtin"), D.SOURCE_USER: self.t("d.user"),
                     D.SOURCE_OPENRUSSIAN: "OpenRussian"}
        for i, e in enumerate(rows):
            self.tree.insert("", "end", iid=str(i),
                             values=(e.display, e.translation, e.pos_label(lang),
                                     e.extra_label(lang), src_names.get(e.source, e.source)))

    def _remember(self, q: str) -> None:
        if q in self.history:
            self.history.remove(q)
        self.history.insert(0, q)
        del self.history[self.MAX_HISTORY:]
        self.hist_box.delete(0, "end")
        for h in self.history:
            self.hist_box.insert("end", h)

    def _pick_history(self, _evt=None) -> None:
        sel = self.hist_box.curselection()
        if sel:
            self.q.set(self.hist_box.get(sel[0]))
            self.search()

    def current(self):
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return self.results[int(sel[0])]
        except (ValueError, IndexError):
            return None

    def on_select(self, _evt=None) -> None:
        from rca.content import rough_ipa
        e = self.current()
        if not e:
            return
        lang = self.app.ui_lang()
        self.w_ru.configure(text=e.display)
        self.w_ipa.configure(text=rough_ipa(e.headword, e.stress) if " " not in e.headword else "")
        pos = e.pos_label(lang)
        if e.extra:
            pos += f" · {e.extra_label(lang)}"
        self.w_pos.configure(text=pos)
        self.w_en.configure(text=e.translation.replace(";", "\n"))
        found = self.repos.words.search(e.headword, limit=3)
        exact = [w for w in found if C.normalize_ru(w["ru"]) == C.normalize_ru(e.headword)]
        if exact:
            w = exact[0]
            self.w_bank.configure(text=f"📚 {w['tr']}  ({w['tags']})")
        else:
            self.w_bank.configure(text="")

    # ------------------------------------------------------------------
    def speak_selected(self) -> None:
        e = self.current()
        if e:
            self.app.speak(e.headword)

    def random_word(self) -> None:
        e = self.dict.random_entry()
        if e:
            self.q.set(e.headword)
            self.search()

    def copy_entry(self) -> None:
        e = self.current()
        if not e:
            return
        self.clipboard_clear()
        self.clipboard_append(f"{e.display} — {e.translation}")
        self.app.set_status(self.t("d.copied"))

    def add_to_bank(self) -> None:
        e = self.current()
        if not e:
            return
        pos = e.pos
        if e.pos == "n" and e.extra in ("m", "f", "n", "pl"):
            pos = f"noun-{e.extra}"
        elif e.pos == "v":
            pos = "verb"
        first = e.translation.split(";")[0].strip()
        self.repos.words.add(e.headword, first, e.translation, stress_pos=e.stress,
                             pos=pos, deck="Sozluk")
        self.app.set_status(self.t("d.added_bank") + f": {e.headword}")
        self.on_select()

    def ask_ai(self) -> None:
        e = self.current()
        text = e.headword if e else self.q.get().strip()
        if not text:
            return
        self._ai_write(self.t("ai.thinking"))
        lang = self.app.ui_lang()

        def job():
            if D.Dictionary.direction(text) == "ru2en":
                return self.app.ai.explain(text, lang)
            return self.app.ai.translate(text, direction="en2ru", ui_lang=lang)

        self.app.worker.run(job, self._ai_write, self._ai_err)

    def _ai_write(self, text: str) -> None:
        self.ai_out.configure(state="normal")
        self.ai_out.delete("1.0", "end")
        self.ai_out.insert("1.0", text)
        self.ai_out.configure(state="disabled")

    def _ai_err(self, err: Exception) -> None:
        self._ai_write(f"{self.t('ai.offline')}\n\n({err})")

    # ------------------------------------------------------------------
    def add_entry(self) -> None:
        dlg = tk.Toplevel(self)
        dlg.title(self.t("d.add_entry"))
        dlg.configure(background=self.palette()["bg"])
        dlg.transient(self.app)
        dlg.grab_set()
        fields = {}
        specs = [("ru", self.t("d.headword") + " (вург: приве'т)"), ("en", self.t("d.trans")),
                 ("pos", self.t("d.pos") + " (n/v/adj/...)"), ("extra", self.t("d.extra") + " (m/f/n/ipf/pf)")]
        for i, (key, label) in enumerate(specs):
            ttk.Label(dlg, text=label).grid(row=i, column=0, sticky="w", padx=12, pady=5)
            v = tk.StringVar(value=self.q.get().strip() if key in ("ru", "en") and
                             (D.Dictionary.direction(self.q.get()) == "ru2en") == (key == "ru") else "")
            ttk.Entry(dlg, textvariable=v, width=40, font=C.FONT_RU).grid(row=i, column=1, padx=12, pady=5)
            fields[key] = v

        def save() -> None:
            ru = fields["ru"].get().strip()
            en = fields["en"].get().strip()
            if not ru or not en:
                messagebox.showwarning(C.APP_NAME, self.t("d.required"), parent=dlg)
                return
            self.repos.dictionary.add(ru, en, fields["pos"].get().strip(), fields["extra"].get().strip())
            word, stress = D.split_stress(ru)
            self.dict.extend([D.Entry(word, stress, fields["pos"].get().strip(),
                                      fields["extra"].get().strip(), en, D.SOURCE_USER, D.mark_all(ru))])
            dlg.destroy()
            self._update_count()
            self.q.set(word)
            self.search()

        ttk.Button(dlg, text=self.t("g.save"), style="Accent.TButton",
                   command=save).grid(row=len(specs), column=1, sticky="e", padx=12, pady=12)
        dlg.bind("<Return>", lambda _e: save())
        dlg.bind("<Escape>", lambda _e: dlg.destroy())

    def import_file(self) -> None:
        path = filedialog.askopenfilename(
            title=self.t("d.import"),
            filetypes=[("CSV / TSV", "*.csv *.tsv *.txt"), ("*", "*.*")])
        if not path:
            return
        try:
            entries = D.read_table(Path(path))
        except Exception as e:                                   # noqa: BLE001
            messagebox.showerror(C.APP_NAME, str(e), parent=self)
            return
        rows = [(e.display.replace(C.STRESS_MARK, "'"), e.translation, e.pos, e.extra) for e in entries]
        n = self.repos.dictionary.add_many(rows)
        self.dict.extend(entries)
        self._update_count()
        self.app.set_status(f"{n} {self.t('d.imported')}")

    def export_file(self) -> None:
        path = filedialog.asksaveasfilename(
            title=self.t("d.export"), defaultextension=".csv",
            initialdir=str(C.EXPORT_DIR), initialfile="sozluk_ru_en.csv",
            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        entries = self.results if self.results else [e for e in self.dict.entries
                                                     if e.source != D.SOURCE_OPENRUSSIAN]
        n = D.write_table(Path(path), entries)
        self.app.set_status(f"{n} {self.t('d.exported')}")

    def load_openrussian(self) -> None:
        if self._or_loaded:
            return
        folder = D.openrussian_dir()
        if not folder.is_dir() or not any(folder.glob("openrussian_*.tsv")):
            self.app.set_status(self.t("d.or_missing"))
            messagebox.showinfo(C.APP_NAME, self.t("d.or_missing"), parent=self)
            return
        self._or_loaded = True
        self.btn_or.state(["disabled"])
        self.app.set_status(self.t("d.loading"))

        def job():
            return D.load_openrussian(folder)

        def done(entries):
            n = self.dict.extend(entries)
            self._update_count()
            self.app.set_status(f"{self.t('d.or_loaded')}: {C.human_int(n)} {self.t('d.entries')}")
            if self.q.get().strip():
                self.search(quiet=True)

        def err(exc):
            self._or_loaded = False
            self.btn_or.state(["!disabled"])
            self.app.set_status(f"OpenRussian: {exc}")

        self.app.worker.run(job, done, err)
