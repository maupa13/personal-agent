"use strict";

const ADMIN_TOUR_STEPS = [
  {
    selector: '[data-tab="overview"]',
    title: "Дашборд",
    title_en: "Dashboard",
    text: "Начинайте отсюда: здоровье системы, пользователи, модели и ключевые показатели.",
    text_en: "Start here: system health, users, models and key metrics.",
  },
  {
    selector: '[data-tab="users"]',
    title: "Пользователи",
    title_en: "Users",
    text: "Регистрация, статусы и доступ управляются здесь. Пароли администратору никогда не показываются.",
    text_en:
      "Manage registration, status and access here. Passwords are never shown to administrators.",
  },
  {
    selector: '[data-tab="billing"]',
    title: "Подписки и Usage",
    title_en: "Subscriptions & usage",
    text: "Тарифы, лимиты remote AI, платежи и расходы отделены от бесплатного локального inference.",
    text_en:
      "Plans, remote AI limits, payments and costs are separated from local inference.",
  },
  {
    selector: '[data-tab="routing"]',
    title: "Маршрутизация AI",
    title_en: "AI routing",
    text: "Пользователь выбирает понятный режим, а здесь администратор назначает реальные provider/model.",
    text_en:
      "Users choose simple modes; administrators assign the real provider/model behind each mode.",
  },
  {
    selector: '[data-tab="monitoring"]',
    title: "Мониторинг",
    title_en: "Monitoring",
    text: "Проверяйте runtime, задачи и ресурсы без просмотра Docker пользователем.",
    text_en:
      "Inspect runtime, tasks and resources without exposing Docker to users.",
  },
  {
    selector: '[data-tab="logs"]',
    title: "Логи и аудит",
    title_en: "Logs & audit",
    text: "Structured JSONL помогает найти ошибку по событию и времени без утечки секретов.",
    text_en:
      "Structured JSONL helps trace errors by event and time without leaking secrets.",
  },
  {
    selector: '[data-tab="system"]',
    title: "Cookies / Авторизация",
    title_en: "Cookies / Authorization",
    text: "Что с cookies можно делать. Для своего сайта — довольно много: хранить session/token авторизации, remember-me, cartId, locale/theme, experimentGroup, anonymous visitorId, CSRF-related cookie, персонализацию, аналитику, состояние туров, локальные настройки и даже корзину без входа. Нельзя складывать туда пароли, API-ключи или чувствительные данные. Если cookie нужна для работы сайта, учитывайте её в политике приватности и в админке показывайте, где она используется.",
    text_en:
      "What you can do with cookies. For your own site, quite a lot: store session/token authorization, remember-me, cartId, locale/theme, experimentGroup, anonymous visitorId, CSRF-related cookie, personalization, analytics, tour state, local preferences and even a guest cart without sign-in. Do not store passwords, API keys or sensitive data there. If a cookie is required for the site to work, reflect it in privacy policy and show where it is used in the admin UI.",
  },
  {
    selector: '[data-tab="diagnostics"]',
    title: "Диагностика",
    title_en: "Diagnostics",
    text: "Безопасный snapshot ускоряет поддержку: версия, состояние БД/runtime и последние события.",
    text_en:
      "A sanitized snapshot speeds up support: version, DB/runtime state and recent events.",
  },
];
let adminTourIndex = 0;
const ADMIN_TOUR_STATE_KEY = "par-admin-tour-state";
function adminTourState() {
  return localStorage.getItem(ADMIN_TOUR_STATE_KEY) || "";
}
function adminTourSetState(status) {
  if (status) localStorage.setItem(ADMIN_TOUR_STATE_KEY, status);
  else localStorage.removeItem(ADMIN_TOUR_STATE_KEY);
}
function adminTourPosition() {
  const step = ADMIN_TOUR_STEPS[adminTourIndex],
    target = document.querySelector(step?.selector || "");
  if (!target) return;
  target.scrollIntoView({ block: "center" });
  requestAnimationFrame(() => {
    const r = target.getBoundingClientRect(),
      spot = $("#adminTourSpotlight"),
      card = $("#adminTourCard");
    Object.assign(spot.style, {
      left: `${Math.max(4, r.left - 7)}px`,
      top: `${Math.max(4, r.top - 7)}px`,
      width: `${r.width + 14}px`,
      height: `${r.height + 14}px`,
    });
    let left = r.right + 18;
    if (left + 360 > innerWidth - 14) left = Math.max(14, r.left - 378);
    Object.assign(card.style, {
      left: `${left}px`,
      top: `${Math.max(14, Math.min(innerHeight - 230, r.top))}px`,
    });
  });
}
function renderAdminTour() {
  const step = ADMIN_TOUR_STEPS[adminTourIndex];
  $("#adminTourProgress").textContent =
    adminLang() === "en"
      ? `${adminTourIndex + 1} of ${ADMIN_TOUR_STEPS.length}`
      : `${adminTourIndex + 1} из ${ADMIN_TOUR_STEPS.length}`;
  $("#adminTourTitle").textContent =
    adminLang() === "en" ? step.title_en || step.title : step.title;
  $("#adminTourText").textContent =
    adminLang() === "en" ? step.text_en || step.text : step.text;
  $("#adminTourBack").disabled = adminTourIndex === 0;
  $("#adminTourNext").textContent =
    adminTourIndex === ADMIN_TOUR_STEPS.length - 1
      ? adminText("Готово", "Done")
      : adminText("Далее", "Next");
  adminTourPosition();
}
async function adminTourPersist(status) {
  adminTourSetState(status);
  if (token) return;
  try {
    await api("/api/onboarding", {
      method: "POST",
      body: JSON.stringify({
        persona: "admin",
        status,
        current_step: adminTourIndex,
      }),
    });
  } catch (_) {}
}
async function startAdminTour(force = false) {
  if (!force && ["completed", "skipped"].includes(adminTourState())) return;
  if (!force && !token) {
    try {
      const current = await api("/api/onboarding?persona=admin");
      if (["completed", "skipped"].includes(current.state?.status)) {
        adminTourSetState(current.state.status);
        return;
      }
    } catch (_) {}
  }
  adminTourIndex = 0;
  $("#adminTourLayer").hidden = false;
  adminTourPersist("in_progress");
  renderAdminTour();
}
async function finishAdminTour(status) {
  adminTourSetState(status);
  await adminTourPersist(status);
  $("#adminTourLayer").hidden = true;
}
async function maybeStartAdminTour() {
  if (["completed", "skipped"].includes(adminTourState())) return;
  await startAdminTour(false);
}

