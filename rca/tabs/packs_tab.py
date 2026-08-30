# -*- coding: utf-8 -*-
"""Paket Sistemi: .rupack (ZIP) disa/ice aktarma. Duz .json geriye donuk uyumludur."""
from __future__ import annotations

import json
import tkinter as tk
import zipfile
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import rca_common as C
from rca.ui_util import LazyTab

PACK_VERSION = "1"


class PacksTab(LazyTab):
    """Kendi kelime/soru paketlerini uret ve paylas."""

    def build(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="Paket Sistemi", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, style="Dim.TLabel", justify="left", wraplength=900,
                  text=".rupack = icinde paket.json + audio/ + images/ bulunan bir ZIP "
                       "dosyasidir. Duz .json paketleri de acilir (eski surum uyumu).").pack(
            anchor="w", pady=(2, 12))

        # --- disa aktarma -------------------------------------------------
        exp = ttk.LabelFrame(root, text="Disa aktar", padding=12)
        exp.pack(fill="x")

        row = ttk.Frame(exp)
        row.pack(fill="x")
        ttk.Label(row, text="Paket adi:").pack(side="left")
        self.name = tk.StringVar(value="Kendi Destem")
        ttk.Entry(row, textvariable=self.name, width=28).pack(side="left", padx=6)
        ttk.Label(row, text="Yazar:").pack(side="left", padx=(12, 4))
        self.author = tk.StringVar(value="")
        ttk.Entry(row, textvariable=self.author, width=20).pack(side="left")

        row2 = ttk.Frame(exp)
        row2.pack(fill="x", pady=8)
        ttk.Label(row2, text="Kaynak deste:").pack(side="left")
        self.deck = tk.StringVar(value="(hepsi)")
        self.deck_box = ttk.Combobox(row2, textvariable=self.deck, state="readonly",
                                     width=24)
        self.deck_box.pack(side="left", padx=6)
        self.include_progress = tk.BooleanVar(value=False)
        ttk.Checkbutton(row2, text="Kendi ilerlememi de ekle",
                        variable=self.include_progress).pack(side="left", padx=12)
        ttk.Button(row2, text="📦 .rupack olustur", style="Accent.TButton",
                   command=self.export_pack).pack(side="left", padx=6)
        ttk.Button(row2, text="{ } .json olustur",
                   command=lambda: self.export_pack(as_json=True)).pack(side="left")

        # --- ice aktarma --------------------------------------------------
        imp = ttk.LabelFrame(root, text="Ice aktar", padding=12)
        imp.pack(fill="x", pady=12)
        ttk.Button(imp, text="📂 Paket ac (.rupack / .json)", style="Accent.TButton",
                   command=self.import_pack).pack(side="left")
        self.imp_info = ttk.Label(imp, text="", style="Dim.TLabel")
        self.imp_info.pack(side="left", padx=12)

        # --- kurulu paketler ----------------------------------------------
        ttk.Label(root, text="Kurulu paketler", style="Title.TLabel").pack(
            anchor="w", pady=(10, 4))
        self.tv = ttk.Treeview(root, columns=("v", "a", "n", "d"), show="headings",
                               height=10)
        for c, w, t in (("v", 80, "Surum"), ("a", 180, "Yazar"),
                        ("n", 110, "Kelime"), ("d", 180, "Kurulum")):
            self.tv.heading(c, text=t)
            self.tv.column(c, width=w, anchor="w")
        self.tv.heading("#0", text="Paket")
        self.tv.pack(fill="both", expand=True)
        self.refresh()

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        """Deste listesini ve kurulu paketleri tazele."""
        if getattr(self, "deck_box", None) is not None:
            self.deck_box["values"] = ["(hepsi)"] + self.repos.words.decks()
            self.refresh()

    def refresh(self) -> None:
        """Kurulu paket tablosunu doldur."""
        self.deck_box["values"] = ["(hepsi)"] + self.repos.words.decks()
        self.tv.delete(*self.tv.get_children())
        rows = self.repos.db.query("SELECT * FROM packs ORDER BY id DESC")
        for r in rows:
            self.tv.insert("", "end", text=r["name"],
                           values=(r["version"], r["author"], r["word_count"],
                                   r["installed_at"][:16].replace("T", " ")))
        if not rows:
            self.tv.insert("", "end", text="(henuz paket kurulmadi)", values=("", "", "", ""))

    # ------------------------------------------------------------------
    def _collect(self) -> dict:
        """Secili desteden paket sozlugu uret."""
        deck = "" if self.deck.get() in ("", "(hepsi)") else self.deck.get()
        words = self.repos.words.all(deck=deck)
        payload = {
            "format": "rupack",
            "version": PACK_VERSION,
            "name": self.name.get().strip() or "Paket",
            "author": self.author.get().strip(),
            "lang": C.TARGET_LANG,
            "created": datetime.now().isoformat(timespec="seconds"),
            "words": [{
                "ru": w["ru"], "tr": w["tr"], "en": w["en"],
                "stress_pos": w["stress_pos"], "pos": w["pos"],
                "freq_rank": w["freq_rank"], "deck": w["tags"],
                "example_ru": w["example_ru"], "example_tr": w["example_tr"],
                "audio": w["audio"],
            } for w in words],
            "questions": [],
        }
        if self.include_progress.get():
            rows = self.repos.db.query(
                "SELECT w.ru, p.box, p.correct, p.wrong, p.due_date FROM word_progress p "
                "JOIN words w ON w.id=p.word_id WHERE p.profile_id=?", (self.pid,))
            payload["progress"] = [dict(r) for r in rows]
        return payload

    def export_pack(self, as_json: bool = False) -> None:
        """Paketi diske yaz."""
        payload = self._collect()
        if not payload["words"]:
            messagebox.showinfo(C.APP_NAME, "Secili destede kelime yok.")
            return
        ext = ".json" if as_json else ".rupack"
        path = filedialog.asksaveasfilename(
            title="Paket kaydet", defaultextension=ext,
            initialdir=str(C.EXPORT_DIR),
            initialfile=f"{payload['name'].replace(' ', '_')}{ext}",
            filetypes=[("Rusca paketi", f"*{ext}"), ("Tumu", "*.*")])
        if not path:
            return
        try:
            if as_json:
                Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
            else:
                with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
                    z.writestr("paket.json",
                               json.dumps(payload, ensure_ascii=False, indent=2))
                    z.writestr("audio/.keep", "")
                    z.writestr("images/.keep", "")
            self.app.set_status(f"Paket yazildi: {path}  ({len(payload['words'])} kelime)")
        except Exception as e:                             # noqa: BLE001
            messagebox.showerror(C.APP_NAME, f"Yazilamadi:\n{e}")

    def import_pack(self) -> None:
        """Paketi oku ve kelimeleri bankaya ekle."""
        path = filedialog.askopenfilename(
            title="Paket ac",
            filetypes=[("Rusca paketi", "*.rupack *.json"), ("Tumu", "*.*")])
        if not path:
            return
        try:
            payload = self._read_pack(Path(path))
        except Exception as e:                             # noqa: BLE001
            messagebox.showerror(C.APP_NAME, f"Paket okunamadi:\n{e}")
            return

        words = payload.get("words") or []
        if not words:
            messagebox.showinfo(C.APP_NAME, "Pakette kelime bulunamadi.")
            return
        added = 0
        for w in words:
            ru = (w.get("ru") or "").strip()
            tr = (w.get("tr") or "").strip()
            if not ru or not tr:
                continue
            self.repos.words.add(
                ru, tr, w.get("en", ""),
                stress_pos=int(w.get("stress_pos", -1) or -1),
                pos=w.get("pos", ""),
                deck=w.get("deck") or payload.get("name", "Paket"),
                example_ru=w.get("example_ru", ""),
                example_tr=w.get("example_tr", ""),
                freq_rank=int(w.get("freq_rank", 9999) or 9999))
            added += 1
        self.repos.db.execute(
            "INSERT INTO packs(name,version,author,installed_at,word_count) "
            "VALUES(?,?,?,?,?)",
            (payload.get("name", Path(path).stem), str(payload.get("version", "1")),
             payload.get("author", ""), datetime.now().isoformat(timespec="seconds"),
             added))
        self.imp_info.configure(text=f"{added} kelime eklendi.")
        self.refresh()
        messagebox.showinfo(C.APP_NAME, f"'{payload.get('name')}' paketinden "
                                        f"{added} kelime ice aktarildi.")

    @staticmethod
    def _read_pack(path: Path) -> dict:
        """.rupack (ZIP) veya duz .json paketini oku."""
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as z:
                name = "paket.json" if "paket.json" in z.namelist() else None
                if name is None:
                    cands = [n for n in z.namelist() if n.lower().endswith(".json")]
                    if not cands:
                        raise ValueError("ZIP icinde paket.json yok")
                    name = cands[0]
                return json.loads(z.read(name).decode("utf-8"))
        return json.loads(path.read_text(encoding="utf-8"))
