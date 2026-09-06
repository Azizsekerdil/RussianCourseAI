# -*- coding: utf-8 -*-
"""Sozluk RU-EN sekmesi: cift yonlu Rusca <-> Ingilizce arama, TTS, AI, ice/disa aktarim.

AI katmani: yerel sonuc yoksa (politika kapali degilse) sorgu arka planda LM Studio'ya
ya da Ayarlar'daki alternatif OpenAI uyumlu uca sorulur; gelen yapisal maddeler
listeye "AI" etiketiyle eklenir ve istenirse yerel sozluge kaydedilir, boylece bir
sonraki arama aninda ve cevrimdisi calisir. Arayuz thread'i hicbir zaman bloklanmaz.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

import rca_common as C
from rca import dictionary as D
from rca.i18n import S
from rca.ui_util import LazyTab, style_text

# politika kodu -> i18n anahtari (arac cubugu ve Ayarlar ayni listeyi kullanir)
POLICY_KEYS = {"auto": "d.policy_auto", "local": "d.policy_local",
               "alt": "d.policy_alt", "off": "d.policy_off"}


def policy_code(label: str) -> str:
    """Kutudaki etiketi politika koduna cevir - etiket HANGI dilde olursa olsun.

    Arayuz dili kutu doldurulduktan sonra degisebilir (Ayarlar'da dil + kaydet,
    ust cubuktan dil secimi); eslestirme bu yuzden aktif dile degil, anahtarin
    tum cevirilerine bakar. Bilinmeyen etiket -> "auto".
    """
    for code, key in POLICY_KEYS.items():
        if label in S[key].values():
            return code
    return "auto"


class DictionaryTab(LazyTab):
    """Gomulu + kullanici + OpenRussian + AI katmanlarini birlestiren sozluk sayfasi."""

    MAX_HISTORY = 12

    def build(self) -> None:
        p = self.palette()
        self.dict = D.build_dictionary(self.repos.dictionary.all())
        self.history: list = []
        self.results: list = []
        self._or_loaded = False
        self._ai_seq = 0              # son AI isteginin sirasi; eski yanitlar yok sayilir
        self._query_key = ""          # listedeki sonuclarin ait oldugu sorgu (normalize)
        self._ai_extra: dict = {}     # sorgu anahtari -> o sorgu icin AI'dan gelen maddeler
        self._provider = None         # son cozumlenen saglayici (durum etiketi icin)

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

        # --- AI satiri: politika secici + saglayici durumu ----------------
        airow = ttk.Frame(root)
        airow.pack(fill="x", pady=(6, 0))
        ttk.Label(airow, text=self.t("d.ai_policy"), style="Dim.TLabel").pack(side="left")
        self.policy_var = tk.StringVar(value=self._policy_label(self.app.settings.get("dict_ai", "auto")))
        self.policy_box = ttk.Combobox(airow, textvariable=self.policy_var, state="readonly",
                                       width=20, values=self._policy_values())
        self.policy_box.pack(side="left", padx=6)
        self.policy_box.bind("<<ComboboxSelected>>", self._on_policy_change)
        self.provider_lbl = ttk.Label(airow, text="", style="Dim.TLabel")
        self.provider_lbl.pack(side="left", padx=(8, 0))

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
        self.w_ex = ttk.Label(right, text="", style="RU.TLabel", font=(C.FONT_FAMILY, 12),
                              wraplength=340, justify="left")
        self.w_ex.pack(anchor="w", pady=(6, 0))
        self.w_note = ttk.Label(right, text="", style="Dim.TLabel", wraplength=340, justify="left")
        self.w_note.pack(anchor="w", pady=(2, 0))
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
        # yalnizca kaydedilmemis AI maddesi seciliyken gorunur
        self.btn_save_ai = ttk.Button(btns2, text="💾 " + self.t("d.save_entry"),
                                      command=self.save_ai_entry)

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
        self.after(250, self.refresh_provider_status)

        self.entry.focus_set()

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        if getattr(self, "entry", None) is not None:
            self.entry.focus_set()
            self._sync_policy()
            self.refresh_provider_status()

    def on_language_change(self) -> None:
        if getattr(self, "policy_box", None) is None:
            return
        self.policy_box["values"] = self._policy_values()
        self._sync_policy()
        self._show_provider(self._provider)
        cur = self.current()
        self._fill(self.results)
        self._reselect(cur)

    def _update_count(self) -> None:
        by = self.dict.count_by_source()
        parts = [f"{self.t('d.builtin')} {by.get(D.SOURCE_BUILTIN, 0)}",
                 f"{self.t('d.user')} {by.get(D.SOURCE_USER, 0)}"]
        if by.get(D.SOURCE_AI):
            parts.append(f"{self.t('d.src_ai')} {by[D.SOURCE_AI]}")
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

    # -- AI politikasi / saglayici durumu --------------------------------
    def _policy_values(self) -> list:
        return [self.t(k) for k in POLICY_KEYS.values()]

    def _policy_label(self, code: str) -> str:
        return self.t(POLICY_KEYS.get(code, "d.policy_auto"))

    def _policy_code(self, label: str) -> str:
        return policy_code(label)

    def _sync_policy(self) -> None:
        """Ayarlar sekmesinden degistirilmis olabilir - kutuyu ayarla esitle."""
        self.policy_var.set(self._policy_label(self.app.settings.get("dict_ai", "auto")))

    def _on_policy_change(self, _evt=None) -> None:
        code = self._policy_code(self.policy_var.get())
        self.app.settings["dict_ai"] = code
        C.save_settings(self.app.settings)
        self.refresh_provider_status()

    def _ai_off(self) -> bool:
        s = self.app.settings
        return s.get("dict_ai", "auto") == "off" or not s.get("ai_enabled", True)

    def refresh_provider_status(self) -> None:
        """Saglayiciyi arka planda cozumle (erisilebilirlik denetimi ag bekletebilir)."""
        if self._ai_off():
            self._provider = None
            self._show_provider(None)
            return
        self.provider_lbl.configure(text=self.t("d.status_checking"),
                                    foreground=self.palette()["fg_dim"])

        def job():
            return self.app.dict_provider()

        def done(client):
            self._provider = client
            self._show_provider(client)

        self.app.worker.run(job, done, lambda _e: self._show_provider(None))

    def _show_provider(self, client) -> None:
        if not self.winfo_exists():
            return
        p = self.palette()
        if self._ai_off():
            text, color = self.t("d.status_off"), p["fg_dim"]
        elif client is None:
            text, color = self.t("d.status_none"), p["warn"]
        elif client is self.app.ai:
            text, color = self.t("d.status_local"), p["ok"]
        else:
            text, color = self.t("d.status_alt"), p["ok"]
        self.provider_lbl.configure(text=text, foreground=color)

    # ------------------------------------------------------------------
    def search(self, quiet: bool = False) -> None:
        q = self.q.get().strip()
        if not q:
            self._query_key = ""
            self._fill([])
            self._update_save_button()
            return
        self._query_key = D.norm_query(q)
        rows = self._with_ai_extra(self._query_key, self.dict.lookup(q))
        cur = self.current()
        self._fill(rows)
        if quiet:
            self._reselect(cur)          # tuslama / OpenRussian yuklendi: secim ve dugme korunur
            return
        self._remember(q)
        if rows:
            self.tree.selection_set(self.tree.get_children()[0])
            self.tree.focus(self.tree.get_children()[0])
            self.on_select()
            self.app.set_status(f"'{q}': {len(rows)} {self.t('d.results')}")
            return
        self._clear_detail()
        self.app.set_status(self.t("d.noresult"))
        self._ai_write(self.t("d.noresult"))
        if not self._ai_off():
            self.ai_lookup(q)                          # yerel sonuc yok -> AI'a sor

    def _with_ai_extra(self, key: str, rows) -> list:
        """Bu sorgu icin AI'dan gelmis ama HENUZ kaydedilmemis maddeleri listenin basina koy.

        Otomatik kayit kapaliyken AI maddeleri self.dict'te degildir, yalnizca burada
        yasar; boylece sessiz bir yeniden arama (OpenRussian yuklendi, tuslama) onlari
        silmez ve ayni sorguya ikinci Enter aga cikmadan ayni yaniti gosterir.
        Kaydedilmis maddeler normal aramadan (kendi siralamasiyla) gelir.
        """
        extra = [e for e in self._ai_extra.get(key) or [] if not self.dict.contains(e)]
        if not extra:
            return list(rows)
        return extra + [e for e in rows if e not in extra]

    def _reselect(self, entry) -> None:
        """Yeniden doldurulan listede ayni madde varsa secimi (ve detay panelini) koru."""
        if entry is not None and entry in self.results:
            iid = str(self.results.index(entry))
            self.tree.selection_set(iid)
            self.tree.focus(iid)
            self.on_select()
        else:
            self._update_save_button()

    def _fill(self, rows) -> None:
        self.tree.delete(*self.tree.get_children())
        self.results = list(rows)
        lang = self.app.ui_lang()
        src_names = {D.SOURCE_BUILTIN: self.t("d.builtin"), D.SOURCE_USER: self.t("d.user"),
                     D.SOURCE_OPENRUSSIAN: "OpenRussian", D.SOURCE_AI: self.t("d.src_ai")}
        for i, e in enumerate(self.results):
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

    def _clear_detail(self) -> None:
        self.w_ru.configure(text="—")
        for w in (self.w_ipa, self.w_pos, self.w_en, self.w_ex, self.w_note, self.w_bank):
            w.configure(text="")
        self.btn_save_ai.pack_forget()

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
        if e.source == D.SOURCE_AI:
            pos += f" · {self.t('d.src_ai')}"
        self.w_pos.configure(text=pos)
        self.w_en.configure(text=e.translation.replace(";", "\n"))
        self.w_ex.configure(text=e.example or "")
        self.w_note.configure(text=e.note or "")
        found = self.repos.words.search(e.headword, limit=3)
        exact = [w for w in found if C.normalize_ru(w["ru"]) == C.normalize_ru(e.headword)]
        if exact:
            w = exact[0]
            self.w_bank.configure(text=f"📚 {w['tr']}  ({w['tags']})")
        else:
            self.w_bank.configure(text="")
        self._update_save_button(e)

    def _update_save_button(self, e=None) -> None:
        """Kaydedilmemis bir AI maddesi seciliyse 'Sozluge kaydet' dugmesini goster."""
        e = e or self.current()
        if e is not None and e.source == D.SOURCE_AI and not self.dict.contains(e):
            self.btn_save_ai.pack(side="left", padx=4)
        else:
            self.btn_save_ai.pack_forget()

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
                             pos=pos, deck="Sozluk", example_ru=e.example or "")
        self.app.set_status(self.t("d.added_bank") + f": {e.headword}")
        self.on_select()

    # -- AI ----------------------------------------------------------------
    def ask_ai(self) -> None:
        """Sorguyu (yerel sonuc olsa da) AI'a sor; gelen maddeler listenin basina eklenir."""
        text = self.q.get().strip()
        e = self.current()
        if not text and e:
            text = e.headword
        if not text:
            return
        if self._ai_off():
            self._ai_write(f"{self.t('d.status_off')}\n{self.t('d.noresult')}")
            self.app.set_status(self.t("d.status_off"))
            return
        self.ai_lookup(text)

    def ai_lookup(self, query: str) -> None:
        """Yapisal sozluk sorgusunu arka planda calistir; yanit ana threadde islenir."""
        query = (query or "").strip()
        if not query:
            return
        self._ai_seq += 1
        seq = self._ai_seq
        owner = self._query_key       # yanit yalnizca bu sorgunun listesine karisabilir
        lang = self.app.ui_lang()
        self.app.set_status(self.t("d.ai_asking"))
        self._ai_write(self.t("d.ai_asking"))

        def job():
            client = self.app.dict_provider()
            if client is None:
                return None, []
            return client, D.ai_lookup(client, query, lang)

        def stale() -> bool:
            """Arada yeni bir AI istegi ya da baska bir sorgu geldiyse yanit atilir."""
            return seq != self._ai_seq or owner != self._query_key or not self.winfo_exists()

        def done(result):
            if stale():
                return
            client, entries = result
            self._provider = client
            self._show_provider(client)
            if client is None:
                msg = self.t("d.ai_unavailable")
                self.app.set_status(msg)
                self._ai_write(f"{self.t('ai.offline')}\n\n{msg}")
                return
            if not entries:
                self.app.set_status(self.t("d.ai_nothing"))
                self._ai_write(f"{self.t('d.ai_nothing')}\n\n{self._provider_line(client)}")
                return
            self._merge_ai(entries, client, query)

        def err(exc: Exception):
            if stale():
                return
            self._provider = None
            self._show_provider(None)
            self._ai_err(exc)
            self.app.set_status(self.t("d.status_none"))

        self.app.worker.run(job, done, err)

    def _merge_ai(self, entries, client, query: str = "") -> None:
        """AI maddelerini listenin basina koy, ilkini sec, istenirse kaydet."""
        entries = list(entries)
        self._ai_extra[D.norm_query(query or self.q.get())] = entries
        keep = [e for e in self.results if e not in entries]
        self._fill(entries + keep)
        first = self.tree.get_children()[0]
        self.tree.selection_set(first)
        self.tree.focus(first)
        self.on_select()
        self._ai_write(self._render_ai(entries, client))
        status = self.t("d.ai_found").format(n=len(entries))
        if self.app.settings.get("dict_ai_autosave", True):
            self._persist_ai(entries)
            status += "  ·  " + self.t("d.ai_saved")
        self.app.set_status(status)
        self._update_save_button()

    def _persist_ai(self, entries) -> int:
        """AI maddelerini dict_entries'e ('ai' kaynagi) ve bellekteki sozluge ekle."""
        fresh = [e for e in entries if not self.dict.contains(e)]
        if not fresh:
            return 0
        rows = [(e.display.replace(C.STRESS_MARK, "'"), e.translation, e.pos, e.extra,
                 e.example, e.note) for e in fresh]
        n = self.repos.dictionary.add_many(rows, source=D.SOURCE_AI)
        self.dict.extend(fresh)
        self._update_count()
        return n

    def save_ai_entry(self) -> None:
        e = self.current()
        if not e or e.source != D.SOURCE_AI:
            return
        self._persist_ai([e])
        self.app.set_status(self.t("d.entry_saved"))
        self._update_save_button(e)

    def _provider_line(self, client) -> str:
        who = "LM Studio" if client is self.app.ai else self.t("d.policy_alt")
        model = getattr(client, "last_model", "") or getattr(client, "model", "")
        return f"{self.t('d.ai_provider')}: {who}" + (f" · {model}" if model else "")

    def _render_ai(self, entries, client) -> str:
        """AI yanitinin sikistirilmis dokumu (madde, tur, ceviri, ornek, not)."""
        lang = self.app.ui_lang()
        lines = [self._provider_line(client), ""]
        for e in entries:
            pos = e.pos_label(lang) + (f", {e.extra_label(lang)}" if e.extra else "")
            lines.append(f"{e.display}  ({pos})  —  {e.translation}")
            if e.example:
                lines.append(f"   ✎ {e.example}")
            if e.note:
                lines.append(f"   ℹ {e.note}")
            lines.append("")
        return "\n".join(lines).rstrip()

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
