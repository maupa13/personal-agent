# Personal Agent Rus v0.7.2 — Manual Acceptance Checklist

> First run: extract package anywhere and execute `RUN-FIRST.cmd`. After installation, run all lifecycle commands from `C:\AI\RusPersonalAgent`.

**Назначение:** ручная проверка релиза на reference Windows PC после автоматических gate-тестов.  
**Принцип:** если шаг фактически не выполнен — не ставить PASS. При любом расхождении сохранять логи/скриншоты и останавливаться на соответствующем разделе.

---

## 0. Перед началом

### Что должно быть

- Windows 11 reference PC;
- Docker Desktop запущен;
- текущий Personal Agent Rus уже установлен или распакован;
- архив `personal-agent-rus-v0.7.2-orchestrator-vps-deployment-release.zip`;
- существующие `.env`, данные и `.git` сохраняются.

### Важно

Не использовать для обычного обновления:

```powershell
docker compose down -v
docker volume prune
docker system prune
```

Не удалять volumes вручную.

---

# 1. Обновление до v0.7.2

Распаковать содержимое v0.7.2 **поверх текущей рабочей папки Personal Agent Rus** с заменой файлов.

Не удалять:

```text
.git
.env
```

Открыть PowerShell в папке проекта.

Запустить:

```powershell
.\VERIFY-PACKAGE.ps1
```

Ожидается:

```text
[PASS] Windows PowerShell lifecycle syntax verified
[PASS] Windows Docker command-binding self-test verified
[PASS] Personal Agent Rus signed package integrity verified
```

Статус:

- [ ] PASS
- [ ] FAIL

Далее:

```powershell
.\REPAIR.cmd
```

Ожидается:

- Core пересобран/обновлён;
- volumes не удалены;
- Ollama/model data сохранены;
- Core ready;
- real inference PASS;
- Repair verification PASS.

Статус:

- [ ] PASS
- [ ] FAIL

---

# 2. Проверка версии и главного UI

Открыть:

```text
http://127.0.0.1:3100
```

Если уже был открыт старый UI — один раз выполнить:

```text
Ctrl+F5
```

Ожидается:

- интерфейс Personal Agent Rus;
- версия `v0.7.2`;
- sidebar;
- Новый чат;
- история;
- режимы Авто / Быстро / Умно;
- возможности Chat / Web / Files / Code;
- ссылка на настройки/аккаунт;
- явный вход в Администрирование;
- пользователь НЕ видит Docker/Ollama/container IDs/model IDs.

Статус:

- [ ] PASS
- [ ] FAIL

---

# 3. Базовый чат

## CHAT-01 Русский язык

Отправить:

```text
ок
```

Ожидается нормальный ответ **по-русски**.

- [ ] PASS
- [ ] FAIL

## CHAT-02 Обычный запрос

Отправить:

```text
Объясни простыми словами, что такое Docker-контейнер и чем он отличается от виртуальной машины.
```

Ожидается:

- реальный ответ модели;
- русский язык;
- отсутствие технической ошибки;
- сообщение появляется в истории.

- [ ] PASS
- [ ] FAIL

## CHAT-03 Presets

Проверить по очереди карточки:

```text
Объяснить
Написать
Проанализировать
```

Для каждой отправить один запрос.

Примеры:

```text
Объяснить: Почему небо голубое?
Написать: Составь короткое деловое письмо о переносе встречи.
Проанализировать: Сравни PostgreSQL и SQLite для локального desktop-приложения.
```

Ожидается заметно соответствующее типу задачи поведение.

- [ ] PASS
- [ ] FAIL

## CHAT-04 Режимы

Один и тот же небольшой запрос выполнить в:

```text
Авто
Быстро
Умно
```

Проверить, что UI переключает режим и запрос завершается.

USER не должен видеть технический model ID.

- [ ] PASS
- [ ] FAIL

---

# 4. История и управление диалогами

Создать минимум 3 чата.

Проверить:

- [ ] Новый чат создаётся;
- [ ] переключение между чатами работает;
- [ ] переименование работает;
- [ ] поиск по истории работает;
- [ ] удаление одного чата работает;
- [ ] очистка текущего чата работает;
- [ ] экспорт чата работает;
- [ ] после F5 история остаётся;
- [ ] после закрытия/открытия браузера история остаётся.

