1. PRODUCT IDENTITY
   Семейство продукта:

Personal Agent

Текущая региональная редакция:

Personal Agent Rus

Архитектура должна позволять впоследствии существование:

Personal Agent RUS

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

Для аутентификации необходимы таблицы:

users (id, email, password_hash, vk_id, name, avatar_url, created_at, updated_at, email_verified, terms_accepted_version, terms_accepted_at, analytics_consent, ad_consent)

sessions (id, user_id, token, expires_at, ip, user_agent)

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

39. CURRENT ROADMAP
    FOUNDATION
    v0.2.x — Docker Product Foundation
    Закрыть до полного PASS:

text
VERIFY
START
Browser E2E
Admin E2E
Security
Restart
Repair
Stop/Start
Windows reboot
После PASS — FREEZE.

v0.3 — ORCHESTRATOR / TASK ENGINE
Реализовать:

conversation/session persistence;

task entity;

state machine;

planner;

execution steps;

progress/SSE;

cancellation;

retries;

verification;

artifact skeleton;

permission skeleton.

USER E2E mandatory.

v0.4 — WEB / SITE / RESEARCH
Реализовать:

search;

static fetch;

dynamic browser;

site profiles;

source extraction;

freshness;

fallback;

research;

citations;

evidence verification.

Обязательные реальные site journeys.

v0.5 — FILES / WORKSPACE / ARTIFACTS
Реализовать:

text
TXT
MD
JSON
CSV
PDF
DOCX
XLSX
PPTX
Creation/read/edit/validation.

v0.6 — CODE / EXECUTION / DATA
Python;

PowerShell;

Java;

build/test;

sandbox;

ETL;

structured data.

v0.7 — VISION / IMAGE / AUDIO
vision;

image generation;

editing;

STT;

TTS.

v0.8 — AUTOMATION / ACTIONS
permissions;

external actions;

schedules;

audit;

long jobs.

v0.9 — SERVER / VPS / MULTI-USER / HYBRID
HTTPS;

authentication (email/password + VK ID);

tenant/user;

quotas;

worker nodes;

hybrid provider routing;

управление пользовательскими соглашениями;

рекламный движок и аналитика.

v1.0
Только после полного release matrix.

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
46. ПРИОРИТЕТ ПРЯМО СЕЙЧАС
    Текущий приоритет — НЕ web/files/code.

Сначала полностью закрыть Docker Product Foundation, включая базовую аутентификацию (email/password) и базовый рекламный движок (без сложного таргетинга на первом этапе).

Конкретно:

исправить CSP-compatible browser acceptance;

прогнать полный browser suite;

прогнать API/security/concurrency/persistence;

прогнать Windows lifecycle;

проверить RESTART;

проверить REPAIR;

проверить STOP → START;

проверить Windows reboot persistence;

реализовать регистрацию/вход по email/паролю (базовый UI, бэкенд);

реализовать хранение пользовательских данных и сессий;

интегрировать пользовательское соглашение (версионирование, отображение, принятие);

реализовать базовый рекламный движок (Intent Classifier на rule-based, Ad Engine, Ad Selector, Ad Render);

реализовать админ-панель для управления рекламными кампаниями (создание, редактирование, статистика);

сохранить regression tests;

FREEZE foundation.

После этого начать v0.3 Orchestrator.

Не переписывать работающий foundation без причины после freeze.

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
    Прямо сейчас работать в следующем порядке.

PHASE 0 — LIVE BASELINE ON REFERENCE PC
Снять фактическое состояние текущего Personal Agent Rus и сохранить evidence.

PHASE 1 — FOUNDATION DEFECT CLOSURE
Закрыть текущий CSP-compatible Playwright defect системно:

text
find all string/eval-based browser waits
remove incompatible patterns
add static regression guard
run complete browser suite with real CSP
capture artifacts
PHASE 2 — FOUNDATION FULL REGRESSION
На реальной Windows reference machine:

