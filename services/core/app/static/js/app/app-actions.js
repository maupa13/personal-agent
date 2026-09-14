"use strict";

async function init() {
  loadStore();
  bindEvents();
  resizeInput();
  showRuntimeState(
    "booting",
    tr("runtimeStartingTitle"),
    tr("runtimeStartingDetail"),
  );
  chat.setAttribute("aria-busy", "true");
  try {
    state.system = await api("/api/system");
    try {
      state.auth = await api("/api/auth/me");
    } catch (_) {
      state.auth = { ok: false, mode: state.system?.auth?.mode || "personal" };
    }
    if (!enforceUiVersion(state.system.version)) return;
    if (state.system?.auth?.mode === "accounts" && !state.auth?.user) {
      const next = location.pathname + location.search + location.hash;
      location.replace(`/login?next=${encodeURIComponent(next)}`);
      return;
    }
    $("#version").textContent = `v${state.system.version}`;
    $("#settingsVersion").textContent = `v${state.system.version}`;
    const account = $("#accountEntry");
    if (account) {
      if (state.auth?.user) {
        account.href = "/account";
        account.querySelector(".account-label").textContent =
          state.auth.user.display_name || L("Аккаунт", "Account");
      } else if (state.system?.auth?.mode === "accounts") {
        account.href = "/login";
        account.querySelector(".account-label").textContent = L(
          "Войти",
          "Sign in",
        );
      } else {
        account.href = "/account";
        account.querySelector(".account-label").textContent = L(
          "Локальный профиль",
          "Local profile",
        );
      }
    }
    const role = String(state.auth?.user?.role || "").toUpperCase();
    const roleAdmin = ["OWNER", "ADMIN"].includes(role);
    const personalOwner = state.system?.auth?.mode === "personal";
    $("#adminEntry").hidden = personalOwner || !roleAdmin;
    const adminSettings = $("#adminSettingsLink");
    if (adminSettings) adminSettings.hidden = !(roleAdmin || personalOwner);
    const logout = $("#logoutEntry");
    if (logout)
      logout.hidden = !(
        state.system?.auth?.mode === "accounts" && state.auth?.user
      );
    applySidebarPreferences();
    await loadExperiencePreferences();
    applyArtifactFormat($("#artifactFormat")?.value || "txt", false);
    try {
      const scenarioPayload = await api("/api/scenarios");
      state.scenarios = scenarioPayload.scenarios || [];
    } catch (_) {
      state.scenarios = [];
    }
    try {
      const prefPayload = await api("/api/preferences/web");
      state.webPreferences = prefPayload.preferences || null;
      renderWebPreferences();
    } catch (_) {
      state.webPreferences = null;
      renderWebPreferences();
    }
    await loadServerStore();
    await loadArtifacts();
    await health();
    await maybeStartTour();
  } catch (error) {
    const friendly = friendlyError(error);
    setHealth(false, friendly.title);
    showRuntimeState(friendly.kind, friendly.title, friendly.detail);
    console.error(error);
  }
  chat.setAttribute("aria-busy", "false");
  requestAnimationFrame(() => document.body.classList.add("ui-ready"));
  input.focus();
}
function linesToDomains(value) {
  return String(value || "")
    .split(/\r?\n|,/)
    .map((x) => x.trim().toLowerCase())
    .filter(Boolean);
}
function renderWebPreferences() {
  const p = state.webPreferences || {};
  if ($("#webSearchScope"))
    $("#webSearchScope").value = p.search_scope || "internet";
  if ($("#webRegion")) $("#webRegion").value = p.region || "";
  if ($("#webAllowedDomains"))
    $("#webAllowedDomains").value = (p.allowed_domains || []).join("\n");
  if ($("#webExcludedDomains"))
    $("#webExcludedDomains").value = (p.excluded_domains || []).join("\n");
  if ($("#webNewsInterests"))
    $("#webNewsInterests").value = (p.news_interests || []).join("\n");
  if ($("#webPreferRussian"))
    $("#webPreferRussian").checked = p.prefer_russian !== false;
  renderWebPresetButtons();
}
async function saveWebPreferences() {
  try {
    const payload = await api("/api/preferences/web", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        search_scope: $("#webSearchScope").value,
        region: $("#webRegion").value,
        allowed_domains: linesToDomains($("#webAllowedDomains").value),
        excluded_domains: linesToDomains($("#webExcludedDomains").value),
        news_interests: String($("#webNewsInterests")?.value || "")
          .split(/\r?\n|,/)
          .map((x) => x.trim())
          .filter(Boolean),
        prefer_russian: $("#webPreferRussian").checked,
      }),
    });
    state.webPreferences = payload.preferences;
    renderWebPreferences();
    toast(
      L("Настройки поиска сохранены", "Search preferences saved"),
      "success",
    );
  } catch (error) {
    toast(error.message, "error");
  }
}
async function health() {
  try {
    const result = await api("/api/health");
    const ready = Boolean(result.ready);
    const degraded = ["web_search", "browser", "code"].some(
      (key) => String(result[key] || "").toLowerCase() === "degraded",
    );
    setHealth(
      ready,
      !ready
        ? tr("starting")
        : degraded
          ? tr("runtimeDegradedTitle")
          : tr("ready"),
    );
    if (!ready)
      showRuntimeState(
        "starting",
        tr("runtimeStartingTitle"),
        tr("runtimeStartingDetail"),
      );
    else if (degraded)
      showRuntimeState(
        "degraded",
        tr("runtimeDegradedTitle"),
        tr("runtimeDegradedDetail"),
      );
    else showRuntimeState("ready", "", "");
  } catch (error) {
    setHealth(false, tr("offline"));
    showRuntimeState(
      "offline",
      tr("runtimeOfflineTitle"),
      tr("runtimeOfflineDetail"),
    );
  }
}
function setHealth(ok, text) {
  for (const selector of ["#dot", "#sideDot"])
    $(selector).className = `dot ${ok ? "ok" : "bad"}`;
  $("#health").textContent = text;
  $("#sideHealth").textContent = text;
  const subtitle = document.querySelector(".sidebar-status small");
  if (subtitle)
    subtitle.textContent =
      runtimeProfile() === "server" ? tr("serverStatus") : tr("localStatus");
}
function resizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(200, Math.max(44, input.scrollHeight))}px`;
}
function openSidebar() {
  document.body.classList.add("sidebar-open");
}
function closeSidebar() {
  document.body.classList.remove("sidebar-open");
}
async function signOut() {
  try {
    await api("/api/auth/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
  } catch (_) {}
  location.href = "/login";
}
async function openArchive() {
  state.activeFolderId = "__archived__";
  const first = state.conversations.find((c) => c.archived_at);
  if (first) await loadConversation(first.id, false);
  saveStore();
  renderAll();
  closeSidebar();
}

function toast(message, type = "info") {
  const item = node("div", `toast ${type}`, message);
  $("#toasts").append(item);
  setTimeout(() => item.classList.add("show"), 10);
  setTimeout(() => {
    item.classList.remove("show");
    setTimeout(() => item.remove(), 180);
  }, 2600);
}
async function copyText(text, button) {
  let ok = false;
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(String(text));
      ok = true;
    }
  } catch (_) {}
  if (!ok) {
    const area = document.createElement("textarea");
    area.value = String(text);
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.append(area);
    area.select();
    try {
      ok = document.execCommand("copy");
    } catch (_) {}
    area.remove();
  }
  if (button) {
    const previous = button.textContent;
    button.textContent = ok ? "Скопировано" : "Выделено";
    setTimeout(() => (button.textContent = previous), 1200);
  }
  toast(
    ok ? "Скопировано в буфер" : "Текст готов к копированию",
    ok ? "success" : "info",
  );
}
function downloadFile(name, type, content) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  toast(`Экспортировано: ${name}`, "success");
}
function safeFilename(value) {
  return (
    String(value || "chat")
      .replace(/[\\/:*?"<>|]+/g, "-")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 64) || "chat"
  );
}
function chatMarkdown(c) {
  const lines = [
    `# ${c.title}`,
    "",
    `${L("Экспорт Персонального агента", "Personal Agent export")} · ${new Date().toLocaleString(langKey() === "en" ? "en-US" : "ru-RU")}`,
    "",
  ];
  for (const message of c.messages) {
    lines.push(
      `## ${message.role === "user" ? L("Вы", "You") : tr("brand")}`,
      "",
      message.content,
      "",
    );
    if (Array.isArray(message.sources) && message.sources.length) {
      lines.push("### Источники", "");
      for (const source of message.sources) {
        lines.push(
          `- [${source.title || source.url}](${source.url})${source.published_date ? ` · ${source.published_date}` : ""}`,
        );
      }
      lines.push("");
    }
    if (Array.isArray(message.attachments) && message.attachments.length) {
      lines.push("### Файлы", "");
      for (const file of message.attachments) {
        lines.push(
          `- ${file.name || "Файл"}${file.sha256 ? ` · SHA-256 ${file.sha256}` : ""}`,
        );
      }
      lines.push("");
    }
  }
  return lines.join("\n");
}
function triggerArtifactDownload(artifact) {
  const anchor = document.createElement("a");
  anchor.href =
    artifact.download_url || `/api/files/${artifact.artifact_id}/download`;
  anchor.download = artifact.name || "";
  anchor.rel = "noopener";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
}
async function persistExport(format, name, content) {
  const payload = await api("/api/files/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ format, name, content }),
  });
  if (!payload?.artifact?.artifact_id)
    throw new Error("Сервер не вернул файл экспорта");
  triggerArtifactDownload(payload.artifact);
  await loadArtifacts();
  return payload.artifact;
}
async function exportCurrent() {
  const c = current();
  if (!c || !c.messages.length) {
    toast("В текущем диалоге пока нечего экспортировать", "info");
    return;
  }
  const name = `${safeFilename(c.title)}.md`;
  const content = chatMarkdown(c);
  try {
    const artifact = await persistExport("md", name, content);
    toast(`Чат сохранён в workspace: ${artifact.name}`, "success");
  } catch (error) {
    downloadFile(name, "text/markdown;charset=utf-8", content);
    setBanner(
      `Серверный экспорт недоступен (${error.message}). Использован локальный Markdown-файл.`,
      "warning",
    );
  }
}
async function exportAll() {
  const name = `personal-agent-rus-chats-${new Date().toISOString().slice(0, 10)}.json`;
  const server = await api("/api/conversations/export");
  const payload = {
    product: "Personal Agent Rus",
    version: UI_VERSION,
    exported_at: new Date().toISOString(),
    schema_version: server.export?.schema_version || 1,
    folders: server.export?.folders || [],
    conversations: server.export?.conversations || [],
  };
  const content = JSON.stringify(payload, null, 2);
  try {
    const artifact = await persistExport("json", name, payload);
    toast(`Архив диалогов сохранён: ${artifact.name}`, "success");
  } catch (error) {
    downloadFile(name, "application/json;charset=utf-8", content);
    setBanner(
      `Серверный экспорт недоступен (${error.message}). Использован локальный JSON-файл.`,
      "warning",
    );
  }
}