---

# 5. Web / URL / Research

## WEB-01 URL honesty + real Web

Отправить:

```text
О чем сейчас говорят на https://dtf.ru/ ? Приведи несколько свежих материалов со ссылками.
```

Ожидается:

- запрос распознан как Web/Research;
- система не отвечает из памяти модели;
- отображаются реальные источники либо честная ошибка получения источника;
- никаких выдуманных заголовков/URL.

Статус:

- [ ] PASS
- [ ] BLOCKED_EXTERNAL
- [ ] FAIL

## WEB-02 Новости

Отправить:

```text
Найди свежие новости о PostgreSQL за последние дни. Сравни несколько источников и дай ссылки.
```

Ожидается:

- несколько источников;
- даты/актуальность;
- source cards/ссылки;
- итог основан на полученных данных.

- [ ] PASS
- [ ] FAIL

## WEB-03 Конкретная страница

Отправить URL обычной статьи и попросить:

```text
Прочитай эту страницу и дай 5 ключевых тезисов.
```

Ожидается, что ответ соответствует содержанию страницы.

- [ ] PASS
- [ ] FAIL

## WEB-04 Недоступный источник

Указать явно несуществующую страницу.

Ожидается:

- понятная ошибка;
- никаких выдуманных данных;
- UI не зависает.

- [ ] PASS
- [ ] FAIL

---

# 6. Files / Workspace / Artifacts

Использовать НЕ личные важные файлы, а тестовые.

## FILE-01 TXT

Создать `manual-test.txt`:

```text
Кодовое слово: АПЕЛЬСИН-742.
Вторая строка: тест Personal Agent Rus.
```

Загрузить и спросить:

```text
Какое кодовое слово находится в файле?
```

Ожидаемый ответ:

```text
АПЕЛЬСИН-742
```

- [ ] PASS
- [ ] FAIL

## FILE-02 PDF

Загрузить обычный текстовый PDF.

Попросить:

```text
Кратко перескажи документ и укажи основные тезисы.
```

- [ ] PASS
- [ ] FAIL

## FILE-03 DOCX

Загрузить DOCX и попросить извлечь конкретный фрагмент/заголовок.

- [ ] PASS
- [ ] FAIL

## FILE-04 XLSX

Загрузить XLSX с несколькими значениями.

Попросить:

```text
Проанализируй таблицу и назови максимальное значение.
```

Проверить ответ вручную.

- [ ] PASS
- [ ] FAIL

## FILE-05 PPTX

Загрузить PPTX.

Попросить перечислить заголовки слайдов/основные идеи.

- [ ] PASS
- [ ] FAIL

## FILE-06 Создание артефакта

Попросить:

```text
Создай Markdown-файл с заголовком "Ручной тест" и тремя пунктами:
1. Chat PASS
2. Web PASS
3. Files PASS
```

Скачать созданный файл.

Проверить:

- файл физически скачался;
- открывается;
- содержимое соответствует запросу.

- [ ] PASS
- [ ] FAIL

---

# 7. Multi-capability Task Engine

Это один из главных новых ручных тестов v0.7.2.

Отправить:

```text
Найди свежую информацию о PostgreSQL из нескольких источников.
Сравни ключевые изменения.
Создай краткий отчет и подготовь результаты в Markdown, Excel и PDF.
```

Ожидается USER-visible progress примерно вида:

```text
Ищу источники
Читаю страницы
Проверяю данные
Анализирую
Создаю Markdown
Создаю Excel
Создаю PDF
Проверяю результаты
Готово
```

В конце должны быть реальные артефакты:

- [ ] MD;
- [ ] XLSX;
- [ ] PDF.

Каждый файл:

- [ ] скачивается;
- [ ] открывается;
- [ ] не пустой;
- [ ] содержит результаты задачи.

Task не должен получить `COMPLETED`, если файл невалиден.

Итог:

- [ ] PASS
- [ ] FAIL

---

# 8. Code

Сначала автоматический реальный Docker gate:

```powershell
.\CODE-ACCEPTANCE.cmd
```

