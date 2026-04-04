const STORAGE_KEY = "slide_app.presentation";
const GENERATION_REQUEST_TIMEOUT_MS = 120000;
const GENERATION_STALL_NOTICE_MS = 20000;
let particleLayer = null;

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
    theme: String(formData.get("theme") || "").trim(),
    objective: String(formData.get("objective") || "").trim(),
    audience: String(formData.get("audience") || "").trim(),
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
        const message = typeof item.msg === "string" ? item.msg : "入力内容を確認してください。";
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
          ? "120秒以内に応答が返らなかったため、生成を停止しました。"
          : "生成処理を中止しました。入力を調整して再実行できます。",
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
    title.textContent = "スライド草案を生成しています";
    text.textContent = "API 経由でモデルへ問い合わせています。数秒から数十秒かかることがあります。";
    detail.textContent = "応答が長い場合は自動でエラー画面に切り替えます。";
  }

  if (state === "waiting") {
    title.textContent = "応答待ちが長くなっています";
    text.textContent = "API モデルの応答が遅れています。必要ならこの場で生成を中止できます。";
    detail.textContent = "複雑な入力やモデル負荷が原因の可能性があります。120秒で自動停止します。";
  }

  if (state === "error") {
    title.textContent = "生成処理が止まりました";
    text.textContent = message || "通信またはモデル API の応答が途中で止まりました。";
    detail.textContent = "もう一度試すか、入力内容を調整してやり直してください。";
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
    button.textContent = isLoading ? "生成中..." : "スライド草案を生成";
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
    setStatus("スライド草案を生成しています。", false, "form-status");
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
      setStatus("生成が完了しました。プレビュー画面へ移動します。", false, "form-status");
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
        document.getElementById("generate-button").textContent = "スライド草案を生成";
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
  return error?.message || "生成処理に失敗しました。";
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
  const response = await postJson("/api/render/html", presentation);
  const html = await response.text();
  const root = document.getElementById("slides-root");
  root.innerHTML = html;
  const titleNode = document.getElementById("presentation-title");
  titleNode.textContent = presentation.deck_title;
  const sidebarTitle = document.getElementById("sidebar-title");
  if (sidebarTitle) {
    sidebarTitle.textContent = presentation.deck_title;
  }
  const slideCountBadge = document.getElementById("slide-count-badge");
  if (slideCountBadge) {
    slideCountBadge.textContent = `${presentation.slides.length} 枚`;
  }
  const editor = document.getElementById("presentation-json");
  editor.value = JSON.stringify(presentation, null, 2);
  attachCardTilt(root);
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
    setStatus("保存されたプレゼン構成JSONがありません。入力画面から生成してください。", true);
    return;
  }

  try {
    await renderSlides(presentation);
    setStatus("生成結果を読み込みました。");
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
      setStatus("編集内容をJSONに反映しました。");
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
      setStatus("JSONを反映しました。");
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
      setStatus("Marp Markdownを出力しました。");
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
      setStatus("PDFを出力しました。");
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
      setStatus("PPTXを出力しました。");
    } catch (error) {
      setStatus(error.message, true);
    }
  });

  enchantButtons();
  attachCardTilt();
  initPageParallax();
}

function initPage() {
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
