'use strict';

const $=s=>document.querySelector(s);
const SUPPORT_EMAIL_DEFAULT='support@rodnoi-agent.ru';
const AUTH_HONEYPOT_DEFAULT='company';

const AUTH_I18N={
 ru:{
  brand:'Родной Агент',
  editionLocal:'Локальная версия',
  editionServer:'Серверная версия',
  login:'Войти',
  register:'Создать аккаунт',
  forgotPassword:'Восстановление доступа',
  resetPassword:'Новый пароль',
  verifyEmail:'Подтверждение email',
  profile:'Профиль',
  account:'АККАУНТ',
  email:'Email',
  password:'Пароль',
  remember:'Запомнить меня на этом устройстве',
  create:'Зарегистрироваться',
  hasAccount:'Уже есть аккаунт? Войти',
  newAccount:'Создать аккаунт',
  back:'← В Родной Агент',
  logout:'Выйти',
  sessions:'Активные сессии',
  otherSessions:'Выйти на других устройствах',
  serverMode:'Свой сервер',
  localMode:'Локальный профиль',
  profileInfoPersonal:'Локальный personal-профиль. Регистрация не требуется.',
  profileInfoServer:'{email} · {role} · {mode}',
  requestBalanceTitle:'Баланс запросов',
  requestBalanceReady:'Локальные модели без лимита. Удалённый лимит: {tokens}. Остаток по стоимости: {rub}.',
  requestBalanceNoRemote:'Локальные модели без лимита. Платформенный remote-лимит пока не настроен.',
  requestBalanceExceeded:'Лимит удалённых запросов исчерпан. Смените режим выполнения, дождитесь обновления периода или выберите другой тариф.',
  usageTitle:'Использование AI',
  usageLocal:'Локально: {tokens} токенов',
  usageRemote:'Платформенный remote: {used} / {limit}',
  usageByok:'Свой ключ: {tokens} токенов',
  billingManual:'Ручное пополнение работает через заявку администратору или промокод. Откройте YooMoney в новой вкладке, затем отправьте reference платежа для зачисления.',
  topupUnavailable:'Не удалось отправить заявку на пополнение. Проверьте сумму и reference платежа.',
  promoUnavailable:'Не удалось активировать промокод. Проверьте код или обратитесь к администратору.',
  themesUnavailable:'Каталог дополнительных тем пока пуст. Базовые темы доступны в настройках интерфейса.',
  themePurchase:'покупка с баланса',
  themeBuy:'Купить',
  themeOwned:'Уже куплена',
  themePurchased:'Тема подключена. Баланс:',
  topupRequested:'Заявка на пополнение отправлена администратору.',
  promoApplied:'Промокод активирован. Баланс обновлён.',
  emailVerified:'Email подтверждён.',
  emailUnverified:'Email ещё не подтверждён. Ссылка для подтверждения доступна на странице входа.',
  topupHistoryEmpty:'Заявок на пополнение пока нет.',
  showTokens:'Показывать токены в ответах',
  noSessions:'Активных сессий нет.',
  lastActive:'Последняя активность',
  remembered:' · запомнено',
  current:' · текущая',
  signInInstead:'Войти',
  inactiveSession:'Сессия не активна.',
  topupBlockedTitle:'YooMoney в браузере',
  topupBlockedDetail:'Встроенная панель YooMoney может блокироваться браузером или провайдером. Откройте оплату в новой вкладке, затем отправьте reference платежа на этой странице.',
  topupOpenLink:'Открыть YooMoney в новой вкладке',
  topupStepsTitle:'Как пополнить баланс',
  topupStepsDetail:'1. Откройте YooMoney. 2. Выполните оплату. 3. Вернитесь на эту страницу и отправьте reference для ручного зачисления.',
  loginSupportNote:'Для восстановления доступа используйте ссылку «Забыли пароль?». Если письмо не пришло или нужен живой ответ, напишите на {support}.',
  registerTrustNote:'Указывайте реальный email: ссылка подтверждения и восстановление пароля работают через одноразовые ссылки с ограниченным сроком действия. По вопросам регистрации: {support}.',
  forgotLead:'Введите email аккаунта. Если восстановление доступно, система подготовит ссылку для смены пароля.',
  forgotLeadNoEmail:'Введите email аккаунта. Если восстановление доступно, письмо для сброса будет отправлено после настройки SMTP на сервере. Если доступ нужен срочно, напишите на {support}.',
  resetLead:'Укажите новый пароль для аккаунта. Ссылка действует ограниченное время.',
  verifyLead:'Проверяю ссылку подтверждения и состояние аккаунта.',
  verifyRequestLead:'Если ссылка подтверждения потеряна, можно подготовить новую.',
  forgotSubmit:'Отправить запрос',
  resetSubmit:'Сохранить новый пароль',
  verifySubmit:'Подтвердить email',
  verifyRequestSubmit:'Отправить письмо повторно',
  backToLogin:'Вернуться ко входу',
  toLogin:'Ко входу',
  forgotLink:'Забыли пароль?',
  recoveryLinkTitle:'Ссылка для восстановления',
  verificationLinkTitle:'Ссылка для подтверждения',
  openLink:'Открыть',
  emailDeliverySent:'Письмо отправлено. Проверьте почту.',
  emailDeliveryDisabled:'Почтовая отправка не настроена на сервере. Заполните SMTP в deploy/server/.env.vps и повторите запрос. Для ручной помощи: {support}.',
  emailDeliveryFailed:'Письмо не отправлено. Проверьте SMTP на сервере в deploy/server/.env.vps и запросите письмо повторно. Если проблема осталась, используйте {support}.',
  captchaRequired:'Подтвердите, что вы не робот.',
  tokenChecking:'Проверяю ссылку…',
  tokenInvalid:'Ссылка недействительна или уже устарела.',
  tokenExpired:'Срок действия ссылки истёк.',
  tokenReadyReset:'Ссылка активна. Можно задать новый пароль.',
  tokenReadyVerify:'Ссылка активна. Можно подтвердить email.',
  tokenAlreadyUsed:'Эта ссылка уже была использована.',
  resetReady:'Если аккаунт существует и готов к восстановлению, ссылка подготовлена.',
  verifyReady:'Если аккаунт существует и ждёт подтверждения, ссылка подготовлена.',
  verifyPendingAdmin:'Email подтверждён. Аккаунт ещё ждёт активации администратором.',
  verifyDone:'Email подтверждён. Вход выполнен.',
  verifyRequestDone:'Если аккаунт существует и ждёт подтверждения, новая ссылка подготовлена.',
  resetDone:'Пароль обновлён. Вход выполнен.',
  registrationPendingVerify:'Аккаунт создан, но перед входом нужно подтвердить email.',
  registrationPendingApproval:'Регистрация создана. Ожидается одобрение администратора.',
  registrationPendingBoth:'Регистрация создана. Подтвердите email, затем дождитесь одобрения администратора.',
 },
 en:{
  brand:'Personal Agent',
  editionLocal:'Local edition',
  editionServer:'Server edition',
  login:'Sign in',
  register:'Create account',
  forgotPassword:'Recover access',
  resetPassword:'New password',
  verifyEmail:'Verify email',
  profile:'Profile',
  account:'ACCOUNT',
  email:'Email',
  password:'Password',
  remember:'Remember me on this device',
  create:'Create account',
  hasAccount:'Already have an account? Sign in',
  newAccount:'Create account',
  back:'← Back to Personal Agent',
  logout:'Sign out',
  sessions:'Active sessions',
  otherSessions:'Sign out on other devices',
  serverMode:'Self-hosted server',
  localMode:'Local profile',
  profileInfoPersonal:'Local personal profile. Registration is not required.',
  profileInfoServer:'{email} · {role} · {mode}',
  requestBalanceTitle:'Request balance',
  requestBalanceReady:'Local models are unlimited. Remote quota: {tokens}. Cost remaining: {rub}.',
  requestBalanceNoRemote:'Local models are unlimited. Platform remote quota is not configured yet.',
  requestBalanceExceeded:'The remote quota is exhausted. Change execution mode, wait for renewal, or switch the plan.',
  usageTitle:'AI usage',
  usageLocal:'Local: {tokens} tokens',
  usageRemote:'Platform remote: {used} / {limit}',
  usageByok:'BYOK: {tokens} tokens',
  billingManual:'Manual top-up works via an administrator-confirmed request or a promo code. Open YooMoney in a new tab, then send the payment reference for reconciliation.',
  topupUnavailable:'The top-up request could not be sent. Check the amount and payment reference.',
  promoUnavailable:'The promo code could not be redeemed. Check the code or contact the administrator.',
  themesUnavailable:'The additional theme catalog is empty. Built-in themes are available in Settings.',
  themePurchase:'balance purchase',
  themeBuy:'Buy',
  themeOwned:'Owned',
  themePurchased:'Theme enabled. Balance:',
  topupRequested:'The top-up request was sent to the administrator.',
  promoApplied:'The promo code was redeemed. Balance updated.',
  emailVerified:'Email verified.',
  emailUnverified:'Email is not verified yet. A verification link is available on the sign-in page.',
  topupHistoryEmpty:'No top-up requests yet.',
  showTokens:'Show token usage in answers',
  noSessions:'No active sessions.',
  lastActive:'Last active',
  remembered:' · remembered',
  current:' · current',
  signInInstead:'Sign in',
  inactiveSession:'Session is not active.',
  topupBlockedTitle:'YooMoney in browser',
  topupBlockedDetail:'The embedded YooMoney panel may be blocked by the browser or the provider. Open YooMoney in a new tab, then send the payment reference on this page.',
  topupOpenLink:'Open YooMoney in a new tab',
  topupStepsTitle:'How to top up',
  topupStepsDetail:'1. Open YooMoney. 2. Complete the payment. 3. Return here and send the payment reference for reconciliation.',
  registerTrustNote:'Use a real email address: verification and password recovery use one-time links with a limited lifetime. Registration questions: {support}.',
  forgotLead:'Enter the account email. If recovery is available, a password reset email will be sent.',
  forgotLeadNoEmail:'Enter the account email. If recovery is available, the reset email will be sent after SMTP is configured on the server. For urgent help, contact {support}.',
  resetLead:'Set a new password for the account. The link is valid for a limited time.',
  verifyLead:'Checking the verification link and account state.',
  verifyRequestLead:'If the verification link was lost, you can prepare a new one.',
  forgotSubmit:'Send request',
  resetSubmit:'Save new password',
  verifySubmit:'Verify email',
  verifyRequestSubmit:'Resend email',
  backToLogin:'Back to sign in',
  toLogin:'To sign in',
  forgotLink:'Forgot password?',
  recoveryLinkTitle:'Recovery link',
  verificationLinkTitle:'Verification link',
  openLink:'Open',
  emailDeliverySent:'The email was sent. Check your inbox.',
  emailDeliveryDisabled:'Email delivery is not configured on the server. Fill SMTP settings in deploy/server/.env.vps and request it again. For manual help, contact {support}.',
  emailDeliveryFailed:'The email was not sent. Check server SMTP in deploy/server/.env.vps and request it again. If it still fails, contact {support}.',
  captchaRequired:'Confirm that you are not a robot.',
  tokenChecking:'Checking the link…',
  tokenInvalid:'The link is invalid or already expired.',
  tokenExpired:'The link has expired.',
  tokenReadyReset:'The link is active. You can set a new password.',
  tokenReadyVerify:'The link is active. You can verify the email.',
  tokenAlreadyUsed:'This link was already used.',
  resetReady:'If the account exists and can be recovered, the link is ready.',
  verifyReady:'If the account exists and is waiting for verification, the link is ready.',
  verifyPendingAdmin:'Email verified. The account is still waiting for administrator activation.',
  verifyDone:'Email verified. You are now signed in.',
  verifyRequestDone:'If the account exists and is waiting for verification, a new link is ready.',
  resetDone:'Password updated. You are now signed in.',
  registrationPendingVerify:'The account was created, but email verification is required before sign-in.',
  registrationPendingApproval:'Registration created. Waiting for administrator approval.',
  registrationPendingBoth:'Registration created. Verify the email, then wait for administrator approval.',
 }
};

