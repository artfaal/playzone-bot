import json
from typing import Any


def format_games_list(games: list) -> str:
    if not games:
        return "Список игр пуст. Добавьте первую игру командой /addgame"

    lines = ["🎮 Список кооперативных игр:\n"]
    for i, game in enumerate(games, 1):
        avg_score = game["avg_score"]
        rating_count = game["rating_count"]
        if avg_score is not None and rating_count > 0:
            score_str = f"⭐ {avg_score}/10 ({rating_count} {_rating_word(rating_count)})"
        else:
            score_str = "нет оценок"
        lines.append(f"{i}. {game['name']}   {score_str}")

    lines.append(f"\nВсего игр: {len(games)}")
    return "\n".join(lines)


MAX_TG_MSG = 4000  # чуть меньше лимита 4096 для запаса


def format_games_desc_chunks(games: list) -> list[str]:
    """Возвращает список сообщений с играми и описаниями.
    Разбивает по границам игр, чтобы не превысить лимит Telegram."""
    if not games:
        return ["Список игр пуст. Добавьте первую игру командой /addgame"]

    total = len(games)

    # Собираем текстовый блок для каждой игры
    blocks: list[str] = []
    for i, game in enumerate(games, 1):
        desc = game["description"] or "нет описания"
        avg_score = game["avg_score"]
        rating_count = game["rating_count"]
        if avg_score is not None and rating_count > 0:
            score_str = f"⭐ {avg_score}/10 ({rating_count} {_rating_word(rating_count)})"
        else:
            score_str = "⭐ нет оценок"
        blocks.append(f"{i}. <b>{game['name']}</b>\n   {desc}\n   {score_str}")

    # Разбиваем на чанки, не превышая MAX_TG_MSG
    chunks: list[str] = []
    current_lines: list[str] = []
    current_len = 0

    for block in blocks:
        # +1 за \n\n между блоками
        needed = len(block) + (2 if current_lines else 0)
        if current_lines and current_len + needed > MAX_TG_MSG:
            chunks.append("\n\n".join(current_lines))
            current_lines = []
            current_len = 0
        current_lines.append(block)
        current_len += needed

    if current_lines:
        chunks.append("\n\n".join(current_lines))

    # Добавляем заголовок с номером страницы, если чанков больше одного
    n = len(chunks)
    header_base = f"📋 Игры с описаниями ({{}}/{n}):\n\n"
    footer = f"\n\nВсего игр: {total}"

    if n == 1:
        return [f"📋 Игры с описаниями:\n\n{chunks[0]}{footer}"]

    result = []
    for idx, chunk in enumerate(chunks, 1):
        header = header_base.format(idx)
        page_footer = footer if idx == n else ""
        result.append(f"{header}{chunk}{page_footer}")
    return result


def format_game_select_results(poll_row: Any, votes: list, options_map: dict) -> str:
    # Count votes per option
    vote_counts: dict[str, list[str]] = {}
    for vote in votes:
        option_ids = json.loads(vote["option_ids"])
        name = vote["full_name"] or vote["username"] or f"id:{vote['user_id']}"
        for oid in option_ids:
            key = str(oid)
            vote_counts.setdefault(key, []).append(name)

    # Sort by vote count descending
    sorted_options = sorted(
        options_map.items(),
        key=lambda kv: len(vote_counts.get(kv[0], [])),
        reverse=True,
    )

    lines = ["🏆 Результаты голосования за игру:\n"]
    winner = None
    for i, (oid, game_name) in enumerate(sorted_options, 1):
        voters = vote_counts.get(oid, [])
        count = len(voters)
        if count == 0 and i > 1:
            continue
        lines.append(f"{i}. {game_name} — {count} {_vote_word(count)}")
        if voters:
            lines.append(f"   👤 {', '.join(voters)}")
        if winner is None and count > 0:
            winner = game_name

    if winner:
        lines.append(f"\nПобедитель: {winner}! 🎉")
    else:
        lines.append("\nНикто не проголосовал.")

    return "\n".join(lines)


def format_rating_results(game_name: str, votes: list, options_map: dict) -> str:
    lines = [f"⭐ Рейтинг игры «{game_name}»:\n"]

    scores = []
    for vote in votes:
        option_ids = json.loads(vote["option_ids"])
        if not option_ids:
            continue
        oid = str(option_ids[0])
        score = int(options_map.get(oid, 0))
        name = vote["full_name"] or vote["username"] or f"id:{vote['user_id']}"
        scores.append((name, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    for name, score in scores:
        lines.append(f"{name} — {score}")

    if scores:
        avg = sum(s for _, s in scores) / len(scores)
        count = len(scores)
        lines.append(f"\nСредняя оценка: {avg:.1f}/10 ({count} {_rating_word(count)})")
    else:
        lines.append("\nНикто не проголосовал.")

    return "\n".join(lines)


def format_day_results(votes: list, options_map: dict) -> str:
    vote_counts: dict[str, list[str]] = {}
    for vote in votes:
        option_ids = json.loads(vote["option_ids"])
        name = vote["full_name"] or vote["username"] or f"id:{vote['user_id']}"
        for oid in option_ids:
            key = str(oid)
            vote_counts.setdefault(key, []).append(name)

    sorted_options = sorted(
        options_map.items(),
        key=lambda kv: len(vote_counts.get(kv[0], [])),
        reverse=True,
    )

    lines = ["📅 Результаты голосования за дату:\n"]
    winner = None
    for oid, date_label in sorted_options:
        voters = vote_counts.get(oid, [])
        count = len(voters)
        lines.append(f"{date_label} — {count} {_vote_word(count)}")
        if voters:
            lines.append(f"   👤 {', '.join(voters)}")
        if winner is None and count > 0:
            winner = date_label

    if winner:
        lines.append(f"\nПобедитель: {winner}! 🎉")
    else:
        lines.append("\nНикто не проголосовал.")

    return "\n".join(lines)


def _vote_word(n: int) -> str:
    if 11 <= n % 100 <= 19:
        return "голосов"
    r = n % 10
    if r == 1:
        return "голос"
    if 2 <= r <= 4:
        return "голоса"
    return "голосов"


def _rating_word(n: int) -> str:
    if 11 <= n % 100 <= 19:
        return "оценок"
    r = n % 10
    if r == 1:
        return "оценка"
    if 2 <= r <= 4:
        return "оценки"
    return "оценок"