applyAdminTheme();
applyAdminLanguage();
$("#adminLocaleToggle")?.addEventListener("click", () => {
  applyAdminLanguage(adminLang() === "en" ? "ru" : "en");
  if (status) renderAll();
  if (lanStatus) renderLan();
  refreshAdminAuthStatus();
});
$("#adminThemeToggle")?.addEventListener("click", () => {
  const current = document.documentElement.dataset.theme || "dark";
  const next = current === "dark" ? "light" : "dark";
  applyAdminTheme(next);
});
$("#loginBtn").onclick = async () => {
  const supplied = $("#token").value.trim();
  $("#loginError").textContent = "";
  if (!supplied) {
    $("#loginError").textContent = adminText(
      "Введите break-glass токен. Если вы владелец локальной установки, откройте Admin с этого ПК — токен не требуется.",
      "Enter the break-glass token. If you own the local installation, open Admin from this computer — no token is required.",
    );
    return;
  }
  try {
    token = supplied;
    await api("/api/admin/login", {
      method: "POST",
      body: JSON.stringify({ token: supplied }),
    });
    sessionStorage.setItem("par-admin-token", token);
    $("#login").hidden = true;
    $("#admin").hidden = false;
    $("#adminNav").hidden = false;
    $("#logoutBtn").hidden = false;
    await load();
  } catch (error) {
    token = "";
    $("#loginError").textContent =
      error.message === "invalid admin token"
        ? adminText(
            "Break-glass токен не совпадает с текущей конфигурацией. Проверьте активный config/.env либо войдите OWNER/ADMIN аккаунтом.",
            "The break-glass token does not match the active configuration. Check the active config/.env or sign in with an OWNER/ADMIN account.",
          )
        : error.message;
  }
};
$("#logoutBtn").onclick = async () => {
  if (roleAdmin) {
    try {
      await api("/api/auth/logout", { method: "POST", body: "{}" });
    } catch (_) {}
    location.href = "/login";
  } else {
    sessionStorage.removeItem("par-admin-token");
    location.reload();
  }
};
$$(".admin-nav-item").forEach(
  (b) => (b.onclick = () => selectTab(b.dataset.tab)),
);
$("#refreshLogs")?.addEventListener("click", refreshLogs);
for (const id of ["logLevel", "logEvent", "logRequest", "logCorrelation"]) {
  $("#" + id)?.addEventListener("change", refreshLogs);
  $("#" + id)?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") refreshLogs();
  });
}
$("#refreshDiagnostics")?.addEventListener("click", refreshDiagnostics);
$("#downloadDiagnostics")?.addEventListener("click", () =>
  downloadDiagnostics().catch(showError),
);
$("#adminTourButton")?.addEventListener("click", () => {
  adminTourSetState("");
  startAdminTour(true);
});
$("#adminTourSkip")?.addEventListener("click", () =>
  finishAdminTour("skipped"),
);
$("#adminTourClose")?.addEventListener("click", () =>
  finishAdminTour("skipped"),
);
$("#adminTourBack")?.addEventListener("click", () => {
  if (adminTourIndex > 0) {
    adminTourIndex--;
    adminTourPersist("in_progress");
    renderAdminTour();
  }
});
$("#adminTourNext")?.addEventListener("click", () => {
  if (adminTourIndex >= ADMIN_TOUR_STEPS.length - 1)
    finishAdminTour("completed");
  else {
    adminTourIndex++;
    adminTourPersist("in_progress");
    renderAdminTour();
  }
});
window.addEventListener("resize", () => {
  if ($("#adminTourLayer") && !$("#adminTourLayer").hidden) adminTourPosition();
});
$("#refreshFeedback")?.addEventListener("click", refreshFeedback);
$("#providerPreset")?.addEventListener("change", configureProviderForm);
$("#providerType")?.addEventListener("change", configureProviderForm);
$("#saveVpnRouting")?.addEventListener("click", saveVpnRouting);
$("#refreshVpnRouting")?.addEventListener("click", refreshVpnRouting);
refreshAdminAuthStatus();
configureProviderForm();
$("#refreshProviders").onclick = async () => {
  await load();
  $("#providerState").textContent = adminText(
    "Discovery обновлён",
    "Discovery refreshed",
  );
  $("#providerState").className = "job-state completed";
};
$("#addProvider").onclick = async () => {
  const output = $("#providerState");
  output.textContent = adminText(
    "Проверяю подключение…",
    "Testing connection…",
  );
  output.className = "job-state running";
  try {
    const body = {
      name: $("#providerName").value.trim(),
      type: $("#providerType").value,
      base_url: $("#providerUrl").value.trim(),
      api_key: $("#providerKey").value,
      billing_class: $("#providerBillingClass").value,
      cost_input_per_million_rub: Number($("#providerInputCost").value || 0),
      cost_output_per_million_rub: Number($("#providerOutputCost").value || 0),
    };
    const result = await api("/api/admin/providers", {
      method: "POST",
      body: JSON.stringify(body),
    });
    output.textContent = `${adminText("Подключено. Обнаружено моделей", "Connected. Models discovered")}: ${result.provider.model_count}`;
    output.className = "job-state completed";
    $("#providerKey").value = "";
    await load();
  } catch (error) {
    output.textContent = error.message;
    output.className = "job-state failed";
  }
};
$("#saveRoutes").onclick = async () => {
  const mapping = {};
  $$("select[data-mode]").forEach(
    (select) => (mapping[select.dataset.mode] = parseRouteValue(select.value)),
  );
  const output = $("#saveState");
  try {
    await api("/api/admin/routing", {
      method: "POST",
      body: JSON.stringify({ routing: mapping }),
    });
    output.textContent = adminText("Сохранено", "Saved");
    output.className = "success-text";
    await load();
    selectTab("routing");
  } catch (error) {
    output.textContent = `${adminText("Ошибка", "Error")}: ${error.message}`;
    output.className = "error";
  }
};
$("#pullBtn").onclick = async () => {
  const model = $("#pullModel").value.trim();
  const provider_id = $("#pullProvider").value;
  const output = $("#pullState");
  if (!model) return;
  $("#pullBtn").disabled = true;
  try {
    const job = await api("/api/admin/models/pull", {
      method: "POST",
      body: JSON.stringify({ provider_id, model }),
    });
    output.textContent = adminText(
      "queued: 0% — В очереди",
      "queued: 0% — In queue",
    );
    output.className = "job-state running";
    const timer = setInterval(async () => {
      try {
        const result = await api(`/api/admin/jobs/${job.job_id}`);
        output.textContent = `${result.status}: ${result.progress}% — ${result.message || result.error || ""}`;
        if (["completed", "failed"].includes(result.status)) {
          clearInterval(timer);
          $("#pullBtn").disabled = false;
          output.className = `job-state ${result.status}`;
          if (result.status === "completed") {
            await load();
            selectTab("models");
          }
        }
      } catch (error) {
        clearInterval(timer);
        $("#pullBtn").disabled = false;
        output.textContent = error.message;
        output.className = "job-state failed";
      }
    }, 500);
  } catch (error) {
    $("#pullBtn").disabled = false;
    output.textContent = `${adminText("Ошибка", "Error")}: ${error.message}`;
    output.className = "job-state failed";
  }
};
$("#saveBillingConfig").onclick = async () => {
  const output = $("#billingConfigState");
  try {
    const provider = $("#billingProvider").value;
    const body = {
      provider,
      shop_id: $("#billingShopId").value.trim(),
      public_base_url: $("#billingPublicUrl").value.trim(),
    };
    if ($("#billingSecret").value) body.secret_key = $("#billingSecret").value;
    const result = await api("/api/admin/billing/payment-config", {
      method: "POST",
      body: JSON.stringify(body),
    });
    output.textContent = result.payment_config.configured
      ? adminText(
          "ЮKassa настроена. Укажите webhook URL в кабинете ЮKassa.",
          "YooKassa configured. Set the webhook URL in YooKassa dashboard.",
        )
      : adminText("Платёжный provider отключён.", "Payment provider disabled.");
    output.className = "job-state completed";
    $("#billingSecret").value = "";
    await load();
    selectTab("billing");
  } catch (error) {
    output.textContent = error.message;
    output.className = "job-state failed";
  }
};

