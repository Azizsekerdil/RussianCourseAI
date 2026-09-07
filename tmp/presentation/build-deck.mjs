import fs from "node:fs/promises";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const OUT = "D:/Russian/docs/presentation/Russian-Course-AI-Trilingual.pptx";
const PREVIEW_DIR = "D:/Russian/tmp/presentation/rendered";
const HERO = "D:/Russian/docs/presentation/assets/russian-course-ai-hero.png";
const SCREENSHOT = "D:/Russian/docs/presentation/assets/russian-course-ai-screenshot.png";

const C = {
  white: "#FFFFFF",
  ink: "#10131A",
  muted: "#5F6675",
  faint: "#EDEFF3",
  rule: "#B8BCC4",
  blue: "#3D8DFF",
  paleBlue: "#EAF5FB",
  navy: "#0F1522",
};

function text(slide, name, value, x, y, w, h, size, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = value;
  shape.text.style = {
    fontSize: size,
    bold: options.bold ?? false,
    color: options.color ?? C.ink,
    alignment: options.align ?? "left",
    verticalAlignment: options.valign ?? "top",
    typeface: "Arial",
  };
  return shape;
}

function line(slide, name, x, y, w, color = C.rule, weight = 1) {
  return slide.shapes.add({
    geometry: "line",
    name,
    position: { left: x, top: y, width: w, height: 0 },
    fill: "none",
    line: { style: "solid", fill: color, width: weight },
  });
}

function rect(slide, name, x, y, w, h, fill, radius = 0) {
  return slide.shapes.add({
    geometry: radius ? "roundRect" : "rect",
    name,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: "none", width: 0 },
    ...(radius ? { borderRadius: radius } : {}),
  });
}

function footer(slide, number) {
  text(slide, `footer-${number}`, String(number).padStart(2, "0"), 1180, 668, 56, 20, 13, {
    color: C.muted,
    align: "right",
  });
}

function notes(slide, sources) {
  slide.speakerNotes.textFrame.setText(
    `[Sources]\n${sources.map((source) => `- ${source}`).join("\n")}`,
  );
}

async function writeBlob(path, blob) {
  await fs.writeFile(path, new Uint8Array(await blob.arrayBuffer()));
}

