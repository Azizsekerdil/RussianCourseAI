# -*- coding: utf-8 -*-
"""Russian Course AI - giris noktasi.

Bu dosya YALNIZCA pencereyi, temayi, kenar cubugunu ve sayfa cercevelerini kurar.
Her sayfanin icerigi kendi modulundedir ve tembel yuklenir.
"""
from __future__ import annotations

import sys
import tkinter as tk
import traceback
from pathlib import Path
from tkinter import messagebox, ttk

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rca_common as C
from rca import i18n
from rca.ui_util import Pill, Sidebar, Worker, apply_theme

# (anahtar, modul, sinif, ikon, grup)
TAB_SPECS = [
    ("tab.srs",       "rca.tabs.srs_tab",       "SRSTab",       "🔁", "grp.learn"),
    ("tab.vocab",     "rca.tabs.vocab_tab",     "VocabTab",     "📚", "grp.learn"),
    ("tab.dictionary", "rca.tabs.dictionary_tab", "DictionaryTab", "📖", "grp.learn"),
    ("tab.exam",      "rca.tabs.exam_tab",      "ExamTab",      "📝", "grp.learn"),
    ("tab.cyrillic",  "rca.tabs.cyrillic_tab",  "CyrillicTab",  "Аа", "grp.lab"),
    ("tab.pron",      "rca.tabs.pron_tab",      "PronTab",      "🔊", "grp.lab"),
    ("tab.grammar",   "rca.tabs.grammar_tab",   "GrammarTab",   "⚙", "grp.lab"),
    ("tab.resources", "rca.tabs.resources_tab", "ResourcesTab", "🗂", "grp.read"),
    ("tab.pdf",       "rca.tabs.pdf_tab",       "PdfTab",       "📕", "grp.read"),
    ("tab.library",   "rca.tabs.library_tab",   "LibraryTab",   "🌐", "grp.read"),
    ("tab.ai",        "rca.tabs.ai_tab",        "AITab",        "🤖", "grp.practice"),
    ("tab.speaking",  "rca.tabs.speaking_tab",  "SpeakingTab",  "💬", "grp.practice"),
    ("tab.writing",   "rca.tabs.writing_tab",   "WritingTab",   "✍", "grp.practice"),
    ("tab.progress",  "rca.tabs.progress_tab",  "ProgressTab",  "📈", "grp.system"),
    ("tab.packs",     "rca.tabs.packs_tab",     "PacksTab",     "📦", "grp.system"),
    ("tab.tokens",    "rca.tabs.tokens_tab",    "TokensTab",    "🎫", "grp.system"),
    ("tab.guide",     "rca.tabs.guide_tab",     "GuideTab",     "❓", "grp.system"),
    ("tab.settings",  "rca.tabs.settings_tab",  "SettingsTab",  "⚙", "grp.system"),
]

GROUP_ORDER = ["grp.learn", "grp.lab", "grp.read", "grp.practice", "grp.system"]


