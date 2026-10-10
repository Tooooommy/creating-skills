# 领域知识：如何设计一个好 Skill

> 供 `creating-skills` 在 Phase 2–3 引用，避免在 SKILL.md 正文中堆砌冗长说明。

## 1. `name` 命名

- 形式：动名词（verb + -ing），如 `processing-pdfs`、`generating-reports`、`reviewing-code`
- 规则：kebab-case，仅小写字母、数字、连字符，≤64 字符
- 反例：`PDFProcessor`（PascalCase）、`pdf_tool`（下划线）、`my-skill-001`（无意义序号）

## 2. `description` 写作公式

```
用于<做什么>的 Skill。当用户<场景 1>、<场景 2>、<场景 3> 时激活。
不适用于<负向边界>。关键词：<k1>、<k2>、<k3>。
```

- 长度：50–150 字（上限 1024）
- 必须含：能力声明 + 触发时机 + 关键词 + 负向边界
- 技巧：列出用户真实会说的短语（"封装成 Skill"、"做个元技能"）

## 3. 单一职责判定

若出现以下信号，应拆分：
- description 需要用"且"、"另外还"连接两个动作
- 需要写很长才能说清"它不做什么"
- 脚本出现两个互不相关的主流程

## 4. 输入输出规范（I/O Spec）

必答四问：
1. **来源**：上下文 / 上传文件 / API / 参数？
2. **格式**：类型、编码、约束（如"CSV 须含 header"）？
3. **落盘**：大文件一律传路径，不传内容进上下文
4. **时机**：一次性全部输出，还是分步汇报？

## 5. 多步骤与依赖

- 显式编号步骤，每步一个动词短语
- 后续步骤依赖前序产物时，**执行前先 `os.path.exists` 检查**
- 耗时 >5s 的步骤必须报进度：`[2/5] 正在调用 OCR ...`

## 6. 错误处理模式

```python
import json, sys

def fail(code: str, msg: str) -> None:
    print(json.dumps({"status": "error", "error": {"code": code, "message": msg}}))
    sys.exit(2)

try:
    ...
    print(json.dumps({"status": "success", "data": {...}}))
except ValueError as e:
    fail("INVALID_INPUT", str(e))
except PermissionError:
    fail("PERMISSION_DENIED", "无权限写入输出目录")
except Exception as e:
    fail("INTERNAL", f"未预期错误: {e}")
```

## 7. 安全清单

- [ ] 路径白名单（拒绝 `..`）
- [ ] 密钥仅 `os.environ`，`.env` 进 `.gitignore`
- [ ] `subprocess.run([cmd, arg, ...])`（列表形式）
- [ ] 不 `eval` / `exec` 用户输入
- [ ] 输出目录可写性预检

## 8. 幂等性

- 同输入 → 同输出（避免"追加"语义）
- 用哈希/时间戳做缓存键：`cache/<sha256(input)>_.json`

## 9. 性能

- 先测再优化：`time.perf_counter()`
- 大文件：`pandas.read_csv(..., chunksize=...)` 或逐行
- 多文件：`concurrent.futures.ThreadPoolExecutor` / `ProcessPoolExecutor`
- 重复计算：本地缓存
- I/O 密集：`asyncio` + `aiofiles`；CPU 密集：`ProcessPoolExecutor`

## 10. 可观测

- 日志 JSON 化：`{"ts":..., "level":"INFO", "step":"phase3", "duration_ms":123}`
- 落盘固定路径：`<output>/<skill>.log`
- 完成信号明确："✅ 已完成，产物：<path>"

## 11. 测试

- 单元测试：正常路径 + 边界（空输入、坏格式、缺依赖、权限不足、路径穿越）
- 触发评测：TP/TN/Edge 三类，以测试集得分为准
- 集成测试：真实跑一遍端到端

## 12. 版本与发布

- 语义化版本 `metadata.version: "1.0.0"`
- 变更记录 `CHANGELOG.md`
- 打包：`zip -r <name>.skill <name>/`（顶层须为 `<name>/SKILL.md`）
- 团队分发：单 Git 仓库 + `skills-registry.json` + CI 自动打包 Release
