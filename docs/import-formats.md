# 导入格式与兼容范围

所有例子为合成内容。适配器是格式族适配，不是客户端版本认证或云端账户爬虫。

## 推荐的标准 JSON

```json
{
  "conversations": [{
    "id": "project-start-1",
    "title": "一次项目选择",
    "messages": [
      {"id": "m1", "role": "user", "content": "我想先验证一个真实场景。", "timestamp": "2026-01-05T09:00:00+08:00"},
      {"id": "m2", "role": "assistant", "content": "可以先确定一个小目标。"}
    ]
  }]
}
```

同一来源内稳定保留 conversation `id` 和 message `id`；重复导入不会重复累计。修改内容会保留新版本。时间可省略，但缺失或无时区的时间不参加时期比较。跨来源的相同文字不被自动合并。

豆包、DeepSeek、千问办公等先将本人选定的会话转换成这个格式。不要把第三方或文档里的话标成用户本人的发言。

## Markdown / 文本

使用明确的英文半角冒号发言边界，也支持 `用户:`、`助手:`：

```text
User: 我这次想先做一个可使用的小版本。
Assistant: 你可以先选一个场景。
User: 我愿意先找两个人试用。
```

没有边界标记的文本会显示待确认警告，不进入分析。建议转成带稳定 ID 的标准 JSON，避免文件改名引入新的资料身份。

## JSONL 格式族

- **Codex**：`session_meta.payload.id` 表示会话；`response_item.payload.type=message`，`role` 和 `content[{type:input_text|output_text,text}]` 为正文。存在规范消息轨道时不用 event_msg 重复计数；纯事件记录支持 user_message/agent_message。
- **Claude Code**：记录 `type=user|assistant`、`sessionId`、`uuid`、`message.role/content`；content 可为文本或 text 块。工具结果、isMeta、isCompactSummary 不作为本人经历。
- **WorkBuddy**：`type=message`，role/content 可在顶层或 message 内。没有可辨识文本的记录不纳入。
- **ChatGPT**：官方 `conversations.json` 列表，包含 mapping/current_node；只沿选中节点回溯父链，不拼接所有兄弟分支。
- **Claude 网页**：官方列表包含 uuid/name/chat_messages；每条含 sender（human/assistant）、text 或文本 content、created_at。

ZIP 中仅解析受支持的文本扩展名。官方网页导出只选择 `conversations.json`；附件、HTML、图片不解析。解析器不跟随 ZIP 链接，也不会把文件解压到用户目录。

测试格式的可执行示例见 `tests/test_sources.py`，标准输入与安全边界见 `tests/test_ingest.py`。平台导出字段可能变化；遇到未知结构请提供最小合成样例，切勿提交真实私聊。
