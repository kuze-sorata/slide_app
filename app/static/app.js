const STORAGE_KEY = "slide_app.presentation";
const UI_LANGUAGE_KEY = "slide_app.ui_language";
const GENERATION_REQUEST_TIMEOUT_MS = 120000;
const GENERATION_STALL_NOTICE_MS = 20000;
let particleLayer = null;
let currentPreviewSlideIndex = 0;
let currentRenderedPresentation = null;
let currentUiLanguage = localStorage.getItem(UI_LANGUAGE_KEY) || "en";

const UI_TRANSLATIONS = {
  en: {
    "index.eyebrow": "MVP",
    "index.heroBadge": "Structured JSON First",
    "index.lead": "Generate short slide drafts from natural language requests. Keep structured JSON as the source of truth, then connect preview editing and export in a minimal flow.",
    "index.metricSourceLabel": "Source of truth",
    "index.metricSourceValue": "Presentation JSON",
    "index.metricEditableLabel": "Editable fields",
    "index.metricEditableValue": "Titles / bullets",
    "index.metricOutputLabel": "Export formats",
    "index.metricOutputValue": "HTML / PDF / PPTX",
    "index.questLabel": "Workflow",
    "index.stepInput": "Input",
    "index.stepGenerate": "Generate",
    "index.stepEdit": "Edit",
    "index.stepExport": "Export",
    "index.noteCap": "Focus",
    "index.noteTitle": "What this MVP prioritizes",
    "index.noteItem1": "Short, slide-ready phrasing",
    "index.noteItem2": "One message per slide",
    "index.noteItem3": "Stable JSON generation and validation",
    "index.noteChip1": "API-hosted LLMs",
    "index.noteChip2": "Marp / PDF / PPTX export",
    "index.noteChip3": "JSON re-validation after edits",
    "index.formEyebrow": "Input",
    "index.formTitle": "Slide generation input",
    "index.formStatusIdle": "Fill in the request, then run generation.",
    "index.infoKicker": "Recommended",
    "index.infoText": "Start with a natural language request describing the audience, purpose, and main points. Use the detailed fields only when needed.",
    "index.hintTitle1": "Natural language request",
    "index.hintText1": "Generation works better when you describe the audience, purpose, must-have points, and constraints in one message.",
    "index.hintTitle2": "Optional controls",
    "index.hintText2": "Slide count, tone, and required points can be overridden in the detailed settings.",
    "index.hintTitle3": "Simple prompt style",
    "index.hintText3": "Write who the deck is for, what should be shared, and what must be included.",
    "index.fieldRequestLabel": "Slide request",
    "index.fieldRequestHelp": "Describe the audience, purpose, key points, and constraints in natural language",
    "index.fieldRequestPlaceholder": "Example: Create a 5-slide update for a sales director covering current progress, key issues, and next actions.",
    "index.fieldCountLabel": "Slide count",
    "index.fieldCountHelp": "3 to 10 slides",
    "index.fieldToneLabel": "Tone",
    "index.fieldOptionalHelp": "Optional",
    "index.fieldTonePlaceholder": "Example: concise and professional",
    "index.detailsSummary": "Detailed settings",
    "index.fieldThemeLabel": "Theme",
    "index.fieldAutoFillHelp": "Auto-derived from the request if empty",
    "index.fieldThemePlaceholder": "Example: Sales update review",
    "index.fieldObjectiveLabel": "Objective",
    "index.fieldObjectivePlaceholder": "Example: Share current progress and next actions",
    "index.fieldAudienceLabel": "Audience",
    "index.fieldAudiencePlaceholder": "Example: sales director",
    "index.fieldNotesLabel": "Extra notes",
    "index.fieldNotesHelp": "Add context or constraints",
    "index.fieldNotesPlaceholder": "Example: Keep the wording easy to present in a meeting",
    "index.fieldRequiredLabel": "Required points",
    "index.fieldMultilineHelp": "One item per line",
    "index.fieldRequiredPlaceholder": "Example:\ncurrent progress\nkey issues\nnext actions",
    "index.fieldForbiddenLabel": "Avoid these phrases",
    "index.fieldForbiddenPlaceholder": "Example:\nvarious\nsomehow",
    "index.footerNote": "After generation, you can edit the deck in the preview page and export to Marp Markdown, PDF, or PPTX.",
    "index.generateButton": "Generate slide draft",
    "index.previewLink": "Open preview",
    "index.cancelButton": "Cancel",
    "index.retryButton": "Try again",
    "index.backToInputButton": "Back to input",
    "preview.eyebrow": "Preview",
    "preview.title": "Review the slide draft",
    "preview.topbarText": "Edit card content and JSON side by side, then re-validate on update.",
    "preview.backLink": "Back to input",
    "preview.controlCap": "Control panel",
    "preview.controlTitle": "Actions",
    "preview.controlHelp": "Edit titles and bullets directly on the cards. JSON is re-validated when you save.",
    "preview.statTitleLabel": "Deck title",
    "preview.statCountLabel": "Slide count",
    "preview.saveJsonButton": "Update JSON",
    "preview.exportMarpButton": "Export Marp Markdown",
    "preview.exportPdfButton": "Export PDF",
    "preview.exportPptxButton": "Export PPTX",
    "preview.tipsTitle": "Editing tips",
    "preview.tip1": "Keep one main claim per slide",
    "preview.tip2": "Try to stay within 3 bullets",
    "preview.tip3": "Make the conclusion clear in the title",
    "preview.jsonTitle": "Presentation JSON",
    "preview.applyJsonButton": "Apply JSON",
    "preview.slideEyebrow": "Slides",
    "preview.presentationTitle": "Preview",
    "preview.metaPill1": "Card editing",
    "preview.metaPill2": "JSON source of truth",
    "preview.metaPill3": "Marp export",
    "preview.statusLoading": "Loading the generated deck.",
    "preview.toolbarText": "Single-slide 16:9 view. Use the left and right arrows to review each slide.",
    "message.defaultValidation": "Please check the input.",
    "message.timeout": "Generation stopped because no response arrived within 120 seconds.",
    "message.cancelled": "Generation was cancelled. You can adjust the input and run it again.",
    "message.loadingTitle": "Generating slide draft",
    "message.loadingText": "Sending the request to the model API. This may take several seconds.",
    "message.loadingDetail": "If the response stalls for too long, the UI will switch to an error state.",
    "message.waitingTitle": "The response is taking longer than usual",
    "message.waitingText": "The API model is still working. You can cancel generation from this screen if needed.",
    "message.waitingDetail": "Complex input or temporary model load may be the cause. Generation stops automatically after 120 seconds.",
    "message.errorTitle": "Generation stopped",
    "message.errorText": "The request or model response stopped before completion.",
    "message.errorDetail": "Try again or adjust the input and rerun generation.",
    "message.generateButtonLoading": "Generating...",
    "message.generateButtonIdle": "Generate slide draft",
    "message.generatingStatus": "Generating slide draft.",
    "message.generationDone": "Generation completed. Moving to the preview page.",
    "message.generationFailed": "Generation failed.",
    "message.noSavedPresentation": "No saved presentation JSON was found. Generate a deck from the input page first.",
    "message.loadedPresentation": "Loaded the generated deck.",
    "message.updatedJson": "Updated the JSON from the edited content.",
    "message.appliedJson": "Applied the JSON editor content.",
    "message.exportedMarp": "Exported Marp Markdown.",
    "message.exportedPdf": "Exported PDF.",
    "message.exportedPptx": "Exported PPTX.",
    "message.slideCount": "{count} slides",
    "aria.prevSlide": "Previous slide",
    "aria.nextSlide": "Next slide",
  },
  ja: {
    "index.eyebrow": "MVP",
    "index.heroBadge": "Structured JSON First",
    "index.lead": "自然文のリクエストから、短いスライド草案を JSON として生成します。JSON を正本として、プレビュー編集とエクスポートまでを最小構成でつなぎます。",
    "index.metricSourceLabel": "正本データ",
    "index.metricSourceValue": "プレゼン構成JSON",
    "index.metricEditableLabel": "編集対象",
    "index.metricEditableValue": "タイトル / 箇条書き",
    "index.metricOutputLabel": "出力形式",
    "index.metricOutputValue": "HTML / PDF / PPTX",
    "index.questLabel": "操作の流れ",
    "index.stepInput": "入力",
    "index.stepGenerate": "生成",
    "index.stepEdit": "編集",
    "index.stepExport": "出力",
    "index.noteCap": "重要事項",
    "index.noteTitle": "優先していること",
    "index.noteItem1": "短く整理されたスライド表現",
    "index.noteItem2": "1スライド1メッセージ",
    "index.noteItem3": "JSONの安定生成と検証",
    "index.noteChip1": "APIホスト型LLM対応",
    "index.noteChip2": "Marp / PDF / PPTX出力",
    "index.noteChip3": "編集後にJSON再検証",
    "index.formEyebrow": "入力",
    "index.formTitle": "資料生成の入力",
    "index.formStatusIdle": "入力後に生成を実行してください。",
    "index.infoKicker": "推奨",
    "index.infoText": "まずは自然文で、誰向けに何を伝えたいかを書いてください。細かい項目は下の詳細設定で補えます。",
    "index.hintTitle1": "自然文入力",
    "index.hintText1": "相手、目的、入れたい論点、制約を一続きで書くと生成品質が上がります。",
    "index.hintTitle2": "補助入力",
    "index.hintText2": "枚数やトーン、必須論点は詳細設定で上書きできます。",
    "index.hintTitle3": "おすすめの書き方",
    "index.hintText3": "「誰向けに、何を共有したいか、何を入れたいか」をそのまま書いてください。",
    "index.fieldRequestLabel": "資料リクエスト",
    "index.fieldRequestHelp": "自然文で、相手・目的・入れたい論点・制約を書いてください",
    "index.fieldRequestPlaceholder": "例: 営業部長向けに、進捗・課題・次の打ち手を5枚で共有したい。",
    "index.fieldCountLabel": "想定スライド枚数",
    "index.fieldCountHelp": "3〜10枚",
    "index.fieldToneLabel": "トーン",
    "index.fieldOptionalHelp": "省略可",
    "index.fieldTonePlaceholder": "例: 簡潔で落ち着いた説明",
    "index.detailsSummary": "詳細設定",
    "index.fieldThemeLabel": "テーマ",
    "index.fieldAutoFillHelp": "空欄なら自然文から補完",
    "index.fieldThemePlaceholder": "例: 営業進捗の振り返り",
    "index.fieldObjectiveLabel": "資料の目的",
    "index.fieldObjectivePlaceholder": "例: 現状と次の打ち手を共有する",
    "index.fieldAudienceLabel": "想定読者",
    "index.fieldAudiencePlaceholder": "例: 営業部長",
    "index.fieldNotesLabel": "補足メモ",
    "index.fieldNotesHelp": "背景や制約条件を補足",
    "index.fieldNotesPlaceholder": "例: 会議でそのまま説明しやすい表現にしたい",
    "index.fieldRequiredLabel": "必ず入れたい論点",
    "index.fieldMultilineHelp": "改行区切りで複数入力",
    "index.fieldRequiredPlaceholder": "例:\n進捗\n課題\n次の打ち手",
    "index.fieldForbiddenLabel": "避けたい表現",
    "index.fieldForbiddenPlaceholder": "例:\nいろいろ\nなんとなく",
    "index.footerNote": "生成後はプレビュー画面で直接編集し、そのまま Marp Markdown と PDF に出力できます。",
    "index.generateButton": "スライド草案を生成",
    "index.previewLink": "プレビュー画面へ",
    "index.cancelButton": "生成を中止",
    "index.retryButton": "もう一度試す",
    "index.backToInputButton": "入力に戻る",
    "preview.eyebrow": "プレビュー",
    "preview.title": "スライド草案の確認",
    "preview.topbarText": "カード編集と JSON 編集を並行できるようにし、更新時に再検証します。",
    "preview.backLink": "入力に戻る",
    "preview.controlCap": "操作パネル",
    "preview.controlTitle": "操作",
    "preview.controlHelp": "タイトルと箇条書きはカード上で直接編集できます。保存時に JSON を再検証します。",
    "preview.statTitleLabel": "資料タイトル",
    "preview.statCountLabel": "スライド枚数",
    "preview.saveJsonButton": "JSONを更新",
    "preview.exportMarpButton": "Marp Markdownを書き出し",
    "preview.exportPdfButton": "PDFを書き出し",
    "preview.exportPptxButton": "PPTXを書き出し",
    "preview.tipsTitle": "編集のヒント",
    "preview.tip1": "1枚につき主張は1つに絞る",
    "preview.tip2": "箇条書きは3点以内を維持する",
    "preview.tip3": "結論がタイトルで伝わる状態にする",
    "preview.jsonTitle": "プレゼン構成JSON",
    "preview.applyJsonButton": "JSONを適用",
    "preview.slideEyebrow": "スライド",
    "preview.presentationTitle": "プレビュー",
    "preview.metaPill1": "カード編集",
    "preview.metaPill2": "JSON正本",
    "preview.metaPill3": "Marp出力",
    "preview.statusLoading": "生成結果を読み込み中です。",
    "preview.toolbarText": "16:9 の単一スライド表示です。左右の矢印で切り替えながら内容を確認できます。",
    "message.defaultValidation": "入力内容を確認してください。",
    "message.timeout": "120秒以内に応答が返らなかったため、生成を停止しました。",
    "message.cancelled": "生成処理を中止しました。入力を調整して再実行できます。",
    "message.loadingTitle": "スライド草案を生成しています",
    "message.loadingText": "API 経由でモデルへ問い合わせています。数秒から数十秒かかることがあります。",
    "message.loadingDetail": "応答が長い場合は自動でエラー画面に切り替えます。",
    "message.waitingTitle": "応答待ちが長くなっています",
    "message.waitingText": "API モデルの応答が遅れています。必要ならこの場で生成を中止できます。",
    "message.waitingDetail": "複雑な入力やモデル負荷が原因の可能性があります。120秒で自動停止します。",
    "message.errorTitle": "生成処理が止まりました",
    "message.errorText": "通信またはモデル API の応答が途中で止まりました。",
    "message.errorDetail": "もう一度試すか、入力内容を調整してやり直してください。",
    "message.generateButtonLoading": "生成中...",
    "message.generateButtonIdle": "スライド草案を生成",
    "message.generatingStatus": "スライド草案を生成しています。",
    "message.generationDone": "生成が完了しました。プレビュー画面へ移動します。",
    "message.generationFailed": "生成処理に失敗しました。",
    "message.noSavedPresentation": "保存されたプレゼン構成JSONがありません。入力画面から生成してください。",
    "message.loadedPresentation": "生成結果を読み込みました。",
    "message.updatedJson": "編集内容をJSONに反映しました。",
    "message.appliedJson": "JSONを反映しました。",
    "message.exportedMarp": "Marp Markdownを出力しました。",
    "message.exportedPdf": "PDFを出力しました。",
    "message.exportedPptx": "PPTXを出力しました。",
    "message.slideCount": "{count} 枚",
    "aria.prevSlide": "前のスライド",
    "aria.nextSlide": "次のスライド",
  },
};