function authLang(){return localStorage.getItem('par-ui-language')==='en'?'en':'ru'}
function T(){return AUTH_I18N[authLang()]}
function AT(ru,en){return authLang()==='en'?en:ru}
function fill(text,vars){return String(text).replace(/\{(\w+)\}/g,(_,key)=>String(vars?.[key]??''))}
function supportEmail(state){return String(state?.support_email||window.__authSystemState?.support_email||SUPPORT_EMAIL_DEFAULT)}
function authSecurity(state){return state?.auth_security||window.__authSystemState?.auth_security||{}}
function honeypotFieldName(state){return String(authSecurity(state).honeypot_field||AUTH_HONEYPOT_DEFAULT)}
function queryToken(){return new URLSearchParams(location.search).get('token')||''}
function authRuntimeProfile(state){return String(state?.runtime_profile||'local').toLowerCase()==='server'?'server':'local'}
function authEditionLabel(lang=authLang(),state=null){const t=AUTH_I18N[lang];return authRuntimeProfile(state)==='server'?t.editionServer:t.editionLocal}
function formatTokens(value){const n=Number(value||0);if(n>=1_000_000)return `${(n/1_000_000).toFixed(2)}M`;if(n>=1000)return `${(n/1000).toFixed(1)}K`;return String(n)}
function formatRub(value){if(value===null||value===undefined)return '—';return `${Number(value||0).toFixed(2)} ₽`}
const AUTH_THEME_COLOR_MAP={system:'#0b0c0f',dark:'#0b0c0f',light:'#f6f7f9',ocean:'#0d1530',forest:'#0d180f',sunset:'#1e120c',sand:'#1b160d',coral:'#1f1015'};
function effectiveAuthTheme(value){if(value==='system')return matchMedia('(prefers-color-scheme: light)').matches?'light':'dark';return value||'dark'}
function setAuthTheme(){
 const pref=localStorage.getItem('par-theme-preference')||'system';
 const theme=effectiveAuthTheme(pref);
 document.documentElement.dataset.theme=theme;
 const root=document.documentElement;
 const palette={light:{bg:'#f6f7f9',panel:'#ffffff',panel2:'#f0f2f5',panel3:'#e7eaf0',line:'#dce0e7',line2:'#cdd3dc',muted:'#667085',text:'#16181d',soft:'#414753',accent:'#17191f'},dark:{bg:'#0b0c0f',panel:'#111318',panel2:'#161920',panel3:'#1d212a',line:'#272b35',line2:'#343945',muted:'#9096a3',text:'#f7f7f8',soft:'#c8ccd4',accent:'#f3f4f6'},ocean:{bg:'#08111d',panel:'#0e1727',panel2:'#132033',panel3:'#19304a',line:'#20344f',line2:'#2c4d77',muted:'#8eaad1',text:'#f3f8ff',soft:'#c8ddff',accent:'#76b7ff'},forest:{bg:'#08150e',panel:'#0e1c12',panel2:'#13261a',panel3:'#183524',line:'#23402c',line2:'#35604a',muted:'#8fbea0',text:'#f1fbf5',soft:'#cce8d4',accent:'#75d29f'},sunset:{bg:'#170f0c',panel:'#241713',panel2:'#2d1d18',panel3:'#39251f',line:'#4d2c24',line2:'#6a4035',muted:'#d2ab97',text:'#fff8f4',soft:'#f0d5c8',accent:'#ff9c66'},sand:{bg:'#17130c',panel:'#231d13',panel2:'#2c2418',panel3:'#382e1f',line:'#4a3d28',line2:'#685739',muted:'#d7c099',text:'#fffaf1',soft:'#f1e0c2',accent:'#e7c78c'},coral:{bg:'#171012',panel:'#241518',panel2:'#2e1b20',panel3:'#3a2329',line:'#4d2a34',line2:'#6f3b4a',muted:'#d9a8b8',text:'#fff7fa',soft:'#f4d0dc',accent:'#ff7e9b'}}[theme]||null;
 if(palette){for(const [key,val] of Object.entries(palette))root.style.setProperty(`--${key}`,val)}
 document.querySelector('meta[name="theme-color"]')?.setAttribute('content',AUTH_THEME_COLOR_MAP[theme]||AUTH_THEME_COLOR_MAP.dark);
}
function setLabel(id,text){const el=$(id),label=el?.closest('label');if(!label)return;for(const n of label.childNodes){if(n.nodeType===Node.TEXT_NODE&&n.textContent.trim()){n.textContent=text;break}}}
function ensureSupportLink(state){
 const email=supportEmail(state);
 const host=document.querySelector('.legal-links')||document.querySelector('.auth-links');
 if(!host)return;
 let link=$('#supportEmailLink');
 if(!link){
  link=document.createElement('a');
  link.id='supportEmailLink';
  host.append(link);
 }
 link.href=`mailto:${email}`;
 link.textContent=email;
}

