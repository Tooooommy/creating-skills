#!/usr/bin/env python3
"""
test_trigger_llmlike.py —— 类 LLM 行为的触发评测（推荐）

与 test_trigger.py 的"关键词启发式"不同，本脚本用**向量相似度**模拟 LLM 的语义匹配，
更贴近真实 Agent 的 description 匹配行为，作为触发评测的权威来源。

若无 sentence-transformers，则自动降级为关键词启发式（仍可用于回归守护）。
"""
import argparse
import json
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = ROOT / "SKILL.md"


def load_description() -> str:
    text = SKILL_MD.read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---")[1]).get("description", "")


def cosine(a, b) -> float:
    import math
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def embed(text: str, dim: int = 64) -> list[float]:
    """极简词袋向量（按字符 n-gram），仅用于回归守护，非 ML。"""
    from collections import Counter
    c = Counter(text)
    v = [0.0] * dim
    for ch, n in c.items():
        v[hash(ch) % dim] += float(n)
    return v


def match(description: str, utterance: str, threshold: float = 0.50) -> bool:
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        model_name = os.environ.get("TRIGGER_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
        model = SentenceTransformer(model_name)
        d = model.encode(description)
        u = model.encode(utterance)
        score = float(d @ u) / (float((d ** 2).sum() ** 0.5) * float((u ** 2).sum() ** 0.5) + 1e-9)
    except Exception:
        # 降级：词袋余弦
        d = embed(description)
        u = embed(utterance)
        score = cosine(d, u)
    return score >= threshold, round(score, 3)


# 测试集（TP/TN/Edge）
CASES = {
    "TP": [
        "帮我创建一个处理 CSV 的 Skill",
        "写一个生成周报的技能包",
        "把 PDF 提取流程封装成 Skill",
        "我要新建一个代码审查的 Skill",
        "给我一个 SKILL.md 模板",
        "做一个把 Markdown 转 Word 的元技能",
        "帮我写个 skill",
        "把这个流程封装一下做成能力包",
        "帮我创建个 skill",
        "写个技能",
        "封装成 skill",
        "做个元技能",
        "生成 SKILL.md",
    ],
    "TN": [
        "帮我处理这个 CSV 文件",
        "生成一份本周周报",
        "把这个 PDF 转成 Word",
        "帮我审查这段代码的 bug",
        "发一封邮件给客户",
        "帮我部署这个服务",
    ],
    "Edge": [
        "我想做个 Skill",
        "把这个流程封装一下",
        "弄个能力包",
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(description="类 LLM 语义触发评测")
    parser.add_argument("--skill-md", default=str(SKILL_MD))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    desc = load_description()
    results: dict = {k: [] for k in CASES}
    tp_hit = tn_hit = 0

    for label, us in CASES.items():
        for u in us:
            triggered, score = match(desc, u)
            results[label].append({"utterance": u, "triggered": triggered, "score": score})
            if label == "TP" and triggered:
                tp_hit += 1
            if label == "TN" and not triggered:
                tn_hit += 1

    tp_rate = tp_hit / len(CASES["TP"])
    fp_rate = 1 - (tn_hit / len(CASES["TN"]))  # 误触发率

    payload = {
        "status": "success" if tp_rate >= 0.8 and fp_rate <= 0.1 else "error",
        "description_length": len(desc),
        "trigger_rate": round(tp_rate, 2),
        "false_trigger_rate": round(fp_rate, 2),
        "threshold": {"trigger_rate": ">= 0.80", "false_trigger_rate": "<= 0.10"},
        "detail": results,
    }

    if not args.json:
        print(f"触发率: {tp_rate:.0%} (阈值 >=80%)", file=sys.stderr)
        print(f"误触发率: {fp_rate:.0%} (阈值 <=10%)", file=sys.stderr)

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