function t(key) {
  return UI_TRANSLATIONS[currentUiLanguage]?.[key] ?? UI_TRANSLATIONS.en[key] ?? key;
}

function setUiLanguage(language) {
  currentUiLanguage = language === "ja" ? "ja" : "en";
  localStorage.setItem(UI_LANGUAGE_KEY, currentUiLanguage);
  applyUiLanguage();
}

function applyUiLanguage() {
  document.documentElement.lang = currentUiLanguage;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    if (node.id === "presentation-title" && currentRenderedPresentation) {
      return;
    }
    const key = node.dataset.i18n;
    const translated = t(key);
    if (translated) {
      node.textContent = translated;
    }
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    const key = node.dataset.i18nPlaceholder;
    const translated = t(key);
    if (translated) {
      node.placeholder = translated;
    }
  });
  document.querySelectorAll("[data-lang-select]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.langSelect === currentUiLanguage);
  });
  const prevButton = document.getElementById("prev-slide-button");
  const nextButton = document.getElementById("next-slide-button");
  if (prevButton) {
    prevButton.setAttribute("aria-label", t("aria.prevSlide"));
  }
  if (nextButton) {
    nextButton.setAttribute("aria-label", t("aria.nextSlide"));
  }
  if (currentRenderedPresentation) {
    updateRenderedPresentationMeta(currentRenderedPresentation);
  }
}

