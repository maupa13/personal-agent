# PERSONAL AGENT RUS

# MASTER PRODUCT SPECIFICATION + IMPLEMENTATION PROMPT + ROADMAP

**Document type:** Canonical Product Specification
**Product:** Personal Agent Rus
**Version:** 1.0
**Target:** Production-ready browser-first AI Agent Platform
**Architecture:** Local-first + Cloud + Hybrid + External Providers
**Distribution:** SaaS / VPS / Self-hosted / Local Edge
**Development methodology:** Specification-Driven Development (SDD)

---

# 1. НАЗНАЧЕНИЕ

Этот документ является единственным каноническим specification для разработки **Personal Agent Rus**.

Он используется как исходный документ для:

- архитектуры;
- coding agents;
- Codex/Claude Code/local coding models;
- backlog;
- acceptance criteria;
- автоматических тестов;
- E2E;
- security verification;
- deployment;
- release gates.

Если более старые документы противоречат этому файлу — приоритет имеет этот документ.

---

# 2. PRODUCT VISION

Personal Agent Rus — это не чат над одной LLM и не переименованный Open WebUI.

Цель — полноценная универсальная **AI Agent Platform**, способная самостоятельно выполнять пользовательские задачи от запроса до проверенного результата.

Пользователь описывает **что нужно сделать**.

Система сама определяет:

1. намерение;
2. необходимые capabilities;
3. подходящие модели;
4. локальный или внешний provider;
5. необходимость web/browser;
6. необходимость файлов;
7. необходимость API/connector;
8. последовательность действий;
9. permissions;
10. способ проверки результата;
11. необходимые артефакты.

---

# 3. PRODUCT NAME

Каноническое название:

```
Personal Agent Rus

```

Общий технологический слой:

```
Personal Agent Core

```

Архитектура должна позволять позднее создавать:

```
Personal Agent EU
Personal Agent US
Personal Agent Enterprise
Personal Agent Private

```

---

# 4. PRODUCT PRINCIPLES

Система должна быть:

```
browser-first
multi-user
multi-tenant
local-first capable
cloud capable
hybrid capable
provider-independent
secure
observable
billable
extensible
testable
production-ready

```

---

# 5. USER EXPERIENCE

Пользователь не должен выбирать:

```
Docker container
Ollama
ComfyUI
Whisper
SearXNG
Playwright
technical model ID
quantization
context size
provider endpoint
GPU settings

```

Эти параметры скрыты за платформой.

Технические настройки доступны только:

```
Admin Console
Developer Mode
Diagnostics

```

---

# 6. ОСНОВНЫЕ ПОЛЬЗОВАТЕЛЬСКИЕ РЕЖИМЫ

UI может показывать понятные действия:

```
Объяснить
Написать
Проанализировать
Найти
Исследовать
Создать
Автоматизировать

```

Но основной интерфейс — свободный чат.

Пользователь не обязан заранее выбирать режим.

---

# 7. DEPLOYMENT MODES

Архитектура должна поддерживать:

```
SAAS
SELF_HOSTED
LOCAL
HYBRID

```

## 7.1 SaaS

Основная публичная версия:

```
Browser
↓
Personal Agent Rus
↓
VPS / Cloud

```

Пользователю достаточно:

```
register
login
choose plan
pay if needed
use product

```

---

# 8. LOCAL EDGE

В будущем должен существовать optional:

```
Personal Agent Edge

```

Он позволяет облачной версии использовать:

```
local files
local projects
local GPU
local models
local applications
local databases
private LAN resources

```

Связь:

```
User PC
↓ outbound encrypted connection
Personal Agent Cloud

```

Сервер не должен требовать открытого входящего порта на пользовательском ПК.

---

# 9. HIGH-LEVEL ARCHITECTURE

```
USER
 ↓
WEB / PWA
 ↓
CDN / WAF / REVERSE PROXY
 ↓
API GATEWAY
 ↓
AUTH / CORE / ADMIN
 ↓
REQUEST ENGINE
 ↓
INTENT ENGINE
 ↓
CONTEXT ENGINE
 ↓
PLANNER
 ↓
POLICY + PERMISSION ENGINE
 ↓
TASK ORCHESTRATOR
 ↓
┌─────────────────┬─────────────────┬──────────────────┐
│                 │                 │                  │
MODEL ROUTER   TOOL ROUTER   CONNECTOR ROUTER    SKILL ROUTER
│                 │                 │
AI PROVIDERS    WORKERS       EXTERNAL SYSTEMS
│
├ LOCAL
├ PRIVATE REMOTE
├ USER BYOK
└ PUBLIC REMOTE

 ↓
VERIFICATION ENGINE
 ↓
ARTIFACT MANAGER
 ↓
FINAL RESPONSE

```

---

# 10. CORE REGISTRIES

Обязательные abstractions:

```
CapabilityRegistry
ToolRegistry
ProviderRegistry
ModelRegistry
ConnectorRegistry
SkillRegistry
AgentRegistry

```

Не реализовывать маршрутизацию огромным набором `if/else`.

---

# 11. CAPABILITY MODEL

Capability — логическая возможность.

Примеры:

```
web.search
web.fetch
browser.navigate
file.read
file.write
code.execute
image.generate
speech.transcribe
video.analyze
database.query
external.send

```

Capability не должен быть связан с конкретным provider.

---

# 12. TOOL MODEL

Tool — конкретная implementation capability.

Каждый tool содержит:

```
id
name
version
category
description

inputSchema
outputSchema

provider

requiredPermissions
riskLevel
sideEffects

networkRequired

timeout
retryPolicy
rateLimit

costMetadata
healthStatus
enabled

```

---

# 13. PROVIDER MODEL

Provider categories:

```
LLM
VISION
IMAGE
AUDIO
VIDEO
EMBEDDING
RERANKER
SEARCH
BROWSER
STORAGE
DATABASE
CUSTOM_API

```

Modes:

```
LOCAL
REMOTE
HYBRID
CUSTOM

```

---

# 14. LOCAL MODEL PROVIDERS

Поддержать архитектурно:

```
Ollama
llama.cpp
LM Studio
vLLM
LocalAI
custom local endpoint

```

Core не должен напрямую зависеть от Ollama.

---

# 15. EXTERNAL AI PROVIDERS

Администратор должен иметь возможность подключить стороннего AI provider.

Настройки:

```
Provider Name
Provider Type
Base URL
API Key
Organization
Project
Timeout
Proxy
Models
Capabilities
Pricing metadata
Privacy policy
Enabled

```

---

