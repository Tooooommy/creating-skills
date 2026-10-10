# 跨平台差异对照（Platform Differences）

> 本文件是 `creating-skills` 的参考文档，用于把**平台差异**从主 `SKILL.md` 中隔离出来。
> 可移植最小集 = 一个目录 + 一个 `SKILL.md`。以下差异不应写入被生成 Skill 的主 SKILL.md。

## 1. Skill 发现（Discovery）

| 运行时 | Skill 存放路径 | 扫描时机 |
|--------|---------------|---------|
| Claude Code | `~/.claude/skills/<name>/`（用户全局）<br>`.claude/skills/<name>/`（项目专用） | 会话启动扫描 `name` + `description` |
| VS Code（Skill 扩展） | 由扩展的 manifest 指定 | 依扩展实现 |
| OpenAI Codex / 其他 | 依各实现 | 依各实现 |

**建议**：跨平台 Skill 不假设发现路径，改为在 `README.md` 中列出各平台放置方式。

## 2. 调用方式（Invocation）

| 运行时 | 调用形式 |
|--------|---------|
| Claude Code | 显式 `/<skill-name>`，或用户描述匹配 `description` 后自动激活 |
| VS Code | 依扩展命令/上下文菜单 |
| OpenAI 系 | 依其 Skills 发现与路由机制 |

## 3. 字段兼容性

| 字段 | 标准（共性） | 平台专属 |
|------|-------------|---------|
| `name` | ✅ 必填，kebab-case，≤64 字符 | — |
| `description` | ✅ 必填，≤1024 字符，唯一触发依据 | — |
| `license` | ✅ 可选 | — |
| `compatibility` | ✅ 可选 | — |
| `metadata` | ✅ 可选（任意键值） | 可存放平台专属标记，如 `metadata.vscode.entry` |
| `allowed-tools` | ⚠️ 实验性 | Claude Code 支持度较高；其他运行时可能忽略 |

**原则**：主 SKILL.md 只用共性字段；平台专属字段塞进 `metadata` 或本目录下的对应文件。

## 4. 打包格式

| 产物 | 说明 | 适用 |
|------|------|------|
| 目录 | `<skill-name>/SKILL.md ...` | 开发、Claude Code 直接引用 |
| `.skill` | 本质是 zip，**压缩包顶层必须为 `<skill-name>/SKILL.md`** | Claude.ai 上传、VS Code 分发 |
| 插件市场 | Claude Code 可 `claude plugin install` 从 marketplace 安装 | 团队/生态分发 |

打包命令（通用）：

```bash
cd <parent-of-skill>
zip -r <skill-name>.skill <skill-name>/ \
  -x "*/__pycache__/*" "*/.env" "*/.git/*" "*/node_modules/*"
```

## 5. 权限模型

- **Claude Code**：权限由沙箱决定，`allowed-tools` 可预批准工具。
- **VS Code**：权限由扩展 host 与 workspace 信任决定。
- **通用原则（最小权限）**：只访问明确需要的资源；路径白名单；密钥走环境变量；拒绝 `../` 穿越。

## 6. 版本与分发

- 语义化版本 `metadata.version: "1.0.0"`。
- 团队多 Skill 建议单 Git 仓库 + 目录隔离 + JSON 注册表 `skills-registry.json`。
- CI：向主分支提交 → 自动校验 → 打包为 Release 附件。