function updateRenderedPresentationMeta(presentation) {
  const titleNode = document.getElementById("presentation-title");
  if (titleNode) {
    titleNode.textContent = presentation.deck_title;
  }
  const sidebarTitle = document.getElementById("sidebar-title");
  if (sidebarTitle) {
    sidebarTitle.textContent = presentation.deck_title;
  }
  const slideCountBadge = document.getElementById("slide-count-badge");
  if (slideCountBadge) {
    slideCountBadge.textContent = t("message.slideCount").replace("{count}", String(presentation.slides.length));
  }
}

function bindLanguageToggle() {
  document.querySelectorAll("[data-lang-select]").forEach((button) => {
    button.addEventListener("click", () => {
      setUiLanguage(button.dataset.langSelect);
    });
  });
}

function setStatus(message, isError = false, targetId = "status-message") {
  const node = document.getElementById(targetId);
  if (!node) {
    return;
  }
  node.textContent = message;
  node.classList.toggle("status-error", isError);
  node.classList.toggle("status-success", !isError);
}

function splitLines(value) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function buildGenerationPayload(form) {
  const formData = new FormData(form);
  return {
    user_request: String(formData.get("user_request") || "").trim() || null,
    theme: String(formData.get("theme") || "").trim() || null,
    objective: String(formData.get("objective") || "").trim() || null,
    audience: String(formData.get("audience") || "").trim() || null,
    slide_count: Number(formData.get("slide_count")),
    tone: String(formData.get("tone") || "").trim() || null,
    extra_notes: String(formData.get("extra_notes") || "").trim() || null,
    required_points: splitLines(String(formData.get("required_points") || "")),
    forbidden_expressions: splitLines(String(formData.get("forbidden_expressions") || "")),
  };
}