$("#topupBalanceBtn")?.addEventListener("click", adjustBillingBalance);
$("#createPromoBtn")?.addEventListener("click", createBillingPromo);
$("#fetchDeployFingerprint").onclick = async () => {
  const out = $("#deployTargetState");
  try {
    const result = await api("/api/admin/deployments/fingerprint", {
      method: "POST",
      body: JSON.stringify({
        host: $("#deployHost").value.trim(),
        port: Number($("#deployPort").value || 22),
      }),
    });
    $("#deployFingerprint").value = result.fingerprint.sha256;
    out.textContent = `${result.fingerprint.type} · ${result.fingerprint.sha256}`;
    out.className = "job-state completed";
  } catch (error) {
    out.textContent = error.message;
    out.className = "job-state failed";
  }
};
$("#saveDeployTarget").onclick = async () => {
  const out = $("#deployTargetState");
  try {
    await api("/api/admin/deployments", {
      method: "POST",
      body: JSON.stringify({
        name: $("#deployName").value.trim() || "VPS",
        host: $("#deployHost").value.trim(),
        port: Number($("#deployPort").value || 22),
        username: $("#deployUser").value.trim(),
        domain: $("#deployDomain").value.trim(),
        profile: $("#deployProfile").value,
        host_key_sha256: $("#deployFingerprint").value.trim(),
      }),
    });
    out.textContent = adminText(
      "Target сохранён. SSH credential не сохранялся.",
      "Target saved. SSH credentials were not stored.",
    );
    out.className = "job-state completed";
    await refreshDeployments();
  } catch (error) {
    out.textContent = error.message;
    out.className = "job-state failed";
  }
};
$("#deployBootstrap").onclick = () => runDeploymentAction("bootstrap");
$("#deployPreflight").onclick = () => runDeploymentAction("preflight");
$("#deployPublish").onclick = () => runDeploymentAction("deploy");
$("#deployVpnApply").onclick = () => runDeploymentAction("vpn-apply");
$("#deployVpnApplyServer").onclick = () =>
  runDeploymentAction("vpn-apply-server");
