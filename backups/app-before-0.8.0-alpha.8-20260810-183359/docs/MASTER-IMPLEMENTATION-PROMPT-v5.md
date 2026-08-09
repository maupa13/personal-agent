# MASTER IMPLEMENTATION PROMPT — Personal Agent Rus

**Документ:** единый execution/specification contract  
**Версия документа:** 8.0  
**Файл:** MASTER-IMPLEMENTATION-PROMPT-v5.md  
**Дата:** 10.08.2026  
**Статус:** mandatory source of truth until superseded by a later approved version

> LIVE STATE > RELEASE EVIDENCE > THIS DOCUMENT'S HISTORICAL BASELINES > ASSUMPTIONS

1. PRODUCT IDENTITY
   Семейство продукта:

Personal Agent

Текущая региональная редакция:

Personal Agent Rus

Архитектура должна позволять впоследствии существование:

Personal Agent Rus

Personal Agent EU

Personal Agent US

Personal Agent Enterprise

других editions

Поэтому региональная специфика не должна жёстко зашиваться в общее ядро.

Разделять:

text
Personal Agent Core
+
Edition configuration
↓
Personal Agent Rus
Пример manifest:

text
{
"product_family": "Personal Agent",
"product": "Personal Agent Rus",
"edition": "rus",
"locale": "ru-RU",
"slug": "personal-agent-rus"
}
1.1. BUSINESS OBJECTIVES
Personal Agent Rus создаётся как коммерчески жизнеспособный продукт, решающий реальные задачи пользователей:

Ускорение ежедневной работы – быстрый доступ к информации, автоматизация рутины, генерация документов и кода.

Повышение качества принимаемых решений – за счёт анализа множества источников, верификации фактов и структурирования результатов.

Снижение порога входа в AI-технологии – пользователь взаимодействует с продуктом, а не с инфраструктурой (модели, провайдеры, API).

Конфиденциальность и контроль – локальный запуск, возможность полного отключения внешних сервисов, прозрачная политика обработки данных.

Удобная и безопасная аутентификация – пользователь может зарегистрироваться по email/паролю или через VK ID, с полным контролем своих данных.

Монетизация через полезную рекламу – при поиске товаров или услуг пользователь видит релевантные предложения (с явной плашкой "Реклама"), администратор настраивает рекламные кампании через удобную панель.

Сбор обезличенных данных для аналитики – для улучшения продукта и предложения более релевантного контента (с соблюдением законодательства и пользовательского соглашения).

Гибкость в выборе моделей – поддержка не только локальных (Ollama, llama.cpp), но и внешних API, включая DeepSeek, OpenAI, Anthropic и другие, с единым интерфейсом.

Все архитектурные решения должны служить этим бизнес-целям.

1.2. UNIQUE VALUE PROPOSITION
Personal Agent Rus отличается от конкурентов тем, что:

Результат сразу виден – пользователь получает конкретный, проверенный результат (документ, анализ, код, исследование), а не просто "ответ".

Прозрачная монетизация – пользователь понимает, за что платит (подписка или разовые задачи), и видит ценность сразу.

Гибкая настройка – администратор может адаптировать продукт под любую бизнес-модель (подписка, pay-per-use, рекламная модель).

Конфиденциальность – локальный запуск, опциональный remote, полный контроль над данными.

Русский контекст – продукт изначально спроектирован для русскоязычных пользователей, поддерживает русский язык на всех уровнях (UI, документация, модели), учитывает локальные сервисы (VK ID, российские маркетплейсы, законодательство).

Открытость для любых моделей – возможность подключать как локальные, так и удалённые модели через единый провайдер-адаптер (включая DeepSeek, OpenAI, Anthropic и другие).

1.3. RUSSIAN CONTEXT (ОСОБЕННОСТИ РУССКОЙ РЕДАКЦИИ)
Personal Agent Rus учитывает специфику русского рынка и пользователей:

Русский язык – интерфейс, документация, сообщения, подсказки – всё на русском языке. Технические термины могут быть на английском, но только там, где это общепринято (API, Docker и т.п.).

Локальные сервисы – поддержка VK ID как основного OAuth провайдера, интеграция с российскими маркетплейсами (для рекламных объявлений), поддержка российских платежных систем (ЮMoney, СБП и т.д.) – когда потребуется.

Законодательство – пользовательское соглашение и политика конфиденциальности должны строго соответствовать российскому законодательству (ФЗ-152 о персональных данных, закон о рекламе). Юрист должен иметь инструменты для проверки и внесения правок.

Сбор данных – только с явного согласия пользователя, все данные обезличены и не передаются третьим лицам без согласия.

Культурные особенности – юмор, примеры, тон общения агента соответствуют русскоязычной аудитории (без излишней формальности, но и без панибратства).

2. ГЛАВНЫЙ ПРОДУКТОВЫЙ ПРИНЦИП
   Personal Agent Rus — самостоятельный продукт.

Он НЕ должен восприниматься пользователем как:

Open WebUI;

Ollama;

Docker;

набор нейросетей;

набор Python scripts;

набор pipes/functions;

административная панель для AI-инженера.

Обычный USER работает с Personal Agent Rus.

В пользовательском интерфейсе НЕ показывать:

text
Open WebUI
Ollama
Docker
Compose
qwen3:...
model IDs
container IDs
pipe IDs
function IDs
provider technical IDs
Эти понятия относятся к реализации и ADMIN/Developer Mode.

Open WebUI может использоваться как legacy/reference/internal component только там, где это оправдано, но не является пользовательским shell и не является архитектурным центром нового продукта.

Предпочтительная новая архитектура — собственные:

Personal Agent Core;

API;

Browser UI;

orchestrator;

capability router;

model/provider registry;

task engine;

artifact system.

2.1. НЕФУНКЦИОНАЛЬНЫЕ ТРЕБОВАНИЯ
Помимо функциональных возможностей, продукт обязан удовлетворять следующим нефункциональным требованиям:

Производительность
Время отклика UI на действия пользователя не более 200 мс (без учёта генерации модели).

Первый токен ответа модели – не более 5 секунд после отправки запроса (на эталонной машине с рекомендованной моделью).

Загрузка страницы – не более 3 секунд.

Поддержка до 10 параллельных активных задач без значительной деградации.

Надёжность
Доступность (uptime) локального экземпляра – 99.9% при нормальных условиях.

Автоматическое восстановление после сбоев контейнеров без потери данных.

Время восстановления после краха Core – менее 30 секунд.

Масштабируемость
Возможность перехода от single-user к multi-user (VPS/сервер) без переписывания ядра.

Поддержка добавления новых моделей и провайдеров через конфигурацию.

Горизонтальное масштабирование browser-воркеров и очередей задач.

Сопровождаемость
Модульная архитектура с чёткими границами (Core, API, UI, Orchestrator, Capabilities).

Единый стиль кода, статический анализ, автоматическое форматирование.

Полный набор тестов (unit, интеграционные, E2E) с покрытием не менее 80% бизнес-логики.

Безопасность
Защита от OWASP Top 10 (XSS, CSRF, SSRF, инъекции, неправильная аутентификация и т.д.).

Изоляция пользовательского кода и внешнего контента.

Шифрование секретов и конфиденциальных данных в покое и при передаче.

Безопасное хранение паролей (bcrypt/Argon2), защита сессий, поддержка OAuth2 (VK ID).

Сбор данных пользователей только с их явного согласия, обезличивание для аналитики.

3. ОСНОВНОЙ DEPLOYMENT: DOCKER-FIRST + BROWSER-FIRST
   Главная версия продукта должна распространяться как Docker application.

Основной runtime:

text
Browser
↓
Personal Agent Rus UI
↓
Personal Agent Core
↓
Orchestrator
↓
Capabilities
↓
Model / Provider Router
↓
Ollama / other local engines / remote APIs (включая DeepSeek)
Основной пользовательский адрес локальной версии:

text
http://127.0.0.1:3100
или эквивалент, определённый конфигурацией.

Пользовательский runtime не должен требовать Playwright/E2E-контейнеры.

Разделять:

text
production compose
test/release acceptance compose
development compose
server/VPS compose
Не заставлять пользователя собирать большие test-images во время обычного START.

4. WINDOWS — REFERENCE DEVELOPMENT TARGET
   Текущая эталонная машина:

text
Windows 11
NVIDIA RTX 5070
VRAM: 12 GB
RAM: 32 GB
Docker Desktop
WSL2
Сначала оптимизировать продукт под этот мощный reference target.

Не тратить ранние milestone на поддержку слабых ПК.

После стабилизации reference build добавить hardware profiles:

text
CPU / Lite
6–8 GB VRAM
12 GB Quality
16–24 GB Max
Hybrid
Remote
Для Windows предусмотреть:

START;

STOP;

RESTART;

STATUS;

VERIFY;

REPAIR;

UPDATE;

BACKUP;

RESTORE;

diagnostics;

Windows reboot persistence;

optional autostart.

Операции lifecycle не должны использовать destructive volume operations.

Запрещено без специальной операции полного удаления:

text
docker compose down -v
docker volume prune
docker system prune
5. WINDOWS INSTALLER — УЧЕСТЬ, НО НЕ ДЕЛАТЬ ЯДРОМ
   Docker/browser version — первичная реализация продукта.

Позже сделать:

text
PersonalAgentRus-Setup.exe
Installer должен быть только удобным bootstrapper вокруг того же Docker/runtime продукта.

Не создавать отдельную Windows-кодовую базу.

Схема:

text
Setup.exe
↓
Windows preflight
↓
runtime prerequisites
↓
download signed Personal Agent release
↓
Docker/runtime
↓
compose up
↓
shortcut/autostart
↓
Browser UI
Installer должен иметь нормальный GUI:

text
Проверка компьютера
Установка runtime
Подготовка AI
Запуск сервисов
Проверка системы
Готово
Под техническим статусом разрешён personality layer с короткими шутками.

Примеры:

text
Проверяем компьютер.
Ни один гигабайт не пострадает без предупреждения.

Будим локальный интеллект.
Кофе ему не нужен, но VRAM пригодится.

Загружаем маленький контрольный мозг.
Серьёзную модель администратор выберет позже.

Проверяем пульс.
У нейросети он измеряется HTTP-кодами.

Специально кое-что ломаем.
Да, сейчас это действительно часть тестирования.

Готово.
Теперь можно работать.
Юмор никогда не заменяет настоящий status/error/progress.

При ERROR юмор отключить и показать:

stage;

конкретную ошибку;

retry;

repair;

details;

persistent log.

6. VPS / SERVER / HYBRID ДОЛЖНЫ БЫТЬ АРХИТЕКТУРНО ВОЗМОЖНЫ
   Тот же Personal Agent Core должен уметь работать:

text
Local PC
VPS
Linux server
NAS
GPU server
Предусмотреть:

text
compose.local.yaml
compose.server.yaml
compose.gpu.yaml
compose.dev.yaml
На VPS:

text
Internet
↓
HTTPS / Reverse Proxy
↓
Personal Agent Core
Не публиковать напрямую в интернет:

Ollama;

DB;

Playwright;

internal services;

Docker APIs.

Server deployment потребует:

authentication (email/password + VK ID);

users;

sessions;

HTTPS;

CSRF;

CORS policy;

secure cookies;

rate limiting;

audit;

quotas;

per-user workspace isolation;

secret management;

backups;

пользовательское соглашение и политика конфиденциальности;

рекламный движок и сбор аналитики.

В перспективе предусмотреть hybrid architecture:

text
VPS Control Plane
↓
encrypted connection
↓
Personal Agent Worker
↓
home RTX GPU
Если локальный worker offline — router может использовать remote fallback.

Не реализовывать hybrid раньше основного продукта, но не создавать архитектурных решений, которые сделают его невозможным.

7. MODELS — ТОЛЬКО ADMIN CONCERN
   USER не выбирает нейросеть.

USER выбирает понятный режим:

text
Авто
Быстро
Умно
Позже:

text
Исследование
Документы
Разработка
Изображения
Но UX не должен превращаться в model selector.

ADMIN управляет:

provider;

model;

capability mapping;

fallback;

context;

generation parameters.

Пример внутренней конфигурации:

text
{
"fast": {
"provider": "ollama",
"model": "qwen2:1.5b"
},
"smart": {
"provider": "deepseek",
"model": "deepseek-chat"
},
"coding": {
"provider": "anthropic",
"model": "claude-3-sonnet"
}
}
USER получает:

text
Быстро
Умно
Разработка
а не model ID.

8. BOOTSTRAP MODEL
   Installation/start acceptance не должен требовать тяжёлую production model.

Использовать маленькую bootstrap/smoke/fallback model.

Её задача:

text
container
→ GPU/runtime
→ inference
→ Core
→ API
→ Browser
Bootstrap model НЕ означает production routing.

После установки ADMIN выбирает настоящие модели.

9. MODEL / PROVIDER REGISTRY
   Нужен полноценный registry.

Абстракция:

text
Personal Agent
↓
Model Resolver
↓
Provider Adapter
├── Ollama
├── llama.cpp
├── LM Studio
├── DeepSeek (API)
├── OpenAI-compatible
├── Anthropic
└── другие remote providers
Не связывать продукт навсегда с одной моделью или Ollama.

Model Registry хранит:

provider;

model;

capabilities;

context;

tool support;

vision;

quality tier;

hardware requirements;

availability;

health;

fallback priority.

ADMIN должен уметь:

видеть установленные models;

загружать model;

удалять model;

назначать model режиму/capability;

менять provider;

проверять model health;

настраивать API-ключи и эндпоинты для внешних провайдеров (включая DeepSeek).

USER не имеет доступа к этим данным.

10. MODES И CAPABILITIES — НЕ СМЕШИВАТЬ
    Нельзя повторять прежнюю ошибку, где:

text
mode=smart
мог превращать WEB-задачу обратно в CHAT.

Разделять минимум:

text
effort
intent
capabilities
execution policy
Например пользователь:

text
«Умно сравни сегодняшние новости PostgreSQL»
должен давать:

text
{
"effort": "smart",
"intent": "research",
"capabilities": ["web"],
"freshness_required": true
}
а не:

text
CHAT
web=false
11. ORCHESTRATOR — ЦЕНТР БУДУЩЕГО ПРОДУКТА
    Сложный запрос не должен обрабатываться как один route.

Пример:

text
«Собери последние материалы с этих сайтов,
сравни их,
сделай Excel и PDF
и сохрани в рабочую папку»
должен превращаться примерно в:

text
REQUEST
↓
PLAN
↓
WEB_DISCOVERY
↓
SITE_EXTRACTION
↓
VERIFY_SOURCES
↓
ANALYZE
↓
CREATE_XLSX
↓
VALIDATE_XLSX
↓
CREATE_PDF
↓
VALIDATE_PDF
↓
SAVE_WORKSPACE
↓
COMPLETED
12. TASK STATE MODEL
    Использовать реальное состояние задач.

Минимально:

text
CREATED
PLANNING
WAITING_PERMISSION
RUNNING
VERIFYING
COMPLETED