function formatApiErrorDetail(detail) {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => {
        if (!item || typeof item !== "object") {
          return "";
        }
        const path = Array.isArray(item.loc) ? item.loc.slice(1).join(".") : "";
        const message = typeof item.msg === "string" ? item.msg : t("message.defaultValidation");
        return path ? `${path}: ${message}` : message;
      })
      .filter(Boolean)
      .join(" / ");
  }
  return "";
}

async function postJson(url, payload, options = {}) {
  const { timeoutMs = 0, signal } = options;
  const controller = new AbortController();
  const timeoutId = timeoutMs > 0
    ? window.setTimeout(() => controller.abort("timeout"), timeoutMs)
    : null;
  if (signal) {
    signal.addEventListener("abort", () => controller.abort(signal.reason), { once: true });
  }
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      const detail = formatApiErrorDetail(data.detail);
      throw new Error(detail || `Request failed: ${response.status}`);
    }
    return response;
  } catch (error) {
    if (controller.signal.aborted) {
      const reason = controller.signal.reason;
      const abortError = new Error(
        reason === "timeout"
          ? t("message.timeout")
          : t("message.cancelled"),
      );
      abortError.name = reason === "timeout" ? "TimeoutError" : "AbortError";
      throw abortError;
    }
    throw error;
  } finally {
    if (timeoutId !== null) {
      window.clearTimeout(timeoutId);
    }
  }
}