# 16. OPENAI-COMPATIBLE PROVIDERS

Минимально поддержать:

```
GET /v1/models
POST /v1/chat/completions
POST /v1/embeddings

```

При наличии:

```
responses
tool calling
structured output
vision
audio
images
reranking
moderation

```

---

# 17. CUSTOM PROVIDERS

Поддержать arbitrary REST-compatible AI endpoint.

---

# 18. BYOK

Поддержать Bring Your Own Key:

```
SYSTEM_KEY
USER_KEY
TENANT_KEY

```

BYOK usage должен учитываться отдельно от platform-paid inference.

---

# 19. MODEL REGISTRY

Metadata:

```
id
providerId
technicalName
displayName
capabilities
languages
contextWindow
maxInputTokens
maxOutputTokens
toolCalling
structuredOutput
vision
audio
reasoning
coding
embedding
local
estimatedVram
estimatedRam
latencyScore
qualityScore
costInput
costOutput
privacyLevel
enabled

```

---

# 20. MODEL ROUTER

Учитывать:

```
task type
required capability
quality
latency
cost
context size
privacy
network
provider health
GPU
RAM
VRAM
user tariff
tenant policy
remaining quota

```

---

# 21. ROUTING POLICIES

```
LOCAL_ONLY
LOCAL_FIRST
CLOUD_FIRST
CLOUD_ONLY
PRIVATE_ONLY
AUTO
CUSTOM

```

---

# 22. FALLBACK

Пример:

```
local preferred
↓
local fallback
↓
private remote
↓
user BYOK
↓
platform cloud provider

```

Remote fallback должен учитывать privacy.

---

# 23. INTENT ENGINE

Один request может содержать несколько intents.

## Text

```
CHAT
QUESTION
EXPLAIN
TEACH
WRITE
REWRITE
CORRECT
SUMMARIZE
TRANSLATE
ANALYZE
COMPARE
CRITIQUE
BRAINSTORM
PLAN
DECIDE
CLASSIFY
EXTRACT

```

## Research

```
SEARCH
WEB_SEARCH
DEEP_RESEARCH
FACT_CHECK
NEWS
MARKET_RESEARCH
COMPETITOR_RESEARCH
PRODUCT_RESEARCH
ACADEMIC_RESEARCH
SOURCE_COMPARISON

```

## Web

```
OPEN_URL
FETCH_URL
READ_PAGE
SITE_ANALYSIS
SITE_SEARCH
CRAWL
SCRAPE
EXTRACT
BROWSER_INTERACTION
FORM_FILL
DOWNLOAD
UPLOAD
SCREENSHOT
MONITOR_PAGE

```

## Files

```
READ_FILE
CREATE_FILE
EDIT_FILE
DELETE_FILE
ANALYZE_FILE
COMPARE_FILES
SEARCH_FILES
CONVERT_FILE
MERGE_FILES
SPLIT_FILES

```

## Code

```
GENERATE_CODE
REVIEW_CODE
FIX_CODE
REFACTOR
DEBUG
TEST
EXECUTE
BUILD
PROJECT_ANALYSIS
PROJECT_MODIFICATION
DEPENDENCY_ANALYSIS
SECURITY_ANALYSIS
PERFORMANCE_ANALYSIS

```

## Data

```
DATA_ANALYSIS
DATA_CLEAN
DATA_TRANSFORM
ETL
SQL
STATISTICS
VISUALIZATION
FORECAST

```

## Media

```
IMAGE_ANALYSIS
IMAGE_GENERATION
IMAGE_EDIT

AUDIO_TRANSCRIPTION
AUDIO_ANALYSIS
TEXT_TO_SPEECH

VIDEO_ANALYSIS
VIDEO_TRANSCRIPTION
VIDEO_SUMMARY
VIDEO_FRAME_ANALYSIS

```

## Automation

```
AUTOMATION
SCHEDULE
MONITOR
BATCH
WORKFLOW

```

## System

```
COMPUTER_USE
OS_ACTION
APPLICATION_CONTROL

```

---

# 24. MULTIMODAL INPUT

Request может содержать одновременно:

```
text
URLs
files
images
audio
video
workspace references
previous artifacts
previous tasks

```

---

# 25. TASK PLANNER

Planner разбивает задачу на:

```
Task
Subtask
Action
Verification
Artifact

```

Поддержать DAG.

Независимые actions могут выполняться параллельно.

---

# 26. TASK STATES

```
CREATED
PLANNING
QUEUED
WAITING_PERMISSION
RUNNING
RETRYING
VERIFYING
WAITING_USER
COMPLETED
PARTIAL
BLOCKED
FAILED
CANCELLED

```

---

# 27. CHECKPOINT / RESUME

Длительные задачи должны сохранять checkpoint.

После restart:

```
resume

```

или переходить в корректный recoverable state.

---

# 28. CANCELLATION

Cancel должен реально отменять:

```
HTTP
browser jobs
model generation
downloads
subprocesses
media jobs
child tasks

```

---

# 29. EXECUTION LIMITS

Обязательные safeguards:

```
maxTasksPerSession
maxSteps
maxToolCalls
maxConsecutiveErrors
maxSameActionRepeats
maxRecoveryAttempts
maxExecutionTime
maxCost

```

---

# 30. CONTEXT ENGINE

Контекст нельзя формировать простым объединением всей истории.

Логическая структура:

```
SYSTEM POLICY
↓
PRODUCT / TENANT POLICY
↓
USER SETTINGS
↓
CURRENT TASK
↓
RECENT CONVERSATION
↓
RETRIEVED MEMORY
↓
RELEVANT DOCUMENTS
↓
TOOL OBSERVATIONS
↓
CURRENT MESSAGE

```

---

# 31. CONTEXT BUDGET

Для каждой модели учитывать:

```
contextWindow
maxInputTokens
maxOutputTokens

```

Расчёт:

```
context window
-
reserved output
-
system instructions
-
tool schemas
-
safety reserve
=
available user context

```

---

# 32. CONTEXT COMPRESSION

Порядок:

```
remove irrelevant tool noise
↓
deduplicate
↓
select relevant docs
↓
summarize older dialogue
↓
compress old observations

```

---

# 33. CONVERSATION SUMMARY

Хранить structured summary:

```
goals
decisions
constraints
preferences
completed actions
open questions
artifacts
important facts

```

Обновлять инкрементально.

---

# 34. MEMORY

Разделить:

```
session memory
conversation memory
long-term user memory
project memory
organization memory
knowledge base

```

---

# 35. MEMORY MODEL