let turnstileScriptPromise=null;
function loadTurnstileScript(){
 const security=authSecurity();
 if(!security.turnstile_site_key)return Promise.resolve(null);
 if(window.turnstile)return Promise.resolve(window.turnstile);
 if(turnstileScriptPromise)return turnstileScriptPromise;
 turnstileScriptPromise=new Promise((resolve,reject)=>{
  const script=document.createElement('script');
  script.src='https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
  script.async=true;
  script.defer=true;
  script.onload=()=>resolve(window.turnstile||null);
  script.onerror=()=>reject(new Error('Turnstile failed to load'));
  document.head.append(script);
 });
 return turnstileScriptPromise;
}

function ensureAuthSecurityFields(form,state){
 if(!form)return;
 const honeypot=honeypotFieldName(state);
 if(honeypot&&!form.querySelector(`[name="${honeypot}"]`)){
  const input=document.createElement('input');
  input.type='text';
  input.name=honeypot;
  input.tabIndex=-1;
  input.autocomplete='off';
  input.setAttribute('aria-hidden','true');
  input.style.position='absolute';
  input.style.left='-10000px';
  input.style.top='auto';
  input.style.width='1px';
  input.style.height='1px';
  input.style.opacity='0';
  form.append(input);
 }
}

async function ensureTurnstile(form,state){
 if(!form)return;
 const security=authSecurity(state);
 if(!security.turnstile_enabled||!security.turnstile_site_key)return;
 if(form.dataset.turnstileReady==='1')return;
 const api=await loadTurnstileScript();
 if(!api)return;
 let holder=form.querySelector('.turnstile-slot');
 if(!holder){
  holder=document.createElement('div');
  holder.className='turnstile-slot';
  holder.style.marginTop='12px';
  form.append(holder);
 }
 const widgetId=api.render(holder,{
  sitekey:security.turnstile_site_key,
  theme:document.documentElement.dataset.theme==='light'?'light':'dark',
  callback:token=>{form.dataset.turnstileToken=token||'';},
  'expired-callback':()=>{form.dataset.turnstileToken='';},
  'error-callback':()=>{form.dataset.turnstileToken='';}
 });
 form.dataset.turnstileWidgetId=String(widgetId);
 form.dataset.turnstileReady='1';
}

