#!/usr/bin/env python3
"""
test_integration.py —— 端到端集成测试

验证:
  1) SKILL.md 结构校验通过
  2) 触发评测达标
  3) 目录结构完整
  4) 打包可生成合法 .skill (zip)
"""
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = ROOT / "SKILL.md"
VALIDATE = ROOT / "scripts" / "validate_skill.py"
TRIGGER = ROOT / "tests" / "test_trigger.py"


def run(cmd, cwd=None):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or ROOT)


def main() -> int:
    failures = []

    # 1) 结构校验
    r = run([sys.executable, str(VALIDATE), str(SKILL_MD), "--json"])
    if r.returncode != 0:
        failures.append(f"结构校验失败:\n{r.stdout}\n{r.stderr}")

    # 2) 触发评测
    r = run([sys.executable, str(TRIGGER), str(SKILL_MD), "--json"])
    if r.returncode != 0:
        failures.append(f"触发评测未达标:\n{r.stdout}")

    # 3) 目录完整性
    for must in ["references/platforms.md", "scripts/requirements.txt", "tests", "README.md", ".gitignore"]:
        if not (ROOT / must).exists():
            failures.append(f"缺少必需文件/目录: {must}")

    # 4) 打包测试（生成 zip 并校验顶层为 <name>/SKILL.md）
    import yaml
    fm = yaml.safe_load(SKILL_MD.read_text().split("---")[1])
    name = fm["name"]
    zip_path = ROOT.parent / f"{name}.skill"
    try:
        r = run(["zip", "-r", str(zip_path), f"{name}/",
                 "-x", "*/__pycache__/*", "*/.env", "*/.git/*"],
                cwd=ROOT.parent)
        if r.returncode != 0:
            failures.append(f"打包失败:\n{r.stderr}")
        else:
            with zipfile.ZipFile(zip_path) as z:
                names = z.namelist()
                if not any(n.startswith(f"{name}/SKILL.md") for n in names):
                    failures.append("zip 顶层结构错误，应为 <skill-name>/SKILL.md")
    finally:
        if zip_path.exists():
            zip_path.unlink()

    if failures:
        print("INTEGRATION TEST FAILED:", file=sys.stderr)
        for f in failures:
            print("- " + f, file=sys.stderr)
        return 1

    print("✅ 集成测试全部通过", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
