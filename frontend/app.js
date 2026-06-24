/* Visual Learn Everything — frontend logic */
(() => {
  "use strict";

  const $ = (sel) => document.querySelector(sel);

  const views = {
    upload: $("#upload-view"),
    loading: $("#loading-view"),
    result: $("#result-view"),
  };

  function show(view) {
    Object.values(views).forEach((v) => v.classList.add("hidden"));
    views[view].classList.remove("hidden");
  }

  // ---- Provider pill ----
  fetch("/api/health")
    .then((r) => r.json())
    .then((h) => {
      $("#provider-pill").textContent = `engine: ${h.provider}${
        h.model ? " · " + h.model : ""
      }`;
    })
    .catch(() => {
      $("#provider-pill").textContent = "engine: unknown";
    });

  // ---- Upload handling ----
  const dropzone = $("#dropzone");
  const fileInput = $("#file-input");

  $("#browse-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    fileInput.click();
  });
  dropzone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length) uploadFile(fileInput.files[0]);
  });

  ["dragenter", "dragover"].forEach((ev) =>
    dropzone.addEventListener(ev, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    })
  );
  ["dragleave", "drop"].forEach((ev) =>
    dropzone.addEventListener(ev, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    })
  );
  dropzone.addEventListener("drop", (e) => {
    const f = e.dataTransfer.files[0];
    if (f) uploadFile(f);
  });

  $("#sample-btn").addEventListener("click", loadSample);
  $("#new-btn").addEventListener("click", () => {
    fileInput.value = "";
    show("upload");
  });

  function showError(msg) {
    const box = $("#error-box");
    box.textContent = msg;
    box.classList.remove("hidden");
  }

  async function loadSample() {
    try {
      const res = await fetch("/samples/sample.md");
      if (!res.ok) throw new Error("Sample not found");
      const text = await res.text();
      const file = new File([text], "sample.md", { type: "text/markdown" });
      uploadFile(file);
    } catch (e) {
      showError("Could not load the sample file: " + e.message);
    }
  }

  let loadingTimer = null;
  const loadingMessages = [
    "Reading your document…",
    "Extracting text and images…",
    "Asking the model to organise the ideas…",
    "Building your mind map and quiz…",
  ];

  function startLoadingAnimation() {
    let i = 0;
    $("#loading-text").textContent = loadingMessages[0];
    $("#loading-sub").textContent = "This usually takes a few seconds.";
    loadingTimer = setInterval(() => {
      i = (i + 1) % loadingMessages.length;
      $("#loading-text").textContent = loadingMessages[i];
    }, 2500);
  }
  function stopLoadingAnimation() {
    if (loadingTimer) clearInterval(loadingTimer);
    loadingTimer = null;
  }

  async function uploadFile(file) {
    $("#error-box").classList.add("hidden");
    show("loading");
    startLoadingAnimation();

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch("/api/process", { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Processing failed.");
      }
      stopLoadingAnimation();
      renderResult(data);
      show("result");
    } catch (e) {
      stopLoadingAnimation();
      show("upload");
      showError(e.message);
    }
  }

  // ---- Rendering ----
  function renderResult(pkg) {
    $("#result-title").textContent = pkg.title || "Learning Material";

    const meta = pkg.meta || {};
    const bits = [];
    if (meta.source_filename) bits.push(meta.source_filename);
    if (meta.source_type) bits.push(meta.source_type.toUpperCase());
    if (meta.provider) bits.push("engine: " + meta.provider);
    if (typeof meta.char_count === "number")
      bits.push(meta.char_count.toLocaleString() + " chars");
    $("#result-meta").textContent = bits.join("  ·  ");

    const note = $("#truncation-note");
    if (meta.truncated) {
      note.textContent =
        "Note: this document is large — only the first portion was analysed.";
      note.classList.remove("hidden");
    } else {
      note.classList.add("hidden");
    }

    renderMindmap(pkg.mindmap);
    renderSummary(pkg.summary);
    renderConcepts(pkg.key_concepts || []);
    renderFlashcards(pkg.flashcards || []);
    renderQuiz(pkg.quiz || []);
    renderImages(pkg.images || []);

    // Reset to first tab.
    activateTab("mindmap");
  }

  // Tabs
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => activateTab(tab.dataset.tab));
  });
  function activateTab(name) {
    document
      .querySelectorAll(".tab")
      .forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
    document
      .querySelectorAll(".panel")
      .forEach((p) => p.classList.toggle("active", p.dataset.panel === name));
    if (name === "mindmap" && currentMarkmap) {
      // Re-fit the SVG now that the panel is visible.
      setTimeout(() => {
        try {
          currentMarkmap.fit();
        } catch (e) {}
      }, 50);
    }
  }

  // Mind map
  let currentMarkmap = null;
  function renderMindmap(node) {
    const svg = $("#mindmap-svg");
    const fallback = $("#mindmap-fallback");
    svg.innerHTML = "";
    fallback.innerHTML = "";
    currentMarkmap = null;

    const hasMarkmap =
      window.markmap && window.markmap.Transformer && window.markmap.Markmap;

    if (hasMarkmap) {
      try {
        const { Transformer, Markmap } = window.markmap;
        const md = mindmapToMarkdown(node);
        const { root } = new Transformer().transform(md);
        svg.classList.remove("hidden");
        fallback.classList.add("hidden");
        currentMarkmap = Markmap.create(svg, { duration: 300 }, root);
        setTimeout(() => {
          try {
            currentMarkmap.fit();
          } catch (e) {}
        }, 60);
        return;
      } catch (e) {
        /* fall through to built-in renderer */
      }
    }
    // Offline / failure fallback: collapsible tree.
    svg.classList.add("hidden");
    fallback.classList.remove("hidden");
    fallback.appendChild(buildTree(node));
  }

  function mindmapToMarkdown(node) {
    const lines = ["# " + textOf(node)];
    childrenOf(node).forEach((c) => walkMd(c, 0, lines));
    return lines.join("\n");
  }
  function walkMd(node, indent, lines) {
    const pad = "  ".repeat(indent);
    lines.push(pad + "- " + textOf(node));
    childrenOf(node).forEach((c) => walkMd(c, indent + 1, lines));
  }

  function buildTree(node) {
    const ul = document.createElement("ul");
    ul.className = "mm-tree";
    const li = document.createElement("li");
    const label = document.createElement("span");
    label.className = "mm-label";
    label.textContent = textOf(node);
    li.appendChild(label);
    const kids = childrenOf(node);
    if (kids.length) li.appendChild(buildChildren(kids));
    ul.appendChild(li);
    return ul;
  }
  function buildChildren(children) {
    const ul = document.createElement("ul");
    children.forEach((c) => {
      const li = document.createElement("li");
      const label = document.createElement("span");
      label.className = "mm-label";
      label.textContent = textOf(c);
      li.appendChild(label);
      const kids = childrenOf(c);
      if (kids.length) li.appendChild(buildChildren(kids));
      ul.appendChild(li);
    });
    return ul;
  }

  function textOf(n) {
    if (typeof n === "string") return n;
    return (n && n.title) || "";
  }
  function childrenOf(n) {
    if (!n || typeof n === "string") return [];
    return Array.isArray(n.children) ? n.children : [];
  }

  function renderSummary(summary) {
    $("#summary-content").textContent = summary || "No summary available.";
  }

  function renderConcepts(concepts) {
    const root = $("#concepts-content");
    root.innerHTML = "";
    if (!concepts.length) {
      root.innerHTML = '<p class="empty-state">No key concepts were extracted.</p>';
      return;
    }
    concepts.forEach((c) => {
      const card = document.createElement("div");
      card.className = "concept-card";
      const h = document.createElement("h4");
      h.textContent = c.term;
      const p = document.createElement("p");
      p.textContent = c.definition;
      card.append(h, p);
      root.appendChild(card);
    });
  }

  function renderFlashcards(cards) {
    const root = $("#flashcards-content");
    root.innerHTML = "";
    if (!cards.length) {
      root.innerHTML = '<p class="empty-state">No flashcards were generated.</p>';
      return;
    }
    cards.forEach((c) => {
      const card = document.createElement("div");
      card.className = "flashcard";
      card.innerHTML = `
        <div class="flashcard-inner">
          <div class="flashcard-face flashcard-front"></div>
          <div class="flashcard-face flashcard-back"></div>
        </div>`;
      card.querySelector(".flashcard-front").textContent = c.front;
      card.querySelector(".flashcard-back").textContent = c.back;
      const hint = document.createElement("span");
      hint.className = "flashcard-hint";
      hint.textContent = "click to flip";
      card.querySelector(".flashcard-front").appendChild(hint);
      card.addEventListener("click", () => card.classList.toggle("flipped"));
      root.appendChild(card);
    });
  }

  function renderQuiz(quiz) {
    const root = $("#quiz-content");
    const scoreBox = $("#quiz-score");
    root.innerHTML = "";
    scoreBox.classList.add("hidden");
    if (!quiz.length) {
      root.innerHTML = '<p class="empty-state">No quiz was generated.</p>';
      return;
    }

    let answered = 0;
    let correct = 0;

    quiz.forEach((q, qi) => {
      const item = document.createElement("div");
      item.className = "quiz-item";
      const question = document.createElement("p");
      question.className = "quiz-q";
      question.textContent = `${qi + 1}. ${q.question}`;
      item.appendChild(question);

      const opts = document.createElement("div");
      opts.className = "quiz-options";
      const buttons = [];
      (q.options || []).forEach((opt, oi) => {
        const btn = document.createElement("button");
        btn.className = "quiz-option";
        btn.textContent = opt;
        btn.addEventListener("click", () => {
          if (item.dataset.done) return;
          item.dataset.done = "1";
          buttons.forEach((b) => (b.disabled = true));
          const isCorrect = oi === q.answer_index;
          btn.classList.add(isCorrect ? "correct" : "wrong");
          if (!isCorrect && buttons[q.answer_index]) {
            buttons[q.answer_index].classList.add("correct");
          }
          if (q.explanation) {
            const ex = document.createElement("div");
            ex.className = "quiz-explain";
            ex.textContent = q.explanation;
            item.appendChild(ex);
          }
          answered++;
          if (isCorrect) correct++;
          if (answered === quiz.length) {
            scoreBox.textContent = `You scored ${correct} / ${quiz.length}`;
            scoreBox.classList.remove("hidden");
          }
        });
        buttons.push(btn);
        opts.appendChild(btn);
      });
      item.appendChild(opts);
      root.appendChild(item);
    });
  }

  function renderImages(images) {
    const root = $("#images-content");
    root.innerHTML = "";
    if (!images.length) {
      root.innerHTML =
        '<p class="empty-state">No images were found in this document.</p>';
      return;
    }
    images.forEach((img) => {
      const fig = document.createElement("figure");
      fig.className = "image-card";
      const el = document.createElement("img");
      el.src = img.url;
      el.alt = img.caption || "Extracted image";
      el.loading = "lazy";
      const cap = document.createElement("figcaption");
      cap.textContent = img.caption || "";
      fig.append(el, cap);
      root.appendChild(fig);
    });
  }
})();
