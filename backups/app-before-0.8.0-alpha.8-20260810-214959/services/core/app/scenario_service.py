from __future__ import annotations

import json
import re
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScenarioDefinition:
    scenario_id: str
    title: str
    description: str
    category: str
    icon: str
    required_capabilities: tuple[str, ...]
    keywords: tuple[str, ...]
    example_prompt: str
    clarification_prompt: str
    max_clarification_rounds: int = 1
    web_intent: str | None = None
    clarification_options: tuple[str, ...] = ()


SCENARIOS: tuple[ScenarioDefinition, ...] = (
    ScenarioDefinition(
        "clothing", "Подобрать одежду", "Найти подходящие вещи по размеру, бюджету, сезону и стилю", "life", "◫",
        ("web",), ("одежд", "футболк", "рубашк", "брюк", "шорт", "куртк", "кроссов", "кед", "обув", "образ"),
        "Подбери мне одежду под мои параметры и бюджет.",
        "Чтобы подобрать действительно подходящие варианты, уточните одним сообщением: размер или основные мерки, примерный бюджет, сезон/повод и что точно не нравится. Можно ответить только на известные пункты — остальное я подберу сам.",
        1, "search",
    ),
    ScenarioDefinition(
        "procurement", "Найти закупки", "Найти и отфильтровать подходящие закупки и тендеры", "work", "▤",
        ("web", "research"), ("закупк", "тендер", "госзакуп", "44-фз", "223-фз"),
        "Найди подходящие закупки по моей теме.",
        "Чтобы не принести случайные закупки, напишите одним сообщением: что именно закупают/ваша специализация, регион (если важен), желаемый диапазон цены и насколько свежие объявления нужны. Если часть параметров не важна — так и напишите.",
        2, "research",
    ),
    ScenarioDefinition(
        "real_estate", "Найти недвижимость", "Собрать и сравнить подходящие варианты жилья", "life", "⌂",
        ("web", "research"), ("квартир", "недвиж", "циан", "дом купить", "снять жиль", "аренд"),
        "Помоги найти и сравнить подходящие варианты недвижимости.",
        "Уточните одним сообщением: город/район, купить или снять, примерный бюджет, сколько комнат и что критично по расположению. Необязательные параметры можно пропустить.",
        2, "research",
    ),
    ScenarioDefinition(
        "gift", "Выбрать подарок", "Подобрать идеи подарка и при необходимости найти варианты покупки", "life", "◇",
        ("web",), ("подар", "что подарить"),
        "Помоги выбрать хороший подарок.",
        "Чтобы идеи были персональными, напишите одним сообщением: кому подарок, повод, примерный бюджет и что человек любит/чем увлекается. Если чего-то не знаете — пропустите.",
        1, "search",
    ),
    ScenarioDefinition(
        "product", "Выбрать товар", "Сравнить товары по реальным критериям и источникам", "life", "▣",
        ("web", "research"), ("купить", "выбрать товар", "сравни товар", "лучший", "маркетплейс"),
        "Помоги выбрать лучший вариант товара под мои требования.",
        "Уточните одним сообщением: что выбираем, бюджет, 2–3 самых важных требования и есть ли магазины/бренды, которые нужно предпочесть или исключить.",
        1, "research",
    ),
    ScenarioDefinition(
        "travel", "Спланировать поездку", "Собрать маршрут, варианты и практические детали поездки", "life", "✈",
        ("web", "research"), ("поездк", "путешеств", "маршрут", "отпуск", "отель", "куда поехать"),
        "Помоги спланировать поездку.",
        "Уточните одним сообщением: откуда и куда/какой тип отдыха хотите, примерные даты, сколько человек и ориентир по бюджету. Если направление ещё не выбрано — напишите предпочтения.",
        1, "research",
    ),
    ScenarioDefinition(
        "news", "Разобраться в новостях", "Собрать свежие источники и объяснить, что произошло", "work", "◉",
        ("web", "research"), ("новост", "что произошло", "что случилось", "свежие события"),
        "Собери свежие новости по интересующей меня теме и объясни главное.",
        "Что вам сейчас интереснее? Выберите тему или напишите свою. Если ничего не выбирать, я соберу главное и самое заметное за последнее время.",
        1, "research", clarification_options=("Главное", "Технологии", "Игры", "Россия", "Мир", "Бизнес", "Наука", "Спорт", "Другое"),
    ),
)

BY_ID = {item.scenario_id: item for item in SCENARIOS}