function authPayload(form,state,payload){
 const out={...(payload||{})};
 const honeypot=honeypotFieldName(state);
 const honeypotInput=honeypot?form?.querySelector(`[name="${honeypot}"]`):null;
 if(honeypot)out[honeypot]=honeypotInput?.value||'';
 const security=authSecurity(state);
 if(security.turnstile_enabled)out.captcha_token=form?.dataset.turnstileToken||'';
 return out;
}

function updateStaticProfileCopy(){
 const t=T();
 $('#balanceTitle')&&( $('#balanceTitle').textContent=t.requestBalanceTitle );
 $('#usageTitle')&&( $('#usageTitle').textContent=t.usageTitle );
 $('#showTokensLabel')&&( $('#showTokensLabel').childNodes[$('#showTokensLabel').childNodes.length-1].textContent=` ${t.showTokens}` );
 $('#topupIntro')&&($('#topupIntro').textContent=t.billingManual);
 $('#topupBlockedTitle')&&($('#topupBlockedTitle').textContent=t.topupBlockedTitle);
 $('#topupBlockedDetail')&&($('#topupBlockedDetail').textContent=t.topupBlockedDetail);
 $('#topupOpenLink')&&($('#topupOpenLink').textContent=t.topupOpenLink);
 $('#topupStepsTitle')&&($('#topupStepsTitle').textContent=t.topupStepsTitle);
 $('#topupStepsDetail')&&($('#topupStepsDetail').textContent=t.topupStepsDetail);
 $('#themeIntro')&&($('#themeIntro').textContent=t.themesUnavailable);
 $('#themeState')&&($('#themeState').textContent=t.themesUnavailable);
}

function applyAuthLanguage(lang=authLang(),state=null){
 localStorage.setItem('par-ui-language',lang);
 document.documentElement.lang=lang;
 const t=AUTH_I18N[lang];
 const brand=$('.localized-brand');
 if(brand)brand.textContent=t.brand;
 const edition=$('.localized-edition');
 if(edition)edition.textContent=authEditionLabel(lang,state);
 const page=document.body.dataset.authPage;
  const h1=$('.auth-card h1');
 if(h1&&page!=='account')h1.textContent=page==='login'?t.login:page==='register'?t.register:page==='forgot-password'?t.forgotPassword:page==='reset-password'?t.resetPassword:page==='verify-email'?t.verifyEmail:h1.textContent;
 const eyebrow=$('.eyebrow');
 if(eyebrow)eyebrow.textContent=page==='account'?(lang==='en'?'PROFILE':'ПРОФИЛЬ'):t.account;
 setLabel('#email',t.email);
 setLabel('#password',t.password);
 const remember=$('#rememberMe')?.closest('label');
 if(remember){
  const txt=Array.from(remember.childNodes).find(n=>n.nodeType===Node.TEXT_NODE&&n.textContent.trim());
  if(txt)txt.textContent=' '+t.remember;
 }
 const submit=$('#authForm button[type="submit"]');
 if(submit)submit.textContent=page==='login'?t.login:page==='register'?t.create:page==='forgot-password'?t.forgotSubmit:page==='reset-password'?t.resetSubmit:page==='verify-email'?t.verifySubmit:submit.textContent;
 const requestSubmit=$('#requestVerificationForm button[type="submit"]');
 if(requestSubmit)requestSubmit.textContent=t.verifyRequestSubmit;
 for(const a of document.querySelectorAll('.auth-links a')){
  if(a.getAttribute('href')==='/')a.textContent=t.back;
  else if(a.getAttribute('href')==='/register')a.textContent=t.newAccount;
  else if(a.getAttribute('href')==='/login')a.textContent=page==='register'?t.hasAccount:t.backToLogin;
  else if(a.getAttribute('href')==='/forgot-password')a.textContent=t.forgotLink;
 }
 if($('#logoutBtnUser'))$('#logoutBtnUser').textContent=t.logout;
 const support=supportEmail(state);
 if($('#loginSupportNote'))$('#loginSupportNote').textContent=fill(t.loginSupportNote,{support});
 if($('#registerTrustNote'))$('#registerTrustNote').textContent=fill(t.registerTrustNote,{support});
 if($('#forgotLead'))$('#forgotLead').textContent=fill(t.forgotLead,{support});
 if($('#resetLead'))$('#resetLead').textContent=t.resetLead;
 if($('#verifyLead'))$('#verifyLead').textContent=queryToken()?t.verifyLead:t.verifyRequestLead;
 if($('#recoveryLinkTitle'))$('#recoveryLinkTitle').textContent=t.recoveryLinkTitle;
 if($('#recoveryLink'))$('#recoveryLink').textContent=t.openLink;
 if($('#tokenState')&&$('#tokenState').textContent.trim()==='')$('#tokenState').textContent=t.tokenChecking;
 if($('#sessionSection h2'))$('#sessionSection h2').textContent=t.sessions;
 if($('#revokeOtherSessions'))$('#revokeOtherSessions').textContent=t.otherSessions;
 document.title=(page==='login'?t.login:page==='register'?t.register:page==='forgot-password'?t.forgotPassword:page==='reset-password'?t.resetPassword:page==='verify-email'?t.verifyEmail:t.profile)+' — '+t.brand;
 const toggle=$('#localeToggle');
 if(toggle)toggle.textContent=lang==='en'?'RU':'EN';
 ensureSupportLink(state);
 updateStaticProfileCopy();
}

