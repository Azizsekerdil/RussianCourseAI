# -*- coding: utf-8 -*-
"""Ogrenci Takip: ustalik tablosu, zayif konular, sinav trendi, haftalik ozet raporu.

Veri yoksa bos grafik cizilmez; acikca 'veri yok' yazilir.
"""
from __future__ import annotations

import html
import tkinter as tk
import webbrowser
from datetime import date, timedelta
from tkinter import ttk

import rca_common as C
from rca.srs import mastery
from rca.ui_util import LazyTab, ScrollFrame, bar_chart, card, line_chart


class ProgressTab(LazyTab):
    """Profil bazli ilerleme paneli."""

    def build(self) -> None:
        p = self.palette()
        sf = ScrollFrame(self)
        sf.paint(p)
        sf.pack(fill="both", expand=True)
        b = sf.body
        self.body = b

        head = ttk.Frame(b, padding=(12, 12, 12, 0))
        head.pack(fill="x")
        ttk.Label(head, text="Ogrenci Takip", style="Title.TLabel").pack(side="left")
        ttk.Button(head, text=self.t("g.refresh"), command=self.refresh).pack(side="right")
        ttk.Button(head, text="📄 Haftalik Ozet", style="Accent.TButton",
                   command=self.weekly_report).pack(side="right", padx=6)

        self.cards = ttk.Frame(b, padding=12)
        self.cards.pack(fill="x")

        ttk.Label(b, text="Son 30 gun - dogru cevap sayisi", style="Title.TLabel",
                  padding=(12, 10, 0, 4)).pack(anchor="w")
        self.chart = tk.Canvas(b, height=180, highlightthickness=0)
        self.chart.pack(fill="x", padx=12)

        ttk.Label(b, text="Sinav puani trendi", style="Title.TLabel",
                  padding=(12, 16, 0, 4)).pack(anchor="w")
        self.trend = tk.Canvas(b, height=170, highlightthickness=0)
        self.trend.pack(fill="x", padx=12)

        ttk.Label(b, text="Zayif konular", style="Title.TLabel",
                  padding=(12, 16, 0, 4)).pack(anchor="w")
        self.weak = ttk.Frame(b, padding=(12, 0))
        self.weak.pack(fill="x")

        ttk.Label(b, text="Kelime ustaligi (en dusuk 25)", style="Title.TLabel",
                  padding=(12, 16, 0, 4)).pack(anchor="w")
        self.tv = ttk.Treeview(b, columns=("ru", "tr", "box", "acc", "due"),
                               show="headings", height=12)
        for c, w, t in (("ru", 180, "Kelime"), ("tr", 200, "Anlam"),
                        ("box", 80, "Kutu"), ("acc", 110, "Ustalik"),
                        ("due", 120, "Tekrar")):
            self.tv.heading(c, text=t)
            self.tv.column(c, width=w, anchor="w")
        self.tv.pack(fill="x", padx=12, pady=(0, 20))

        self.refresh()

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        """Sekmeye donuste tazele."""
        if getattr(self, "cards", None) is not None:
            self.refresh()

    def refresh(self) -> None:
        """Tum panelleri yeniden hesapla."""
        p = self.palette()
        for c in self.cards.winfo_children():
            c.destroy()
        for c in self.weak.winfo_children():
            c.destroy()

        d = self.repos.progress.dashboard(self.pid)
        tot = self.repos.study.totals(self.pid)
        streak = self.repos.study.streak(self.pid)
        attempts = tot["correct"] + tot["wrong"]
        acc = (100.0 * tot["correct"] / attempts) if attempts else 0.0
        goal = int(self.app.settings.get("daily_goal", 20))
        today_rows = [r for r in self.repos.study.daily(self.pid, 1)]
        today_done = today_rows[0]["correct"] + today_rows[0]["wrong"] if today_rows else 0

        items = [
            ("Gorulen kelime", str(d["seen"])),
            ("Ogrenildi", str(d["learned"])),
            ("Bugun tekrar", str(d["due"])),
            ("Seri", f"{streak} gun"),
            ("Dogruluk", f"%{acc:.0f}" if attempts else "-"),
            ("Bugunki hedef", f"{today_done}/{goal}"),
            ("Sure", f"{tot['seconds'] // 3600} sa {tot['seconds'] % 3600 // 60} dk"),
        ]
        for i, (title, value) in enumerate(items):
            c = card(self.cards, title, value, p)
            c.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            self.cards.columnconfigure(i, weight=1)

        daily = self.repos.study.daily(self.pid, 30)
        self.after(50, lambda: bar_chart(self.chart, daily, p, "correct"))

        exams = self.repos.exams.history(self.pid, 20)
        scores = [float(e["score"]) for e in reversed(exams)]
        self.after(50, lambda: line_chart(self.trend, scores, p))

        weak = self.repos.topics.weak(self.pid, 8)
        if not weak:
            ttk.Label(self.weak, text="Konu verisi yok - dilbilgisi laboratuvarlarindan "
                                      "veya sinavdan alistirma yapin.",
                      style="Dim.TLabel").pack(anchor="w")
        else:
            for w in weak:
                row = ttk.Frame(self.weak, style="Card.TFrame", padding=10)
                row.pack(fill="x", pady=2)
                ttk.Label(row, text=w["title"], style="Card.TLabel",
                          width=34).pack(side="left")
                pb = ttk.Progressbar(row, maximum=100, value=w["pct"], length=240)
                pb.pack(side="left", padx=10)
                color = p["err"] if w["pct"] < 50 else (p["warn"] if w["pct"] < 75 else p["ok"])
                ttk.Label(row, text=f"%{w['pct']:.0f}  ({w['total']} deneme)",
                          style="Card.TLabel", foreground=color).pack(side="left")

        self.tv.delete(*self.tv.get_children())
        rows = self.repos.db.query(
            "SELECT w.ru, w.tr, p.box, p.correct, p.wrong, p.due_date FROM words w "
            "JOIN word_progress p ON p.word_id=w.id WHERE p.profile_id=? "
            "AND (p.correct+p.wrong)>0 ORDER BY "
            "(CAST(p.correct AS REAL)/(p.correct+p.wrong)) ASC, p.wrong DESC LIMIT 25",
            (self.pid,))
        for r in rows:
            m = mastery(int(r["correct"]), int(r["wrong"]), int(r["box"] or 0))
            self.tv.insert("", "end", values=(r["ru"], r["tr"], r["box"],
                                              f"%{m * 100:.0f}", r["due_date"] or "-"))
        if not rows:
            self.tv.insert("", "end", values=("(veri yok)", "", "", "", ""))

    # ------------------------------------------------------------------
    def weekly_report(self) -> None:
        """A4 yazdirilabilir tek sayfa HTML raporu uret ve tarayicida ac."""
        p = self.palette()
        prof = self.repos.db.one("SELECT * FROM profiles WHERE id=?", (self.pid,))
        name = prof["name"] if prof else "Ogrenci"
        daily = self.repos.study.daily(self.pid, 7)
        tot7c = sum(d["correct"] for d in daily)
        tot7w = sum(d["wrong"] for d in daily)
        secs = sum(d["seconds"] for d in daily)
        d = self.repos.progress.dashboard(self.pid)
        streak = self.repos.study.streak(self.pid)
        weak = self.repos.topics.weak(self.pid, 6)
        exams = self.repos.exams.history(self.pid, 5)

        if tot7c + tot7w == 0:
            body_note = ("<p class='empty'>Bu hafta calisma verisi yok. "
                         "Tekrar veya sinav yaptiginizda bu rapor dolacak.</p>")
            bars = ""
        else:
            body_note = ""
            top = max(max(x["correct"] + x["wrong"] for x in daily), 1)
            bars = "<div class='chart'>"
            for x in daily:
                h = int(70 * (x["correct"] + x["wrong"]) / top)
                bars += (f"<div class='col'><div class='bar' style='height:{h}px'></div>"
                         f"<span>{x['day'][5:]}</span></div>")
            bars += "</div>"

        weak_rows = "".join(
            f"<tr><td>{html.escape(w['title'])}</td><td>%{w['pct']:.0f}</td>"
            f"<td>{w['total']}</td></tr>" for w in weak)
        if not weak_rows:
            weak_rows = "<tr><td colspan='3' class='empty'>Konu verisi yok</td></tr>"

        exam_rows = "".join(
            f"<tr><td>{e['started_at'][:16].replace('T', ' ')}</td>"
            f"<td>{e['correct']}/{e['total']}</td><td>%{e['score']:.0f}</td></tr>"
            for e in exams)
        if not exam_rows:
            exam_rows = "<tr><td colspan='3' class='empty'>Bu donemde sinav yok</td></tr>"

        acc = (100.0 * tot7c / (tot7c + tot7w)) if (tot7c + tot7w) else 0
        start = (date.today() - timedelta(days=6)).strftime("%d.%m.%Y")
        end = date.today().strftime("%d.%m.%Y")

        doc = f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<title>{html.escape(C.APP_NAME)} - Haftalik Ozet</title>
