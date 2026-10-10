# SKILL.md 标准模板（被生成 Skill 的骨架）

> 由 `creating-skills` 在 Phase 2 套用。保留章节骨架，填充具体内容。

```markdown
---
name: <kebab-case, ≤64 字符, 动名词形式>
description: >
  <50–150 字。用于<做什么>的 Skill。当用户<场景1>、<场景2> 时激活。
  不适用于<负向边界>。关键词：<k1>、<k2>。
license: MIT
compatibility: <运行时要求>
metadata:
  version: "1.0.0"
  author: <作者>
  platforms: [claude-code, vscode, openai-codex]
allowed-tools: [bash, read, write]   # 实验性，按需
---

# <Skill 中文名>

> 一句话定位

## 一、何时激活（Trigger）
- 正向信号：...
- 负向信号（不激活）：...

## 二、输入输出规范（I/O Spec）
### 输入
- 来源 / 格式 / 校验
### 输出
- 内容 / 格式 / 落盘 / 时机

## 三、执行步骤
1. 步骤一：动作 → 产出 `<f1>`
2. 步骤二：依赖 `<f1>`，动作 → 产出 `<f2>`

## 四、脚本调用（若有）
`scripts/main.py --input <p> --output <p> [--dry-run]`
- 参数：命令行传入
- 输出：JSON → stdout；诊断 → stderr
- 依赖：`scripts/requirements.txt` 或 PEP 723 内联

## 五、错误处理
| 错误 | 检测 | 反馈 | 可恢复 |
|------|------|------|--------|

## 六、安全与权限
- 最小权限 / 路径白名单 / 密钥走环境变量 / subprocess 列表参数

## 七、上下文与状态
- 无持久存储；中间状态写 `.state.json`；参数优先级

## 八、日志与可观测
- 日志路径（JSON）/ 进度汇报 / 完成信号

## 九、示例
- 示例 1
- 示例 2
```
