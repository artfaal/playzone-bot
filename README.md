# playzone-bot

Telegram-бот для организации игровых сессий в команде. Хранит список кооперативных игр, проводит не анонимные голосования за игру, дату и рейтинг после сессии.

## Возможности

- 📋 Список игр с рейтингами и описаниями
- 🎮 Голосование за игру — случайная выборка или ручной выбор
- 📅 Голосование за дату игровой сессии
- ⭐ Рейтинг сыгранной игры (1–10), с накоплением оценок
- 👤 Не анонимные опросы — в итогах видно, кто как голосовал
- 🔐 Разделение прав: создавать голосования могут только администраторы
- 💬 Голосования всегда публикуются в группу, управлять можно из лички

## Стек

- [aiogram 3.x](https://docs.aiogram.dev/) — Telegram Bot API
- [aiosqlite](https://aiosqlite.omnilib.dev/) — асинхронная работа с SQLite
- [python-dotenv](https://github.com/theskumar/python-dotenv) — конфигурация через `.env`
- Docker + docker-compose

## Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone <repo-url>
cd playzone-bot
```

### 2. Создать `.env`

```bash
cp .env.example .env
```

Заполнить переменные:

```env
TELEGRAM_BOT_TOKEN=токен_от_BotFather
ADMIN_IDS=123456789,987654321
GROUP_CHAT_ID=-1001234567890
DATABASE_PATH=/data/playzone.db
```

| Переменная | Описание |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен бота от [@BotFather](https://t.me/BotFather) |
| `ADMIN_IDS` | ID администраторов через запятую |
| `GROUP_CHAT_ID` | ID группового чата (отрицательное число) |
| `DATABASE_PATH` | Путь к файлу БД внутри контейнера |

> **Как узнать GROUP_CHAT_ID:** напишите что-нибудь в группу, затем откройте `https://api.telegram.org/bot<TOKEN>/getUpdates` и найдите `"chat":{"id": -100XXXXXXXXX}`.

### 3. Запустить

```bash
docker compose up --build -d
```

## Команды

### Все пользователи

| Команда | Описание |
|---|---|
| `/start` | Приветствие и список команд |
| `/help` | Список команд |
| `/addgame` | Добавить игру (FSM: название → описание) |
| `/games` | Список игр с рейтингами |
| `/games_desc` | Список игр с описаниями |

### Только администраторы

| Команда | Описание |
|---|---|
| `/deletegame <название>` | Удалить игру из списка |
| `/start_vote_random` | Голосование: 5 случайных игр |
| `/start_vote_manual` | Голосование: выбрать игры из списка |
| `/start_rating` | Голосование: рейтинг игры (1–10) |
| `/start_day_vote` | Голосование: выбор даты (формат `25.02, 01.03`) |
| `/close_poll` | Закрыть опрос и опубликовать итоги в группу |

## Структура проекта

```
playzone-bot/
├── bot/
│   ├── config.py             # Конфигурация из .env
│   ├── main.py               # Точка входа
│   ├── database/
│   │   ├── schema.sql        # DDL: games, polls, poll_votes, ratings
│   │   ├── connection.py     # Подключение к SQLite
│   │   └── queries.py        # SQL-запросы
│   ├── handlers/
│   │   ├── common.py         # /start, /help
│   │   ├── games.py          # /addgame, /games, /games_desc, /deletegame
│   │   ├── admin_polls.py    # Команды голосований
│   │   └── poll_answers.py   # Обработка ответов на опросы
│   ├── filters/
│   │   └── is_admin.py       # Фильтр IsAdmin
│   ├── states/
│   │   └── states.py         # FSM-состояния
│   └── utils/
│       └── formatters.py     # Форматирование сообщений
├── data/                     # SQLite БД (volume)
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

## База данных

| Таблица | Назначение |
|---|---|
| `games` | Список игр (мягкое удаление через `is_active`) |
| `polls` | Созданные опросы с типом и маппингом вариантов |
| `poll_votes` | Голоса пользователей (upsert при каждом изменении) |
| `ratings` | Оценки игр, сохраняются при закрытии рейтингового опроса |

## Разработка

Запуск без Docker (потребуется Python 3.12+):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m bot.main
```
