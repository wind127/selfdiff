# 快速开始

## 交给 AI 安装

将这段提示词复制给具备终端操作能力的 AI 助手：

```text
请帮我安装并启动 SelfDiff（https://github.com/wind127/selfdiff）。按当前系统和最新 README 准备 Python 3.10+ 和独立虚拟环境，安装最新 Release 的 wheel，启动本机服务并打开合成示例，最后给我访问地址和重启命令。
```

## 运行发布包

安装 Python 3.10+，从 [v0.1.1 Release](https://github.com/wind127/selfdiff/releases/tag/v0.1.1) 下载 `selfdiff-0.1.1-py3-none-any.whl`，在下载目录执行：

```sh
python -m pip install selfdiff-0.1.1-py3-none-any.whl
python -m selfdiff.cli serve
```

使用终端打印的完整本机链接。令牌位于 URL fragment，页面交换会话后会清除它。服务重启后旧会话失效，使用新的启动链接。

“体验示例”创建独立的虚构人物资料空间；“导入我的会话”进入你的真实资料空间。示例不需要模型，不读取你的聊天记录。

## 导入自己的资料

选择来源和文件，检查预览里的消息数、日期与警告，再“确认导入”。也可填写你明确选择的本机文件/目录。文件支持 JSON、JSONL、ZIP、Markdown、文本；单文件 50 MiB，ZIP 解压后 200 MiB、200 项。标准格式参见 [import-formats.md](import-formats.md)。

命令行先预览再导入，预览不创建数据库：

```sh
python -m selfdiff.cli import --source normalized --path ./example.json --data-dir ./.local/my-data --dry-run
python -m selfdiff.cli import --source normalized --path ./example.json --data-dir ./.local/my-data
python -m selfdiff.cli serve --data-dir ./.local/my-data --port 8765
```

`--workspace-id` 可指定现有资料空间。未指定时 CLI 使用首个非示例空间；没有时创建。

## 配置分析模型

在“模型设置”填写供应商兼容接口的基础地址（通常以 `/v1` 结尾）和模型 ID。地址需为 HTTPS；本机 `http://127.0.0.1:端口/v1` 也可以。密钥通过 `SELFDIFF_API_KEY` 环境变量提供，设置后重启服务。应用不提供密钥明文持久化。

先“保存并测试连接”；这只发送不含个人资料的测试请求，可能产生供应商费用。之后在“个人档案”选择来源和日期，点击“预览本次分析”，核对范围后启动。分析有提取和复核步骤，不同供应商的上下文限制、JSON 支持和收费方式不同。

发现均需本人审阅。查看引用、反例和情境，选择符合/部分符合/不符合，再补充自己的说法。资料不足不代表你缺少某种能力或人格特征。

## 常见情况

- 没有模型：仍可导入、搜索、删除；合成示例照常可用。
- 格式无法识别：核对来源选择；必要时转换为标准 JSON。没有发言人边界的文本不能直接分析。
- 模型不可达：检查模型名、地址、密钥环境、供应商 JSON 输出支持；原资料不受影响。
- 分析不完整：只把成功批次视为已覆盖，不能当成全部会话总结。可在检查模型后重试。
- 已取消/中断：不会自动继续付费请求。重试需本人再次启动。
- 删除资料：整个当前空间的派生结论会清空；原始外部文件仍在。
- 启动链接失效：使用同一浏览器已有会话，或重启服务获取新的链接；不要把链接发给他人。