Memory categories:

```
USER_PREFERENCE
USER_FACT
PROJECT_FACT
DECISION
WORKFLOW_PREFERENCE
CUSTOM_INSTRUCTION

```

Поля:

```
memoryId
userId
tenantId
type
content
source
createdAt
updatedAt
confidence
expiresAt

```

---

# 36. MEMORY PRIVACY

Не сохранять автоматически:

```
passwords
API keys
auth tokens
payment credentials
sensitive temporary secrets

```

Policies:

```
MEMORY_DISABLED
EXPLICIT_ONLY
SAFE_AUTOMATIC
CUSTOM

```

---

# 37. MEMORY CONTROL

Пользователь может:

```
view
edit
delete
clear all
disable memory
disable specific categories

```

---

# 38. CONTEXT RECOVERY

После restart сохраняются:

```
conversation history
summary
memory references
artifact references
task state
compressed context metadata

```

---

# 39. CONTEXT ACCEPTANCE

```
CTX-01 50+ messages remain coherent
CTX-02 context never exceeds model limit
CTX-03 restart preserves semantics
CTX-04 user clears memory
CTX-05 deleted memory does not reappear
CTX-06 irrelevant history is not blindly injected
CTX-07 large files are selectively retrieved
CTX-08 smaller model triggers safe compression

```

---

# 40. WEB SEARCH

Search provider abstraction.

Primary self-hosted implementation может быть:

```
SearXNG

```

Поддержать:

```
general web
news
images
video
academic
products
site-specific
local search

```

---

# 41. DEEP RESEARCH

Workflow:

```
research question
↓
subquestions
↓
queries
↓
multiple searches
↓
source discovery
↓
fetch
↓
browser fallback
↓
extract
↓
deduplicate
↓
source scoring
↓
cross-check
↓
contradiction analysis
↓
synthesis
↓
citations

```

Для comprehensive research — стремиться к широкому coverage, ориентир \~30 candidate sources, если тема это оправдывает.

---

# 42. SOURCE QUALITY

Оценивать:

```
primary/secondary source
authority
date
author
evidence
domain reputation
cross-source confirmation

```

Search snippet не является достаточным доказательством.

---

# 43. FACTUALITY POLICY

Modes:

```
FAST
BALANCED
STRICT
RESEARCH

```

`STRICT` и `RESEARCH` требуют более сильной external verification.

---

# 44. TEMPORAL FACTS

Для:

```
prices
news
laws
software versions
current office holders
schedules
product specs

```

предпочитать актуальный lookup.

---

# 45. UNCERTAINTY

Различать:

```
CONFIRMED
LIKELY
UNCERTAIN
NOT_FOUND
CONFLICTING_SOURCES

```

Не выдавать предположение за факт.

---

# 46. CITATION VERIFICATION

Перед final response проверять:

```
source exists
source actually retrieved
citation supports claim
citation is not only snippet

```

---

# 47. QUOTE / NUMERIC VERIFICATION

Прямые цитаты должны существовать в source.

Важные числа желательно извлекать/рассчитывать deterministically.

---

# 48. FACT-CHECK ACCEPTANCE

```
FACT-01 missing data → NOT_FOUND
FACT-02 conflicting sources surfaced
FACT-03 current facts use lookup policy
FACT-04 citations support claims
FACT-05 exact quote verified
FACT-06 numeric aggregation deterministic where possible
FACT-07 strict mode does not silently invent

```

---

# 49. WEB FETCH

Порядок:

```
HTTP fetch
↓
parse
↓
content extraction

```

Fallback:

```
Playwright/browser agent

```

---

# 50. BROWSER AGENT

Capabilities:

```
navigate
click
doubleClick
type
select
hover
scroll
drag
upload
download
tabs
cookies
DOM
screenshot
waitFor

```

---

# 51. WEB INTERACTION

Поддержать:

```
search on site
filters
pagination
infinite scroll
form fill
download
upload
catalog extraction
status checks

```

---

# 52. BROWSER SESSION ISOLATION

Изолировать:

```
cookies
sessions
localStorage
downloads
credentials

```

по:

```
userId
tenantId
browserProfileId

```

---

# 53. CRAWLER / SCRAPER

Ограничения:

```
depth
maxPages
maxBytes
sameDomain
URL patterns
rateLimit
concurrency
deduplication
timeout

```

---

# 54. FILE WORKSPACE

Каждому пользователю отдельный workspace.

Cloud:

```
/users/<userId>/workspace

```

Edge:

```
C:\PersonalAgent\workspace\<userId>

```

Дополнительные директории только через allowlist.

---

# 55. FILE FORMATS

Поддержать:

```
TXT MD CSV JSON XML YAML HTML
PDF DOCX XLSX PPTX
JPG PNG WEBP GIF SVG
MP3 WAV M4A FLAC OGG
MP4 MKV MOV WEBM
ZIP TAR GZ
JAVA KT PY JS TS JSX TSX GO RS CS CPP C PHP RB PS1 BAT SH SQL LOG

```

---

# 56. DOCUMENT PIPELINE

```
detect
validate
extract metadata
extract text
extract images
extract tables
OCR if needed
chunk/index
analyze

```

---

# 57. PDF

```
text
scans/OCR
tables
images
metadata
page references
create
merge
split

```

---

# 58. DOCX

```
read
create
edit
format
headings
tables
images
headers
footers
layout

```

---

# 59. XLSX

```
multiple sheets
formulas
styles
tables
filters
charts
conditional formatting
analytics

```

Не разрушать workbook semantics.

---

# 60. PPTX

```
read
create
edit
slides
layouts
images
tables
charts
notes

```

---

# 61. ARCHIVE SECURITY

Проверять:

```
zip slip
nested archives
max extracted size
max file count
path traversal

```

---

# 62. KNOWLEDGE BASE / RAG

Поддержать ingestion:

```
files
folders
documents
notes
URLs
artifacts

```

RAG:

```
chunk
metadata
embedding
keyword search
vector search
reranker
context builder
citations

```

---

# 63. CODING AGENT

Работать с:

```
snippet
file
folder
repository
multi-module project

```

---

# 64. PROJECT DISCOVERY

```
tree
languages
build systems
modules
entry points
tests
configs
migrations
CI
dependencies

```

---

# 65. BUILD SYSTEMS

```
Maven
Gradle
npm
pnpm
yarn
pip
Poetry
Cargo
dotnet
CMake
Make

```

---

# 66. CODING WORKFLOW

