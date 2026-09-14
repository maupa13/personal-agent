"use strict";

async function api(path, options) {
  const opts = { ...(options || {}) };
  const method = String(opts.method || "GET").toUpperCase();
  opts.headers = { ...(opts.headers || {}) };
  if (!["GET", "HEAD", "OPTIONS"].includes(method) && state.auth?.csrf_token)
    opts.headers["X-CSRF-Token"] = state.auth.csrf_token;
  let response;
  try {
    response = await fetch(path, opts);
  } catch (cause) {
    const error = new Error("network unavailable");
    error.status = 0;
    error.code = "network_unavailable";
    error.cause = cause;
    throw error;
  }
  let payload = {};
  try {
    payload = await response.json();
  } catch (_) {}
  if (!response.ok) {
    const error = new Error(payload.error || "request failed");
    error.status = response.status;
    error.code = payload.code;
    error.capability = payload.capability;
    error.request_id =
      payload.request_id || response.headers.get("X-Request-ID") || "";
    error.correlation_id =
      payload.correlation_id || response.headers.get("X-Correlation-ID") || "";
    error.duration_ms =
      payload.duration_ms ??
      Number(response.headers.get("X-PA-Duration-Ms") || 0);
    error.debug = payload.debug || null;
    throw error;
  }
  return payload;
}
function friendlyError(error) {
  const status = Number(error?.status || 0),
    code = String(error?.code || "");
  if (status === 0 || code === "network_unavailable")
    return {
      kind: "offline",
      title: tr("runtimeOfflineTitle"),
      detail: tr("runtimeOfflineDetail"),
    };
  if (status === 429 || code.includes("quota"))
    return {
      kind: "quota",
      title: tr("runtimeQuotaTitle"),
      detail: tr("runtimeQuotaDetail"),
    };
  if (status === 401)
    return {
      kind: "permission",
      title: langKey() === "en" ? "Sign in required" : "Нужно войти",
      detail:
        langKey() === "en"
          ? "Your session is not active. Sign in and retry."
          : "Сессия не активна. Войдите в аккаунт и повторите.",
    };
  if (status === 403)
    return {
      kind: "permission",
      title: tr("runtimePermissionTitle"),
      detail: tr("runtimePermissionDetail"),
    };
  if (status === 503 || status === 502 || status === 504)
    return {
      kind: "degraded",
      title: tr("runtimeDegradedTitle"),
      detail: tr("runtimeDegradedDetail"),
    };
  return {
    kind: "error",
    title: tr("runtimeErrorTitle"),
    detail: tr("runtimeErrorDetail"),
  };
}
function showRuntimeState(kind, title, detail, { retry = true } = {}) {
  state.connectionState = kind;
  const host = $("#runtimeStateBanner");
  if (!host) return;
  if (kind === "ready") {
    host.hidden = true;
    host.className = "runtime-state";
    return;
  }
  host.hidden = false;
  host.className = `runtime-state ${kind}`;
  setText("#runtimeStateTitle", title || "");
  setText("#runtimeStateDetail", detail || "");
  $("#runtimeRetry").hidden = !retry;
  const icons = {
    booting: "◌",
    starting: "◌",
    degraded: "△",
    offline: "×",
    quota: "!",
    permission: "!",
    error: "!",
  };
  setText("#runtimeStateIcon", icons[kind] || "!");
}
function updateRuntimeStateCopy() {
  const kind = state.connectionState;
  if (kind === "ready") return showRuntimeState("ready", "", "");
  if (kind === "booting" || kind === "starting")
    showRuntimeState(
      kind,
      tr("runtimeStartingTitle"),
      tr("runtimeStartingDetail"),
    );
  else if (kind === "offline")
    showRuntimeState(
      kind,
      tr("runtimeOfflineTitle"),
      tr("runtimeOfflineDetail"),
    );
  else if (kind === "quota")
    showRuntimeState(kind, tr("runtimeQuotaTitle"), tr("runtimeQuotaDetail"));
  else if (kind === "permission")
    showRuntimeState(
      kind,
      tr("runtimePermissionTitle"),
      tr("runtimePermissionDetail"),
    );
  else if (kind === "degraded")
    showRuntimeState(
      kind,
      tr("runtimeDegradedTitle"),
      tr("runtimeDegradedDetail"),
    );
  else if (kind === "error")
    showRuntimeState(kind, tr("runtimeErrorTitle"), tr("runtimeErrorDetail"));
}

