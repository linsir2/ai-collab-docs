#!/usr/bin/env python3
"""
gen_ts_types.py — 从 designs/openapi.yml 自动生成 TypeScript 类型定义
========================================================================
单一真相源: designs/openapi.yml
用法: python contracts/gen_ts_types.py [--check]
输出: services/web/src/contracts.ts
"""
import yaml
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OPENAPI_PATH = PROJECT_ROOT / "designs" / "openapi.yml"
OUTPUT_PATH = PROJECT_ROOT / "services" / "web" / "src" / "contracts.ts"

TYPE_MAP = {"string": "string", "integer": "number", "number": "number", "boolean": "boolean"}
HEADER = """\
// AUTO-GENERATED from designs/openapi.yml
// DO NOT EDIT MANUALLY.
// Run: python contracts/gen_ts_types.py
// Source: designs/openapi.yml

"""


def load_openapi():
    with open(OPENAPI_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_ts_type(schema, schemas):
    """OpenAPI schema → TypeScript type string."""
    if not isinstance(schema, dict):
        return "any"
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    s_type = schema.get("type", "object")
    if s_type == "string" and "enum" in schema:
        return schema.get("title", "string")
    if s_type == "array":
        items = schema.get("items", {})
        return f"Array<{resolve_ts_type(items, schemas)}>"
    if s_type == "object" and "properties" not in schema:
        return "Record<string, any>"
    return TYPE_MAP.get(s_type, "any")


def generate_ts_enum(name, schema):
    """Generate TypeScript enum from OpenAPI schema."""
    desc = schema.get("description", "")
    members = schema.get("enum", [])
    lines = [f"// {desc}"]
    lines.append(f"export enum {name} {{")
    for m in members:
        key = m.upper().replace("-", "_").replace(":", "_").replace(" ", "_").replace(".", "_")
        lines.append(f'  {key} = "{m}",')
    lines.append("}")
    lines.append("")
    return lines


def generate_ts_interface(name, schema, schemas):
    """Generate TypeScript interface from OpenAPI object schema."""
    desc = schema.get("description", "")
    required = set(schema.get("required", []))
    properties = schema.get("properties", {})

    lines = [f"// {desc}"]
    lines.append(f"export interface {name} {{")
    for prop_name, prop_schema in properties.items():
        is_req = prop_name in required
        ts_type = resolve_ts_type(prop_schema, schemas)
        suffix = "" if is_req else "?"
        lines.append(f"  {prop_name}{suffix}: {ts_type};")
    lines.append("}")
    lines.append("")
    return lines


def scan_schemas(schemas):
    enums, objects = {}, {}
    for name, s in schemas.items():
        if not isinstance(s, dict):
            continue
        if s.get("type") == "string" and "enum" in s:
            enums[name] = s
        elif s.get("type") == "object":
            objects[name] = s
    return enums, objects


def generate():
    api = load_openapi()
    schemas = api.get("components", {}).get("schemas", {})
    enums, objects = scan_schemas(schemas)

    lines = [HEADER]
    lines.append("// ── Enums ──\n")
    for name in sorted(enums):
        lines.extend(generate_ts_enum(name, enums[name]))
    lines.append("// ── Interfaces ──\n")
    for name in sorted(objects):
        lines.extend(generate_ts_interface(name, objects[name], schemas))
    return "\n".join(lines)


def main():
    ts_code = generate()
    dry_run = "--check" in sys.argv

    if dry_run:
        if OUTPUT_PATH.exists():
            existing = OUTPUT_PATH.read_text(encoding="utf-8")
            if existing == ts_code:
                print("✅ contracts.ts is up-to-date with openapi.yml")
            else:
                print("❌ contracts.ts OUT OF SYNC")
        else:
            print("❌ contracts.ts does not exist")
        return

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(ts_code, encoding="utf-8")
    print(f"✅ Generated {OUTPUT_PATH} ({len(ts_code)} chars)")


if __name__ == "__main__":
    main()
