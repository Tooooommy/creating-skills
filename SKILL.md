---
name: creating-skills
description: >
  创建 Skill 的元技能。当用户说"帮我创建一个/个/个 skill"、"写一个/个技能/能力包/元技能"、
  "把某流程封装成 skill"、"生成 SKILL.md"、"做个 skill-creator"时激活。它先 grill 澄清需求，
  再按开放标准生成跨平台 Skill 包。不适用于一次性业务任务，也不执行业务逻辑。
  关键词：创建技能、新建 Skill、技能模板、SKILL.md、meta-skill、skill-creator、封装流程、能力包。
license: MIT
compatibility: 需要 Python 3.9+（运行校验与评测脚本）
metadata:
  version: "1.0.0"
  author: yuanbao
  platforms: [claude-code, vscode, openai-codex]
allowed-tools: [bash, read, write, edit, delegate, ask_user_question]
---

# creating-skills：创建 Skill 的 Skill（元技能）

> 把"领域知识 + 流程经验 + 环境约束"沉淀为可复用、可分发、跨平台运行的 Skill 能力包。
> 它不直接完成用户的业务任务，而是**生成一个新的 Skill**。

---

## 一、何时激活（Trigger）

**正向信号**（激活）：

1. 用户明确要求"创建一个 Skill / 技能 / 能力包 / 元技能"；
2. 想把重复流程（读 PDF、生成报告、调用 API、代码审查……）"封装起来复用"；
3. 说"写一个 SKILL.md"、"给我一个技能模板"；
4. 用户反复让 AI 执行同类操作，本 Skill 应主动建议"是否沉淀为 Skill"。

**负向信号**（不激活）：用户只想一次性完成某个业务任务（"帮我写份 Word"、"处理这个 CSV"），
而非"把这个能力做成可复用的 Skill"。此时应先完成任务，再**建议**是否封装。

---

## 二、设计原则（Design Principles）

| 原则 | 说明 |
|------|------|
| **单一职责** | 一个 Skill 只做一件事。description 需写很长才能说清"不做什么"时，说明该拆分。 |
| **渐进式披露** | 三层加载：① `name`+`description`（发现）→ ② 完整 `SKILL.md`（激活）→ ③ 按需读 `references/`、调 `scripts/`（执行）。 |
| **描述即入口** | `description` 是唯一触发判断依据，须写清"能做什么 + 何时该用"，50–150 字，上限 1024 字符。 |
| **脚本自包含** | 脚本放 `scripts/`，依赖显式声明；参数经命令行传入；JSON 到 stdout；诊断到 stderr。 |
| **最小权限** | 路径白名单；密钥走环境变量；subprocess 用列表参数；禁 `os.system(f"...")` 拼接。 |
| **幂等** | 同输入多次执行，输出一致。 |
| **可观测** | 耗时 >5s 分步报进度；步骤级耗时；日志落盘。 |
| **跨平台** | 以"目录 + SKILL.md"为可移植最小集；平台差异隔离到 `references/platforms.md`。 |

---

## 三、工作流程（Workflow）

```
Phase 0  接收意图      —— 捕获初步想法（可仅一句话）
Phase 1  GRILL 澄清    —— 结构化问卷，补齐 6 大维度
Phase 2  最小草稿      —— SKILL.md 骨架（frontmatter + 步骤大纲）
Phase 3  资源落实      —— scripts/ + references/ + tests/
Phase 4  评测修订      —— 触发评测 + 功能评测，证据化迭代
Phase 5  打包交付      —— 按宿主打包 .skill / zip / 目录
```

### Phase 1：GRILL 结构化问卷（关键，不可跳过）

**需求不明确时必须先 grill，再生成。** 按 6 维度追问，一次 ≤4 问，可分轮。

| # | 维度 | 必问 | 决策影响 |
|---|------|------|---------|
| Q1 | 目标与边界 | 解决什么**具体问题**？明确"**不**做什么"。 | `description` 触发边界 |
| Q2 | 输入输出 | 输入（文件/文本/API/无）？输出（文件/JSON/改代码/文本）？落盘何处？ | I/O 规范、脚本接口 |
| Q3 | 运行环境 | 宿主（Claude Code / VS Code / Codex / 跨平台）？依赖（Python 包/Node/二进制/API Key）？ | `compatibility`、`allowed-tools` |
| Q4 | 工具与脚本 | 是否调外部工具/API/DB？是否需脚本（Python 优先）？ | 是否建 `scripts/`、依赖声明方式 |
| Q5 | 步骤与依赖 | 能否拆为显式步骤？步骤间有无文件依赖？哪些耗时需报进度？ | 多步骤流程、依赖检查 |
| Q6 | 异常与边界 | 哪些会出错（缺文件/坏格式/限流/鉴权/路径穿越）？如何反馈？可恢复？ | 错误处理章节 |

