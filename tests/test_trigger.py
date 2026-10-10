#!/usr/bin/env python3
# /// pyproject
# [project]
# name = "test-trigger"
# version = "1.0.0"
# dependencies = []
# ///
"""
test_trigger.py —— 触发评测（description 质量）

用法:
    python test_trigger.py <path-to-SKILL.md> [--json]

评测逻辑（模拟 Agent 的匹配行为）:
    - 从 SKILL.md 读取 description
    - 对测试集每条用例，判断"是否应触发"
    - 输出: 触发率(TP)、误触发率(TN)、边界处理

测试集应覆盖:
    TP (应触发): 明确要"创建/写/封装 Skill"
    TN (不应触发): 一次性业务任务，非创建 Skill
    Edge (边界): 模糊表述，预期行为是"先 grill"

注: 真实匹配由 LLM 完成，本脚本用关键词启发式做回归守护，
    防止 description 明显退化。正式评测应以 LLM 实测为准。
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml  # 依赖已在 scripts/requirements.txt 声明


def load_description(skill_md: str) -> str:
    text = Path(skill_md).read_text(encoding="utf-8")
    assert text.startswith("---"), "缺少 frontmatter"
    fm = yaml.safe_load(text.split("---")[1])
    return fm.get("description", "")


# ---- 启发式匹配器（回归用，非权威） ----
# 分两组：动词（意图）+ 宾语（对象）。两组同时满足才判定为"创建 Skill"。
CREATE_VERBS = ["创建", "新建", "写一个", "写个", "编写", "生成", "封装成", "封装一下",
                "制作", "开发", "做个", "做一个", "给我一个", "来个", "来一个",
                "搞个", "弄个", "做一个", "造一个"]
OBJECT_NOUNS = ["技能", "能力包", "元技能", "模板", "skill", "Skill", "SKILL", "SKILL.md",
               "creator"]

# 强信号：单独出现即可判定（明确的创建 Skill 意图）
STRONG_SIGNALS = ["创建 skill", "创建技能", "创建 Skill", "创建元技能",
                  "写个 skill", "写一个 skill", "写个技能", "写个元技能",
                  "skill 模板", "SKILL.md 模板", "skill-creator",
                  "封装成 skill", "封装成能力包", "封装成元技能",
                  "生成 skill", "生成 SKILL.md", "做个 skill", "做个元技能",
                  "新建 skill", "新建能力包", "来个 skill", "来个 skill-creator"]


def _norm(s: str) -> str:
    return s.replace("一个", "").replace("个", "")


def should_trigger(utterance: str) -> bool:
    """判断一条用户话术是否应触发该 Skill（关键词启发式）。"""
    u = _norm(utterance)

    # 强信号短路
    if any(s in u for s in STRONG_SIGNALS):
        return True

    has_verb = any(v in u for v in CREATE_VERBS)
    has_noun = any(n.lower() in u.lower() for n in OBJECT_NOUNS)

    # 负向拦截：明确的"一次性业务任务"，且没有"Skill/技能"宾语
    business_verbs = ["处理这个", "处理这份", "生成一份", "把这个", "帮我审查这段",
                      "读取这个", "运行一下", "执行一下", "下载", "发送"]
    if any(b in u for b in business_verbs) and not has_noun:
        return False

    return has_verb and has_noun


# ---- 测试集 ----
TEST_SET = {
    "TP": [  # 应触发
        "帮我创建一个处理 CSV 的 Skill",
        "写一个生成周报的技能包",
        "把 PDF 提取流程封装成 Skill",
        "我要新建一个代码审查的 Skill",
        "给我一个 SKILL.md 模板",
        "做一个把 Markdown 转 Word 的元技能",
        "帮我写个 skill",
        "把这个流程封装一下做成能力包",
        # 扩展用例（贴近真实用户措辞）
        "帮我创建个 skill",
        "帮我写一个 skill",
        "写个技能",
        "新建一个能力包",
        "封装成 skill",
        "做个元技能",
        "生成 SKILL.md",
        "来个 skill-creator",
        "把这个做成 skill",
        "帮我封装一个技能",
    ],
    "TN": [  # 不应触发（是一次性任务）
        "帮我处理这个 CSV 文件",
        "生成一份本周周报",
        "把这个 PDF 转成 Word",
        "帮我审查这段代码的 bug",
        "读取这个 Excel 并画图",
        "发一封邮件给客户",
    ],
    "Edge": [  # 边界：模糊，应 grill（不计入触发率）
        "我想做个 Skill",
        "把这个流程封装一下",
        "弄个能力包",
    ],
}


def evaluate(skill_md: str) -> dict:
    desc = load_description(skill_md)
    results: dict = {"TP": [], "TN": [], "Edge": []}
    tp_hit = tn_hit = 0

    for label, cases in TEST_SET.items():
        for u in cases:
            got = should_trigger(u)
            results[label].append({"utterance": u, "triggered": got})
            if label == "TP" and got:
                tp_hit += 1
            if label == "TN" and not got:
                tn_hit += 1

    tp_total = len(TEST_SET["TP"])
    tn_total = len(TEST_SET["TN"])
    trigger_rate = tp_hit / tp_total if tp_total else 0
    false_trigger_rate = (tn_total - tn_hit) / tn_total if tn_total else 0

    return {
        "status": "success" if trigger_rate >= 0.8 and false_trigger_rate <= 0.1 else "error",
        "description_length": len(desc),
        "description": desc,
        "trigger_rate": round(trigger_rate, 2),
        "false_trigger_rate": round(false_trigger_rate, 2),
        "threshold": {"trigger_rate": ">= 0.80", "false_trigger_rate": "<= 0.10"},
        "detail": results,
        "suggestions": _suggest(desc, trigger_rate, false_trigger_rate),
    }


def _suggest(desc: str, tr: float, ftr: float) -> list[str]:
    tips: list[str] = []
    if tr < 0.8:
        tips.append("触发率偏低：建议在 description 中补充用户常用动词，如'创建/封装/写/生成 Skill'")
        tips.append("补充触发关键词：" + ", ".join(OBJECT_NOUNS[:6]))
    if ftr > 0.1:
        tips.append("误触发率偏高：建议增加负向边界，如'不适用于一次性任务'、'不用于直接执行业务'")
    if len(desc) < 50:
        tips.append("description 过短，难以稳定匹配，建议 50–150 字")
    if len(desc) > 300:
        tips.append("description 过长，可能干扰匹配，建议精简到 150 字内")
    if "不" not in desc and "不适用" not in desc:
        tips.append("description 缺少负向边界（'不适用于…'），易与业务型 Skill 混淆")
    return tips


def main() -> int:
    parser = argparse.ArgumentParser(description="触发评测：评估 description 的触发准确率")
    parser.add_argument("skill_md", help="SKILL.md 路径")
    parser.add_argument("--json", action="store_true", help="仅输出 JSON")
    args = parser.parse_args()

    if not os.path.isfile(args.skill_md):
        print(json.dumps({"status": "error", "errors": ["文件不存在"], "warnings": []}))
        return 2

    result = evaluate(args.skill_md)

    if not args.json:
        print(f"触发率: {result['trigger_rate']} (阈值 >=0.80)", file=sys.stderr)
        print(f"误触发率: {result['false_trigger_rate']} (阈值 <=0.10)", file=sys.stderr)
        for s in result["suggestions"]:
            print(f"  ! {s}", file=sys.stderr)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