$("#deployRollback").onclick = () => runDeploymentAction("rollback");
$("#refreshMonitoring").onclick = refreshMonitoring;
$("#saveRegistrationPolicy").onclick = async () => {
  const out = $("#registrationPolicyState");
  try {
    const result = await api("/api/admin/auth/registration-policy", {
      method: "POST",
      body: JSON.stringify({
        registration_policy: $("#registrationPolicy").value,
      }),
    });
    out.textContent = `${adminText("Сохранено", "Saved")}: ${result.registration_policy}`;
    out.className = "job-state completed";
    await load();
    selectTab("users");
  } catch (error) {
    out.textContent = error.message;
    out.className = "job-state failed";
  }
};
$("#refreshSearchPolicy")?.addEventListener("click", refreshSearchPolicy);
$("#saveSearchPolicy")?.addEventListener("click", saveSearchPolicy);
$("#refreshSiteProfiles")?.addEventListener("click", async () => {
  try {
    const result = await api("/api/admin/site-profiles");
    siteProfiles = result.profiles || [];
    renderSiteProfiles();
  } catch (error) {
    alert(error.message);
  }
});
$("#copyLanUrl").onclick = async () => {
  const value = lanStatus?.url || "";
  if (!value) return;
  try {
    await navigator.clipboard.writeText(value);
  } catch (_) {}
  $("#copyLanUrl").textContent = adminText("Скопировано", "Copied");
  setTimeout(
    () =>
      ($("#copyLanUrl").textContent = adminText(
        "Скопировать адрес",
        "Copy address",
      )),
    1200,
  );
};
(async () => {
  try {
    const me = await api("/api/auth/me");
    csrfToken = me.csrf_token || "";
    const role = String(me.user?.role || "").toUpperCase();
    if (["OWNER", "ADMIN"].includes(role)) {
      roleAdmin = true;
      $("#login").hidden = true;
      $("#admin").hidden = false;
      $("#adminNav").hidden = false;
      $("#logoutBtn").hidden = false;
      $("#logoutBtn").textContent = adminText(
        "Выйти из аккаунта",
        "Sign out of account",
      );
      await load();
      maybeStartAdminTour();
      return;
    }
  } catch (_) {}
  if (token) {
    try {
      $("#login").hidden = true;
      $("#admin").hidden = false;
      $("#adminNav").hidden = false;
      $("#logoutBtn").hidden = false;
      await load();
      return;
    } catch (_) {
      sessionStorage.removeItem("par-admin-token");
      token = "";
    }
  }
})();