**输出**：整理为 **《需求确认单》**（Markdown 表格），复述并确认后再进 Phase 2。

### Phase 2：生成 SKILL.md 草稿

套用 `references/skill-md-template.md`。frontmatter 以 `---` 起止，`name:`/`description:` 冒号后一个空格。

### Phase 3：资源落实

```
<skill-name>/
├── SKILL.md                  # 必填
├── scripts/
│   ├── main.py               # --help / --input / --output / --dry-run
│   ├── requirements.txt      # 或 PEP 723 内联
│   └── lib/                  # 公共模块（避免循环依赖）
├── references/
│   ├── platforms.md          # 跨平台差异
│   ├── api.md                # 外部 API（若有）
│   └── domain-knowledge.md   # 领域知识
├── tests/
│   ├── test_main.py
│   └── fixtures/
├── assets/                   # 可选
├── README.md
└── .gitignore
```

**脚本铁律**（详见 `references/domain-knowledge.md`）：

1. 入口集中校验参数，失败写清"期望 / 实际"；
2. `argparse` + `--help`；
3. JSON → stdout；诊断 → stderr；
4. 密钥 `os.environ`，未配置清晰报错；
5. subprocess 列表参数；
6. 路径白名单：
   ```python
   from pathlib import Path
   import os
   def assert_safe(p: str, root: str) -> Path:
       rp = (Path(root) / p).resolve()
       if not str(rp).startswith(str(Path(root).resolve()) + os.sep):
           raise ValueError(f"路径越界: {p}")
       return rp
   ```
7. 大文件只传路径；相同输入缓存；
8. `time.perf_counter()` 记耗时；
9. I/O 密集 `asyncio`/`aiofiles`；CPU 密集 `ProcessPoolExecutor`；多文件 `concurrent.futures`；
10. 依赖自检（轻量/开发场景）：
    ```python
    try:
        import pandas  # noqa
    except ImportError:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pandas"], check=True)
    ```

### Phase 4：评测与修订（Evidence-based）

#### 4.1 触发评测（description）

测试集：TP（应触发）≥8 条、TN（不应触发）≥5 条、Edge（边界）≥3 条。

- **触发率** = TP 命中 / TP 总数，目标 **≥ 80%**
- **误触发率** = TN 误命中 / TN 总数，目标 **≤ 10%**

触发率低 → 补用户常用动词/关键词；误触发高 → 加负向边界；与兄弟 Skill 混淆 → 增大区分度。
**以测试集得分为准，警惕训练集过拟合。**

```bash
python tests/test_trigger.py <SKILL.md>          # 关键词回归
python tests/test_trigger_llmlike.py <SKILL.md>  # 语义评测（推荐，需 sentence-transformers）
```

#### 4.2 功能评测

运行 `scripts/main.py`，断言退出码与 JSON 的 `status`。统一返回：
`{"status": "success"|"error", "data": {...}, "error": {"code": "...", "message": "..."}}`
覆盖：参数缺失、坏输入、路径穿越、依赖缺失、API 429。

#### 4.3 结构校验

```bash
python scripts/validate_skill.py <SKILL.md> [--json]
```

校验：`name` kebab-case ≤64、`description` 20–1024、必需章节齐全、脚本 `--help` 可用。

### Phase 5：打包与交付

| 宿主 | 产物 | 说明 |
|------|------|------|
| Claude Code | `~/.claude/skills/<name>/` 或 `.claude/skills/<name>/` | 重启生效；或 `claude plugin install` |
| VS Code / 通用 | `.skill`（zip，顶层 `<name>/SKILL.md`） | 先 validate 再打包 |
| Codex 等 | 目录 / zip | 参考 `references/platforms.md` |

```bash
cd <parent>
zip -r <name>.skill <name>/ -x "*/__pycache__/*" "*/.env" "*/.git/*"
```

**交付清单**（README 须含）：