let csrfToken='';
async function api(path,options){
 const opts={...(options||{})};
 const method=String(opts.method||'GET').toUpperCase();
 opts.headers={...(opts.headers||{})};
 if(!['GET','HEAD','OPTIONS'].includes(method)&&csrfToken)opts.headers['X-CSRF-Token']=csrfToken;
 const response=await fetch(path,opts);
 let payload={};
 try{payload=await response.json()}catch(_){}
 if(payload.csrf_token)csrfToken=payload.csrf_token;
 if(!response.ok){
  const error=new Error(payload.error||'Ошибка запроса');
  error.status=response.status;
  throw error;
 }
 return payload;
}

async function loadConfig(){
 const [authState,systemState]=await Promise.allSettled([api('/api/auth/me'),api('/api/system')]);
 if(systemState.status==='fulfilled')window.__authSystemState=systemState.value||{};
 if(authState.status==='rejected'){
  if(authState.reason?.status===401){
   return {ok:false,mode:'accounts',runtime_profile:systemState.status==='fulfilled'?systemState.value.runtime_profile:'local',support_email:systemState.status==='fulfilled'?systemState.value.support_email:SUPPORT_EMAIL_DEFAULT,auth_security:systemState.status==='fulfilled'?systemState.value.auth_security||{}:{}};
  }
  throw authState.reason;
 }
 const state=authState.value||{};
 if(systemState.status==='fulfilled'){
  if(systemState.value?.runtime_profile)state.runtime_profile=systemState.value.runtime_profile;
  if(systemState.value?.support_email)state.support_email=systemState.value.support_email;
  if(systemState.value?.auth_security)state.auth_security=systemState.value.auth_security;
 }
 return state;
}

function planName(plan){
 if(authLang()!=='en')return plan.display_name;
 return ({LIGHT:'Light',MEDIUM:'Medium',PRO:'Pro',ADMIN:'Admin'})[plan.id]||plan.display_name;
}

function planDescription(plan){
 if(plan.id==='ADMIN')return AT('Администратор: коммерческих ограничений нет. Локальные и удалённые вызовы только учитываются в статистике.','Administrator: no commercial limits. Local and remote calls are still measured in usage statistics.');
 const remote=Number(plan.remote_token_limit||0)>0
  ? AT(`Remote API: до ${formatTokens(plan.remote_token_limit)} токенов/мес. по текущей настройке администратора.`,`Remote API: up to ${formatTokens(plan.remote_token_limit)} tokens/month under the current admin configuration.`)
  : AT('Platform-paid remote API по умолчанию отключён до настройки лимита администратором.','Platform-paid remote API is disabled by default until an administrator configures a quota.');
 return `${AT('Локальные модели — без лимита.','Local models are unlimited.')} ${remote}`;
}

function renderPlanCatalog(plans,current){
 const host=$('#planCatalog');
 if(!host)return;
 host.replaceChildren();
 for(const plan of plans){
  const card=document.createElement('article');
  card.className='plan-card';
  if(plan.id===current)card.classList.add('current');
  const title=document.createElement('strong');
  title.textContent=planName(plan);
  const price=document.createElement('span');
  price.className='plan-price';
  price.textContent=plan.price_rub?`${plan.price_rub} ₽/${AT('мес','mo')}`:AT('Бесплатно','Free');
  const copy=document.createElement('small');
  copy.textContent=`${AT('Локально без лимита','Unlimited local')} · ${AT('поддержка','support')}: ${plan.support_level}`;
  card.append(title,price,copy);
  if(plan.id!==current){
   const button=document.createElement('button');
   button.className='secondary-button';
   button.type='button';
   button.textContent=plan.price_rub?AT('Подключить','Choose plan'):AT('Перейти на Лайт','Switch to Light');
   button.onclick=()=>changePlan(plan.id);
   card.append(button);
  }
  host.append(card);
 }
}