function savePresentation(presentation) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(presentation));
}

function loadPresentation() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }
  return JSON.parse(raw);
}

function setGenerationOverlayState(state, message = "") {
  const spinner = document.getElementById("loading-spinner");
  const title = document.getElementById("loading-title");
  const text = document.getElementById("loading-text");
  const detail = document.getElementById("loading-detail");
  const actions = document.getElementById("loading-actions");
  const overlay = document.getElementById("generation-overlay");
  const retryButton = document.getElementById("retry-generate-button");
  const cancelButton = document.getElementById("cancel-generate-button");
  const closeButton = document.getElementById("close-overlay-button");

  if (!overlay || !spinner || !title || !text || !detail || !actions) {
    return;
  }

  overlay.dataset.state = state;
  actions.hidden = state === "loading";
  spinner.hidden = state === "error";
  spinner.classList.toggle("loading-spinner", state !== "error");
  spinner.classList.toggle("loading-error-icon", state === "error");
  if (retryButton) {
    retryButton.hidden = state !== "error";
  }
  if (cancelButton) {
    cancelButton.hidden = state === "error";
  }
  if (closeButton) {
    closeButton.hidden = state === "waiting";
  }

  if (state === "loading") {
    title.textContent = t("message.loadingTitle");
    text.textContent = t("message.loadingText");
    detail.textContent = t("message.loadingDetail");
  }

  if (state === "waiting") {
    title.textContent = t("message.waitingTitle");
    text.textContent = t("message.waitingText");
    detail.textContent = t("message.waitingDetail");
  }

  if (state === "error") {
    title.textContent = t("message.errorTitle");
    text.textContent = message || t("message.errorText");
    detail.textContent = t("message.errorDetail");
  }
}