- [ ] `SKILL.md`（frontmatter 合法、description 通过触发评测）
- [ ] `scripts/` + 依赖声明
- [ ] `tests/` + 运行方式
- [ ] `references/`（含跨平台对照）
- [ ] `.gitignore`（排除 `.env`）
- [ ] 版本与变更记录
- [ ] 安装与配置说明（环境变量名）
- [ ] 2–3 个端到端示例

---

## 四、跨平台适配（Cross-platform）

可移植最小集 = 目录 + SKILL.md。差异**不**写入主文件，隔离到 `references/platforms.md`：

| 维度 | Claude Code | VS Code Skill | Codex / 其他 |
|------|-------------|---------------|--------------|
| 发现路径 | `~/.claude/skills/` 或 `.claude/skills/` | 扩展 manifest | 依实现 |
| 调用 | `/<skill>` 或描述匹配 | 依扩展 | 依实现 |
| 权限字段 | `allowed-tools` | 扩展 manifest | 各自 |
| 打包 | 目录 / 插件市场 | `.skill` (zip) | zip / 目录 |

主 SKILL.md 只用共性字段（`name`、`description`、`license`、`compatibility`、`metadata`）。

---

## 五、本 Skill 的错误处理

| 场景 | 处理 |
|------|------|
| 需求仍模糊，无法形成《需求确认单》 | 继续 grill；最多 3 轮，仍模糊则出"最小可行草稿"并标 `[TODO]` |
| 宿主不明确 | 默认"跨平台"，README 注明"未做宿主深度适配" |
| 结构校验失败 | 自动修复（frontmatter、name 正则、缺失章节），重跑 |
| 触发评测未达标 | 修订 description，重测，记录前后分数 |
| 脚本失败 | 捕 traceback，定位步骤，给修复 diff |
| 依赖缺失 | README 列出；脚本自检并友好提示 |

---

## 六、日志与可观测

- 日志：`<cwd>/creating-skills.log`（JSON，每行一条）
- 字段：`timestamp`、`phase`、`step`、`duration_ms`、`skill_name`、`status`
- 进度：`[Phase 3/5] 正在编写 scripts/main.py ...`
- 完成信号：`✅ Skill <name> 已生成，产物：<path>，共 <n> 个文件。见 README.md。`

---

## 七、示例（Examples）

### 示例 1：清晰需求 → 直接生成

> **用户**：创建一个 Skill，把 Markdown 转成带目录的 Word，输入 .md，输出 .docx 到 ./out/。

仅补问"是否自定义样式 / 处理图片"。确认后生成 `markdown-to-docx/` 完整包，跑评测，打包。

### 示例 2：模糊需求 → 先 grill（典型）

> **用户**：我想做个 Skill。

第 1 轮（Q1+Q2）：
1. 解决什么**具体问题**？它**不**做什么？
2. 输入是什么？输出什么形式？

第 2 轮（Q3+Q4）：
3. 运行在哪儿？需要什么依赖？
4. 是否调外部工具/API？是否需脚本（建议 Python）？

第 3 轮（Q5+Q6）：
5. 能否拆成显式步骤？有无文件依赖？
6. 哪些会出错？如何反馈？

→ 《需求确认单》→ 确认 → Phase 2。

### 示例 3：从重复行为主动建议

> **用户**：（第 5 次让 AI 生成周报）"整理成周报。"

先完成本次，再建议："你近期多次让我做'整理周报'。要不要封装成 Skill `weekly-report`？
之后说'生成本周周报'即可按统一格式自动产出。回复'好'即开始。"

---

## 八、自检清单（Release Gate）

- [ ] `name` kebab-case、≤64、动名词
- [ ] `description` 50–150 字：做什么 + 何时用 + 关键词 + 负向边界
- [ ] 触发率 ≥ 80%，误触发率 ≤ 10%
- [ ] `tests/` 全绿，边界错误优雅处理
- [ ] 章节齐全：触发 / I/O / 步骤 / 错误处理 / 安全 / 日志 / 示例
- [ ] 脚本：`--help`、JSON→stdout、诊断→stderr、无硬编码密钥
- [ ] 路径白名单、subprocess 列表参数、参数集中校验
- [ ] 依赖已声明
- [ ] `.gitignore` 排除 `.env`/`__pycache__`/产物
- [ ] `README.md` 含安装、配置（环境变量名）、示例
- [ ] 语义化版本 + 变更记录
- [ ] 平台差异隔离到 `references/platforms.md`
- [ ] 大文件只传路径；相同输入缓存；耗时步骤有进度
- [ ] 幂等
