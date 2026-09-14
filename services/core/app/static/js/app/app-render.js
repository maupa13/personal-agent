"use strict";

function renderFolders() {
  const host = $("#folders");
  if (!host) return;
  host.replaceChildren();
  const all = node(
    "button",
    `folder-item${!state.activeFolderId ? " active" : ""}`,
  );
  all.type = "button";
  all.append(
    node("span", "folder-icon", "▦"),
    node("span", "folder-copy", tr("allChats")),
  );
  all.onclick = () => {
    state.activeFolderId = null;
    saveStore();
    renderAll();
  };
  host.append(all);
  for (const folder of state.folders) {
    const row = node(
      "div",
      `folder-item${state.activeFolderId === folder.id ? " active" : ""}`,
    );
    row.dataset.folderId = folder.id;
    const select = node("button", "folder-select");
    select.type = "button";
    const copy = node("span", "folder-copy");
    copy.append(
      node("strong", "", folder.name),
      node("small", "", folder.conversation_count || 0),
    );
    select.append(node("span", "folder-icon", "▱"), copy);
    select.onclick = () => {
      state.activeFolderId = folder.id;
      saveStore();
      renderAll();
    };
    const actions = node("span", "folder-actions");
    const rename = node("button", "folder-mini", "✎");
    rename.type = "button";
    rename.title = L("Переименовать проект", "Rename project");
    rename.onclick = (event) => {
      event.stopPropagation();
      renameFolder(folder);
    };
    const remove = node("button", "folder-mini", "×");
    remove.type = "button";
    remove.title = L("Удалить проект", "Delete project");
    remove.onclick = (event) => {
      event.stopPropagation();
      deleteFolder(folder);
    };
    actions.append(rename, remove);
    row.append(select, actions);
    host.append(row);
  }
  const archivedCount = state.conversations.filter((c) => c.archived_at).length;
  const archive = node(
    "button",
    `folder-item archive-item${state.activeFolderId === "__archived__" ? " active" : ""}`,
  );
  archive.type = "button";
  archive.append(
    node("span", "folder-icon", "□"),
    node(
      "span",
      "folder-copy",
      `${tr("archive")}${archivedCount ? ` · ${archivedCount}` : ""}`,
    ),
  );
  archive.onclick = async () => {
    state.activeFolderId = "__archived__";
    const first = state.conversations.find((c) => c.archived_at);
    if (first) await loadConversation(first.id, false);
    saveStore();
    renderAll();
  };
  host.append(archive);
}
function renderConversations() {
  conversationList.replaceChildren();
  renderFolders();
  const visible = state.conversations.filter((c) => {
    const archive = Boolean(c.archived_at);
    const scope =
      state.activeFolderId === "__archived__"
        ? archive
        : !archive &&
          (!state.activeFolderId || c.folder_id === state.activeFolderId);
    return scope && (!state.search || state.searchMatches?.has(c.id));
  });
  const groups = new Map();
  for (const c of visible) {
    const key = dateGroup(c.updatedAt);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(c);
  }
  for (const [label, items] of groups) {
    const section = node("div", "conversation-group");
    section.append(node("div", "conversation-group-title", label));
    for (const conversation of items) {
      const row = node(
        "div",
        `conversation-item${conversation.id === state.activeId ? " active" : ""}`,
      );
      row.dataset.id = conversation.id;
      row.setAttribute("role", "button");
      row.tabIndex = 0;
      row.onclick = () => selectConversation(conversation.id);
      row.onkeydown = (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectConversation(conversation.id);
        }
      };
      const icon = node(
        "button",
        "conversation-icon",
        conversation.pinned_at ? "◆" : "◌",
      );
      icon.type = "button";
      icon.title = conversation.pinned_at
        ? L("Открепить", "Unpin")
        : L("Закрепить", "Pin");
      icon.onclick = async (event) => {
        event.stopPropagation();
        await setConversationPinned(conversation, !conversation.pinned_at);
      };
      const copy = node("span", "conversation-copy");
      copy.append(
        node("strong", "", conversation.title),
        node("small", "", relativeTime(conversation.updatedAt)),
      );
      const remove = node("button", "conversation-delete", "×");
      remove.type = "button";
      remove.title = L("Удалить диалог", "Delete chat");
      remove.onclick = async (event) => {
        event.stopPropagation();
        if (
          await confirmAction(
            L("Удалить диалог?", "Delete chat?"),
            L(
              `«${conversation.title}» будет удалён из истории.`,
              `“${conversation.title}” will be removed from history.`,
            ),
            L("Удалить", "Delete"),
            "danger",
          )
        ) {
          try {
            await deleteConversationNow(conversation.id);
            toast(L("Диалог удалён", "Chat deleted"), "success");
          } catch (error) {
            toast(error.message, "warning");
          }
        }
      };
      row.append(icon, copy, remove);
      section.append(row);
    }
    conversationList.append(section);
  }
  $("#conversationEmpty").hidden = visible.length !== 0;
}
function capChip(label, status) {
  const element = node("span", `cap-chip ${status}`);
  element.append(node("span", "cap-dot", ""), node("span", "", label));
  return element;
}
function capabilityVisualStatus(status) {
  if (status === "ready") return "ready";
  if (status === "admin") return "ready";
  if (status === "degraded") return "degraded";
  if (status === "planned") return "planned";
  return "planned";
}
function capabilityStatusText(capability, entitled) {
  const status = String(capability?.status || "planned");
  if (!entitled)
    return L("Недоступно на текущем тарифе", "Unavailable on the current plan");
  if (status === "ready")
    return L("Доступно в текущей сборке", "Available in this build");
  if (status === "admin")
    return L(
      "Доступно через администратора",
      "Available through administration",
    );
  if (status === "degraded" || status === "unavailable")
    return L(
      "Доступно с ограничениями текущего окружения",
      "Limited by the current environment",
    );
  return L(
    "Подключается отдельным продуктовым слоем",
    "Coming in a separate product layer",
  );
}
function capabilityBadgeText(capability, entitled) {
  const status = String(capability?.status || "planned");
  if (!entitled) return L("Тариф", "Plan");
  if (status === "ready") return L("Готово", "Ready");
  if (status === "admin") return L("Admin", "Admin");
  if (status === "degraded" || status === "unavailable")
    return L("Ограничено", "Limited");
  return L("Запланировано", "Planned");
}
const WELCOME_PROMPTS = {
  ru: [
    [
      "preset",
      "explain",
      "Объяснить",
      "Разобрать сложную тему простыми словами",
    ],
    ["preset", "write", "Написать", "Подготовить текст, план или идею"],
    [
      "preset",
      "analyze",
      "Проанализировать",
      "Сравнить варианты и сделать вывод",
    ],
    [
      "intent",
      "search",
      "Найти",
      "Найти актуальные данные и источники в интернете",
    ],
    [
      "intent",
      "research",
      "Исследовать",
      "Собрать несколько источников, сравнить и сделать вывод",
    ],
  ],
  en: [
    [
      "preset",
      "explain",
      "Explain",
      "Break down a complex topic in plain language",
    ],
    ["preset", "write", "Write", "Prepare text, a plan or an idea"],
    ["preset", "analyze", "Analyze", "Compare options and make a conclusion"],
    [
      "intent",
      "search",
      "Find",
      "Find current information and sources on the web",
    ],
    [
      "intent",
      "research",
      "Research",
      "Collect several sources, compare them and make a conclusion",
    ],
  ],
};
const SCENARIO_I18N = {
  clothing: [
    "Choose clothes",
    "Find items by size, budget, season and style",
    "Help me choose clothes for my measurements and budget.",
  ],
  procurement: [
    "Find procurements",
    "Find and filter suitable procurements and tenders",
    "Find suitable procurements for my topic.",
  ],
  real_estate: [
    "Find property",
    "Collect and compare suitable real-estate options",
    "Help me find and compare suitable property options.",
  ],
  gift: [
    "Choose a gift",
    "Find personalized gift ideas and buying options",
    "Help me choose a good gift.",
  ],
  product: [
    "Choose a product",
    "Compare products by real requirements and sources",
    "Help me choose the best product for my needs.",
  ],
  travel: [
    "Plan a trip",
    "Build an itinerary, options and practical trip details",
    "Help me plan a trip.",
  ],
  news: [
    "Understand the news",
    "Collect fresh sources and explain what happened",
    "Collect fresh news on my topic and explain the key points.",
  ],
};
function scenarioDisplay(item) {
  if (langKey() !== "en") return item;
  const en = SCENARIO_I18N[item.id];
  return en
    ? { ...item, title: en[0], description: en[1], example_prompt: en[2] }
    : item;
}
function renderWelcome() {
  const wrap = node("div", "welcome");
  wrap.append(
    node("div", "welcome-mark", "PA"),
    node("h1", "", tr("welcomeTitle")),
    node("p", "", tr("welcomeText")),
  );
  const cards = node("div", "starter-grid");
  const prompts = WELCOME_PROMPTS[langKey()];
  for (const [kind, id, title, description] of prompts) {
    const active =
      kind === "preset" ? state.preset === id : state.intentHint === id;
    const button = node("button", `starter-card${active ? " active" : ""}`);
    button.type = "button";
    button.dataset[kind === "preset" ? "preset" : "intent"] = id;
    button.append(node("strong", "", title), node("span", "", description));
    button.onclick = () => {
      state.scenarioId = null;
      if (kind === "preset") {
        state.intentHint = "auto";
        state.preset = id;
        localStorage.setItem(PRESET_KEY, id);
        toast(`${L("Режим задачи", "Task preset")}: ${title}`, "success");
      } else {
        state.preset = "none";
        localStorage.setItem(PRESET_KEY, "none");
        state.intentHint = id;
        setBanner(
          id === "research"
            ? L(
                "Следующий запрос будет выполнен как исследование с несколькими веб-источниками.",
                "The next request will run as research using multiple web sources.",
              )
            : L(
                "Следующий запрос будет выполнен с веб-поиском.",
                "The next request will use web search.",
              ),
          "info",
        );
        toast(`${L("Веб-режим", "Web mode")}: ${title}`, "success");
      }
      renderAll();
      input.focus();
    };
    cards.appendChild(button);
  }
  if (state.scenarios.length) {
    wrap.append(node("h2", "scenario-heading", tr("scenarioHeading")));
    const gallery = node("div", "scenario-grid");
    for (const raw of state.scenarios.slice(0, 8)) {
      const item = scenarioDisplay(raw);
      const card = node(
        "button",
        `scenario-card${state.scenarioId === item.id ? " active" : ""}`,
      );
      card.type = "button";
      card.dataset.scenario = item.id;
      card.append(node("span", "scenario-icon", item.icon || "◇"));
      const copy = node("span", "scenario-copy");
      copy.append(
        node("strong", "", item.title),
        node("small", "", item.description),
      );
      card.append(copy);
      card.onclick = () => {
        state.scenarioId = item.id;
        state.preset = "none";
        state.intentHint = "auto";
        localStorage.setItem(PRESET_KEY, "none");
        input.value = item.example_prompt || "";
        resizeInput();
        renderAll();
        input.focus();
        input.setSelectionRange(input.value.length, input.value.length);
        toast(
          `${langKey() === "en" ? "Assistant" : "Помощник"}: ${item.title}`,
          "success",
        );
      };
      gallery.append(card);
    }
    wrap.append(gallery);
  }
  const caps = node("div", "capability-row");
  const capabilities = state.system?.capabilities || {
    chat: { status: "ready", label: "Чат" },
    web: { status: "ready", label: "Веб" },
    files: { status: "ready", label: "Файлы" },
  };
  const capLabels = {
    chat: L("Чат", "Chat"),
    web: L("Веб", "Web"),
    research: L("Исследование", "Research"),
    files: L("Файлы", "Files"),
    code: L("Код", "Code"),
    billing: L("Подписка", "Subscription"),
    tasks: L("Задачи", "Tasks"),
    deployment: L("Развёртывание", "Deployment"),
    media: L("Медиа", "Media"),
  };
  for (const [key, capability] of Object.entries(capabilities).slice(0, 4))
    caps.append(
      capChip(
        capLabels[key] || capability.label || L("Возможность", "Capability"),
        capabilityVisualStatus(capability.status),
      ),
    );
  wrap.append(cards, caps);
  chat.appendChild(wrap);
}