FAILED
CANCELLED
ROLLING_BACK
ROLLED_BACK
USER должен видеть понятный progress:

text
Ищу источники
Читаю страницы
Сравниваю данные
Создаю таблицу
Проверяю PDF
Готово
Не показывать внутренние container/function/model names.

13. SUCCESS ТОЛЬКО ПОСЛЕ ПРОВЕРКИ
    Фундаментальный invariant:

Нельзя сообщать SUCCESS без фактической проверки результата.

Примеры.

Нельзя:

text
PDF готов
если PDF только предположительно создан.

Нужно:

text
create PDF
↓
file exists
↓
size > 0
↓
parser/open validation
↓
artifact record
↓
SUCCESS
Нельзя:

text
Сайт проверен
если browser/fetch реально не получил данные.

Нельзя:

text
Код исправлен
если tests не были запущены.

Нельзя:

text
Installation PASS
если проверен только START.

14. ARTIFACT CONTRACT
    Все созданные пользователем результаты должны иметь единый artifact contract.

Минимально:

text
artifact_id
job_id
name
mime
path/storage ref
size
SHA256
version
validation_status
created_at
source_refs
preview metadata
Artifact должен быть физически доступен пользователю.

15. FILE / WORKSPACE CAPABILITIES
    Обязательные форматы:

text
TXT
MD
JSON
CSV
PDF
DOCX
XLSX
PPTX
Для каждого acceptance включает:

text
create
↓
verify exists
↓
read/open
↓
verify content
↓
modify
↓
save
↓
read again
↓
artifact delivered
Проверять не только код генерации, но и пользовательский путь.

16. CODE CAPABILITY
    Поддерживать минимум:

Python;

PowerShell;

Java.

Позже другие языки.

Сценарий:

text
USER request
↓
create/change code
↓
compile
↓
tests
↓
failure if any
↓
repair
↓
rerun tests
↓
result
Проверять:

stdout;

stderr;

exit code;

timeout;

cancellation;

permissions;

generated files.

Нельзя использовать Thread.sleep как механизм синхронизации тестов/процессов.

17. WEB / SITE CAPABILITY
    Web — не просто «SearXNG search».

Нужны:

text
search
static fetch
dynamic browser
site parsing
site profiles
link follow
pagination
freshness
fallbacks
source verification
Обязательно тестировать реальные пользовательские сценарии минимум для классов сайтов, которые уже проходили раньше:

DTF;

Habr;

AWS articles;

Skillfactory;

JavaRush;

YouTube;

ЕГРЮЛ;

zakupki.gov.ru;

Google News / news search;

торговые площадки;

обычные static pages;

JavaScript-heavy pages.

Не считать внешний сайт дефектом продукта автоматически.

Если primary strategy не работает:

text
browser
↓ fail
static fetch
↓
search fallback
↓
site-specific profile
Если всё недоступно, Personal Agent должен честно сказать, что источник сейчас получить не удалось.

Никаких выдуманных данных.

18. RESEARCH
    Research должен поддерживать:

много источников;

дедупликацию;

freshness;

citations;

source verification;

conflicting sources;

unavailable sources;

summaries;

comparison;

reports.

Acceptance:

text
3+ sources
10+ sources
duplicate sources
one unavailable
several unavailable
conflicting claims
fresh information
citation opens
citation supports claim
Запрещены hallucinated sources.

19. VISION / IMAGE
    Предусмотреть:

image upload;

vision/analysis;

image generation;

image editing;

multimodal tasks.

UI не должен требовать знания ComfyUI.

ComfyUI или другой engine — implementation detail.

20. AUDIO
    Предусмотреть:

audio upload;

STT;

microphone input;

TTS;

voice response.

Whisper/Speaches и конкретные models — внутренние backend components.

21. VIDEO
    Предусмотреть:

video upload/analysis;

generation/editing в будущем;

jobs с долгим progress;

cancellation;

artifact validation.

Не делать обязательным для раннего foundation milestone.

22. AUTOMATION / ACTIONS
    В будущем Personal Agent должен уметь выполнять действия.

Любые destructive/external actions требуют permission model.

Разделять:

text
READ
WRITE
EXECUTE
EXTERNAL_ACTION
DESTRUCTIVE
Sensitive action:

text
plan
↓
permission
↓
execute
↓
verify
↓
audit
23. SECURITY
    USER и ADMIN — разные security boundaries.

USER:

не получает model IDs;

не имеет admin API;

не видит provider secrets;

не видит runtime internals.

ADMIN:

model registry;

providers;

routing;

runtime diagnostics;

system configuration.

Для server/VPS позже — настоящий multi-user auth.

Security acceptance минимум:

no token → 401;

invalid token → 401;

USER cannot call admin API;

invalid payload → 400;

path traversal blocked;

XSS blocked;

backend-controlled strings never injected unsafely via innerHTML;

CSP strict;

security headers;

secrets not returned in responses/logs;

filesystem isolation.

Не ослаблять CSP ради того, чтобы прошёл тест.

Тест должен работать с CSP продукта.

23.1. АУТЕНТИФИКАЦИЯ И РЕГИСТРАЦИЯ
Общие требования
Personal Agent Rus предоставляет пользователям следующие способы аутентификации:

Локальная регистрация по email и паролю.

Вход через VK ID (OAuth 2.0) — для удобства и быстрого доступа.

Оба способа должны сосуществовать, и пользователь может привязать VK ID к уже существующей учётной записи (или создать новую).

Регистрация (email + пароль)
Форма регистрации содержит поля: email, пароль, подтверждение пароля, согласие с пользовательским соглашением (галочка).

Валидация на клиенте и сервере:

email – корректный формат, уникальность.

пароль – минимальная длина 8 символов, содержит буквы и цифры (требования могут быть гибкими).

После успешной регистрации пользователь автоматически входит в систему (или перенаправляется на страницу входа с уведомлением).

Подтверждение email (верификация) – опционально на первых порах, но архитектурно предусмотреть возможность включения.

Вход (email + пароль)
Форма входа: email, пароль, опция «Запомнить меня» (увеличивает срок жизни сессии).

При успешном входе создаётся сессия (JWT или server-side session с secure cookie).

Поддержка logout.

Вход через VK ID
На странице входа/регистрации есть кнопка «Войти через VK ID».

Реализовать OAuth 2.0 flow согласно документации VK API.

После успешной авторизации VK возвращает email (если разрешено) и базовые данные пользователя (имя, avatar).

Если пользователь с таким email уже зарегистрирован локально – связываем аккаунты (после подтверждения владения, например, запросом пароля).

Если нет – создаём нового пользователя с данными из VK, генерируем случайный пароль (или оставляем без пароля, но с возможностью установить позже).

Сессия создаётся аналогично локальному входу.

Управление сессией
Использовать httpOnly, Secure, SameSite=Lax cookies для хранения токена.

Токен должен иметь ограниченное время жизни (например, 24 часа) с возможностью продления через refresh-токен (или просто с помощью «Запомнить меня»).

При выходе (logout) сессия аннулируется на сервере и клиент удаляет cookie.

Восстановление пароля
Форма «Забыли пароль?» – ввод email, отправка ссылки для сброса.

Реализовать через временный токен, хранимый в БД (с expiration).

После сброса пароля уведомить пользователя.

Пользовательское соглашение и политика конфиденциальности
При регистрации обязательно ознакомление и согласие с пользовательским соглашением (check-box).

Текст соглашения должен быть доступен для чтения в виде отдельной страницы (или модального окна с прокруткой).

Соглашение должно быть версионировано – каждая версия сохраняется в БД или файле с меткой времени.

Администратор (или юрист) должен иметь возможность легко заменить текст соглашения без изменения кода – текст хранится в отдельном файле (например, terms_v1.html, terms_v2.html) или в БД с возможностью редактирования через админ-интерфейс.

При изменении соглашения пользователи должны быть уведомлены (при следующем входе или через email) и должны повторно принять новую версию.

Юрист должен иметь возможность внести правки в текст без погружения в код – для этого предусмотреть простой редактор (или просто заменить файл с текстом, если это допустимо).

В документации описать, где лежит файл соглашения и как его обновить.

Защита данных пользователя
Пароли хранятся только в захэшированном виде (bcrypt или Argon2, соль).

Email используется как логин, но не отображается публично.

Данные пользователя (история чатов, настройки) привязаны к user_id и не доступны другим пользователям (в multi-user режиме).

Администратор не имеет доступа к паролям.

Сбор данных для аналитики и рекламы происходит только с явного согласия пользователя (отдельная галочка при регистрации или в настройках).

UI/UX требования для аутентификации
Страницы входа/регистрации должны быть минималистичными, адаптивными, с понятными подсказками.

Кнопка «Войти через VK ID» должна быть заметной, но не перекрывать локальный вход.

После входа пользователь видит своё имя/аватар (если есть) в углу интерфейса, с возможностью выйти.

При ошибках (неверный пароль, занятый email) показывать понятные сообщения, без раскрытия излишней информации (например, «Неверный email или пароль», а не «Пользователь не найден»).

Для VK ID – обработать ошибки авторизации (отказ пользователя, технические сбои) и показать понятные сообщения.

23.2. РЕКЛАМНЫЙ ДВИЖОК И СБОР ДАННЫХ
Бизнес-требования
Personal Agent Rus может показывать пользователям рекламу в следующих случаях:

Поиск товаров и услуг – если пользователь запрашивает информацию о товарах, ценах, магазинах, услугах и т.п.

Коммерческие запросы – если пользователь явно ищет что-то купить, сравнить, заказать.

Контекстные подсказки – если запрос пользователя может быть дополнен коммерческим предложением (например, «где купить X», «лучшие Y»).

Реклама всегда сопровождается явной плашкой "Реклама" или "Партнёрский материал", чтобы пользователь понимал природу предложения.

Администратор настраивает рекламный движок через специальную панель в админ-интерфейсе.

Сбор данных пользователей
Важно: сбор данных осуществляется только при явном согласии пользователя (отдельная галочка при регистрации или в настройках профиля). Пользователь может отказаться от сбора данных в любой момент, но тогда рекламный функционал будет недоступен (или будет показываться только общая, не таргетированная реклама).

Собираемые данные (обезличенные):

Тип запросов (категории, темы).

Частота использования функций (чат, исследование, файлы, код).

Предпочтительные режимы работы (быстро, умно).

Демографические данные (если пользователь предоставил).

Поведенческие паттерны (время использования, сессии).

История коммерческих запросов (поиск товаров, цен).

Эти данные помогают:

Улучшать релевантность рекламных предложений.

Анализировать потребности пользователей для развития продукта.

Определять популярные функции и направления.

Запрещено:

Передавать личные данные третьим лицам без явного согласия.

Раскрывать конкретные запросы пользователей (только агрегированные данные).

Использовать данные для таргетинга вне Personal Agent Rus.

Архитектура рекламного движка
text
USER REQUEST
↓
Intent Classifier
↓ (если коммерческий запрос)
Ad Engine
↓ (запрос к базе рекламных объявлений)
Ad Selector (по релевантности, бюджета, приоритетам)
↓
Ad Render (с плашкой "Реклама")
↓
RESPONSE (answer + ad(s))
Компоненты:

Intent Classifier – определяет, является ли запрос коммерческим (по ключевым словам, контексту, истории). Может использовать ML-модель или rule-based (легче поддерживать на начальном этапе).

Ad Engine – управляет рекламными кампаниями, объявлениями, таргетингом.

Ad Selector – выбирает подходящее объявление по:

Релевантности запросу (категории, ключевые слова).

Бюджету и остатку средств.

Приоритету (администратор может задать срочность/важность).

Гео (если доступно и разрешено).

Ad Render – формирует блок с рекламой (карточка, текст, ссылка, кнопка) с обязательной плашкой.

Панель управления рекламой (администратор)
Администратор имеет доступ к полноценной панели управления рекламой:

Разделы:

Рекламные кампании – создать/редактировать/удалить кампанию.

Название, описание, бюджет, даты.

Ссылка на целевой сайт/товар.

Формат (текст, баннер, карточка).

Объявления – внутри кампании создать объявления.

Заголовок, текст, изображение (опционально).

Категории для таргетинга (по которым запросы будут показывать это объявление).

Ключевые слова (дополнительно для точного таргетинга).

Приоритет (от 1 до 10, где 10 – самый высокий).

Статус (активно, на модерации, остановлено).

Статистика (показы, клики, CTR – позже).

Аналитика – общая статистика по кампаниям и объявлениям.

Количество показов.

Количество кликов (если отслеживается).

Остаток бюджета.

Тренды.

Настройки таргетинга – глобальные ограничения.

Максимум объявлений на один запрос (например, не более 3).

Минимальный бюджет для показа.

Приоритетные категории.

Исключения (категории, где реклама не показывается).

UI/UX для администратора:

Дружелюбный интерфейс с дашбордами, графиками.

Простой редактор объявлений (как в социальных сетях).

Валидация полей, предпросмотр объявления (как оно будет выглядеть у пользователя).

Возможность дублировать кампании, архивировать.

Фильтры по датам, статусам, категориям.

UI/UX для пользователя
Рекламные блоки выглядят органично, но с явной меткой "Реклама" или "Партнёрский материал".

Блок может быть отдельным элементом под основным ответом или справа (в боковой панели).

Если пользователь заинтересован – кликает, переходит на страницу рекламодателя (или открывает товар в Personal Agent).

Если не интересует – просто игнорирует, это не влияет на основной опыт.

Пользователь может в настройках отключить показ рекламы (но тогда продукт может перейти на платную модель, или реклама будет заменена на нейтральные рекомендации).

Критерии качества:

Реклама не должна перекрывать основной контент.

Реклама не должна вводить пользователя в заблуждение (явная маркировка).

Реклама не должна замедлять работу продукта.

Технические требования
Ad Engine должен быть выделен в отдельный модуль (возможно, отдельный микросервис, но для начала – внутренний модуль Core).

Данные по рекламным объявлениям хранятся в БД (таблицы ads_campaigns, ads_items, ads_clicks, ads_impressions).

Сбор аналитики по показам и кликам – обязателен для отчётов и биллинга.

При нехватке бюджета кампания автоматически приостанавливается.

Все рекламные блоки логируются для аудита.

24. CURRENT KNOWN STATE — HISTORICAL BASELINE, NOT SOURCE OF TRUTH
    Этот раздел хранит последний известный baseline и нужен для continuity, но не разрешает пропускать повторную проверку.

Перед продолжением разработки агент обязан снять свежий live baseline. Если этот раздел расходится с текущими файлами, Git, Docker/runtime, тестами или логами, приоритет всегда у фактического состояния.

text
LIVE STATE > RELEASE EVIDENCE > DOCUMENTED KNOWN STATE > ASSUMPTIONS
После изменений в source code, tests, Dockerfile, Compose, config, migrations, UI, routing, lifecycle scripts или packaging связанные прежние PASS считаются stale, пока соответствующий gate не запущен снова.

