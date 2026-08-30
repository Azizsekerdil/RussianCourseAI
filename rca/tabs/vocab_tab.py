# -*- coding: utf-8 -*-
"""Kelime Bankasi & Sozluk sekmesi."""
from __future__ import annotations

import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import rca_common as C
from rca.ui_util import LazyTab, style_text


class VocabTab(LazyTab):
    """Cift yonlu TR<->RU<->EN sozluk, frekans listesi ve kelime duzenleme."""

    def build(self) -> None:
        p = self.palette()
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        # --- arama satiri -------------------------------------------------
        bar = ttk.Frame(root)
        bar.pack(fill="x")
        ttk.Label(bar, text=self.t("g.search") + ":").pack(side="left")
        self.q = tk.StringVar()
        e = ttk.Entry(bar, textvariable=self.q, width=32, font=C.FONT_RU)
        e.pack(side="left", padx=6)
        e.bind("<Return>", lambda _e: self.do_search())
        ttk.Button(bar, text=self.t("g.search"), style="Accent.TButton",
                   command=self.do_search).pack(side="left")

        ttk.Label(bar, text=self.t("v.deck") + ":").pack(side="left", padx=(18, 4))
        self.deck = tk.StringVar(value="(hepsi)")
        self.deck_box = ttk.Combobox(bar, textvariable=self.deck, state="readonly", width=20)
        self.deck_box.pack(side="left")
        self.deck_box.bind("<<ComboboxSelected>>", lambda _e: self.reload())

        ttk.Label(bar, text="Frekans:").pack(side="left", padx=(18, 4))
        self.freq = tk.StringVar(value="hepsi")
        fb = ttk.Combobox(bar, textvariable=self.freq, state="readonly", width=10,
                          values=["hepsi", "ilk 100", "ilk 500", "ilk 1000"])
        fb.pack(side="left")
        fb.bind("<<ComboboxSelected>>", lambda _e: self.reload())

        ttk.Button(bar, text="+ " + self.t("g.add"), command=self.add_word).pack(side="right")
        ttk.Button(bar, text="CSV " + self.t("g.import"),
                   command=self.import_csv).pack(side="right", padx=4)
        ttk.Button(bar, text="CSV " + self.t("g.export"),
                   command=self.export_csv).pack(side="right")

        # --- liste + detay ------------------------------------------------
        pane = ttk.PanedWindow(root, orient="horizontal")
        pane.pack(fill="both", expand=True, pady=(10, 0))

        left = ttk.Frame(pane)
        cols = ("ru", "tr", "en", "pos", "deck")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        for c, w, txt in (("ru", 170, self.t("v.word")), ("tr", 200, self.t("v.meaning")),
                          ("en", 150, "EN"), ("pos", 90, "Tur"), ("deck", 140, self.t("v.deck"))):
            self.tree.heading(c, text=txt)
            self.tree.column(c, width=w, anchor="w")
        vs = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vs.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", lambda _e: self.speak_selected())
        pane.add(left, weight=3)

        right = ttk.Frame(pane, padding=(12, 0))
        self.w_ru = ttk.Label(right, text="-", style="RU.TLabel", font=("Segoe UI", 24, "bold"))
        self.w_ru.pack(anchor="w")
        self.w_ipa = ttk.Label(right, text="", style="Dim.TLabel")
        self.w_ipa.pack(anchor="w")
        self.w_tr = ttk.Label(right, text="", style="TLabel", font=C.FONT_UI_BOLD)
        self.w_tr.pack(anchor="w", pady=(10, 0))
        self.w_en = ttk.Label(right, text="", style="Dim.TLabel")
        self.w_en.pack(anchor="w")
        self.w_ex = ttk.Label(right, text="", style="RU.TLabel", wraplength=320,
                              justify="left")
        self.w_ex.pack(anchor="w", pady=(12, 0))
        self.w_extr = ttk.Label(right, text="", style="Dim.TLabel", wraplength=320,
                                justify="left")
        self.w_extr.pack(anchor="w")
        self.w_pair = ttk.Label(right, text="", style="Warn.TLabel", wraplength=320)
        self.w_pair.pack(anchor="w", pady=(10, 0))
        self.w_stat = ttk.Label(right, text="", style="Dim.TLabel")
        self.w_stat.pack(anchor="w", pady=(10, 0))

        btns = ttk.Frame(right)
        btns.pack(anchor="w", pady=14)
        self.btn_listen = ttk.Button(btns, text="🔊 " + self.t("g.listen"),
                                     command=self.speak_selected)
        self.btn_listen.pack(side="left")
        if not self.app.can_speak():
            self.btn_listen.state(["disabled"])
        ttk.Button(btns, text="★ Favori", command=self.toggle_star).pack(side="left", padx=4)
        ttk.Button(btns, text="AI'a sor", command=self.ask_ai).pack(side="left")
        ttk.Button(btns, text=self.t("g.delete"), style="Err.TButton",
                   command=self.delete_word).pack(side="left", padx=4)

        ttk.Label(right, text="AI yaniti:", style="Dim.TLabel").pack(anchor="w")
        self.ai_out = tk.Text(right, height=10, wrap="word")
        style_text(self.ai_out, p)
        self.ai_out.pack(fill="both", expand=True)
        self.ai_out.configure(state="disabled")
        pane.add(right, weight=2)

        self.rows = []
        self.reload()

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        """Sekmeye donuste deste listesini tazele."""
        if getattr(self, "deck_box", None) is not None:
            self.deck_box["values"] = ["(hepsi)"] + self.repos.words.decks()

    def reload(self) -> None:
        """Filtrelere gore listeyi doldur."""
        deck = "" if self.deck.get() in ("", "(hepsi)") else self.deck.get()
        rows = self.repos.words.all(deck=deck)
        limits = {"ilk 100": 100, "ilk 500": 500, "ilk 1000": 1000}
        lim = limits.get(self.freq.get())
        if lim:
            rows = [r for r in rows if int(r.get("freq_rank") or 9999) <= lim]
        self._fill(rows)
        self.deck_box["values"] = ["(hepsi)"] + self.repos.words.decks()
        self.app.set_status(f"{len(rows)} kelime listelendi")

    def do_search(self) -> None:
        """Arama kutusundaki metne gore listele."""
        q = self.q.get().strip()
        if not q:
            self.reload()
            return
        rows = self.repos.words.search(q)
        self._fill(rows)
        self.app.set_status(f"'{q}' icin {len(rows)} sonuc")

    def _fill(self, rows) -> None:
        """Treeview'i doldur."""
        self.tree.delete(*self.tree.get_children())
        self.rows = rows
        for r in rows:
            self.tree.insert("", "end", iid=str(r["id"]),
                             values=(r["ru"], r["tr"], r["en"], r["pos"], r["tags"]))

    def current(self):
        """Secili kelime kaydi (yoksa None)."""
        sel = self.tree.selection()
        if not sel:
            return None
        return self.repos.words.get(int(sel[0]))

    def on_select(self, _evt=None) -> None:
        """Detay panelini guncelle."""
        from rca.content import rough_ipa
        w = self.current()
        if not w:
            return
        stress = int(w.get("stress_pos") or -1)
        self.w_ru.configure(text=C.add_stress(w["ru"], stress))
        self.w_ipa.configure(text=rough_ipa(w["ru"], stress))
        self.w_tr.configure(text=w["tr"])
        self.w_en.configure(text=w["en"])
        self.w_ex.configure(text=w.get("example_ru") or "")
        self.w_extr.configure(text=w.get("example_tr") or "")
        pair_id = w.get("aspect_pair_id")
        if pair_id:
            pw = self.repos.words.get(int(pair_id))
            self.w_pair.configure(text=f"Gorunus cifti: {pw['ru']} ({pw['tr']})" if pw else "")
        else:
            self.w_pair.configure(text="")
        st = self.repos.progress.state(self.pid, int(w["id"]))
        row = self.repos.db.one(
            "SELECT correct, wrong, starred FROM word_progress WHERE profile_id=? AND word_id=?",
            (self.pid, int(w["id"])))
        c = int(row["correct"]) if row else 0
        x = int(row["wrong"]) if row else 0
        star = "★" if row and int(row["starred"] or 0) else "☆"
        self.w_stat.configure(
            text=f"{star}  kutu {st.box}/6 · dogru {c} · yanlis {x} · tekrar {st.due}")

    def speak_selected(self) -> None:
        """Secili kelimeyi seslendir."""
        w = self.current()
        if w:
            self.app.speak(w["ru"])

    def toggle_star(self) -> None:
        """Favori isaretini degistir."""
        w = self.current()
        if not w:
            return
        on = self.repos.progress.toggle_star(self.pid, int(w["id"]))
        self.app.set_status("Favorilere eklendi" if on else "Favoriden cikarildi")
        self.on_select()

    def ask_ai(self) -> None:
        """Secili kelimeyi yerel modele sor."""
        w = self.current()
        if not w:
            return
        self._ai_write(self.t("ai.thinking"))

        def job():
            return self.app.ai.explain(
                f"{w['ru']} ({w['tr']})", self.app.ui_lang(),
                context=w.get("example_ru") or "")

        self.app.worker.run(job, self._ai_write, self._ai_err)

    def _ai_write(self, text: str) -> None:
        self.ai_out.configure(state="normal")
        self.ai_out.delete("1.0", "end")
        self.ai_out.insert("1.0", text)
        self.ai_out.configure(state="disabled")

    def _ai_err(self, err: Exception) -> None:
        self._ai_write(f"{self.t('ai.offline')}\n\n({err})")

    # ------------------------------------------------------------------
    def add_word(self) -> None:
        """Yeni kelime ekleme penceresi."""
        dlg = tk.Toplevel(self)
        dlg.title(self.t("g.add"))
        dlg.configure(background=self.palette()["bg"])
        dlg.transient(self.app)
        dlg.grab_set()
        fields = {}
        specs = [("ru", "Rusca"), ("tr", "Turkce"), ("en", "Ingilizce"),
                 ("example_ru", "Ornek cumle (RU)"), ("example_tr", "Ornek cumle (TR)"),
                 ("tags", "Deste")]
        for i, (key, label) in enumerate(specs):
            ttk.Label(dlg, text=label).grid(row=i, column=0, sticky="w", padx=12, pady=5)
            v = tk.StringVar(value="Ozel" if key == "tags" else "")
            ttk.Entry(dlg, textvariable=v, width=38, font=C.FONT_RU).grid(
                row=i, column=1, padx=12, pady=5)
            fields[key] = v

        def save() -> None:
            ru = fields["ru"].get().strip()
            tr = fields["tr"].get().strip()
            if not ru or not tr:
                messagebox.showwarning(C.APP_NAME, "Rusca ve Turkce alanlari zorunlu.",
                                       parent=dlg)
                return
            self.repos.words.add(ru, tr, fields["en"].get().strip(),
                                 deck=fields["tags"].get().strip() or "Ozel",
                                 example_ru=fields["example_ru"].get().strip(),
                                 example_tr=fields["example_tr"].get().strip())
            dlg.destroy()
            self.reload()

        ttk.Button(dlg, text=self.t("g.save"), style="Accent.TButton",
                   command=save).grid(row=len(specs), column=1, sticky="e", padx=12, pady=12)
        dlg.bind("<Return>", lambda _e: save())
        dlg.bind("<Escape>", lambda _e: dlg.destroy())

    def delete_word(self) -> None:
        """Secili kelimeyi sil."""
        w = self.current()
        if not w:
            return
        if messagebox.askyesno(C.APP_NAME, f"'{w['ru']}' silinsin mi?"):
            self.repos.words.delete(int(w["id"]))
            self.reload()

    def export_csv(self) -> None:
        """Listeyi CSV olarak disa aktar (noktali virgul ayirici)."""
        path = filedialog.asksaveasfilename(
            title="CSV disa aktar", defaultextension=".csv",
            initialdir=str(C.EXPORT_DIR), filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                wr = csv.writer(f, delimiter=";")
                wr.writerow(["kelime", "anlam", "ingilizce", "ornek_ru", "ornek_tr", "deste"])
                for r in self.rows:
                    wr.writerow([r["ru"], r["tr"], r["en"], r.get("example_ru", ""),
                                 r.get("example_tr", ""), r["tags"]])
            self.app.set_status(f"Disa aktarildi: {path}")
        except Exception as e:                                  # noqa: BLE001
            messagebox.showerror(C.APP_NAME, f"Yazilamadi:\n{e}")

    def import_csv(self) -> None:
        """CSV'den kelime ice aktar. Bicim: kelime;anlam;ornek;deste"""
        path = filedialog.askopenfilename(title="CSV ice aktar",
                                          filetypes=[("CSV", "*.csv"), ("Tumu", "*.*")])
        if not path:
            return
        added = 0
        try:
            with open(path, encoding="utf-8-sig", newline="") as f:
                sample = f.read(2048)
                f.seek(0)
                delim = ";" if sample.count(";") >= sample.count(",") else ","
                rd = csv.reader(f, delimiter=delim)
                for i, row in enumerate(rd):
                    if not row or len(row) < 2:
                        continue
                    if i == 0 and not C.has_cyrillic(row[0]):
                        continue                              # baslik satiri
                    ru, tr = row[0].strip(), row[1].strip()
                    ex = row[2].strip() if len(row) > 2 else ""
                    deck = row[3].strip() if len(row) > 3 else "Ice Aktarilan"
                    if ru and tr:
                        self.repos.words.add(ru, tr, deck=deck, example_ru=ex)
                        added += 1
        except Exception as e:                                 # noqa: BLE001
            messagebox.showerror(C.APP_NAME, f"Okunamadi:\n{e}")
            return
        self.reload()
        messagebox.showinfo(C.APP_NAME, f"{added} kelime ice aktarildi.")
