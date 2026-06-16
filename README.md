# Hermes 使用说明

本仓库用于记录当前 Hermes 的主要使用方式、默认配置与后续调整约定。

## 当前主要使用方式

- 当前主要通过飞书接入 Hermes 使用。
- 后续默认也会优先通过飞书入口来使用 Hermes，方便团队在同一个协作工具内完成对话、调用和通知闭环。

## 已配置内容

- `config/hermes.yaml`：Hermes 的默认配置文件，包含飞书入口、token provider 与路由规则。
- `.env.example`：环境变量模板，用于放置飞书应用凭证、Codex token、GPT token 与默认 token 模式。
- `scripts/verify_hermes_config.py`：本地检查脚本，用于确认当前配置是否走 Codex/GPT，且没有误引入 Duojie API 配置。

## 现在怎么使用

1. 复制环境变量模板：

   ```bash
   cp .env.example .env
   ```

2. 在 `.env` 中填入飞书应用凭证和模型 token：

   ```bash
   FEISHU_APP_ID=你的飞书应用ID
   FEISHU_APP_SECRET=你的飞书应用密钥
   FEISHU_VERIFICATION_TOKEN=你的飞书事件校验token
   FEISHU_ENCRYPT_KEY=你的飞书事件加密key
   CODEX_TOKEN=你的Codex token
   GPT_TOKEN=你的GPT token
   HERMES_TOKEN_MODE=auto
   ```

3. 让 Hermes 服务启动时读取 `config/hermes.yaml` 和 `.env`。当前仓库只保存配置约定；实际启动命令需要放到 Hermes 服务所在项目里执行。
4. 在飞书里给 Hermes 机器人发送消息。如果是代码、repo、diff、PR 等任务，默认会按路由规则走 Codex；如果是文案、总结、翻译、对话等任务，会优先走 GPT。

## 怎么确认接入的是 Codex 而不是 Duojie API

可以从三个层面确认：

1. **看配置**：`config/hermes.yaml` 只配置了 `codex` 和 `gpt` provider，没有配置 `duojie` provider。
2. **看环境变量**：`.env.example` 只要求 `CODEX_TOKEN` 和 `GPT_TOKEN`，没有 `DUOJIE_API_KEY`、`DUOJIE_TOKEN` 或类似变量。
3. **跑检查脚本**：

   ```bash
   python scripts/verify_hermes_config.py
   ```

   如果输出里看到以下结果，就说明当前仓库配置默认选择 Codex，且没有发现 Duojie 相关配置：

   ```text
   default_provider=codex
   fallback_provider=codex
   codex_provider_configured=true
   duojie_reference_in_config=false
   duojie_env_present=false
   status=codex_selected
   ```

> 注意：这个脚本检查的是本仓库内的配置和当前 shell 环境变量。最终线上是否真的走 Codex，还要以 Hermes 服务运行时加载的配置、环境变量和请求日志为准。建议在线上日志里打印 `provider=codex`、`token_mode=auto|codex|gpt`，但不要打印真实 token。

## Token 默认策略

Hermes 的 token 默认可以走以下任一模型/服务入口：

- Codex
- GPT

默认配置中 `hermes.token.mode` 为 `auto`，表示 Hermes 会根据路由规则自动选择 Codex 或 GPT。如果后续需要固定某一种 token 来源，可以将配置改为：

```yaml
hermes:
  token:
    mode: codex # 或 gpt
```

也可以通过环境变量覆盖：

```bash
HERMES_TOKEN_MODE=codex
```

## 后续调整方式

1. 飞书作为默认交互入口，Hermes 负责统一承接请求。
2. Token 来源保持兼容 Codex 与 GPT，避免后续切换模型入口时需要改动飞书侧接入逻辑。
3. 如需区分不同场景，可在 `config/hermes.yaml` 的 `hermes.routing.rules` 中调整规则，例如：
   - 代码类任务优先走 Codex。
   - 通用对话、文案、总结或翻译任务优先走 GPT。
4. 如果某段时间希望所有请求都固定走一个入口，可以直接设置 `HERMES_TOKEN_MODE=codex` 或 `HERMES_TOKEN_MODE=gpt`。

## 已直接应用到本地 Hermes

如果你要直接使用本机 Hermes，可以执行：

```bash
python scripts/apply_local_hermes_config.py --target ~/.hermes
```

脚本会把本仓库的 `config/hermes.yaml` 写入 `~/.hermes/config/hermes.yaml`，并在没有 `.env` 时生成 `~/.hermes/.env`。如果目标配置已存在，脚本会先生成 `.bak.<timestamp>` 备份。写入后，本地 Hermes 应以 `~/.hermes` 作为 `HERMES_HOME` 启动，并继续在 `.env` 中填写真实飞书凭证和 Codex/GPT token。

本次默认应用结果是：

```text
provider_default=codex
provider_fallback=codex
duojie_configured=false
```

## 本地已填入的默认值

本地 `~/.hermes/.env` 现在会由脚本直接写入以下默认策略：

- `HERMES_TOKEN_MODE=codex`：强制本地 Hermes 走 Codex，避免误走 Duojie。
- `CODEX_BASE_URL`：优先使用当前 shell 的 `CODEX_BASE_URL`，没有时使用 `OPENAI_BASE_URL`。
- `CODEX_TOKEN`、飞书凭证、`GPT_TOKEN`：如果当前 shell 已经有同名环境变量，脚本会带入；否则保持为空，等待你填真实密钥。

如果你要重新把当前 shell 的值写进本地 Hermes，执行：

```bash
python scripts/apply_local_hermes_config.py --target ~/.hermes --force
```

## 启动 Gateway

是的，通过飞书接入 Hermes 时需要启动 gateway，因为飞书事件/消息需要先进入 gateway，再由 Hermes 按配置路由到 Codex/GPT。

本仓库提供了启动脚本：

```bash
HERMES_HOME=~/.hermes scripts/start_hermes_gateway.sh
```

脚本会读取 `~/.hermes/.env` 和 `~/.hermes/config/hermes.yaml`，然后优先执行 `hermes gateway --config ...`；如果本机没有 `hermes` 命令，则尝试 `gateway --config ...`。如果两个命令都不存在，说明当前环境还没有安装或暴露本地 Hermes gateway 可执行文件。
