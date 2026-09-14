"use strict";

const UI_VERSION = "1.0.3";
const STORAGE_KEY = "par-conversations-v2";
const LEGACY_STORAGE_KEY = "par-conversations-v1";
const ACTIVE_KEY = "par-active-conversation";
const MODE_KEY = "par-mode";
const PRESET_KEY = "par-preset";
const LEGACY_CHAT = "par-chat";
const MAX_CONVERSATIONS = 100;
const MAX_MESSAGES = 200;

const state = {
  mode: localStorage.getItem(MODE_KEY) || "auto",
  preset: localStorage.getItem(PRESET_KEY) || "none",
  intentHint: "auto",
  auth: null,
  conversations: [],
  folders: [],
  activeFolderId: null,
  activeId: null,
  legacyConversations: [],
  system: null,
  search: "",
  searchMatches: null,
  busy: false,
  pendingFiles: [],
  artifacts: [],
  codeJobId: null,
  codePollTimer: null,
  taskMode: null,
  tasks: [],
  taskPollTimers: {},
  scenarios: [],
  scenarioId: null,
  webPreferences: null,
  experiencePreferences: null,
  connectionState: "booting",
  lastRuntimeError: null,
  animateMessageId: null,
};

const WEB_CATEGORY_PRESETS = {
  broad: {
    label: "Весь интернет",
    label_en: "Entire web",
    search_scope: "internet",
    allowed_domains: [],
    excluded_domains: [],
    news_interests: [],
    prefer_russian: true,
  },
  marketplaces: {
    label: "Маркетплейсы",
    label_en: "Marketplaces",
    search_scope: "selected",
    allowed_domains: [
      "wildberries.ru",
      "ozon.ru",
      "market.yandex.ru",
      "aliexpress.ru",
      "lamoda.ru",
      "megamarket.ru",
    ],
    excluded_domains: [],
    news_interests: [],
    prefer_russian: true,
  },
  registries: {
    label: "Госреестры",
    label_en: "Government registries",
    search_scope: "selected",
    allowed_domains: [
      "zakupki.gov.ru",
      "egrul.nalog.ru",
      "egrip.nalog.ru",
      "rosreestr.gov.ru",
      "fssp.gov.ru",
      "nalog.gov.ru",
    ],
    excluded_domains: [],
    news_interests: [],
    prefer_russian: true,
  },
  list: {
    label: "Сайты по списку",
    label_en: "Sites by list",
    search_scope: "selected",
    allowed_domains: [],
    excluded_domains: [],
    news_interests: [],
    prefer_russian: true,
  },
};
const ARTIFACT_FORMATS = [
  "txt",
  "md",
  "json",
  "csv",
  "pdf",
  "docx",
  "xlsx",
  "pptx",
];

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));
const chat = $("#chat");
const modes = $("#modes");
const input = $("#input");
const send = $("#send");
const conversationList = $("#conversations");

