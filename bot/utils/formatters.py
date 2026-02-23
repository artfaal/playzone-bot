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