async function changePlan(planId){
 const state=$('#billingState');
 state.textContent='';
 try{
  const result=await api('/api/billing/checkout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({plan_id:planId})});
  if(result.confirmation_url){
   location.href=result.confirmation_url;
   return;
  }
  state.textContent=result.free?AT('Тариф изменён. Обновляю…','Plan changed. Refreshing…'):AT('Платёж создан.','Payment created.');
  state.className='job-state completed';
  setTimeout(()=>location.reload(),350);
 }catch(error){
  state.textContent=error.message+(error.status===503?AT(' — администратору нужно подключить платёжный API.',' — an administrator needs to configure the payment API.'):'');
  state.className='job-state failed';
 }
}

function renderEntitlements(snapshot){
 const host=$('#entitlementSummary');
 if(!host)return;
 host.replaceChildren();
 const labels=authLang()==='en'
  ? {chat:'Chat',web:'Web search',research:'Research',files_read:'Read files',files_create:'Create files',code:'Development',remote_ai:'Remote AI',advanced_exports:'Advanced export'}
  : {chat:'Чат',web:'Веб-поиск',research:'Исследование',files_read:'Чтение файлов',files_create:'Создание файлов',code:'Разработка',remote_ai:'Удалённый AI',advanced_exports:'Расширенный экспорт'};
 for(const [key,label] of Object.entries(labels)){
  const item=snapshot?.entitlements?.features?.[key];
  if(!item)continue;
  const chip=document.createElement('span');
  chip.className=`entitlement-chip ${item.enabled?'on':'off'}`;
  chip.textContent=`${item.enabled?'✓':'×'} ${label}`;
  host.append(chip);
 }
}

function renderUsage(snapshot){
 const local=snapshot.usage?.by_class?.LOCAL||{total_tokens:0};
 const remote=snapshot.usage?.by_class?.PLATFORM_REMOTE||{total_tokens:0};
 const byok=snapshot.usage?.by_class?.BYOK||{total_tokens:0};
 const quota=snapshot.quota||{};
 const usageParts=[fill(T().usageLocal,{tokens:formatTokens(local.total_tokens)})];
 if(Number(remote.total_tokens||0)||quota.platform_remote_tokens_limit!==null){
  usageParts.push(fill(T().usageRemote,{used:formatTokens(remote.total_tokens),limit:quota.platform_remote_tokens_limit===null?'∞':formatTokens(quota.platform_remote_tokens_limit)}));
 }
 if(Number(byok.total_tokens||0))usageParts.push(fill(T().usageByok,{tokens:formatTokens(byok.total_tokens)}));
 $('#usageSummary').textContent=usageParts.join(' · ');
}

function renderRequestBalance(snapshot){
 const quota=snapshot.quota||{};
 const summary=$('#balanceSummary');
 const state=$('#balanceState');
 if(!summary||!state)return;
 const tokenRemaining=quota.platform_remote_tokens_remaining;
 const costRemaining=quota.platform_remote_cost_rub_remaining;
 if(tokenRemaining===null&&costRemaining===null){
  summary.textContent=T().requestBalanceNoRemote;
  state.textContent=AT('Доступны локальные запросы и BYOK.','Local requests and BYOK are available.');
  state.className='job-state';
  return;
 }
 summary.textContent=fill(T().requestBalanceReady,{
  tokens:tokenRemaining===null?'∞':formatTokens(tokenRemaining),
  rub:costRemaining===null?'∞':formatRub(costRemaining),
 });
 if((tokenRemaining!==null&&tokenRemaining<=0)||(costRemaining!==null&&costRemaining<=0)){
  state.textContent=T().requestBalanceExceeded;
  state.className='job-state failed';
 }else{
  state.textContent=AT('Лимиты активны и обновляются по расчётному периоду тарифа.','Quota is active and renews with the billing period.');
  state.className='job-state completed';
 }
}

function renderTopupHistory(snapshot){
 const host=$('#topupHistory');
 if(!host)return;
 host.replaceChildren();
 const items=snapshot.topup_requests||[];
 if(!items.length){
  host.append(Object.assign(document.createElement('p'),{className:'muted',textContent:T().topupHistoryEmpty}));
  return;
 }
 for(const item of items){
  const row=document.createElement('div');
  row.className='usage-admin-row';
  const ref=item.payment_reference?` · ref ${item.payment_reference}`:'';
  const note=item.note?` · ${item.note}`:'';
  row.append(
   Object.assign(document.createElement('strong'),{textContent:`${Number(item.amount_rub||0).toFixed(2)} ₽`}),
   Object.assign(document.createElement('span'),{textContent:item.source||'yoomoney'}),
   Object.assign(document.createElement('span'),{textContent:item.status}),
   Object.assign(document.createElement('span'),{textContent:`${new Date(Number(item.created_at||0)*1000).toLocaleString(authLang()==='en'?'en-US':'ru-RU')}${ref}${note}`})
  );
  host.append(row);
 }
}

function setupBillingActions(){
 const themeCatalog=$('#themeCatalog');
 if(themeCatalog){
  themeCatalog.replaceChildren();
  const themes=window.__billingSnapshot?.themes||[];
  if(!themes.length){
   const note=document.createElement('div');note.className='account-note';note.textContent=T().themesUnavailable;themeCatalog.append(note);
  }else{
   for(const theme of themes){
    const row=document.createElement('div');row.className='plan-row';
    const copy=document.createElement('div');copy.append(Object.assign(document.createElement('strong'),{textContent:theme.name}),Object.assign(document.createElement('small'),{textContent:theme.owned?T().themeOwned:`${Number(theme.price_rub||0).toFixed(0)} ₽ · ${T().themePurchase}`}));
    const button=document.createElement('button');button.type='button';button.className='secondary-button';button.textContent=theme.owned?T().themeOwned:T().themeBuy;button.disabled=!!theme.owned;
    button.onclick=async()=>{const stateNode=$('#themeState');try{const result=await api('/api/billing/themes/purchase',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({theme_id:theme.id})});if(stateNode){stateNode.textContent=`${T().themePurchased} ${formatRub(result.balance?.balance_rub)}`;stateNode.className='job-state completed'}await loadBilling()}catch(error){if(stateNode){stateNode.textContent=error.message;stateNode.className='job-state failed'}}};row.append(copy,button);themeCatalog.append(row);
   }
  }
 }
 const topupState=$('#topupState');
 const promoState=$('#promoState');
 $('#requestTopup').onclick=async()=>{
  if(!topupState)return;
  topupState.textContent='';
  try{
   const result=await api('/api/billing/topup-requests',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({amount_rub:Number($('#topupAmountRub')?.value||0),payment_reference:$('#topupPaymentReference')?.value||'',note:$('#topupNote')?.value||'',source:'yoomoney'})});
   topupState.textContent=T().topupRequested;
   topupState.className='job-state completed';
   $('#topupAmountRub').value='';
   $('#topupPaymentReference').value='';
   $('#topupNote').value='';
   window.__billingSnapshot={...(window.__billingSnapshot||{}),topup_requests:[result.topup_request,...((window.__billingSnapshot?.topup_requests)||[])]};
   renderTopupHistory(window.__billingSnapshot);
  }catch(error){
   topupState.textContent=error.message||T().topupUnavailable;
   topupState.className='job-state failed';
  }
 };
 $('#redeemPromoCode').onclick=async()=>{
  if(!promoState)return;
  promoState.textContent='';
  try{
   const result=await api('/api/billing/promocodes/redeem',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code:$('#promoCodeInput')?.value||''})});
   promoState.textContent=`${T().promoApplied} ${formatRub(result.balance?.balance_rub)}`;
   promoState.className='job-state completed';
   $('#promoCodeInput').value='';
   setTimeout(()=>location.reload(),400);
  }catch(error){
   promoState.textContent=error.message||T().promoUnavailable;
   promoState.className='job-state failed';
  }
 };
}