function semanticVersion(value) {
  const match = String(value || "").match(/\d+\.\d+\.\d+/);
  return match ? match[0] : null;
}
function enforceUiVersion(systemVersion) {
  const backend = semanticVersion(systemVersion);
  const ui = semanticVersion(
    document.querySelector('meta[name="app-version"]')?.content || UI_VERSION,
  );
  if (!backend || !ui || backend === ui) return true;
  const key = `par-ui-reloaded-${backend}`;
  if (sessionStorage.getItem(key) !== "1") {
    sessionStorage.setItem(key, "1");
    const url = new URL(location.href);
    url.searchParams.set("ui", backend);
    location.replace(url.toString());
    return false;
  }
  setBanner(
    L(
      `Интерфейс ${ui} не совпадает с Core ${backend}. Выполните REPAIR и обновите страницу.`,
      `UI ${ui} does not match Core ${backend}. Run REPAIR and refresh the page.`,
    ),
    "warning",
  );
  return true;
}
const I18N = {
  ru: {
    brand: "Родной Агент",
    edition: "Локальная версия",
    pageTitle: "Родной Агент",
    newChat: "Новый чат",
    newProject: "Новый проект",
    search: "Поиск диалогов",
    projects: "Проекты",
    dialogs: "Диалоги",
    clear: "Очистить",
    files: "Файлы",
    code: "Код",
    tasks: "Задачи",
    settings: "Настройки",
    profile: "Профиль",
    help: "Помощь",
    feedback: "Обратная связь",
    admin: "Администрирование",
    logout: "Выйти",
    send: "Отправить",
    thinking: "Думаю…",
    placeholder: "Напишите сообщение…",
    share: "Поделиться",
    download: "Скачать",
    ready: "Готов",
    starting: "Запускается",
    offline: "Нет связи",
    retry: "Повторить",
    allChats: "Все чаты",
    archive: "Архив",
    now: "сейчас",
    minutes: "мин",
    hours: "ч",
    today: "Сегодня",
    yesterday: "Вчера",
    last7: "Последние 7 дней",
    earlier: "Ранее",
    nothingFound: "Ничего не найдено",
    welcomeTitle: "Чем займёмся?",
    welcomeText:
      "Родной Агент помогает решать задачи с интернетом, файлами, кодом и проверяемыми результатами. Технические детали остаются в администрировании.",
    scenarioHeading: "Попробуйте решить задачу",
    localStatus: "Локальный режим",
    serverStatus: "Свой сервер",
    topbarSubtitle: "Помощник, который делает работу вместе с вами",
    runtimeOfflineTitle: "Связь с агентом потеряна",
    runtimeOfflineDetail:
      "Ваши данные сохранены. Проверьте, что Personal Agent запущен, и повторите подключение.",
    runtimeStartingTitle: "Система запускается",
    runtimeStartingDetail:
      "Некоторые возможности ещё готовятся. Чат станет доступен сразу после проверки runtime.",
    runtimeDegradedTitle: "Есть временные ограничения",
    runtimeDegradedDetail:
      "Основной интерфейс доступен. Недоступный модуль можно проверить в настройках или диагностике.",
    runtimeQuotaTitle: "Достигнут лимит тарифа",
    runtimeQuotaDetail:
      "Данные не потеряны. Измените режим выполнения, дождитесь обновления лимита или выберите другой тариф.",
    runtimePermissionTitle: "Недостаточно прав",
    runtimePermissionDetail:
      "Эта операция недоступна вашей роли или текущему тарифу.",
    runtimeErrorTitle: "Не удалось выполнить запрос",
    runtimeErrorDetail:
      "Данные сохранены. Можно повторить после восстановления сервиса.",
    general: "Общие",
    data: "Данные",
    webSites: "Веб и сайты",
    capabilities: "Возможности",
    interfaceStyle: "Интерфейс и стиль",
    uiLanguage: "Язык интерфейса",
    responseLanguage: "Язык ответов",
    theme: "Тема",
    themeOcean: "Голубая",
    themeForest: "Светло-зелёная",
    themeSunset: "Закат",
    themeSand: "Песок",
    themeCoral: "Коралл",
    uiScale: "Масштаб интерфейса",
    scaleCompact: "Компактный",
    scaleNormal: "Обычный",
    scaleLarge: "Крупный",
    execution: "Где выполнять",
    tone: "Стиль ответа",
    save: "Сохранить",
    saved: "Сохранено",
    systemTheme: "Как в системе",
    dark: "Тёмная",
    light: "Светлая",
    answerLikeQuery: "Как в запросе",
    auto: "Авто",
    localOnly: "Только локально",
    preferLocal: "Предпочитать локально",
    remoteAllowed: "Можно удалённо",
    remoteOnly: "Только удалённо",
    toneNormal: "Обычный",
    toneFriendly: "Дружелюбный",
    toneIronic: "С иронией",
    toneMeme: "Мемный",
    toneSerious: "Очень серьёзный",
    toneExpert: "Экспертный",
    toneBrief: "Кратко",
    toneDetailed: "Подробно",
    settingsTitle: "Настройки",
    historyData: "История и данные",
    internetSearch: "Поиск в интернете",
    workspaceArtifacts: "Workspace и артефакты",
    workspaceHint:
      "Здесь можно и загрузить свой файл, и создать новый документ прямо в приложении, а затем прикрепить его в чат.",
    safeCode: "Код и безопасный запуск",
    tasksProgress: "Задачи и прогресс",
    helpTitle: "Помощь и возможности",
    tourBack: "Назад",
    tourNext: "Далее",
    tourDone: "Готово",
    tourSkip: "Пропустить",
  },
  en: {
    brand: "Personal Agent",
    edition: "Local edition",
    pageTitle: "Personal Agent",
    newChat: "New chat",
    newProject: "New project",
    search: "Search chats",
    projects: "Projects",
    dialogs: "Chats",
    clear: "Clear",
    files: "Files",
    code: "Code",
    tasks: "Tasks",
    settings: "Settings",
    profile: "Profile",
    help: "Help",
    feedback: "Feedback",
    admin: "Administration",
    logout: "Sign out",
    send: "Send",
    thinking: "Thinking…",
    placeholder: "Write a message…",
    share: "Share",
    download: "Download",
    ready: "Ready",
    starting: "Starting",
    offline: "Offline",
    retry: "Retry",
    allChats: "All chats",
    archive: "Archive",
    now: "now",
    minutes: "min",
    hours: "h",
    today: "Today",
    yesterday: "Yesterday",
    last7: "Last 7 days",
    earlier: "Earlier",
    nothingFound: "Nothing found",
    welcomeTitle: "What shall we do?",
    welcomeText:
      "Personal Agent helps with web research, files, code and verified results. Technical details stay in Administration.",
    scenarioHeading: "Try a real task",
    localStatus: "Local mode",
    serverStatus: "Self-hosted server",
    topbarSubtitle: "An assistant that works on the task with you",
    runtimeOfflineTitle: "Connection to Personal Agent was lost",
    runtimeOfflineDetail:
      "Your data is safe. Make sure Personal Agent is running and retry the connection.",
    runtimeStartingTitle: "System is starting",
    runtimeStartingDetail:
      "Some capabilities are still warming up. Chat will be available after runtime checks complete.",
    runtimeDegradedTitle: "Some capabilities are temporarily limited",
    runtimeDegradedDetail:
      "The main interface is available. Check the affected module in Settings or Diagnostics.",
    runtimeQuotaTitle: "Plan limit reached",
    runtimeQuotaDetail:
      "No data was lost. Change execution mode, wait for the limit to renew, or choose another plan.",
    runtimePermissionTitle: "Permission required",
    runtimePermissionDetail:
      "This action is unavailable for your role or current plan.",
    runtimeErrorTitle: "The request could not be completed",
    runtimeErrorDetail:
      "Your data is safe. You can retry after the service recovers.",
    general: "General",
    data: "Data",
    webSites: "Web & sites",
    capabilities: "Capabilities",
    interfaceStyle: "Interface & style",
    uiLanguage: "Interface language",
    responseLanguage: "Response language",
    theme: "Theme",
    themeOcean: "Ocean",
    themeForest: "Forest",
    themeSunset: "Sunset",
    themeSand: "Sand",
    themeCoral: "Coral",
    uiScale: "Interface scale",
    scaleCompact: "Compact",
    scaleNormal: "Normal",
    scaleLarge: "Large",
    execution: "Execution",
    tone: "Response style",
    save: "Save",
    saved: "Saved",
    systemTheme: "System",
    dark: "Dark",
    light: "Light",
    answerLikeQuery: "Match the request",
    auto: "Auto",
    localOnly: "Local only",
    preferLocal: "Prefer local",
    remoteAllowed: "Remote allowed",
    remoteOnly: "Remote only",
    toneNormal: "Normal",
    toneFriendly: "Friendly",
    toneIronic: "Ironic",
    toneMeme: "Meme",
    toneSerious: "Very serious",
    toneExpert: "Expert",
    toneBrief: "Brief",
    toneDetailed: "Detailed",
    settingsTitle: "Settings",
    historyData: "History & data",
    internetSearch: "Web search",
    workspaceArtifacts: "Workspace & artifacts",
    workspaceHint:
      "You can both upload your own file and create a new document right in the app, then attach it to the chat.",
    safeCode: "Code & safe execution",
    tasksProgress: "Tasks & progress",
    helpTitle: "Help & capabilities",
    tourBack: "Back",
    tourNext: "Next",
    tourDone: "Done",
    tourSkip: "Skip",
  },
};
function langKey() {
  return state.experiencePreferences?.ui_language === "en" ? "en" : "ru";
}
function tr(key) {
  const lang = langKey();
  return I18N[lang][key] ?? I18N.ru[key] ?? key;
}
function L(ru, en) {
  return langKey() === "en" ? en : ru;
}
function runtimeProfile() {
  return String(state.system?.runtime_profile || "local").toLowerCase() ===
    "server"
    ? "server"
    : "local";
}
function editionLabel(lang = langKey()) {
  return runtimeProfile() === "server"
    ? lang === "en"
      ? "Server edition"
      : "Серверная версия"
    : lang === "en"
      ? "Local edition"
      : "Локальная версия";
}
function defaultChatTitle() {
  return L("Новый чат", "New chat");
}
const THEME_COLOR_MAP = {
  system: "#0b0c0f",
  dark: "#0b0c0f",
  light: "#f6f7f9",
  ocean: "#0d1530",
  forest: "#0d180f",
  sunset: "#1e120c",
  sand: "#1b160d",
  coral: "#1f1015",
};
function effectiveTheme(value) {
  const theme = String(value || "system");
  if (theme === "system")
    return matchMedia("(prefers-color-scheme: light)").matches
      ? "light"
      : "dark";
  return theme;
}
function applyTheme(value) {
  const theme = effectiveTheme(
    value || state.experiencePreferences?.theme || "system",
  );
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("par-theme-preference", value || "system");
  const root = document.documentElement;
  const palette =
    {
      light: {
        bg: "#f6f7f9",
        panel: "#ffffff",
        panel2: "#f0f2f5",
        panel3: "#e7eaf0",
        line: "#dce0e7",
        line2: "#cdd3dc",
        muted: "#667085",
        text: "#16181d",
        soft: "#414753",
        accent: "#17191f",
      },
      dark: {
        bg: "#0b0c0f",
        panel: "#111318",
        panel2: "#161920",
        panel3: "#1d212a",
        line: "#272b35",
        line2: "#343945",
        muted: "#9096a3",
        text: "#f7f7f8",
        soft: "#c8ccd4",
        accent: "#f3f4f6",
      },
      ocean: {
        bg: "#08111d",
        panel: "#0e1727",
        panel2: "#132033",
        panel3: "#19304a",
        line: "#20344f",
        line2: "#2c4d77",
        muted: "#8eaad1",
        text: "#f3f8ff",
        soft: "#c8ddff",
        accent: "#76b7ff",
      },
      forest: {
        bg: "#08150e",
        panel: "#0e1c12",
        panel2: "#13261a",
        panel3: "#183524",
        line: "#23402c",
        line2: "#35604a",
        muted: "#8fbea0",
        text: "#f1fbf5",
        soft: "#cce8d4",
        accent: "#75d29f",
      },
      sunset: {
        bg: "#170f0c",
        panel: "#241713",
        panel2: "#2d1d18",
        panel3: "#39251f",
        line: "#4d2c24",
        line2: "#6a4035",
        muted: "#d2ab97",
        text: "#fff8f4",
        soft: "#f0d5c8",
        accent: "#ff9c66",
      },
      sand: {
        bg: "#17130c",
        panel: "#231d13",
        panel2: "#2c2418",
        panel3: "#382e1f",
        line: "#4a3d28",
        line2: "#685739",
        muted: "#d7c099",
        text: "#fffaf1",
        soft: "#f1e0c2",
        accent: "#e7c78c",
      },
      coral: {
        bg: "#171012",
        panel: "#241518",
        panel2: "#2e1b20",
        panel3: "#3a2329",
        line: "#4d2a34",
        line2: "#6f3b4a",
        muted: "#d9a8b8",
        text: "#fff7fa",
        soft: "#f4d0dc",
        accent: "#ff7e9b",
      },
    }[theme] || null;
  if (palette) {
    for (const [key, val] of Object.entries(palette))
      root.style.setProperty(`--${key}`, val);
  }
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute("content", THEME_COLOR_MAP[theme] || THEME_COLOR_MAP.dark);
}
function applyUiScale(value) {
  const scale = ["compact", "normal", "large"].includes(value)
    ? value
    : "normal";
  document.documentElement.dataset.uiScale = scale;
  localStorage.setItem("par-ui-scale", scale);
}
function executionLabel(value) {
  const key =
    {
      auto: "auto",
      local_only: "localOnly",
      prefer_local: "preferLocal",
      remote_allowed: "remoteAllowed",
      remote_only: "remoteOnly",
    }[value] || "auto";
  return tr(key);
}
function setText(selector, value) {
  const element = $(selector);
  if (element) element.textContent = value;
}
function setLabelText(controlId, value) {
  const control = $(controlId);
  const label = control?.closest("label");
  if (!label) return;
  for (const child of label.childNodes) {
    if (child.nodeType === Node.TEXT_NODE && child.textContent.trim()) {
      child.textContent = value;
      break;
    }
  }
}
function setOptionText(selectId, value, text) {
  const option = $(`${selectId} option[value="${value}"]`);
  if (option) option.textContent = text;
}
function applyLanguage(lang) {
  lang = lang === "en" ? "en" : "ru";
  if (!state.experiencePreferences) state.experiencePreferences = {};
  state.experiencePreferences.ui_language = lang;
  localStorage.setItem("par-ui-language", lang);
  document.documentElement.lang = lang;
  const t = I18N[lang];
  document.title = t.pageTitle;
  setText("#brandName", t.brand);
  setText("#brandEdition", editionLabel(lang));
  setText("#versionBrand", t.brand);
  setText("#topbarSubtitle", t.topbarSubtitle);
  setText("#newChat span:nth-child(2)", t.newChat);
  setText("#newFolder .new-project-label", t.newProject);
  if ($("#chatSearch")) {
    $("#chatSearch").placeholder = t.search;
    $("#chatSearch").setAttribute("aria-label", t.search);
  }
  setText(".project-heading .sidebar-section-title", t.projects);
  const titles = $$(".sidebar-section-row .sidebar-section-title");
  if (titles[1]) titles[1].textContent = t.dialogs;
  setText("#clearAllShortcut", t.clear);
  setText("#conversationEmpty", t.nothingFound);
  setText("#filesEntry span:nth-child(2)", t.files);
  setText("#codeEntry span:nth-child(2)", t.code);
  setText("#tasksEntry span:nth-child(2)", t.tasks);
  setText("#settingsEntry span:nth-child(2)", t.settings);
  setText("#archiveEntry span:nth-child(2)", t.archive);
  setText("#logoutEntry span:nth-child(2)", t.logout);
  setText("#helpEntry span:nth-child(2)", t.help);
  setText("#feedbackEntry span:nth-child(2)", t.feedback);
  setText("#adminEntry span:nth-child(2)", t.admin);
  if (input) input.placeholder = t.placeholder;
  setText("#send span:first-child", state.busy ? t.thinking : t.send);
  setText("#shareChatButton span:last-child", t.share);
  setText("#exportChatButton span:last-child", t.download);
  setText(
    "#sideHealth",
    state.connectionState === "ready"
      ? t.ready
      : $("#sideHealth")?.textContent || t.starting,
  );
  setText(
    "#settingsEyebrow",
    lang === "en" ? "PERSONAL AGENT" : "Родной Агент",
  );
  setText("#helpEyebrow", lang === "en" ? "PERSONAL AGENT" : "Родной Агент");
  setText("#settingsTitle", t.settingsTitle);
  setText("#helpTitle", t.helpTitle);
  const tabs = {
    general: t.general,
    data: t.data,
    web: t.webSites,
    files: t.files,
    code: t.code,
    tasks: t.tasks,
    capabilities: t.capabilities,
  };
  for (const [id, label] of Object.entries(tabs))
    setText(`[data-settings-tab="${id}"]`, label);
  setText('[data-settings-panel="general"] h3', t.interfaceStyle);
  setText('[data-settings-panel="data"] h3', t.historyData);
  setText('[data-settings-panel="web"] h3', t.internetSearch);
  setText('[data-settings-panel="files"] h3', t.workspaceArtifacts);
  setText('[data-settings-panel="code"] h3', t.safeCode);
  setText('[data-settings-panel="tasks"] h3', t.tasksProgress);
  setText('[data-settings-panel="capabilities"] h3', t.capabilities);
  setLabelText("#uiLanguage", t.uiLanguage);
  setLabelText("#responseLanguage", t.responseLanguage);
  setLabelText("#themeSelect", t.theme);
  setLabelText("#uiScale", t.uiScale);
  if ($("#webNewsInterestsLabel"))
    $("#webNewsInterestsLabel").childNodes[0].nodeValue =
      langKey() === "en"
        ? "News topics I care about "
        : "Темы новостей, которые мне интересны ";
  setLabelText("#executionPolicy", t.execution);
  setLabelText("#tonePreset", t.tone);
  setLabelText(
    "#profileNotes",
    lang === "en" ? "Personal preferences" : "Личные предпочтения",
  );
  if ($("#profileNotes"))
    $("#profileNotes").placeholder =
      lang === "en"
        ? "For example: keep answers brief, show prices in rubles, give the conclusion first"
        : "Например: отвечай кратко, цены показывай в рублях, сначала давай вывод, потом детали";
  setText(
    "#profileNotesHint",
    lang === "en"
      ? "This note is stored in your profile and used as a soft personal instruction in future answers."
      : "Эта заметка сохраняется в вашем профиле и используется как мягкая персональная инструкция в новых ответах.",
  );
  setText(
    "#artifactPanelLead",
    lang === "en"
      ? "Uploaded and generated files are stored in your isolated workspace and verified before delivery."
      : "Загруженные и созданные файлы хранятся в изолированном workspace вашего профиля и проверяются перед выдачей.",
  );
  setText("#artifactPanelHint", t.workspaceHint);
  setText("#saveExperiencePreferences", t.save);
  setOptionText("#responseLanguage", "auto", t.answerLikeQuery);
  setOptionText("#themeSelect", "system", t.systemTheme);
  setOptionText("#themeSelect", "dark", t.dark);
  setOptionText("#themeSelect", "light", t.light);
  setOptionText("#themeSelect", "ocean", t.themeOcean);
  setOptionText("#themeSelect", "forest", t.themeForest);
  setOptionText("#themeSelect", "sunset", t.themeSunset);
  setOptionText("#themeSelect", "sand", t.themeSand);
  setOptionText("#themeSelect", "coral", t.themeCoral);
  setOptionText("#uiScale", "compact", t.scaleCompact);
  setOptionText("#uiScale", "normal", t.scaleNormal);
  setOptionText("#uiScale", "large", t.scaleLarge);
  setOptionText("#executionPolicy", "auto", t.auto);
  setOptionText("#executionPolicy", "local_only", t.localOnly);
  setOptionText("#executionPolicy", "prefer_local", t.preferLocal);
  setOptionText("#executionPolicy", "remote_allowed", t.remoteAllowed);
  setOptionText("#executionPolicy", "remote_only", t.remoteOnly);
  setOptionText("#tonePreset", "normal", t.toneNormal);
  setOptionText("#tonePreset", "friendly", t.toneFriendly);
  setOptionText("#tonePreset", "ironic", t.toneIronic);
  setOptionText("#tonePreset", "meme", t.toneMeme + " ⚡");
  setOptionText("#tonePreset", "serious", t.toneSerious);
  setOptionText("#tonePreset", "expert", t.toneExpert);
  setOptionText("#tonePreset", "brief", t.toneBrief);
  setOptionText("#tonePreset", "detailed", t.toneDetailed);
  setText("#runtimeRetry", t.retry);
  setText("#tourSkip", t.tourSkip);
  setText("#tourBack", t.tourBack);
  if ($("#feedbackMessage"))
    $("#feedbackMessage").placeholder =
      lang === "en" ? "What should be improved?" : "Что улучшить?";
  if ($("#attachBtn")) {
    $("#attachBtn").setAttribute(
      "aria-label",
      lang === "en" ? "Files and tools" : "Файлы и инструменты",
    );
    $("#attachBtn").setAttribute(
      "title",
      lang === "en" ? "Files and tools" : "Файлы и инструменты",
    );
  }
  if ($("#sidebarResizer"))
    $("#sidebarResizer").setAttribute(
      "aria-label",
      lang === "en" ? "Resize sidebar" : "Изменить ширину боковой панели",
    );
  if ($("#collapseSidebar"))
    $("#collapseSidebar").setAttribute(
      "aria-label",
      lang === "en" ? "Collapse sidebar" : "Свернуть боковую панель",
    );
  if ($("#userGuideLink"))
    $("#userGuideLink").href =
      lang === "en" ? "/static/user-guide.en.html" : "/static/user-guide.html";
  if ($("#whyLink"))
    $("#whyLink").href =
      lang === "en" ? "/static/why.en.html" : "/static/why.html";
  if ($("#localSetupLink"))
    $("#localSetupLink").href =
      lang === "en"
        ? "/static/local-setup.en.html"
        : "/static/local-setup.html";
  translateExact($("#settingsModal"), lang);
  translateExact($("#helpBackdrop"), lang);
  translateExact($("#chatMenu"), lang);
  renderAll();
  renderToneMenu();
  updateRuntimeStateCopy();
}
const STATIC_EN = {
  Очистить: "Clear",
  Профиль: "Profile",
  "Администрирование ↗": "Administration ↗",
  "История диалогов хранится сервером и переживает очистку кэша браузера и перезапуск Core. Экспорт создаёт проверенный файл в вашем workspace.":
    "Conversation history is stored by the server and survives browser cache cleanup and Core restarts. Export creates a verified file in your workspace.",
  "Поделиться текущим чатом": "Share current chat",
  "Скачать текущий чат (.md)": "Download current chat (.md)",
  "Экспортировать все диалоги (.json)": "Export all chats (.json)",
  "Очистить текущий чат": "Clear current chat",
  "Удалить все диалоги": "Delete all chats",
  "Auto использует эти предпочтения при сценариях и обычных веб-запросах. Техническую стратегию сайтов настраивает администратор.":
    "Auto uses these preferences for scenarios and ordinary web requests. Technical site strategies are managed by the administrator.",
  "Область поиска": "Search scope",
  "Весь интернет": "Entire web",
  "Предпочитать российские сайты": "Prefer Russian sites",
  "Только выбранные сайты": "Selected sites only",
  "Город / регион": "City / region",
  "Искать только на сайтах": "Search only these sites",
  "Не использовать сайты": "Do not use sites",
  Маркетплейсы: "Marketplaces",
  Госреестры: "Government registries",
  "Сайты по списку": "Sites by list",
  "Категория поиска": "Search category",
  "Поднимать российские источники выше, когда они релевантны":
    "Prefer Russian sources when relevant",
  "Сохранить настройки поиска": "Save search preferences",
  "Загруженные и созданные файлы хранятся в изолированном workspace вашего профиля и проверяются перед выдачей.":
    "Uploaded and generated files are stored in your isolated workspace and verified before delivery.",
  Формат: "Format",
  "Имя файла": "File name",
  Содержимое: "Content",
  "Создать и проверить": "Create and verify",
  "Загрузить файл": "Upload file",
  "Код выполняется в отдельном sandbox-worker без сети и без доступа к Docker socket, Core, базе данных или вашим секретам.":
    "Code runs in an isolated sandbox worker without network access and without access to Docker socket, Core, the database or your secrets.",
  Язык: "Language",
  "Лимит времени": "Time limit",
  Запустить: "Run",
  Отменить: "Cancel",
  "Задачи и прогресс": "Tasks & progress",
  "Обновить задачи": "Refresh tasks",
  "Помощь и возможности": "Help & capabilities",
  "Пройти обучение": "Start guided tour",
  Руководство: "Guide",
  "Установить локальный AI": "Set up local AI",
  Подтверждение: "Confirmation",
  Отмена: "Cancel",
  Продолжить: "Continue",
  "Обратная связь": "Feedback",
  Тип: "Type",
  Оценка: "Rating",
  Сообщение: "Message",
  Отправить: "Send",
  "Версия интерфейса": "UI version",
  "Должна совпадать с Core": "Must match Core",
  "Локальный AI-помощник, который умеет работать с интернетом, файлами, кодом и проверяемыми результатами — без необходимости разбираться в инфраструктуре.":
    "A local-first AI assistant for web, files, code and verified results — without requiring infrastructure knowledge.",
  "▶ Пройти обучение": "▶ Start guided tour",
  "Пошагово покажем интерфейс за пару минут.":
    "A short interactive walkthrough of the interface.",
  "Основные сценарии и ответы на вопросы.":
    "Core workflows and common questions.",
  "Что умеет Родной Агент": "What Personal Agent can do",
  "Чат, интернет, файлы, код, задачи и приватность.":
    "Chat, web, files, code, tasks and privacy.",
  "Почему Родной Агент": "Why Personal Agent",
  "Чем local-first агент отличается от обычного AI-чата.":
    "How a local-first agent differs from a regular AI chat.",
  "Пошаговый старт на Windows: Docker, модель, проверка и LAN.":
    "Step-by-step Windows setup: runtime, model, verification and LAN.",
  "Ненавязчиво сообщить идею, ошибку или оценить качество.":
    "Send an idea, bug report or quality rating without leaving the product.",
  "Не прикладывайте пароли, API-ключи и приватные документы. Сообщение сохранится локально/на вашем сервере для администратора.":
    "Do not include passwords, API keys or private documents. The message is stored locally/on your server for an administrator.",
  Идея: "Idea",
  Ошибка: "Bug",
  "Качество ответа": "Answer quality",
  Интерфейс: "Interface",
  Другое: "Other",
  "Без оценки": "No rating",
  "5 — отлично": "5 — excellent",
  "1 — плохо": "1 — poor",
  "Что улучшить?": "What should be improved?",
  Русский: "Russian",
  "«Только локально» запрещает скрытый remote fallback. «Мемный» меняет подачу, но не требования к точности и проверке.":
    "“Local only” prevents hidden remote fallback. “Meme” changes presentation, never accuracy or verification requirements.",
};
function translateExact(container, lang) {
  if (!container) return;
  const forward = STATIC_EN,
    reverse = Object.fromEntries(
      Object.entries(forward).map(([a, b]) => [b, a]),
    );
  const map = lang === "en" ? forward : reverse;
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  for (const textNode of nodes) {
    const raw = textNode.textContent,
      trimmed = raw.trim();
    if (!trimmed || !map[trimmed]) continue;
    textNode.textContent = raw.replace(trimmed, map[trimmed]);
  }
}
function renderExperiencePreferences() {
  const p = state.experiencePreferences || {};
  if ($("#uiLanguage")) $("#uiLanguage").value = p.ui_language || "ru";
  if ($("#responseLanguage"))
    $("#responseLanguage").value = p.response_language || "auto";
  if ($("#themeSelect")) {
    $("#themeSelect").value = p.theme || "system";
    const themeKeys = {
      ocean: "theme_ocean",
      forest: "theme_forest",
      sunset: "theme_sunset",
      sand: "theme_sand",
      coral: "theme_coral",
    };
    for (const option of $("#themeSelect").options) {
      const key = themeKeys[option.value];
      const locked = !!key && !entitlementEnabled(key);
      option.disabled = locked;
      option.title = locked
        ? L("Доступно на более высоком тарифе", "Available on a higher plan")
        : "";
    }
  }
  if ($("#uiScale")) $("#uiScale").value = p.ui_scale || "normal";
  if ($("#executionPolicy"))
    $("#executionPolicy").value = p.execution_policy || "auto";
  if ($("#tonePreset")) $("#tonePreset").value = p.tone || "normal";
  if ($("#profileNotes")) $("#profileNotes").value = p.profile_notes || "";
  if ($("#executionQuickLabel"))
    $("#executionQuickLabel").textContent = executionLabel(
      p.execution_policy || "auto",
    );
  applyTheme(p.theme || "system");
  applyUiScale(p.ui_scale || "normal");
  applyLanguage(p.ui_language || "ru");
}
async function loadExperiencePreferences() {
  try {
    const payload = await api("/api/preferences/experience");
    state.experiencePreferences = payload.preferences || {};
    renderExperiencePreferences();
  } catch (_) {
    state.experiencePreferences = {
      ui_language: localStorage.getItem("par-ui-language") || "ru",
      response_language: "auto",
      theme: localStorage.getItem("par-theme-preference") || "system",
      execution_policy: "auto",
      tone: "normal",
      ui_scale: localStorage.getItem("par-ui-scale") || "normal",
      profile_notes: "",
    };
    renderExperiencePreferences();
  }
}
async function saveExperiencePreferences() {
  const out = $("#experienceState");
  try {
    const payload = await api("/api/preferences/experience", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ui_language: $("#uiLanguage").value,
        response_language: $("#responseLanguage").value,
        theme: $("#themeSelect").value,
        ui_scale: $("#uiScale").value,
        execution_policy: $("#executionPolicy").value,
        tone: $("#tonePreset").value,
        profile_notes: $("#profileNotes")?.value || "",
      }),
    });
    state.experiencePreferences = payload.preferences;
    renderExperiencePreferences();
    out.textContent = tr("saved");
    out.className = "job-state completed";
    toast(
      langKey() === "en" ? "Settings saved" : "Настройки сохранены",
      "success",
    );
  } catch (error) {
    out.textContent = friendlyError(error).title;
    out.className = "job-state failed";
  }
}
async function shareCurrent() {
  const c = current();
  if (!c || !c.messages.length) {
    toast(
      L(
        "В текущем диалоге пока нечем делиться",
        "There is nothing to share in this chat yet",
      ),
      "info",
    );
    return;
  }
  const ttl = await selectAction(
    L("Поделиться диалогом", "Share chat"),
    L(
      "Будет создан отдельный read-only снимок. Ссылка не даёт доступ к аккаунту, другим чатам или workspace.",
      "A separate read-only snapshot will be created. The link does not grant access to the account, other chats or workspace.",
    ),
    [
      { value: "86400", label: L("1 день", "1 day") },
      { value: "604800", label: L("7 дней", "7 days") },
      { value: "2592000", label: L("30 дней", "30 days") },
    ],
    "604800",
    L("Создать ссылку", "Create link"),
  );
  if (ttl === null) return;
  try {
    const payload = await api(`/api/conversations/${c.id}/share`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ttl_seconds: Number(ttl) }),
    });
    const share = payload.share;
    if (navigator.share) {
      try {
        await navigator.share({
          title: share.title,
          text: `${tr("brand")}: ${share.title}`,
          url: share.url,
        });
        toast(
          L("Открыто системное меню «Поделиться»", "System share menu opened"),
          "success",
        );
        return;
      } catch (error) {
        if (error?.name === "AbortError") return;
      }
    }
    await copyText(share.url);
    setBanner(
      L(
        "Создан приватный снимок диалога. Ссылка не даёт доступ к аккаунту или workspace.",
        "A private chat snapshot was created. The link does not grant access to the account or workspace.",
      ),
      "info",
    );
  } catch (error) {
    toast(error.message, "error");
  }
}
async function sendFeedback() {
  const out = $("#feedbackState");
  try {
    const payload = await api("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        category: $("#feedbackCategory").value,
        rating: $("#feedbackRating").value || null,
        message: $("#feedbackMessage").value,
        page: location.pathname,
      }),
    });
    $("#feedbackMessage").value = "";
    out.textContent = L("Спасибо! Сохранено.", "Thank you! Saved.");
    out.className = "job-state completed";
    toast(
      L("Спасибо за обратную связь", "Thanks for your feedback"),
      "success",
    );
  } catch (error) {
    out.textContent = error.message;
    out.className = "job-state failed";
  }
}
