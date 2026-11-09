"""Validate a public synthetic collaboration plan; never perform external actions."""
import json
import sys
from pathlib import Path


def validate(data):
    errors = []
    if type(data) is not dict:
        return ["plan must be an object"]

    title = data.get("title")
    if type(title) is not str or not title.strip():
        errors.append("title is required")

    if data.get("data_classification") != "synthetic":
        errors.append("public examples must be synthetic; private records stay outside this repo")

    expected_kind = 'event-space'
    if data.get("kind") != expected_kind:
        errors.append("kind must be " + expected_kind)

    count = data.get("expected_attendees")
    capacity = data.get("venue_capacity")
    if type(count) not in (int, float) or type(capacity) not in (int, float) or count <= 0 or capacity <= 0 or int(count) != count or int(capacity) != capacity:
        errors.append("attendance and capacity must be positive integers")
    elif count > capacity:
        errors.append("attendance exceeds the stated venue capacity")

    roles = data.get("roles", [])
    if type(roles) is not list or not all(type(role) is str and role.strip() for role in roles):
        errors.append("roles must be a list of nonempty names")
        roles = []

    end = 0
    agenda = data.get("agenda")
    if type(agenda) is not list or not agenda or not all(type(item) is dict for item in agenda):
        errors.append("agenda must contain at least one object")
        agenda = []

    roles_set = set(roles)
    for item in agenda:
        start = item.get("start_minute")
        duration = item.get("duration_minutes")
        if type(start) not in (int, float) or type(duration) not in (int, float) or start < 0 or duration <= 0:
            errors.append("agenda timing must be nonnegative with a positive duration")
            continue
        if start < end:
            errors.append("agenda entries overlap or are out of order")
        end = start + duration

        owner_role = item.get("owner_role")
        if owner_role not in roles_set:
            errors.append("each agenda item needs a listed owner role")

        item_title = item.get("title")
        if type(item_title) is not str or not item_title.strip():
            errors.append("agenda title is required")

    return errors


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 scripts/validate.py <plan.json>")
    try:
        problems = validate(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(str(error))
    if problems:
        print("\n".join(problems), file=sys.stderr)
        raise SystemExit(1)
    print("PASS: structural checks only; no real-world activity or results verified")