function setGenerationLoading(isLoading) {
  const overlay = document.getElementById("generation-overlay");
  const button = document.getElementById("generate-button");
  if (overlay) {
    overlay.hidden = !isLoading;
  }
  if (button instanceof HTMLButtonElement) {
    button.disabled = isLoading;
    button.textContent = isLoading ? t("message.generateButtonLoading") : t("message.generateButtonIdle");
  }
  if (isLoading) {
    setGenerationOverlayState("loading");
  }
}

function ensureParticleLayer() {
  if (particleLayer) {
    return particleLayer;
  }
  particleLayer = document.createElement("div");
  particleLayer.className = "particle-layer";
  document.body.appendChild(particleLayer);
  return particleLayer;
}

function spawnMagicBurst(x, y, count = 10) {
  const layer = ensureParticleLayer();
  for (let index = 0; index < count; index += 1) {
    const particle = document.createElement("span");
    particle.className = "magic-particle";
    const angle = (Math.PI * 2 * index) / count;
    const distance = 26 + Math.random() * 34;
    particle.style.left = `${x}px`;
    particle.style.top = `${y}px`;
    particle.style.setProperty("--tx", `${Math.cos(angle) * distance}px`);
    particle.style.setProperty("--ty", `${Math.sin(angle) * distance}px`);
    particle.style.animationDelay = `${Math.random() * 80}ms`;
    layer.appendChild(particle);
    window.setTimeout(() => particle.remove(), 900);
  }
}

function enchantButtons(scope = document) {
  const buttons = scope.querySelectorAll(".primary-button, .secondary-button, .link-button");
  buttons.forEach((button) => {
    if (button.dataset.enchanted === "true") {
      return;
    }
    button.dataset.enchanted = "true";
    button.classList.add("button-enchanted");
    button.addEventListener("pointerenter", () => {
      button.classList.remove("is-flashing");
      void button.offsetWidth;
      button.classList.add("is-flashing");
    });
    button.addEventListener("click", (event) => {
      const rect = button.getBoundingClientRect();
      const x = event.clientX || rect.left + rect.width / 2;
      const y = event.clientY || rect.top + rect.height / 2;
      spawnMagicBurst(x, y, 9);
    });
  });
}

function attachCardTilt(scope = document) {
  const cards = scope.querySelectorAll(".slide-card, .metric-card, .hint-card, .stat-box");
  cards.forEach((card) => {
    if (card.dataset.tiltBound === "true") {
      return;
    }
    card.dataset.tiltBound = "true";
    card.classList.add("is-tilting");
    card.addEventListener("pointermove", (event) => {
      const rect = card.getBoundingClientRect();
      const px = (event.clientX - rect.left) / rect.width;
      const py = (event.clientY - rect.top) / rect.height;
      const rotateY = (px - 0.5) * 8;
      const rotateX = (0.5 - py) * 8;
      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
    });
    card.addEventListener("pointerleave", () => {
      card.style.transform = "";
    });
    card.addEventListener("click", (event) => {
      spawnMagicBurst(event.clientX, event.clientY, 7);
    });
  });
}

function initPageParallax() {
  const hero = document.querySelector(".hero-copy, .preview-header");
  if (!hero || hero.dataset.parallaxBound === "true") {
    return;
  }
  hero.dataset.parallaxBound = "true";
  document.addEventListener("pointermove", (event) => {
    const offsetX = ((event.clientX / window.innerWidth) - 0.5) * 14;
    const offsetY = ((event.clientY / window.innerHeight) - 0.5) * 12;
    hero.style.transform = `translate3d(${offsetX}px, ${offsetY}px, 0)`;
  });
}