text
STATIC
API
SECURITY
CONCURRENCY
PERSISTENCE
REAL BROWSER DESKTOP
REAL BROWSER MOBILE VIEWPORT
ADMIN
MODEL PULL/ASSIGN
START
VERIFY
RESTART
VERIFY
REPAIR
VERIFY
STOP
START
VERIFY
PHASE 3 — REBOOT / RECOVERY
Провести настоящий Windows reboot acceptance, когда automation/process позволяет это сделать с достоверной проверкой после загрузки.

Не симулировать reboot обычным restart контейнеров.

PHASE 4 — FOUNDATION FREEZE
Создать release evidence bundle и freeze только после PASS.

PHASE 5 — v0.3 ORCHESTRATOR
До реализации WEB/FILES/CODE создать security-ready abstractions:

text
Task
Step
Capability
Tool
Permission
ExecutionPolicy
NetworkPolicy
PrivacyPolicy
Artifact
Verification
Queue
PHASE 6 — АУТЕНТИФИКАЦИЯ и РЕКЛАМА (можно параллельно с оркестратором)
Реализовать регистрацию/вход по email/паролю, хранение пользователей, сессии, базовое пользовательское соглашение, а также базовый рекламный движок (Intent Classifier на rule-based, Ad Engine, Ad Selector, Ad Render) и админ-панель для управления рекламой.

PHASE 7 — ПРОВАЙДЕРЫ И МОДЕЛИ (включая DeepSeek)
Реализовать Provider Registry, Model Registry, адаптеры для Ollama, DeepSeek, OpenAI (как минимум). Сделать админ-панель для управления провайдерами (добавление ключей, тестирование, назначение моделей режимам).

PHASE 8+ — CAPABILITIES
Каждую capability добавлять вертикально:

text
spec
→ architecture
→ acceptance
→ implementation
→ deterministic tests
→ real USER journey
→ failure test
→ security test
→ evidence
→ freeze capability
Нельзя сначала написать все backend capabilities, а пользовательские E2E оставить «на потом».

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
    87.1. Оnboarding новых сотрудников
    Проект должен быть легко развернуть на локальной машине за 10–15 минут (следуя документации).

Использование Docker Compose для быстрого старта.

Наличие тестового набора данных для проверки работоспособности.

87.2. Код-ревью и стандарты
Обязательное code review перед merge в основную ветку.

Статический анализатор (flake8, mypy, pylint) в CI.

Единый стиль кода (black/isort) – автоматическое форматирование.

Покрытие тестами новых фич – обязательно (не ниже 80% для нового кода).

87.3. Документация для разработчиков
Подробное описание каждого модуля.

Схема базы данных.

Примеры работы с API.

Руководство по добавлению новой capability.

Руководство по добавлению нового провайдера.

87.4. Сообщество и обратная связь
Создать GitHub Issues для багов и фич-реквестов.

Поддерживать Discord/Telegram канал для общения.

Регулярно выпускать релизы с changelog.I'm ready to provide the next immediate continuation of the given code snippet
while adhering strictly to the guidelines. Please go ahead and provide the context.

87.4. Ииконки в браузере
Должна быть завершенность продукта.


88. ЗАКЛЮЧИТЕЛЬНЫЕ ПОЛОЖЕНИЯ
    Данный документ является единственным и обязательным источником истины для всех этапов разработки, тестирования, выпуска и эксплуатации Personal Agent Rus.

Любое отступление от зафиксированных здесь правил, принципов и требований считается нарушением контракта и требует немедленного исправления.

Все изменения в продукте должны проходить полный цикл от спецификации до пользовательского принятия, с обязательным формированием доказательной базы.

Personal Agent Rus создаётся для реальных пользователей, поэтому главный критерий успеха – это удовлетворённость и результат, а не количество строк кода или зелёных тестов.

Настоящий документ вступает в силу немедленно и действует до выхода v1.0 и последующих версий, пока не будет заменён новой версией с обратной совместимостью.

Дата финальной версии: 10.08.2026
Версия: 6.0