let actionResolver = null;
function openActionModal({
  title,
  message,
  confirmText = "Продолжить",
  danger = false,
  inputValue = null,
  inputLabel = "Название",
  selectOptions = null,
  selectValue = "",
}) {
  $("#actionTitle").textContent = title;
  $("#actionMessage").textContent = message || "";
  $("#actionConfirm").textContent = confirmText;
  $("#actionConfirm").className = danger ? "danger-button" : "primary-button";
  const field = $("#actionInput");
  const label = $("#actionInputLabel");
  const select = $("#actionSelect");
  const hasInput = inputValue !== null;
  const hasSelect = Array.isArray(selectOptions);
  field.hidden = !hasInput;
  label.hidden = !hasInput;
  if (hasInput) {
    field.value = String(inputValue);
    label.textContent = inputLabel;
  }
  select.hidden = !hasSelect;
  select.replaceChildren();
  if (hasSelect) {
    for (const option of selectOptions) {
      const item = node("option", "", option.label);
      item.value = option.value;
      if (String(option.value) === String(selectValue)) item.selected = true;
      select.append(item);
    }
  }
  $("#actionBackdrop").hidden = false;
  requestAnimationFrame(() => {
    (hasInput ? field : hasSelect ? select : $("#actionConfirm")).focus();
    if (hasInput) field.select();
  });
  return new Promise((resolve) => {
    actionResolver = resolve;
  });
}
function closeActionModal(result) {
  $("#actionBackdrop").hidden = true;
  const resolver = actionResolver;
  actionResolver = null;
  if (resolver) resolver(result);
}
async function confirmAction(
  title,
  message,
  confirmText = "Продолжить",
  kind = "normal",
) {
  return Boolean(
    await openActionModal({
      title,
      message,
      confirmText,
      danger: kind === "danger",
    }),
  );
}
async function promptAction(
  title,
  message,
  value,
  inputLabel = L("Название диалога", "Chat title"),
) {
  const result = await openActionModal({
    title,
    message,
    confirmText: "Сохранить",
    inputValue: value,
    inputLabel,
  });
  return result === false ? null : String(result || "").trim();
}
async function selectAction(
  title,
  message,
  options,
  value = "",
  confirmText = "Выбрать",
) {
  const result = await openActionModal({
    title,
    message,
    confirmText,
    selectOptions: options,
    selectValue: value,
  });
  return result === false ? null : String(result);
}

