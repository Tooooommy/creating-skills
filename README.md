# creating-skills

> **创建 Skill 的 Skill**（元技能 / meta-skill）。
> 依据 [Agent Skills 开放标准](https://github.com/anthropics/skills) 与 [菜鸟教程 Skills 系列](https://www.runoob.com/skills/) 编写。
> 跨平台兼容：Claude Code / VS Code Skill / OpenAI Codex 等。

## 它能做什么

把你口中的"想法"沉淀为一个**完整、规范、可分发**的 Skill 能力包：

```
SKILL.md + scripts/ + references/ + tests/ + README + 打包
```

核心机制：**需求不明确时，先 grill（结构化澄清），再生成。**

## 安装

### Claude Code

```bash
# 用户全局
mkdir -p ~/.claude/skills
cp -r creating-skills ~/.claude/skills/

# 或项目专用
mkdir -p .claude/skills
cp -r creating-skills .claude/skills/
```

重启 Claude Code 后，说"帮我创建一个 Skill"即可触发。

### VS Code / 其他

将本目录打包为 `.skill`（本质是 zip，顶层须为 `creating-skills/SKILL.md`）后按对应运行时方式安装。

## 使用流程

```
你说"我想做个 Skill"
   ↓
[Phase 1] 我追问 6 个维度（目标/输入输出/环境/工具/步骤/异常）
   ↓
[确认] 《需求确认单》
   ↓
[Phase 2-3] 生成 SKILL.md + scripts/ + references/ + tests/
   ↓
[Phase 4] 触发评测 + 结构校验 + 功能测试
   ↓
[Phase 5] 打包交付，输出 README 与示例
```

## 脚本

| 脚本 | 用途 | 调用 |
|------|------|------|
| `scripts/validate_skill.py` | 结构校验 | `python validate_skill.py <SKILL.md> [--json]` |
| `tests/test_trigger.py` | 触发评测 | `python test_trigger.py <SKILL.md> [--json]` |
| `tests/test_integration.py` | 端到端 | `python test_integration.py` |

依赖：`pyyaml>=6.0`（`scripts/requirements.txt`）。

## 配置（环境变量）

本 Skill 本身不依赖外部 API Key。若被生成的 Skill 需要密钥，请在生成的 `README.md` 中明确环境变量名，并在脚本中从 `os.environ` 读取。

## 目录结构

```
creating-skills/
├── SKILL.md                  # 核心：执行指引
├── scripts/
│   ├── validate_skill.py     # Skill 结构校验器
│   └── requirements.txt      # 依赖
├── references/
│   └── platforms.md          # 跨平台差异对照
├── tests/
│   ├── test_trigger.py       # 触发评测
│   └── test_integration.py    # 端到端
├── README.md
└── .gitignore
```

## 示例

### 清晰需求 → 直接生成

> 用户：帮我创建一个 Skill，把 Markdown 转成带目录的 Word，输入 .md，输出 .docx 到 ./out/。

仅补问"是否需自定义样式"，确认后即生成 `markdown-to-docx/` 完整包。

### 模糊需求 → 先 grill

> 用户：我想做个 Skill。

分 3 轮追问（目标边界 → 输入输出 → 环境依赖 → 工具脚本 → 步骤依赖 → 异常边界），
整理《需求确认单》确认后再生成。

## 版本

`metadata.version: "1.0.0"`（语义化）。

## License

MIT