class App(tk.Tk):
    """Ana pencere: kenar cubugu + tek icerik alani."""

    def __init__(self) -> None:
        super().__init__()
        C.ensure_dirs()
        self.settings = C.load_settings()
        self.title(f"{C.APP_NAME} {C.VERSION}")
        self.geometry("1340x860")
        self.minsize(1080, 680)
        self._set_icon()

        self.style = ttk.Style(self)
        self.palette = apply_theme(self, self.style, self.settings["theme"])
        self.worker = Worker(self)

        self.db = None
        self.repos = None
        self.profile_id = 0
        self.speaker = None
        self.ai = None                 # yerel LM Studio istemcisi
        self.ai_alt = None             # alternatif OpenAI uyumlu uc (NIM / OpenRouter / ...)
        self._tabs = {}
        self._current_key = None

        self._boot()
        self._build_shell()
        self._build_pages()
        self._bind_keys()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(60, lambda: self.sidebar.select(TAB_SPECS[0][0]))
        self.after(400, self.check_ai)
        self.after(700, self.refresh_badges)

    # -- baslangic ---------------------------------------------------------
    def _set_icon(self) -> None:
        """Pencere simgesini ayarla (yoksa sessizce gec)."""
        try:
            ico = C.PROGRAM_DIR / "assets" / "app.ico"
            if ico.exists():
                self.iconbitmap(default=str(ico))
        except Exception:
            pass

    def _boot(self) -> None:
        """Veritabani, profil, ses ve AI istemcisini hazirla.

        Herhangi biri kurulamazsa program yine acilir; ilgili ozellik kapali kalir.
        """
        from rca.db import Database, Repos
        try:
            self.db = Database()
            self.repos = Repos(self.db)
        except Exception as e:                              # noqa: BLE001
            messagebox.showerror(C.APP_NAME,
                                 f"Veritabani acilamadi:\n{e}\n\n"
                                 f"Dosya: {C.DB_PATH}\n"
                                 "Dosyayi tasiyip programi yeniden baslatin.")
            raise SystemExit(1)

        pid = self.settings.get("profile_id")
        try:
            known = {p["id"] for p in self.repos.profiles.all()}
            self.profile_id = pid if pid in known else self.repos.profiles.ensure_default()
        except Exception:
            self.profile_id = self.repos.profiles.ensure_default()
        self.settings["profile_id"] = self.profile_id
        C.save_settings(self.settings)

        from rca.tts import Speaker
        try:
            self.speaker = Speaker(rate=int(self.settings.get("tts_rate", 150)))
        except Exception:
            self.speaker = None

        import rca.secrets as secrets
        from rca.ai_client import AIClient
        self.ai = AIClient(self.settings.get("ai_base", C.LMSTUDIO_BASE),
                           token_logger=self._log_tokens)
        # Alternatif uc: anahtar gizli depodan (Credential Manager / dosya) okunur,
        # settings.json'da asla yer almaz. Iki istemci de ayni token defterini kullanir.
        self.ai_alt = AIClient(self.settings.get("alt_base", C.NIM_BASE),
                               token_logger=self._log_tokens,
                               api_key=secrets.get_secret(secrets.KEY_ALT_API),
                               model=self.settings.get("alt_model", C.ALT_DEFAULT_MODEL))

    def _log_tokens(self, model, task, ptok, ctok, ms, ok) -> None:
        """AI istemcisinden gelen token bilgisini deftere yaz."""
        try:
            self.repos.tokens.log(model, task, ptok, ctok, ms, ok)
        except Exception:
            pass

    def refresh_ai_clients(self) -> None:
        """Ayarlar kaydedilince iki istemciyi de (adres / anahtar / model) tazele."""
        import rca.secrets as secrets
        s = self.settings
        if self.ai is not None:
            self.ai.configure(base=s.get("ai_base", C.LMSTUDIO_BASE))
        if self.ai_alt is not None:
            self.ai_alt.configure(base=s.get("alt_base", C.NIM_BASE),
                                  api_key=secrets.get_secret(secrets.KEY_ALT_API),
                                  model=s.get("alt_model", C.ALT_DEFAULT_MODEL))

    def dict_provider(self):
        """Sozluk icin kullanilacak AI istemcisi (dict_ai politikasina gore) ya da None.

        Erisilebilirlik denetimi ag bekletebilir: arka plandan (worker) cagirin.
        """
        from rca.ai_client import resolve_dict_provider
        return resolve_dict_provider(self.settings, self.ai, self.ai_alt)

    # -- iskelet -----------------------------------------------------------
    def _build_shell(self) -> None:
        """Kenar cubugu, ust bar, icerik alani ve durum cubugu."""
        p = self.palette

        self.sidebar = Sidebar(self, p, self._on_nav)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.add_brand(C.APP_NAME.replace(" AI", ""), f"AI · v{C.VERSION}")

        seen_groups = []
        for key, _m, _c, icon, group in TAB_SPECS:
            if group not in seen_groups:
                seen_groups.append(group)
                self.sidebar.add_group(self.t(group), group)
            self.sidebar.add_item(key, icon, self.t(key))
        self.sidebar.add_spacer()

        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True)

        # --- ust bar ------------------------------------------------------
        top = tk.Frame(right, background=p["panel"], height=54)
        top.pack(fill="x")
        top.pack_propagate(False)

        self.page_title = tk.Label(top, text="", background=p["panel"],
                                   foreground=p["fg"], font=(C.FONT_FAMILY, 14, "bold"))
        self.page_title.pack(side="left", padx=(20, 0))
        self.page_hint = tk.Label(top, text="", background=p["panel"],
                                  foreground=p["fg_mute"], font=C.FONT_UI_SM)
        self.page_hint.pack(side="left", padx=(12, 0))

        self.ai_pill = Pill(top, p, "AI: kontrol...", "fg_dim", width=176, bg=p["panel"])
        self.ai_pill.pack(side="right", padx=(8, 18))
        self.ai_pill.bind("<Button-1>", lambda _e: self.check_ai())

        ttk.Button(top, text="+", width=3, style="Panel.TButton",
                   command=self.new_profile).pack(side="right")
        self.profile_var = tk.StringVar()
        self.profile_box = ttk.Combobox(top, textvariable=self.profile_var,
                                        state="readonly", width=17)
        self.profile_box.pack(side="right", padx=(0, 6))
        self.profile_box.bind("<<ComboboxSelected>>", self._on_profile_change)
        self.profile_label = tk.Label(top, text=self.t("g.profile"),
                                      background=p["panel"], foreground=p["fg_dim"],
                                      font=C.FONT_UI_SM)
        self.profile_label.pack(side="right", padx=(0, 8))
        self.refresh_profiles()

        # Dil secimi her sayfadan ulasilabilir ve secim aninda uygulanir.
        self.language_var = tk.StringVar(
            value=i18n.LANG_NAMES.get(self.ui_lang(), i18n.LANG_NAMES["tr"]))
        self.language_box = ttk.Combobox(
            top, textvariable=self.language_var, state="readonly", width=9,
            values=[i18n.LANG_NAMES[code] for code in i18n.LANGS])
        self.language_box.pack(side="right", padx=(6, 8))
        self.language_box.bind("<<ComboboxSelected>>", self._on_language_change)
        self.language_label = tk.Label(top, text="🌐", background=p["panel"],
                                       foreground=p["fg_dim"], font=C.FONT_UI_SM)
        self.language_label.pack(side="right")

        # --- durum cubugu -------------------------------------------------
        self.status = tk.StringVar(value=self.t("g.ready"))
        bar = tk.Frame(right, background=p["deep"], height=26)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Label(bar, textvariable=self.status, background=p["deep"],
                 foreground=p["fg_dim"], font=C.FONT_UI_SM).pack(side="left", padx=16)
        tk.Label(bar, text=str(C.APP_HOME), background=p["deep"],
                 foreground=p["fg_mute"], font=C.FONT_UI_SM).pack(side="right", padx=16)

        # --- icerik -------------------------------------------------------
        self.content = ttk.Frame(right, padding=(18, 14, 18, 10))
        self.content.pack(fill="both", expand=True)

    def _build_pages(self) -> None:
        """Sayfa cercevelerini olustur - icerik tembel yuklenir."""
        import importlib
        for key, module_path, cls_name, _icon, _grp in TAB_SPECS:
            try:
                mod = importlib.import_module(module_path)
                frame = getattr(mod, cls_name)(self.content, self)
            except Exception:                                # noqa: BLE001
                frame = self._error_page(traceback.format_exc())
            self._tabs[key] = frame

    def _error_page(self, detail: str) -> ttk.Frame:
        """Yuklenemeyen sayfa icin bilgi cercevesi."""
        from rca.ui_util import LazyTab, style_text
        f = LazyTab(self.content, self)
        f._built = True
        ttk.Label(f, text="Bu bolum yuklenemedi.", style="Err.TLabel").pack(
            anchor="w", pady=(16, 4))
        box = tk.Text(f, height=18, wrap="word")
        style_text(box, self.palette, mono=True)
        box.pack(fill="both", expand=True, pady=8)
        box.insert("1.0", detail)
        box.configure(state="disabled")
        return f

    def _bind_keys(self) -> None:
        """Genel kisayollar."""
        order = [spec[0] for spec in TAB_SPECS]
        for i in range(1, 10):
            if i <= len(order):
                self.bind(f"<Control-Key-{i}>",
                          lambda _e, k=order[i - 1]: self.sidebar.select(k))
        self.bind("<Control-q>", lambda e: self.on_close())
        self.bind("<F5>", lambda e: self._refresh_current())
        self.bind("<Control-Next>", lambda e: self._step(1))
        self.bind("<Control-Prior>", lambda e: self._step(-1))

    def _step(self, delta: int) -> None:
        """Kenar cubugunda bir sonraki/onceki sayfaya gec."""
        order = [spec[0] for spec in TAB_SPECS]
        if self._current_key not in order:
            return
        i = (order.index(self._current_key) + delta) % len(order)
        self.sidebar.select(order[i])

    # -- gezinme -----------------------------------------------------------
    def _on_nav(self, key: str) -> None:
        """Kenar cubugundan sayfa secildi."""
        page = self._tabs.get(key)
        if page is None:
            return
        current = self._tabs.get(self._current_key)
        if current is not None and current is not page:
            current.pack_forget()
        self._current_key = key
        page.pack(fill="both", expand=True)
        page.ensure_built()
        try:
            page.on_show()
        except Exception:
            pass
        self.page_title.configure(text=self.t(key))
        self.page_hint.configure(text=self.u(PAGE_HINTS.get(key, "")))
        self.localize_widgets(page)
        self.set_status(self.t("g.ready"))

    def current_page(self):
        """Su anda goruntulenen sayfa parcasi."""
        return self._tabs.get(self._current_key)

    def _refresh_current(self) -> None:
        """Gorunen sayfayi tazele (F5)."""
        page = self.current_page()
        if page is not None:
            try:
                page.on_show()
                self.localize_widgets(page)
                self.set_status(self.t("g.refreshed"))
            except Exception:
                pass

    def goto_tab(self, key: str):
        """Sayfaya gec, icerigin kurulmasini garanti et ve parcayi dondur."""
        if key not in self._tabs:
            return None
        self.sidebar.select(key)
        return self._tabs.get(key)

    # -- profil ------------------------------------------------------------
    def _on_profile_change(self, _evt=None) -> None:
        """Profil degistiginde gorunen sayfayi tazele."""
        name = self.profile_var.get()
        for prof in self.repos.profiles.all():
            if prof["name"] == name:
                self.profile_id = int(prof["id"])
                break
        self.settings["profile_id"] = self.profile_id
        C.save_settings(self.settings)
        self.set_status(f"Profil: {name}")
        self._refresh_current()
        self.refresh_badges()

    def refresh_profiles(self) -> None:
        """Profil listesini yeniden doldur."""
        profs = self.repos.profiles.all()
        self.profile_box["values"] = [p["name"] for p in profs]
        for p in profs:
            if int(p["id"]) == int(self.profile_id):
                self.profile_var.set(p["name"])
                return
        if profs:
            self.profile_var.set(profs[0]["name"])
            self.profile_id = int(profs[0]["id"])

    def new_profile(self) -> None:
        """Yeni ogrenci profili olustur."""
        from tkinter import simpledialog
        name = simpledialog.askstring(C.APP_NAME, self.t("g.new_profile"), parent=self)
        if not name or not name.strip():
            return
        self.profile_id = self.repos.profiles.create(name.strip())
        self.refresh_profiles()
        self._on_profile_change()

    # -- rozetler / AI -----------------------------------------------------
    def refresh_badges(self) -> None:
        """Kenar cubugundaki sayi rozetlerini guncelle."""
        try:
            d = self.repos.progress.dashboard(self.profile_id)
            self.sidebar.set_badge("tab.srs", str(d["due"]) if d["due"] else "")
            self.sidebar.set_badge("tab.vocab", "")
        except Exception:
            pass

    def check_ai(self) -> None:
        """LM Studio durumunu arka planda yokla."""
        if not self.settings.get("ai_enabled", True):
            self.ai_pill.set("AI: kapali", "fg_dim")
            return
        self.ai_pill.set("AI: kontrol...", "fg_dim")

        def done(models):
            if models:
                mdl = self.ai.resolve("chat") or models[0]
                self.ai_pill.set(mdl[:22], "ok")
            else:
                self.ai_pill.set("AI: cevrimdisi", "warn")
        self.worker.run(lambda: self.ai.models(force=True), done,
                        lambda e: self.ai_pill.set("AI: cevrimdisi", "warn"))

    # -- yardimcilar -------------------------------------------------------
    def t(self, key: str) -> str:
        """Secili arayuz diline gore metin."""
        return i18n.t(key, self.settings.get("ui_lang", "tr"))

    def u(self, text: str) -> str:
        """Eski, dogrudan yazilmis arayuz metnini secili dile cevir."""
        return i18n.ui(text, self.ui_lang())

    def ui_lang(self) -> str:
        """Aktif arayuz dili kodu."""
        return self.settings.get("ui_lang", "tr")

    def _on_language_change(self, _evt=None) -> None:
        """Ust cubuktaki dil secimini kaydet ve aninda uygula."""
        selected = self.language_var.get()
        code = next((key for key, name in i18n.LANG_NAMES.items()
                     if name == selected), "tr")
        self.set_ui_language(code)

    def set_ui_language(self, code: str) -> None:
        """Arayuz dilini guvenli bicimde degistir ve secimi kalici yap."""
        if code not in i18n.LANGS:
            code = "tr"
        self.settings["ui_lang"] = code
        C.save_settings(self.settings)
        if getattr(self, "language_var", None) is not None:
            self.language_var.set(i18n.LANG_NAMES[code])
        self.relabel_tabs()

    def localize_widgets(self, root) -> None:
        """Kurulmus eski sayfalardaki sabit metinleri yerinde cevir.

        Kaynak metin widget uzerinde saklandigi icin English -> Русский gibi
        ard arda gecislerde de Turkce kaynak kaybolmaz.
        """
        lang = self.ui_lang()

        def translate_option(widget) -> None:
            if isinstance(widget, ttk.Combobox):
                return  # seceneklerin is kodlariyla eslesmesini bozma
            try:
                current = str(widget.cget("text"))
            except (tk.TclError, TypeError):
                return
            if not current:
                return
            last = getattr(widget, "_i18n_last_text", None)
            source = getattr(widget, "_i18n_source_text", current)
            if last is not None and current != last:
                source = current
            translated = i18n.ui(source, lang)
            if translated != current:
                try:
                    widget.configure(text=translated)
                except tk.TclError:
                    return
            widget._i18n_source_text = source
            widget._i18n_last_text = translated

        def walk(widget) -> None:
            translate_option(widget)

            if isinstance(widget, ttk.Treeview):
                sources = getattr(widget, "_i18n_heading_sources", {})
                for col in ("#0", *tuple(widget["columns"])):
                    try:
                        current = str(widget.heading(col, "text"))
                    except tk.TclError:
                        continue
                    source = sources.get(col, current)
                    sources[col] = source
                    widget.heading(col, text=i18n.ui(source, lang))
                widget._i18n_heading_sources = sources

            if isinstance(widget, ttk.Notebook):
                sources = getattr(widget, "_i18n_tab_sources", {})
                for child in widget.tabs():
                    current = str(widget.tab(child, "text"))
                    source = sources.get(child, current)
                    sources[child] = source
                    widget.tab(child, text=i18n.ui(source, lang))
                widget._i18n_tab_sources = sources

            if isinstance(widget, tk.Canvas):
                sources = getattr(widget, "_i18n_canvas_sources", {})
                for item in widget.find_all():
                    try:
                        current = widget.itemcget(item, "text")
                    except tk.TclError:
                        continue
                    if not current:
                        continue
                    source = sources.get(item, current)
                    sources[item] = source
                    widget.itemconfigure(item, text=i18n.ui(source, lang))
                widget._i18n_canvas_sources = sources

            for child in widget.winfo_children():
                walk(child)

        try:
            walk(root)
        except tk.TclError:
            pass

    def set_status(self, text: str) -> None:
        """Durum cubugu metnini degistir."""
        self.status.set(text)

    def speak(self, text: str) -> None:
        """Metni seslendir (ses kapaliysa veya motor yoksa sessizce gec)."""
        if self.speaker and self.settings.get("tts_enabled", True):
            self.speaker.say(text)

    def can_speak(self) -> bool:
        """Seslendirme kullanilabilir mi?"""
        return bool(self.speaker and self.speaker.available())

    def retheme(self) -> None:
        """Tema degisti - yeniden baslatma onerilir."""
        self.palette = apply_theme(self, self.style, self.settings["theme"])
        self._refresh_current()

    def relabel_tabs(self) -> None:
        """Arayuz dili degistiginde kurulmus arayuzu aninda guncelle."""
        for key, _m, _c, _i, _g in TAB_SPECS:
            self.sidebar.set_label(key, self.t(key))
        for group in GROUP_ORDER:
            self.sidebar.set_group_label(group, self.t(group))
        self.profile_label.configure(text=self.t("g.profile"))
        if self._current_key:
            self.page_title.configure(text=self.t(self._current_key))
            self.page_hint.configure(text=self.u(PAGE_HINTS.get(self._current_key, "")))
        for page in self._tabs.values():
            if not getattr(page, "_built", False):
                continue
            try:
                page.on_language_change()
            except Exception:
                pass
            self.localize_widgets(page)
        self.status.set(self.t("g.ready"))
        self.check_ai()

    def on_close(self) -> None:
        """Kapanis: ayarlari yaz, ses ve veritabanini kapat."""
        for step in (lambda: C.save_settings(self.settings),
                     lambda: self.speaker and self.speaker.stop(),
                     lambda: self.db and self.db.close()):
            try:
                step()
            except Exception:
                pass
        self.destroy()


PAGE_HINTS = {
    "tab.srs": "Space cevir · 1/2/3 degerlendir",
    "tab.vocab": "Cift tikla = dinle",
    "tab.exam": "Enter = kontrol et",
    "tab.pdf": "Metin sec araciyla parca secip AI'a sorun",
    "tab.ai": "Ctrl+Enter = gonder",
    "tab.library": "Yalnizca acik lisansli kaynaklar",
    "tab.resources": "Space = bitirdim isareti",
}


def main() -> int:
    """Uygulamayi baslat."""
    try:
        app = App()
    except SystemExit as e:
        return int(e.code or 1)
    except Exception:
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(C.APP_NAME,
                                 "Program baslatilamadi:\n\n" + traceback.format_exc())
            root.destroy()
        except Exception:
            traceback.print_exc()
        return 1
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