async function refreshCodeStatus() {
  const host = $("#codeRunState");
  if (!host) return;
  try {
    const result = await api("/api/code/status");
    const ready = (result.languages || [])
      .filter((x) => x.available)
      .map((x) => x.label)
      .join(", ");
    host.textContent = result.ready
      ? `Sandbox готов · ${ready} · сеть отключена`
      : `Sandbox частично доступен · ${ready}`;
    host.dataset.state = result.ready ? "ready" : "degraded";
  } catch (error) {
    host.textContent = `Sandbox недоступен: ${error.message}`;
    host.dataset.state = "error";
  }
}
function renderCodeJob(job) {
  const stateHost = $("#codeRunState");
  const out = $("#codeStdout");
  const err = $("#codeStderr");
  const result = job?.result || {};
  const compile = job?.compile || {};
  const pieces = [job?.status || "UNKNOWN", job?.language || ""];
  if (result.duration_ms != null) pieces.push(`${result.duration_ms} ms`);
  if (result.exit_code != null) pieces.push(`exit ${result.exit_code}`);
  stateHost.textContent =
    pieces.filter(Boolean).join(" · ") + (job?.error ? ` · ${job.error}` : "");
  out.textContent = [compile.stdout, result.stdout].filter(Boolean).join("\n");
  err.textContent = [compile.stderr, result.stderr].filter(Boolean).join("\n");
  const done = ["COMPLETED", "FAILED", "CANCELLED"].includes(job?.status);
  $("#runCode").disabled = !done;
  $("#cancelCode").disabled = done;
}
async function pollCodeJob() {
  if (!state.codeJobId) return;
  try {
    const payload = await api(`/api/code/jobs/${state.codeJobId}`);
    renderCodeJob(payload.job);
    if (["COMPLETED", "FAILED", "CANCELLED"].includes(payload.job.status)) {
      state.codeJobId = null;
      state.codePollTimer = null;
      return;
    }
  } catch (error) {
    $("#codeRunState").textContent = error.message;
    state.codeJobId = null;
    $("#runCode").disabled = false;
    $("#cancelCode").disabled = true;
    return;
  }
  state.codePollTimer = setTimeout(pollCodeJob, 250);
}
async function runCode() {
  const language = $("#codeLanguage").value;
  const code = $("#codeEditor").value;
  const timeout_seconds = Number($("#codeTimeout").value || 10);
  if (!code.trim()) {
    toast("Введите код", "error");
    return;
  }
  $("#runCode").disabled = true;
  $("#cancelCode").disabled = false;
  $("#codeStdout").textContent = "";
  $("#codeStderr").textContent = "";
  $("#codeRunState").textContent = "Запускаю в изолированном sandbox…";
  try {
    const payload = await api("/api/code/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ language, code, timeout_seconds }),
    });
    state.codeJobId = payload.job.id;
    renderCodeJob(payload.job);
    pollCodeJob();
  } catch (error) {
    $("#runCode").disabled = false;
    $("#cancelCode").disabled = true;
    $("#codeRunState").textContent = error.message;
    toast(error.message, "error");
  }
}
async function cancelCode() {
  if (!state.codeJobId) return;
  try {
    const payload = await api(`/api/code/jobs/${state.codeJobId}/cancel`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    renderCodeJob(payload.job);
    state.codeJobId = null;
    if (state.codePollTimer) clearTimeout(state.codePollTimer);
  } catch (error) {
    toast(error.message, "error");
  }
}

function openSettings(tab = "general") {
  $("#settingsBackdrop").hidden = false;
  selectSettingsTab(tab);
  $("#closeSettings").focus();
}
function closeSettings() {
  $("#settingsBackdrop").hidden = true;
  $("#settingsEntry").focus();
}
function selectSettingsTab(name) {
  $$("[data-settings-tab]").forEach((button) =>
    button.classList.toggle("active", button.dataset.settingsTab === name),
  );
  $$("[data-settings-panel]").forEach((panel) =>
    panel.classList.toggle("active", panel.dataset.settingsPanel === name),
  );
}
function toggleChatMenu(force) {
  const menu = $("#chatMenu");
  const nextHidden = force === undefined ? !menu.hidden : !force;
  if (!nextHidden) {
    const c = current();
    const pin = menu.querySelector('[data-action="pin"]');
    const archive = menu.querySelector('[data-action="archive"]');
    if (pin) pin.textContent = c?.pinned_at ? "Открепить" : "Закрепить";
    if (archive)
      archive.textContent = c?.archived_at ? "Вернуть из архива" : "В архив";
  }
  menu.hidden = nextHidden;
  $("#chatMenuButton").setAttribute("aria-expanded", String(!nextHidden));
}

function taskPhaseLabel(task) {
  const labels =
    langKey() === "en"
      ? {
          created: "Created",
          planning: "Planning",
          web: "Searching sources",
          analysis: "Analyzing",
          artifacts: "Creating files",
          verification: "Verifying result",
          completed: "Done",
          failed: "Error",
          cancelled: "Cancelled",
        }
      : {
          created: "Создано",
          planning: "Планирую",
          web: "Ищу источники",
          analysis: "Анализирую",
          artifacts: "Создаю файлы",
          verification: "Проверяю результат",
          completed: "Готово",
          failed: "Ошибка",
          cancelled: "Отменено",
        };
  return (
    labels[task?.phase] || task?.phase || task?.status || L("Задача", "Task")
  );
}
function renderTaskList() {
  const host = $("#taskList");
  if (!host) return;
  host.replaceChildren();
  if (!state.tasks.length) {
    host.append(node("div", "muted", L("Задач пока нет.", "No tasks yet.")));
    return;
  }
  for (const task of state.tasks) {
    const row = node("div", "task-row");
    const copy = node("div", "task-copy");
    copy.append(
      node("strong", "", task.title || task.task_type),
      node(
        "small",
        "",
        `${task.status} · ${task.progress || 0}% · ${taskPhaseLabel(task)}`,
      ),
    );
    const actions = node("div", "task-actions");
    if (
      !["COMPLETED", "FAILED", "CANCELLED", "PARTIAL", "BLOCKED"].includes(
        task.status,
      )
    ) {
      const cancel = node("button", "danger-button", "Отменить");
      cancel.type = "button";
      cancel.onclick = () => cancelTask(task.id);
      actions.append(cancel);
    }
    row.append(copy, actions);
    host.append(row);
  }
}
async function loadTasks() {
  try {
    const result = await api("/api/tasks?limit=50");
    state.tasks = result.tasks || [];
    renderTaskList();
  } catch (_) {
    state.tasks = [];
    renderTaskList();
  }
}
async function cancelTask(taskId) {
  try {
    await api(`/api/tasks/${taskId}/cancel`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    toast("Отмена запрошена", "success");
    await loadTasks();
  } catch (error) {
    toast(error.message, "error");
  }
}
function updateTaskMessage(message, task) {
  message.taskId = task.id;
  message.kind = "task";
  message.content = `${taskPhaseLabel(task)} · ${task.progress || 0}%`;
  if (task.status === "FAILED")
    message.content = `Задача завершилась ошибкой: ${task.error || "неизвестная ошибка"}`;
  if (task.status === "CANCELLED")
    message.content = L("Задача отменена.", "Task cancelled.");
  if (task.status === "COMPLETED") {
    message.content =
      task.result?.answer ||
      L("Готово. Результаты проверены.", "Done. The results were verified.");
    message.sources = task.result?.sources || [];
    message.attachments = (task.result?.artifacts || []).map((a) => ({
      artifact_id: a.id,
      name: a.name,
      format: (a.name || "").split(".").pop() || "file",
      download_url: `/api/files/${a.id}/download`,
    }));
  }
}
async function pollTask(taskId, message) {
  try {
    const payload = await api(`/api/tasks/${taskId}`);
    const task = payload.task;
    updateTaskMessage(message, task);
    saveStore();
    renderAll();
    if (
      ["COMPLETED", "FAILED", "CANCELLED", "PARTIAL", "BLOCKED"].includes(
        task.status,
      )
    ) {
      delete state.taskPollTimers[taskId];
      state.taskMode = null;
      await loadTasks();
      return;
    }
  } catch (error) {
    message.content = `Не удалось обновить задачу: ${error.message}`;
    saveStore();
    renderAll();
    delete state.taskPollTimers[taskId];
    return;
  }
  state.taskPollTimers[taskId] = setTimeout(
    () => pollTask(taskId, message),
    700,
  );
}
async function sendTaskRequest(content) {
  const c = current();
  addMessage({ role: "user", content });
  const progress = addMessage({
    role: "assistant",
    content: "Создаю задачу…",
    kind: "task",
  });
  try {
    await api(`/api/conversations/${c.id}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role: "user", content }),
    });
  } catch (_) {}
  setBusy(true);
  try {
    const payload = await api("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "research_report",
        question: content,
        formats: ["md", "xlsx", "pdf"],
      }),
    });
    updateTaskMessage(progress, payload.task);
    saveStore();
    renderAll();
    pollTask(payload.task.id, progress);
    setBanner(
      L(
        "Задача выполняется сервером: можно обновить страницу и вернуться позже.",
        "The task is running on the server. You can refresh the page and return later.",
      ),
      "info",
    );
  } catch (error) {
    progress.content = `${L("Не удалось создать задачу", "Could not create task")}: ${error.message}`;
    progress.kind = "error";
    saveStore();
    renderAll();
    state.taskMode = null;
  } finally {
    setBusy(false);
    input.value = "";
    resizeInput();
    input.focus();
  }
}
function toggleToolTray(force) {
  const tray = $("#toolTray");
  const nextHidden = force === undefined ? !tray.hidden : !force;
  tray.hidden = nextHidden;
  $("#attachBtn").setAttribute("aria-expanded", String(!nextHidden));
}

async function renameCurrent() {
  const c = current();
  if (!c) return;
  const value = await promptAction(
    L("Переименовать диалог", "Rename chat"),
    L(
      "Название сохранится в Персональном агенте и будет доступно после перезапуска.",
      "The title will be stored by Personal Agent and remain available after restart.",
    ),
    c.title,
  );
  if (value === null) return;
  const result = await api(`/api/conversations/${c.id}/rename`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: value || defaultChatTitle() }),
  });
  const index = state.conversations.findIndex((x) => x.id === c.id);
  state.conversations[index] = serverConversation(result.conversation);
  renderAll();
  toast(L("Диалог переименован", "Chat renamed"), "success");
}
async function clearCurrent() {
  const c = current();
  if (!c || !c.messages.length) {
    toast(L("Диалог уже пуст", "Chat is already empty"));
    return;
  }
  if (
    await confirmAction(
      L("Очистить сообщения?", "Clear messages?"),
      L(
        "Название диалога будет сброшено, сообщения удалятся с сервера.",
        "The chat title will be reset and messages will be deleted from the server.",
      ),
      L("Очистить", "Clear"),
      "danger",
    )
  ) {
    await clearCurrentNow();
    toast(L("Сообщения очищены", "Messages cleared"), "success");
  }
}
async function deleteCurrent() {
  const c = current();
  if (!c) return;
  if (
    await confirmAction(
      L("Удалить диалог?", "Delete chat?"),
      L(
        `«${c.title}» будет удалён из вашей истории.`,
        `“${c.title}” will be deleted from your history.`,
      ),
      L("Удалить", "Delete"),
      "danger",
    )
  ) {
    await deleteConversationNow(c.id);
    toast(L("Диалог удалён", "Chat deleted"), "success");
  }
}
async function clearAll() {
  if (
    await confirmAction(
      L("Удалить все диалоги?", "Delete all chats?"),
      L(
        "Будет удалена вся история текущего пользователя. Файлы workspace не удаляются.",
        "All chat history for the current user will be deleted. Workspace files will be kept.",
      ),
      L("Удалить всё", "Delete all"),
      "danger",
    )
  ) {
    await clearAllNow();
    toast(L("История очищена", "History cleared"), "success");
  }
}
async function renameFolder(folder) {
  const name = await promptAction(
    L("Переименовать проект", "Rename project"),
    L(
      "Новое название будет сохранено для всех ваших устройств.",
      "The new name will be saved for all your devices.",
    ),
    folder.name,
    L("Название проекта", "Project name"),
  );
  if (name === null || !name) return;
  const result = await api(`/api/folders/${folder.id}/rename`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  const index = state.folders.findIndex((x) => x.id === folder.id);
  if (index >= 0) state.folders[index] = result.folder;
  renderAll();
  toast(L("Проект переименован", "Project renamed"), "success");
}
async function deleteFolder(folder) {
  if (
    !(await confirmAction(
      L("Удалить проект?", "Delete project?"),
      L(
        `Диалоги из «${folder.name}» останутся в истории без проекта.`,
        `Chats from “${folder.name}” will remain in history without a project.`,
      ),
      L("Удалить проект", "Delete project"),
      "danger",
    ))
  )
    return;
  await api(`/api/folders/${folder.id}`, { method: "DELETE" });
  if (state.activeFolderId === folder.id) state.activeFolderId = null;
  await loadServerStore(state.search);
  toast(
    L(
      "Проект удалён, диалоги сохранены",
      "Project deleted; chats were preserved",
    ),
    "success",
  );
}
async function setConversationPinned(conversation, pinned) {
  const result = await api(`/api/conversations/${conversation.id}/pin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pinned }),
  });
  const index = state.conversations.findIndex((x) => x.id === conversation.id);
  if (index >= 0)
    state.conversations[index] = serverConversation(result.conversation);
  saveStore();
  renderAll();
  toast(
    pinned
      ? L("Диалог закреплён", "Chat pinned")
      : L("Диалог откреплён", "Chat unpinned"),
    "success",
  );
}
async function moveCurrent() {
  const c = current();
  if (!c) return;
  const options = [
    { value: "", label: L("Без проекта", "No project") },
    ...state.folders.map((folder) => ({
      value: folder.id,
      label: folder.name,
    })),
  ];
  const folderId = await selectAction(
    L("Переместить диалог", "Move chat"),
    L(
      "Выберите проект для текущего диалога.",
      "Choose a project for the current chat.",
    ),
    options,
    c.folder_id || "",
  );
  if (folderId === null) return;
  const result = await api(`/api/conversations/${c.id}/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ folder_id: folderId || null }),
  });
  const index = state.conversations.findIndex((x) => x.id === c.id);
  if (index >= 0)
    state.conversations[index] = serverConversation(result.conversation);
  await loadServerStore(state.search);
  toast(
    folderId
      ? L("Диалог перемещён в проект", "Chat moved to project")
      : L("Диалог перемещён в «Все чаты»", "Chat moved to All chats"),
    "success",
  );
}
async function archiveCurrent() {
  const c = current();
  if (!c) return;
  const archived = !Boolean(c.archived_at);
  const result = await api(`/api/conversations/${c.id}/archive`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ archived }),
  });
  const index = state.conversations.findIndex((x) => x.id === c.id);
  if (index >= 0)
    state.conversations[index] = serverConversation(result.conversation);
  if (archived && state.activeFolderId !== "__archived__") {
    const next = state.conversations.find(
      (x) => !x.archived_at && x.id !== c.id,
    );
    state.activeId = next?.id || null;
    if (!state.activeId) await newConversation(false);
  }
  await loadServerStore(state.search);
  toast(
    archived
      ? L("Диалог перемещён в архив", "Chat archived")
      : L("Диалог возвращён из архива", "Chat restored from archive"),
    "success",
  );
}
async function createFolder() {
  const name = await promptAction(
    L("Новый проект", "New project"),
    L(
      "Проекты помогают группировать связанные диалоги.",
      "Projects help group related chats.",
    ),
    L("Новый проект", "New project"),
    L("Название проекта", "Project name"),
  );
  if (name === null || !String(name).trim()) return;
  const result = await api("/api/folders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  state.folders.push(result.folder);
  state.activeFolderId = result.folder.id;
  const active = current();
  if (
    active &&
    active.messages?.length &&
    active.folder_id !== result.folder.id
  ) {
    const moveNow = await confirmAction(
      L(
        "Перенести текущий диалог в новый проект?",
        "Move the current chat to the new project?",
      ),
      L(
        `Проект «${result.folder.name}» уже создан. Можно сразу перенести туда текущий диалог.`,
        `Project “${result.folder.name}” was created. You can move the current chat there now.`,
      ),
      L("Перенести", "Move"),
    );
    if (moveNow) {
      await api(`/api/conversations/${active.id}/move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_id: result.folder.id }),
      });
      await loadServerStore(state.search);
      toast(
        L("Проект создан, диалог перенесён", "Project created and chat moved"),
        "success",
      );
      return;
    }
  }
  saveStore();
  renderAll();
  toast(
    L(
      "Проект создан. Новый чат будет открываться внутри него.",
      "Project created. New chats will now open inside it.",
    ),
    "success",
  );
}
async function sendRequest({ addUser = true, text = null } = {}) {
  if (state.busy) return;
  let content = String(text ?? input.value).trim();
  if (addUser && !content && state.pendingFiles.length)
    content = L(
      "Проанализируй приложенные файлы и выдели главное.",
      "Analyze the attached files and highlight the key points.",
    );
  if (addUser && !content) return;
  setBanner("");
  if (addUser && state.taskMode === "research_report") {
    await sendTaskRequest(content);
    return;
  }
  if (addUser) {
    const attachments = [...state.pendingFiles];
    addMessage({ role: "user", content, attachments });
    state.pendingFiles = [];
    renderPendingFiles();
    input.value = "";
    resizeInput();
  }
  setBusy(true);
  setThinking(true);
  const pendingIntent = state.intentHint;
  if (pendingIntent === "research")
    setBanner(
      L(
        "Исследую: ищу источники → читаю страницы → сверяю факты → формирую вывод…",
        "Researching: searching sources → reading pages → checking facts → building a conclusion…",
      ),
      "info",
    );
  else if (pendingIntent === "search" || /https?:\/\//i.test(content))
    setBanner(
      L(
        "Ищу и читаю веб-источники. Ответ появится после синтеза фактов…",
        "Searching and reading web sources. The answer will appear after the facts are synthesized…",
      ),
      "info",
    );
  try {
    const c = current();
    const history = c.messages
      .filter((message) => !String(message.kind || "").startsWith("capability"))
      .map(({ role, content }) => ({ role, content }));
    const fileIds = [
      ...new Set(
        c.messages
          .flatMap((message) =>
            (message.attachments || []).map((item) => item.artifact_id),
          )
          .filter(Boolean),
      ),
    ].slice(-12);
    const result = await api("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: state.mode,
        preset: state.preset,
        intent_hint: state.intentHint,
        scenario_id: state.scenarioId || "",
        file_ids: fileIds,
        messages: history,
        conversation_id: c.id,
        persist_user: addUser,
        attachments: addUser ? c.messages.at(-1)?.attachments || [] : [],
      }),
    });
    const received = addMessage({
      ...result.message,
      sources: result.sources || [],
    });
    if (received && result.intent !== "clarification")
      state.animateMessageId = received.id;
    if (result.intent !== "clarification") state.scenarioId = null;
    else if (result.scenario?.id) state.scenarioId = result.scenario.id;
    state.intentHint = "auto";
    setBanner(
      result.intent === "clarification"
        ? langKey() === "en"
          ? "One short clarification is needed — after your answer Personal Agent will continue the task."
          : "Нужно одно короткое уточнение — после ответа Родной Агент продолжит задачу."
        : "",
    );
    try {
      await loadServerStore(state.search);
    } catch (_) {}
    if ((result.sources || []).length)
      toast(
        `${L("Ответ собран по", "Answer synthesized from")} ${result.sources.length} ${L("веб-источникам", "web sources")}`,
        "success",
      );
  } catch (error) {
    if (error.code === "capability_unavailable") {
      const c = current();
      const last = [...(c?.messages || [])]
        .reverse()
        .find(
          (message) => message.role === "user" && message.kind === "message",
        );
      if (last) last.kind = "capability-request";
      saveStore();
      addMessage({
        role: "assistant",
        content:
          error.message ||
          L(
            "Для этого запроса нужна возможность, которая пока не подключена.",
            "This request needs a capability that is not connected yet.",
          ),
        kind: "capability",
      });
      setBanner(
        L(
          "Запрос остановлен до обращения к локальной модели: требуется отдельная capability.",
          "The request was stopped before local inference because a separate capability is required.",
        ),
        "warning",
      );
    } else {
      const friendly = friendlyError(error);
      addMessage({
        role: "assistant",
        content: `${friendly.title}. ${friendly.detail}`,
        kind: "error",
      });
      setBanner(friendly.detail, "warning");
      showRuntimeState(friendly.kind, friendly.title, friendly.detail);
    }
  } finally {
    setThinking(false);
    setBusy(false);
    input.focus();
  }
}
async function regenerateAt(index) {
  if (state.busy) return;
  const c = current();
  if (!c) return;
  let assistantIndex = Math.min(index, c.messages.length - 1);
  while (
    assistantIndex >= 0 &&
    c.messages[assistantIndex]?.role !== "assistant"
  )
    assistantIndex--;
  if (assistantIndex < 0) return;
  let userIndex = assistantIndex - 1;
  while (userIndex >= 0 && c.messages[userIndex]?.role !== "user") userIndex--;
  if (userIndex < 0) return;
  c.messages.splice(assistantIndex, 1);
  c.updatedAt = now();
  saveStore();
  renderAll();
  toast(L("Повторяю последний ответ", "Retrying the last answer"));
  await sendRequest({ addUser: false, text: c.messages[userIndex].content });
}

