# -*- coding: utf-8 -*-
"""Token Kullanim Defteri.

AI'a giden her istegin SAYACI tutulur; istek METINLERI hicbir zaman saklanmaz.
"""
from __future__ import annotations

import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import rca_common as C
from rca.ui_util import LazyTab, card


class TokensTab(LazyTab):
    """Bugun / 7 gun / 30 gun / tum zamanlar kartlari ve gruplu tablolar."""

    def build(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        head = ttk.Frame(root)
        head.pack(fill="x")
        ttk.Label(head, text="Token Kullanim Defteri", style="Title.TLabel").pack(side="left")
        ttk.Button(head, text=self.t("g.refresh"), command=self.refresh).pack(side="right")
        ttk.Button(head, text="CSV " + self.t("g.export"), style="Accent.TButton",
                   command=self.export_csv).pack(side="right", padx=6)
        ttk.Button(head, text="Defteri temizle", style="Err.TButton",
                   command=self.clear).pack(side="right")

        ttk.Label(root, style="Dim.TLabel", wraplength=900, justify="left",
                  text="Bu defter yalnizca model adi, gorev turu, token sayilari ve sureyi "
                       "tutar. Gonderdiginiz metinler kaydedilmez.").pack(
            anchor="w", pady=(4, 12))

        self.cards = ttk.Frame(root)
        self.cards.pack(fill="x")

        bar = ttk.Frame(root)
        bar.pack(fill="x", pady=(16, 6))
        ttk.Label(bar, text="Grupla:").pack(side="left")
        self.by = tk.StringVar(value="model")
        for code, label in (("model", "Modele gore"), ("task", "Ise gore"),
                            ("day", "Gune gore")):
            ttk.Radiobutton(bar, text=label, value=code, variable=self.by,
                            command=self.refresh).pack(side="left", padx=6)

        self.tv = ttk.Treeview(root, columns=("k", "c", "t", "ms"), show="headings")
        for c, w, t in (("k", 320, "Anahtar"), ("c", 120, "Cagri"),
                        ("t", 160, "Token"), ("ms", 140, "Ort. sure (ms)")):
            self.tv.heading(c, text=t)
            self.tv.column(c, width=w, anchor="w")
        self.tv.pack(fill="both", expand=True, pady=6)

        self.refresh()

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        """Sekmeye donuste tazele."""
        if getattr(self, "cards", None) is not None:
            self.refresh()

    def refresh(self) -> None:
        """Kartlari ve tabloyu yeniden hesapla."""
        p = self.palette()
        for c in self.cards.winfo_children():
            c.destroy()
        s = self.repos.tokens.summary()
        labels = {"today": "Bugun", "7d": "Son 7 gun", "30d": "Son 30 gun",
                  "all": "Tum zamanlar"}
        for i, key in enumerate(("today", "7d", "30d", "all")):
            v = s[key]
            c = card(self.cards, f"{labels[key]}  ·  {v['calls']} cagri",
                     C.human_int(v["tokens"]), p)
            c.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            self.cards.columnconfigure(i, weight=1)

        self.tv.delete(*self.tv.get_children())
        rows = self.repos.tokens.grouped(self.by.get())
        for r in rows:
            self.tv.insert("", "end", values=(r["k"], r["calls"],
                                              C.human_int(r["tokens"]),
                                              f"{float(r['avg_ms']):.0f}"))
        if not rows:
            self.tv.insert("", "end", values=("(henuz AI cagrisi yok)", "", "", ""))

    def export_csv(self) -> None:
        """Ham kayitlari CSV olarak disa aktar."""
        rows = self.repos.tokens.all_rows()
        if not rows:
            messagebox.showinfo(C.APP_NAME, "Defter bos.")
            return
        path = filedialog.asksaveasfilename(
            title="CSV disa aktar", defaultextension=".csv",
            initialdir=str(C.EXPORT_DIR), initialfile="token_defteri.csv",
            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
                wr.writeheader()
                wr.writerows(rows)
            self.app.set_status(f"Disa aktarildi: {path}")
        except Exception as e:                          # noqa: BLE001
            messagebox.showerror(C.APP_NAME, f"Yazilamadi:\n{e}")

    def clear(self) -> None:
        """Tum token kayitlarini sil."""
        if messagebox.askyesno(C.APP_NAME, "Token defteri tamamen silinsin mi?"):
            self.repos.db.execute("DELETE FROM token_log")
            self.refresh()
