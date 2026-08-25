#!/usr/bin/env python3
"""Validate ProofStamp v1 artifacts against the bundled JSON Schemas using only Python stdlib."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
SESSION_SCHEMA = SKILL_ROOT / "schemas" / "proofstamp-session-v1.schema.json"
RECEIPT_SCHEMA = SKILL_ROOT / "schemas" / "proofstamp-receipt-v1.schema.json"


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path.name} is not valid UTF-8 JSON: {exc}") from exc


def resolve_ref(root: dict, ref: str) -> dict:
    if not ref.startswith("#/"):
        raise ValueError(f"unsupported non-local $ref: {ref}")
    node: object = root
    for raw_part in ref[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            raise ValueError(f"invalid schema $ref: {ref}")
        node = node[part]
    if not isinstance(node, dict):
        raise ValueError(f"schema $ref does not resolve to an object: {ref}")
    return node


def json_equal(left: object, right: object) -> bool:
    """Compare JSON values without conflating booleans with numbers."""
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if left is None or right is None:
        return left is None and right is None
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(
            json_equal(a, b) for a, b in zip(left, right)
        )
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            json_equal(left[key], right[key]) for key in left
        )
    return left == right


def type_matches(value: object, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ValueError(f"unsupported schema type: {expected}")


def validate_format(value: str, fmt: str) -> bool:
    if fmt == "uri":
        parsed = urlparse(value)
        return bool(parsed.scheme)
    if fmt == "date-time":
        candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            parsed = datetime.fromisoformat(candidate)
            return "T" in value and parsed.tzinfo is not None
        except ValueError:
            return False
    raise ValueError(f"unsupported schema format: {fmt}")


def validate_node(value: object, schema: dict, root: dict, path: str = "$") -> list[str]:
    if "$ref" in schema:
        return validate_node(value, resolve_ref(root, schema["$ref"]), root, path)

    errors: list[str] = []

    if "oneOf" in schema:
        matches = 0
        for candidate in schema["oneOf"]:
            errs = validate_node(value, candidate, root, path)
            if not errs:
                matches += 1
        if matches != 1:
            errors.append(f"{path}: must match exactly one oneOf branch (matched {matches})")
        return errors

    if "const" in schema and not json_equal(value, schema["const"]):
        errors.append(f"{path}: must equal {schema['const']!r}")
        return errors

    if "enum" in schema and not any(json_equal(value, item) for item in schema["enum"]):
        errors.append(f"{path}: value {value!r} is not in the allowed enum")
        return errors

    expected = schema.get("type")
    if expected is not None:
        expected_types = expected if isinstance(expected, list) else [expected]
        if not any(type_matches(value, item) for item in expected_types):
            errors.append(f"{path}: expected type {expected!r}, got {type(value).__name__}")
            return errors

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required property {key!r}")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}: unexpected property {key!r}")

        for key, child_schema in properties.items():
            if key in value:
                errors.extend(validate_node(value[key], child_schema, root, f"{path}.{key}"))

    if isinstance(value, list):
        min_items = schema.get("minItems")
        if min_items is not None and len(value) < min_items:
            errors.append(f"{path}: must contain at least {min_items} item(s)")

        if schema.get("uniqueItems"):
            for index, item in enumerate(value):
                if any(json_equal(item, earlier) for earlier in value[:index]):
                    errors.append(f"{path}[{index}]: duplicate item is not allowed")

        item_schema = schema.get("items")
        if item_schema is not None:
            for index, item in enumerate(value):
                errors.extend(validate_node(item, item_schema, root, f"{path}[{index}]"))

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if min_length is not None and len(value) < min_length:
            errors.append(f"{path}: string must contain at least {min_length} character(s)")
        pattern = schema.get("pattern")
        if pattern is not None and re.search(pattern, value) is None:
            errors.append(f"{path}: string does not match required pattern {pattern!r}")
        fmt = schema.get("format")
        if fmt is not None and not validate_format(value, fmt):
            errors.append(f"{path}: value is not a valid {fmt}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        if minimum is not None and value < minimum:
            errors.append(f"{path}: value must be >= {minimum}")

    return errors


def validate_file(path: Path, schema_path: Path) -> list[str]:
    value = load_json(path)
    schema = load_json(schema_path)
    if not isinstance(schema, dict):
        raise ValueError(f"schema root must be an object: {schema_path}")
    return validate_node(value, schema, schema)


def detect_schema(path: Path) -> Path:
    value = load_json(path)
    if not isinstance(value, dict):
        raise ValueError("ProofStamp root must be a JSON object")
    meta = value.get("proofstamp")
    if not isinstance(meta, dict):
        raise ValueError("ProofStamp metadata is missing")
    fmt = meta.get("format")
    if fmt == "proofstamp-session":
        return SESSION_SCHEMA
    if fmt == "proofstamp-receipt":
        return RECEIPT_SCHEMA
    raise ValueError(f"unsupported ProofStamp format: {fmt!r}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="ProofStamp JSON file(s) to validate")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    failed = False
    for path in args.files:
        try:
            if not path.is_file():
                raise ValueError(f"file does not exist: {path}")
            schema_path = detect_schema(path)
            errors = validate_file(path, schema_path)
        except (ValueError, OSError) as exc:
            print(f"{path}: validation error: {exc}", file=sys.stderr)
            failed = True
            continue

        if errors:
            print(f"{path}: schema validation failed", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            failed = True
        else:
            print(f"{path}: schema validation passed")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