async function initIndexPage() {
  const form = document.getElementById("generation-form");
  if (!form) {
    return;
  }
  let isSubmitting = false;
  let stallNoticeId = null;
  let currentRequestController = null;

  const clearGenerationTimers = () => {
    if (stallNoticeId !== null) {
      window.clearTimeout(stallNoticeId);
      stallNoticeId = null;
    }
  };

  const resetGenerationUi = () => {
    clearGenerationTimers();
    if (currentRequestController) {
      currentRequestController.abort("cancelled");
      currentRequestController = null;
    }
    setGenerationLoading(false);
    setGenerationOverlayState("loading");
    isSubmitting = false;
  };

  const runGeneration = async () => {
    if (isSubmitting) {
      return;
    }
    isSubmitting = true;
    setGenerationLoading(true);
    setStatus(t("message.generatingStatus"), false, "form-status");
    stallNoticeId = window.setTimeout(() => {
      setGenerationOverlayState("waiting");
    }, GENERATION_STALL_NOTICE_MS);
    currentRequestController = new AbortController();
    try {
      const payload = buildGenerationPayload(form);
      const response = await postJson("/api/generate", payload, {
        timeoutMs: GENERATION_REQUEST_TIMEOUT_MS,
        signal: currentRequestController.signal,
      });
      const presentation = await response.json();
      clearGenerationTimers();
      currentRequestController = null;
      savePresentation(presentation);
      setStatus(t("message.generationDone"), false, "form-status");
      window.location.href = "/preview";
    } catch (error) {
      const message = normalizeGenerationError(error);
      clearGenerationTimers();
      currentRequestController = null;
      setGenerationOverlayState("error", message);
      if (document.getElementById("generation-overlay")) {
        document.getElementById("generation-overlay").hidden = false;
      }
      if (document.getElementById("generate-button") instanceof HTMLButtonElement) {
        document.getElementById("generate-button").disabled = false;
        document.getElementById("generate-button").textContent = t("message.generateButtonIdle");
      }
      isSubmitting = false;
      setStatus(message, true, "form-status");
    }
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    await runGeneration();
  });

  const button = document.getElementById("generate-button");
  button?.addEventListener("click", async (event) => {
    event.preventDefault();
    await runGeneration();
  });

  document.getElementById("retry-generate-button")?.addEventListener("click", async () => {
    await runGeneration();
  });

  document.getElementById("cancel-generate-button")?.addEventListener("click", () => {
    if (currentRequestController) {
      currentRequestController.abort("cancelled");
    }
  });

  document.getElementById("close-overlay-button")?.addEventListener("click", () => {
    resetGenerationUi();
  });

  enchantButtons();
  attachCardTilt();
  initPageParallax();
}

function normalizeGenerationError(error) {
  if (error?.name === "AbortError" || error?.name === "TimeoutError") {
    return error.message;
  }
  return error?.message || t("message.generationFailed");
}

function collectEditedPresentation(basePresentation) {
  const slides = basePresentation.slides.map((slide) => {
    const titleNode = document.querySelector(
      `[data-field="title"][data-slide-id="${slide.id}"]`,
    );
    const bulletNodes = document.querySelectorAll(
      `[data-field="bullet"][data-slide-id="${slide.id}"]`,
    );
    return {
      ...slide,
      title: titleNode ? titleNode.textContent.trim() : slide.title,
      bullets: Array.from(bulletNodes)
        .map((node) => node.textContent.trim())
        .filter(Boolean)
        .slice(0, 4),
    };
  });
  return {
    ...basePresentation,
    deck_title: slides[0]?.title || basePresentation.deck_title,
    slides,
  };
}

async function renderSlides(presentation) {
  currentRenderedPresentation = presentation;
  const response = await postJson("/api/render/html", presentation);
  const html = await response.text();
  const root = document.getElementById("slides-root");
  root.innerHTML = html;
  updateRenderedPresentationMeta(presentation);
  const editor = document.getElementById("presentation-json");
  editor.value = JSON.stringify(presentation, null, 2);
  setupSlideCarousel(presentation.slides.length);
  attachCardTilt(root);
}

