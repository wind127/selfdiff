# 开发与发布验证

后端位于 `src/selfdiff`，前端位于 `web/src`。标准来源模型由 `models.py` 定义；sources 只解析，store 管理版本与删除，evidence 校验原句，analysis 管理模型和持久任务，api 只暴露本人本机接口。

激活 Python 3.10+ 虚拟环境后：

```sh
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.lock
python -m pip install --no-deps -e .
npm --prefix web ci
python scripts/build_release.py
python -m selfdiff.cli serve --data-dir ./.local/dev-data
```

Windows 可直接用 `.venv\Scripts\python.exe` 替换命令中的 python，无需更改 PowerShell 执行策略。前端开发可在第二终端运行 `npm --prefix web run dev`；将 CLI 启动链接的 fragment 携带到 Vite 的本机地址，代理仅用于本机开发。正式发布使用打包后的同源页面。

## 自动检查

```sh
python -m pytest -q
npm --prefix web run typecheck
cd web
npx playwright install chromium
npm run test:e2e
cd ..
python scripts/build_release.py
python -m pip download -r requirements.lock -d .local/wheelhouse
python scripts/smoke_install.py dist
```

E2E 占用本机 8770（应用）与 8771（假模型），需要端口空闲。所有数据放在临时目录，替换继承的模型密钥为固定测试字符串，使用真实 HTTP 协议但不访问真实模型供应商。测试生成的示例截图位于 docs/images，不能用开发者个人会话替代。

`build_release.py` 构建 React 资源，再构建 wheel/sdist；`check_package.py` 检查资源、合成示例和私密路径排除；`smoke_install.py` 在全新 venv、源码目录之外运行安装包，检查 health、HTML、JS、CSS，不依赖 Node。若存在 `.local/wheelhouse`，安装检查离线安装依赖。

锁文件在 Python 3.10、Node 22 上解析。CI 验证 Windows/Linux 的 Python 3.10/3.12 后端与 Linux 的浏览器及安装包流程。依赖上游弃用警告与业务失败需分开记录，不应过滤掉业务错误。

## 贡献适配器

提交一个最小合成 fixture、明确格式出处与预期消息列表。优先检查角色、工具/压缩摘要、分支、重放、时间和稳定 ID，再增加 registry 入口与支持矩阵。没有公开可验证格式时只提供通用转换，不宣传原生全历史扫描。

## 发布

确认全部测试和独立审阅通过；核对 Git 追踪文件和发行包不含私聊、数据库、密钥、环境文件或个人绝对路径。推送后确认 CI，最后为已验证提交创建 tag/Release，附 wheel、sdist 与 SHA-256。不能以假模型测试代替真实供应商或分析质量验证。