Ожидается PASS для:

```text
Python
Java 21
PowerShell
sandbox contract
```

- [ ] PASS
- [ ] FAIL

## CODE-01 Python вручную

В UI Code выполнить:

```python
print(sum(range(1, 101)))
```

Ожидается:

```text
5050
```

- [ ] PASS
- [ ] FAIL

## CODE-02 Ошибка

Запустить заведомо ошибочный Python-код:

```python
print(unknown_variable)
```

Ожидается:

- controlled failure;
- stderr/ошибка;
- система НЕ говорит «успешно».

- [ ] PASS
- [ ] FAIL

## CODE-03 Timeout

Запустить бесконечный цикл только через предназначенный Code sandbox test/UI.

Ожидается:

- hard timeout/cancel;
- UI возвращается в рабочее состояние;
- Core не падает.

- [ ] PASS
- [ ] FAIL

---

# 9. Registration / Login / Account

Если текущий профиль `personal`, основной локальный UI может не требовать логина.

Отдельно открыть:

```text
http://127.0.0.1:3100/register
http://127.0.0.1:3100/login
http://127.0.0.1:3100/account
```

Проверить:

- [ ] страницы существуют;
- [ ] формы нормально выглядят;
- [ ] нет model IDs/runtime internals.

Если тестируете `accounts` mode:

- [ ] регистрация;
- [ ] login;
- [ ] logout;
- [ ] новая login-сессия;
- [ ] account открывается после входа.

---

# 10. Тарифы / Usage

В личном кабинете должны отображаться:

```text
Лайт      0 ₽ / месяц
Медиум  500 ₽ / месяц
Про     1000 ₽ / месяц
```

Проверить:

- [ ] Лайт;
- [ ] Медиум 500 ₽;
- [ ] Про 1000 ₽;
- [ ] отображение не показывает технический provider/model пользователю.

## Tokens setting

Найти настройку отображения usage/token statistics.

По умолчанию:

- [ ] токены скрыты.

Включить:

```text
Показывать использование токенов
```

После нового запроса:

- [ ] usage/tokens становятся видны.

Выключить:

- [ ] снова скрыты.

Важно:

```text
LOCAL → не расходует коммерческий remote quota
REMOTE PLATFORM API → учитывается quota/cost
BYOK → учитывается статистика, но не platform-paid cost
```

---

# 11. Admin Console

Открыть из USER UI:

```text
Администрирование
```

или:

```text
http://127.0.0.1:3100/admin
```

Проверить, что без правильной admin auth технические данные недоступны.

После входа проверить вкладки/разделы.

## ADMIN-01 Providers

Ожидается:

- [ ] локальный Ollama обнаружен автоматически;
- [ ] видны реально установленные модели;
- [ ] не нужно вручную добавлять уже существующие Ollama model IDs.

## ADMIN-02 External provider

Если есть тестовый OpenAI-compatible endpoint / LM Studio:

- добавить provider;
- Test connection;
- Discover models.

Ожидается:

- [ ] provider добавился;
- [ ] модели обнаружились;
- [ ] secret после сохранения обратно полностью не показывается.

## ADMIN-03 Routing

Проверить назначения:

```text
Авто
Быстро
Умно
```

Изменить один mapping → сохранить → F5.

- [ ] mapping сохранился.

Вернуть исходный mapping.

## ADMIN-04 Billing / Usage

Проверить:

- [ ] тарифы;
- [ ] local usage;
- [ ] remote usage;
- [ ] BYOK usage;
- [ ] token/cost counters;
- [ ] quota/budget configuration.

## ADMIN-05 Monitoring

Открыть `Мониторинг`.

Проверить отображение:

- [ ] version = 0.7.0;
- [ ] uptime;
- [ ] load;
- [ ] RAM;
- [ ] disk;
- [ ] DB;
- [ ] users/sessions;
- [ ] tasks;
- [ ] failed tasks;
- [ ] artifacts;
- [ ] usage;
- [ ] deployments;
- [ ] warnings/alerts.

---

# 12. Restart / Persistence

До рестарта создать:

- минимум 2 чата;
- один artifact;
- одну Admin routing-настройку;
- при возможности зарегистрированный test account.