async function loadBilling(){
 const [snapshot,plans]=await Promise.all([api('/api/billing/me'),api('/api/billing/plans')]);
 const box=$('#billingAccount');
 box.hidden=false;
 const plan=snapshot.plan;
 $('#currentPlan').textContent=planName(plan);
 $('#currentPlanPrice').textContent=plan.price_rub?`${plan.price_rub} ₽/${AT('мес','mo')}`:'0 ₽';
 $('#planDescription').textContent=planDescription(plan);
 renderRequestBalance(snapshot);
 renderUsage(snapshot);
 window.__billingSnapshot=snapshot;
 renderTopupHistory(snapshot);
 const toggle=$('#showTokens');
 toggle.checked=!!snapshot.preferences.show_token_usage;
 toggle.onchange=async()=>{
  try{
   await api('/api/billing/preferences',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({show_token_usage:toggle.checked})});
  }catch(error){
   toggle.checked=!toggle.checked;
   $('#billingState').textContent=error.message;
  }
 };
 renderPlanCatalog(plans.plans||[],plan.id);
 setupBillingActions();
 return snapshot;
}

function sessionLabel(item){
 const ua=String(item.user_agent||'');
 let device=AT('Устройство','Device');
 if(/Android|iPhone|Mobile/i.test(ua))device=AT('Телефон','Phone');
 else if(/Windows/i.test(ua))device='Windows';
 else if(/Macintosh|Mac OS/i.test(ua))device='Mac';
 return `${device}${item.ip?` · ${item.ip}`:''}${item.current?T().current:''}`;
}

async function loadSessions(){
 const section=$('#sessionSection');
 if(!section)return;
 try{
  const result=await api('/api/auth/sessions');
  section.hidden=false;
  const host=$('#sessionList');
  host.replaceChildren();
  const active=(result.sessions||[]).filter(s=>!s.revoked_at&&Number(s.expires_at||0)>Date.now()/1000);
  for(const item of active){
   const row=document.createElement('div');
   row.className='session-row';
   const copy=document.createElement('div');
   const strong=document.createElement('strong');
   strong.textContent=sessionLabel(item);
   const small=document.createElement('small');
   small.textContent=`${T().lastActive}: ${new Date(Number(item.last_seen_at||0)*1000).toLocaleString(authLang()==='en'?'en-US':'ru-RU')}${item.remember_me?T().remembered:''}`;
   copy.append(strong,small);
   row.append(copy);
   if(!item.current){
    const b=document.createElement('button');
    b.className='secondary-button';
    b.type='button';
    b.textContent=AT('Завершить','End');
    b.onclick=async()=>{await api(`/api/auth/sessions/${item.id}/revoke`,{method:'POST',body:'{}'});await loadSessions()};
    row.append(b);
   }
   host.append(row);
  }
  if(!active.length)host.textContent=T().noSessions;
  $('#revokeOtherSessions').onclick=async()=>{
   try{
    await api('/api/auth/sessions/revoke-all',{method:'POST',body:'{}'});
    $('#sessionState').textContent=AT('Другие сессии завершены.','Other sessions ended.');
    await loadSessions();
   }catch(error){
    $('#sessionState').textContent=error.message;
   }
  };
 }catch(error){
  section.hidden=false;
  $('#sessionState').textContent=error.message;
 }
}

function profileModeLabel(state){
 return authRuntimeProfile(state)==='server'?T().serverMode:T().localMode;
}

function revealLink(link,kind='recovery'){
 const wrap=$('#recoveryLinkWrap');
 const anchor=$('#recoveryLink');
 const title=$('#recoveryLinkTitle');
 if(!wrap||!anchor||!link)return;
 if(title)title.textContent=kind==='verify'?T().verificationLinkTitle:T().recoveryLinkTitle;
 anchor.href=link;
 anchor.textContent=T().openLink;
 wrap.hidden=false;
}

function hideRevealLink(){
 const wrap=$('#recoveryLinkWrap');
 const anchor=$('#recoveryLink');
 if(anchor){
  anchor.removeAttribute('href');
  anchor.textContent=T().openLink;
 }
 if(wrap)wrap.hidden=true;
}

function deliveryMessage(mode){
 if(mode==='smtp')return T().emailDeliverySent;
 if(mode==='failed')return fill(T().emailDeliveryFailed,{support:supportEmail()});
 if(mode==='disabled')return fill(T().emailDeliveryDisabled,{support:supportEmail()});
 if(mode==='skipped')return '';
 return '';
}

async function loadTokenState(kind,token){
 const holder=$('#tokenState');
 if(!holder)return null;
 holder.textContent=T().tokenChecking;
 try{
  const result=await api(kind==='verify'?`/api/auth/verify-email?token=${encodeURIComponent(token)}`:`/api/auth/password-reset?token=${encodeURIComponent(token)}`);
  const state=result.token_status||{};
  if(state.used_at)holder.textContent=T().tokenAlreadyUsed;
  else if(state.expired)holder.textContent=T().tokenExpired;
  else if(state.usable)holder.textContent=kind==='verify'?T().tokenReadyVerify:T().tokenReadyReset;
  else holder.textContent=T().tokenInvalid;
  return state;
 }catch(error){
  holder.textContent=T().tokenInvalid;
  return null;
 }
}

