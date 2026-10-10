#!/usr/bin/env python3
# /// pyproject
# [project]
# name = "validate-skill"
# version = "1.0.0"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
validate_skill.py —— Skill 结构校验器

用法:
    python validate_skill.py <path-to-SKILL.md> [--json]

退出码:
    0  校验通过
    1  校验失败（结构问题）
    2  参数/IO 错误

输出:
    stdout: JSON {"status": "success"|"error", "errors": [...], "warnings": [...]}
    stderr: 人类可读的进度/诊断信息
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pyyaml"], check=True)
    import yaml  # noqa: F811


REQUIRED_SECTIONS = [
    "何时激活",
    "输入输出规范",
    "执行步骤",
    "错误处理",
]

NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
DESC_MIN, DESC_MAX = 20, 1024


def assert_safe(path: str, root: str) -> Path:
    """路径白名单：禁止 ../ 穿越。"""
    resolved = (Path(root) / path).resolve()
    if not str(resolved).startswith(str(Path(root).resolve()) + os.sep):
        raise ValueError(f"路径越界: {path}")
    return resolved


def validate(skill_md: str) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    root = os.path.dirname(os.path.abspath(skill_md))

    text = Path(skill_md).read_text(encoding="utf-8")

    # 1) frontmatter 存在且可解析
    if not text.startswith("---"):
        errors.append("文件未以 '---' 开头，缺少 YAML frontmatter")
        return {"status": "error", "errors": errors, "warnings": warnings}

    parts = text.split("---", 2)
    if len(parts) < 3:
        errors.append("frontmatter 未正确以 '---' 结束")
        return {"status": "error", "errors": errors, "warnings": warnings}

    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as e:
        errors.append(f"frontmatter YAML 解析失败: {e}")
        return {"status": "error", "errors": errors, "warnings": warnings}

    # 2) name
    name = fm.get("name")
    if not name:
        errors.append("缺少必填字段: name")
    elif not isinstance(name, str) or not NAME_RE.fullmatch(name):
        errors.append(f"name 不合法: '{name}'，须为 kebab-case、≤64 字符")

    # 3) description
    desc = fm.get("description")
    if not desc:
        errors.append("缺少必填字段: description")
    elif isinstance(desc, str):
        if len(desc) < DESC_MIN:
            warnings.append(f"description 过短（{len(desc)} 字），建议 50–150 字")
        if len(desc) > DESC_MAX:
            errors.append(f"description 超过 {DESC_MAX} 字符上限")

    # 4) 必需章节存在（兼容 "## 二、输入输出规范" / "### 输入输出" / "## 三、工作流程" 等写法）
    #    只校验章节的"语义关键词"，不要求字面完全一致
    SECTION_KEYWORDS = ["触发", "输入输出", "步骤", "错误处理"]  # 对应 REQUIRED_SECTIONS 的语义
    norm_text = re.sub(r"[#* \t\r\n]", "", text)
    for kw in SECTION_KEYWORDS:
        if kw not in norm_text:
            errors.append(f"缺少必需章节（语义关键词未命中）: {kw}")

    # 5) 目录完整性（可选但推荐）
    for expected in ["scripts", "tests", "references"]:
        p = assert_safe(expected, root)
        if not p.exists():
            warnings.append(f"建议包含目录: {expected}/（当前缺失）")

    # 6) 脚本 --help 自检（若存在 main.py）
    main_py = assert_safe("scripts/main.py", root)
    if main_py.exists():
        import subprocess
        try:
            out = subprocess.run(
                [sys.executable, str(main_py), "--help"],
                capture_output=True, text=True, timeout=10,
            )
            if out.returncode != 0:
                warnings.append("scripts/main.py --help 执行失败")
        except FileNotFoundError:
            warnings.append("未找到 python 解释器，跳过 --help 检查")
        except subprocess.TimeoutExpired:
            warnings.append("scripts/main.py --help 超时")

    status = "success" if not errors else "error"
    return {"status": status, "errors": errors, "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="校验 Skill 的 SKILL.md 是否符合开放标准",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("skill_md", help="SKILL.md 的路径")
    parser.add_argument("--json", action="store_true", help="仅输出 JSON（默认也会输出人类可读摘要）")
    args = parser.parse_args()

    if not os.path.isfile(args.skill_md):
        print(json.dumps({"status": "error", "errors": [f"文件不存在: {args.skill_md}"], "warnings": []}))
        return 2

    result = validate(args.skill_md)

    if not args.json:
        print(f"[{'PASS' if result['status']=='success' else 'FAIL'}] {args.skill_md}", file=sys.stderr)
        for e in result["errors"]:
            print(f"  ✗ {e}", file=sys.stderr)
        for w in result["warnings"]:
            print(f"  ! {w}", file=sys.stderr)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
