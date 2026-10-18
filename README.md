# SelfDiff · 见己

**对自己的理解，也值得有版本记录。**

把散落在不同 AI 工具里的会话放在一起，发现反复出现的卡点、成功条件与变化。每项发现能回查原话、查看反例，并由你确认、修正或驳回。

[English](README.en.md) · [快速开始](docs/quickstart.md) · [导入格式](docs/import-formats.md) · [隐私与数据流](docs/privacy.md)

![SelfDiff 合成示例档案](docs/images/demo.png)

## 从一句话，到一个可以修正的发现

> “我总想把方案比较完再动手，结果这一周还没有开始。”

另一段会话也提到比较方案后迟迟未开始。SelfDiff 把两次记录放在一起，提出一个有边界的观察：**当需求不清楚时，比较方案可能占用了验证的时间。**

你可以补充：“需求明确时，我开始得很快。”这个修订会成为新版本；原话仍在，旧结论也能回看。上图与此例均为从头创作的合成资料。

## 能做什么

- **六维个人档案**：目标与价值、思考与决策、学习与协作、行动与成果、兴趣主线、阶段变化。资料不足时留空。
- **有原文的洞察**：校验消息身份、版本、发言人和精确引文；反复模式至少需要两个独立会话。
- **本人修订**：符合、部分符合、不符合、自己的表述与理由；驳回主题不会被同键重跑覆盖。
- **自我判断对照**：为一个具体判断寻找支持、反例与情境，不把未找到反例当成反例不存在。
- **两个时期比较**：比较观点和选择，区分观点改变、情境补充、模型误解与来源用途变化。
- **可控导出**：JSON、Markdown 完整档案；另行选择、编辑和确认后下载不附原话的 HTML 分享卡。
- **无需密钥的合成示例**：独立资料空间；自己的导入不会混入示例结论。

## 立即运行

需要 Python 3.10+。发布 wheel 已包含界面，使用者无需 Node.js。

```sh
python -m pip install https://github.com/wind127/selfdiff/releases/download/v0.1.0/selfdiff-0.1.0-py3-none-any.whl
python -m selfdiff.cli serve
```

浏览器会打开带一次性令牌的本机链接。默认监听 `127.0.0.1:8765`，资料保存在 `~/.selfdiff`。点击“体验示例”即可体验完整流程。也可使用 `selfdiff serve` 命令。

真实资料的导入、搜索和管理不需要模型。分析需在“模型设置”填写兼容接口地址与模型名；需要密钥时，在启动服务的进程环境设置 `SELFDIFF_API_KEY`。支持云端 HTTPS 接口和本机 HTTP 接口（如本机模型提供的兼容服务）。供应商需支持 `/chat/completions` 和 JSON 对象输出。

```powershell
# Windows PowerShell：密钥值由你自己填写，应用不持久化它
$env:SELFDIFF_API_KEY = "你的供应商密钥"
python -m selfdiff.cli serve
```

```sh
# macOS / Linux
export SELFDIFF_API_KEY="your-provider-key"
python -m selfdiff.cli serve
```

也支持 `SELFDIFF_BASE_URL`、`SELFDIFF_MODEL` 环境变量。具体步骤见[快速开始](docs/quickstart.md)。

## 来源支持范围

| 来源 | v0.1 导入方式 | 边界 |
|---|---|---|
| Codex | 指定 JSONL 文件或目录 | 测试覆盖 session_meta、response_item 文本消息和事件记录；优先使用规范消息轨道 |
| Claude Code | 指定项目 JSONL | user/assistant/message 与文本块；排除工具结果、元信息和压缩摘要 |
| WorkBuddy | 指定 JSONL | type:message、role/content 或 message 内嵌结构；未知变体不猜测 |
| ChatGPT | 官方 conversations.json / ZIP | 沿 current_node 的父链导入所选分支 |
| Claude 网页 | 官方 conversations.json / ZIP | chat_messages、human/assistant、text/content 结构 |
| DeepSeek、豆包、千问办公及其他 | 标准 JSON、带 User:/Assistant: 标记的 Markdown/文本 | **通用导入，未实现云端账号全历史扫描** |

原生适配指测试覆盖的格式族，并非各客户端未来版本的兼容保证。没有角色边界的文本不会直接用于个人事实分析。请先用导入预览检查范围。参见[格式示例](docs/import-formats.md)。

## 数据与分析边界

资料、引用、修订和快照保存在本机 SQLite。应用不设账号、不默认上传或遥测；分析时仅将所选用户发言及候选发现发送到你配置的模型。预览中的批次数不等于供应商账单。前端、字体和示例无需 CDN。

AI 会话只是现实生活的一个侧面。候选发现等待本人审阅；不会生成智商、疾病诊断或人格/执行力排名。助手输出、引文、角色扮演与无依据的模型断言不能作为用户亲自陈述的证据。启发式分类和模型判断仍可能出错，请检查原文与情境。

删除会话后，为避免间接引用残留，当前资料空间内的生成洞察、修订、快照和分析缓存一并清除；剩余资料可重新分析。外部原始文件和你已经下载的导出文件不受应用删除操作影响。

## 开发与验证

需要 Python 3.10+、Node.js 22.12+。以下为源码安装；Windows 用 `.venv\Scripts\python.exe`，macOS/Linux 用 `.venv/bin/python`。

```sh
git clone https://github.com/wind127/selfdiff.git
cd selfdiff
python -m venv .venv
# 激活虚拟环境后执行
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.lock
python -m pip install --no-deps -e .
npm --prefix web ci
python scripts/build_release.py
python -m selfdiff.cli serve
```

```sh
python -m pytest -q
npm --prefix web run typecheck
cd web
npx playwright install chromium
npm run test:e2e
```

端到端测试使用独立临时资料与本机假 HTTP 模型，不使用你的真实模型密钥或私聊。测试验证应用流程与引用规则，**不等于真实供应商联通或个人分析质量已获验证**。

[开发说明](docs/development.md) · [贡献指南](CONTRIBUTING.md) · [MIT License](LICENSE)