```
UNDERSTAND
↓
SPECIFY CHANGE
↓
PLAN
↓
PATCH
↓
BUILD
↓
TEST
↓
ANALYZE
↓
FIX
↓
RETEST
↓
VERIFY

```

---

# 67. SAFE CODE EDITING

Использовать:

```
diff
patch
atomic writes
rollback

```

---

# 68. CODE EXECUTION

Возвращать:

```
command
workingDirectory
duration
stdout
stderr
exitCode
resourceUsage

```

---

# 69. SANDBOX

Недоверенный code execution:

```
CPU limit
RAM limit
disk limit
network policy
timeout
filesystem isolation
process limit

```

---

# 70. DATABASE AGENT

Поддержать:

```
PostgreSQL
MySQL
MariaDB
SQLite
SQL Server

```

Future:

```
MongoDB
Redis
OpenSearch
ClickHouse

```

Capabilities:

```
schema inspection
queries
optimization
index analysis
migration analysis
controlled write operations

```

---

# 71. DATA / ETL

Поддержать:

```
CSV
XLSX
JSON
Parquet
SQL
API

```

Operations:

```
clean
filter
join
aggregate
statistics
correlation
anomaly detection
trend
forecast
visualization
ETL

```

---

# 72. IMAGE

Capabilities:

```
image analysis
OCR
screenshot analysis
diagram analysis
chart analysis
object detection
text-to-image
image-to-image
inpainting
outpainting
upscale
background removal

```

---

# 73. AUDIO

```
transcription
timestamps
language detection
diarization
translation
summary
TTS

```

---

# 74. VIDEO

Pipeline:

```
probe
↓
extract audio
↓
transcribe
↓
scene detection
↓
keyframes
↓
vision
↓
OCR
↓
timeline
↓
reasoning

```

---

# 75. COMPUTER USE

Future high-risk capability.

```
screen capture
↓
vision
↓
action planner
↓
mouse/keyboard
↓
verify

```

Requires explicit permissions.

---

# 76. API CONNECTORS

Поддержать внешние системы, не только LLM.

Protocols:

```
REST
GraphQL
WebSocket
SSE
Webhook
gRPC later
SOAP optional

```

---

# 77. CONNECTOR AUTH

```
None
API Key
Bearer
Basic
OAuth2
Client Credentials
Custom Header
Cookie
Client Certificate

```

---

# 78. CONNECTOR CATEGORIES

```
Email
Calendar
Contacts
CRM
ERP
Knowledge Base
Cloud Storage
Messenger
Git
Issue Tracker
Analytics
Database
Smart Home
Custom API

```

---

# 79. CONNECTOR PERMISSIONS

Различать:

```
READ
CREATE
UPDATE
DELETE
SEND
EXECUTE

```

Read-only connector не может автоматически выполнять writes.

---

# 80. CONNECTOR CONSENT

Read после выданного permission не обязан каждый раз спрашивать confirmation.

Side effects:

```
send
delete
publish
purchase
external update

```

должны использовать Permission Engine.

---

# 81. CONNECTOR FAILURE

При external outage:

```
no fake success
clear error
PARTIAL/BLOCKED status
possible alternative

```

---

# 82. MCP / PLUGINS / SKILLS

Поддержать:

```
MCP servers
Plugin manifests
Skill registry
User-created skills

```

Plugin permissions должны быть declarative.

---

# 83. AUTOMATION ENGINE

Поддержать:

```
one-time
scheduled
recurring
event-driven
condition-based

```

---

# 84. SCHEDULER

Требования:

```
persistent schedules
restart recovery
duplicate protection
time zones
retry
locking
misfire policy

```

---

# 85. NOTIFICATIONS

```
web
email
push
messenger connector
webhook

```

---

# 86. ARTIFACT MANAGER

Каждый созданный результат регистрируется:

```
artifactId
tenantId
userId
taskId
type
mime
storageKey
size
checksum
createdAt
expiresAt
metadata

```

---

# 87. ARTIFACT TYPES

```
TXT
MD
JSON
CSV
HTML
PDF
DOCX
XLSX
PPTX
images
audio
video
archives
code
patches
reports
datasets

```

---

# 88. STORAGE

Использовать object-storage abstraction.

Например:

```
S3-compatible
MinIO
cloud object storage

```

Большие files не хранить в PostgreSQL.

---

# 89. MULTI-TENANCY

Multi-user и multi-tenant — с первого дня.

Основные entities:

```
tenant
user
membership
role
subscription
conversation
message
task
artifact
workspace
providerCredential
usage
auditEvent

```

---

# 90. DATA ISOLATION

Каждый access учитывает:

```
tenantId
userId

```

Обязательны automated IDOR/tenant-isolation tests.

---

# 91. REGISTRATION

Flow:

```
Sign Up
↓
verify email/phone according config
↓
create account
↓
accept terms
↓
create workspace
↓
assign free plan/trial
↓
onboarding

```

---

# 92. AUTHENTICATION

```
email/password
magic link optional
OAuth optional
passkeys future
enterprise SSO future

```

---

# 93. PASSWORD SECURITY

Использовать production-grade hashing:

```
Argon2id

```

или эквивалент.

---

# 94. SESSION SECURITY

```
HttpOnly
Secure
SameSite
CSRF protection
session rotation
session list
revoke

```

---

# 95. PASSWORD RESET

```
request
↓
single-use token
↓
expiry
↓
reset
↓
invalidate relevant sessions

```

---

# 96. ACCOUNT SECURITY

```
2FA/TOTP
backup codes
login alerts
session management
suspicious login detection

```

---

# 97. PERSONAL CABINET

Разделы:

```
Profile
Security
Sessions
Subscription
Payments
Invoices/Receipts
Usage
Limits
API Keys
Connected Providers
Connected Services
Storage
Memory
Workspaces
Automations
Notifications
Privacy
Data Export
Delete Account

```

---

# 98. ONBOARDING / HELP

First-run tour:

```
chat
attachments
research
artifacts
privacy
usage

```

Также:

```
contextual help
FAQ
user docs
admin docs
versioned docs

```

---

# 99. BILLING SUBSYSTEM

Отдельные components:

```
Plan Catalog
Subscription Service
Entitlement Engine
Usage Metering
Payment Adapter
Invoice/Receipt Adapter
Webhook Handler
Billing Ledger

```

---

# 100. PLAN MODEL

Configuration-driven plans:

```
FREE
PLUS
PRO
TEAM
ENTERPRISE

```

---

# 101. ENTITLEMENTS

Не использовать scattered `if plan ==`.

Параметры:

```
maxMessages
maxResearchTasks
maxStorage
maxFileSize
maxConcurrentTasks
allowedModels
premiumModels
webAccess
codeExecution
videoAnalysis
automation
API
BYOK
teamMembers

```

---

# 102. USAGE METERING

Считать:

```
input tokens
output tokens
requests
GPU time
research tasks
searches
browser minutes
code execution
image generation
STT minutes
TTS characters
video minutes
storage
network usage if needed

```

---

# 103. BILLING LEDGER

Append-oriented usage events:

```
usageEventId
userId
tenantId
taskId
providerId
modelId
metric
quantity
unit
estimatedCost
timestamp

```

---

# 104. PAYMENT PROVIDER ABSTRACTION

Operations:

```
createPayment
createSubscription
cancelSubscription
refund
getStatus
handleWebhook

```

Core не должен зависеть от одного payment gateway.

---

# 105. PAYMENT WEBHOOK SECURITY

```
signature verification
timestamp validation
idempotency
deduplication
replay protection

```

---

# 106. SUBSCRIPTION STATES

```
TRIAL
ACTIVE
PAST_DUE
GRACE_PERIOD
CANCEL_AT_PERIOD_END
CANCELLED
EXPIRED

```

---

# 107. PAYMENT STATES

```
CREATED
PENDING
PAID
FAILED
CANCELLED
REFUNDED
PARTIALLY_REFUNDED

```

---

# 108. COST GOVERNANCE

Отдельно от customer billing.

Provider costs:

```
requests/day
requests/month
tokens/day
tokens/month
cost/day
cost/month
GPU minutes
browser minutes
audio/video limits

```

Scopes:

```
SYSTEM
TENANT
USER
PROVIDER
MODEL
API_KEY

```

---

# 109. REAL-TIME QUOTA CHANGES

Admin должен менять quotas без restart/deploy.

---

# 110. QUOTA WARNINGS

Configurable thresholds:

```
50%
75%
90%
100%

```

---

# 111. COST EXHAUSTION

При превышении remote quota:

```
fallback local/private

```

если возможно.

Пользователь получает понятное сообщение, а не `500`.

---

# 112. COST-AWARE ROUTING

Router учитывает:

```
remaining quota
estimated cost
plan
provider budget
quality requirement

```

---

# 113. COST REPORTS

Admin:

```
usage by provider
usage by model
usage by tenant
usage by user
estimated cost
provider-reported cost where available

```

---

# 114. PUBLIC API

Personal Agent Rus должен предоставлять API:

```
POST /api/v1/chat
POST /api/v1/tasks
GET /api/v1/tasks/{id}
POST /api/v1/files
GET /api/v1/artifacts/{id}

```

---

# 115. OPENAI-COMPATIBLE INBOUND API

Architecture-ready:

```
/v1/models
/v1/chat/completions

```

Чтобы Personal Agent Rus можно было подключать к:

```
IDE
bots
automation tools
third-party clients

```

---

# 116. USER API KEYS

Личный кабинет:

```
Create
Name
Permissions
Expiration
Last Used
Revoke

```

Полный key показывать только один раз.

---

# 117. RATE LIMITING

По:

```
IP
user
tenant
API key
endpoint
plan

```

---

# 118. ANTI-ABUSE

Detect:

```
mass registration
credential stuffing
API abuse
resource exhaustion
automation loops
spam
fraud signals
browser abuse

```

---

# 119. PERMISSION ENGINE

Capabilities:

```
NETWORK
FILE_READ
FILE_WRITE
FILE_DELETE
BROWSER_READ
BROWSER_INTERACT
CODE_EXECUTE
SHELL_EXECUTE
DATABASE_READ
DATABASE_WRITE
EXTERNAL_API_READ
EXTERNAL_API_WRITE
SEND_MESSAGE
COMPUTER_CONTROL
REMOTE_AI

```

---

# 120. PERMISSION SCOPES

```
ALLOW_ONCE
ALLOW_SESSION
ALLOW_WORKSPACE
ALWAYS
DENY

```

---

# 121. SIDE EFFECT CLASSIFICATION

```
READ_ONLY
REVERSIBLE
WRITE
DESTRUCTIVE
FINANCIAL
EXTERNAL_COMMUNICATION

```

---

# 122. RISK LEVEL

```
LOW
MEDIUM
HIGH
CRITICAL

```

---

# 123. SECRETS

Хранить encrypted:

```
API keys
OAuth tokens
DB credentials
payment credentials
SMTP credentials

```

Secrets не должны попадать в:

```
logs
prompts
traces
analytics
responses

```

---

# 124. SSRF PROTECTION

Защита:

```
localhost
metadata endpoints
private ranges
redirect attacks
DNS rebinding
unsupported protocols

```

Private-network access — отдельная explicit policy.

---

# 125. UPLOAD SECURITY

Проверять:

```
size
MIME
extension
magic bytes
archive contents
malware where appropriate

```

---

# 126. PROMPT INJECTION DEFENSE

External web/file content считается untrusted.

Разделять:

```
system policy
user instructions
external content
tool results

```

Документ не может сам изменить agent policy.

---

# 127. LOGGING

Structured JSON logs.

Common fields:

```
timestamp
severity
service
environment
version
traceId
requestId
tenantId
userId
taskId
stepId
providerId

```

PII minimization обязательна.

---

# 128. LOG LEVELS

```
TRACE
DEBUG
INFO
WARN
ERROR

```

DEBUG/TRACE не включать постоянно в production.

---

# 129. AUDIT LOG

Отдельный immutable-oriented audit trail:

```
LOGIN
LOGOUT
PASSWORD_CHANGE
2FA_CHANGE
USER_CREATED
USER_DELETED
ROLE_CHANGED
PAYMENT
SUBSCRIPTION_CHANGE
API_KEY_CREATED
API_KEY_REVOKED
PROVIDER_CHANGED
SECRET_CHANGED
FILE_DELETED
ADMIN_ACTION
PERMISSION_GRANTED

```

---

# 130. OBSERVABILITY

Разделять:

```
Application Log
Audit Log
Task Event
Metric
Trace
User-visible Activity

```

---

# 131. METRICS

Product:

```
requests
active users
task completion
task failures

```

API:

```
RPS
p50
p95
p99
4xx
5xx

```

Agent:

```
active tasks
queue depth
tool calls
failures
retries
cancellations

```

AI:

```
latency
tokens
provider errors
fallback count
GPU
VRAM
loaded models

```

Infrastructure:

```
CPU
RAM
disk
network
DB pool
Redis
storage

```

Billing:

```
payment failures
webhook failures
usage lag

```

---

# 132. TRACING

Distributed tracing:

```
request
→ orchestrator
→ model
→ tool
→ provider
→ storage

```

OpenTelemetry-compatible architecture.

---

# 133. ALERTING

Channels:

```
Email
Telegram-compatible bot/webhook
Generic Webhook

```

Rules:

```
core down
5xx spike
p95 latency threshold
disk pressure
DB down
queue stalled
GPU worker down
provider outage
payment webhook errors
backup failure

```

---

# 134. ADMIN CONSOLE

Admin dashboard:

```
users
registrations
active users
subscriptions
revenue
usage
tasks
errors
providers
models
workers
queues
storage
system health

```

---

# 135. ADMIN USER MANAGEMENT

Admin может:

```
find user
suspend
unsuspend
change plan
reset quota
grant credits
inspect sanitized diagnostics

```

Не давать unrestricted access к private conversations по умолчанию.

---

# 136. PROVIDER ADMIN

```
add
edit
disable
test connection
discover models
set priority
set limits
set pricing
set privacy

```

---

# 137. FEATURE FLAGS

Например:

```
video_agent
computer_use
premium_research
new_router
new_billing

```

---

# 138. VPS / CLOUD TOPOLOGY

Минимально:

```
Internet
↓
DNS/CDN/WAF
↓
Reverse Proxy
↓
Web + API
↓
PostgreSQL
Redis
Object Storage
Queue

Workers:
AI
Web
Browser
Files
Code
Image
Audio
Video
Notifications
Billing

```

---

# 139. MODULAR MONOLITH FIRST

Не создавать десятки микросервисов без необходимости.

Первая production architecture:

```
Modular Monolith API
+
isolated heavy workers

```

Выносить отдельный сервис только если есть:

```
scaling need
security boundary
technology requirement
independent lifecycle

```

---

# 140. QUEUES

Jobs:

```
AI
research
browser
files
code
image
audio
video
notifications
billing

```

Поддержать:

```
priority
retry
dead-letter
timeout
cancel
idempotency

```

---

# 141. GPU SCHEDULING

Учитывать:

```
VRAM
loaded model
job priority
model affinity
queue
estimated size

```

---

# 142. BACKPRESSURE

При overload:

```
queue
defer
graceful reject

```

Не убивать сервер.

---

# 143. FRONTEND

Responsive:

```
desktop
laptop
tablet
phone

```

---

# 144. MOBILE WEB

Обязательно:

```
registration
login
chat
file upload
image upload
camera upload
audio upload
voice input
artifact download
task status
payments/account

```

---

# 145. TASK PROGRESS UI

Показывать user-safe progress:

```
Ищу источники
Найдено 18 источников
Анализирую файл
Создаю Excel
Проверяю результат

```

Не показывать hidden chain-of-thought.

---

# 146. PWA

Architecture-ready:

```
home screen
push
share target

```

---

# 147. LEGAL / CONSENT

Versioned:

```
Terms
Privacy Policy
Cookie Policy
AI Usage Policy
Payment Terms

```

Хранить acceptance record.

---

# 148. DATA EXPORT / ACCOUNT DELETE

Пользователь может:

```
export profile
export conversations
export files/artifacts
delete account

```

Deletion workflow должен учитывать legally required retained billing/audit records.

---

# 149. BACKUPS

Автоматические backups:

```
PostgreSQL
object metadata
configuration
critical encrypted secret metadata

```

---

# 150. BACKUP POLICY

```
frequency
retention
encryption
off-site copy
restore test

```

Backup без проверенного restore не считается достаточным.

---

# 151. DISASTER RECOVERY

Определить:

```
RPO
RTO
restore procedure
DNS recovery
storage recovery
secret recovery

```

---

# 152. CI/CD

Branch strategy:

```
main
feature/*
fix/*

```

`develop` допускается только если реально нужен.

`main` должен быть deployable.

---

# 153. PR PIPELINE

```
format/lint
compile
unit tests
static analysis
dependency scan
security scan
integration tests
contract tests
build

```

---

# 154. MAIN / RELEASE PIPELINE

```
full build
↓
tests
↓
container images
↓
SBOM
↓
image scan
↓
versioned artifacts
↓
deploy staging
↓
staging E2E
↓
release gate

```

---

# 155. CONTAINER VERSIONING

Использовать immutable tags:

```
personal-agent-api:1.4.2

```

`latest` может быть только alias.

---

# 156. ROLLBACK

Application rollback не должен разрушать persistent data.

DB migrations должны быть backward-compatible насколько возможно.

Использовать expand/contract migrations для risky schema changes.

---

# 157. ENVIRONMENTS

```
local
test
staging
production

```

Production secrets запрещены в tests.

---

# 158. DOCUMENTATION

User docs:

```
Getting Started
Chat
Files
Research
Images
Audio
Video
Coding
Automations
Privacy
Plans & Limits
API
Troubleshooting
FAQ

```

Admin docs:

```
Deployment
Configuration
Users
Providers
Models
Billing
Backups
Restore
Monitoring
Security
Updates
Incident Recovery

```

Документация versioned вместе с release.

---

# 159. PERFORMANCE

Контролировать:

```
API latency
chat latency
research duration
queue wait
provider latency
GPU utilization

```

---

# 160. JAVA BACKEND GUIDELINES

Если backend на Java:

```
Java 21+
Spring Boot 3+

```

Использовать:

```
records
sealed types where useful
pattern matching
virtual threads where appropriate

```

Не применять reactive stack только ради моды.

---

# 161. JAVA PERFORMANCE

Следить за:

```
GC
large allocations
streaming files
bounded concurrency
timeouts
backpressure
DB pool
N+1
indexes
query plans

```

---

# 162. DATABASE

Основной transactional store:

```
PostgreSQL

```

Cache/coordination:

```
Redis-compatible

```

Large files:

```
Object Storage

```

---

# 163. DATABASE MODEL

Минимально:

```
users
tenants
tenant_members
sessions

plans
subscriptions
payments
payment_events

usage_events
quota_state

conversations
messages

tasks
task_steps
task_events

artifacts
files
workspaces

providers
models
user_provider_credentials

connectors
connector_credentials

automations
api_keys
audit_events
feature_flags

```

---

# 164. DATABASE RULES

```
migrations only
indexes
pagination
avoid N+1
transaction boundaries
connection pool

```

---

# 165. OUTBOX / EVENTS

Для критичных event flows использовать transactional outbox where justified.

Domain events:

```
UserRegistered
TaskCreated
TaskCompleted
PaymentSucceeded
SubscriptionChanged
ArtifactCreated
AutomationTriggered

```

---

# 166. FAILURE MODEL

Ошибки:

```
USER_ERROR
VALIDATION
PERMISSION
PROVIDER
NETWORK
TIMEOUT
RATE_LIMIT
RESOURCE
INTERNAL
SECURITY

```

Пользователь получает понятное сообщение, не stack trace.

---

# 167. SUPPORT / DIAGNOSTICS

Поддержать:

```
support contact
error ID
status page
sanitized diagnostic bundle

```

Diagnostic bundle:

```
versions
health
task IDs
error IDs
selected logs

```

Без secrets и private content.

---

# 168. USER SCENARIOS

Обязательные end-to-end сценарии:

## Chat

```
register
→ login
→ ask
→ route model
→ stream response
→ record usage

```

## Research

```
question
→ search
→ sources
→ verify
→ cited answer

```

## Web parsing

```
URL
→ fetch/browser
→ pagination
→ extract
→ XLSX

```

## File

```
upload PDF
→ parse/OCR
→ analyze
→ answer with refs

```

## Excel

```
upload
→ analyze
→ charts
→ new XLSX
→ PDF report

```

## Code

```
upload/open repository
→ scan
→ build
→ test
→ patch
→ retest

```

## Audio

```
upload
→ transcribe
→ diarize
→ summarize
→ action items

```

## Video

```
upload
→ transcript
→ scenes
→ OCR/vision
→ report

```

## API

```
GET external data
→ compare with file
→ preview
→ permission
→ external write

```

## Automation

```
create schedule/condition
→ execute later
→ notify

```

---

# 169. SECURITY TESTS

Обязательные:

```
IDOR
tenant isolation
SSRF
XSS
CSRF
SQL injection
path traversal
zip slip
auth bypass
rate limit bypass
webhook spoofing
secret leakage
prompt injection
upload abuse

```

---

# 170. BILLING TESTS

```
payment success
duplicate webhook
out-of-order webhook
payment failure
refund
subscription cancel
upgrade
downgrade
grace period
quota renewal

```

---

# 171. AGENT TESTS

```
tool success
tool failure
timeout
malformed output
provider outage
fallback
permission denied
cancel
resume
max-step
max-cost

```

---

# 172. WEB ACCEPTANCE

```
simple search
news
multi-source research
static page
dynamic page
JS page
pagination
download
structured extraction
citation verification

```

Использовать реальные regression cases, включая сложные сайты.

---

# 173. FILE ACCEPTANCE

```
TXT
MD
JSON
CSV
PDF text
PDF scan
DOCX
XLSX
PPTX
ZIP
image
audio
video
Java
Python
PowerShell

```

---

# 174. CODING ACCEPTANCE

Sample Java project:

```
read
modify
compile
JUnit 5
integration test
failure recovery

```

---

# 175. CONTEXT ACCEPTANCE

```
50+ message dialogue
restart recovery
memory clear
large document selective retrieval
model context switch

```

---

# 176. COST ACCEPTANCE

```
daily quota
monthly quota
real-time quota update
local fallback
usage per model
race-condition protection
idempotent usage events
BYOK separated

```

---

# 177. CONNECTOR ACCEPTANCE

```
public API read
OAuth
token refresh
invalid auth
disconnect/revoke
read-only protection
outage handling

```

---

# 178. MONITORING ACCEPTANCE

```
service outage detected
alert delivered
disk pressure detected
provider outage visible
queue backlog visible
GPU metrics
trace correlation
restart preserves durable state

```

---

# 179. HELP ACCEPTANCE

```
new user completes first task
tour skippable
tour restartable
FAQ in product
admin docs separated
docs version matches app

```

---

# 180. CI ACCEPTANCE

```
failed test blocks release
security gate works
versioned images created
staging reproducible
E2E blocks release
previous image redeployable
data survives rollback

```

---

# 181. SDD PROCESS

Работать строго:

```
SPECIFICATION
↓
ARCHITECTURE
↓
ACCEPTANCE MATRIX
↓
BACKLOG
↓
IMPLEMENTATION
↓
AUTOMATED TESTS
↓
E2E
↓
SECURITY TESTS
↓
VERIFY
↓
PASS
↓
NEXT PHASE

```

---

# 182. DEFINITION OF DONE

Feature считается DONE только если:

```
implemented
tested
documented
observable
secure
permissions defined
usage impact defined
billing impact defined
E2E passed

```

---

# 183. ROADMAP PRINCIPLE

Строить вертикальными slices.

Не делать многомесячную infrastructure-only разработку без работающего пользовательского сценария.

---

# 184. PHASE 0 — FOUNDATION

```
repo structure
config
PostgreSQL
Redis
Object Storage
migrations
logging
metrics
tracing
health
CI
Docker
backup foundation

```

---

# 185. PHASE 1 — AUTH / REGISTRATION / ACCOUNT

```
sign up
login
logout
verify
password reset
sessions
user
tenant
workspace
dashboard
onboarding
privacy settings

```

---

# 186. PHASE 2 — CORE CHAT / CONTEXT

```
conversations
messages
streaming
attachments foundation
Context Engine
Memory foundation
conversation restore
local provider
OpenAI-compatible provider
router v1

```

---

# 187. PHASE 3 — PROVIDER PLATFORM / COST GOVERNANCE

```
Provider Registry
Model Registry
BYOK
provider UI
health
fallback
quota
cost tracking
priority
routing policies

```

---

# 188. PHASE 4 — WEB / RESEARCH / FACTUALITY

```
SearXNG
fetch
parser
Playwright
citations
research planner
fact-checking
source scoring
citation verifier

```

---

# 189. PHASE 5 — FILES / WORKSPACE

```
upload
storage
workspace
TXT/MD/CSV/JSON
PDF
DOCX
XLSX
PPTX
OCR
Artifact Manager

```

---

# 190. PHASE 6 — CODING AGENT

```
project workspace
terminal
sandbox
project discovery
patch
build
test
debug

```

---

# 191. PHASE 7 — IMAGE

```
vision
OCR
generation
editing
ComfyUI provider

```

---

# 192. PHASE 8 — AUDIO

```
STT
audio analysis
TTS
artifacts

```

---

# 193. PHASE 9 — VIDEO

```
probe
audio
transcript
scenes
frames
vision
timeline
summary

```

---

# 194. PHASE 10 — DATA / ETL / DATABASE

```
advanced XLSX
SQL
charts
ETL
DB connectors

```