const TOUR_STEPS = [
  {
    selector: "#brandHelp",
    title: "Добро пожаловать в Родной Агент",
    title_en: "Welcome to Personal Agent",
    text: "Здесь можно пройти обучение заново, открыть руководство и быстро посмотреть возможности продукта.",
    text_en:
      "Restart the guided tour, open the guide and quickly explore the product capabilities here.",
  },
  {
    selector: "#newChat",
    title: "Новый чат",
    title_en: "New chat",
    text: "Создайте отдельный диалог. Быстрая клавиша — Ctrl+N.",
    text_en: "Start a separate conversation. Shortcut: Ctrl+N.",
  },
  {
    selector: "#input",
    title: "Просто напишите задачу",
    title_en: "Just describe the task",
    text: "Опишите результат обычным языком. Родной Агент сам выберет нужные возможности.",
    text_en:
      "Describe the outcome in plain language. Personal Agent will choose the required capabilities.",
  },
  {
    selector: "#attachBtn",
    title: "Файлы и инструменты",
    title_en: "Files and tools",
    text: "Прикрепляйте документы или включайте Web, Code и длинные задачи.",
    text_en: "Attach documents or enable Web, Code and long-running tasks.",
  },
  {
    selector: "#chatSearch",
    title: "История и поиск",
    title_en: "History and search",
    text: "Диалоги теперь хранятся на сервере и находятся по заголовку и содержимому.",
    text_en:
      "Chats are stored by the server and can be found by title or message content.",
  },
  {
    selector: "#newFolder",
    title: "Проекты",
    title_en: "Projects",
    text: "Группируйте связанные диалоги в проекты. Новый чат создаётся в выбранном проекте.",
    text_en:
      "Group related chats into projects. New chats are created in the selected project.",
  },
  {
    selector: "#exportChatButton",
    title: "Результат можно забрать",
    title_en: "Take the result with you",
    text: "Скачивайте текущий чат как проверенный Markdown-артефакт.",
    text_en: "Download the current chat as a verified Markdown artifact.",
  },
  {
    selector: "#executionQuick",
    title: "Приватность понятна сразу",
    title_en: "Privacy at a glance",
    text: "Локальный режим означает, что базовая обработка идёт на вашем компьютере. Remote-переходы должны быть явными.",
    text_en:
      "Local mode keeps the base processing on your computer. Any switch to remote processing must be explicit.",
  },
  {
    selector: "#accountEntry",
    title: "Профиль и тариф",
    title_en: "Profile and plan",
    text: "Здесь находятся аккаунт, подписка, использование и пользовательские настройки.",
    text_en:
      "Your account, subscription, usage and personal settings are available here.",
  },
];
let tourIndex = 0;
const TOUR_STATE_KEY = "par-tour-state";
const TOUR_TRIGGER_KEY = "par-tour-trigger";
function tourState() {
  return localStorage.getItem(TOUR_STATE_KEY) || "";
}
function setTourState(status) {
  if (status) localStorage.setItem(TOUR_STATE_KEY, status);
  else localStorage.removeItem(TOUR_STATE_KEY);
}
function consumeTourTrigger() {
  const armed = sessionStorage.getItem(TOUR_TRIGGER_KEY) === "1";
  if (armed) sessionStorage.removeItem(TOUR_TRIGGER_KEY);
  return armed;
}
function applySidebarPreferences() {
  const width = Math.max(
    240,
    Math.min(420, Number(localStorage.getItem("par-sidebar-width") || 282)),
  );
  document.documentElement.style.setProperty("--sidebar-user", `${width}px`);
  const isMobile = window.matchMedia("(max-width:720px)").matches;
  const collapsed =
    !isMobile && localStorage.getItem("par-sidebar-collapsed") === "1";
  $("#sidebar").classList.toggle("collapsed", collapsed);
  if (collapsed)
    document.documentElement.style.setProperty("--sidebar-user", "68px");
}
function setSidebarCollapsed(value) {
  localStorage.setItem("par-sidebar-collapsed", value ? "1" : "0");
  applySidebarPreferences();
  const button = $("#collapseSidebar");
  button.textContent = value ? "›" : "‹";
  button.setAttribute("aria-expanded", String(!value));
  button.title = value
    ? langKey() === "en"
      ? "Expand sidebar (Ctrl+B)"
      : "Развернуть панель (Ctrl+B)"
    : langKey() === "en"
      ? "Collapse sidebar (Ctrl+B)"
      : "Свернуть панель (Ctrl+B)";
}
function setSidebarWidth(width) {
  const next = Math.max(240, Math.min(420, Number(width) || 282));
  document.documentElement.style.setProperty("--sidebar-user", `${next}px`);
  localStorage.setItem("par-sidebar-width", String(next));
  return next;
}
function bindSidebarResize() {
  const handle = $("#sidebarResizer");
  let active = false;
  handle.tabIndex = 0;
  handle.setAttribute("aria-valuemin", "240");
  handle.setAttribute("aria-valuemax", "420");
  handle.addEventListener("pointerdown", (event) => {
    active = true;
    handle.classList.add("dragging");
    handle.setPointerCapture(event.pointerId);
  });
  handle.addEventListener("pointermove", (event) => {
    if (!active) return;
    const width = setSidebarWidth(event.clientX);
    handle.setAttribute("aria-valuenow", String(width));
  });
  const stop = () => {
    active = false;
    handle.classList.remove("dragging");
  };
  handle.addEventListener("pointerup", stop);
  handle.addEventListener("pointercancel", stop);
  handle.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    let current = Number(localStorage.getItem("par-sidebar-width") || 282);
    if (event.key === "Home") current = 240;
    else if (event.key === "End") current = 420;
    else current += event.key === "ArrowRight" ? 16 : -16;
    const width = setSidebarWidth(current);
    handle.setAttribute("aria-valuenow", String(width));
  });
}
function openHelp() {
  closeSidebar();
  $("#helpBackdrop").hidden = false;
}
function closeHelp() {
  $("#helpBackdrop").hidden = true;
}
function renderHelpCapabilities() {
  const host = $("#helpCapabilities");
  host.replaceChildren();
  for (const [key, item] of Object.entries(state.system?.capabilities || {})) {
    const row = node("div", "help-capability");
    const status = String(item.status || "").toLowerCase();
    row.append(
      node(
        "span",
        "",
        status === "ready"
          ? "✓"
          : status === "admin"
            ? "⚙"
            : status === "degraded"
              ? "!"
              : "○",
      ),
    );
    const copy = node("div", "");
    const detail =
      status === "ready"
        ? L("Доступно сейчас", "Available now")
        : status === "degraded"
          ? L("Ограниченно доступно", "Limited availability")
          : status === "admin"
            ? L(
                "Настраивается администратором",
                "Configured by an administrator",
              )
            : status === "planned"
              ? L(
                  "Запланировано, но ещё не подключено",
                  "Planned but not connected yet",
                )
              : L("Сейчас недоступно", "Currently unavailable");
    copy.append(
      node("strong", "", item.label || key),
      node("small", "", detail),
    );
    row.append(copy);
    host.append(row);
  }
  host.hidden = false;
}
function tourTarget() {
  return document.querySelector(TOUR_STEPS[tourIndex]?.selector || "");
}
function positionTour() {
  const target = tourTarget();
  if (!target) return;
  target.scrollIntoView({ block: "center", inline: "nearest" });
  requestAnimationFrame(() => {
    const rect = target.getBoundingClientRect();
    const pad = 7;
    const spot = $("#tourSpotlight");
    Object.assign(spot.style, {
      left: `${Math.max(4, rect.left - pad)}px`,
      top: `${Math.max(4, rect.top - pad)}px`,
      width: `${Math.max(24, rect.width + pad * 2)}px`,
      height: `${Math.max(24, rect.height + pad * 2)}px`,
    });
    const card = $("#tourCard");
    const w = Math.min(360, window.innerWidth - 28);
    let left = rect.right + 18;
    if (left + w > window.innerWidth - 14)
      left = Math.max(14, rect.left - w - 18);
    let top = Math.max(14, Math.min(window.innerHeight - 230, rect.top));
    if (window.innerWidth < 720) {
      left = 14;
      top = Math.max(14, window.innerHeight - 250);
    }
    Object.assign(card.style, { left: `${left}px`, top: `${top}px` });
  });
}
async function persistTour(status) {
  try {
    await api("/api/onboarding", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        persona: "user",
        status,
        current_step: tourIndex,
      }),
    });
  } catch (_) {}
}
function renderTour() {
  const step = TOUR_STEPS[tourIndex];
  if (!step) return;
  $("#tourProgress").textContent =
    langKey() === "en"
      ? `${tourIndex + 1} of ${TOUR_STEPS.length}`
      : `${tourIndex + 1} из ${TOUR_STEPS.length}`;
  $("#tourTitle").textContent =
    langKey() === "en" ? step.title_en || step.title : step.title;
  $("#tourText").textContent =
    langKey() === "en" ? step.text_en || step.text : step.text;
  $("#tourBack").disabled = tourIndex === 0;
  $("#tourNext").textContent =
    tourIndex === TOUR_STEPS.length - 1 ? tr("tourDone") : tr("tourNext");
  positionTour();
}
async function startTour(force = false) {
  closeHelp();
  if (!force) {
    const local = tourState();
    if (["completed", "skipped"].includes(local)) return;
    try {
      const value = await api("/api/onboarding");
      const remote = value.state?.status;
      if (["completed", "skipped"].includes(remote)) {
        setTourState(remote);
        return;
      }
    } catch (_) {
      if (["completed", "skipped"].includes(local)) return;
    }
  }
  tourIndex = 0;
  $("#tourLayer").hidden = false;
  setTourState("in_progress");
  await persistTour("in_progress");
  renderTour();
}
async function finishTour(status = "completed") {
  setTourState(status);
  await persistTour(status);
  $("#tourLayer").hidden = true;
  input.focus();
}
async function maybeStartTour() {
  if (!consumeTourTrigger()) return;
  if (["completed", "skipped"].includes(tourState())) return;
  await startTour(false);
}

