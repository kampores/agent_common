# 7.5. 推理结果与异常处理

[LLM 手册总览](01_unified_llm_client_zh.md)

> 配置准备与基础调用请首先参阅 [7.1 模型配置管理与文本生成](01_model_profiles_and_generation_zh.md)。

## 1. 返回值与异常处理

| 场景 | 当前运行行为 | 检查项 |
| :--- | :--- | :--- |
| 模型配置未注册 | 构造函数中抛出 `LlmInferenceError` | `llm_pool` 键名及模型选择配置 |
| 不支持的 provider | 抛出 `LlmInferenceError` | 确认是否为 `auto`、`external`、`local` 之一 |
| 外部服务禁用·API Key 缺失 | 外部路径返回 `None` | 启用配置与认证环境变量 |
| HTTP·URL 通信故障 | 抛出 `LlmInferenceError` | 服务端响应、地址、认证、网络 |
| 必需响应字段缺失 | 抛出 `LlmInferenceError` | 标准/Fabrix 格式与实际响应结构 |
| 本地文件不存在 | 返回 `None` | 基于项目根目录的文件路径 |
| 本地运行依赖未安装 | 模型文件存在时抛出 `LlmInferenceError` | 运行环境中的依赖安装情况 |
| JSON 解析、数字转换、部分超时·模型执行错误 | 原生异常可能会向上抛出 | 切勿假定仅凭 `LlmInferenceError` 即可捕获所有失败 |

调用方应用程序需明确区分 `None` 与异常的不同处理逻辑。在任务处理边界处，应优先捕获并处理显式预期的异常，最后捕获未预期的异常以决定是否继续后续任务。异常日志记录必须使用 `ProjectLogger` 的 `logger.exception`。