function setupSlideCarousel(slideCount) {
  const root = document.getElementById("slides-root");
  if (!root) {
    return;
  }
  const slides = Array.from(root.querySelectorAll(".slide-card"));
  if (slides.length === 0) {
    return;
  }
  currentPreviewSlideIndex = Math.min(currentPreviewSlideIndex, slides.length - 1);
  if (currentPreviewSlideIndex < 0) {
    currentPreviewSlideIndex = 0;
  }

  const updateView = () => {
    slides.forEach((slide, index) => {
      slide.classList.toggle("is-active", index === currentPreviewSlideIndex);
    });
    const position = document.getElementById("current-slide-position");
    if (position) {
      position.textContent = `${currentPreviewSlideIndex + 1} / ${slideCount}`;
    }
    const prevButton = document.getElementById("prev-slide-button");
    const nextButton = document.getElementById("next-slide-button");
    if (prevButton instanceof HTMLButtonElement) {
      prevButton.disabled = currentPreviewSlideIndex === 0;
    }
    if (nextButton instanceof HTMLButtonElement) {
      nextButton.disabled = currentPreviewSlideIndex === slides.length - 1;
    }
  };

  const moveTo = (nextIndex) => {
    if (nextIndex < 0 || nextIndex >= slides.length) {
      return;
    }
    currentPreviewSlideIndex = nextIndex;
    updateView();
  };

  document.getElementById("prev-slide-button")?.replaceWith(
    document.getElementById("prev-slide-button").cloneNode(true),
  );
  document.getElementById("next-slide-button")?.replaceWith(
    document.getElementById("next-slide-button").cloneNode(true),
  );

  document.getElementById("prev-slide-button")?.addEventListener("click", () => {
    moveTo(currentPreviewSlideIndex - 1);
  });
  document.getElementById("next-slide-button")?.addEventListener("click", () => {
    moveTo(currentPreviewSlideIndex + 1);
  });

  window.onkeydown = (event) => {
    if (document.body.dataset.page !== "preview") {
      return;
    }
    if (event.key === "ArrowLeft") {
      moveTo(currentPreviewSlideIndex - 1);
    }
    if (event.key === "ArrowRight") {
      moveTo(currentPreviewSlideIndex + 1);
    }
  };

  updateView();
}

function downloadBlob(content, contentType, fileName) {
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(url);
}

async function initPreviewPage() {
  let presentation = loadPresentation();
  if (!presentation) {
    setStatus(t("message.noSavedPresentation"), true);
    return;
  }

  try {
    await renderSlides(presentation);
    setStatus(t("message.loadedPresentation"));
  } catch (error) {
    setStatus(error.message, true);
    return;
  }

  document.getElementById("save-json-button")?.addEventListener("click", async () => {
    try {
      const edited = collectEditedPresentation(presentation);
      const response = await postJson("/api/update", edited);
      presentation = await response.json();
      savePresentation(presentation);
      await renderSlides(presentation);
      setStatus(t("message.updatedJson"));
    } catch (error) {
      setStatus(error.message, true);
    }
  });

  document.getElementById("apply-json-button")?.addEventListener("click", async () => {
    try {
      const editor = document.getElementById("presentation-json");
      const parsed = JSON.parse(editor.value);
      const response = await postJson("/api/update", parsed);
      presentation = await response.json();
      savePresentation(presentation);
      await renderSlides(presentation);
      setStatus(t("message.appliedJson"));
    } catch (error) {
      setStatus(error.message, true);
    }
  });

  document.getElementById("export-marp-button")?.addEventListener("click", async () => {
    try {
      const edited = collectEditedPresentation(presentation);
      const response = await postJson("/api/export/marp", edited);
      const markdown = await response.text();
      downloadBlob(markdown, "text/markdown;charset=utf-8", "presentation.md");
      setStatus(t("message.exportedMarp"));
    } catch (error) {
      setStatus(error.message, true);
    }
  });

  document.getElementById("export-pdf-button")?.addEventListener("click", async () => {
    try {
      const edited = collectEditedPresentation(presentation);
      const response = await postJson("/api/export/pdf", edited);
      const pdf = await response.blob();
      downloadBlob(pdf, "application/pdf", "presentation.pdf");
      setStatus(t("message.exportedPdf"));
    } catch (error) {
      setStatus(error.message, true);
    }
  });

  document.getElementById("export-pptx-button")?.addEventListener("click", async () => {
    try {
      const edited = collectEditedPresentation(presentation);
      const response = await postJson("/api/export/pptx", edited);
      const pptx = await response.blob();
      downloadBlob(
        pptx,
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "presentation.pptx",
      );
      setStatus(t("message.exportedPptx"));
    } catch (error) {
      setStatus(error.message, true);
    }
  });

  enchantButtons();
  attachCardTilt();
  initPageParallax();
}

function initPage() {
  bindLanguageToggle();
  applyUiLanguage();
  const page = document.body.dataset.page;
  if (page === "index") {
    initIndexPage();
  }
  if (page === "preview") {
    initPreviewPage();
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initPage);
} else {
  initPage();
}