На текущий момент CSP-несовместимый тест Playwright, использующий wait_for_function со строковым кодом, переписан на безопасные locator-ожидания и expect(...). Это исправление применено ко всем подобным вхождениям в тестовом наборе, и добавлен статический анализ для предотвращения повторного появления такого анти-паттерна.

На текущей Windows reference machine уже реально подтвержден:

text
VERIFY-PACKAGE PASS
START PASS
Docker/Compose PASS
Ollama PASS
bootstrap model download PASS
Core build PASS
Core readiness PASS
real inference PASS
public/admin smoke boundary PASS
RESTART PASS
VERIFY after restart PASS
Текущий FULL-ACCEPTANCE выявил дефект acceptance-теста:

Playwright использовал string-based:

text
page.wait_for_function("...")
что требует JavaScript eval и нарушает строгую CSP:

text
script-src 'self'
Это не основание ослаблять CSP.

Исправить Playwright suite так, чтобы она вообще не использовала eval/string wait_for_function.

Предпочитать:

text
locator waits
expect(...)
polling from Python
explicit DOM reads
После исправления обязательно прогнать ВСЮ suite, а не только упавшую строку.

25. ОСНОВНАЯ ПРОБЛЕМА ПРЕДЫДУЩЕГО ПРОЦЕССА
    Ранее разработка несколько раз попадала в цикл:

text
создать release
↓
запустить
↓
упасть на раннем этапе
↓
сделать r5/r6/r7...
↓
обнаружить следующий базовый дефект
Это запрещённая модель работы дальше.

Причины уже встречавшихся дефектов:

неправильное использование $LASTEXITCODE;

скрытая ошибка elevated PowerShell;

hardcoded disk threshold;

Windows PowerShell UTF-8/ANSI;

слишком широкая ASCII verification;

__pycache__ ошибочно блокировал user verify;

installer копировал мусор extraction folder;

Docker output буферизовался;

обязательная тяжёлая model для smoke;

обязательный огромный Playwright image в normal install;

PowerShell $Args съел Docker Compose arguments;

race-prone readiness tests;

browser test нарушал собственную CSP.

Эти классы ошибок должны получить regression tests.

Не исправлять только симптом.

26. RELEASE GATES
    Нельзя выпускать ZIP после static/unit tests.

Минимальные release gates:

GATE A — STATIC
text
syntax
imports
JSON
Dockerfiles
Compose config
generated artifact hygiene
secrets scan
destructive commands scan
GATE B — WINDOWS COMMAND CONTRACT
Windows PowerShell должен реальным parser/dry-run test подтвердить lifecycle команды:

text
compose config
compose up ollama
compose exec ollama
compose up core
compose ps
compose restart
compose stop
Никакой special variable binding проблемы.

GATE C — CORE/API
Проверить:

health;

readiness;

USER boundary;

ADMIN boundary;

chat;

validation;

routing;

model pull;

persistence;

backend failure;

concurrency;

аутентификация и регистрация (email+VK);

рекламный движок (Intent Classifier, Ad Engine);

поддержка внешних провайдеров (DeepSeek, OpenAI и др.).

GATE D — REAL BROWSER
Chromium + реальный HTTP Core + реальная CSP.

Проверить:

desktop;

mobile;

modes;

chat;

refresh;

storage;

admin;

routing;

pull;

errors;

XSS;

формы регистрации/входа, VK ID flow, соглашение;

отображение рекламы (плашка, кликабельность).

GATE E — WINDOWS REAL RUNTIME
На reference Windows:

text
START
VERIFY
FULL ACCEPTANCE
RESTART
VERIFY
REPAIR
VERIFY
STOP
START
VERIFY
GATE F — WINDOWS REBOOT
После стабилизации:

text
running
↓
real Windows reboot
↓
login
↓
runtime recovery/autostart
↓
data intact
↓
VERIFY
GATE G — CLEAN MACHINE
На чистой Windows VM:

text
Docker prerequisites
↓
fresh Personal Agent deployment
↓
first start
↓
real chat
↓
restart
↓
repair
↓
PASS
GATE H — ДОКУМЕНТАЦИЯ
Проверить наличие пользовательской документации (как запустить, как использовать базовые функции, как зарегистрироваться и войти).

Проверить наличие административной документации (управление моделями, конфигурация, backup/restore, управление пользователями, управление рекламой, подключение DeepSeek и других провайдеров).

Проверить наличие руководства по устранению неполадок.

Проверить, что документация не содержит технических деталей, не предназначенных для конечного пользователя.

Проверить версионность и соответствие текущей реализации.

Проверить наличие инструкции для юриста по редактированию пользовательского соглашения.

Проверить наличие инструкции для администратора по настройке рекламных кампаний.

Только после PASS всех применимых gates слой считается frozen.

27. USER JOURNEY TEST SUITE
    Создать отдельную структуру:

text
tests/user_journeys/
Минимум:

text
001_first_start
002_first_chat
003_refresh_continue
004_switch_modes
005_long_chat
006_parallel_requests
007_backend_timeout
008_backend_failure
009_recovery
010_mobile
011_admin_login
012_admin_model_assign
013_model_download
014_restart_persistence
015_security_xss
016_invalid_input

020_latest_news
021_specific_site
022_dynamic_site
023_research_multi_source
024_source_failure
025_conflicting_sources

030_upload_txt
031_upload_pdf
032_create_docx
033_create_xlsx
034_create_pdf
035_modify_artifact

040_python_task
041_powershell_task
042_java_task
043_failing_tests_repair

050_image_upload
051_vision
052_image_generation
053_image_editing

060_audio_upload
061_stt
062_tts

070_complex_multi_capability_task

080_documentation_user
081_documentation_admin

090_registration_email
091_login_email
092_registration_vk
093_login_vk
094_logout
095_password_reset
096_terms_acceptance
097_terms_update_notification

100_ad_showing
101_ad_click
102_ad_campaign_management
103_ad_analytics
104_ad_targeting
105_ad_budget_management

110_deepseek_integration
111_ollama_integration
112_provider_switch
113_external_api_key_management
Не нужно реализовать все capabilities одновременно.

Но когда capability появляется — соответствующий journey становится mandatory.

28. CHAOS / FAILURE TESTS
    После каждого слоя добавлять controlled failure scenarios.

Примеры:

text
kill Core during request
kill Ollama
internet unavailable
target website unavailable
model missing
model pull interrupted
disk nearly full
port occupied
corrupt config
Docker restart
Windows reboot
invalid user file
huge user file
timeout
VK ID service unavailable
email delivery failure (for password reset)
Ad Engine unavailable
Ad budget exhausted
Ad campaign misconfigured
DeepSeek API unavailable
DeepSeek API key invalid
DeepSeek rate limit exceeded
Продукт должен:

не показывать white screen;

не зависать навечно;

показывать понятное состояние;

позволять retry/recovery;

сохранять данные, где возможно.

29. OBSERVABILITY
    Каждая долгосрочная операция должна иметь:

text
phase
status
progress
current action
last message
error
timestamps
Логи разделить:

text
user-facing
application
runtime
audit
diagnostics
Не показывать USER сырые технические traceback.

ADMIN/diagnostics должны иметь доступ к подробностям.

Особое внимание аудиту: все действия аутентификации (вход, регистрация, смена пароля, принятие соглашения), рекламные показы и клики должны логироваться с user_id, IP, timestamp. Также логировать вызовы внешних API (DeepSeek, OpenAI) с обезличенными данными для контроля расходов.

30. DATABASE
    Для локального single-user prototype SQLite допустим.

Но repository/service abstraction должна позволять позднее перейти на PostgreSQL для VPS/multi-user.

Не размазывать raw SQL по handlers.

Добавить migrations.

Для продуктового UX и серверной истории также обязательны таблицы/репозитории:

conversations (id, user_id, folder_id, title, created_at, updated_at, archived_at, pinned_at)

messages (id, conversation_id, user_id, role, content, status, created_at, updated_at)

message_sources (id, message_id, url, title, source_type, retrieved_at, verification_status)

folders (id, user_id, name, created_at, updated_at)

user_onboarding (user_id, tour_id, tour_version, status, current_step, completed_at, updated_at)

plan_entitlements (plan_id, feature_key, enabled, limit_value, metadata)

Для аутентификации необходимы таблицы:

users (id, email, password_hash, vk_id, name, avatar_url, created_at, updated_at, email_verified, terms_accepted_version, terms_accepted_at, analytics_consent, ad_consent)

sessions (id, user_id, token_hash, created_at, expires_at, last_seen_at, revoked_at, ip, user_agent)

password_reset_tokens (id, user_id, token, expires_at)

terms_versions (id, version, content, created_at, active)

Для рекламы:

ads_campaigns (id, name, description, budget, spent, start_date, end_date, status, created_at, updated_at)

ads_items (id, campaign_id, title, text, image_url, target_url, category, keywords, priority, status, impressions, clicks, created_at, updated_at)

ads_impressions (id, ad_id, user_id, request_id, timestamp, ip, user_agent)

ads_clicks (id, ad_id, user_id, request_id, timestamp, ip, user_agent, referrer)

Для провайдеров и моделей:

providers (id, name, type, api_endpoint, api_key_encrypted, is_active, created_at, updated_at)

models (id, provider_id, name, display_name, capabilities, context_length, cost_per_1k_tokens, is_active, created_at, updated_at)

model_assignments (id, mode, model_id, priority, created_at)

31. PERFORMANCE
    Reference target мощный, поэтому качество первично.

Но следить за:

model cold start;

GPU memory;

parallelism;

context;

streaming;

queueing;

browser workers;

DB indexes;

N+1;

memory leaks;

container restart times;

Ad Engine latency (должна быть < 50 мс);

latency внешних API (DeepSeek, OpenAI) – должны быть таймауты и ретраи.

Для LLM измерять отдельно:

text
load time
prompt eval
generation
tokens/sec
total latency
cost per request (для внешних API)
Не путать холодную загрузку модели с generation performance.

32. SOURCE CODE QUALITY
    Использовать production-ready patterns.

Не использовать:

text
printStackTrace
silent catch
magic success
Thread.sleep как synchronization
unbounded retries
hidden destructive cleanup
Все retries:

bounded;

backoff;

logged;

cancellation-aware.

Все network calls (в том числе к DeepSeek/OpenAI):

timeout;

error classification;

retry policy where appropriate.

33. SDD WORKFLOW
    Работать строго:

text
1. SPECIFICATION
2. ARCHITECTURE
3. ACCEPTANCE MATRIX
4. IMPLEMENTATION
5. AUTOMATED TESTS
6. USER E2E
7. FAILURE/RECOVERY TESTS
8. PASS
9. FREEZE
10. NEXT LAYER
    Не перескакивать.

Если во время реализации обнаружен новый architectural requirement:

обновить spec;

обновить acceptance;

затем код.

34. НЕ СПРАШИВАТЬ ПОЛЬЗОВАТЕЛЯ ТО, ЧТО МОЖНО ОПРЕДЕЛИТЬ САМОМУ
    Проверять:

файлы проекта;

существующие scripts;

logs;

Docker;

config;

предыдущие implementations.

Не заставлять пользователя вручную делать работу агента.

Не просить каждый раз:

text
открой файл
найди строку
поменяй значение
если можно сделать patch/package.

35. ИСПОЛЬЗОВАТЬ УЖЕ НАКОПЛЕННЫЙ ОПЫТ ПРОЕКТА
    Перед переписыванием installer/lifecycle изучить соседние работающие реализации в C:\AI, в частности предыдущие LOCAL-AI/Lodestar installer/repair patterns.

Повторно использовать удачные принципы:

canonical root;

in-place upgrade;

backup;

snapshot;

staged apply;

rollback;

no volume deletion;

persistent logs;

VERIFY;

acceptance before cleanup.

Не копировать старую архитектуру вслепую — использовать проверенные patterns.

36. GIT / DISTRIBUTION
    Подготовить normal repository:

text
personal-agent/
├── services/
├── ui/
├── config/
├── migrations/
├── scripts/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── user_journeys/
│   └── release/
├── docs/
├── deploy/
│   ├── local/
│   ├── server/
│   └── dev/
└── .github/workflows/
Для release предпочтительно:

text
ghcr.io/.../personal-agent-core:<version>
USER release:

text
docker compose pull
docker compose up
а не локальная сборка Core.

Development mode может использовать build.

37. UPDATE
    В будущем ADMIN UI:

text
Доступно обновление
[Обновить]
Update flow:

text
backup
↓
pull new images
↓
migration
↓
recreate
↓
health
↓
acceptance
↓
commit
При failure:

text
rollback
Нельзя терять:

chats;

settings;

workspace;

models;

artifacts;

users and their data;

рекламные кампании и статистику;

настройки провайдеров (API-ключи).

38. BACKUP / RESTORE
    Backup должен включать:

DB (включая таблицы пользователей, сессий, рекламы, провайдеров и моделей);

configuration;

workspace;

metadata;

optionally models;

пользовательские соглашения (версии).

Модели можно хранить отдельно, поскольку они повторно скачиваемы.

Restore обязательно тестировать.

39. CURRENT ROADMAP — АКТУАЛЬНЫЙ ПОСЛЕ 0.7.4-local.5

Исторические v0.2–v0.7 milestones больше не являются execution order.
Они описывают уже созданные или частично созданные capabilities и используются только для traceability.

Текущий подтверждённый продуктовый статус:

text
0.7.4-local.5
=
technical local alpha
+
Docker runtime
+
local inference
+
Web/Browser
+
Files/Artifacts foundation
+
Code sandbox foundation
+
Auth/Billing/Admin foundations
+
real Windows launch evidence
-
consumer productization

Следующий обязательный этап:

v0.8.0-alpha.1 — PRODUCTIZATION FOUNDATION

Закрыть единым vertical slice:

text
UX shell redesign
server-side conversations
folders/projects
first-user onboarding
role-based USER/ADMIN navigation
OWNER/ADMIN/USER roles
structured logs + diagnostics
real Admin Console shell
browser/PWA identity
help center
migration from browser-local chat state where possible

Mandatory:
- desktop real browser E2E;
- mobile viewport E2E;
- server-side persistence;
- restart persistence;
- USER cannot see Admin UI/API;
- guided onboarding complete/skip/restart;
- diagnostics and structured log evidence.

v0.8.0-alpha.2 — ACCOUNTS / LAN / ENTITLEMENTS / BILLING

text
accounts mode
registration policies
LAN second-device login
two-user isolation
plan catalog
entitlement engine
usage/quota enforcement
billing lifecycle
admin user/plan/session management
LAN QR/address/status
secure-context strategy

v0.8.0-beta.1 — ADMIN / GUIDE / QUALITY HARDENING

text
full Admin Console
user/admin guided tours
contextual help
USER-GUIDE
ADMIN-GUIDE
LAN-GUIDE
PRIVACY-AND-DATA
PLANS-AND-LIMITS
WHY-PERSONAL-AGENT-RUS
TROUBLESHOOTING
backup/restore E2E
diagnostics bundle
quality/performance baseline
second-device real E2E