async function init(){
 setAuthTheme();
 applyAuthLanguage();
 const page=document.body.dataset.authPage;
 const error=$('#authError');
 const success=$('#authSuccess');
 const authForm=$('#authForm');
 const requestVerificationForm=$('#requestVerificationForm');
 let state;
 try{state=await loadConfig()}catch(exc){if(error)error.textContent=exc.message;return}
 applyAuthLanguage(authLang(),state);
 ensureAuthSecurityFields(authForm,state);
 ensureAuthSecurityFields(requestVerificationForm,state);
 try{
  await Promise.all([ensureTurnstile(authForm,state),ensureTurnstile(requestVerificationForm,state)]);
 }catch(_){}
 $('#localeToggle')?.addEventListener('click',()=>applyAuthLanguage(authLang()==='en'?'ru':'en',state));
 if(page==='register'){
  if(state.mode==='personal'){
   const lead=$('#authLead');
   if(lead)lead.textContent=AT('Сейчас включён локальный personal-профиль: регистрация не требуется. Для VPS/multi-user администратор включает режим аккаунтов.','Local personal mode is enabled: registration is not required. For VPS/multi-user, an administrator enables accounts mode.');
   $('#authForm').hidden=true;
   return;
  }
 authForm.onsubmit=async event=>{
   event.preventDefault();
   error.textContent='';
   success.textContent='';
   hideRevealLink();
   try{
    const payload=authPayload(authForm,state,{display_name:$('#displayName').value,email:$('#email').value,password:$('#password').value});
    if(authSecurity(state).turnstile_required&&!payload.captcha_token)throw new Error(T().captchaRequired);
    const result=await api('/api/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    if(result.verification_required&&result.status==='pending')success.textContent=T().registrationPendingBoth;
    else if(result.verification_required)success.textContent=T().registrationPendingVerify;
    else if(result.status==='pending')success.textContent=T().registrationPendingApproval;
    else{
     sessionStorage.setItem('par-tour-trigger','1');
     success.textContent=AT('Аккаунт создан. Вход выполнен.','Account created and signed in.');
     setTimeout(()=>location.href='/',500);
    }
    if(result.verification_url)revealLink(result.verification_url,'verify');
    else if(result.verification_required&&result.email_delivery)success.textContent=`${success.textContent} ${deliveryMessage(result.email_delivery)}`.trim();
   }catch(exc){error.textContent=exc.message}
  };
 }
 if(page==='login'){
  if(state.mode==='personal'){
   success.textContent=AT('Сейчас включён локальный personal-профиль: отдельный вход пользователю не требуется.','Local personal mode is enabled: a separate user sign-in is not required.');
   $('#authForm').hidden=true;
   return;
  }
  if(state.ok&&state.user){location.href='/account';return}
  authForm.onsubmit=async event=>{
   event.preventDefault();
   error.textContent='';
   try{
    const payload=authPayload(authForm,state,{email:$('#email').value,password:$('#password').value,remember_me:!!$('#rememberMe')?.checked});
    await api('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    location.href='/';
   }catch(exc){error.textContent=exc.message}
  };
 }
 if(page==='forgot-password'){
  if(state.mode==='personal'){
   success.textContent=AT('Сейчас включён локальный personal-профиль: отдельное восстановление пароля не требуется.','Local personal mode is enabled: separate password recovery is not required.');
   $('#authForm').hidden=true;
   return;
  }
  const lead=$('#forgotLead');
  if(lead&&state.mode==='accounts')lead.textContent=T().forgotLead;
  authForm.onsubmit=async event=>{
   event.preventDefault();
   error.textContent='';
   success.textContent='';
   hideRevealLink();
   try{
    const payload=authPayload(authForm,state,{email:$('#email').value});
    if(authSecurity(state).turnstile_required&&!payload.captcha_token)throw new Error(T().captchaRequired);
    const result=await api('/api/auth/password-reset/request',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    success.textContent=deliveryMessage(result.email_delivery)||T().resetReady;
    if(result.reset_url)revealLink(result.reset_url,'recovery');
   }catch(exc){error.textContent=exc.message}
  };
 }
 if(page==='reset-password'){
  const token=queryToken();
  const tokenState=await loadTokenState('reset',token);
  if(!tokenState?.usable)return;
  $('#authForm').hidden=false;
  $('#authForm').onsubmit=async event=>{
   event.preventDefault();
   error.textContent='';
   success.textContent='';
   try{
    await api('/api/auth/password-reset/confirm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token,password:$('#password').value})});
    success.textContent=T().resetDone;
    setTimeout(()=>location.href='/',700);
   }catch(exc){error.textContent=exc.message}
  };
  return;
 }
 if(page==='verify-email'){
  const token=queryToken();
  if(!token){
   $('#tokenState').textContent=T().verifyRequestLead;
   $('#requestVerificationForm').hidden=false;
   requestVerificationForm.onsubmit=async event=>{
    event.preventDefault();
    error.textContent='';
    success.textContent='';
    hideRevealLink();
    try{
     const payload=authPayload(requestVerificationForm,state,{email:$('#email').value});
     if(authSecurity(state).turnstile_required&&!payload.captcha_token)throw new Error(T().captchaRequired);
     const result=await api('/api/auth/verify-email/request',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
     success.textContent=deliveryMessage(result.email_delivery)||T().verifyRequestDone;
     if(result.verification_url)revealLink(result.verification_url,'verify');
    }catch(exc){error.textContent=exc.message}
   };
   return;
  }
  const tokenState=await loadTokenState('verify',token);
  if(!tokenState?.usable)return;
  $('#authForm').hidden=false;
  $('#authForm').onsubmit=async event=>{
   event.preventDefault();
   error.textContent='';
   success.textContent='';
   try{
    const result=await api('/api/auth/verify-email',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token})});
    success.textContent=result.user?.status==='active'?T().verifyDone:T().verifyPendingAdmin;
    if(result.user?.status==='active')sessionStorage.setItem('par-tour-trigger','1');
    setTimeout(()=>location.href=result.user?.status==='active'?'/':'/login',700);
   }catch(exc){error.textContent=exc.message}
  };
  return;
 }
 if(page==='account'){
  const info=$('#accountInfo');
 if(state.user){
   $('#accountTitle').textContent=state.user.display_name||T().profile;
   info.textContent=state.mode==='personal'
    ? T().profileInfoPersonal
    : fill(T().profileInfoServer,{email:state.user.email||'',role:state.user.role||'USER',mode:profileModeLabel(state)});
   const verification=$('#accountVerification');
   if(verification){
    verification.textContent=Number(state.user.email_verified||0)?T().emailVerified:T().emailUnverified;
   }
   try{
    const snapshot=await loadBilling();
    renderEntitlements(snapshot);
    if(state.mode==='accounts')await loadSessions();
   }catch(exc){
    const bs=$('#billingState');
    if(bs){
     bs.textContent=exc.message;
     bs.className='job-state failed';
    }
   }
  }else{
   info.textContent=T().inactiveSession;
   $('#logoutBtnUser').textContent=T().signInInstead;
   $('#logoutBtnUser').onclick=()=>location.href='/login';
   return;
  }
  $('#logoutBtnUser').onclick=async()=>{
   if(state.mode==='personal'){location.href='/';return}
   try{await api('/api/auth/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})}
   finally{location.href='/login'}
  };
 }
}

init();
window.addEventListener('pageshow',event=>{if(event.persisted)location.reload()});
