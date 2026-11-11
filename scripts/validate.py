"""Validate a public synthetic collaboration plan; never perform external actions."""
import json
import sys
from pathlib import Path


def validate(data):
    errors = []
    if not isinstance(data, dict):
        return ["plan must be an object"]
    if not text(data.get("title")):
        errors.append("title is required")
    elif len(data.get("title")) > 200:
        errors.append("title must not exceed 200 characters")
    if data.get("data_classification") != "synthetic":
        errors.append("public examples must be synthetic; private records stay outside this repo")
    expected_kind = 'event-space'
    if data.get("kind") != expected_kind:
        errors.append("kind must be " + expected_kind)
    check(data, errors)
    return errors


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def records(data, key, errors):
    value = data.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, dict) for item in value):
        errors.append(key + " must contain at least one object")
        return []
    return value


def unique_ids(items, label, errors):
    identifiers = [item.get("id") for item in items]
    if any(not isinstance(value, str) or not value.strip() for value in identifiers):
        errors.append(label + " ids must be nonempty strings")
        return set()
    if len(set(identifiers)) != len(identifiers):
        errors.append(label + " ids must be unique")
    return set(identifiers)


def text(value):
    if not isinstance(value, str) or not value.strip():
        return False
    if "<" in value or ">" in value:
        return False
    return True


def check(data, errors):
    count, capacity = data.get("expected_attendees"), data.get("venue_capacity")
    if not number(count) or not number(capacity) or count <= 0 or capacity <= 0 or int(count) != count or int(capacity) != capacity:
        errors.append("attendance and capacity must be positive integers")
    elif count > 10000 or capacity > 10000:
        errors.append("attendance and capacity must not exceed 10000")
    elif count > capacity:
        errors.append("attendance exceeds the stated venue capacity")
    roles = data.get("roles", [])
    if not isinstance(roles, list) or not all(text(role) for role in roles):
        errors.append("roles must be a list of nonempty names")
        roles = []
    elif any(len(role) > 200 for role in roles):
        errors.append("role names must not exceed 200 characters")
    end = 0
    for item in records(data, "agenda", errors):
        start, duration = item.get("start_minute"), item.get("duration_minutes")
        if not number(start) or not number(duration) or start < 0 or duration <= 0:
            errors.append("agenda timing must be nonnegative with a positive duration")
            continue
        if start > 10000 or duration > 10000:
            errors.append("agenda timing must not exceed 10000 minutes")
        if start < end:
            errors.append("agenda entries overlap or are out of order")
        end = start + duration
        if item.get("owner_role") not in roles:
            errors.append("each agenda item needs a listed owner role")
        if not text(item.get("title")):
            errors.append("agenda title is required")
        elif len(item.get("title")) > 200:
            errors.append("agenda title must not exceed 200 characters")



if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 scripts/validate.py <plan.json>")
    try:
        path = Path(sys.argv[1])
        if path.stat().st_size > 1024 * 1024:
            raise SystemExit("file size exceeds 1MB limit")
        problems = validate(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(str(error))
    if problems:
        print("\n".join(problems), file=sys.stderr)
        raise SystemExit(1)
    print("PASS: structural checks only; no real-world activity or results verified")
