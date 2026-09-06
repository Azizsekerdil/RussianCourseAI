# -*- coding: utf-8 -*-
"""Ayarlar: arayuz dili, tema, hedef, ses, AI adresi, profiller, veri yonetimi."""
from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk

import rca_common as C
import rca.secrets as secrets
from rca.i18n import LANG_NAMES, LANGS
from rca.tabs.dictionary_tab import POLICY_KEYS, policy_code
from rca.ui_util import LazyTab, ScrollFrame


class SettingsTab(LazyTab):
    """Tum yapilandirma tek ekranda."""

    def build(self) -> None:
        p = self.palette()
        sf = ScrollFrame(self)
        sf.paint(p)
        sf.pack(fill="both", expand=True)
        b = ttk.Frame(sf.body, padding=14)
        b.pack(fill="both", expand=True)

        s = self.app.settings

        # --- arayuz -------------------------------------------------------
        g1 = ttk.LabelFrame(b, text="Arayuz", padding=12)
        g1.pack(fill="x")

        ttk.Label(g1, text="Dil:").grid(row=0, column=0, sticky="w", pady=4)
        self.lang = tk.StringVar(value=LANG_NAMES.get(s.get("ui_lang", "tr"), "Türkçe"))
        ttk.Combobox(g1, textvariable=self.lang, state="readonly", width=14,
                     values=[LANG_NAMES[l] for l in LANGS]).grid(row=0, column=1,
                                                                 sticky="w", padx=8)
        ttk.Label(g1, text="(sekme adlari ve AI sistem yonergesi bu dile gore degisir)",
                  style="Dim.TLabel").grid(row=0, column=2, sticky="w")

        ttk.Label(g1, text="Tema:").grid(row=1, column=0, sticky="w", pady=4)
        self.theme = tk.StringVar(value=s.get("theme", "dark"))
        ttk.Combobox(g1, textvariable=self.theme, state="readonly", width=14,
                     values=["dark", "light"]).grid(row=1, column=1, sticky="w", padx=8)

        ttk.Label(g1, text="Gunluk hedef:").grid(row=2, column=0, sticky="w", pady=4)
        self.goal = tk.IntVar(value=int(s.get("daily_goal", 20)))
        ttk.Spinbox(g1, from_=5, to=200, increment=5, width=8,
                    textvariable=self.goal).grid(row=2, column=1, sticky="w", padx=8)
        ttk.Label(g1, text="kelime / gun", style="Dim.TLabel").grid(row=2, column=2,
                                                                    sticky="w")

        ttk.Label(g1, text="CEFR seviyesi:").grid(row=3, column=0, sticky="w", pady=4)
        self.cefr = tk.StringVar(value=s.get("cefr", "A1"))
        ttk.Combobox(g1, textvariable=self.cefr, state="readonly", width=8,
                     values=C.CEFR_LEVELS).grid(row=3, column=1, sticky="w", padx=8)

        # --- ses ----------------------------------------------------------
        g2 = ttk.LabelFrame(b, text="Ses", padding=12)
        g2.pack(fill="x", pady=12)
        self.tts_on = tk.BooleanVar(value=bool(s.get("tts_enabled", True)))
        ttk.Checkbutton(g2, text="Seslendirme acik", variable=self.tts_on).grid(
            row=0, column=0, sticky="w")
        ttk.Label(g2, text="Hiz:").grid(row=1, column=0, sticky="w", pady=6)
        self.rate = tk.IntVar(value=int(s.get("tts_rate", 150)))
        ttk.Scale(g2, from_=80, to=260, variable=self.rate, orient="horizontal",
                  length=220).grid(row=1, column=1, sticky="w", padx=8)
        self.rate_lbl = ttk.Label(g2, text=str(self.rate.get()), style="Dim.TLabel")
        self.rate_lbl.grid(row=1, column=2, sticky="w")
        self.rate.trace_add("write", lambda *_a: self.rate_lbl.configure(
            text=str(int(self.rate.get()))))
        status = (self.app.speaker.status_text() if self.app.speaker
                  else "Ses motoru yuklenemedi.")
        ttk.Label(g2, text=status, style="Dim.TLabel", wraplength=700,
                  justify="left").grid(row=2, column=0, columnspan=3, sticky="w", pady=6)
        ttk.Button(g2, text="Test et", command=self.test_voice).grid(
            row=3, column=0, sticky="w")

        # --- yapay zeka ---------------------------------------------------
        g3 = ttk.LabelFrame(b, text="Yapay zeka (yerel)", padding=12)
        g3.pack(fill="x")
        self.ai_on = tk.BooleanVar(value=bool(s.get("ai_enabled", True)))
        ttk.Checkbutton(g3, text="AI ozellikleri acik", variable=self.ai_on).grid(
            row=0, column=0, sticky="w")
        ttk.Label(g3, text="LM Studio adresi:").grid(row=1, column=0, sticky="w", pady=6)
        self.ai_base = tk.StringVar(value=s.get("ai_base", C.LMSTUDIO_BASE))
        ttk.Entry(g3, textvariable=self.ai_base, width=36).grid(row=1, column=1,
                                                                sticky="w", padx=8)
        ttk.Button(g3, text="Baglantiyi dene", command=self.test_ai).grid(
            row=1, column=2, sticky="w")
        self.ai_status = ttk.Label(g3, text="", style="Dim.TLabel", wraplength=700,
                                   justify="left")
        self.ai_status.grid(row=2, column=0, columnspan=3, sticky="w", pady=6)

        ttk.Label(g3, text="Varsayilan model:").grid(row=3, column=0, sticky="w")
        self.ai_model = tk.StringVar(value=s.get("ai_model", C.DEFAULT_MODEL))
        self.model_box = ttk.Combobox(g3, textvariable=self.ai_model, width=36,
                                      values=[C.DEFAULT_MODEL])
        self.model_box.grid(row=3, column=1, sticky="w", padx=8)

        # --- alternatif uc (OpenAI uyumlu uzak servis: NIM / OpenRouter / Groq...) ---
        g3b = ttk.LabelFrame(b, text=self.t("set.alt_group"), padding=12)
        g3b.pack(fill="x", pady=(12, 0))
        self.alt_on = tk.BooleanVar(value=bool(s.get("alt_enabled", False)))
        ttk.Checkbutton(g3b, text=self.t("set.alt_enabled"), variable=self.alt_on).grid(
            row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(g3b, text=self.t("set.alt_base")).grid(row=1, column=0, sticky="w", pady=6)
        self.alt_base = tk.StringVar(value=s.get("alt_base", C.NIM_BASE) or C.NIM_BASE)
        ttk.Entry(g3b, textvariable=self.alt_base, width=44).grid(row=1, column=1,
                                                                  sticky="w", padx=8)
        ttk.Label(g3b, text=self.t("set.alt_base_hint"), style="Dim.TLabel", wraplength=380,
                  justify="left").grid(row=1, column=2, sticky="w")
        ttk.Label(g3b, text=self.t("set.alt_model")).grid(row=2, column=0, sticky="w")
        self.alt_model = tk.StringVar(value=s.get("alt_model", C.ALT_DEFAULT_MODEL))
        ttk.Entry(g3b, textvariable=self.alt_model, width=44).grid(row=2, column=1,
                                                                   sticky="w", padx=8)
        ttk.Label(g3b, text=self.t("set.alt_key")).grid(row=3, column=0, sticky="w", pady=6)
        # Alan gercek anahtarla ASLA doldurulmaz; yalnizca yeni anahtar yazmak icin kullanilir.
        self.alt_key = tk.StringVar(value="")
        ttk.Entry(g3b, textvariable=self.alt_key, width=44, show="•").grid(
            row=3, column=1, sticky="w", padx=8)
        self.alt_key_state = ttk.Label(g3b, text="", style="Dim.TLabel", wraplength=380,
                                       justify="left")
        self.alt_key_state.grid(row=3, column=2, sticky="w")
        arow = ttk.Frame(g3b)
        arow.grid(row=4, column=0, columnspan=3, sticky="w", pady=(2, 0))
        ttk.Button(arow, text=self.t("set.alt_test"), command=self.test_alt).pack(side="left")
        ttk.Button(arow, text=self.t("set.alt_delete_key"), style="Err.TButton",
                   command=self.delete_alt_key).pack(side="left", padx=6)
        self.alt_status = ttk.Label(g3b, text="", style="Dim.TLabel", wraplength=700,
                                    justify="left")
        self.alt_status.grid(row=5, column=0, columnspan=3, sticky="w", pady=6)
        ttk.Label(g3b, style="Warn.TLabel", wraplength=700, justify="left",
                  text=self.t("set.alt_note")).grid(row=6, column=0, columnspan=3, sticky="w")

        ttk.Label(g3b, text=self.t("set.dict_ai")).grid(row=7, column=0, sticky="w", pady=(10, 0))
        self.dict_ai = tk.StringVar(value=self._policy_label(s.get("dict_ai", "auto")))
        self.dict_ai_box = ttk.Combobox(g3b, textvariable=self.dict_ai, state="readonly",
                                        width=26, values=[self.t(k) for k in POLICY_KEYS.values()])
        self.dict_ai_box.grid(row=7, column=1, sticky="w", padx=8, pady=(10, 0))
        self.dict_autosave = tk.BooleanVar(value=bool(s.get("dict_ai_autosave", True)))
        ttk.Checkbutton(g3b, text=self.t("d.ai_autosave"), variable=self.dict_autosave).grid(
            row=8, column=0, columnspan=3, sticky="w", pady=(4, 0))
        self._refresh_key_state()

        # --- profiller ----------------------------------------------------
        g4 = ttk.LabelFrame(b, text="Profiller", padding=12)
        g4.pack(fill="x", pady=12)
        self.prof_list = ttk.Treeview(g4, columns=("cefr", "created"), show="headings",
                                      height=5)
        self.prof_list.heading("cefr", text="Seviye")
        self.prof_list.heading("created", text="Olusturma")
        self.prof_list.column("cefr", width=90)
        self.prof_list.column("created", width=180)
        self.prof_list.grid(row=0, column=0, columnspan=3, sticky="ew", pady=4)
        ttk.Button(g4, text="Yeni profil", command=self.new_profile).grid(
            row=1, column=0, sticky="w")
        ttk.Button(g4, text="Secili profili sil", style="Err.TButton",
                   command=self.del_profile).grid(row=1, column=1, sticky="w", padx=6)

        # --- veri ---------------------------------------------------------
        g5 = ttk.LabelFrame(b, text="Veri", padding=12)
        g5.pack(fill="x")
        ttk.Label(g5, text=str(C.APP_HOME), style="Dim.TLabel").pack(anchor="w")
        row = ttk.Frame(g5)
        row.pack(anchor="w", pady=6)
        ttk.Button(row, text="Veri klasorunu ac", command=self.open_data).pack(side="left")
        ttk.Button(row, text="Ilerlemeyi sifirla (bu profil)", style="Err.TButton",
                   command=self.reset_progress).pack(side="left", padx=6)
        ttk.Button(row, text="Eksik seed kelimeleri geri yukle",
                   command=self.reseed).pack(side="left")

        try:
            from rca.library import ssl_source
            source = ssl_source()
        except Exception:
            source = "bilinmiyor"
        note = (f"Kaynak Merkezi indirmelerinde kullanilan sertifika deposu: {source}.")
        if source == "varsayilan":
            note += ("\nPython'un gomulu deposu bazi kurulumlarda eskimistir ve gecerli "
                     "siteler 'certificate has expired' hatasi verebilir. Sorun yasarsaniz: "
                     "pip install truststore certifi")
        ttk.Label(g5, text=note, style="Dim.TLabel", wraplength=760,
                  justify="left").pack(anchor="w", pady=(6, 0))
        ttk.Label(g5, style="Dim.TLabel", wraplength=760, justify="left",
                  text="Sertifika dogrulamasi hicbir kosulda kapatilmaz.").pack(anchor="w")

        # --- kaydet -------------------------------------------------------
        bar = ttk.Frame(b)
        bar.pack(fill="x", pady=16)
        ttk.Button(bar, text=self.t("g.save"), style="Accent.TButton",
                   command=self.save).pack(side="left")
        self.saved = ttk.Label(bar, text="", style="OK.TLabel")
        self.saved.pack(side="left", padx=12)

        self.refresh_profiles()
        self.test_ai(silent=True)

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        """Profil listesini tazele."""
        if getattr(self, "prof_list", None) is not None:
            self.refresh_profiles()

    def on_language_change(self) -> None:
        """Dil degisti (ust cubuk ya da Kaydet): dil kutusu ve politika etiketleri yeni dile gecer.

        Kaydedilmemis politika secimi korunur: etiket once koda cevrilir, sonra yeni
        dilde yeniden yazilir. Dil kutusu da esitlenir ki sonraki bir Kaydet eski
        dili geri getirmesin.
        """
        if getattr(self, "dict_ai_box", None) is None:
            return
        self.lang.set(LANG_NAMES.get(self.app.ui_lang(), LANG_NAMES["tr"]))
        pending = self._policy_code(self.dict_ai.get())
        self.dict_ai_box["values"] = [self.t(k) for k in POLICY_KEYS.values()]
        self.dict_ai.set(self._policy_label(pending))

    def refresh_profiles(self) -> None:
        """Profil tablosunu doldur."""
        self.prof_list.delete(*self.prof_list.get_children())
        for prof in self.repos.profiles.all():
            self.prof_list.insert("", "end", iid=str(prof["id"]),
                                  text=prof["name"],
                                  values=(prof["cefr"],
                                          str(prof["created_at"])[:16].replace("T", " ")))
        # Treeview show=headings oldugu icin adi ilk sutunda gostermek adina:
        self.prof_list.configure(show="tree headings")
        self.prof_list.heading("#0", text="Profil")
        self.prof_list.column("#0", width=200)

    def new_profile(self) -> None:
        """Yeni profil olustur."""
        self.app.new_profile()
        self.refresh_profiles()

    def del_profile(self) -> None:
        """Secili profili sil (son profil silinemez)."""
        sel = self.prof_list.selection()
        if not sel:
            return
        pid = int(sel[0])
        if len(self.repos.profiles.all()) <= 1:
            messagebox.showinfo(C.APP_NAME, "Son profil silinemez.")
            return
        name = self.prof_list.item(sel[0], "text")
        if not messagebox.askyesno(C.APP_NAME,
                                   f"'{name}' profili ve tum ilerlemesi silinsin mi?"):
            return
        self.repos.profiles.delete(pid)
        if pid == self.pid:
            self.app.profile_id = self.repos.profiles.ensure_default()
        self.app.refresh_profiles()
        self.refresh_profiles()

    # ------------------------------------------------------------------
    def test_voice(self) -> None:
        """Ses motorunu dene."""
        if not self.app.speaker or not self.app.speaker.available():
            messagebox.showinfo(C.APP_NAME, "Ses motoru bulunamadi.\n\n"
                                            "Kurmak icin: pip install pyttsx3\n"
                                            "Windows ayarlarindan Rusca ses paketi ekleyin.")
            return
        self.app.speaker.set_rate(int(self.rate.get()))
        self.app.speaker.say("Здравствуйте! Это тест русского голоса.")

    def test_ai(self, silent: bool = False) -> None:
        """LM Studio baglantisini dene."""
        base = self.ai_base.get().strip()
        self.app.ai.base = base.rstrip("/")
        self.ai_status.configure(text="Kontrol ediliyor...",
                                 foreground=self.palette()["fg_dim"])

        def job():
            return self.app.ai.models(force=True)

        def done(models):
            p = self.palette()
            if models:
                self.model_box["values"] = models
                self.ai_status.configure(
                    text=f"Baglandi · {len(models)} model: " + ", ".join(models[:4]) +
                         ("..." if len(models) > 4 else ""), foreground=p["ok"])
            else:
                self.ai_status.configure(
                    text="Baglanti yok. LM Studio'yu acip Local Server'i baslatin. "
                         "Program bu olmadan da tam calisir; yalnizca AI kapali kalir.",
                    foreground=p["warn"])
        self.app.worker.run(job, done, lambda e: self.ai_status.configure(
            text=f"Hata: {e}", foreground=self.palette()["err"]))

    # -- alternatif uc ---------------------------------------------------
    def _policy_label(self, code: str) -> str:
        return self.t(POLICY_KEYS.get(code, "d.policy_auto"))

    def _policy_code(self, label: str) -> str:
        return policy_code(label)                      # etiketin dili onemsiz

    def _refresh_key_state(self) -> None:
        """Gercek anahtar gosterilmez; yalnizca kayitli olup olmadigi soylenir."""
        has = secrets.has_secret(secrets.KEY_ALT_API)
        self.alt_key_state.configure(
            text=self.t("set.alt_key_saved") if has else self.t("set.alt_key_none"))

    def test_alt(self) -> None:
        """Alternatif ucun /v1/models listesini arka planda dene ve sonucu yaz."""
        from rca.ai_client import AIClient
        base = self.alt_base.get().strip() or C.NIM_BASE
        key = self.alt_key.get().strip() or secrets.get_secret(secrets.KEY_ALT_API)
        client = AIClient(base, api_key=key, model=self.alt_model.get().strip())
        self.alt_status.configure(text=self.t("set.alt_checking"),
                                  foreground=self.palette()["fg_dim"])

        def job():
            return client.models(force=True), client.last_error

        def done(result):
            models, err = result
            p = self.palette()
            if models:
                self.alt_status.configure(
                    text=f"{self.t('set.alt_ok')} · {len(models)} {self.t('set.models')}: "
                         + ", ".join(models[:4]) + ("..." if len(models) > 4 else ""),
                    foreground=p["ok"])
            else:
                self.alt_status.configure(text=f"{self.t('set.alt_fail')}: {err or base}",
                                          foreground=p["warn"])
        self.app.worker.run(job, done, lambda e: self.alt_status.configure(
            text=f"{self.t('set.alt_fail')}: {e}", foreground=self.palette()["err"]))

    def delete_alt_key(self) -> None:
        """Kayitli anahtari gizli depodan sil."""
        secrets.delete_secret(secrets.KEY_ALT_API)
        self.alt_key.set("")
        self.app.refresh_ai_clients()
        self._refresh_key_state()
        self.alt_status.configure(text=self.t("set.alt_key_deleted"),
                                  foreground=self.palette()["fg_dim"])

    def open_data(self) -> None:
        """Veri klasorunu ac."""
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(C.APP_HOME))          # noqa: S606
            else:
                subprocess.Popen(["xdg-open", str(C.APP_HOME)])
        except Exception as e:                          # noqa: BLE001
            messagebox.showerror(C.APP_NAME, str(e))

    def reset_progress(self) -> None:
        """Bu profilin tum ilerlemesini sil (kelimeler kalir)."""
        if not messagebox.askyesno(
                C.APP_NAME, "Bu profildeki tum tekrar, sinav ve konu ilerlemesi silinecek.\n"
                            "Kelime bankasi silinmez. Devam edilsin mi?"):
            return
        for table in ("word_progress", "topic_progress", "study_log"):
            self.repos.db.execute(f"DELETE FROM {table} WHERE profile_id=?", (self.pid,))
        self.repos.db.execute("DELETE FROM exam_answers WHERE exam_id IN "
                              "(SELECT id FROM exams WHERE profile_id=?)", (self.pid,))
        self.repos.db.execute("DELETE FROM exams WHERE profile_id=?", (self.pid,))
        self.app.set_status("Ilerleme sifirlandi")

    def reseed(self) -> None:
        """Silinmis seed kelimeleri geri yukle."""
        from rca.seed_words import A1_WORDS
        added = 0
        for (ru, tr, en, stress, pos, freq, deck, ex_ru, ex_tr) in A1_WORDS:
            row = self.repos.db.one("SELECT id FROM words WHERE ru_norm=?",
                                    (C.normalize_ru(ru),))
            if row:
                continue
            self.repos.words.add(ru, tr, en, stress, pos, deck, ex_ru, ex_tr, freq)
            added += 1
        messagebox.showinfo(C.APP_NAME, f"{added} kelime geri yuklendi.")

    # ------------------------------------------------------------------
    def save(self) -> None:
        """Ayarlari yaz ve gerekli yerlere uygula."""
        s = self.app.settings
        code = next((l for l in LANGS if LANG_NAMES[l] == self.lang.get()), "tr")
        lang_changed = code != s.get("ui_lang")
        theme_changed = self.theme.get() != s.get("theme")
        # politika etiketi ui_lang degismeden ONCE koda cevrilir (etiket eski dilde yazili)
        policy = self._policy_code(self.dict_ai.get())

        s["ui_lang"] = code
        s["theme"] = self.theme.get()
        s["daily_goal"] = int(self.goal.get())
        s["cefr"] = self.cefr.get()
        s["tts_enabled"] = bool(self.tts_on.get())
        s["tts_rate"] = int(self.rate.get())
        s["ai_enabled"] = bool(self.ai_on.get())
        s["ai_base"] = self.ai_base.get().strip()
        s["ai_model"] = self.ai_model.get().strip()
        s["alt_enabled"] = bool(self.alt_on.get())
        s["nim_enabled"] = s["alt_enabled"]              # eski surumler icin ayni bayrak
        s["alt_base"] = self.alt_base.get().strip() or C.NIM_BASE
        s["alt_model"] = self.alt_model.get().strip()
        s["dict_ai"] = policy
        s["dict_ai_autosave"] = bool(self.dict_autosave.get())
        # Anahtar yalnizca alan doluysa ve YALNIZCA gizli depoya yazilir (settings.json'a asla).
        key_msg = ""
        key = self.alt_key.get().strip()
        if key:
            secrets.set_secret(secrets.KEY_ALT_API, key)
            self.alt_key.set("")
            key_msg = "  " + self.t("set.alt_key_stored")
        C.save_settings(s)

        if self.app.speaker:
            self.app.speaker.set_rate(int(self.rate.get()))
        self.app.refresh_ai_clients()
        self._refresh_key_state()
        self.repos.profiles.set_cefr(self.pid, s["cefr"])

        if lang_changed:
            self.app.set_ui_language(code)
        if theme_changed:
            self.app.retheme()
        self.app.check_ai()

        msg = self.u("Kaydedildi.") + key_msg
        if theme_changed:
            restart = {
                "tr": "  Temanin tam uygulanmasi icin programi yeniden baslatin.",
                "en": "  Restart the app to apply the theme everywhere.",
                "ru": "  Перезапустите программу, чтобы применить тему везде.",
            }
            msg += restart.get(self.app.ui_lang(), restart["tr"])
        self.saved.configure(text=msg)
        self.after(6000, lambda: self.saved.configure(text=""))
        self.app.set_status(msg)
