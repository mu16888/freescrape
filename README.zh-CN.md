# FreeScrape 中文说明

[![tests](https://github.com/mu16888/freescrape/actions/workflows/test.yml/badge.svg)](https://github.com/mu16888/freescrape/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> 本文件是 [README.md](README.md) 的简体中文版。若两处说法有出入，**以英文版为准**。

**一句话**：一个免费、开源的命令行抓取工具。在终端里把网页转成 Markdown / JSON、搜网页、按模板抽结构化数据，也能接进 AI 编程助手。不需要付费账号、不需要代理网络、不上传你的数据。

> ⚠️ **独立项目声明**：FreeScrape 与 Bright Data 或任何商业抓取服务商**没有关联**，未获其背书或赞助。它只是用开源组件复刻了商业抓取工具的「命令用法」，不是任何商业产品的替代品。

---

## 一、先看清能力边界

商业抓取工具真正收费的部分是**住宅代理网络**和**反爬解锁**（自动过验证码、过 Cloudflare 拦截）——那背后是大量真实设备 IP 和打码基础设施，无法免费复刻。FreeScrape 免费复刻的是**软件这一层**：

| 能力 | FreeScrape（免费） | 商业工具（付费） |
|---|---|---|
| 命令行用法、输出格式 | ✅ | ✅ |
| 本地配置（不用登录账号） | ✅ | ✅ |
| 网页 → Markdown / JSON 正文抽取 | ✅ httpx + trafilatura | ✅ |
| 免费网页搜索（DuckDuckGo / Bing） | ✅ | ✅ 搜索 API |
| 真实浏览器自动化（Playwright） | ✅ | ✅ 云端浏览器 |
| AI 发现 / 提取（自备模型接口） | ✅ | ✅ |
| 接进 AI 编程助手（MCP） | ✅ | ✅ |
| 预置抽取模板（可自行扩展） | ✅ | ✅ 数千个 |
| **住宅代理网络** | ❌ 需你自己提供代理 | ✅ 付费 |
| **反爬解锁 / 验证码破解** | ❌ 不提供，仅尽力而为 | ✅ 付费 |

**结论**：普通网站够用；遇到防护严格的站点会抓不到。这是设计上如实承认的限制，不是故障。**它不会帮你绕验证码，也不承诺能抓任何网站。**

---

## 二、安装

**前提**：Python ≥ 3.10。

> ⚠️ 目前**只能从源码安装**。项目尚未发布到 PyPI，`pip install freescrape` 会报找不到包，请不要照旧教程敲这条。

```bash
git clone https://github.com/mu16888/freescrape.git
cd freescrape
python -m pip install -e .
```

装完后终端里就有 `freescrape` 命令。三个可选增强：

```bash
# 真实浏览器自动化（browser 命令，会下载 Chromium）
python -m pip install -e ".[browser]" && playwright install chromium

# AI 功能（discover），任意 OpenAI 兼容接口，密钥自备；也可指向本地 Ollama
python -m pip install -e ".[llm]"
```

也可以不装成命令，装好依赖后在源码目录直接运行：

```bash
python -m freescrape <命令>
```

> 小提示：`-e .` 表示「可编辑安装」，改源码后不用重装就能生效。但**移动项目目录后必须在新位置重新执行一次** `python -m pip install -e .`，否则命令会指向旧路径。

---

## 三、快速上手

```bash
# 1. 首次配置（交互式：UA、代理、可选模型接口，可一路回车跳过）
freescrape init

# 2. 抓一个网页，输出 Markdown
freescrape scrape https://example.com

# 3. 免费搜网页，不需要 API 密钥
freescrape search "web scraping best practices"

# 4. 查看并运行内置抽取模板
freescrape pipelines search
freescrape pipelines run hackernews

# 5. 遇到必须执行 JS 才出内容的页面，改用真实浏览器
freescrape scrape https://spa.example.com --browser

# 6. 把抓取能力接给 AI 编程助手
freescrape add mcp
```

所有命令都支持三个输出选项：`--json`（结构化输出，方便管道传给别的程序）、`--pretty`（缩进美化）、`-o 文件名`（写文件，按扩展名自动存成 json / md / csv）。`--json` 模式下告警走错误输出，不会混进数据里。

---

## 四、命令一览

| 命令 | 作用 | 常用参数 |
|---|---|---|
| `scrape <网址>` | 抓网页并抽正文 | `--browser`（用真实浏览器）、`--proxy <地址>`、`--timeout <秒>`、`--html`（附带原始 HTML） |
| `search <关键词>` | 免费搜索，返回标题 / 链接 / 摘要 | `--engine ddg\|bing`（默认 ddg）、`--max N` |
| `discover <关键词>` | 先搜再让 AI 排序、总结 | 未配置模型时退回原始结果 |
| `browser` | 真实浏览器操作：`open`、`snapshot`、`screenshot <网址> <路径>`、`click`、`type`、`scroll` | `--selector`、`--text` |
| `pipelines` | 内置 / 自定义抽取模板：`search`、`info <名称>`、`run <名称>` | — |
| `config` | 本地配置：`list`、`get <键>`、`set <键> <值>` | — |
| `budget` | 显示费用状态，恒为 $0.00 | — |
| `add mcp` / `mcp --stdio` | 把 `scrape`、`search` 暴露成 MCP 工具，供 Claude Code、Cursor 等调用 | — |

---

## 五、配置

配置文件在 `~/.freescrape/config.json`（Windows 上是 `C:\Users\<用户名>\.freescrape\config.json`），全部留在本地。

| 键 | 含义 |
|---|---|
| `user_agent` | 默认请求头里的浏览器标识 |
| `proxy` | 代理地址 `http://主机:端口`，直连填 `null` |
| `timeout` | 请求超时秒数 |
| `browser_headless` | 浏览器是否默认后台运行 |
| `llm_api_key` / `llm_base_url` / `llm_model` | 模型接口凭据（可选） |

也支持环境变量 `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL`。

> 代理默认**不走系统代理**，只有你显式配置了 `proxy` 或命令带 `--proxy` 才生效——这样避免系统里某个失效代理悄悄让请求失败。

---

## 六、自定义抽取模板

把一份 JSON 描述文件放到 `~/.freescrape/pipelines/<名称>.json`，就能用 `freescrape pipelines run <名称>` 调用。最小例子：

```json
{
  "name": "my_pipeline",
  "description": "抓某个列表页的标题和链接",
  "url": "https://example.com",
  "item_selector": "div.item",
  "fields": [
    {"name": "title", "selector": "a", "attr": "text"},
    {"name": "link",  "selector": "a", "attr": "href"}
  ]
}
```

`item_selector` 指「每条数据所在的那块 HTML」，`fields` 里的 `selector` 指从这块里取哪个元素，`attr` 用 `text` 取文字、用 `href` 等取属性值。

---

## 七、常见问题

| 问题 | 回答 |
|---|---|
| 为什么某网站抓不到？ | 常见三种：站点有强反爬、页面必须执行 JS 才有内容、网络本身不通。先试 `--browser`；仍不行就自带 `--proxy`；再不行属于能力边界，工具不会绕验证码。 |
| 会花钱吗？ | 核心功能 0 元。只有你自己接了付费模型接口或付费代理才会产生费用。 |
| 命令行输出为什么还是英文？ | 本文件只翻译**文档**。命令帮助、报错、运行输出仍是英文；要连命令行一起中文化，需要改代码做多语言支持，属于另一项开发工作。 |
| 有 `fs` 这个短命令吗？ | 目前没有。安装配置里只注册了 `freescrape` 一个命令。 |
| 中文版和英文版不一致怎么办？ | 以英文版为准，并欢迎提 issue 或 PR 修正。 |

---

## 八、参与维护

贡献规则见英文的 [CONTRIBUTING.md](CONTRIBUTING.md)。三条底线：能力边界不许夸大、核心功能不许依赖付费接口、`--json` 输出必须保持合法（Windows 管道下也要测）。

---

## 许可证

[MIT](LICENSE)。可自由使用、修改、分发。

---

## 免责声明

抓取网页可能受目标网站服务条款与适用法律约束。请遵守 `robots.txt`、控制请求频率、不要用于违反网站条款的用途；使用后果由使用者自行承担。
