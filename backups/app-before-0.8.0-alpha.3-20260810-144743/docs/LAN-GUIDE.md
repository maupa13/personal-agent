# LAN Guide

Версия: 0.8.0-alpha.3

Personal Agent имеет LAN foundation, но полный second-device acceptance для 0.8.0-alpha.3 остаётся внешним gate на реальном Windows reference PC и физическом мобильном устройстве.

При включении LAN не публикуйте Ollama, БД, browser worker, code worker или Docker API напрямую. Для multi-user LAN предпочтителен `accounts` mode с регистрационной политикой `approval_required`.

Некоторые browser capabilities (микрофон/камера) требуют Secure Context; обычный HTTP LAN нельзя выдавать за полностью эквивалентный HTTPS/mobile experience.