function appendInlineMarkdown(host, text) {
  const pattern =
    /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\(https?:\/\/[^\s)]+\)|\*[^*\n]+\*)/g;
  let cursor = 0;
  for (const match of text.matchAll(pattern)) {
    if (match.index > cursor)
      host.append(document.createTextNode(text.slice(cursor, match.index)));
    const token = match[0];
    if (token.startsWith("**")) {
      const strong = document.createElement("strong");
      strong.textContent = token.slice(2, -2);
      host.append(strong);
    } else if (token.startsWith("`")) {
      const code = document.createElement("code");
      code.className = "inline-code";
      code.textContent = token.slice(1, -1);
      host.append(code);
    } else if (token.startsWith("[")) {
      const parts = token.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/);
      if (parts) {
        const link = document.createElement("a");
        link.href = parts[2];
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = parts[1];
        host.append(link);
      } else host.append(document.createTextNode(token));
    } else if (token.startsWith("*")) {
      const em = document.createElement("em");
      em.textContent = token.slice(1, -1);
      host.append(em);
    }
    cursor = (match.index || 0) + token.length;
  }
  if (cursor < text.length)
    host.append(document.createTextNode(text.slice(cursor)));
}
function renderTextBlock(host, text) {
  const lines = text.replace(/\r/g, "").split("\n");
  let list = null;
  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) {
      list = null;
      continue;
    }
    const heading = line.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      list = null;
      const h = document.createElement(
        `h${Math.min(4, heading[1].length + 2)}`,
      );
      appendInlineMarkdown(h, heading[2]);
      host.append(h);
      continue;
    }
    const bullet = line.match(/^[-*]\s+(.+)$/);
    if (bullet) {
      if (!list || list.tagName !== "UL") {
        list = document.createElement("ul");
        host.append(list);
      }
      const li = document.createElement("li");
      appendInlineMarkdown(li, bullet[1]);
      list.append(li);
      continue;
    }
    const ordered = line.match(/^\d+[.)]\s+(.+)$/);
    if (ordered) {
      if (!list || list.tagName !== "OL") {
        list = document.createElement("ol");
        host.append(list);
      }
      const li = document.createElement("li");
      appendInlineMarkdown(li, ordered[1]);
      list.append(li);
      continue;
    }
    list = null;
    if (line.startsWith("> ")) {
      const quote = document.createElement("blockquote");
      appendInlineMarkdown(quote, line.slice(2));
      host.append(quote);
      continue;
    }
    const paragraph = document.createElement("p");
    appendInlineMarkdown(paragraph, line);
    host.append(paragraph);
  }
}
function renderRichText(host, content) {
  host.replaceChildren();
  const text = String(content || "");
  const fence = /```([^\n`]*)\n([\s\S]*?)```/g;
  let cursor = 0;
  for (const match of text.matchAll(fence)) {
    if ((match.index || 0) > cursor)
      renderTextBlock(host, text.slice(cursor, match.index));
    const block = node("div", "code-block");
    const header = node("div", "code-header");
    const language = (match[1] || "code").trim() || "code";
    const copy = node("button", "code-copy", L("Копировать", "Copy"));
    copy.type = "button";
    const codeText = match[2].replace(/\n$/, "");
    copy.onclick = () => copyText(codeText, copy);
    header.append(node("span", "", language), copy);
    const pre = document.createElement("pre");
    const code = document.createElement("code");
    code.textContent = codeText;
    pre.appendChild(code);
    block.append(header, pre);
    host.append(block);
    cursor = (match.index || 0) + match[0].length;
  }
  if (cursor < text.length) renderTextBlock(host, text.slice(cursor));
  if (!host.childNodes.length) host.textContent = text;
}
function sourceKindLabel(kind) {
  const labels = {
    news: ["Новость", "News"],
    product: ["Товар", "Product"],
    real_estate: ["Объект", "Property"],
    procurement: ["Закупка", "Procurement"],
    marketplace: ["Маркетплейс", "Marketplace"],
    registry: ["Реестр", "Registry"],
    source: ["Источник", "Source"],
  };
  const pair = labels[kind] || labels.source;
  return L(pair[0], pair[1]);
}
function sourceHost(source) {
  if (source.domain) return source.domain;
  try {
    return new URL(source.url).hostname.replace(/^www\./, "");
  } catch (_) {
    return "";
  }
}
function sourceDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 32);
  return date.toLocaleString(langKey() === "en" ? "en-US" : "ru-RU", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}
function renderSources(message) {
  const sources = Array.isArray(message.sources)
    ? message.sources.filter((source) => source && source.url)
    : [];
  if (!sources.length) return null;
  const kinds = new Set(sources.map((source) => source.kind || "source"));
  const mainKind = kinds.size === 1 ? [...kinds][0] : "source";
  const wrap = node(
    "section",
    `message-sources result-section kind-${mainKind}`,
  );
  wrap.setAttribute("aria-label", L("Найденные материалы", "Found results"));
  const heading = node("div", "result-section-head");
  const title = node(
    "div",
    "sources-title",
    `${mainKind === "news" ? L("Найденные новости", "News found") : mainKind === "product" ? L("Найденные варианты", "Options found") : mainKind === "real_estate" ? L("Найденные объекты", "Properties found") : mainKind === "procurement" ? L("Найденные закупки", "Procurements found") : mainKind === "marketplace" ? L("Найденные товары", "Products found") : mainKind === "registry" ? L("Найденные записи", "Records found") : L("Источники", "Sources")} · ${sources.length}`,
  );
  heading.append(title);
  wrap.append(heading);
  const list = node("div", "source-list result-card-grid");
  for (const [index, source] of sources.entries()) {
    const kind = [
      "news",
      "product",
      "real_estate",
      "procurement",
      "marketplace",
      "registry",
    ].includes(source.kind)
      ? source.kind
      : "source";
    const link = node("a", `source-card result-card kind-${kind}`);
    link.href = source.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.style.setProperty("--result-index", String(index));
    const top = node("div", "result-card-top");
    const badge = node(
      "span",
      `result-kind result-kind-${kind}`,
      sourceKindLabel(kind),
    );
    const domain = node("span", "result-domain", sourceHost(source));
    top.append(badge, domain);
    const label = node(
      "strong",
      "result-title",
      source.title || sourceHost(source) || source.url,
    );
    link.append(top, label);
    if (source.summary) {
      const summary = node("p", "result-summary", source.summary);
      link.append(summary);
    }
    const meta = node("div", "result-meta");
    const date = sourceDate(source.published_date);
    if (date) meta.append(node("span", "result-date", date));
    if (source.price) meta.append(node("span", "result-price", source.price));
    const method =
      source.strategy && source.strategy !== "web" ? source.strategy : "";
    if (method) meta.append(node("span", "result-strategy", method));
    meta.append(node("span", "result-open", "↗"));
    link.append(meta);
    list.append(link);
  }
  wrap.append(list);
  return wrap;
}
function renderMessageAttachments(message) {
  const items = Array.isArray(message?.attachments) ? message.attachments : [];
  if (!items.length) return null;
  const wrap = node("div", "message-attachments");
  for (const item of items) {
    const link = node("a", "message-file");
    link.href = item.download_url || `/api/files/${item.artifact_id}/download`;
    link.target = "_blank";
    link.rel = "noopener";
    link.append(
      node("span", "", String(item.format || "file").toUpperCase()),
      node("span", "", item.name || L("Файл", "File")),
    );
    wrap.append(link);
  }
  return wrap;
}
function renderPendingFiles() {
  const bar = $("#attachmentBar");
  if (!bar) return;
  bar.replaceChildren();
  bar.hidden = state.pendingFiles.length === 0;
  for (const item of state.pendingFiles) {
    const chip = node("div", "attachment-chip");
    chip.append(node("span", "", String(item.format || "file").toUpperCase()));
    const copy = node("span", "");
    copy.append(
      node("strong", "", item.name),
      node("small", "", prettySize(item.size)),
    );
    const remove = node("button", "", "×");
    remove.type = "button";
    remove.title = L(
      "Убрать из следующего сообщения",
      "Remove from the next message",
    );
    remove.onclick = () => {
      state.pendingFiles = state.pendingFiles.filter(
        (x) => x.artifact_id !== item.artifact_id,
      );
      renderPendingFiles();
    };
    chip.append(copy, remove);
    bar.append(chip);
  }
}
async function uploadSelectedFiles(files) {
  const selected = Array.from(files || []);
  if (selected.length > 6) {
    toast(
      L(
        "За один раз можно загрузить не больше 6 файлов",
        "No more than 6 files can be uploaded at once",
      ),
      "error",
    );
    return;
  }
  for (const file of selected) {
    try {
      setBanner(
        `${L("Загружаю и проверяю", "Uploading and verifying")} ${file.name}…`,
        "info",
      );
      const response = await fetch("/api/files/upload", {
        method: "POST",
        headers: {
          "Content-Type": file.type || "application/octet-stream",
          "X-PA-Filename": encodeURIComponent(file.name),
          ...(state.auth?.csrf_token
            ? { "X-CSRF-Token": state.auth.csrf_token }
            : {}),
        },
        body: file,
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok)
        throw new Error(
          payload.error ||
            L("Не удалось загрузить файл", "Could not upload file"),
        );
      state.pendingFiles.push(payload.artifact);
      state.pendingFiles = state.pendingFiles.slice(-12);
      renderPendingFiles();
      toast(`${file.name}: ${L("файл проверен", "file verified")}`, "success");
    } catch (error) {
      toast(`${file.name}: ${error.message}`, "error");
    }
  }
  setBanner(
    state.pendingFiles.length
      ? L(
          "Файлы прикреплены. Задайте вопрос или отправьте их для анализа.",
          "Files attached. Ask a question or send them for analysis.",
        )
      : "",
  );
  await loadArtifacts();
}
function openFilePicker() {
  $("#fileInput")?.click();
}
function renderArtifactList() {
  const host = $("#artifactList");
  if (!host) return;
  host.replaceChildren();
  if (!state.artifacts.length) {
    host.append(
      node(
        "div",
        "muted",
        L(
          "В workspace пока нет файлов.",
          "There are no files in the workspace yet.",
        ),
      ),
    );
    return;
  }
  for (const item of state.artifacts) {
    const row = node("div", "artifact-row");
    row.dataset.artifactId = item.artifact_id;
    row.append(
      node("div", "artifact-kind", String(item.format || "file").toUpperCase()),
    );
    const copy = node("div", "artifact-copy");
    copy.append(
      node("strong", "", item.name),
      node(
        "small",
        "",
        `v${item.version} · ${prettySize(item.size)} · ${item.validation_status}`,
      ),
    );
    const actions = node("div", "artifact-actions");
    const attach = node("button", "", L("В чат", "Attach"));
    attach.type = "button";
    attach.onclick = () => {
      if (!state.pendingFiles.some((x) => x.artifact_id === item.artifact_id))
        state.pendingFiles.push(item);
      renderPendingFiles();
      closeSettings();
      input.focus();
      toast(L("Файл прикреплён", "File attached"), "success");
    };
    const download = node("a", "", L("Скачать", "Download"));
    download.href = item.download_url;
    download.target = "_blank";
    download.rel = "noopener";
    const remove = node("button", "", L("Удалить", "Delete"));
    remove.type = "button";
    remove.onclick = async () => {
      if (
        !(await confirmAction(
          L("Удалить файл?", "Delete file?"),
          L(
            `«${item.name}» будет удалён из workspace.`,
            `“${item.name}” will be deleted from the workspace.`,
          ),
          L("Удалить", "Delete"),
          "danger",
        ))
      )
        return;
      try {
        await api(`/api/files/${item.artifact_id}`, { method: "DELETE" });
        state.pendingFiles = state.pendingFiles.filter(
          (x) => x.artifact_id !== item.artifact_id,
        );
        renderPendingFiles();
        await loadArtifacts();
        toast(L("Файл удалён", "File deleted"), "success");
      } catch (error) {
        toast(error.message, "error");
      }
    };
    actions.append(attach, download, remove);
    row.append(copy, actions);
    host.append(row);
  }
}
async function loadArtifacts() {
  try {
    const result = await api("/api/files");
    state.artifacts = result.artifacts || [];
    renderArtifactList();
  } catch (error) {
    state.artifacts = [];
    renderArtifactList();
    if (
      state.system?.debug_diagnostics ||
      state.auth?.user?.role === "OWNER" ||
      state.auth?.user?.role === "ADMIN"
    )
      console.error("artifact.list.failed", {
        message: error?.message || String(error),
        request_id: error?.request_id || "",
        correlation_id: error?.correlation_id || "",
        duration_ms: error?.duration_ms || 0,
      });
  }
}
async function createArtifactFromUi() {
  const fmt = $("#artifactFormat").value;
  let name = $("#artifactName").value.trim() || `document.${fmt}`;
  if (!name.toLowerCase().endsWith(`.${fmt}`))
    name = `${name.replace(/\.[^.]+$/, "")}.${fmt}`;
  let content = $("#artifactContent").value;
  if (fmt === "json") {
    try {
      content = JSON.parse(content);
    } catch (_) {
      toast(L("Для JSON введите корректный JSON", "Enter valid JSON"), "error");
      return;
    }
  }
  if (fmt === "csv") {
    content = {
      rows: content
        .split(/\r?\n/)
        .filter(Boolean)
        .map((line) => line.split(",").map((cell) => cell.trim())),
    };
  }
  try {
    const result = await api("/api/files/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ format: fmt, name, content }),
    });
    state.pendingFiles.push(result.artifact);
    renderPendingFiles();
    await loadArtifacts();
    toast(
      `${result.artifact.name}: ${L("создан и проверен", "created and verified")}`,
      "success",
    );
  } catch (error) {
    toast(error.message, "error");
  }
}

function formatDuration(ms) {
  const value = Number(ms || 0);
  if (!Number.isFinite(value) || value < 0) return "";
  if (value < 1000) return `${Math.round(value)} ms`;
  return `${(value / 1000).toFixed(value < 10000 ? 1 : 0)} s`;
}
function renderQuickReplies(message) {
  const options = Array.isArray(message?.metadata?.quick_replies)
    ? message.metadata.quick_replies.filter(Boolean).slice(0, 12)
    : [];
  if (!options.length) return null;
  const wrap = node("div", "quick-replies");
  for (const option of options) {
    const button = node("button", "quick-reply", String(option));
    button.type = "button";
    button.onclick = () => {
      input.value = String(option);
      resizeInput();
      input.focus();
      sendRequest({ addUser: true });
    };
    wrap.append(button);
  }
  return wrap;
}
function renderMessageMeta(message) {
  if (
    message.role !== "assistant" ||
    !message.metadata ||
    typeof message.metadata !== "object"
  )
    return null;
  const meta = message.metadata;
  const duration = formatDuration(meta.duration_ms);
  if (!duration && !meta.debug) return null;
  const wrap = node("div", "message-meta");
  if (duration) wrap.append(node("span", "message-meta-chip", `⏱ ${duration}`));
  if (Number(meta.source_count) > 0)
    wrap.append(
      node(
        "span",
        "message-meta-chip",
        `${L("источников", "sources")}: ${Number(meta.source_count)}`,
      ),
    );
  if (meta.debug && typeof meta.debug === "object") {
    const details = document.createElement("details");
    details.className = "message-debug";
    const summary = node("summary", "", L("Диагностика", "Diagnostics"));
    details.append(summary);
    const native = meta.inference_native || {};
    const rows = [
      ["request", meta.request_id],
      ["correlation", meta.correlation_id],
      ["intent", meta.intent],
      ["routing", formatDuration(meta.routing_ms)],
      ["web", formatDuration(meta.web_ms)],
      ["inference", formatDuration(meta.inference_ms)],
      ["model load", formatDuration(native.load_ms)],
      ["prompt eval", formatDuration(native.prompt_eval_ms)],
      ["generation", formatDuration(native.generation_ms)],
      ["output tokens", native.output_tokens],
      ["tokens/sec", native.tokens_per_sec],
      ["target", meta.debug.execution_target],
      ["execution", meta.debug.execution_policy],
    ];
    for (const [key, value] of rows) {
      if (value !== undefined && value !== null && String(value) !== "")
        details.append(node("div", "message-debug-row", `${key}: ${value}`));
    }
    wrap.append(details);
  }
  return wrap;
}

function renderMessageActions(message, index) {
  const actions = node("div", "message-actions");
  const copy = node("button", "message-action", L("Копировать", "Copy"));
  copy.type = "button";
  copy.onclick = () => copyText(message.content, copy);
  actions.append(copy);
  if (message.role === "assistant" && message.kind !== "capability") {
    const regenerate = node(
      "button",
      "message-action",
      L("Повторить", "Retry"),
    );
    regenerate.type = "button";
    regenerate.onclick = () => regenerateAt(index);
    actions.append(regenerate);
  }
  return actions;
}
function progressiveReveal(bubble, message) {
  const text = String(message.content || "");
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce || text.length < 90) {
    renderRichText(bubble, text);
    state.animateMessageId = null;
    return;
  }
  bubble.replaceChildren();
  bubble.classList.add("progressive-reveal");
  bubble.setAttribute("aria-busy", "true");
  const started = performance.now();
  const targetMs = Math.max(500, Math.min(1800, text.length * 2.1));
  let last = -1;
  function tick(ts) {
    if (!bubble.isConnected || state.animateMessageId !== message.id) return;
    const progress = Math.min(1, (ts - started) / targetMs);
    const eased = 1 - Math.pow(1 - progress, 2.2);
    let pos = Math.max(last + 1, Math.floor(text.length * eased));
    if (pos < text.length) {
      const next = text.indexOf(" ", pos);
      if (next > pos && next - pos < 18) pos = next;
    }
    pos = Math.min(text.length, pos);
    if (pos !== last) {
      bubble.textContent = text.slice(0, pos);
      last = pos;
      if (pos % 180 < 24)
        document.scrollingElement?.scrollTo({
          top: document.scrollingElement.scrollHeight,
          behavior: "instant",
        });
    }
    if (progress < 1) requestAnimationFrame(tick);
    else {
      bubble.classList.remove("progressive-reveal");
      bubble.removeAttribute("aria-busy");
      renderRichText(bubble, text);
      state.animateMessageId = null;
    }
  }
  requestAnimationFrame(tick);
}
function renderChat() {
  chat.replaceChildren();
  const conversation = current();
  $("#conversationTitle").textContent =
    conversation?.title || defaultChatTitle();
  if (!conversation || conversation.messages.length === 0) {
    renderWelcome();
    return;
  }
  conversation.messages.forEach((message, index) => {
    const row = node(
      "article",
      `message-row ${message.role}${message.kind === "capability" ? " capability-message" : ""}`,
    );
    row.dataset.messageId = message.id;
    const avatar = node("div", "avatar", message.role === "user" ? "" : "PA");
    const body = node("div", "message-body");
    if (message.role !== "user")
      body.append(node("div", "message-author", tr("brand")));
    const bubble = node("div", `msg ${message.role}`);
    if (message.role === "assistant" && state.animateMessageId === message.id)
      progressiveReveal(bubble, message);
    else if (message.role === "assistant")
      renderRichText(bubble, message.content);
    else bubble.textContent = message.content;
    body.append(bubble);
    const quickReplies = renderQuickReplies(message);
    if (quickReplies) body.append(quickReplies);
    const attachments = renderMessageAttachments(message);
    if (attachments) body.append(attachments);
    const sources = renderSources(message);
    if (sources) body.append(sources);
    const meta = renderMessageMeta(message);
    if (meta) body.append(meta);
    body.append(renderMessageActions(message, index));
    row.append(avatar, body);
    chat.appendChild(row);
  });
  requestAnimationFrame(() => {
    document.scrollingElement?.scrollTo({
      top: document.scrollingElement.scrollHeight,
      behavior: "instant",
    });
  });
}
function entitlementEnabled(key) {
  const item = state.auth?.entitlements?.features?.[key];
  return item ? !!item.enabled : true;
}
function renderModes() {
  modes.replaceChildren();
  let defs = state.system?.modes || [];
  defs = defs.filter((mode) => entitlementEnabled(`mode_${mode.id}`));
  if (!defs.length)
    defs = (state.system?.modes || []).filter((mode) => mode.id === "auto");
  if (!defs.some((item) => item.id === state.mode)) {
    state.mode = defs[0]?.id || "auto";
    localStorage.setItem(MODE_KEY, state.mode);
  }
  const currentMode = defs.find((item) => item.id === state.mode) || defs[0];
  if (currentMode)
    $("#modeButton").firstChild.textContent =
      `${currentMode.label || currentMode.id} `;
  for (const mode of defs) {
    const button = node(
      "button",
      `mode${mode.id === state.mode ? " active" : ""}`,
      mode.label || mode.id,
    );
    button.type = "button";
    button.dataset.mode = mode.id;
    button.title = mode.description || "";
    button.onclick = () => {
      state.mode = mode.id;
      localStorage.setItem(MODE_KEY, mode.id);
      modes.hidden = true;
      $("#modeButton").setAttribute("aria-expanded", "false");
      renderModes();
      toast(`${L("Режим", "Mode")}: ${mode.label || mode.id}`);
    };
    modes.appendChild(button);
  }
}
function renderToneMenu() {
  const host = $("#toneMenu");
  if (!host) return;
  host.replaceChildren();
  const defs = state.system?.tones || [];
  const current = state.experiencePreferences?.tone || "normal";
  const labels =
    langKey() === "en"
      ? {
          normal: "Normal",
          friendly: "Friendly",
          ironic: "Ironic",
          meme: "Meme",
          serious: "Very serious",
          expert: "Expert",
          brief: "Brief",
          detailed: "Detailed",
        }
      : {
          normal: "Обычный",
          friendly: "Дружелюбный",
          ironic: "С иронией",
          meme: "Мемный",
          serious: "Очень серьёзный",
          expert: "Экспертный",
          brief: "Кратко",
          detailed: "Подробно",
        };
  const button = $("#toneButton");
  if (button) {
    button.textContent =
      current === "normal"
        ? "✨"
        : `${current === "meme" ? "😂" : current === "ironic" ? "😏" : current === "serious" ? "🧐" : current === "expert" ? "🎓" : current === "brief" ? "⚡" : current === "detailed" ? "📚" : "✨"}`;
    button.title = `${langKey() === "en" ? "Style" : "Стиль"}: ${labels[current] || current}`;
  }
  for (const tone of defs) {
    const item = node(
      "button",
      `mode${tone.id === current ? " active" : ""}`,
      labels[tone.id] || tone.label || tone.id,
    );
    item.type = "button";
    item.onclick = async () => {
      try {
        const payload = await api("/api/preferences/experience", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tone: tone.id }),
        });
        state.experiencePreferences = payload.preferences;
        renderExperiencePreferences();
        host.hidden = true;
        $("#toneButton").setAttribute("aria-expanded", "false");
        toast(
          `${langKey() === "en" ? "Style" : "Стиль"}: ${labels[tone.id] || tone.id}`,
          "success",
        );
      } catch (error) {
        toast(friendlyError(error).title, "error");
      }
    };
    host.append(item);
  }
}
function renderCapabilities() {
  const host = $("#capabilitySettings");
  if (!host) return;
  host.replaceChildren();
  for (const [key, capability] of Object.entries(
    state.system?.capabilities || {},
  )) {
    const row = node("div", "capability-setting");
    const feature = key === "files" ? "files_read" : key;
    const entitled = entitlementEnabled(feature);
    const copy = node("div", "");
    copy.append(
      node("strong", "", capability.label || key),
      node("span", "", capabilityStatusText(capability, entitled)),
    );
    const statusClass = !entitled
      ? "locked"
      : capabilityVisualStatus(capability.status);
    row.append(
      copy,
      node(
        "span",
        `capability-badge ${statusClass}`,
        capabilityBadgeText(capability, entitled),
      ),
    );
    host.append(row);
  }
}
function renderAll() {
  renderConversations();
  renderChat();
  renderModes();
  renderCapabilities();
  renderPendingFiles();
  renderArtifactList();
}
function addMessage(message) {
  const conversation = current();
  if (!conversation) return null;
  const clean = cleanMessage(message);
  conversation.messages.push(clean);
  conversation.messages = conversation.messages.slice(-MAX_MESSAGES);
  if (!conversation.customTitle)
    conversation.title = titleFromMessages(conversation.messages);
  conversation.updatedAt = now();
  saveStore();
  renderAll();
  return clean;
}
function setBanner(text, type = "info") {
  const banner = $("#capabilityBanner");
  if (!text) {
    banner.hidden = true;
    banner.textContent = "";
    return;
  }
  banner.hidden = false;
  banner.className = `capability-banner ${type}`;
  banner.textContent = text;
}
function setBusy(busy) {
  state.busy = busy;
  send.disabled = busy;
  input.disabled = busy;
  chat.setAttribute("aria-busy", String(busy));
  send.classList.toggle("working", busy);
  send.querySelector("span:first-child").textContent = busy
    ? tr("thinking")
    : tr("send");
}
function setThinking(show) {
  $("#thinkingRow")?.remove();
  if (!show) return;
  const row = node("article", "message-row assistant thinking-row");
  row.id = "thinkingRow";
  const avatar = node("div", "avatar", "PA");
  const body = node("div", "message-body");
  body.append(node("div", "message-author", tr("brand")));
  const dots = node("div", "thinking-dots");
  dots.append(node("span"), node("span"), node("span"));
  body.append(dots);
  row.append(avatar, body);
  chat.append(row);
  requestAnimationFrame(() => row.scrollIntoView({ block: "end" }));
}
