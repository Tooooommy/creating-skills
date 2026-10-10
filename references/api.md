# 外部 API 集成要点

> 当被生成的 Skill 需要调用第三方 HTTP API 时，引用本章。

## 1. 调用方式

```python
import os, requests

API_KEY = os.environ.get("MY_API_KEY")
if not API_KEY:
    raise RuntimeError("缺少环境变量 MY_API_KEY，请在 shell 中 export 后重试")

headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
resp = requests.post(url, headers=headers, json=payload, timeout=30)
resp.raise_for_status()
```

## 2. 密钥管理

- **永远**从环境变量读取，禁止硬编码
- `.env` 必须写入 `.gitignore`
- README 中明确写出所需环境变量名
- 可选：支持 `.env` 文件加载（`python-dotenv`），但生产环境优先环境变量

## 3. 限流与重试

```python
import time, random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

s = requests.Session()
s.mount("https://", HTTPAdapter(
    max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
))

def call_with_backoff(fn, max_retry=5):
    for i in range(max_retry):
        try:
            return fn()
        except requests.exceptions.RequestException as e:
            if getattr(e.response, "status_code", None) == 429:
                wait = min(2 ** i + random.random(), 30)
                print(f"[retry {i+1}/{max_retry}] 429 限流，等待 {wait:.1f}s", file=sys.stderr)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("超过最大重试次数")
```

## 4. 批量调用

- 加延迟：`time.sleep(0.2)` 避免打满 QPS
- 并发：I/O 密集用 `asyncio.Semaphore` 限流 + `aiohttp`
- 缓存：相同入参缓存到 `<output>/.cache/<hash>.json`

## 5. 超时

```python
asyncio.wait_for(coro, timeout=30)
# 或 requests(timeout=(connect, read))
```

## 6. 错误映射

| HTTP | 含义 | Skill 行为 |
|------|------|-----------|
| 400 | 参数错误 | 反馈具体字段 |
| 401/403 | 鉴权失败 | 提示检查 API Key |
| 404 | 资源不存在 | 提示确认 ID |
| 429 | 限流 | 指数退避重试 |
| 5xx | 服务端 | 重试 3 次后报错 |