<style>
 @page {{ size: A4; margin: 18mm; }}
 body {{ font-family: "Segoe UI", Arial, sans-serif; color:#1c1e24; }}
 h1 {{ font-size: 20pt; margin:0 0 2px; }}
 .sub {{ color:#5d6470; margin-bottom:18px; }}
 .grid {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:18px; }}
 .card {{ border:1px solid #c9ccd4; border-radius:8px; padding:10px 14px; min-width:110px; }}
 .card b {{ display:block; font-size:19pt; }}
 .card span {{ color:#5d6470; font-size:9pt; }}
 table {{ width:100%; border-collapse:collapse; margin-bottom:16px; font-size:10pt; }}
 th,td {{ border-bottom:1px solid #dfe2e8; padding:6px 4px; text-align:left; }}
 th {{ background:#f0f2f6; }}
 .chart {{ display:flex; align-items:flex-end; gap:8px; height:96px; margin:8px 0 20px; }}
 .col {{ text-align:center; font-size:8pt; color:#5d6470; }}
 .bar {{ width:34px; background:#2f6fe0; border-radius:3px 3px 0 0; }}
 .empty {{ color:#8a90a0; font-style:italic; }}
 h2 {{ font-size:12pt; margin:14px 0 6px; }}
 @media print {{ .noprint {{ display:none; }} }}
</style></head><body>
<h1>{html.escape(name)} · Haftalik Ozet</h1>
<div class="sub">{start} – {end} · {html.escape(C.APP_NAME)} v{C.VERSION}</div>
{body_note}
<div class="grid">
 <div class="card"><b>{tot7c}</b><span>dogru (7 gun)</span></div>
 <div class="card"><b>{tot7w}</b><span>yanlis (7 gun)</span></div>
 <div class="card"><b>%{acc:.0f}</b><span>dogruluk</span></div>
 <div class="card"><b>{secs // 60}</b><span>dakika calisma</span></div>
 <div class="card"><b>{streak}</b><span>gun seri</span></div>
 <div class="card"><b>{d['learned']}</b><span>ogrenilen kelime</span></div>
 <div class="card"><b>{d['due']}</b><span>bekleyen tekrar</span></div>
</div>
<h2>Gunluk etkinlik</h2>
{bars}
<h2>Zayif konular</h2>
<table><tr><th>Konu</th><th>Basari</th><th>Deneme</th></tr>{weak_rows}</table>
<h2>Son sinavlar</h2>
<table><tr><th>Tarih</th><th>Dogru</th><th>Puan</th></tr>{exam_rows}</table>
<p class="noprint" style="color:#5d6470;font-size:9pt">
Yazdirmak icin Ctrl+P. Bu rapor cevrimdisi uretildi; hicbir veri disari gonderilmedi.</p>
</body></html>"""

        out = C.EXPORT_DIR / f"haftalik_ozet_{date.today():%Y%m%d}_{self.pid}.html"
        try:
            C.ensure_dirs()
            out.write_text(doc, encoding="utf-8")
            webbrowser.open(out.as_uri())
            self.app.set_status(f"Rapor: {out}")
        except Exception as e:                          # noqa: BLE001
            self.app.set_status(f"Rapor yazilamadi: {e}")