function ensureSupportInboxPanel() {
  const feedbackTab = document.querySelector('[data-panel="feedback"]');
  if (!feedbackTab || $("#supportMailboxList")) return;
  const panel = node("div", "panel");
  const heading = node("div", "panel-heading");
  const left = node("div", "");
  left.append(
    node("span", "eyebrow", "SUPPORT MAIL"),
    node("h2", "", status?.support_email || "support@rodnoi-agent.ru"),
  );
  const button = node(
    "button",
    "secondary-button",
    adminText("Обновить inbox", "Refresh inbox"),
  );
  button.type = "button";
  button.onclick = () => refreshSupportInbox();
  const meta = node("p", "muted", adminText("Загрузка…", "Loading…"));
  meta.id = "supportMailboxMeta";
  const list = node("div", "feedback-admin-list");
  list.id = "supportMailboxList";
  heading.append(left, button);
  panel.append(heading, meta, list);
  feedbackTab.append(panel);
}
function renderSupportInbox(payload) {
  ensureSupportInboxPanel();
  const meta = $("#supportMailboxMeta"),
    host = $("#supportMailboxList");
  if (!meta || !host) return;
  clear(host);
  const inbox = payload?.inbox || status?.support_inbox || {};
  const email =
    payload?.support_email ||
    status?.support_email ||
    "support@rodnoi-agent.ru";
  const heading = meta.previousElementSibling?.querySelector("h2");
  if (heading) heading.textContent = email;
  meta.textContent = inbox.enabled
    ? `${email} · ${adminText("непрочитано", "unread")}: ${Number(inbox.unread || 0)} · ${adminText("всего", "total")}: ${Number(inbox.total || 0)}`
    : adminText(
        "Inbox поддержки ещё не готов: проверьте контейнер smtp и volume support-mail.",
        "Support inbox is not ready yet: check the smtp container and the support-mail volume.",
      );
  if (!payload?.items?.length) {
    host.append(
      node("p", "muted", adminText("Писем пока нет.", "No messages yet.")),
    );
    return;
  }
  for (const item of payload.items) {
    const card = node("article", "feedback-admin-card");
    const top = node("div", "provider-card-head");
    top.append(
      node(
        "strong",
        "",
        item.subject || adminText("(без темы)", "(no subject)"),
      ),
      node("span", "provider-meta", item.state || ""),
    );
    card.append(
      top,
      node("p", "", item.preview || ""),
      node(
        "small",
        "muted",
        `${item.from || "unknown"} → ${item.to || email} · ${new Date(Number(item.received_at || 0) * 1000).toLocaleString(adminLang() === "en" ? "en-US" : "ru-RU")}`,
      ),
    );
    host.append(card);
  }
}
async function refreshSupportInbox() {
  ensureSupportInboxPanel();
  const meta = $("#supportMailboxMeta"),
    host = $("#supportMailboxList");
  if (meta) meta.textContent = adminText("Загрузка…", "Loading…");
  if (host) host.textContent = "";
  try {
    supportInboxStatus = await api("/api/admin/support-inbox?limit=50");
    renderSupportInbox(supportInboxStatus);
  } catch (error) {
    if (meta) meta.textContent = error.message;
  }
}
function mailField(
  id,
  labelRu,
  labelEn,
  type = "text",
  rows = 0,
  placeholder = "",
) {
  const wrap = document.createElement("label");
  const title = document.createElement("span");
  title.textContent = adminText(labelRu, labelEn);
  wrap.append(title);
  const control =
    rows > 0
      ? document.createElement("textarea")
      : document.createElement("input");
  control.id = id;
  if (rows > 0) control.rows = rows;
  else control.type = type;
  if (placeholder) control.placeholder = placeholder;
  wrap.append(control);
  return wrap;
}
function ensureMailSettingsPanel() {
  const feedbackTab = document.querySelector('[data-panel="feedback"]');
  if (!feedbackTab || $("#mailSettingsForm")) return;
  const panel = node("div", "panel");
  const heading = node("div", "panel-heading");
  const left = node("div", "");
  left.append(
    node("span", "eyebrow", "EMAIL & SUPPORT"),
    node("h2", "", adminText("Почта и поддержка", "Mail and support")),
  );
  const summary = node(
    "p",
    "muted",
    adminText(
      "Оформление писем, адрес поддержки и тестовая отправка меняются здесь без деплоя. SMTP в env остаётся транспортом доставки.",
      "Configure email appearance, support address and test delivery here without redeploying. SMTP in env remains the transport layer.",
    ),
  );
  summary.id = "mailSettingsSummary";
  heading.append(left);
  panel.append(heading, summary);
  const form = node("div", "provider-form");
  form.id = "mailSettingsForm";
  form.append(
    mailField("mailProductName", "Название продукта", "Product name"),
    mailField("mailSupportEmail", "Почта поддержки", "Support email", "email"),
    mailField("mailSupportName", "Имя поддержки", "Support name"),
    mailField("mailSenderEmail", "Email отправителя", "Sender email", "email"),
    mailField("mailSenderName", "Имя отправителя", "Sender name"),
    mailField("mailReplyToEmail", "Reply-To email", "Reply-To email", "email"),
    mailField(
      "mailPublicBaseUrl",
      "Публичный URL",
      "Public base URL",
      "url",
      0,
      "https://rodnoi-agent.ru",
    ),
    mailField(
      "mailFooterText",
      "Текстовый footer",
      "Plain-text footer",
      "text",
      4,
    ),
    mailField("mailFooterHtml", "HTML footer", "HTML footer", "text", 8),
    mailField(
      "mailVerifySubject",
      "Тема подтверждения",
      "Verification subject",
    ),
    mailField(
      "mailVerifyText",
      "Текст подтверждения",
      "Verification text",
      "text",
      8,
    ),
    mailField(
      "mailVerifyHtml",
      "HTML подтверждения",
      "Verification HTML",
      "text",
      10,
    ),
    mailField(
      "mailResetSubject",
      "Тема сброса пароля",
      "Password reset subject",
    ),
    mailField(
      "mailResetText",
      "Текст сброса пароля",
      "Password reset text",
      "text",
      8,
    ),
    mailField(
      "mailResetHtml",
      "HTML сброса пароля",
      "Password reset HTML",
      "text",
      10,
    ),
  );
  const vars = node(
    "div",
    "info-callout",
    adminText(
      "Переменные шаблонов: {product_name}, {support_email}, {support_name}, {sender_name}, {sender_email}, {reply_to_email}, {url}, {expires_at_utc}, {action}, {year}.",
      "Template variables: {product_name}, {support_email}, {support_name}, {sender_name}, {sender_email}, {reply_to_email}, {url}, {expires_at_utc}, {action}, {year}.",
    ),
  );
  const actions = node("div", "panel-actions");
  const save = node(
    "button",
    "primary-button",
    adminText("Сохранить почтовые настройки", "Save mail settings"),
  );
  save.type = "button";
  save.onclick = () => saveMailSettings();
  const test = node(
    "button",
    "secondary-button",
    adminText("Отправить тест", "Send test"),
  );
  test.type = "button";
  test.onclick = () => sendMailSettingsTest();
  actions.append(save, test);
  const testForm = node("div", "provider-form");
  testForm.style.marginTop = "16px";
  testForm.append(
    mailField("mailTestRecipient", "Тестовый email", "Test email", "email"),
    (() => {
      const label = document.createElement("label");
      const span = document.createElement("span");
      span.textContent = adminText("Тип письма", "Email type");
      const select = document.createElement("select");
      select.id = "mailTestKind";
      for (const item of [
        { value: "verify", ru: "Подтверждение email", en: "Verify email" },
        { value: "reset", ru: "Сброс пароля", en: "Password reset" },
      ]) {
        const option = document.createElement("option");
        option.value = item.value;
        option.textContent = adminText(item.ru, item.en);
        select.append(option);
      }
      label.append(span, select);
      return label;
    })(),
  );
  const state = node("p", "job-state");
  state.id = "mailSettingsState";
  panel.append(form, vars, actions, testForm, state);
  feedbackTab.insertBefore(panel, feedbackTab.firstChild);
}
function collectMailSettings() {
  return {
    product_name: $("#mailProductName")?.value.trim() || "",
    support_email: $("#mailSupportEmail")?.value.trim() || "",
    support_name: $("#mailSupportName")?.value.trim() || "",
    sender_email: $("#mailSenderEmail")?.value.trim() || "",
    sender_name: $("#mailSenderName")?.value.trim() || "",
    reply_to_email: $("#mailReplyToEmail")?.value.trim() || "",
    public_base_url: $("#mailPublicBaseUrl")?.value.trim() || "",
    footer_text: $("#mailFooterText")?.value || "",
    footer_html: $("#mailFooterHtml")?.value || "",
    templates: {
      verify: {
        subject: $("#mailVerifySubject")?.value.trim() || "",
        text: $("#mailVerifyText")?.value || "",
        html: $("#mailVerifyHtml")?.value || "",
      },
      reset: {
        subject: $("#mailResetSubject")?.value.trim() || "",
        text: $("#mailResetText")?.value || "",
        html: $("#mailResetHtml")?.value || "",
      },
    },
  };
}
function renderMailSettings() {
  ensureMailSettingsPanel();
  if (!emailSettings) return;
  const summary = $("#mailSettingsSummary");
  if (summary)
    summary.textContent = `${adminText("Отправитель", "Sender")}: ${emailSettings.sender_email || status?.support_email || "—"} · ${adminText("поддержка", "support")}: ${emailSettings.support_email || status?.support_email || "—"}`;
  const mapping = {
    mailProductName: emailSettings.product_name,
    mailSupportEmail: emailSettings.support_email,
    mailSupportName: emailSettings.support_name,
    mailSenderEmail: emailSettings.sender_email,
    mailSenderName: emailSettings.sender_name,
    mailReplyToEmail: emailSettings.reply_to_email,
    mailPublicBaseUrl: emailSettings.public_base_url,
    mailFooterText: emailSettings.footer_text,
    mailFooterHtml: emailSettings.footer_html,
    mailVerifySubject: emailSettings.templates?.verify?.subject,
    mailVerifyText: emailSettings.templates?.verify?.text,
    mailVerifyHtml: emailSettings.templates?.verify?.html,
    mailResetSubject: emailSettings.templates?.reset?.subject,
    mailResetText: emailSettings.templates?.reset?.text,
    mailResetHtml: emailSettings.templates?.reset?.html,
  };
  for (const [id, value] of Object.entries(mapping)) {
    const el = $("#" + id);
    if (el && document.activeElement !== el) el.value = value || "";
  }
}
async function saveMailSettings() {
  const out = $("#mailSettingsState");
  if (out) {
    out.textContent = "";
    out.className = "job-state running";
  }
  try {
    const payload = await api("/api/admin/email-settings", {
      method: "POST",
      body: JSON.stringify(collectMailSettings()),
    });
    emailSettings = payload.settings || null;
    if (status && emailSettings?.support_email)
      status.support_email = emailSettings.support_email;
    renderMailSettings();
    if (out) {
      out.textContent = adminText(
        "Почтовые настройки сохранены.",
        "Mail settings saved.",
      );
      out.className = "job-state completed";
    }
  } catch (error) {
    if (out) {
      out.textContent = error.message;
      out.className = "job-state failed";
    }
  }
}
async function sendMailSettingsTest() {
  const out = $("#mailSettingsState");
  if (out) {
    out.textContent = adminText(
      "Отправляю тестовое письмо…",
      "Sending test email…",
    );
    out.className = "job-state running";
  }
  try {
    const recipient = $("#mailTestRecipient")?.value.trim() || "";
    const kind = $("#mailTestKind")?.value || "verify";
    const payload = await api("/api/admin/email-settings/test", {
      method: "POST",
      body: JSON.stringify({ recipient, kind }),
    });
    if (out) {
      out.textContent = payload.delivered
        ? adminText("Тестовое письмо отправлено.", "Test email sent.")
        : adminText(
            "SMTP не отправил письмо.",
            "SMTP did not send the message.",
          );
      out.className = payload.delivered
        ? "job-state completed"
        : "job-state failed";
    }
  } catch (error) {
    if (out) {
      out.textContent = error.message;
      out.className = "job-state failed";
    }
  }
}
async function refreshFeedback() {
  const host = $("#feedbackList");
  if (host) host.textContent = adminText("Загрузка…", "Loading…");
  ensureMailSettingsPanel();
  ensureSupportInboxPanel();
  try {
    const [payload, supportPayload, mailPayload] = await Promise.all([
      api("/api/admin/feedback"),
      api("/api/admin/support-inbox?limit=50"),
      api("/api/admin/email-settings"),
    ]);
    supportInboxStatus = supportPayload;
    emailSettings = mailPayload.settings || emailSettings;
    if (status && emailSettings?.support_email)
      status.support_email = emailSettings.support_email;
    renderFeedbackItems(payload.items || []);
    renderMailSettings();
    renderSupportInbox(supportPayload);
  } catch (error) {
    if (host) host.textContent = error.message;
    const meta = $("#supportMailboxMeta");
    if (meta) meta.textContent = error.message;
    const state = $("#mailSettingsState");
    if (state) state.textContent = error.message;
  }
}