v0.9.0 — FEATURE-COMPLETE LOCAL BETA

Все согласованные local-first capabilities должны быть доступны через единый UX,
с entitlement/security/persistence/observability contracts.

v1.0.0

Только после mandatory release matrix:
reference Windows + reboot + clean machine + LAN/mobile + auth + persistence +
backup/restore + security + product UX + documentation + business gates.

Никакая capability не получает PASS только потому, что её backend endpoint существует.


40. ПРАВИЛО RELEASE
    Перед выдачей любого release artifact выполнить максимум доступных реальных тестов.

Нельзя писать:

text
готово
после:

text
py_compile PASS
Если runtime нельзя физически запустить в текущей environment — явно сказать, какие gates остаются external.

Но всё, что можно проверить автоматически локально, должно быть проверено ДО передачи пользователю.

41. ПРАВИЛО ПРИ ОБНАРУЖЕНИИ BUG
    Если тест упал:

НЕ делать сразу новый ZIP только с одной исправленной строкой.

Сначала:

text
1. определить root cause;
2. найти тот же anti-pattern во всём проекте;
3. исправить все occurrences;
4. добавить regression test;
5. прогнать соответствующий subsystem;
6. прогнать полный release gate;
7. только потом package.
   Пример текущего CSP bug:

не только заменить одну строку.

Нужно:

убрать все string-based wait_for_function;

запретить этот pattern static check;

прогнать Desktop;

Mobile;

Admin;

Chat;

Pull;

XSS;

Persistence;

реальный CSP;

сохранить screenshot/HTML/console artifacts при failure.

42. FAILURE ARTIFACTS
    При browser E2E failure автоматически сохранять:

text
logs/acceptance-artifacts/
├── screenshot.png
├── page.html
├── console.log
├── page-errors.log
├── network-errors.log
└── test-context.json
Чтобы пользователь не присылал только stacktrace.

43. MAIN DEFINITION OF DONE
    Personal Agent Rus считается реально работающим продуктом только если обычный пользователь может:

text
запустить систему
↓
открыть браузер
↓
увидеть Personal Agent Rus
↓
не увидеть Docker/Ollama/models
↓
написать запрос
↓
получить реальный ответ
↓
переключить режим
↓
продолжить после refresh
↓
продолжить после restart
ADMIN при этом может:

text
открыть Admin
↓
авторизоваться
↓
увидеть models/providers
↓
загрузить model
↓
назначить её режиму
↓
перезапустить систему
↓
увидеть сохранённую конфигурацию
И дальнейшие capabilities:

text
web
research
files
code
images
audio
video
automation
реклама и аналитика
DeepSeek / внешние модели
считаются существующими только после соответствующего реального USER E2E.

44. ОСНОВНОЙ КОМБИНИРОВАННЫЙ ACCEPTANCE
    К релизу высокого уровня Personal Agent Rus обязан выполнить сценарий примерно:

text
«Найди свежие материалы по заданной теме
на нескольких сайтах,
проверь источники,
сравни данные,
подготовь краткий отчёт,
создай Excel и PDF
и сохрани результаты в workspace.»
И реально пройти:

text
PLAN
↓
SEARCH
↓
BROWSE
↓
EXTRACT
↓
VERIFY SOURCES
↓
ANALYZE
↓
CREATE XLSX
↓
VERIFY XLSX
↓
CREATE PDF
↓
VERIFY PDF
↓
SAVE
↓
RETURN ARTIFACTS
Только после этого:

text
COMPLETED
45. EXECUTION BEHAVIOR
    Не ограничивайся рекомендациями.

Если работаешь внутри проекта и имеешь возможность изменять файлы:

изменяй их.

Если можешь запустить тест:

запускай.

Если можешь воспроизвести bug:

воспроизводи.

Если можешь проверить результат:

проверяй.

Не выдавай пользователю новый artifact до прохождения соответствующего gate.

Не уходи в бесконечное проектирование.

Цикл должен быть:

text
inspect
→ implement
→ test
→ fix
→ regression
→ user E2E
→ package
46. ПРИОРИТЕТ ПРЯМО СЕЙЧАС — PRODUCTIZATION, НЕ НОВЫЕ CAPABILITIES

Текущий приоритет — превратить работающий local alpha в понятный самостоятельный продукт.

До добавления новых крупных capabilities обязательны:

text
1. UX/UI shell redesign
2. server-side conversation persistence
3. folders/projects/history/search
4. first-user guided onboarding
5. role-based USER / OWNER / ADMIN experience
6. registration/login/session hardening
7. structured logging + diagnostics
8. Admin Console redesign
9. plan/entitlement foundation
10. LAN accounts + second-device journey
11. guides/help/"why Personal Agent"
12. browser/PWA identity and complete visual states

Рекламный движок, дополнительные remote providers и дальнейшие capabilities
не должны блокировать этот productization slice.

Базовая рекламная архитектура может оставаться в коде/spec,
но публичный рекламный UX становится mandatory только после:
identity → consent → entitlement/billing → audit → user experience.

Запрещено:
- делать ещё один release только с cosmetic patch;
- добавлять новые backend capabilities при незакрытом USER shell;
- оставлять history canonical в localStorage;
- показывать обычному USER Admin/Runtime/Provider UI;
- считать "контейнеры работают" эквивалентом product readiness.

После PASS productization foundation переходить к следующему vertical slice.


47. ФИНАЛЬНЫЙ ПРИНЦИП
    Главная метрика проекта:

не количество написанного кода и не количество зелёных unit tests, а количество пользовательских сценариев, которые реально проходят от начала до конца.

Если internal test говорит PASS, а настоящий пользовательский journey падает — milestone FAILED.

Если UI красивый, но задача физически не выполнена — FAILED.

Если файл «создан», но не открывается — FAILED.

Если сайт «исследован», но evidence отсутствует — FAILED.

Если model selected, но backend использовал другую — FAILED.

Если после restart пропали данные — FAILED.

Если USER видит внутреннюю model ID — FAILED.

Если Admin configuration потерялась — FAILED.

Если recovery не работает — FAILED.

Если регистрация не сохраняет данные или соглашение не показывается — FAILED.

Если реклама показывается без плашки или не по запросу — FAILED.

Если DeepSeek API не вызывается при назначенной модели — FAILED.

Если всё перечисленное проверено фактическими тестами — только тогда PASS.

Продолжай разработку Personal Agent Rus именно по этим правилам до рабочего продукта.

48. LIVE STATE DISCOVERY — САМОЕ НАЧАЛО КАЖДОЙ СЕССИИ
    Перед любым существенным изменением агент выполняет discovery текущего проекта.

Минимально проверить и зафиксировать:

text
OS / build
PowerShell version
Git status / branch / HEAD
project root
free disk
CPU / RAM
GPU / VRAM / driver
Docker Desktop/runtime
Docker / Compose versions
running containers
named volumes
networks
published ports
current images + digests
existing config
DB schema/migration version
models/providers
workspace paths
recent persistent logs
last release evidence
Также проверить:

нет ли нескольких конкурирующих копий проекта;

нет ли старых контейнеров с теми же портами;

нет ли устаревших compose projects;

не используется ли случайно предыдущий release directory;

нет ли незакоммиченных пользовательских данных внутри source tree;

не запущен ли старый Core/UI;

соответствуют ли version/manifest/package друг другу.

Discovery не должен разрушать состояние.

Запрещено во время discovery:

text
down -v
volume prune
system prune
rm persistent data
reset database
Результат discovery сохранять в release/test artifacts как machine-readable snapshot.

49. CANONICAL FILESYSTEM / STORAGE CONTRACT
    Ни один runtime component не должен зависеть от current working directory.

Для Windows определить canonical root, например:

text
C:\AI\PersonalAgent\
├── runtime\
├── config\
├── data\
├── workspace\
├── artifacts\
├── logs\
├── backups\
├── packages\
├── diagnostics\
└── temp\
Точный путь может быть configurable, но должен иметь один centralized resolver.

Явно разделять:

text
SOURCE CODE
RELEASE PACKAGE
RUNTIME
CONFIG
DATABASE
WORKSPACE
ARTIFACTS
MODELS
LOGS
BACKUPS
TEMP
Source/release extraction directory не является persistent storage.

Для persistent данных запрещены неявные зависимости от:

text
$PWD
Get-Location
./data
../logs
relative output path
process startup directory
Каждый Docker named volume должен иметь:

stable logical name;

owner component;

purpose;

backup policy;

restore policy;

delete policy.

START/STOP/REPAIR/VERIFY/UPDATE/BACKUP должны корректно работать независимо от директории, из которой пользователь вызвал entry script.

Acceptance обязательно включает запуск lifecycle command:

text
из project root
из C:\AI
из произвольной другой директории
Результат должен быть одинаковым.

50. CONFIGURATION / SECRET CONTRACT
    Вся конфигурация должна иметь формальную schema/version.

Минимально:

text
config_version
defaults
validation rules
environment overrides
secret references
migration rules
unknown-field policy
redaction rules
Невалидная конфигурация не должна приводить к white screen или молчаливому fallback.

Должно быть понятно:

text
which file
which field
expected value
actual problem
how to repair
Secrets:

не хранятся в Git;

не возвращаются USER API;

не печатаются в logs;

не попадают в browser HTML;

не попадают в diagnostics archive без redaction;

не передаются tool/capability без необходимости.

Изменение конфигурации ADMIN-ом должно быть persisted, versioned и проверяться после restart.

Для VK ID необходимо хранить client_id и client_secret – они являются секретами и должны быть в переменных окружения, не в коде.

Для DeepSeek и других внешних API – аналогично, ключи хранятся в зашифрованном виде в БД (поле api_key_encrypted) и не выводятся в логи.

51. ORCHESTRATOR IDEMPOTENCY / STEP COMMIT CONTRACT
    Task engine обязан быть устойчив к restart, retry, timeout и duplicate delivery.

Каждый Job/Task/Step имеет стабильный ID.

Минимальная execution semantics шага:

text
NOT_STARTED
STARTED
COMMITTED
VERIFYING
VERIFIED
FAILED
Результат шага сохраняется до перехода к следующему шагу.

Retry не должен молча дублировать:

artifact creation;

file writes;

external messages/actions;

model pull;

migration;

downloads;

user-visible operations.

Для внешних API использовать idempotency key, где это поддерживается.

После crash/restart orchestrator обязан определить:

text
что не начиналось;
что началось, но не завершилось;
что было committed;
что уже verified;
что безопасно retry;
что требует user/admin decision.
Для потенциально destructive/external действий нельзя автоматически повторять неопределённый шаг без проверки фактического результата.

Acceptance:

text
crash before execution
crash during execution
crash after commit before verification
retry same task
restart Core
restart Docker
browser reconnect
Не должно быть duplicate user effects.

52. WEB SECURITY — SSRF / NETWORK ISOLATION
    Все URL, redirects и DNS results считаются untrusted.

Web capability должна защищать host/runtime/internal network от SSRF.

По умолчанию блокировать или явно policy-gate доступ к:

text
localhost
127.0.0.0/8
::1
RFC1918 private networks
link-local networks
169.254.169.254
Docker internal services
Docker API
host management ports
DB ports
admin-only endpoints
file://
unsupported protocols
Проверять destination:

text
before DNS resolution
after DNS resolution
after every redirect
Учитывать:

DNS rebinding;

redirect to private IP;

IPv4/IPv6 alternative notation;

encoded hosts;

redirect loops;

oversized responses;

endless streams;

decompression bombs;

malicious downloads.

Browser worker не должен автоматически иметь доступ ко всей host network.

SSRF acceptance mandatory до признания WEB capability production-ready.

53. INDIRECT PROMPT INJECTION / UNTRUSTED CONTENT
    Любой внешний контент считается DATA, а не instruction authority.

К untrusted content относятся:

text
web pages
search snippets
PDF/DOCX/XLSX/PPTX
uploaded files
images with text
email/messages when integrations appear
tool output
external API output
retrieved code/comments
Такой контент не может самостоятельно:

менять system policy;

выдавать разрешение;

включать новый tool;

раскрывать secrets;

отправлять локальные файлы наружу;

менять privacy mode;

инициировать destructive action;

менять provider policy;

выполнять shell command.

Обязательные adversarial journeys:

text
website says "ignore previous instructions"
PDF asks to reveal secrets
HTML asks to execute shell
search result injects fake system message
document asks to upload workspace
site asks to disable verification
Ожидаемый результат:

text
content extracted as data
malicious instruction ignored/isolated
no privilege escalation
no secret disclosure
no unauthorized action
54. CODE EXECUTION SANDBOX
    Generated/user code нельзя выполнять с правами самого Personal Agent runtime.

По умолчанию execution environment:

text
dedicated workspace
no Docker socket
no unrestricted host filesystem
no provider/admin secrets
bounded CPU
bounded RAM
bounded disk
bounded processes
bounded stdout/stderr
hard timeout
cancellation
process-tree termination
network disabled unless task requires it
Network permission должна быть capability/policy controlled.

Рабочий каталог sandbox должен быть isolated от:

Personal Agent source;

persistent DB;

Docker control socket;

credentials;

unrelated user files.

Обязательные security tests:

text
read outside workspace
write outside workspace
symlink escape
spawn unlimited children
consume excessive RAM
consume excessive disk
endless stdout
endless process
access Docker socket
access internal DB
read provider secret
network access when disabled
Cancellation должна завершать дочернее дерево процессов, а не только wrapper process.

55. DATA EGRESS / PRIVACY POLICY
    Model routing и privacy routing — разные механизмы.

Определить минимум:

text
LOCAL_ONLY
REMOTE_ALLOWED
REMOTE_REQUIRED
Remote fallback никогда не должен молча отправлять пользовательские данные наружу, если active privacy policy это запрещает.

Policy должна применяться к:

prompts;

conversation history;

uploaded files;

extracted document text;

images/audio/video;

artifacts;

tool results;

embeddings if used later.

ADMIN определяет provider/data-egress policy.

USER должен получать понятное уведомление или permission там, где переход с local processing на remote materially меняет privacy expectations.

При LOCAL_ONLY отсутствие подходящей local model даёт честную ошибку/предложение ADMIN-у, а не скрытый remote fallback.

Пользовательские данные (email, имя, история) также подпадают под политику конфиденциальности, которая должна быть ясно изложена в пользовательском соглашении.

56. SUPPLY CHAIN / RELEASE INTEGRITY
    Production release не использует mutable dependencies без фиксации версии.

Запрещено считать production-safe:

text
image: latest
unversioned download URL
unchecked installer
unchecked model artifact
Production image фиксируется version tag и immutable digest.

Release должен генерировать минимум:

text
release-manifest.json
SHA256SUMS
SBOM
dependency inventory
license inventory
container image digests
migration version
config schema version
build metadata
По возможности предусмотреть signing release artifacts/container images.

Windows installer в production должен поддерживать code signing.

Downloaded package проверяется до применения.

Dependency/security scan не заменяет runtime acceptance, но является обязательной частью release evidence.

57. MODEL PROVENANCE / LICENSING
    Model Registry дополнительно хранит:

text
source
revision/version
digest
license
commercial_use status
redistribution status
terms/source reference
quantization
artifact size
installed_at
verified_at
Нельзя считать модель установленной только по имени в provider list.

Проверять:

text
artifact available
provider can load it
real inference works
capability contract matches
model identity/digest recorded
Distribution package не должен автоматически перераспространять model weights без проверки соответствующей license policy.

58. MOBILE / LAN / SECURE CONTEXT CONTRACT
    Разделять три режима доступа:

text
Desktop local
LAN / mobile
Server / internet
127.0.0.1 на ПК не является mobile access strategy.

LAN/mobile mode должен иметь определённый механизм discovery/addressing и secure-origin strategy для browser capabilities, которые требуют Secure Context.

Особенно проверить:

microphone;

camera if introduced;

clipboard where used;

file upload;

downloads;

persistent session;

reconnect.

Нельзя проектировать audio/mobile UX так, будто обычный insecure HTTP LAN origin гарантированно даст все browser permissions.

Когда mobile capability входит в gate, acceptance проводится на реальном мобильном браузере или максимально близком физическом device test, а не только через desktop viewport emulation.

Минимальный mobile journey:

text
open Personal Agent
login/session
send chat
receive streaming response
upload file
upload image
refresh
continue conversation
download artifact
microphone input when audio ships
recover after PC/Core restart
59. DETERMINISTIC WEB TESTS + LIVE SITE CANARIES
    Реальные сайты обязательны, но release CI не должен становиться случайным из-за внешней недоступности.

Поэтому WEB tests делятся на два независимых слоя.

A. Deterministic fixtures
Локально контролируемые test-sites воспроизводят:

text
static HTML
dynamic JS rendering
pagination
infinite-like feed
redirect
redirect loop
403
404
429
500
timeout
slow response
malformed HTML
large page
robots/policy behavior
login wall
cookie banner
content changed after navigation
malicious prompt injection
SSRF redirect
Эти тесты mandatory и должны давать deterministic PASS.

B. Live canaries
Отдельно тестировать реальные сайты/классы источников:

text
DTF
Habr
AWS articles
Skillfactory
JavaRush
YouTube
ЕГРЮЛ
zakupki.gov.ru
Google News / news search
marketplaces
ordinary static sites
JavaScript-heavy sites
Live result имеет состояние:

text
PASS
PRODUCT_FAIL
BLOCKED_EXTERNAL
BLOCKED_EXTERNAL разрешён только если diagnostics подтверждает внешнюю причину и fallback/polite failure продукта работает корректно.

BLOCKED_EXTERNAL никогда не конвертируется в PASS.

Если определённый live site заявлен как обязательный release capability и долго остаётся blocked, release report должен это явно показывать.

60. UNIFIED TEST RESULT SEMANTICS
    Для всех suites использовать формальную семантику:

text
PASS
FAIL
BLOCKED_ENVIRONMENT
BLOCKED_EXTERNAL
NOT_IMPLEMENTED
SKIPPED_NOT_APPLICABLE
Правила:

PASS — проверяемое expected behavior реально выполнено;

FAIL — продукт или тестовый контракт нарушен;

BLOCKED_ENVIRONMENT — текущая среда физически не позволяет провести тест;

BLOCKED_EXTERNAL — независимый внешний ресурс не позволяет завершить live test;

NOT_IMPLEMENTED — capability ещё не реализована;

SKIPPED_NOT_APPLICABLE — тест действительно не относится к текущей edition/profile.

Mandatory release gate считается закрытым только по required PASS.

Количество SKIPPED/BLOCKED не должно скрываться из summary.

Итоговый release report обязан показывать counts и конкретные test IDs каждого статуса.

61. FLAKY TEST POLICY
    Тест, который упал и прошёл только после случайного rerun, не считается автоматически исправленным.

Запрещён release pattern:

text
FAIL
rerun
PASS
→ declare green
При flaky behavior:

text
capture artifacts
identify race/timing/resource cause
remove unstable synchronization
add deterministic wait/condition
add regression coverage
rerun cleanly
Не использовать arbitrary sleep как основной способ починки race.

Release gate должен проходить clean run.

Допустимый retry должен быть частью явно определённой semantics внешней операции, а не способом скрыть нестабильный тест.

62. DATABASE / MIGRATION / ROLLBACK CONTRACT
    Каждая migration должна иметь:

text
migration_id
from_version
to_version
preconditions
backup requirement
forward compatibility note
rollback/recovery strategy
verification
Update не считается committed до:

text
backup
migration
new runtime start
health/readiness
application acceptance
persistence verification
Если старая версия Core несовместима с новой DB schema, rollback images обязан также восстановить совместимый DB snapshot.

Нельзя обещать rollback, если rollback проверяет только containers, но не данные.

Migration acceptance:

text
fresh database
previous release database
partially failed migration
restart during migration
retry
rollback
post-rollback data integrity
63. API CONTRACT / VERSION COMPATIBILITY
    API между UI/Core/workers должен иметь formal schema.

Предпочтительно OpenAPI/JSON schema там, где применимо.

Проверять:

frontend ↔ backend compatibility;

version mismatch;

required/optional fields;

invalid field types;

unknown fields policy;

error envelope;

pagination where used;

streaming contract;

cancellation contract.

Breaking change требует explicit migration/versioning strategy.

UI не должен падать white screen из-за неизвестного backend field или controlled backend error.

Для аутентификации добавить эндпоинты:

/api/auth/register – регистрация

/api/auth/login – вход

/api/auth/logout – выход

/api/auth/vk – VK OAuth callback

/api/auth/password-reset-request – запрос сброса

/api/auth/password-reset – сброс

/api/auth/me – получение данных пользователя

/api/auth/terms – получение текущего соглашения

/api/auth/accept-terms – принятие соглашения

/api/auth/analytics-consent – управление согласием на сбор данных

Для рекламы:

/api/admin/ads/campaigns – CRUD кампаний

/api/admin/ads/items – CRUD объявлений

/api/admin/ads/analytics – статистика

/api/ads/show – получение рекламы для текущего запроса (внутренний)

Для провайдеров и моделей:

/api/admin/providers – CRUD провайдеров (включая DeepSeek)

/api/admin/models – CRUD моделей

/api/admin/models/assign – назначение модели режиму

/api/admin/models/test – проверка работоспособности модели (вызов с тестовым запросом)

Все эндпоинты должны быть задокументированы в OpenAPI.

64. SSE / STREAMING / RECONNECT CONTRACT
    Streaming не считается рабочим только потому, что tokens однажды появились в UI.

Проверять:

text
normal stream
slow stream
stream interrupted
browser refresh during stream
temporary network disconnect
Core restart while task running
reconnect
resume current task state
final state delivery
no duplicate chunks/messages
no missing final state
cancel during stream
Task truth хранится server-side, а browser stream — только transport/view.

Refresh browser не должен уничтожать task state.

Сессии при этом должны оставаться валидными (проверять, что после перезагрузки страницы пользователь остаётся в системе).

65. CONCURRENCY / QUEUES / BACKPRESSURE
    Reference machine мощная, но ресурсы конечны.

Для каждой capability определить concurrency/resource policy.

Минимально:

text
LLM queue
GPU queue
CPU execution queue
browser worker pool
artifact generation queue
media queue
max queue length
priority
cancellation
fairness
Если ресурс занят, USER должен видеть понятное состояние:

text
В очереди
Ожидаю модель
Создаю результат
а не зависание/случайный timeout.

Обязательные journeys:

text
two chats same user
two browser tabs
parallel chat + research
parallel artifact generation
cancel A while B continues
admin changes routing while old job runs
restart with queued jobs
GPU OOM / model cannot fit
queue overflow
Существующая задача должна сохранять deterministic routing context, если ADMIN меняет model mapping во время её выполнения, либо поведение должно быть формально определено.

66. UPLOAD / DOWNLOAD / ARCHIVE SECURITY
    Файлы пользователя считаются untrusted.

Тестировать минимум:

text
path traversal
MIME spoofing
double extension
malformed PDF
malformed Office file
zip slip
archive bomb
symlink escape
huge file
zero-byte file
filename control characters
duplicate filenames
very long filename
disk exhaustion
interrupted upload
interrupted download
Uploaded filename не должен напрямую становиться trusted filesystem path.

Temporary files должны иметь lifecycle/cleanup policy.

Artifact download должен проверять authorization и принадлежность workspace/user boundary.

67. LOGGING / RETENTION / DIAGNOSTICS PRIVACY
    Определить для каждого вида логов:

text
rotation
max size
retention
redaction
access boundary
archive behavior
User prompts и полный artifact content не должны без необходимости постоянно дублироваться в технические logs.

Diagnostics bundle должен:

помогать воспроизвести проблему;

содержать versions/status/errors;

редактировать secrets/tokens;

не собирать весь private workspace по умолчанию.

Проверить disk growth при длительной работе.

Аудиторские логи (входы, регистрации, смена паролей, принятие соглашений, рекламные показы и клики) должны храниться отдельно с защитой от удаления.

68. RELEASE EVIDENCE — PASS ДОЛЖЕН БЫТЬ ДОКАЗУЕМЫМ
    Сохранять artifacts не только при failure, но и доказательства успешного release gate.

Пример:

text
release-evidence/<version>/
├── manifest.json
├── environment.json
├── git-state.json
├── images.json
├── storage.json
├── static-results.json
├── api-results.json
├── browser-results.json
├── user-journeys.json
├── security-results.json
├── performance-results.json
├── lifecycle-results.json
├── backup-restore-results.json
├── reboot-results.json
├── live-canaries.json
├── screenshots\
├── logs\
├── timings\
└── sha256sums.txt
Каждый result record минимум:

text
test_id
started_at
finished_at
status
expected
observed
evidence refs
environment ref
Foundation freeze должен ссылаться на конкретный evidence bundle.

После изменения foundation evidence становится stale в затронутых gates.

69. FULL TEST PYRAMID — НЕ ТОЛЬКО UNIT И НЕ ТОЛЬКО E2E
    Для каждой capability использовать нужные уровни тестирования.

text
STATIC
UNIT
CONTRACT
INTEGRATION
COMPONENT
BROWSER E2E
USER JOURNEY
LIVE CANARY
FAILURE / CHAOS
SECURITY / ADVERSARIAL
PERFORMANCE
LIFECYCLE
REBOOT
CLEAN MACHINE
Назначение:

STATIC
Ловит syntax/config/forbidden patterns/secrets/destructive commands.

UNIT
Ловит локальную business logic быстро и детерминированно.

CONTRACT
Фиксирует API/provider/tool/artifact schemas.

INTEGRATION
Проверяет реальные DB, filesystem, provider adapters, queues и internal services.

Особенно важно для аутентификации: интеграционные тесты с реальной БД, проверка хэширования, сессий, VK OAuth mock, а также для рекламного движка – тесты Ad Selector, Intent Classifier, и для внешних провайдеров – тесты с моками DeepSeek API.

COMPONENT
Проверяет Core/UI/service как собранный компонент.

BROWSER E2E
Проверяет реальный browser + CSP + HTTP + UI state.

Включает заполнение форм регистрации, вход, logout, восстановление пароля, принятие соглашения, переход по VK ID (с использованием тестового OAuth сервера или мока), а также отображение рекламы и клики по ней.

USER JOURNEY
Проверяет задачу пользователя от намерения до результата.

Все UJ-090...113 являются обязательными.

LIVE CANARY
Проверяет интеграцию с настоящим внешним миром (включая реальный VK OAuth, если доступен тестовый клиент, и реальные рекламные сети, если настроены, а также DeepSeek API с тестовым ключом).

FAILURE / CHAOS
Проверяет controlled failures и recovery (например, недоступность VK сервиса, Ad Engine, DeepSeek API).

SECURITY / ADVERSARIAL
Проверяет boundary violations и hostile inputs (атаки на форму входа, подбор пароля, CSRF, XSS, попытки подменить рекламные объявления, перехват API-ключей).

PERFORMANCE
Проверяет latency, queueing, resource use и regression.

LIFECYCLE
Проверяет START/STOP/RESTART/REPAIR/UPDATE/BACKUP/RESTORE, в том числе сохранность пользовательских данных и рекламных кампаний.

REBOOT
Проверяет настоящий OS reboot recovery.

CLEAN MACHINE
Проверяет реальную воспроизводимость установки.

Ни один уровень не считается полной заменой другого.

70. TEST DATA / FIXTURE POLICY
    Test data должна быть reproducible и не зависеть от личных приватных данных владельца машины.

Создать controlled fixtures для:

conversations;

documents;

spreadsheets;

images;

audio;

code projects;

websites;

malformed files;

malicious files;

migration DB snapshots;

пользователей (тестовые email, пароли);

тестовых версий пользовательского соглашения;

тестовых рекламных кампаний и объявлений;

тестовых провайдеров (DeepSeek mock, OpenAI mock).

Не использовать production/user workspace как expendable test fixture.

Tests должны создавать собственный namespace/workspace и очищать только принадлежащие им временные данные.

Cleanup failure не должен приводить к удалению unrelated volumes/workspaces.

71. COMPLETE USER JOURNEY MATRIX
    (Все предыдущие UJ сохранены, добавим новые для DeepSeek и провайдеров)