function uid() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  return `c-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
function now() {
  return Date.now();
}
function current() {
  return state.conversations.find((c) => c.id === state.activeId) || null;
}
function cleanMessage(message) {
  return {
    id: String(message?.id || uid()),
    role: message?.role === "assistant" ? "assistant" : "user",
    content: String(message?.content || "").slice(0, 50000),
    kind: String(message?.kind || "message").slice(0, 40),
    sources: Array.isArray(message?.sources)
      ? message.sources.slice(0, 12).map((source) => ({
          title: String(source?.title || "").slice(0, 300),
          url: String(source?.url || "").slice(0, 2000),
          domain: String(source?.domain || "").slice(0, 255),
          status: String(source?.status || "").slice(0, 40),
          strategy: String(source?.strategy || "").slice(0, 40),
          published_date: String(source?.published_date || "").slice(0, 100),
          summary: String(source?.summary || "").slice(0, 500),
          kind: String(source?.kind || "source").slice(0, 40),
          price: String(source?.price || "").slice(0, 64),
        }))
      : [],
    attachments: Array.isArray(message?.attachments)
      ? message.attachments
          .slice(0, 12)
          .map((item) => ({
            artifact_id: String(item?.artifact_id || "").slice(0, 64),
            name: String(item?.name || L("Файл", "File")).slice(0, 180),
            format: String(item?.format || "").slice(0, 12),
            size: Number(item?.size) || 0,
            download_url: String(item?.download_url || "").slice(0, 400),
          }))
          .filter((item) => item.artifact_id)
      : [],
    metadata:
      message?.metadata && typeof message.metadata === "object"
        ? JSON.parse(JSON.stringify(message.metadata))
        : {},
    createdAt: Number(message?.createdAt || message?.created_at) || now(),
  };
}
function normalizeConversation(conversation) {
  return {
    id: String(conversation?.id || uid()),
    title:
      String(conversation?.title || defaultChatTitle())
        .replace(/\s+/g, " ")
        .trim()
        .slice(0, 80) || defaultChatTitle(),
    messages: Array.isArray(conversation?.messages)
      ? conversation.messages.slice(-MAX_MESSAGES).map(cleanMessage)
      : [],
    updatedAt: Number(conversation?.updatedAt) || now(),
    customTitle: Boolean(
      conversation?.customTitle || conversation?.custom_title,
    ),
    folder_id: conversation?.folder_id || null,
    pinned_at: conversation?.pinned_at || null,
    archived_at: conversation?.archived_at || null,
    message_count: Number(conversation?.message_count) || 0,
    preview: String(conversation?.preview || ""),
  };
}
function titleFromMessages(messages) {
  const first = (messages || []).find(
    (m) =>
      m.role === "user" &&
      m.kind !== "capability-request" &&
      String(m.content || "").trim(),
  );
  if (!first) return defaultChatTitle();
  const text = String(first.content).replace(/\s+/g, " ").trim();
  return text.length > 46 ? `${text.slice(0, 46)}…` : text;
}
function loadJson(key, fallback) {
  try {
    const parsed = JSON.parse(localStorage.getItem(key) || "");
    return parsed ?? fallback;
  } catch (_) {
    return fallback;
  }
}
function loadStore() {
  let raw = loadJson(STORAGE_KEY, null);
  if (!Array.isArray(raw)) raw = loadJson(LEGACY_STORAGE_KEY, []);
  if (!Array.isArray(raw)) {
    const legacy = loadJson(LEGACY_CHAT, []);
    raw =
      Array.isArray(legacy) && legacy.length
        ? [
            {
              title: titleFromMessages(legacy),
              messages: legacy,
              updatedAt: now(),
            },
          ]
        : [];
  }
  state.legacyConversations = Array.isArray(raw)
    ? raw.map(normalizeConversation)
    : [];
  state.activeId = localStorage.getItem(ACTIVE_KEY) || null;
  state.activeFolderId = localStorage.getItem("par-active-folder") || null;
}
function normalizeDomainLines(values) {
  return Array.isArray(values)
    ? values
        .map((value) =>
          String(value || "")
            .toLowerCase()
            .trim()
            .replace(/^https?:\/\//, "")
            .replace(/\/.*$/, "")
            .replace(/^\./, ""),
        )
        .filter(Boolean)
    : [];
}
function sameDomainList(left, right) {
  const a = normalizeDomainLines(left),
    b = normalizeDomainLines(right);
  return a.length === b.length && a.every((item, index) => item === b[index]);
}
function webPresetFromPreferences(preferences) {
  const scope = String(preferences?.search_scope || "internet");
  const allowed = normalizeDomainLines(preferences?.allowed_domains || []);
  const excluded = normalizeDomainLines(preferences?.excluded_domains || []);
  const interests = Array.isArray(preferences?.news_interests)
    ? preferences.news_interests
        .map((item) => String(item || "").trim())
        .filter(Boolean)
    : [];
  const preferRussian = preferences?.prefer_russian !== false;
  for (const [key, preset] of Object.entries(WEB_CATEGORY_PRESETS)) {
    if (scope !== preset.search_scope) continue;
    if (!sameDomainList(allowed, preset.allowed_domains)) continue;
    if (!sameDomainList(excluded, preset.excluded_domains)) continue;
    if (JSON.stringify(interests) !== JSON.stringify(preset.news_interests))
      continue;
    if (Boolean(preferRussian) !== Boolean(preset.prefer_russian)) continue;
    return key;
  }
  return scope === "selected" ? "list" : "broad";
}
function currentWebPreferences() {
  return {
    search_scope:
      $("#webSearchScope")?.value ||
      state.webPreferences?.search_scope ||
      "internet",
    allowed_domains: linesToDomains($("#webAllowedDomains")?.value || ""),
    excluded_domains: linesToDomains($("#webExcludedDomains")?.value || ""),
    news_interests: String($("#webNewsInterests")?.value || "")
      .split(/\r?\n|,/)
      .map((item) => item.trim())
      .filter(Boolean),
    prefer_russian: $("#webPreferRussian")
      ? $("#webPreferRussian").checked
      : state.webPreferences?.prefer_russian !== false,
  };
}
function renderWebPresetButtons() {
  const current = webPresetFromPreferences(currentWebPreferences());
  $$("[data-web-preset]").forEach((button) =>
    button.classList.toggle("active", button.dataset.webPreset === current),
  );
}
function applyWebPreset(key) {
  const preset = WEB_CATEGORY_PRESETS[key];
  if (!preset) return;
  if ($("#webSearchScope")) $("#webSearchScope").value = preset.search_scope;
  if ($("#webAllowedDomains"))
    $("#webAllowedDomains").value = (preset.allowed_domains || []).join("\n");
  if ($("#webExcludedDomains"))
    $("#webExcludedDomains").value = (preset.excluded_domains || []).join("\n");
  if ($("#webNewsInterests"))
    $("#webNewsInterests").value = (preset.news_interests || []).join("\n");
  if ($("#webPreferRussian"))
    $("#webPreferRussian").checked = Boolean(preset.prefer_russian);
  renderWebPresetButtons();
  toast(
    `${L("Категория поиска", "Search category")}: ${langKey() === "en" ? preset.label_en || preset.label : preset.label}`,
    "success",
  );
}
function applyArtifactFormat(format, updateName = true) {
  const field = $("#artifactFormat");
  const nameField = $("#artifactName");
  if (field) field.value = format;
  if (updateName && nameField) {
    nameField.value =
      (nameField.value || "document").replace(/\.[^.]+$/, "") + `.${format}`;
  }
  $$("[data-artifact-preset]").forEach((button) =>
    button.classList.toggle("active", button.dataset.artifactPreset === format),
  );
}
function saveStore() {
  state.conversations.sort(
    (a, b) =>
      (b.updatedAt || b.updated_at || 0) - (a.updatedAt || a.updated_at || 0),
  );
  if (state.activeId) localStorage.setItem(ACTIVE_KEY, state.activeId);
  else localStorage.removeItem(ACTIVE_KEY);
  if (state.activeFolderId)
    localStorage.setItem("par-active-folder", state.activeFolderId);
  else localStorage.removeItem("par-active-folder");
}
function serverConversation(raw) {
  return normalizeConversation({
    id: raw.id,
    title: raw.title,
    messages: raw.messages || [],
    updatedAt: raw.updated_at || raw.updatedAt,
    customTitle: raw.custom_title || raw.customTitle,
    folder_id: raw.folder_id,
    pinned_at: raw.pinned_at,
    archived_at: raw.archived_at,
    message_count: raw.message_count,
    preview: raw.preview,
  });
}
async function loadServerStore(query = "") {
  const params = new URLSearchParams({ include_archived: "1" });
  if (query) params.set("q", query);
  let payload = await api(`/api/conversations?${params.toString()}`);
  if (
    !query &&
    !(payload.conversations || []).length &&
    state.legacyConversations.length
  ) {
    try {
      await api("/api/conversations/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conversations: state.legacyConversations }),
      });
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(LEGACY_STORAGE_KEY);
      localStorage.removeItem(LEGACY_CHAT);
      payload = await api("/api/conversations?include_archived=1");
    } catch (error) {
      toast(
        `${L("Не удалось перенести старую историю", "Could not migrate the previous history")}: ${error.message}`,
        "warning",
      );
    }
  }
  state.folders = payload.folders || state.folders || [];
  if (query) {
    state.searchMatches = new Set(
      (payload.conversations || []).map((item) => item.id),
    );
    renderAll();
    return;
  }
  state.searchMatches = null;
  state.conversations = (payload.conversations || []).map(serverConversation);
  if (!state.conversations.length) {
    const created = await api("/api/conversations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: defaultChatTitle(),
        folder_id: state.activeFolderId || null,
      }),
    });
    state.conversations = [serverConversation(created.conversation)];
  }
  if (!state.conversations.some((c) => c.id === state.activeId))
    state.activeId = state.conversations[0]?.id || null;
  if (state.activeId) await loadConversation(state.activeId, false);
  saveStore();
  renderAll();
}
async function loadConversation(conversationId, render = true) {
  const payload = await api(
    `/api/conversations/${encodeURIComponent(conversationId)}`,
  );
  const full = serverConversation(payload.conversation);
  const index = state.conversations.findIndex((c) => c.id === conversationId);
  if (index >= 0) state.conversations[index] = full;
  else state.conversations.unshift(full);
  state.activeId = conversationId;
  saveStore();
  if (render) renderAll();
  return full;
}
async function newConversation(render = true) {
  const active = current();
  if (active && active.messages?.length === 0) {
    state.activeId = active.id;
  } else {
    const created = await api("/api/conversations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: defaultChatTitle(),
        folder_id: state.activeFolderId || null,
      }),
    });
    state.conversations.unshift(serverConversation(created.conversation));
    state.activeId = created.conversation.id;
  }
  saveStore();
  if (render) {
    renderAll();
    input.focus();
    closeSidebar();
  }
}
async function selectConversation(conversationId) {
  if (!state.conversations.some((c) => c.id === conversationId)) return;
  await loadConversation(conversationId, true);
  closeSidebar();
}
async function deleteConversationNow(conversationId) {
  await api(`/api/conversations/${encodeURIComponent(conversationId)}`, {
    method: "DELETE",
  });
  state.conversations = state.conversations.filter(
    (c) => c.id !== conversationId,
  );
  if (state.activeId === conversationId)
    state.activeId = state.conversations[0]?.id || null;
  if (!state.activeId) await newConversation(false);
  else await loadConversation(state.activeId, false);
  saveStore();
  renderAll();
}
async function clearCurrentNow() {
  const c = current();
  if (!c) return;
  const payload = await api(`/api/conversations/${c.id}/clear`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  });
  const full = serverConversation(payload.conversation);
  const index = state.conversations.findIndex((x) => x.id === c.id);
  if (index >= 0) state.conversations[index] = full;
  renderAll();
}
async function clearAllNow() {
  const ids = state.conversations.map((c) => c.id);
  for (const id of ids) {
    try {
      await api(`/api/conversations/${id}`, { method: "DELETE" });
    } catch (_) {}
  }
  state.conversations = [];
  state.activeId = null;
  await newConversation(false);
  renderAll();
}
function prettySize(value) {
  const bytes = Math.max(0, Number(value) || 0);
  if (bytes < 1024) return `${Math.round(bytes)} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let amount = bytes / 1024,
    unit = units[0];
  for (let i = 1; i < units.length && amount >= 1024; i++) {
    amount /= 1024;
    unit = units[i];
  }
  const digits = amount >= 100 ? 0 : amount >= 10 ? 1 : 2;
  return `${amount.toFixed(digits)} ${unit}`;
}
function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = String(text);
  return element;
}
function relativeTime(timestamp) {
  const value = Number(timestamp || 0);
  if (!value) return "";
  const date = new Date(value);
  const nowDate = new Date();
  const sameDay =
    date.getFullYear() === nowDate.getFullYear() &&
    date.getMonth() === nowDate.getMonth() &&
    date.getDate() === nowDate.getDate();
  if (sameDay)
    return date.toLocaleTimeString(langKey() === "en" ? "en-US" : "ru-RU", {
      hour: "2-digit",
      minute: "2-digit",
    });
  return date.toLocaleDateString(langKey() === "en" ? "en-US" : "ru-RU", {
    day: "2-digit",
    month: "short",
  });
}
function dateGroup(timestamp) {
  const d = new Date(Number(timestamp || 0));
  const nowD = new Date();
  const day = new Date(nowD.getFullYear(), nowD.getMonth(), nowD.getDate());
  const other = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const delta = Math.floor((day - other) / 86400000);
  if (delta <= 0) return tr("today");
  if (delta === 1) return tr("yesterday");
  if (delta < 7) return tr("last7");
  return tr("earlier");
}