async function main() {
  await fs.mkdir(PREVIEW_DIR, { recursive: true });
  await fs.mkdir("D:/Russian/docs/presentation", { recursive: true });

  const heroBytes = await fs.readFile(HERO);
  const screenshotBytes = await fs.readFile(SCREENSHOT);
  const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });

  // 1 — Cover: Codex Grid slide-08 composition (text left, hero right).
  {
    const slide = deck.slides.add();
    slide.background.fill = C.white;
    text(slide, "cover-kicker", "DESKTOP RUSSIAN LEARNING", 42, 40, 500, 24, 14, {
      bold: true,
      color: C.blue,
    });
    text(slide, "cover-title", "Russian\nCourse AI", 42, 112, 560, 150, 62, { bold: true });
    line(slide, "cover-rule", 42, 292, 128, C.blue, 4);
    text(slide, "cover-tr", "Rusçayı tek bir odaklı uygulamada öğrenin.", 42, 330, 540, 42, 22, { bold: true });
    text(slide, "cover-en", "Learn Russian in one focused desktop app.", 42, 388, 540, 42, 22, { color: C.blue, bold: true });
    text(slide, "cover-ru", "Изучайте русский в одном приложении.", 42, 446, 540, 42, 22, { color: C.muted, bold: true });
    text(slide, "cover-meta", "Windows 10/11 (x64) + macOS (Apple Silicon)  •  A1-C1  •  TR / EN / RU", 42, 590, 580, 28, 15, { color: C.muted });
    rect(slide, "hero-backing", 658, 42, 582, 588, C.navy, 18);
    slide.images.add({
      blob: heroBytes,
      contentType: "image/png",
      alt: "Dark editorial render of a laptop used for Russian study",
      fit: "cover",
      geometry: "roundRect",
      borderRadius: 18,
      position: { left: 658, top: 42, width: 582, height: 588 },
    });
    footer(slide, 1);
    notes(slide, [
      "D:/Russian/README.md (product positioning and supported levels)",
      "D:/Russian/docs/presentation/assets/russian-course-ai-hero.png (AI-generated original cover visual)",
    ]);
  }

  // 2 — Real interface evidence.
  {
    const slide = deck.slides.add();
    slide.background.fill = C.navy;
    text(slide, "screen-title", "One interface. Every practice mode.", 58, 34, 1120, 58, 46, { bold: true, color: C.white });
    text(slide, "screen-subtitle", "Tek arayüz. Tüm çalışma biçimleri.  •  Один интерфейс. Все форматы практики.", 60, 102, 1120, 28, 18, { color: "#AEB8CA" });
    rect(slide, "screen-frame", 60, 156, 1160, 500, "#171D2A", 14);
    slide.images.add({
      blob: screenshotBytes,
      contentType: "image/png",
      alt: "Russian Course AI spaced-review dashboard in dark mode",
      fit: "contain",
      geometry: "roundRect",
      borderRadius: 12,
      position: { left: 72, top: 168, width: 1136, height: 476 },
    });
    text(slide, "screen-footer", "02", 1180, 680, 56, 18, 13, { color: "#AEB8CA", align: "right" });
    notes(slide, [
      "D:/Russian/docs/presentation/assets/russian-course-ai-screenshot.png (user-supplied product screenshot)",
    ]);
  }

  // 3 — Three-language access: Codex Grid slide-06 three-column silhouette.
  {
    const slide = deck.slides.add();
    slide.background.fill = C.white;
    text(slide, "language-title", "One interface, three languages", 42, 36, 940, 60, 46, { bold: true });
    text(slide, "language-subtitle", "Dil seçimi anında uygulanır ve sonraki açılış için kaydedilir.", 42, 112, 900, 30, 19, { color: C.muted });
    line(slide, "language-rule", 42, 196, 1196, C.rule, 1);
    const columns = [
      { x: 42, label: "TÜRKÇE", title: "Öğrenmeye odaklanın", body: "Menüler, çalışma akışı ve AI yönergeleri seçtiğiniz dile uyum sağlar.", color: C.ink },
      { x: 453, label: "ENGLISH", title: "Learn without friction", body: "Navigation, study flows, and AI guidance follow your selected language.", color: C.blue },
      { x: 864, label: "РУССКИЙ", title: "Учитесь без барьеров", body: "Навигация, упражнения и инструкции для ИИ работают на выбранном языке.", color: C.muted },
    ];
    for (const [i, col] of columns.entries()) {
      text(slide, `language-label-${i}`, col.label, col.x, 238, 350, 24, 14, { bold: true, color: col.color });
      text(slide, `language-head-${i}`, col.title, col.x, 292, 350, 80, 30, { bold: true, color: col.color });
      text(slide, `language-body-${i}`, col.body, col.x, 400, 350, 126, 20, { color: col.color });
      line(slide, `language-accent-${i}`, col.x, 560, 112, col.color, 4);
    }
    footer(slide, 3);
    notes(slide, [
      "D:/Russian/rca/i18n.py (Turkish, English, and Russian interface catalog)",
      "D:/Russian/Russian_Course_AI.pyw (instant and persistent language switching)",
    ]);
  }

  // 4 — Learning loop: sparse three-step process.
  {
    const slide = deck.slides.add();
    slide.background.fill = C.white;
    text(slide, "loop-title", "A daily loop that keeps momentum", 42, 36, 1000, 60, 46, { bold: true });
    text(slide, "loop-subtitle", "Her gün küçük bir döngü.  •  A small loop every day.  •  Небольшой цикл каждый день.", 42, 112, 1120, 30, 18, { color: C.muted });
    line(slide, "loop-track", 110, 330, 1060, C.rule, 2);
    const steps = [
      { x: 84, n: "01", en: "LEARN", tr: "ÖĞREN", ru: "УЧИТЬ", detail: "Words • Dictionary • Cyrillic • Grammar" },
      { x: 456, n: "02", en: "PRACTICE", tr: "PRATİK", ru: "ПРАКТИКА", detail: "Speaking • Writing • Pronunciation" },
      { x: 828, n: "03", en: "REVIEW", tr: "TEKRAR", ru: "ПОВТОРЕНИЕ", detail: "Spaced review • Exams • Progress" },
    ];
    for (const [i, step] of steps.entries()) {
      rect(slide, `loop-node-${i}`, step.x, 300, 62, 62, i === 1 ? C.blue : C.ink, 31);
      text(slide, `loop-number-${i}`, step.n, step.x, 316, 62, 24, 16, { bold: true, color: C.white, align: "center" });
      text(slide, `loop-en-${i}`, step.en, step.x, 402, 300, 34, 27, { bold: true, color: i === 1 ? C.blue : C.ink });
      text(slide, `loop-tr-${i}`, step.tr, step.x, 448, 300, 28, 19, { bold: true, color: C.muted });
      text(slide, `loop-ru-${i}`, step.ru, step.x, 486, 300, 28, 19, { color: C.muted });
      text(slide, `loop-detail-${i}`, step.detail, step.x, 546, 300, 42, 17, { color: C.muted });
    }
    footer(slide, 4);
    notes(slide, [
      "D:/Russian/rca/tabs/srs_tab.py (daily review workflow and five study modes)",
      "D:/Russian/Russian_Course_AI.pyw (learning, lab, read, practice, and system navigation groups)",
    ]);
  }

  // 5 — Breadth, grounded in the actual navigation count.
  {
    const slide = deck.slides.add();
    slide.background.fill = C.faint;
    text(slide, "breadth-title", "More than flashcards", 42, 36, 800, 60, 46, { bold: true });
    text(slide, "breadth-triple", "Kelime kartlarından fazlası  •  Больше, чем карточки", 42, 108, 900, 28, 18, { color: C.muted });
    text(slide, "breadth-number", "18", 50, 206, 360, 220, 150, { bold: true, color: C.blue });
    text(slide, "breadth-caption", "focused workspaces\nodaklı çalışma alanı\nспециализированных разделов", 54, 446, 420, 126, 25, { bold: true });
    line(slide, "breadth-divider", 500, 188, 0, C.rule, 1).position = { left: 500, top: 188, width: 0, height: 414 };
    const items = [
      "RU-EN-TR dictionary · Yön seçimli sözlük · Словарь RU-EN-TR",
      "Word bank & grammar · Kelime bankası · Грамматика",
      "PDF reader · PDF okuyucu · PDF-читалка",
      "AI tutor · AI öğretmen · ИИ-преподаватель",
      "Speaking, handwriting, exams, progress",
      "Konuşma, el yazısı, sınav, ilerleme",
      "Разговор, почерк, экзамены, прогресс",
    ];
    items.forEach((item, i) => {
      const y = 202 + i * 58;
      line(slide, `breadth-item-rule-${i}`, 554, y + 34, 626, i < 4 ? C.rule : "#D7D9DE", 1);
      text(slide, `breadth-item-${i}`, item, 554, y, 626, 34, i < 4 ? 20 : 18, {
        bold: i < 4,
        color: i === 3 ? C.blue : C.ink,
      });
    });
    footer(slide, 5);
    notes(slide, [
      "D:/Russian/Russian_Course_AI.pyw (18 entries in TAB_SPECS)",
      "D:/Russian/rca/dictionary.py + rca/dict_data.py (RU-EN-TR dictionary with direction switch, 1,360 built-in entries with Turkish glosses, OpenRussian layer)",
      "D:/Russian/README.md (feature descriptions)",
    ]);
  }

  // 6 — Accurate privacy framing with explicit optional network use.
  {
    const slide = deck.slides.add();
    slide.background.fill = C.white;
    text(slide, "privacy-title", "Private by default. Flexible when needed.", 42, 36, 1100, 60, 46, { bold: true });
    text(slide, "privacy-tr", "Varsayılan olarak özel. Gerektiğinde esnek.", 42, 106, 820, 28, 19, { color: C.muted });
    text(slide, "privacy-ru", "Конфиденциальность по умолчанию. Гибкость при необходимости.", 42, 140, 1000, 28, 19, { color: C.muted });
    line(slide, "privacy-divider", 638, 212, 0, C.rule, 1).position = { left: 638, top: 212, width: 0, height: 350 };
    text(slide, "local-label", "LOCAL CORE", 62, 230, 470, 22, 14, { bold: true, color: C.blue });
    text(slide, "local-head", "Study data stays on your machine", 62, 280, 500, 72, 31, { bold: true });
    text(slide, "local-copy", "İlerleme SQLite içinde yerel saklanır.\nSözlük ve AI öğretmen LM Studio ile yerelde çalışır.\n\nПрогресс хранится локально в SQLite.\nСловарь и ИИ работают локально через LM Studio.", 62, 382, 500, 170, 19, { color: C.muted });
    text(slide, "optional-label", "OPTIONAL NETWORK", 696, 230, 470, 22, 14, { bold: true, color: C.ink });
    text(slide, "optional-head", "Online features activate only by choice", 696, 280, 500, 72, 31, { bold: true });
    text(slide, "optional-copy", "Kaynak indirmeleri ve alternatif AI ucu (NVIDIA NIM / özel OpenAI uyumlu URL) internet kullanır; anahtar Credential Manager'da.\nCore learning remains available without them.\n\nЗагрузки и альтернативный ИИ-узел (NVIDIA NIM) используют интернет.\nОсновное обучение доступно и без них.", 696, 382, 500, 170, 19, { color: C.muted });
    footer(slide, 6);
    notes(slide, [
      "D:/Russian/README.md (local LM Studio, optional NVIDIA NIM, and Resource Center network behavior)",
      "D:/Russian/rca/db.py (SQLite persistence)",
    ]);
  }

  // 7 — Platforms & download: v1.2.1 release availability with the private-repo caveat.
  {
    const slide = deck.slides.add();
    slide.background.fill = C.white;
    text(slide, "platform-title", "Platforms & Download", 42, 36, 1000, 60, 46, { bold: true });
    text(slide, "platform-subtitle", "Platformlar & İndirme  •  Платформы и загрузка", 42, 112, 1100, 30, 19, { color: C.muted });
    line(slide, "platform-rule", 42, 196, 1196, C.rule, 1);
    const rows = [
      { label: "TÜRKÇE", color: C.ink, body: "Windows 10/11 (x64) + macOS (Apple Silicon) — İndirme: github.com/Azizsekerdil/RussianCourseAI/releases (v1.2.1) (özel repo)" },
      { label: "ENGLISH", color: C.blue, body: "Windows 10/11 (x64) & macOS (Apple Silicon) — Download: GitHub Releases (v1.2.1)" },
      { label: "РУССКИЙ", color: C.muted, body: "Windows 10/11 (x64) и macOS (Apple Silicon) — Загрузка: GitHub Releases (v1.2.1)" },
    ];
    for (const [i, row] of rows.entries()) {
      const y = 232 + i * 104;
      text(slide, `platform-label-${i}`, row.label, 42, y, 300, 22, 14, { bold: true, color: row.color });
      text(slide, `platform-body-${i}`, row.body, 42, y + 28, 1196, 56, 17, { color: C.ink });
    }
    line(slide, "platform-footnote-rule", 42, 556, 1196, C.rule, 1);
    text(
      slide,
      "platform-footnote",
      "Release v1.2.1 — iki paket: Windows zip + macOS zip. macOS paketi Apple Silicon (arm64) içindir ve notarize edilmemiştir; ilk açılışta sağ tık → Aç.\nDepo özel (private) — github.com/Azizsekerdil/RussianCourseAI bağlantısına yalnızca hesap sahibi erişebilir.",
      42, 576, 1120, 84, 15,
      { color: C.muted },
    );
    footer(slide, 7);
    notes(slide, [
      "https://github.com/Azizsekerdil/RussianCourseAI/releases/tag/v1.2.1 (v1.2.1 release with Windows and macOS zip assets; private repository)",
    ]);
  }

  // 8 — Deliberate close: Codex Grid slide-26 composition.
  {
    const slide = deck.slides.add();
    slide.background.fill = C.white;
    text(slide, "close-kicker", "START YOUR NEXT SESSION", 42, 42, 420, 24, 14, { bold: true, color: C.blue });
    text(slide, "close-title", "Build a Russian routine\nthat belongs to you.", 42, 174, 1050, 180, 62, { bold: true });
    text(slide, "close-tr", "Size ait bir Rusça rutini oluşturun.", 42, 454, 720, 34, 23, { bold: true });
    text(slide, "close-ru", "Создайте свой ритм изучения русского.", 42, 504, 760, 34, 23, { color: C.muted, bold: true });
    line(slide, "close-rule", 42, 580, 1196, C.rule, 1);
    text(slide, "close-action", "INSTALL  •  LEARN  •  REVIEW", 42, 614, 620, 28, 18, { bold: true, color: C.blue });
    text(slide, "close-meta", "Windows 10/11 + macOS  •  A1-C1  •  TR / EN / RU", 700, 614, 538, 28, 17, { color: C.muted, align: "right" });
    footer(slide, 8);
    notes(slide, ["D:/Russian/README.md (installation, learning levels, and feature overview)"]);
  }

  for (const [index, slide] of deck.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await writeBlob(`${PREVIEW_DIR}/${stem}.png`, await deck.export({ slide, format: "png", scale: 1 }));
    await fs.writeFile(`${PREVIEW_DIR}/${stem}.layout.json`, await (await slide.export({ format: "layout" })).text());
  }
  await writeBlob(`${PREVIEW_DIR}/montage.webp`, await deck.export({ format: "webp", montage: true, scale: 1 }));
  const pptx = await PresentationFile.exportPptx(deck);
  await pptx.save(OUT);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
