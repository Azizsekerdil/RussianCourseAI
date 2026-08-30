# -*- coding: utf-8 -*-
"""Kurs Kaynaklari sekmesi: Resources/ agacini gez, bitirdim isaretle, ac/yazdir."""
from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import rca_common as C
from rca.ui_util import LazyTab

ICONS = {".pdf": "📕", ".docx": "📄", ".doc": "📄", ".txt": "📃", ".md": "📝",
         ".mp3": "🎵", ".wav": "🎵", ".png": "🖼", ".jpg": "🖼", ".jpeg": "🖼"}


class ResourcesTab(LazyTab):
    """Ders ve alistirma dosyalarini agac gorunumunde listeler."""

    def build(self) -> None:
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        bar = ttk.Frame(root)
        bar.pack(fill="x")
        ttk.Label(bar, text="Kok klasor:").pack(side="left")
        self.root_var = tk.StringVar(value=str(C.RESOURCES_DIR))
        ttk.Entry(bar, textvariable=self.root_var, width=60).pack(side="left", padx=6)
        ttk.Button(bar, text="Degistir", command=self.pick_root).pack(side="left")
        ttk.Button(bar, text=self.t("g.refresh"), command=self.reload).pack(side="left", padx=6)

        ttk.Label(bar, text=self.t("g.search") + ":").pack(side="left", padx=(20, 4))
        self.q = tk.StringVar()
        e = ttk.Entry(bar, textvariable=self.q, width=22)
        e.pack(side="left")
        e.bind("<KeyRelease>", lambda _ev: self.reload())

        self.tree = ttk.Treeview(root, columns=("done", "size"), show="tree headings")
        self.tree.heading("#0", text="Dosya")
        self.tree.heading("done", text="Bitirdim")
        self.tree.heading("size", text="Boyut")
        self.tree.column("#0", width=560)
        self.tree.column("done", width=90, anchor="center")
        self.tree.column("size", width=100, anchor="e")
        vs = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vs.set)
        self.tree.pack(side="left", fill="both", expand=True, pady=10)
        vs.pack(side="right", fill="y", pady=10)
        self.tree.bind("<Double-1>", lambda _ev: self.open_selected())
        self.tree.bind("<space>", lambda _ev: self.toggle_done())

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(btns, text="☐/☑ Bitirdim (Space)",
                   command=self.toggle_done).pack(side="left")
        ttk.Button(btns, text="PDF Okuyucuda ac", style="Accent.TButton",
                   command=self.open_in_reader).pack(side="left", padx=6)
        ttk.Button(btns, text="Varsayilan programda ac",
                   command=self.open_selected).pack(side="left")
        ttk.Button(btns, text="Klasoru goster",
                   command=self.reveal).pack(side="left", padx=6)
        ttk.Button(btns, text="Yazdir", command=self.print_file).pack(side="left")

        self.info = ttk.Label(self, text="", style="Dim.TLabel")
        self.info.pack(anchor="w", padx=10, pady=(0, 8))
        self.reload()

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        """Sekmeye donuste agaci tazele."""
        if getattr(self, "tree", None) is not None:
            self.reload()

    def pick_root(self) -> None:
        """Kok klasoru degistir."""
        d = filedialog.askdirectory(title="Kaynak klasoru sec",
                                    initialdir=self.root_var.get())
        if d:
            self.root_var.set(d)
            self.reload()

    def reload(self) -> None:
        """Agaci yeniden kur."""
        self.tree.delete(*self.tree.get_children())
        base = Path(self.root_var.get())
        if not base.exists():
            try:
                base.mkdir(parents=True, exist_ok=True)
                (base / "Dersler").mkdir(exist_ok=True)
                (base / "Alistirmalar").mkdir(exist_ok=True)
            except Exception:
                pass
        if not base.exists():
            self.info.configure(text=f"Klasor bulunamadi: {base}")
            return
        done = self.repos.resources.done_set(self.pid)
        needle = self.q.get().strip().lower()
        count = self._walk(base, "", done, needle)
        self.info.configure(
            text=f"{count} dosya · ders klasoru: 📘 Dersler · alistirma: 📝 Alistirmalar · "
                 f"Space = bitirdim isareti")

    def _walk(self, path: Path, parent: str, done: set, needle: str) -> int:
        """Klasoru ozyinelemeli dolas ve agaca ekle."""
        total = 0
        try:
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except Exception:
            return 0
        for entry in entries:
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                icon = "📘" if "ders" in entry.name.lower() else (
                    "📝" if "alist" in entry.name.lower() or "exer" in entry.name.lower()
                    else "📁")
                node = self.tree.insert(parent, "end", text=f"{icon} {entry.name}",
                                        values=("", ""), open=True,
                                        tags=("dir", str(entry)))
                sub = self._walk(entry, node, done, needle)
                total += sub
                if sub == 0 and needle:
                    self.tree.delete(node)
            else:
                if needle and needle not in entry.name.lower():
                    continue
                key = str(entry)
                icon = ICONS.get(entry.suffix.lower(), "📄")
                try:
                    size = entry.stat().st_size
                    size_txt = f"{size / 1024:.0f} KB" if size < 1024 * 1024 else \
                               f"{size / 1048576:.1f} MB"
                except Exception:
                    size_txt = "-"
                self.tree.insert(parent, "end", text=f"{icon} {entry.name}",
                                 values=("☑" if key in done else "☐", size_txt),
                                 tags=("file", key))
                total += 1
        return total

    def _selected_path(self):
        """Secili dugumun dosya yolu (klasorse None)."""
        sel = self.tree.selection()
        if not sel:
            return None
        tags = self.tree.item(sel[0], "tags")
        if len(tags) < 2:
            return None
        return Path(tags[1]), tags[0]

    def toggle_done(self) -> None:
        """Bitirdim isaretini degistir."""
        got = self._selected_path()
        if not got or got[1] != "file":
            return
        path, _ = got
        on = self.repos.resources.toggle(self.pid, str(path))
        sel = self.tree.selection()[0]
        vals = list(self.tree.item(sel, "values"))
        vals[0] = "☑" if on else "☐"
        self.tree.item(sel, values=vals)
        self.app.set_status(("Bitirdi: " if on else "Isaret kaldirildi: ") + path.name)

    def open_selected(self) -> None:
        """Dosyayi varsayilan programda ac."""
        got = self._selected_path()
        if not got:
            return
        path, kind = got
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(path))            # noqa: S606
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as e:                      # noqa: BLE001
            messagebox.showerror(C.APP_NAME, f"Acilamadi:\n{e}")

    def open_in_reader(self) -> None:
        """Secili PDF'i program icindeki okuyucuda ac."""
        got = self._selected_path()
        if not got or got[1] != "file":
            return
        path, _ = got
        if path.suffix.lower() != ".pdf":
            messagebox.showinfo(C.APP_NAME, "Yalnizca PDF dosyalari okuyucuda acilir.")
            return
        self.app.settings["last_pdf"] = str(path)
        C.save_settings(self.app.settings)
        try:
            widget = self.app.goto_tab("tab.pdf")
            if widget is not None and hasattr(widget, "load_pdf"):
                widget.load_pdf(str(path))
        except Exception as e:                      # noqa: BLE001
            messagebox.showerror(C.APP_NAME, f"Okuyucu acilamadi:\n{e}")

    def reveal(self) -> None:
        """Dosyanin bulundugu klasoru ac."""
        got = self._selected_path()
        if not got:
            return
        path, kind = got
        folder = path if kind == "dir" else path.parent
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(folder))          # noqa: S606
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as e:                      # noqa: BLE001
            messagebox.showerror(C.APP_NAME, f"Acilamadi:\n{e}")

    def print_file(self) -> None:
        """Dosyayi sistemin varsayilan yazicisina gonder."""
        got = self._selected_path()
        if not got or got[1] != "file":
            return
        path, _ = got
        if not sys.platform.startswith("win"):
            messagebox.showinfo(C.APP_NAME, "Yazdirma yalnizca Windows'ta desteklenir.")
            return
        try:
            os.startfile(str(path), "print")       # noqa: S606
            self.app.set_status(f"Yaziciya gonderildi: {path.name}")
        except Exception as e:                      # noqa: BLE001
            messagebox.showerror(C.APP_NAME, f"Yazdirilamadi:\n{e}")
