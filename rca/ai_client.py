# -*- coding: utf-8 -*-
"""LM Studio (OpenAI uyumlu) istemcisi.

- Yalnizca stdlib kullanir (urllib) - harici bagimlilik yok.
- Model bulunamazsa ozellik COKMEZ; profil kurulu modellere karsi cozumlenir.
- Istek metinleri hicbir yerde saklanmaz; yalnizca token sayaclari defterlenir.
- Aginternet cagrisi sadece kullanici NIM'i acikca acarsa yapilir.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, Optional

import rca_common as C
from rca.i18n import SYSTEM_PROMPTS

TIMEOUT_LIST = 3.0
TIMEOUT_CHAT = 180.0


class AIError(Exception):
    """AI katmanindaki beklenen hatalar (baglanti yok, model yok...)."""


class AIClient:
    """LM Studio yerel ucuna konusan ince istemci."""

    def __init__(self, base: str = None, token_logger: Callable = None) -> None:
        self.base = (base or C.LMSTUDIO_BASE).rstrip("/")
        self._models: List[str] = []
        self._checked_at = 0.0
        self._online = False
        self.token_logger = token_logger      # (model, task, ptok, ctok, ms, ok) -> None
        self.api_key = "lm-studio"            # yerel uc anahtar istemez

    # -- kesif -------------------------------------------------------------
    def models(self, force: bool = False) -> List[str]:
        """Kurulu model kimliklerini dondur; ulasilamazsa bos liste."""
        if not force and self._models and (time.time() - self._checked_at) < 30:
            return self._models
        self._checked_at = time.time()
        try:
            req = urllib.request.Request(f"{self.base}/v1/models",
                                         headers={"Authorization": f"Bearer {self.api_key}"})
            with urllib.request.urlopen(req, timeout=TIMEOUT_LIST) as r:
                data = json.loads(r.read().decode("utf-8"))
            self._models = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
            self._online = True
        except Exception:
            self._models = []
            self._online = False
        return self._models

    def is_online(self) -> bool:
        """Yerel uc erisilebilir mi?"""
        self.models()
        return self._online

    def resolve(self, task: str) -> Optional[str]:
        """Gorev icin en uygun kurulu modeli sec.

        Once profil listesindeki tercih sirasi, sonra ad benzerligi, en son
        kurulu ilk model denenir. Hicbiri yoksa None.
        """
        installed = self.models()
        if not installed:
            return None
        prefs = C.MODEL_PROFILES.get(task, C.MODEL_PROFILES["chat"])
        low = {m.lower(): m for m in installed}
        for p in prefs:
            if p.lower() in low:
                return low[p.lower()]
        for p in prefs:
            for m in installed:
                if p.split("-")[0].lower() in m.lower():
                    return m
        if task == "vision":
            for m in installed:
                if any(k in m.lower() for k in ("vl", "vision", "llava")):
                    return m
            return None                      # gorsel modeli yoksa zorlamayiz
        return installed[0]

    # -- sohbet ------------------------------------------------------------
    def chat(self, messages: List[Dict[str, str]], task: str = "chat",
             temperature: float = 0.3, max_tokens: int = 800,
             model: str = None) -> str:
        """Sohbet tamamlama iste ve yalnizca metni dondur.

        Baglanti yoksa veya model bulunamazsa AIError firlatir - cagiran taraf
        bunu kullaniciya sakin bir mesajla gosterir.
        """
        mdl = model or self.resolve(task)
        if not mdl:
            raise AIError("model-yok")
        payload = {
            "model": mdl,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base}/v1/chat/completions", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.api_key}"})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_CHAT) as r:
                data = json.loads(r.read().decode("utf-8"))
        except urllib.error.URLError as e:
            self._log(mdl, task, 0, 0, int((time.time() - t0) * 1000), False)
            raise AIError(f"baglanti: {e}") from e
        except Exception as e:
            self._log(mdl, task, 0, 0, int((time.time() - t0) * 1000), False)
            raise AIError(str(e)) from e

        ms = int((time.time() - t0) * 1000)
        usage = data.get("usage") or {}
        self._log(mdl, task, int(usage.get("prompt_tokens", 0)),
                  int(usage.get("completion_tokens", 0)), ms, True)
        try:
            return (data["choices"][0]["message"]["content"] or "").strip()
        except Exception:
            return ""

    def _log(self, model: str, task: str, ptok: int, ctok: int, ms: int, ok: bool) -> None:
        """Token defterine yaz (istek metni yazilmaz)."""
        if self.token_logger:
            try:
                self.token_logger(model, task, ptok, ctok, ms, ok)
            except Exception:
                pass

    # -- yuksek seviye gorevler -------------------------------------------
    def explain(self, text: str, ui_lang: str = "tr", context: str = "") -> str:
        """Secili Rusca metni acikla (dilbilgisi + ceviri)."""
        sysmsg = SYSTEM_PROMPTS.get(ui_lang, SYSTEM_PROMPTS["tr"])
        user = f"Su Rusca parcayi acikla:\n\n{text}"
        if context:
            user += f"\n\nBaglam:\n{context}"
        user += ("\n\nSirasiyla ver: 1) ceviri 2) kelime kelime cozumleme "
                 "3) gecen dilbilgisi kurallarinin adi 4) benzer bir ornek cumle.")
        return self.chat([{"role": "system", "content": sysmsg},
                          {"role": "user", "content": user}], task="grammar")

    def translate(self, text: str, direction: str = "ru2tr", ui_lang: str = "tr") -> str:
        """Metni cevir. direction: ru2tr | tr2ru"""
        target = "Turkce" if direction == "ru2tr" else "Rusca"
        sysmsg = SYSTEM_PROMPTS.get(ui_lang, SYSTEM_PROMPTS["tr"])
        user = (f"Asagidaki metni {target} diline cevir. Yalnizca ceviriyi ver, "
                f"aciklama ekleme.\n\n{text}")
        return self.chat([{"role": "system", "content": sysmsg},
                          {"role": "user", "content": user}],
                         task="translate", temperature=0.1)

    def correct(self, sentence: str, ui_lang: str = "tr") -> str:
        """Yazi duzeltici: hatayi isaretle, kurali adlandir, dogrusunu ver."""
        sysmsg = SYSTEM_PROMPTS.get(ui_lang, SYSTEM_PROMPTS["tr"])
        user = (
            "Ogrencinin yazdigi Rusca cumle asagida. Su bicimde yanit ver:\n"
            "HATA: (yanlis parca)\n"
            "KURAL: (ihlal edilen kuralin adi, orn. 'винительный падеж')\n"
            "DOGRU: (duzeltilmis cumle, vurgu isaretli)\n"
            "NEDEN: (bir cumlelik aciklama)\n"
            "Hata yoksa sadece 'DOGRU: <cumle>' yaz.\n\n"
            f"Cumle: {sentence}")
        return self.chat([{"role": "system", "content": sysmsg},
                          {"role": "user", "content": user}],
                         task="correct", temperature=0.1)

    def roleplay(self, scenario: str, level: str, history: List[Dict[str, str]],
                 ui_lang: str = "tr") -> str:
        """Rol yapma diyalogu - CEFR seviyesine gore kelime sinirlamasi."""
        sysmsg = (
            f"{SYSTEM_PROMPTS.get(ui_lang, SYSTEM_PROMPTS['tr'])}\n"
            f"Simdi bir rol yapma alistirmasi yonetiyorsun. Senaryo: {scenario}. "
            f"Ogrencinin seviyesi {level}. YALNIZCA {level} seviyesine uygun kelime ve "
            f"yapi kullan. Kisa cumleler kur (en fazla 2 cumle), her yanitin sonunda "
            f"ogrenciye bir soru sor. Rusca konus.")
        msgs = [{"role": "system", "content": sysmsg}] + history
        return self.chat(msgs, task="dialogue", temperature=0.7, max_tokens=300)

    def session_report(self, history: List[Dict[str, str]], ui_lang: str = "tr") -> str:
        """Konusma oturumu sonu raporu: hata dokumu + 5 kelime."""
        sysmsg = SYSTEM_PROMPTS.get(ui_lang, SYSTEM_PROMPTS["tr"])
        convo = "\n".join(f"{m['role']}: {m['content']}" for m in history)
        user = ("Asagidaki diyalogda ogrencinin yaptigi hatalari listele "
                "(hata -> kural -> dogrusu). Sonra ogrenmesi gereken 5 kelimeyi "
                "'RU - TR' bicimde ver.\n\n" + convo)
        return self.chat([{"role": "system", "content": sysmsg},
                          {"role": "user", "content": user}], task="grammar")

    def describe_image(self, image_b64: str, prompt: str, ui_lang: str = "tr") -> str:
        """Gorsel/OCR gorevi - vision profili yoksa AIError."""
        mdl = self.resolve("vision")
        if not mdl:
            raise AIError("vision-model-yok")
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
        ]
        return self.chat([{"role": "system", "content": SYSTEM_PROMPTS.get(ui_lang, SYSTEM_PROMPTS["tr"])},
                          {"role": "user", "content": content}],
                         task="vision", model=mdl)


def approx_tokens(text: str) -> int:
    """Kaba token tahmini (usage bilgisi gelmezse defter icin)."""
    return max(1, len(text or "") // 3)
