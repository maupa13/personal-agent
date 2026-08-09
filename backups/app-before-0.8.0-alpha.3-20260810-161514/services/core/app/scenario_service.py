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
        "Напишите тему, компанию, человека или область, по которой нужны свежие новости. Если важен период или конкретные источники — добавьте их в том же сообщении.",
        1, "research",
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
                CREATE INDEX IF NOT EXISTS idx_scenario_states_user ON scenario_states(user_id,status,updated_at);
                CREATE INDEX IF NOT EXISTS idx_site_profiles_category ON site_profiles(category,enabled);
                """
            )
            ts = int(time.time())
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
            cleaned = re.sub(r"новост\w*|свеж\w*|последн\w*|сегодня|найд\w*|собер\w*", " ", lower)
            return 2 if len(re.findall(r"[а-яёa-z0-9]{3,}", cleaned)) >= 1 else 0
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
            }

        if conversation_id:
            with self.lock, self.db() as conn:
                conn.execute(
                    "UPDATE scenario_states SET status='executing',clarification_round=?,initial_text=?,updated_at=? WHERE conversation_id=? AND user_id=?",
                    (rounds, combined, int(time.time()), conversation_id, user_id),
                )
                conn.commit()
        return {
            "action": "execute", "scenario": self.public_definition(item), "combined_text": combined,
            "task_text": self._assessment_text(combined),
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
            return {"search_scope": "internet", "prefer_russian": True, "region": "", "allowed_domains": [], "excluded_domains": []}
        return {
            "search_scope": str(row["search_scope"]), "prefer_russian": bool(int(row["prefer_russian"])), "region": str(row["region"] or ""),
            "allowed_domains": json.loads(row["allowed_domains_json"] or "[]"), "excluded_domains": json.loads(row["excluded_domains_json"] or "[]"),
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
            out = []
            for item in raw:
                domain = str(item).strip().lower().strip(".")
                if not re.fullmatch(r"[a-z0-9.-]{3,253}", domain) or ".." in domain:
                    raise ScenarioError(f"invalid domain in {key}")
                if domain not in out:
                    out.append(domain)
            return out
        allowed, excluded = domains("allowed_domains"), domains("excluded_domains")
        prefer = bool(value.get("prefer_russian", search_scope == "prefer_ru"))
        with self.lock, self.db() as conn:
            conn.execute(
                "INSERT INTO user_web_preferences(user_id,search_scope,prefer_russian,region,allowed_domains_json,excluded_domains_json,updated_at) VALUES(?,?,?,?,?,?,?) "
                "ON CONFLICT(user_id) DO UPDATE SET search_scope=excluded.search_scope,prefer_russian=excluded.prefer_russian,region=excluded.region,allowed_domains_json=excluded.allowed_domains_json,excluded_domains_json=excluded.excluded_domains_json,updated_at=excluded.updated_at",
                (user_id, search_scope, int(prefer), region, json.dumps(allowed), json.dumps(excluded), int(time.time())),
            )
            conn.commit()
        return self.preferences(user_id)

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
