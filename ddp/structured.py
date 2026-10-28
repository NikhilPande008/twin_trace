"""
Structured output: schemas, request formats, and a local validator.

Why this module exists
----------------------
1. `response_format={"type": "json_object"}` forces a JSON *object*. The prompts in the
   baseline asked for a bare JSON *array*, which a constrained decoder cannot emit, so the
   first live run would have failed or the parser would have grabbed a nested array.
   Every structured call now asks for an object wrapper: {"factors": [...]}, {"items": [...]}.
2. Server-side schema enforcement is not trusted blindly: reasoning models can emit text
   outside the constrained channel (see vLLM #44012). So every response is ALSO validated
   locally against the same schema, with one repair retry, and the caller fails closed.

Mode is configurable: STRUCTURED_OUTPUT_MODE = json_object (default) | json_schema.
json_schema falls back to json_object automatically if the endpoint rejects it (HTTP 400).
"""

from __future__ import annotations

import json
from typing import Any

POE_IDS = [f"POE-{n:03d}" for n in range(2, 13)]

SCHEMAS: dict[str, dict] = {
    "poe_assessment": {
        "type": "object",
        "required": ["factors"],
        "properties": {
            "factors": {
                "type": "array", "minItems": 11, "maxItems": 11,
                "items": {
                    "type": "object",
                    "required": ["factor_id", "factor_name", "assessment", "evidence",
                                 "evidence_txn_ids", "rules_cited"],
                    "properties": {
                        "factor_id": {"type": "string", "enum": POE_IDS},
                        "factor_name": {"type": "string"},
                        "assessment": {"type": "string",
                                       "enum": ["triggered", "clear", "insufficient_data"]},
                        "evidence": {"type": "string"},
                        "evidence_txn_ids": {"type": "array", "items": {"type": "string"}},
                        "rules_cited": {"type": "array", "items": {"type": "string"}},
                    },
                },
            }
        },
    },
    "quality_check": {
        "type": "object",
        "required": ["items"],
        "properties": {
            "items": {
                "type": "array", "minItems": 10, "maxItems": 10,
                "items": {
                    "type": "object",
                    "required": ["item_number", "applies", "note"],
                    "properties": {
                        "item_number": {"type": "integer", "minimum": 1, "maximum": 10},
                        "item": {"type": "string"},
                        "applies": {"type": "boolean"},
                        "note": {"type": "string"},
                    },
                },
            }
        },
    },
    "stress_memo": {
        "type": "object",
        "required": ["summary", "load_bearing_evidence", "reopen_triggers"],
        "properties": {
            "summary": {"type": "string"},
            "load_bearing_evidence": {"type": "array", "items": {"type": "string"}},
            "reopen_triggers": {"type": "array", "items": {"type": "string"}},
        },
    },
}

WRAPPER_KEY = {"poe_assessment": "factors", "quality_check": "items"}


def response_format(name: str, mode: str) -> dict:
    if mode == "json_schema":
        return {"type": "json_schema",
                "json_schema": {"name": name, "schema": SCHEMAS[name], "strict": True}}
    return {"type": "json_object"}


class SchemaError(ValueError):
    pass


def _check(value: Any, schema: dict, path: str) -> None:
    t = schema.get("type")
    if t == "object":
        if not isinstance(value, dict):
            raise SchemaError(f"{path}: expected object")
        for k in schema.get("required", []):
            if k not in value:
                raise SchemaError(f"{path}: missing '{k}'")
        for k, sub in schema.get("properties", {}).items():
            if k in value:
                _check(value[k], sub, f"{path}.{k}")
    elif t == "array":
        if not isinstance(value, list):
            raise SchemaError(f"{path}: expected array")
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise SchemaError(f"{path}: {len(value)} items < {schema['minItems']}")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise SchemaError(f"{path}: {len(value)} items > {schema['maxItems']}")
        for i, v in enumerate(value):
            _check(v, schema.get("items", {}), f"{path}[{i}]")
    elif t == "string":
        if not isinstance(value, str):
            raise SchemaError(f"{path}: expected string")
        if "enum" in schema and value not in schema["enum"]:
            raise SchemaError(f"{path}: {value!r} not in {schema['enum']}")
    elif t == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            raise SchemaError(f"{path}: expected integer")
        if value < schema.get("minimum", value) or value > schema.get("maximum", value):
            raise SchemaError(f"{path}: {value} out of range")
    elif t == "boolean":
        if not isinstance(value, bool):
            raise SchemaError(f"{path}: expected boolean")


def _extract_json(raw: str) -> Any:
    text = (raw or "").strip()
    if "```" in text:
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]
            if text.startswith("json"):
                text = text[4:]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # tolerate prose around a single JSON value: try the outermost object, then array
    for open_c, close_c in (("{", "}"), ("[", "]")):
        i, j = text.find(open_c), text.rfind(close_c)
        if i != -1 and j > i:
            try:
                return json.loads(text[i:j + 1])
            except json.JSONDecodeError:
                continue
    raise SchemaError("response is not valid JSON")


def parse_and_validate(raw: str, name: str) -> Any:
    """Parse model text and validate against SCHEMAS[name].

    A bare array is accepted for wrapped schemas (older prompts / test fixtures) and wrapped
    before validation. Returns the validated object.
    """
    obj = _extract_json(raw)
    key = WRAPPER_KEY.get(name)
    if key and isinstance(obj, list):
        obj = {key: obj}
    _check(obj, SCHEMAS[name], "$")
    _check_semantics(obj, name)
    return obj


def _check_semantics(obj: Any, name: str) -> None:
    """What JSON Schema cannot say here: each factor / checklist item exactly once."""
    if name == "poe_assessment":
        ids = [f["factor_id"] for f in obj["factors"]]
        dup = sorted({i for i in ids if ids.count(i) > 1})
        missing = sorted(set(POE_IDS) - set(ids))
        if dup or missing:
            raise SchemaError(f"$.factors: each POE factor exactly once "
                              f"(duplicated {dup}, missing {missing})")
    if name == "quality_check":
        nums = [i.get("item_number") for i in obj["items"]]
        if sorted(nums) != list(range(1, 11)):
            raise SchemaError("$.items: item_number must be 1..10, each exactly once")