DEFAULT_SITE_PROFILES = (
    ("zakupki", "zakupki.gov.ru", "procurement", "search,browser,static", "ru"),
    ("cian", "cian.ru", "real_estate", "search,browser,static", "ru"),
    ("yandex", "yandex.ru", "search", "search", "ru"),
    ("rbc", "rbc.ru", "news", "search,browser,static", "ru"),
)


class ScenarioError(Exception):
    pass


class ScenarioService:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.lock = threading.RLock()

    def db(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        with self.lock, self.db() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS scenario_states (
                  conversation_id TEXT NOT NULL,
                  user_id TEXT NOT NULL,
                  scenario_id TEXT NOT NULL,
                  initial_text TEXT NOT NULL,
                  clarification_round INTEGER NOT NULL DEFAULT 0,
                  status TEXT NOT NULL,
                  updated_at INTEGER NOT NULL,
                  PRIMARY KEY(conversation_id,user_id)
                );
                CREATE TABLE IF NOT EXISTS user_web_preferences (
                  user_id TEXT PRIMARY KEY,
                  search_scope TEXT NOT NULL DEFAULT 'internet',
                  prefer_russian INTEGER NOT NULL DEFAULT 1,
                  region TEXT NOT NULL DEFAULT '',
                  allowed_domains_json TEXT NOT NULL DEFAULT '[]',
                  excluded_domains_json TEXT NOT NULL DEFAULT '[]',
                  news_interests_json TEXT NOT NULL DEFAULT '[]',
                  updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS site_profiles (
                  id TEXT PRIMARY KEY,
                  domain_pattern TEXT NOT NULL,
                  category TEXT NOT NULL,
                  acquisition_order TEXT NOT NULL,
                  egress_region TEXT NOT NULL DEFAULT 'auto',
                  enabled INTEGER NOT NULL DEFAULT 1,
                  updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS admin_search_policy (
                  id TEXT PRIMARY KEY,
                  provider_order_json TEXT NOT NULL DEFAULT '["searxng"]',
                  general_max_sources INTEGER NOT NULL DEFAULT 5,
                  news_max_sources INTEGER NOT NULL DEFAULT 8,
                  research_max_sources INTEGER NOT NULL DEFAULT 10,
                  preferred_domains_json TEXT NOT NULL DEFAULT '[]',
                  blocked_domains_json TEXT NOT NULL DEFAULT '[]',
                  updated_at INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_scenario_states_user ON scenario_states(user_id,status,updated_at);
                CREATE INDEX IF NOT EXISTS idx_site_profiles_category ON site_profiles(category,enabled);
                """
            )
            pref_columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(user_web_preferences)").fetchall()}
            if "news_interests_json" not in pref_columns:
                conn.execute("ALTER TABLE user_web_preferences ADD COLUMN news_interests_json TEXT NOT NULL DEFAULT '[]'")
            ts = int(time.time())
            conn.execute(
                "INSERT OR IGNORE INTO admin_search_policy(id,provider_order_json,general_max_sources,news_max_sources,research_max_sources,preferred_domains_json,blocked_domains_json,updated_at) VALUES('default','[\"searxng\"]',5,8,10,'[]','[]',?)",
                (ts,),
            )
            for row in DEFAULT_SITE_PROFILES:
                conn.execute(
                    "INSERT OR IGNORE INTO site_profiles(id,domain_pattern,category,acquisition_order,egress_region,enabled,updated_at) VALUES(?,?,?,?,?,1,?)",
                    (*row, ts),
                )
            conn.commit()

    @staticmethod
    def public_definition(item: ScenarioDefinition) -> dict[str, Any]:
        return {
            "id": item.scenario_id,
            "title": item.title,
            "description": item.description,
            "category": item.category,
            "icon": item.icon,
            "required_capabilities": list(item.required_capabilities),
            "example_prompt": item.example_prompt,
            "max_clarification_rounds": item.max_clarification_rounds,
            "clarification_options": list(item.clarification_options),
        }

    def list_scenarios(self, entitlements: dict[str, Any]) -> list[dict[str, Any]]:
        out = []
        for item in SCENARIOS:
            if all(bool((entitlements.get(cap) or {}).get("enabled")) for cap in item.required_capabilities):
                out.append(self.public_definition(item))
        return out

    def detect(self, text: str) -> ScenarioDefinition | None:
        lower = str(text or "").lower()
        # A direct URL is a stronger routing signal than a generic scenario keyword.
        # Auto scenarios may enrich free-form goals, but must not replace URL/site tasks.
        if re.search(r"https?://", lower):
            return None
        best: tuple[int, ScenarioDefinition] | None = None
        for item in SCENARIOS:
            score = sum(2 if key in lower else 0 for key in item.keywords)
            if item.scenario_id == "product" and any(x in lower for x in ("цена", "модель", "характеристик")):
                score += 1
            if score and (best is None or score > best[0]):
                best = (score, item)
        return best[1] if best else None

    def _active_state(self, user_id: str, conversation_id: str) -> dict[str, Any] | None:
        if not conversation_id:
            return None
        with self.lock, self.db() as conn:
            row = conn.execute(
                "SELECT * FROM scenario_states WHERE user_id=? AND conversation_id=? AND status='clarifying'",
                (user_id, conversation_id),
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def _assessment_text(text: str) -> str:
        # Internal conversation scaffolding is metadata, not user evidence.  If it
        # participates in heuristics, words such as "параметры пользователя" can
        # accidentally satisfy a scenario and terminate clarification too early.
        cleaned = re.sub(
            r"(?im)^\s*Дополнительные\s+параметры\s+пользователя\s*:\s*",
            "",
            str(text or ""),
        )
        return re.sub(r"[ \t]+", " ", cleaned).strip()

    @staticmethod
    def _signal_count(item: ScenarioDefinition, text: str) -> int:
        text = ScenarioService._assessment_text(text)
        lower = text.lower()
        number = bool(re.search(r"\b\d[\d\s]*(?:₽|руб|тыс|млн|р\b)", lower))
        if item.scenario_id == "clothing":
            size = bool(re.search(r"\b(?:xx?s|s|m|l|xl|xxl|\d{2,3})\b", lower)) or any(x in lower for x in ("размер", "рост", "талия", "груд", "бедр", "стоп"))
            context = any(x in lower for x in ("лет", "зим", "осен", "весн", "офис", "работ", "свад", "повседнев", "спорт"))
            dislike = any(x in lower for x in ("не люблю", "не нравится", "не хочу", "исключ"))
            return sum((number, size, context, dislike))
        if item.scenario_id == "procurement":
            subject = len(re.findall(r"[а-яёa-z0-9]{4,}", re.sub(r"закуп\w*|тендер\w*|найд\w*", " ", lower))) >= 2
            region = any(x in lower for x in ("область", "край", "москва", "петербург", "регион", "республик", "округ"))
            freshness = any(x in lower for x in ("сегодня", "недел", "месяц", "свеж", "актуаль", "до "))
            return sum((subject, region, number, freshness))
        if item.scenario_id == "real_estate":
            location = bool(re.search(r"\b(?:москв|петербург|спб|казан|екатеринбург|новосибирск|город|район)\w*", lower))
            type_ = any(x in lower for x in ("квартир", "дом", "студи", "комнат", "снять", "аренд", "купить"))
            commute = any(x in lower for x in ("метро", "центр", "школ", "работ", "транспорт"))
            return sum((location, type_, number, commute))
        if item.scenario_id == "gift":
            person = any(x in lower for x in ("муж", "жен", "друг", "подруг", "мам", "пап", "ребен", "коллег", "сын", "доч"))
            occasion = any(x in lower for x in ("день рожд", "юбилей", "свад", "новый год", "празд", "годовщ"))
            interest = any(x in lower for x in ("любит", "увлека", "интерес", "игр", "книг", "спорт", "пк"))
            return sum((person, occasion, interest, number))
        if item.scenario_id == "product":
            subject = len(re.findall(r"[а-яёa-z0-9]{4,}", re.sub(r"куп\w*|выбр\w*|лучш\w*|товар\w*", " ", lower))) >= 1
            requirements = any(x in lower for x in ("важно", "нужно", "хочу", "не менее", "не больше", "характерист"))
            brand = any(x in lower for x in ("бренд", "марка", "xiaomi", "asus", "samsung", "apple", "honor"))
            return sum((subject, requirements, brand, number))
        if item.scenario_id == "travel":
            destination = bool(re.search(r"\b(?:в|на)\s+[А-Яа-яЁёA-Za-z-]{4,}", text))
            dates = any(x in lower for x in ("июн", "июл", "август", "сентябр", "дней", "недел", "дата", "летом", "зимой"))
            people = bool(re.search(r"\b\d+\s*(?:человек|взросл|дет)", lower))
            return sum((destination, dates, people, number))
        if item.scenario_id == "news":
            # Explicit domain/company/topic is enough. Generic starter copy such as
            # "по интересующей меня теме" is not a topic and must not suppress
            # one useful clarification for a first-time user.
            if re.search(r"(?:[a-z0-9-]+\.)+[a-z]{2,63}", lower):
                return 2
            cleaned = re.sub(r"новост\w*|свеж\w*|последн\w*|сегодня|найд\w*|собер\w*|разобра\w*|объясн\w*|главн\w*|интересующ\w*|тем\w*|меня|мне|самое|популярн\w*|актуальн\w*", " ", lower)
            tokens = [x for x in re.findall(r"[а-яёa-z0-9]{3,}", cleaned) if x not in {"что", "как", "про", "для", "или", "все", "всё"}]
            return 2 if tokens else 0
        return 2

    def prepare(self, *, user_id: str, conversation_id: str, text: str, explicit_scenario_id: str = "") -> dict[str, Any]:
        text = str(text or "").strip()
        state = self._active_state(user_id, conversation_id)
        if state:
            item = BY_ID.get(str(state["scenario_id"]))
            if not item:
                return {"action": "none"}
            combined = f"{state['initial_text']}\n\nДополнительные параметры пользователя: {text}".strip()
            rounds = int(state["clarification_round"]) + 1
        else:
            item = BY_ID.get(str(explicit_scenario_id or "").strip()) if explicit_scenario_id else self.detect(text)
            if not item:
                return {"action": "none"}
            combined = text
            rounds = 0

        # News can use explicitly saved interests before asking anything.
        # This keeps the starter flow useful for returning users while a new
        # user receives one bounded clarification instead of a generic answer.
        if item.scenario_id == "news" and self._signal_count(item, combined) < 2:
            interests = [str(x).strip() for x in (self.preferences(user_id).get("news_interests") or []) if str(x).strip()]
            if interests:
                combined = f"{combined}\n\n{', '.join(interests[:8])}".strip()
        signals = self._signal_count(item, combined)
        needs = signals < 2
        if needs and rounds < item.max_clarification_rounds and conversation_id:
            with self.lock, self.db() as conn:
                conn.execute(
                    "INSERT INTO scenario_states(conversation_id,user_id,scenario_id,initial_text,clarification_round,status,updated_at) VALUES(?,?,?,?,?,'clarifying',?) "
                    "ON CONFLICT(conversation_id,user_id) DO UPDATE SET scenario_id=excluded.scenario_id,initial_text=excluded.initial_text,clarification_round=excluded.clarification_round,status='clarifying',updated_at=excluded.updated_at",
                    (conversation_id, user_id, item.scenario_id, combined, rounds, int(time.time())),
                )
                conn.commit()
            return {
                "action": "clarify", "scenario": self.public_definition(item), "message": item.clarification_prompt,
                "round": rounds + 1, "max_rounds": item.max_clarification_rounds,
                "options": list(item.clarification_options),
            }

        if conversation_id:
            with self.lock, self.db() as conn:
                conn.execute(
                    "UPDATE scenario_states SET status='executing',clarification_round=?,initial_text=?,updated_at=? WHERE conversation_id=? AND user_id=?",
                    (rounds, combined, int(time.time()), conversation_id, user_id),
                )
                conn.commit()

        task_text = self._assessment_text(combined)
        if item.scenario_id == "news":
            # Starter copy is UX text, not a useful search query. On the final
            # bounded clarification round, turn quick replies into concise
            # search intent instead of leaking the whole starter sentence to
            # the search provider. Explicit domains always remain untouched.
            if re.search(r"(?:[a-z0-9-]+\.)+[a-z]{2,63}", task_text.lower()):
                pass
            elif state:
                topic = re.sub(r"\s+", " ", text).strip()
                if topic.casefold() in {"главное", "main", "top", "главные"}:
                    task_text = "главные свежие новости сегодня"
                elif topic:
                    task_text = f"свежие новости сегодня: {topic}"
            elif self._signal_count(item, task_text) < 2:
                interests = [str(x).strip() for x in (self.preferences(user_id).get("news_interests") or []) if str(x).strip()]
                if interests:
                    task_text = "свежие новости сегодня по интересам: " + ", ".join(interests[:8])

        return {
            "action": "execute", "scenario": self.public_definition(item), "combined_text": combined,
            "task_text": task_text,
            "web_intent": item.web_intent,
            "instruction": (
                f"SCENARIO: {item.title}. Цель пользователя: {combined}. "
                "Используй указанные ограничения как приоритетные. Не задавай дополнительные вопросы без критической необходимости. "
                "Если каких-то необязательных данных всё ещё нет, сделай разумные предположения и явно перечисли их коротко. "
                "Результат должен помогать принять решение, а не быть общим перечнем советов."
            ),
        }

    def finish(self, *, user_id: str, conversation_id: str) -> None:
        if not conversation_id:
            return
        with self.lock, self.db() as conn:
            conn.execute(
                "UPDATE scenario_states SET status='completed',updated_at=? WHERE user_id=? AND conversation_id=?",
                (int(time.time()), user_id, conversation_id),
            )
            conn.commit()

    def preferences(self, user_id: str) -> dict[str, Any]:
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT * FROM user_web_preferences WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            return {"search_scope": "internet", "prefer_russian": True, "region": "", "allowed_domains": [], "excluded_domains": [], "news_interests": []}
        return {
            "search_scope": str(row["search_scope"]), "prefer_russian": bool(int(row["prefer_russian"])), "region": str(row["region"] or ""),
            "allowed_domains": json.loads(row["allowed_domains_json"] or "[]"), "excluded_domains": json.loads(row["excluded_domains_json"] or "[]"),
            "news_interests": json.loads(row["news_interests_json"] or "[]"),
        }

    def set_preferences(self, user_id: str, value: dict[str, Any]) -> dict[str, Any]:
        search_scope = str(value.get("search_scope", "internet")).strip().lower()
        if search_scope not in {"internet", "prefer_ru", "selected"}:
            raise ScenarioError("invalid search_scope")
        region = re.sub(r"\s+", " ", str(value.get("region", "")).strip())[:120]

        def domains(key: str) -> list[str]:
            raw = value.get(key) or []
            if not isinstance(raw, list) or len(raw) > 30:
                raise ScenarioError(f"invalid {key}")
            out: list[str] = []
            for raw_item in raw:
                domain = str(raw_item).strip().lower().strip(".")
                if not re.fullmatch(r"[a-z0-9.-]{3,253}", domain) or ".." in domain:
                    raise ScenarioError(f"invalid domain in {key}")
                if domain not in out:
                    out.append(domain)
            return out

        allowed, excluded = domains("allowed_domains"), domains("excluded_domains")
        if set(allowed) & set(excluded):
            raise ScenarioError("a domain cannot be both allowed and excluded")
        raw_interests = value.get("news_interests") or []
        if isinstance(raw_interests, str):
            raw_interests = re.split(r"[\n,;]+", raw_interests)
        if not isinstance(raw_interests, list) or len(raw_interests) > 20:
            raise ScenarioError("invalid news_interests")
        news_interests: list[str] = []
        seen_interests: set[str] = set()
        for raw_item in raw_interests:
            item = re.sub(r"\s+", " ", str(raw_item or "").strip())[:80]
            key = item.casefold()
            if item and key not in seen_interests:
                news_interests.append(item)
                seen_interests.add(key)
            if len(news_interests) >= 8:
                break
        prefer = bool(value.get("prefer_russian", search_scope == "prefer_ru"))
        with self.lock, self.db() as conn:
            conn.execute(
                "INSERT INTO user_web_preferences(user_id,search_scope,prefer_russian,region,allowed_domains_json,excluded_domains_json,news_interests_json,updated_at) VALUES(?,?,?,?,?,?,?,?) "
                "ON CONFLICT(user_id) DO UPDATE SET search_scope=excluded.search_scope,prefer_russian=excluded.prefer_russian,region=excluded.region,allowed_domains_json=excluded.allowed_domains_json,excluded_domains_json=excluded.excluded_domains_json,news_interests_json=excluded.news_interests_json,updated_at=excluded.updated_at",
                (user_id, search_scope, int(prefer), region, json.dumps(allowed), json.dumps(excluded), json.dumps(news_interests, ensure_ascii=False), int(time.time())),
            )
            conn.commit()
        return self.preferences(user_id)

    @staticmethod
    def _domain_list(value: Any, *, limit: int = 50) -> list[str]:
        if isinstance(value, str):
            raw = re.split(r"[\s,;]+", value)
        elif isinstance(value, list):
            raw = value
        else:
            raw = []
        out: list[str] = []
        for item in raw:
            domain = str(item or "").strip().lower().strip(".")
            if not domain:
                continue
            if not re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", domain):
                raise ScenarioError(f"invalid domain: {domain}")
            if domain not in out:
                out.append(domain)
            if len(out) >= limit:
                break
        return out

    def search_policy(self) -> dict[str, Any]:
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT * FROM admin_search_policy WHERE id='default'").fetchone()
        if not row:
            return {"provider_order": ["searxng"], "general_max_sources": 5, "news_max_sources": 8, "research_max_sources": 10, "preferred_domains": [], "blocked_domains": []}
        try: providers = json.loads(row["provider_order_json"] or "[]")
        except Exception: providers = ["searxng"]
        try: preferred = json.loads(row["preferred_domains_json"] or "[]")
        except Exception: preferred = []
        try: blocked = json.loads(row["blocked_domains_json"] or "[]")
        except Exception: blocked = []
        return {
            "provider_order": [str(x) for x in providers if str(x)] or ["searxng"],
            "general_max_sources": int(row["general_max_sources"]),
            "news_max_sources": int(row["news_max_sources"]),
            "research_max_sources": int(row["research_max_sources"]),
            "preferred_domains": [str(x) for x in preferred],
            "blocked_domains": [str(x) for x in blocked],
            "updated_at": int(row["updated_at"]),
        }

    def set_search_policy(self, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ScenarioError("search policy must be an object")
        current = self.search_policy()
        providers = value.get("provider_order", current["provider_order"])
        if not isinstance(providers, list) or not providers:
            raise ScenarioError("provider_order must be a non-empty list")
        providers = [str(x).strip().lower() for x in providers if str(x).strip()]
        # alpha.6 has one real search-provider adapter. Never persist a fake one.
        if any(x != "searxng" for x in providers):
            raise ScenarioError("only searxng search provider is available in this build")
        def bounded(name: str, default: int, low: int = 1, high: int = 20) -> int:
            try: result = int(value.get(name, default))
            except Exception as exc: raise ScenarioError(f"invalid {name}") from exc
            if result < low or result > high: raise ScenarioError(f"{name} must be between {low} and {high}")
            return result
        general = bounded("general_max_sources", current["general_max_sources"])
        news = bounded("news_max_sources", current["news_max_sources"], 7, 20)
        research = bounded("research_max_sources", current["research_max_sources"], 7, 20)
        preferred = self._domain_list(value.get("preferred_domains", current["preferred_domains"]))
        blocked = self._domain_list(value.get("blocked_domains", current["blocked_domains"]))
        if set(preferred) & set(blocked):
            raise ScenarioError("a domain cannot be both preferred and blocked")
        ts = int(time.time())
        with self.lock, self.db() as conn:
            conn.execute(
                "UPDATE admin_search_policy SET provider_order_json=?,general_max_sources=?,news_max_sources=?,research_max_sources=?,preferred_domains_json=?,blocked_domains_json=?,updated_at=? WHERE id='default'",
                (json.dumps(providers), general, news, research, json.dumps(preferred), json.dumps(blocked), ts),
            )
            conn.commit()
        return self.search_policy()

    def site_profiles(self) -> list[dict[str, Any]]:
        with self.lock, self.db() as conn:
            rows = conn.execute("SELECT * FROM site_profiles ORDER BY category,id").fetchall()
        return [dict(row) | {"enabled": bool(int(row["enabled"]))} for row in rows]

    def update_site_profile(self, profile_id: str, *, enabled: bool, acquisition_order: str | None = None, egress_region: str | None = None) -> dict[str, Any]:
        profile_id = str(profile_id).strip().lower()
        with self.lock, self.db() as conn:
            row = conn.execute("SELECT * FROM site_profiles WHERE id=?", (profile_id,)).fetchone()
            if not row:
                raise ScenarioError("site profile not found")
            order = str(acquisition_order if acquisition_order is not None else row["acquisition_order"]).strip().lower()
            allowed = {"search", "browser", "static"}
            parts = [x.strip() for x in order.split(",") if x.strip()]
            if not parts or any(x not in allowed for x in parts):
                raise ScenarioError("invalid acquisition_order")
            region = str(egress_region if egress_region is not None else row["egress_region"]).strip().lower()
            if region not in {"auto", "ru", "global"}:
                raise ScenarioError("invalid egress_region")
            conn.execute("UPDATE site_profiles SET enabled=?,acquisition_order=?,egress_region=?,updated_at=? WHERE id=?", (int(bool(enabled)), ",".join(parts), region, int(time.time()), profile_id))
            conn.commit()
            out = conn.execute("SELECT * FROM site_profiles WHERE id=?", (profile_id,)).fetchone()
        result = dict(out); result["enabled"] = bool(int(result["enabled"])); return result