function bindEvents() {
  $("#runtimeRetry").onclick = () => health();
  $("#newChat").onclick = () => newConversation(true);
  $("#newFolder").onclick = createFolder;
  $("#brandHelp").onclick = openHelp;
  $("#archiveEntry").onclick = () =>
    openArchive().catch((error) => toast(error.message, "warning"));
  $("#logoutEntry").onclick = signOut;
  $("#helpEntry").onclick = openHelp;
  $("#feedbackEntry").onclick = () => {
    openHelp();
    const box = $("#feedbackInline");
    if (box) box.hidden = false;
    setTimeout(() => $("#feedbackMessage")?.focus(), 0);
  };
  $("#closeHelp").onclick = closeHelp;
  $("#helpBackdrop").onclick = (e) => {
    if (e.target === $("#helpBackdrop")) closeHelp();
  };
  $("#restartTour").onclick = () => startTour(true);
  $("#showCapabilities").onclick = renderHelpCapabilities;
  $("#collapseSidebar").onclick = () =>
    setSidebarCollapsed(!$("#sidebar").classList.contains("collapsed"));
  bindSidebarResize();
  $("#openSidebar").onclick = openSidebar;
  $("#closeSidebar").onclick = closeSidebar;
  $("#sidebarBackdrop").onclick = closeSidebar;
  let searchTimer;
  $("#chatSearch").addEventListener("input", (event) => {
    state.search = event.target.value;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(
      () =>
        loadServerStore(state.search).catch((error) =>
          toast(error.message, "warning"),
        ),
      180,
    );
  });
  $("#clearAllShortcut").onclick = clearAll;
  $("#filesEntry").onclick = () => {
    openSettings("files");
    loadArtifacts();
  };
  $("#codeEntry").onclick = () => {
    openSettings("code");
    refreshCodeStatus();
  };
  $("#tasksEntry").onclick = () => {
    openSettings("tasks");
    loadTasks();
  };
  $("#settingsEntry").onclick = () => openSettings("general");
  $("#closeSettings").onclick = closeSettings;
  $("#settingsBackdrop").onclick = (event) => {
    if (event.target === $("#settingsBackdrop")) closeSettings();
  };
  $$("[data-settings-tab]").forEach(
    (button) =>
      (button.onclick = () => selectSettingsTab(button.dataset.settingsTab)),
  );
  $("#exportCurrentChat").onclick = exportCurrent;
  $("#exportAllChats").onclick = exportAll;
  $("#clearCurrentChat").onclick = clearCurrent;
  $("#clearAllChats").onclick = clearAll;
  $("#runCode").onclick = runCode;
  $("#cancelCode").onclick = cancelCode;
  $("#refreshTasks").onclick = loadTasks;
  $("#fileInput").onchange = async (event) => {
    await uploadSelectedFiles(event.target.files);
    event.target.value = "";
  };
  $("#uploadArtifact").onclick = openFilePicker;
  $("#createArtifact").onclick = createArtifactFromUi;
  $("#artifactFormat").onchange = (event) => {
    applyArtifactFormat(event.target.value);
  };
  $("#exportChatButton").onclick = exportCurrent;
  $("#shareChatButton").onclick = shareCurrent;
  if ($("#shareCurrentChat")) $("#shareCurrentChat").onclick = shareCurrent;
  if ($("#executionQuick"))
    $("#executionQuick").onclick = () => openSettings("general");
  $("#chatMenuButton").onclick = (event) => {
    event.stopPropagation();
    toggleChatMenu();
  };
  $("#chatMenu").onclick = (event) => {
    const item = event.target.closest("[data-action]");
    if (!item) return;
    toggleChatMenu(false);
    const action = item.dataset.action;
    if (action === "rename") renameCurrent();
    else if (action === "pin") {
      const c = current();
      if (c) setConversationPinned(c, !c.pinned_at);
    } else if (action === "move") moveCurrent();
    else if (action === "archive") archiveCurrent();
    else if (action === "share") shareCurrent();
    else if (action === "export") exportCurrent();
    else if (action === "clear") clearCurrent();
    else if (action === "delete") deleteCurrent();
  };
  if ($("#saveWebPreferences"))
    $("#saveWebPreferences").onclick = saveWebPreferences;
  if ($("#saveExperiencePreferences"))
    $("#saveExperiencePreferences").onclick = saveExperiencePreferences;
  if ($("#openFeedback"))
    $("#openFeedback").onclick = () => {
      $("#feedbackInline").hidden = !$("#feedbackInline").hidden;
      if (!$("#feedbackInline").hidden) $("#feedbackMessage").focus();
    };
  if ($("#sendFeedback")) $("#sendFeedback").onclick = sendFeedback;
  $("#attachBtn").onclick = (event) => {
    event.stopPropagation();
    toggleToolTray();
  };
  $("#modeButton").onclick = (event) => {
    event.stopPropagation();
    const tones = $("#toneMenu");
    if (tones) tones.hidden = true;
    modes.hidden = !modes.hidden;
    $("#modeButton").setAttribute("aria-expanded", String(!modes.hidden));
  };
  $("#toneButton")?.addEventListener("click", (event) => {
    event.stopPropagation();
    modes.hidden = true;
    const host = $("#toneMenu");
    host.hidden = !host.hidden;
    $("#toneButton").setAttribute("aria-expanded", String(!host.hidden));
  });
  $$("[data-web-preset]").forEach(
    (button) =>
      (button.onclick = () => applyWebPreset(button.dataset.webPreset)),
  );
  $$("[data-artifact-preset]").forEach(
    (button) =>
      (button.onclick = () =>
        applyArtifactFormat(button.dataset.artifactPreset)),
  );
  $("#toolTray").onclick = (event) => {
    const tool = event.target.closest("[data-tool]");
    if (!tool) return;
    toggleToolTray(false);
    const id = tool.dataset.tool;
    if (id === "web") {
      state.intentHint = "search";
      setBanner(
        L(
          "Веб включён для следующего запроса: поиск, чтение сайтов и источники.",
          "Web is enabled for the next request: search, site reading and sources.",
        ),
        "info",
      );
      input.focus();
      return;
    }
    if (id === "files") {
      openFilePicker();
      return;
    }
    if (id === "code") {
      openSettings("code");
      refreshCodeStatus();
      return;
    }
    if (id === "task-report") {
      state.taskMode = "research_report";
      setBanner(
        L(
          "Следующий запрос станет задачей: источники → анализ → MD/XLSX/PDF → проверка.",
          "The next request will become a task: sources → analysis → MD/XLSX/PDF → verification.",
        ),
        "info",
      );
      input.focus();
      return;
    }
    setBanner(
      `${tool.querySelector("strong")?.textContent || L("Эта возможность", "This capability")} ${L("пока не подключена. Кнопка показана как честный preview будущей capability.", "is not connected yet. The button is an honest preview of a future capability.")}`,
      "info",
    );
  };
  $("#actionCancel").onclick = () => closeActionModal(false);
  $("#actionConfirm").onclick = () => {
    const field = $("#actionInput"),
      select = $("#actionSelect");
    closeActionModal(
      !field.hidden ? field.value : !select.hidden ? select.value : true,
    );
  };
  $("#actionBackdrop").onclick = (event) => {
    if (event.target === $("#actionBackdrop")) closeActionModal(false);
  };
  $("#actionInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      $("#actionConfirm").click();
    }
  });
  input.addEventListener("input", resizeInput);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      $("#form").requestSubmit();
    }
  });
  $("#form").onsubmit = (event) => {
    event.preventDefault();
    sendRequest();
  };
  document.addEventListener("click", (event) => {
    if (!event.target.closest(".menu-wrap")) toggleChatMenu(false);
    if (
      !event.target.closest("#toolTray") &&
      !event.target.closest("#attachBtn")
    )
      toggleToolTray(false);
    if (!event.target.closest(".composer-mode-wrap")) {
      modes.hidden = true;
      $("#modeButton").setAttribute("aria-expanded", "false");
      const tones = $("#toneMenu");
      if (tones) {
        tones.hidden = true;
        $("#toneButton")?.setAttribute("aria-expanded", "false");
      }
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      if (!$("#tourLayer").hidden) {
        finishTour("skipped");
        return;
      }
      toggleChatMenu(false);
      toggleToolTray(false);
      closeHelp();
      if (!$("#actionBackdrop").hidden) closeActionModal(false);
      else if (!$("#settingsBackdrop").hidden) closeSettings();
      else closeSidebar();
    }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "n") {
      event.preventDefault();
      newConversation(true);
    } else if (
      (event.ctrlKey || event.metaKey) &&
      event.key.toLowerCase() === "k"
    ) {
      event.preventDefault();
      $("#chatSearch").focus();
    } else if (
      (event.ctrlKey || event.metaKey) &&
      event.key.toLowerCase() === "b"
    ) {
      event.preventDefault();
      setSidebarCollapsed(!$("#sidebar").classList.contains("collapsed"));
    }
  });
  $("#tourSkip").onclick = () => finishTour("skipped");
  $("#tourBack").onclick = () => {
    if (tourIndex > 0) {
      tourIndex--;
      persistTour("in_progress");
      renderTour();
    }
  };
  $("#tourNext").onclick = () => {
    if (tourIndex >= TOUR_STEPS.length - 1) {
      finishTour("completed");
    } else {
      tourIndex++;
      persistTour("in_progress");
      renderTour();
    }
  };
  window.addEventListener("resize", () => {
    if (!$("#tourLayer").hidden) positionTour();
  });
}

matchMedia("(prefers-color-scheme: light)").addEventListener?.("change", () => {
  if ((state.experiencePreferences?.theme || "system") === "system")
    applyTheme("system");
});
applyTheme(localStorage.getItem("par-theme-preference") || "system");
applyUiScale(localStorage.getItem("par-ui-scale") || "normal");
init();
setInterval(health, 15000);
