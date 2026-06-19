"""
gen_contracts.py — 从 designs/openapi.yml 生成 contracts/ 下的 Python 类型
=============================================================================
单一真相源: designs/openapi.yml
输出: contracts/_auto_enums.py + contracts/_auto_models.py
用法: python contracts/gen_contracts.py           # 重建两个AUTO文件
      python contracts/gen_contracts.py --check   # 仅检查差异
"""
import yaml
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OPENAPI_PATH = PROJECT_ROOT / "designs" / "openapi.yml"
ENUMS_PATH = PROJECT_ROOT / "contracts" / "_auto_enums.py"
MODELS_PATH = PROJECT_ROOT / "contracts" / "_auto_models.py"

AUTO_HEADER = '"""\nAUTO-GENERATED from designs/openapi.yml\nDO NOT EDIT MANUALLY.\nRun: python contracts/gen_contracts.py\n"""\n'


def openapi_type(prop: dict, schemas: dict) -> str:
    """Map OpenAPI schema property to Python type annotation."""
    if "$ref" in prop:
        return prop["$ref"].split("/")[-1]
    t = prop.get("type", "Any")
    if t == "string":
        return "str"
    elif t == "integer":
        return "int"
    elif t == "number":
        return "float"
    elif t == "boolean":
        return "bool"
    elif t == "array":
        items = prop.get("items", {})
        if "$ref" in items:
            inner = items["$ref"].split("/")[-1]
        elif items.get("type") == "string":
            inner = "str"
        else:
            inner = "Any"
        return f"list[{inner}]"
    elif t == "object":
        return "Any"
    return "Any"


def generate_enums(schemas: dict) -> str:
    """Generate all StrEnum classes."""
    enums = {}
    for name, s in schemas.items():
        if s.get("type") == "string" and "enum" in s:
            enums[name] = s

    lines = [AUTO_HEADER + "from enum import StrEnum\n\n"]
    for name in sorted(enums):
        s = enums[name]
        desc = s.get("description", name)
        if desc:
            lines.append(f'# {desc}')
        lines.append(f"class {name}(StrEnum):")
        for val in s["enum"]:
            key = val.upper().replace("-", "_").replace(".", "_")
            lines.append(f'    {key} = "{val}"')
        lines.append("")
    return "\n".join(lines)


def generate_models(schemas: dict) -> str:
    """Generate all frozen dataclass models with correct field ordering."""
    objects = {}
    for name, s in schemas.items():
        if s.get("type") == "object" and "properties" in s:
            objects[name] = s

    lines = [AUTO_HEADER]
    lines.append("from dataclasses import dataclass, field")
    lines.append("from typing import Optional, Any")
    lines.append("from uuid import uuid4")
    lines.append("")
    lines.append("from contracts._auto_enums import *  # noqa: F403")
    lines.append("")

    # Topological sort: schemas referencing others come after their deps
    resolved = set()
    pending = set(objects.keys())
    order = []

    def refs_of(model_name):
        s = objects[model_name]
        refs = set()
        for _pn, pv in s.get("properties", {}).items():
            if "$ref" in pv:
                rn = pv["$ref"].split("/")[-1]
                if rn in objects: refs.add(rn)
            elif pv.get("type") == "array" and "$ref" in pv.get("items", {}):
                rn = pv["items"]["$ref"].split("/")[-1]
                if rn in objects: refs.add(rn)
        return refs - {model_name}

    while pending:
        added = False
        for n in sorted(pending):
            if refs_of(n) <= resolved:
                order.append(n)
                pending.discard(n)
                added = True
                break
        if not added:
            order.extend(sorted(pending))
            break

    for name in order:
        s = objects[name]
        resolved.add(name)

    for name in order:
        s = objects[name]
        required = set(s.get("required", []))
        desc = s.get("description", name)

        lines.append("\n@dataclass(frozen=True)")
        lines.append(f"class {name}:")
        if desc and desc != name:
            lines.append(f'    """{desc}"""')

        props = s.get("properties", {})
        if not props:
            lines.append("    pass")
            continue

        # Sort fields: required-no-default > required-with-uuid-default > optional
        def sort_key(item):
            pn, pp = item
            pt = openapi_type(pp, schemas)
            is_uuid = pt == "str" and pp.get("format") == "uuid"
            if pn in required:
                return (0, 0) if not is_uuid else (0, 1)
            return (1, 0)

        for prop_name, prop in sorted(props.items(), key=sort_key):
            py_type = openapi_type(prop, schemas)
            if prop_name in required:
                if py_type == "str" and prop.get("format") == "uuid":
                    lines.append(f'    {prop_name}: str = field(default_factory=lambda: str(uuid4()))')
                else:
                    lines.append(f"    {prop_name}: {py_type}")
            else:
                default_val = prop.get("default")
                if default_val is not None:
                    if isinstance(default_val, str):
                        lines.append(f'    {prop_name}: Optional[{py_type}] = "{default_val}"')
                    else:
                        lines.append(f"    {prop_name}: Optional[{py_type}] = {default_val}")
                elif py_type == "str" and prop.get("format") == "uuid":
                    lines.append(f'    {prop_name}: Optional[str] = field(default_factory=lambda: str(uuid4()))')
                elif py_type in ("int", "float"):
                    lines.append(f"    {prop_name}: Optional[{py_type}] = 0")
                elif py_type == "bool":
                    lines.append(f"    {prop_name}: Optional[{py_type}] = False")
                else:
                    lines.append(f"    {prop_name}: Optional[{py_type}] = None")

    return "\n".join(lines)


def rebuild(dry_run: bool = False):
    with open(OPENAPI_PATH, encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    schemas = spec.get("components", {}).get("schemas", {})
    enum_code = generate_enums(schemas)
    model_code = generate_models(schemas)

    if dry_run:
        ok = True
        for path, code in [(ENUMS_PATH, enum_code), (MODELS_PATH, model_code)]:
            if path.exists():
                old = path.read_text(encoding="utf-8")
                if old.strip() == code.strip():
                    print(f"✅ {path.name} is up-to-date")
                else:
                    print(f"❌ {path.name} OUT OF SYNC")
                    ok = False
            else:
                print(f"❌ {path.name} does not exist")
                ok = False
        if ok:
            print("✅ All AUTO files up-to-date with openapi.yml")
        else:
            print("❌ Run: python contracts/gen_contracts.py")
        return

    ENUMS_PATH.write_text(enum_code, encoding="utf-8")
    print(f"✅ {ENUMS_PATH.name} ({len(enum_code)} chars)")
    MODELS_PATH.write_text(model_code, encoding="utf-8")
    print(f"✅ {MODELS_PATH.name} ({len(model_code)} chars)")


if __name__ == "__main__":
    rebuild(dry_run="--check" in sys.argv)
