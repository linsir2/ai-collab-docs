#!/usr/bin/env python3
"""
gen_ts_types.py — 从 contracts.py 自动生成 TypeScript 类型定义
==============================================================
单一真相源: contracts/contracts.py → frontend/src/shared/types/contracts.ts
用法: python gen_ts_types.py contracts/contracts.py ../frontend/src/shared/types/contracts.ts
"""

import ast
import json
import sys
from pathlib import Path

# ─── Python → TypeScript 类型映射 ───
PY_TO_TS = {
    "str": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "dict": "Record<string, unknown>",
    "list": "unknown[]",
    "Any": "unknown",
    "None": "void",
}

# 已知泛型容器
GENERIC_MAP = {
    "Optional": lambda t: f"{t} | null",
    "list": lambda t: f"{t}[]",
    "dict": lambda _, v: f"Record<string, {v}>",
}


def resolve_ts_type(annotation: ast.expr) -> str:
    """将 Python AST 类型注解递归转为 TypeScript 类型字符串"""
    if isinstance(annotation, ast.Name):
        name = annotation.id
        return PY_TO_TS.get(name, name)

    if isinstance(annotation, ast.Constant) and annotation.value is None:
        return "null"

    if isinstance(annotation, ast.Subscript):
        # e.g., Optional[str], list[int], dict[str, Any]
        base = annotation.value
        base_name = base.id if isinstance(base, ast.Name) else ""
        slice_node = annotation.slice

        # Extract type args
        if isinstance(slice_node, ast.Tuple):
            args = [resolve_ts_type(el) for el in slice_node.elts]
        else:
            args = [resolve_ts_type(slice_node)]

        if base_name in GENERIC_MAP:
            return GENERIC_MAP[base_name](*args)
        if base_name == "Optional":
            return f"{args[0]} | null"
        # Unknown generic
        return f"{base_name}<{', '.join(args)}>"

    if isinstance(annotation, ast.Attribute):
        return annotation.attr

    return "unknown"


def extract_enum(node: ast.ClassDef) -> tuple[str, list[str]]:
    """提取 StrEnum/Enum 定义"""
    members = []
    for stmt in node.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id not in ("__doc__",):
                    val = getattr(stmt.value, "value", str(stmt.value))
                    members.append(f"  {target.id} = {json.dumps(val) if isinstance(val, str) else repr(val)},")
    return node.name, members


def extract_dataclass(node: ast.ClassDef) -> tuple[str, list[dict]]:
    """提取 frozen dataclass 字段"""
    fields = []
    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and stmt.annotation:
            fname = stmt.target.id if isinstance(stmt.target, ast.Name) else "?"
            ts_type = resolve_ts_type(stmt.annotation)
            # 检测是否有默认值(Optional)
            has_default = stmt.value is not None or (
                hasattr(stmt, "value") and getattr(stmt, "value", None) is not None
            )
            # 简单启发: 如果有注释且含"可选",标记为optional
            is_optional = has_default
            fields.append({"name": fname, "type": ts_type, "optional": is_optional})
    return node.name, fields


def dedent(s: str) -> str:
    return s.strip()


def comment_line(node: ast.AST, contract_path: str) -> str:
    """提取行尾注释"""
    end_line = getattr(node, "end_lineno", None)
    if end_line:
        try:
            with open(contract_path) as f:
                lines = f.readlines()
            line = lines[end_line - 1]
            comment = line.split("#", 1)
            if len(comment) > 1:
                return comment[1].strip()
        except (FileNotFoundError, IndexError):
            pass
    return ""


def generate(source: str) -> str:
    """主生成函数"""
    tree = ast.parse(Path(source).read_text())
    output = []
    output.append("// ⚠️ AUTO-GENERATED from contracts/contracts.py")
    output.append("// 单一真相源 — 请勿手动编辑此文件")
    output.append("// 运行: make types")
    output.append("")

    for node in ast.iter_child_nodes(tree):
        # 跳过 import / from / docstring
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue  # docstring

        if isinstance(node, ast.ClassDef):
            # 判断是 Enum 还是 Dataclass
            is_enum = any(
                isinstance(b, ast.Name) and ("Enum" in b.id or "StrEnum" in b.id)
                for b in node.bases
            )
            is_dataclass = any(
                isinstance(d, ast.Call)
                and hasattr(d.func, "id")
                and d.func.id == "dataclass"
                for d in node.decorator_list
            )

            if is_enum:
                name, members = extract_enum(node)
                output.append(f"export enum {name} {{")
                output.extend(members)
                output.append("}")
                output.append("")

            elif is_dataclass:
                name, fields = extract_dataclass(node)
                output.append(f"export interface {name} {{")
                for f in fields:
                    opt = "?" if f["optional"] else ""
                    output.append(f"  {f['name']}{opt}: {f['type']};")
                output.append("}")
                output.append("")

    return "\n".join(output)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python gen_ts_types.py <contracts.py> <output.ts>")
        sys.exit(1)

    src = sys.argv[1]
    dst = sys.argv[2]
    ts_code = generate(src)
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_text(ts_code)
    print(f"✅ Generated {dst} ({len(ts_code)} chars)")