Запустить:

```powershell
.\RESTART.cmd
```

После PASS:

```powershell
.\VERIFY.cmd
```

Открыть UI.

Проверить:

- [ ] чаты на месте;
- [ ] artifacts на месте;
- [ ] admin routing на месте;
- [ ] account/session semantics корректны;
- [ ] модель отвечает.

---

# 13. STOP → START

Запустить:

```powershell
.\STOP.cmd
```

Убедиться, что UI перестал отвечать.

Затем:

```powershell
.\START.cmd
.\VERIFY.cmd
```

Проверить:

- [ ] данные сохранены;
- [ ] чат работает;
- [ ] settings сохранены.

---

# 14. Repair здоровой системы

Запустить повторно:

```powershell
.\REPAIR.cmd
```

Ожидается:

- repair idempotent;
- user data не удаляются;
- named volumes сохраняются;
- Core снова ready;
- real inference PASS.

- [ ] PASS
- [ ] FAIL

---

# 15. Полные автоматические gates после ручной проверки

Запустить:

```powershell
.\WEB-ACCEPTANCE.cmd
.\CODE-ACCEPTANCE.cmd
.\FULL-ACCEPTANCE.cmd
.\RELEASE-ACCEPTANCE.cmd
```

Не закрывать окно при первом PASS — дождаться финального результата каждого script.

Отметить:

- [ ] WEB-ACCEPTANCE PASS
- [ ] CODE-ACCEPTANCE PASS
- [ ] FULL-ACCEPTANCE PASS
- [ ] RELEASE-ACCEPTANCE PASS

---

# 16. LAN — реальный телефон/ноутбук

Это отдельный environment gate.

На Windows убедиться, что текущая сеть имеет профиль **Private**.

В PowerShell:

```powershell
.\LAN-ENABLE.cmd
.\LAN-STATUS.cmd
```

Скрипт должен показать LAN URL.

На телефоне/ноутбуке в той же Wi-Fi сети открыть этот URL.

Проверить с физического устройства:

- [ ] UI открывается;
- [ ] новый чат;
- [ ] реальный ответ;
- [ ] refresh;
- [ ] история;
- [ ] загрузка файла;
- [ ] загрузка изображения, если UI разрешает;
- [ ] скачивание artifact;
- [ ] mobile layout;
- [ ] Admin не открыт без auth.

После теста при желании:

```powershell
.\LAN-DISABLE.cmd
```

Итог:

- [ ] LAN-LIVE PASS
- [ ] FAIL

---

# 17. VPS — только если уже есть VPS и домен

Для реального gate нужны:

```text
VPS IP/hostname
SSH login
SSH password ИЛИ private key
public domain
DNS A/AAAA
TCP 80/443
remote/OpenAI-compatible AI provider
```

В UI:

```text
Администрирование → VPS / Deploy
```

## VPS-01 Fingerprint

Ввести host/port/login/domain.

Нажать:

```text
Получить fingerprint
```

Сверить fingerprint сервера.

- [ ] PASS

## VPS-02 Prepare VPS

Если свежий Debian/Ubuntu и вход root:

```text
Подготовить VPS
```

Ожидается установка Docker + Compose.

- [ ] PASS / N/A

## VPS-03 Preflight

Нажать:

```text
Preflight
```

Для слабого VPS ожидается рекомендация:

```text
server-lite
```

- [ ] PASS

## VPS-04 Remote provider

Для server-lite выбрать уже настроенный remote provider либо потом настроить его в VPS Admin.

Не выбирать local Ollama как единственную AI-модель слабого VPS.

- [ ] PASS

## VPS-05 Deploy

Нажать:

```text
Deploy + Hot Verify
```

PASS допустим только если:

1. Core healthy внутри VPS;
2. `https://DOMAIN/api/system` реально открывается извне;
3. product = Personal Agent Rus;
4. version = 0.7.0.

- [ ] PASS
- [ ] FAIL

## VPS-06 Browser hot test

Открыть:

```text
https://DOMAIN
```

Проверить:

- [ ] registration;
- [ ] login;
- [ ] chat;
- [ ] remote AI answer;
- [ ] account;
- [ ] Admin;
- [ ] Monitoring;
- [ ] Secure HTTPS.

Итог:

- [ ] DEPLOY-LIVE PASS
- [ ] FAIL

---

# 18. YooKassa — пока только при наличии реального merchant/test shop

Gate нельзя считать PASS без реального магазина и публичного HTTPS.

Нужно:

```text
Shop ID
Secret Key
HTTPS domain
webhook URL
```

Webhook:

```text
https://DOMAIN/api/billing/webhook/yookassa
```

Проверить:

- создание checkout;
- переход на YooKassa;
- тестовый payment;
- callback/webhook;
- subscription activation;
- duplicate webhook idempotency;
- usage/plan отображение после оплаты.

Итог:

- [ ] BILL-LIVE PASS
- [ ] BLOCKED_ENVIRONMENT
- [ ] FAIL

---

# 19. Windows reboot gate

Перед reboot:

- создать новый chat;
- запомнить его содержимое;
- убедиться, что runtime работает.

Перезагрузить **настоящую Windows**, не Docker.

После входа:

- запустить Personal Agent согласно текущей настройке autostart/manual start;
- выполнить:

```powershell
.\VERIFY.cmd
```

Проверить:

- [ ] containers/runtime восстановлены;
- [ ] данные чата на месте;
- [ ] artifacts на месте;
- [ ] settings на месте;
- [ ] inference работает.

Итог:

- [ ] REBOOT PASS
- [ ] FAIL

---

# 20. Что присылать при FAIL

Не пересказывать ошибку вручную.

Сначала выполнить:

```powershell
.\STATUS.cmd
.\LOGS.cmd
```

Прислать:

1. весь вывод упавшей команды;
2. `logs\PERSONAL-AGENT-LAST.log`;
3. содержимое `logs\acceptance-artifacts\`, если папка появилась;
4. скриншот проблемного UI;
5. точный текст запроса, на котором произошёл FAIL;
6. для VPS — название упавшего deployment stage, но НЕ пароль/private key/API secret.

Никогда не отправлять:

```text
PA_ADMIN_TOKEN
API keys
YooKassa Secret Key
SSH private key
пароли
```

---

# 21. Минимум, который нужен мне от тебя сейчас

Если не хочется проходить весь длинный чек-лист за один раз, сначала выполнить **эти 10 пунктов**:

1. `VERIFY-PACKAGE.ps1`
2. `REPAIR.cmd`
3. открыть UI и подтвердить `v0.7.2`
4. обычный русский chat
5. DTF/Web запрос
6. загрузить TXT и проверить кодовое слово
7. Research → MD/XLSX/PDF
8. открыть Admin → Providers + Monitoring + VPS/Deploy
9. `CODE-ACCEPTANCE.cmd`
10. `FULL-ACCEPTANCE.cmd`

Если всё это PASS — затем:

```text
RESTART
STOP → START
LAN phone/laptop
Windows reboot
VPS live
YooKassa live
```

---

# Ручной итоговый статус

```text
LOCAL USER UI            PASS / FAIL
CHAT                     PASS / FAIL
WEB/RESEARCH             PASS / FAIL / BLOCKED_EXTERNAL
FILES                    PASS / FAIL
MULTI-CAPABILITY TASK    PASS / FAIL
CODE                     PASS / FAIL
AUTH/ACCOUNT             PASS / FAIL
BILLING UI/USAGE         PASS / FAIL
ADMIN                    PASS / FAIL
MONITORING               PASS / FAIL
RESTART/PERSISTENCE      PASS / FAIL
STOP/START               PASS / FAIL
REPAIR                   PASS / FAIL
AUTOMATED RELEASE GATES  PASS / FAIL
LAN LIVE                 PASS / FAIL / BLOCKED_ENVIRONMENT
WINDOWS REBOOT           PASS / FAIL
VPS LIVE                 PASS / FAIL / BLOCKED_ENVIRONMENT
YOOKASSA LIVE            PASS / FAIL / BLOCKED_ENVIRONMENT
```

**Не ставить `RELEASE PASS`, если обязательный environment gate для выбранного профиля не выполнен.**