P. PROVIDER & MODEL MANAGEMENT
UJ-110 Add DeepSeek provider (admin)
text
Admin goes to /admin/providers
→ clicks "Add Provider"
→ selects type "DeepSeek"
→ enters API endpoint (default: https://api.deepseek.com/v1)
→ enters API key (secret)
→ saves
→ provider appears in list
→ health check passed (test call)
UJ-111 Add OpenAI provider (admin)
text
Аналогично, с типом "OpenAI" и эндпоинтом https://api.openai.com/v1
UJ-112 Assign DeepSeek model to a mode
text
Admin goes to /admin/models/assign
→ selects mode "smart"
→ selects provider "DeepSeek"
→ selects model "deepseek-chat"
→ saves
→ USER request in "smart" mode now uses DeepSeek
→ response comes from DeepSeek API
UJ-113 Switch between providers
text
Admin changes mode "smart" from DeepSeek to Ollama
→ USER request in "smart" mode now uses Ollama
→ response comes from local Ollama
→ no data loss, conversation continues
UJ-114 Invalid API key
text
Admin enters wrong DeepSeek API key
→ health check fails
→ error message "Invalid API key"
→ provider marked as inactive
→ USER requests failover to next available provider
UJ-115 DeepSeek rate limit
text
DeepSeek API returns 429 (rate limit)
→ Personal Agent retries with backoff
→ if still failing, shows user-friendly error "Модель временно перегружена, попробуйте позже"
→ logs error for admin
UJ-116 Provider cost tracking
text
Admin sees in analytics dashboard:
→ total tokens used per provider
→ estimated cost per provider
→ cost per user (if multi-user)
72. REAL LOCAL WINDOWS ACCEPTANCE LOOP
    На текущей reference Windows machine разработка должна идти короткими проверяемыми вертикальными slices.

Для каждого изменения:

text
1. DISCOVER affected live state
2. reproduce issue / establish failing test when applicable
3. update specification/acceptance if behavior changes
4. implement smallest coherent fix
5. run targeted tests
6. run regression for same anti-pattern/class
7. run affected integration/component tests
8. run affected real browser USER journey
9. run affected failure/recovery test
10. verify persistence if stateful
11. record evidence
    Перед package/release дополнительно:

text
STATIC
→ UNIT/CONTRACT/INTEGRATION
→ API
→ REAL BROWSER
→ USER JOURNEYS (включая регистрацию/вход/рекламу/DeepSeek)
→ SECURITY
→ PERFORMANCE BASELINE
→ START/VERIFY
→ RESTART/VERIFY
→ REPAIR/VERIFY
→ STOP/START/VERIFY
→ BACKUP/RESTORE verification where gate requires
→ WINDOWS REBOOT where gate requires
→ LIVE CANARIES
→ EVIDENCE REVIEW
→ PACKAGE
→ PACKAGE VERIFY
Если package создаётся после тестов из других bytes/source state, тесты package считаются недостаточными.

Иными словами:

text
TEST WHAT YOU SHIP
SHIP WHAT YOU TESTED
Финальный artifact должен иметь hash/version, связанные с evidence bundle.

73. CLEAN MACHINE / SECOND MACHINE STRATEGY
    Reference PC доказывает функциональность текущей разработки.

Но он не доказывает чистую установку, потому что на нём уже могут существовать:

Docker images;

networks;

volumes;

cached models;

environment variables;

old config;

developer tools.

Поэтому после foundation stabilization обязательна чистая Windows VM или отдельная машина.

Проверить два профиля.

Fresh machine without Personal Agent data
text
prerequisite detection
installation/bootstrap
pull required images
bootstrap model
first start
first chat
restart
repair
backup
uninstall behavior
Second machine without production models
Проверить, что product bootstrap не требует заранее вручную устанавливать тяжёлые модели.

Не использовать скрытые зависимости с developer PC.

74. PERFORMANCE / SOAK ACCEPTANCE
    Функциональный PASS недостаточен, если продукт деградирует после длительной работы.

Для reference machine сохранить baseline минимум для:

text
cold START time
Core readiness
model cold load
first-token latency (локальные модели)
first-token latency (DeepSeek API)
generation tokens/sec
total chat latency
browser page load
research latency
artifact generation latency
memory usage
VRAM usage
container restart time
Ad Engine latency
DeepSeek API latency (включая сетевую задержку)
Не вводить универсальный жёсткий threshold без baseline/обоснования.

Сравнивать regression относительно предыдущего frozen release.

После foundation добавить soak tests:

text
many sequential chats
repeated refresh
repeated start/stop
long-running UI session
many artifact operations
browser worker reuse/restart
log growth
memory/VRAM recovery
many ad impressions
many API calls to DeepSeek
Проверять утечки и деградацию, а не только пик throughput.

75. ACCESSIBILITY / UI RESILIENCE
    К v1.0 USER UI должен проходить минимум:

keyboard navigation для основных flows (включая формы логина и регистрации);

visible focus;

понятные form errors (подсветка полей, сообщения);

desktop/mobile responsive behavior;

progress не только цветом;

reconnect/error state;

no infinite spinner;

no unrecoverable white screen;

large conversation rendering without severe degradation;

формы регистрации/входа должны быть доступны и понятны даже неподготовленному пользователю;

рекламные блоки должны быть доступны для screen readers (aria-label);

админ-панель управления провайдерами должна быть интуитивной (даже для нетехнических администраторов).

USER-facing error обязан отвечать на вопрос:

text
что произошло
что система уже сделала
можно ли retry
потеряны ли данные
нужно ли действие пользователя/администратора
76. ACCEPTANCE MATRIX AS CODE
    Acceptance matrix должна существовать не только в Markdown.

Для автоматизируемых checks иметь machine-readable registry, например:

text
test_id
capability
release_gate
mandatory_from_version
environment
persona
status
evidence_required
Release tooling должно уметь вычислять:

text
which mandatory tests apply
which passed
which failed
which are blocked
which are stale after changed components
Это предотвращает ручное забывание пользовательских сценариев при следующих версиях.

77. CHANGE IMPACT / SELECTIVE + FULL REGRESSION
    Для быстрой разработки разрешены targeted tests после маленького изменения.

Но release gate обязан учитывать impact graph.

Пример:

text
change router
→ chat
→ web intent
→ model selection
→ admin mapping
→ persistence
→ combined journeys
Изменение общего компонента (например, аутентификации, Ad Engine или Provider Registry) должно invalidates PASS зависимых gates.

Перед freeze всё равно выполняется full required release matrix.

Нельзя использовать selective tests как финальное доказательство релиза.

78. PACKAGE / DISTRIBUTION ACCEPTANCE
    Release archive/image/installer — отдельный объект тестирования.

Проверить:

text
version consistency
manifest consistency
checksums
unexpected files
secret absence
__pycache__/temp/build junk absence
correct line endings/encoding where relevant
entry scripts
relative/canonical paths
fresh extraction
package verification command
После создания package выполнить acceptance именно из package/extracted release, а не только из source working tree.

Package не должен зависеть от случайных файлов, оставшихся в developer repository.

79. STOP CONDITIONS / NO FALSE COMPLETION
    Agent не должен бесконечно полировать одну область, но и не должен объявлять milestone раньше времени.

Работа над текущим gate завершается только когда:

text
all mandatory tests PASS
no unresolved P0/P1 defect in gate scope
required evidence exists
package/runtime bytes correspond to tested version
data-preservation checks pass
user journey passes end-to-end
Допустимо остановиться с честным BLOCKED, если существует физическое внешнее ограничение, которое невозможно устранить текущими средствами.

В таком случае итог должен содержать:

text
exact blocked test IDs
why blocked
what was still verified
what remains unverified
no claim of full PASS
80. CURRENT EXECUTION ORDER — FROM NOW

PHASE 0 — LIVE BASELINE
Снять live state reference PC и сохранить machine-readable evidence.

PHASE 1 — PRODUCT SHELL / UX
text
resizable/collapsible sidebar
compact new-chat action
conversation grouping
folders/projects
global search
compact effort selector near composer
USER-only navigation
desktop/mobile responsive shell
empty/loading/error/streaming states
browser favicon/icons/manifest/theme metadata

PHASE 2 — SERVER-SIDE CONVERSATIONS
text
SQLite repositories
folders
conversations
messages
message_sources
chat export/import
migration/versioning
restart/cache-clear persistence
second-device continuity

PHASE 3 — IDENTITY / ROLES / ONBOARDING
text
OWNER
ADMIN
USER
personal/accounts mode
registration policy
login/logout
session list/revoke
first-user owner setup
guided USER tour
guided ADMIN tour
tour persistence/versioning
help center
terms/privacy acceptance

PHASE 4 — OBSERVABILITY / ADMIN
text
structured JSONL logs
request/correlation IDs
stage timings
rotation/retention
audit log
diagnostic bundle
Admin Dashboard
Users
Plans/Billing
AI/Routing
Runtime
LAN
Logs/Audit
Backups/Updates
Ads
Terms

PHASE 5 — LAN / ENTITLEMENTS / BILLING
text
LAN enable/disable/status
QR/address discovery
accounts mode
second-device E2E
plan catalog
entitlement engine
quota enforcement
subscription lifecycle
payment lifecycle
cost governance

PHASE 6 — PROVIDERS / MODELS
Ollama + OpenAI-compatible + configured remote adapters through common registry.
Provider model names are discovered/configured; USER never sees technical IDs.

PHASE 7+ — CAPABILITIES
Каждую capability добавлять вертикально:

text
spec
→ architecture
→ acceptance
→ implementation
→ deterministic tests
→ real USER journey
→ failure/recovery
→ security
→ persistence
→ observability
→ evidence
→ freeze

Перед package/release:

text
STATIC
→ UNIT/CONTRACT/INTEGRATION
→ API
→ REAL BROWSER
→ USER JOURNEYS
→ SECURITY
→ PERFORMANCE
→ START/VERIFY
→ RESTART/VERIFY
→ REPAIR/VERIFY
→ STOP/START/VERIFY
→ BACKUP/RESTORE
→ REBOOT where required
→ LIVE CANARIES
→ EVIDENCE REVIEW
→ PACKAGE
→ PACKAGE VERIFY

TEST WHAT YOU SHIP.
SHIP WHAT YOU TESTED.


81. ULTIMATE PRODUCT ACCEPTANCE
    Personal Agent Rus v1.0 считается готовым не тогда, когда стартуют контейнеры, а когда неподготовленный пользователь способен пройти полный путь без знания внутренней архитектуры.

Финальный high-level journey:

text
получить продукт
→ установить/запустить
→ открыть Personal Agent Rus
→ зарегистрироваться (или войти через VK)
→ принять пользовательское соглашение
→ дать согласие на сбор данных (опционально)
→ выполнить обычный чат
→ продолжить после refresh/restart
→ попросить свежую информацию
→ получить проверенные источники
→ сделать коммерческий запрос (купить, сравнить)
→ увидеть релевантную рекламу с плашкой "Реклама"
→ загрузить документ
→ попросить изменить/проанализировать его
→ получить реальный artifact
→ выполнить сложную multi-capability задачу
→ скачать результаты
→ пережить controlled backend failure
→ продолжить работу после recovery
ADMIN journey:

text
login
→ configure provider/model (добавить DeepSeek, OpenAI, Ollama)
→ download/validate model (если локальная)
→ assign capabilities/modes
→ inspect health/queues/diagnostics
→ backup
→ update
→ validate
→ rollback when deliberately induced update failure occurs
→ verify persistence
→ manage terms & conditions (upload new version)
→ create ad campaigns and ad items
→ monitor ad analytics (impressions, clicks, budget)
→ monitor provider costs and usage
Security journey:

text
USER cannot cross ADMIN boundary
web cannot SSRF internal runtime
external content cannot inject tool authority
code cannot escape sandbox
remote provider cannot receive LOCAL_ONLY data
artifact cannot escape workspace authorization
secrets do not leak into UI/logs/evidence
passwords hashed, sessions secure
terms acceptance enforced
analytics data anonymized
ad clicks logged with user consent
API keys for DeepSeek/OpenAI encrypted in DB
Release journey:

text
source commit
→ immutable build
→ package
→ package acceptance
→ reference Windows acceptance
→ clean-machine acceptance at required gate
→ evidence bundle
→ checksum/signature
→ published release
Только совокупность этих доказательств даёт право на статус RELEASE PASS.

82. FINAL INVARIANT
    Для любого утверждения агента вида:

text
работает
исправлено
создано
скачано
сохранено
восстановлено
защищено
готово
PASS
должен существовать проверяемый факт или evidence, соответствующий уровню утверждения.

Нельзя повышать уровень уверенности:

text
"код выглядит правильно" ≠ TEST PASS
"API отвечает" ≠ USER JOURNEY PASS
"файл существует" ≠ ARTIFACT PASS
"контейнер healthy" ≠ PRODUCT PASS
"suite один раз позеленела после rerun" ≠ STABLE PASS
"внешний сайт недоступен" ≠ WEB PASS
"пользователь создан в БД" ≠ USER JOURNEY PASS (нужен реальный вход и работа)
"реклама в БД" ≠ AD SHOWING PASS (нужен реальный показ в UI)
"DeepSeek ключ сохранён" ≠ DEEPSEEK WORKING PASS (нужен реальный вызов API)
Главное правило Personal Agent Rus:

text
BUILD REAL THING
TEST REAL THING
VERIFY USER RESULT
PRESERVE USER DATA
RECORD EVIDENCE
ONLY THEN DECLARE PASS
83. ПРОЦЕСС ВЫПУСКА И CI/CD
    Для обеспечения воспроизводимости и качества каждый релиз проходит следующие автоматизированные этапы:

Сборка – создание immutable образов контейнеров с фиксированными тегами и digest.

Статический анализ – проверка кода, секретов, лицензий, уязвимостей зависимостей.

Модульные и интеграционные тесты – в изолированной среде (включая тесты аутентификации, рекламного движка, провайдеров с тестовой БД и моками API).

Сборка пакета – формирование release-архива (ZIP/Installer) с манифестом и контрольными суммами.

Тестирование пакета – развёртывание из собранного пакета на чистой тестовой машине (VM) и прогон всех обязательных User Journeys (включая регистрацию, VK ID, рекламу, DeepSeek).

Приёмочные испытания на reference-машине – полный цикл lifecycle, reboot, backup/restore.

Проверка документации – Gate H.

Формирование evidence bundle – все логи, скриншоты, метрики, результаты тестов.

Подпись и публикация – в реестр контейнеров и/или на страницу загрузок.

Каждый commit в основную ветку должен проходить этапы 1–4. Ночные сборки проходят этапы 1–6. Релиз-кандидаты – все этапы, включая 7–9.

84. ТРЕБОВАНИЯ К ДОКУМЕНТАЦИИ
    Пользовательская документация
    Краткое руководство по установке и первому запуску (с картинками).

Описание основных режимов работы (чат, исследование, работа с файлами).

Часто задаваемые вопросы (FAQ) с ответами на типичные проблемы.

Инструкция по регистрации и входу (email и VK ID).

Описание пользовательского соглашения и политики конфиденциальности.

Объяснение, почему показывается реклама и как она работает.

Доступна из интерфейса (встроенная справка) и в виде отдельного PDF/HTML.

Административная документация
Инструкция по установке и настройке (выбор моделей, провайдеров, режимов).

Описание файловой структуры, переменных окружения, команд lifecycle.

Руководство по backup/restore, обновлению, диагностике.

Описание формата логов и способов сбора диагностики.

Инструкция по управлению пользователями (если применимо).

Инструкция для юриста по обновлению пользовательского соглашения – где находится файл, как его заменить, как проверить версию, как уведомить пользователей.

Инструкция для администратора по управлению рекламными кампаниями (создание, редактирование, таргетинг, аналитика).

Инструкция по подключению внешних провайдеров (DeepSeek, OpenAI, Anthropic и др.) – как получить API-ключ, где его ввести, как протестировать, как назначить модель режиму.

Инструкция по мониторингу стоимости – как отслеживать расходы на API, как настроить лимиты.

Документация для разработчиков
Архитектурный обзор с диаграммами.

Инструкция по локальной разработке, запуску тестов.

Описание API (OpenAPI), контрактов между сервисами.

Правила оформления кода, процесс ревью, работа с Git.

Описание процесса аутентификации (JWT/cookies, OAuth2 flow для VK).

Описание архитектуры рекламного движка (Intent Classifier, Ad Engine, Ad Selector, Ad Render, база данных).

Описание архитектуры Provider/Model Registry – как добавлять нового провайдера, как писать адаптер, как тестировать.

Инструкция по добавлению новых рекламных провайдеров или форматов.

85. ИНТЕГРАЦИЯ С DEEPSEEK И ДРУГИМИ ВНЕШНИМИ API
    85.1. Поддерживаемые провайдеры
    Personal Agent Rus должен поддерживать как минимум:

Ollama – локальный, бесплатный, для быстрых ответов.

DeepSeek – внешний API, хорошее соотношение цена/качество, поддержка русского языка.

OpenAI (GPT-3.5, GPT-4) – для задач, требующих максимального качества.

Anthropic (Claude) – опционально, для сложного анализа.

В будущем можно добавлять других провайдеров через единый адаптер.

85.2. Требования к адаптеру
Каждый провайдер должен реализовывать единый интерфейс:

python
class ProviderAdapter:
def chat_completion(self, messages, model, temperature=0.7, max_tokens=2000, stream=False, **kwargs):
# возвращает ответ (или стрим)
def check_health(self):
# проверяет доступность API и валидность ключа
def get_models(self):
# возвращает список доступных моделей
def estimate_cost(self, prompt_tokens, completion_tokens):
# возвращает ориентировочную стоимость
85.3. Безопасность
API-ключи хранятся в зашифрованном виде в БД.

Никогда не выводятся в логи, UI, ответы.

Используются только для аутентификации запросов к внешнему API.

Администратор может в любой момент отозвать ключ.

85.4. Fallback и ротация
Если основной провайдер недоступен (ошибка, таймаут, rate limit), система автоматически переключается на следующий по приоритету (если настроен). Пользователь видит уведомление: "Основная модель временно недоступна, используется резервная".

85.5. Мониторинг стоимости
Администратор видит дашборд с расходами по каждому провайдеру, модели, пользователю (если multi-user). Можно установить дневной/месячный лимит, при превышении которого провайдер автоматически отключается (или отправляется уведомление).

86. ЭКСПЛУАТАЦИЯ И МОНИТОРИНГ
    86.1. Системные требования
    Минимальные: 4 GB RAM, 2 vCPU, 20 GB диска (без моделей).

Рекомендуемые: 8+ GB RAM, 4+ vCPU, 50+ GB диска.

Для локальных моделей – наличие GPU с достаточным VRAM.

Для внешних API – стабильное интернет-соединение.

86.2. Мониторинг состояния
Health-эндпоинт /health – возвращает статус Core, DB, подключённых провайдеров.

Метрики: количество запросов, среднее время ответа, ошибки, использование памяти, диска.

Оповещения: при превышении порогов (CPU, RAM, диск, ошибки API) – администратор получает email/telegram уведомление.

Логи: централизованный сбор (ELK или аналоги) с ротацией и архивацией.

86.3. Масштабирование
При увеличении нагрузки можно добавить дополнительные инстансы Core (горизонтальное масштабирование).

Для внешних API – увеличение лимитов или добавление нескольких ключей.

Для локальных моделей – добавление дополнительных GPU-серверов.

86.4. Резервное копирование
Ежедневный автоматический backup БД и конфигурации.

Backup хранится в отдельном каталоге, можно настроить отправку в облачное хранилище.

Восстановление – с помощью команды restore (интерактивный или автоматический).

87. РАЗВИТИЕ ПРОЕКТА И ПРИВЛЕЧЕНИЕ НОВЫХ РАЗРАБОТЧИКОВ

87.1. Onboarding новых сотрудников

Проект должен быть воспроизводимо развёрнут по документации.
Цель 10–15 минут допустима только после измеренного clean-machine baseline.

Обязательны:
- Docker Compose;
- test fixtures;
- dev setup guide;
- one-command verification;
- documented architecture boundaries.

87.2. Код-ревью и стандарты

Обязательное code review перед merge в основную ветку.

Static analysis / type checking / formatting должны быть закреплены CI.
Конкретный toolchain выбирается repository-ом и не должен дублироваться без необходимости.

Новые business-critical paths требуют автоматических tests и E2E acceptance.

87.3. Документация для разработчиков

Обязательны:
- архитектурный обзор;
- схема БД/migrations;
- API/OpenAPI;
- добавление capability;
- добавление provider adapter;
- auth/session flow;
- logging/tracing;
- release/evidence process.

87.4. Сообщество и обратная связь

Предусмотреть issue tracker, changelog и понятный канал обратной связи.
Конкретные публичные каналы (GitHub/Telegram/иные) определяются перед public beta.

87.5. Browser / App Identity

Продукт должен иметь завершённую browser identity:

text
favicon.ico
SVG/PNG icon set
apple-touch-icon where applicable
web app manifest
product name
short_name
theme/background metadata
version/about screen
proper document title
no generic framework/browser placeholder icons

При поддержке installable web-app/PWA:
- icons multiple sizes;
- standalone metadata;
- offline/error fallback only where actually implemented;
- installability tested in supported browsers.


88. PRODUCTIZATION CONTRACT — ОБЯЗАТЕЛЬНО ДО BETA / 1.0

Этот раздел закрывает требования, которые недостаточно формализованы в предыдущих разделах.
При конфликте с историческим roadmap этого документа приоритет имеет раздел 88 и актуальный section 80.

88.1. USER UX SHELL

Desktop sidebar:
- drag-resize 240–420 px;
- width persists per user/device;
- collapse to compact rail;
- Ctrl+B toggle;
- mobile uses overlay drawer;
- no permanent blank/reserved technical column.

Navigation USER:
text
Новый чат
Поиск
Проекты
Диалоги
Файлы/Артефакты/Задачи contextual
Аккаунт
Тариф
Настройки
Помощь

USER не видит:
text
Администрирование
provider IDs
model IDs
Docker
Compose
runtime internals
deployment internals
raw diagnostics

Conversation UX:
- grouping: Сегодня / Вчера / 7 дней / Старше;
- pin/archive/rename/delete;
- folders/projects;
- move conversation;
- search titles + message content;
- export current chat MD;
- export all JSON/ZIP;
- long conversation virtualization/performance.

Composer:
- attachment/tools button;
- compact mode selector near input;
- Auto by default;
- only entitlement-allowed modes;
- Stop while generating;
- human-readable phases;
- drag/drop;
- keyboard shortcuts;
- clear error/retry state.

88.2. FIRST USER / OWNER EXPERIENCE

On a fresh installation with no owner:

text
Open product
→ Welcome
→ Explain local-first/privacy in plain language
→ Create OWNER account or explicitly choose trusted personal mode
→ Choose access: This PC / Home LAN / Server
→ Registration policy
→ Privacy / remote-data policy
→ AI readiness check
→ Finish
→ USER guided tour

No Docker/model/provider jargon in the standard wizard.

88.3. GUIDED USER TOUR

First authenticated USER automatically receives a skippable guided tour.

UI behavior:
- dimmed overlay;
- spotlight target;
- animated arrow/pointer;
- short tooltip;
- Back / Next / Skip;
- progress N of M;
- keyboard support;
- prefers-reduced-motion respected;
- mobile placement adapts to viewport.

Minimum steps:
1. Welcome / why Personal Agent;
2. New chat;
3. Composer;
4. Attach files;
5. Web/Research;
6. Projects/history;
7. Artifacts/downloads;
8. Privacy/local-vs-remote indicator;
9. Account/plan;
10. Finish with suggested first actions.

Clicking Personal Agent logo after onboarding opens Help Center:
text
Что умеет Personal Agent
Пройти обучение заново
Горячие клавиши
Руководство
Что нового
О программе

Tour state is server-side:

text
user_onboarding
---------------
user_id
tour_id
tour_version
status
current_step
completed_at
updated_at

New product versions may show only new steps instead of replaying the whole tour.

88.4. GUIDED ADMIN TOUR

ADMIN/OWNER receives a separate walkthrough on first Admin Console entry.

Minimum:
1. Dashboard;
2. Users/registration;
3. Plans/entitlements;
4. Providers/models/routing;
5. Usage/cost;
6. Monitoring;
7. Logs/audit;
8. LAN;
9. Backup/update;
10. Terms/privacy;
11. Ads where enabled;
12. Diagnostics.

Admin help explains consequences in product language first.
Technical IDs/details are behind "Подробнее"/Developer Mode.

88.5. SERVER-SIDE CONVERSATION TRUTH

Browser localStorage MUST NOT be canonical storage for conversations.

LOCAL uses SQLite with repository abstraction.
SERVER target uses PostgreSQL without rewriting handlers.

Required entities:
text
folders
conversations
messages
message_sources
conversation_exports
user_onboarding

All user-owned records include user_id.
Every read/write repository path enforces ownership.

Acceptance:
- cache clear does not delete chat history;
- browser refresh preserves state;
- Core restart preserves history;
- same account on second LAN device sees history;
- user A cannot access user B data;
- export/import is versioned and validated.

88.6. AUTH / SESSION PRODUCT CONTRACT

Modes:
text
personal
accounts

Roles:
text
OWNER
ADMIN
USER

Registration:
text
open
approval_required
closed

Use server-side sessions as the default architecture.
Persist only token hashes, never raw session tokens.

Session capabilities:
- HttpOnly cookie;
- Secure under HTTPS;
- SameSite policy;
- CSRF protection;
- session rotation;
- session list;
- revoke one/all;
- remember-me policy;
- failed-login throttling;
- audit.

Password:
- Argon2id for new hashes;
- migration path for older hashes;
- reset token single-use + expiry;
- password reset invalidates relevant sessions.

VK/OAuth:
- state/CSRF validation;
- PKCE where supported/applicable;
- strict redirect allowlist;
- account linking requires explicit proof;
- no blind account linking solely by matching email.

Normal Admin login uses role-based account auth.
Environment admin token is break-glass only.

88.7. PLANS / ENTITLEMENTS

Do not scatter:
text
if plan == "pro"

Use Plan Catalog + Entitlement Engine.

Minimum entitlement keys:
text
chat
web
research
deep_research
files_read
files_create
code
long_tasks
remote_ai
priority_queue
advanced_exports
automation
media
max_concurrent_tasks
remote_token_quota
remote_cost_quota
storage_quota
max_file_size

Mode selector is derived from effective entitlements.

Backend is authoritative.
Hidden/disabled UI is not security enforcement.

Local self-owned inference can be treated independently from platform-funded remote quota.

Plan names/prices are configuration/business data, not hard-coded core logic.

88.8. ADMIN CONSOLE

Admin Console is a separate surface.

Required sections:
text
Dashboard
Users
Registrations
Plans / Entitlements
Subscriptions
Payments
Usage / Cost
AI / Providers
Models / Routing
Tasks / Queues
Artifacts / Storage
Runtime
LAN
Logs
Audit
Security
Backups
Updates
Terms / Privacy
Ads
Feature Flags
Diagnostics
Settings

Dashboard minimum:
- active/new users;
- active sessions;
- requests/min;
- p50/p95 latency;
- error rate;
- active/failed tasks;
- web/browser/code failures;
- provider tokens/cost;
- subscriptions;
- payment failures;
- CPU/RAM/disk;
- GPU/VRAM;
- queue depth;
- alerts.

Admin actions must be audited:
actor, action, target, outcome, timestamp, correlation_id.

Admin must not receive raw passwords or unrestricted private-user content by default.

88.9. STRUCTURED LOGGING / DEBUG MODE

Until 1.0, debug diagnostics are mandatory but privacy-safe.

Application log JSONL fields:
text
timestamp
level
service
environment
version
event
request_id
correlation_id
user_id
conversation_id
task_id
step_id
intent
provider_id
model_id
duration_ms
status
error_type

Stage timings where applicable:
text
routing_ms
queue_ms
search_ms
browser_ms
inference_ms
artifact_ms
code_ms
db_ms

Log classes:
text
application
runtime
audit
task events
metrics
trace
user-visible activity

Never log by default:
- password;
- raw session token;
- provider API key;
- payment secret;
- Authorization header;
- complete private file contents.

Debug prompt/content logging:
- explicit opt-in;
- redacted;
- visually marked;
- auto-expiring where possible.

LOCAL rotation default:
- 20 MB × 10 files for app/runtime;
- audit retained separately;
- diagnostics bundle created explicitly.

Admin Logs UX:
- filter level/service/request/user/time;
- correlate one request across services;
- download sanitized diagnostic bundle.

Diagnostic bundle:
- versions;
- image/container status;
- health;
- recent errors;
- sanitized config;
- DB/migration version;
- RAM/disk/GPU;
- acceptance results;
- no secrets/private workspace by default.

88.10. LAN / MOBILE PRODUCT UX

LAN is a first-class feature.

Admin UI:
text
LAN: Off/On
Address
QR code
Private-network warning
Registration policy
Connected sessions/devices
[Enable] [Disable] [Copy address]

When LAN is enabled:
- accounts mode is recommended/required unless explicit trusted personal-LAN override;
- registration defaults to approval_required;
- firewall Private profile only;
- no internal services published.

Acceptance includes a real second device.

Secure Context:
HTTP LAN may support chat/files, but microphone/camera/clipboard capabilities that require secure origin
must be honestly marked and tested with an HTTPS/secure-bridge strategy before claiming full mobile capability.

88.11. HELP / DOCUMENTATION / DIFFERENTIATION

In-product Help Center is mandatory.

Ship:
text
USER-GUIDE.md
ADMIN-GUIDE.md
LAN-GUIDE.md
PRIVACY-AND-DATA.md
PLANS-AND-LIMITS.md
TROUBLESHOOTING.md
WHY-PERSONAL-AGENT-RUS.md
CHANGELOG.md

"Почему Personal Agent Rus" must describe only implemented/evidenced differentiation.

Target proposition:
Private local-first agent workspace for Russian-speaking users that can use local GPU,
search and verify web sources, work with real files/projects, execute and verify code/tasks,
create downloadable artifacts, and optionally use remote AI under explicit privacy/cost/plan policy.

88.12. COMPLETE PRODUCT STATES

Every major page/component must define:
text
loading
empty
ready
partial/degraded
error
permission denied
quota exceeded
offline/reconnecting
success

No:
- white screens;
- infinite spinner;
- raw traceback to USER;
- silent failure;
- layout dead space;
- unexplained disabled button.

88.13. PWA / BROWSER COMPLETENESS

Mandatory browser assets:
- favicon;
- product SVG/logo assets;
- common PNG sizes;
- apple-touch icon if supported;
- manifest.webmanifest;
- title;
- theme-color/background;
- proper About/version view.

Installable/PWA behavior is claimed only if actually tested.

88.14. PRODUCTIZATION ACCEPTANCE IDS

Mandatory before 0.8 beta:

text
UX-001 sidebar resize persists
UX-002 collapse/expand + mobile overlay
UX-003 compact new chat + correct shortcuts
UX-004 folders/projects CRUD
UX-005 grouped conversations
UX-006 search title+content
UX-007 USER has no Admin navigation/routes/data
UX-008 compact entitlement-aware mode selector
UX-009 complete loading/empty/error/degraded states
UX-010 browser icons/manifest/title complete

ONB-001 first USER tour auto-starts
ONB-002 tour is skippable
ONB-003 tour can be restarted from logo/help
ONB-004 progress persists server-side
ONB-005 tour_version supports new-only steps
ONB-006 mobile walkthrough keeps target visible
ONB-007 reduced-motion/accessibility works
ONB-101 ADMIN has separate guided tour

CONV-001 cache clear preserves conversations
CONV-002 Core restart preserves conversations
CONV-003 second device sees same account history
CONV-004 user isolation
CONV-005 folders persist
CONV-006 chat export MD
CONV-007 all-data export validated

AUTH-001 open registration
AUTH-002 approval-required registration
AUTH-003 closed registration
AUTH-004 login/logout
AUTH-005 session list/revoke
AUTH-006 failed-login throttling
AUTH-007 USER gets 403 Admin
AUTH-008 OWNER/ADMIN reaches Admin
AUTH-009 password reset single-use/expiry
AUTH-010 terms version acceptance

PLAN-001 entitlements backend enforced
PLAN-002 UI derived from effective entitlements
PLAN-003 mode availability follows plan
PLAN-004 remote quotas enforced
PLAN-005 local inference accounting separated from platform remote quota

ADMIN-001 dashboard uses real metrics
ADMIN-002 users/sessions/roles actions work
ADMIN-003 plan changes work and audit
ADMIN-004 provider/routing changes persist and audit
ADMIN-005 logs correlate request IDs
ADMIN-006 diagnostic bundle sanitized
ADMIN-007 backup/update state visible

OBS-001 structured JSON logs
OBS-002 request/correlation IDs end-to-end
OBS-003 secrets absent
OBS-004 rotation
OBS-005 diagnostic bundle
OBS-006 log growth soak

LAN-001 enable/disable/status
LAN-002 correct URL + QR
LAN-003 second-device login
LAN-004 two-user isolation
LAN-005 restart/reconnect
LAN-006 secure-context limitations are explicit

GUIDE-001 Help Center accessible via Personal Agent logo
GUIDE-002 USER guide bundled
GUIDE-003 ADMIN guide bundled
GUIDE-004 docs version matches app
GUIDE-005 WHY document contains only evidenced claims

88.15. PRODUCTIZATION DEFINITION OF DONE

0.8 productization slice is DONE only if a nontechnical user can:

text
open product
→ understand what it is
→ complete/skip onboarding
→ start chat
→ find old chat
→ create project/folder
→ attach/download file
→ understand current mode
→ understand local/remote privacy state
→ see plan/limits
→ refresh/restart without losing history
→ use Help Center
→ never encounter infrastructure jargon

and ADMIN can:

text
login
→ understand dashboard
→ manage users
→ manage plans
→ manage providers/routing
→ inspect health/queues
→ inspect logs with correlation
→ export diagnostics
→ manage LAN
→ manage backup/update
→ replay Admin tour

Only real USER/ADMIN E2E with persistence and evidence can mark this PASS.

89. ЗАКЛЮЧИТЕЛЬНЫЕ ПОЛОЖЕНИЯ

Данный документ является обязательным source of truth для реализации, тестирования и выпуска Personal Agent Rus.

Приоритет требований:
text
1. Security
2. Data integrity
3. Correctness
4. Privacy
5. Reliability
6. Product quality
7. UX
8. Performance
9. Cost
10. Developer convenience

При конфликте исторического baseline и фактического состояния:
text
LIVE STATE > CURRENT RELEASE EVIDENCE > CURRENT SPEC > HISTORICAL BASELINE > ASSUMPTIONS

Главный критерий:
не количество endpoints, контейнеров или unit tests,
а реальный пользовательский результат, который переживает refresh/restart и подтверждён evidence.

90. PRODUCT POSITIONING — НЕ "ЕЩЁ ОДИН WEBUI"

Personal Agent Rus не позиционируется как техническая замена Open WebUI для AI-энтузиастов.

Целевая категория продукта:

text
consumer-friendly personal AI operating layer
+
agentic workspace
+
local-first / hybrid AI
+
verified outcomes
+
scenario-driven assistance
+
commercial SaaS control plane

Для простого USER ключевая ценность:

text
"Мне не нужно понимать, как пользоваться LLM.
Я говорю, чего хочу добиться.
Personal Agent сам выбирает способ,
задаёт только необходимые вопросы,
выполняет работу,
проверяет результат
и возвращает готовый итог."

Конкурентное отличие должно доказываться пользовательскими journey, а не маркетинговыми словами.

Mandatory differentiation journeys:
- zero-prompt beginner can start from scenario card;
- Auto mode correctly routes normal requests;
- agent asks bounded clarifying questions only when material information is missing;
- agent performs web/file/code/research work without exposing infrastructure;
- result survives restart and is downloadable/reusable;
- local-only and remote modes are understandable to nontechnical users;
- paid entitlement unlocks measurable additional value.

91. SAAS / VPS PRODUCTION TOPOLOGY

91.1. Preferred architecture

Для российской коммерческой редакции предпочтительная архитектура не "весь backend за границей",
а разделённый control/data plane.

Recommended logical topology:

text
                           Internet
                              |
                    +---------+---------+
                    |                   |
               RU PUBLIC EDGE       GLOBAL PUBLIC EDGE
             domain / landing         optional
                    |
              RU APPLICATION PLANE
        +-----------+------------+
        |           |            |
      Web/API     Auth         PostgreSQL
        |           |            |
        +------ Core/Tasks -------+
                    |
             Policy / Egress Router
              /                 \
             /                   \
      RU EGRESS WORKERS      GLOBAL AI GATEWAY
      Russian sites/APIs      supported regions
      Yandex / CIAN /         remote AI providers
      zakupki / marketplaces  where contract permits
             \                   /
              +------ results ---+

Primary user DB, identity, subscriptions, consent, audit and canonical user data
for the Russian SaaS edition SHOULD remain in the RU application plane unless legal review
explicitly approves another topology.

A foreign AI gateway MUST NOT contain a replica of the main user database.

Send only the minimum payload required for the selected remote operation.

91.2. Provider compliance

Do not treat a foreign VPS as a generic circumvention mechanism.

Every remote provider adapter must store:
- supported-country policy reference;
- operator/account eligibility;
- data-egress classification;
- commercial-use status;
- configured region;
- last policy review date.

If a provider's terms do not permit serving the target users/operator,
the provider is disabled for that edition regardless of technical reachability.

Provider availability is a policy decision, not merely "HTTP 200".

91.3. Initial sizing profiles

SAAS-START / early public beta:
text
RU App VPS:
4 vCPU
8 GB RAM
80-160 GB NVMe
PostgreSQL
Redis-compatible queue/cache optional
reverse proxy
backups

GLOBAL AI Gateway:
2-4 vCPU
4-8 GB RAM
40-80 GB SSD
no canonical user DB
stateless where possible

Browser/Web Worker pool:
2-4 vCPU
4-8 GB RAM per worker node initially
scale horizontally
strict concurrency limits

If document conversion / browser jobs become heavy:
separate worker node from Core.

The sizing is a starting profile, not a guaranteed capacity.
Before public launch run measured load tests for:
- 10 concurrent users;
- 50 concurrent users;
- 100 concurrent users;
- mixed chat/research/browser/file workloads.

91.4. Database

SQLite remains supported for:
- local single-user installation;
- developer/test mode;
- portable/offline deployment.

PostgreSQL becomes the canonical server/VPS database before public multi-user beta.

Use repository/service abstraction shared by both.

Server production requirements:
- PostgreSQL 16+ compatible target unless repository chooses newer supported baseline;
- migrations;
- transaction boundaries;
- connection pooling;
- indexes on user_id, conversation_id, task status, timestamps, payment/subscription keys;
- pagination;
- backup/PITR strategy;
- query metrics;
- slow-query logging;
- no N+1 in conversation/admin lists.

No business feature may be implemented only for SQLite if it is required in SaaS.

92. PUBLIC WEBSITE / SEO / DISCOVERY

Personal Agent Rus requires a public indexable website independent from authenticated app routes.

Minimum public routes:
text
/
 /features
 /how-it-works
 /pricing
 /local-ai
 /research
 /files
 /coding
 /privacy
 /security
 /faq
 /guides/*
 /use-cases/*
 /terms
 /privacy-policy
 /login
 /register

Authenticated conversations/workspaces are noindex/private.

SEO requirements:
- server-rendered or prerendered public pages;
- unique title/description/canonical;
- sitemap.xml;
- robots.txt;
- OpenGraph metadata;
- structured data where semantically valid;
- fast Core Web Vitals target;
- Yandex Webmaster integration;
- Google Search Console integration;
- analytics only under applicable consent policy.

Create useful indexable use-case pages from real capabilities, not doorway/spam pages.

Example useful pages:
- AI помощник для выбора одежды;
- поиск и анализ закупок;
- анализ объявлений недвижимости;
- подбор подарков;
- что приготовить;
- что посмотреть;
- поиск свежих новостей;
- анализ документов;
- помощник разработчика.

93. SCENARIO ENGINE — AI ДЛЯ ЛЮДЕЙ, КОТОРЫЕ НЕ ЗНАЮТ КАК ПИСАТЬ PROMPT

93.1. Scenario Gallery

Beginner experience includes a visible "С чего начать?" / "Помощники" surface.

Scenario definitions are data/config, not hard-coded UI logic.

Each scenario has:
text
scenario_id
edition
title
description
icon
category
intent
required_capabilities
entitlements
input_schema
clarification_policy
site_policy
result_contract
example_queries
version
enabled

Initial scenario families:

LIFE:
- подобрать одежду;
- выбрать подарок;
- найти рецепт;
- выбрать фильм/сериал;
- выбрать книгу;
- составить поездку;
- выбрать товар;
- сравнить услуги.

WORK:
- найти закупки;
- проверить контрагента;
- исследовать рынок;
- сравнить предложения;
- собрать новости;
- сделать отчёт;
- проанализировать документы.

REAL ESTATE:
- найти варианты недвижимости;
- сравнить районы/объекты;
- проверить параметры объявления;
- подготовить shortlist.

DEVELOPER:
- разобраться в ошибке;
- изменить проект;
- проверить код;
- подготовить документацию.

93.2. Auto mode remains primary

Scenario UI is not a separate weaker assistant.

The same planner/router powers:
- normal free-form chat;
- scenario cards;
- deep links/public landing scenario;
- onboarding suggested actions.

Scenario cards prefill structured constraints and improve UX.
Auto mode must still recognize equivalent intent from natural language.

93.3. Bounded Clarification Policy

The agent asks a question only if the missing value materially changes the result.

For each scenario define:
- required fields;
- optional high-value fields;
- inferable fields;
- safe defaults;
- max clarification rounds;
- fallback behavior.

Default policy:
text
0 questions if enough information exists
1 grouped clarification when several high-value constraints are missing
maximum 2 clarification rounds for ordinary consumer scenarios
then proceed with stated assumptions and allow refinement

Do not ask one field per message when they can be grouped.

Example — clothing:
Bad:
text
Какой пол?
Какой рост?
Какой размер?
Какой бюджет?
Какой стиль?
...

Good:
text
Чтобы подобрать действительно подходящие варианты, уточните одним сообщением:
• для кого ищем;
• примерный размер/мерки;
• бюджет;
• сезон/повод;
• что точно не нравится.
Можно ответить только на известные пункты — остальное я подберу сам.

If user profile already contains valid preferences/measurements and policy allows use,
do not ask again.

93.4. Site/Search Profiles

Admin can configure domain/search policies without exposing them to USER.

Entity:
text
site_profiles

Fields:
site/domain pattern
category
preferred acquisition method
search engine preference
browser/static/search order
region/geo egress
pagination strategy
rate-limit policy
auth requirement
robots/policy note
selectors/extraction hints where maintainable
fallback order
enabled
last_verified_at

Examples/categories:
- Yandex Search;
- Google Search where contract/region permits;
- CIAN-like real estate;
- zakupki.gov.ru;
- ЕГРЮЛ;
- marketplaces;
- retail sites;
- news sites;
- JS-heavy community sites.

USER settings expose only understandable preferences:
text
"Искать по всему интернету"
"Предпочитать российские сайты"
"Искать только на выбранных сайтах"
"Учитывать мой город/регион"
"Показывать товары с доставкой"
"Не использовать сайты: ..."

Admin/Developer Mode controls technical profiles.

94. LEGACY PRODUCT / "РЕШИ ЗА МЕНЯ" MIGRATION STRATEGY

Existing external products/sites may later be migrated into Personal Agent,
but migration is a separate audited project.

Do not couple Personal Agent Core to a legacy DB schema.

Migration phases:
text
DISCOVER
→ inventory current DB/users/content/auth/payments
→ classify personal data
→ map schemas
→ build read-only importer
→ dry-run
→ reconciliation report
→ user/account linking strategy
→ staged migration
→ rollback plan
→ production cutover

Potentially reusable legacy assets:
- existing audience/accounts where legally and technically transferable;
- public content/use-case pages;
- scenario concepts;
- consent/terms history where valid;
- payments/subscription history where compatible;
- SEO authority/redirect mappings.

Never migrate:
- plaintext passwords;
- raw session tokens;
- undocumented secrets;
- data without a lawful migration basis.

Password hashes are migrated only if the hashing scheme and security posture are acceptable;
otherwise use account-claim/password-reset migration.

URL migration:
- preserve valuable indexed URLs where possible;
- use permanent redirects only after mapping;
- maintain sitemap/canonical;
- monitor Yandex/Google indexing and 404s.

95. SAAS BUSINESS ACCEPTANCE

Before public paid SaaS beta mandatory journeys include:

text
SAAS-001 public landing indexed/crawlable
SAAS-002 register/login/terms/consent
SAAS-003 plan purchase
SAAS-004 payment webhook idempotency
SAAS-005 entitlement becomes effective
SAAS-006 quota enforcement
SAAS-007 renewal/cancel/past-due behavior
SAAS-008 user data isolation
SAAS-009 PostgreSQL backup/restore
SAAS-010 RU web worker successfully handles Russian-source scenario
SAAS-011 global provider gateway obeys provider policy
SAAS-012 LOCAL_ONLY data never crosses gateway
SAAS-013 provider outage fallback
SAAS-014 scenario beginner completes useful task without prompt expertise
SAAS-015 bounded clarification does not exceed configured rounds
SAAS-016 admin sees cost/usage/audit
SAAS-017 SEO sitemap/robots/canonical validation
SAAS-018 diagnostics without secret leakage

96. CURRENT PRODUCT VISION

Personal Agent Rus is designed to become part of an ordinary user's daily life.

Product success is not:
text
"USER learned how to prompt an LLM."

Product success is:
text
"USER stopped thinking about prompting
and started reliably solving everyday tasks."

The product should move progressively from:
text
question → answer

to:
text
goal
→ understand context
→ ask minimum necessary clarification
→ plan
→ find/use tools
→ verify
→ deliver concrete result
→ remember useful preferences with permission
→ improve the next interaction

This experience is the primary consumer differentiation.

97. DOCUMENT STATUS

This document supersedes MASTER-IMPLEMENTATION-PROMPT-v4.md.

Date: 10.08.2026
Version: 8.0