---

# 195. PHASE 11 — CONNECTORS / MCP / PLUGINS

```
Connector SDK
REST
OAuth
MCP
Plugin Registry
Skills

```

---

# 196. PHASE 12 — AUTOMATIONS

```
scheduler
recurring
conditions
notifications
persistent workflows

```

---

# 197. PHASE 13 — BILLING / PAYMENTS

```
plans
entitlements
usage
payments
subscriptions
webhooks
billing cabinet
cost governance integration

```

---

# 198. PHASE 14 — ADMIN / OPERATIONS

```
admin dashboard
users
plans
providers
models
usage
costs
logs
alerts
health
backup/restore

```

---

# 199. PHASE 15 — PUBLIC API

```
API keys
REST API
OpenAI-compatible API
developer docs
quotas

```

---

# 200. PHASE 16 — LOCAL EDGE

```
edge service
secure pairing
local workspace
local model
local GPU
local tools
encrypted connection

```

---

# 201. PHASE 17 — COMPUTER USE

Только после mature permission/security layer.

---

# 202. PHASE 18 — TEAM / ENTERPRISE

```
organizations
roles
shared workspaces
shared knowledge
SSO
enterprise policies
private providers
enterprise audit

```

---

# 203. FIRST PUBLIC MVP

Минимально реально работают:

```
registration
login
personal cabinet
chat
model routing
local/remote providers
web search
URL reading
research
file uploads
PDF/DOCX/XLSX analysis
image analysis
artifacts
usage limits
payments
subscriptions
admin
logging
monitoring
backup
security
mobile browser

```

---

# 204. STARTING DEPLOYMENT STRATEGY

Порядок:

```
1. Local development machine
2. Browser-first Docker product
3. Multi-user/auth
4. Core agent capabilities
5. Full E2E PASS
6. Staging VPS
7. Domain + HTTPS
8. Billing sandbox
9. Production payments
10. Public beta
11. Scale infrastructure

```

Не начинать с production VPS до того, как локальный vertical slice стабилен.

---

# 205. RELEASE GATES

Stable release запрещён, если не пройдены:

```
auth
tenant isolation
registration
core chat
context restore
payment integrity
usage/quota
backup restore
security smoke
DB migrations
monitoring
production smoke

```

---

# 206. NO FAKE FEATURES

Запрещено:

```
mock production responses
fake progress
success without artifact verification
button-only implementations

```

---

# 207. NO DATA-DESTRUCTIVE REPAIR

Запрещено использовать как обычный repair:

```
docker compose down -v
drop database
delete all volumes

```

Upgrade должен сохранять пользовательские данные.

---

# 208. IMPLEMENTATION AGENT RULES

Перед изменением repository агент обязан:

1. прочитать этот specification;
2. изучить repository;
3. построить current architecture map;
4. выполнить gap analysis;
5. определить следующий vertical slice;
6. определить acceptance;
7. реализовать;
8. написать tests;
9. запустить tests;
10. исправить failures;
11. показать PASS/FAIL evidence.

---

# 209. REQUIRED INITIAL DOCUMENTS

Создать:

```
docs/specification/MASTER-SPEC.md

docs/architecture/ARCHITECTURE.md
docs/architecture/SECURITY.md
docs/architecture/DATA-MODEL.md
docs/architecture/PROVIDERS.md
docs/architecture/AGENTS.md
docs/architecture/BILLING.md
docs/architecture/DEPLOYMENT.md
docs/architecture/CONTEXT-MEMORY.md
docs/architecture/OBSERVABILITY.md

docs/acceptance/ACCEPTANCE-MATRIX.md

docs/roadmap/ROADMAP.md
docs/roadmap/PHASE-0.md

```

Но именно:

```
docs/specification/MASTER-SPEC.md

```

остаётся главным источником требований.

---

# 210. REQUIRED AGENT REPORT AFTER EACH PHASE

После каждого phase агент обязан вывести:

```
PHASE
STATUS: PASS / FAIL / PARTIAL

Implemented:
- ...

Files changed:
- ...

Migrations:
- ...

Tests added:
- ...

Tests executed:
- ...

Results:
- PASS ...
- FAIL ...

Security checks:
- ...

Known limitations:
- ...

Next phase:
- ...

```

Нельзя скрывать failed tests.

---

# 211. ULTIMATE USER ACCEPTANCE

Новый пользователь без технических знаний способен:

```
register
login
pay
chat
attach files
research web
interact with websites
analyze PDFs/Excel/Word
analyze images/audio/video
write/fix/run code
use external APIs
create documents/reports
create automations
download artifacts
view usage
manage subscription
manage memory/privacy

```

---

# 212. ULTIMATE SYSTEM ACCEPTANCE

Все операции:

```
isolated between users
permission-controlled
securely logged
audit-tracked
usage-metered
billing-aware
observable
recoverable
backed up
test-covered

```

---

# 213. FINAL ARCHITECTURAL INVARIANT

Каждая новая функция должна следовать:

```
USER INTENT
↓
CAPABILITY
↓
POLICY / PERMISSION
↓
PROVIDER-INDEPENDENT TOOL
↓
ROUTER
↓
IMPLEMENTATION
↓
VERIFICATION
↓
ARTIFACT / RESULT

```

---

# 214. PRIORITY ORDER

При конфликте требований:

```
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

```

---

# 215. FINAL DIRECTIVE

Не создавать очередной AI chat clone.

Создать полноценную платформу **Personal Agent Rus**, объединяющую:

```
AI models
agents
research
web
browser
files
documents
coding
data
images
audio
video
automation
external APIs
connectors
MCP
plugins
local computing
cloud computing
BYOK
registration
personal cabinet
payments
subscriptions
billing
quotas
memory
fact-checking
administration
security
logging
audit
monitoring
public API
enterprise-ready architecture

```

в одном понятном браузерном продукте.

---

# 216. FIRST EXECUTION INSTRUCTION

Получив этот specification в repository, implementation agent должен сначала выполнить:

```
1. Repository Discovery
2. Gap Analysis
3. Current Architecture Map
4. Target Architecture
5. Dependency Map
6. Threat Model
7. Data Model
8. API Contracts
9. Capability Registry Design
10. Provider/Tool Design
11. Context/Memory Design
12. Billing/Quota Design
13. Acceptance Matrix
14. Prioritized Roadmap
15. Phase 0 Backlog
16. Phase 0 Implementation
17. Automated Verification

```

Только после PASS переходить к следующему vertical slice.

---

# END OF MASTER SPECIFICATION