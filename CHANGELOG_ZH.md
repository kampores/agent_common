# 版本变更历史 (Changelog)

> [ KO 한국어 (CHANGELOG_KO.md) ](CHANGELOG_KO.md) | [ EN English (CHANGELOG_EN.md) ](CHANGELOG_EN.md) | [ ZH 中文 (CHANGELOG_ZH.md) ](CHANGELOG_ZH.md) | [ JA 日本語 (CHANGELOG_JA.md) ](CHANGELOG_JA.md)

### v0.4.97 (2026-10-05)

- **按类选择配置文件自动生成与自动补全的写入对象 (遵循规则 1.7.5、4.2，兼容性变更)**:
  - 新增配置 `config_loader.config_file_auto_repair_dict`: 以 `<类名>_bool` 形式的键 (例如 `BigQueryClient_bool`) 指定各类是否启用的字典。所有类默认均为 `false`，`ensure_config_file()` 仅把值为 `true` 的类的默认配置写入 `config.yml`。
  - 支持的类: `ConfigLoader`, `ProjectLogger`, `S3Client`, `GcsClient`, `GcpCredentialResolver`, `BigQueryClient`, `ProgressTracker`, `TableFormatter`, `ToolParser`, `LlmClient`。各类新增 `DEFAULT_SCHEMA_DICT` 类属性，用于保存要写入的默认配置。
  - 调用程序自身的 Schema (通过 `register_schema()` 注册或以 `default_schema` 传入) 仍然始终生成并补全。
  - 值按 `_bool` 后缀规则解析 (`true`/`false` 及等价字符串，其他值立即报错)。若已启用的键在 `agent_common` 中找不到对应的类，将记录警告日志 `config_auto_repair_unknown_class` 并跳过 (已添加 4 种语言的消息)。
  - 兼容性: 旧版本即使不使用 `LlmClient` 也会把 `llm`、`llm_pool` 自动写入 `config.yml`，现在不再写入。如有需要请设置 `LlmClient_bool: true`。
- **新增全局 Schema 注册方法 (遵循规则 1.5.4)**:
  - `ConfigLoader.register_schema_globally(schema_dict)`: 把传入的 Schema 注册到全局 Schema 注册表。`ReadOnlyConfig.register_schema()` 在三处调用了该方法，但 `agent_common` 中并未定义，进入这些分支时会抛出 `AttributeError`，现已修复。
  - `ConfigLoader.register_enabled_class_schemas_globally()`: 仅把在 `config_loader.config_file_auto_repair_dict` 中为 `true` 的类的 `DEFAULT_SCHEMA_DICT` 注册到全局。`ensure_config_file()` 会首先调用它，因此已启用类的默认配置同时作用于文件写入和运行时默认值。
  - 调用程序 Schema 已注册的值不会被类默认值覆盖。
- **将 LLM 默认配置移入包默认配置文件**:
  - 移除 `llm.py` 在导入时和 `LlmClient` 构造时通过 `register_schema()` 进行的全局注册，并在 `default_agent_common.yml` 中定义相同的值 (`llm.router_model_str`、`llm.sql_generator_model_str`、`llm.system_prompt_str`、`llm.default_purpose_str`)。运行时配置值不变。
- **按类拆分 `clients.py` 模块 Schema**:
  - 删除模块级 `APP_DEFAULT_SCHEMA_DICT`，拆分为 `S3Client`、`GcsClient`、`GcpCredentialResolver`、`BigQueryClient` 各自的 `DEFAULT_SCHEMA_DICT`。公共键 `transfer.timeout_seconds_int` 分别包含在三个客户端中。
  - 删除没有任何类读取的 `transfer.chunk_size_int`、`bigquery.max_retries_int`。
- **修正 `logger.py` 默认 Schema 中的 `logging.log_file_str`**:
  - 将与包默认配置 (`default_agent_common.yml`) 不一致的路径模板改为相同的值，避免启用 `ProjectLogger` 时写入与实际生效默认值不同的路径。
- **移除 `logging.level_dict` 查找中对无后缀键的回退 (遵循规则 1.5.3，兼容性变更)**:
  - `ProjectLogger.configure` 查找日志级别的顺序整理为两步: 先查 `<程序名>_str` 键，再查 `default` 键。不再识别无后缀的 `<程序名>` 键，需改为 `<程序名>_str`。
- **补充手册 `1.6` (遵循规则 4.2)**:
  - 在 4 种语言的手册中新增 `2.1` 节，说明按类选择的配置、各类写入的配置项以及首次运行时的应用方法。

### v0.4.96 (2026-10-04)

- **将语言标识统一为 ISO 639-1 语言代码 (遵循规则 1.1.3, 4.2，兼容性变更)**:
  - 将国家代码形式的 `KR`、`JP` 改为语言代码 `KO`、`JA`。`EN`、`ZH` 保持不变，支持的语言为 `KO`、`EN`、`ZH`、`JA`。
  - 默认语言及 `logging.language_str` 默认值由 `KR` 改为 `KO`。
  - 从 `Localizer` 中删除国家代码别名 (`KR`, `JP`, `CN`, `US`) 以及文件后缀交叉查找 (`kr`↔`ko`, `jp`↔`ja`, `zh`↔`cn`)。无法识别的值仍按原有方式回退到默认语言 `KO`，因此配置中使用 `JP` 的需改为 `JA`。
  - 文件名变更: `logging_messages_kr.yml` → `logging_messages_ko.yml`，`logging_messages_jp.yml` → `logging_messages_ja.yml`。
  - 文档路径变更: `manual/kr` → `manual/ko`，`manual/jp` → `manual/ja`（文件后缀 `_kr.md` → `_ko.md`，`_jp.md` → `_ja.md`），`CHANGELOG_KR.md` → `CHANGELOG_KO.md`，`CHANGELOG_JP.md` → `CHANGELOG_JA.md`，`AGENTS_KR.md` → `AGENTS_KO.md`，`AGENTS_DOCS_ENV_KR.md` → `AGENTS_DOCS_ENV_KO.md`。README 与 `pyproject.toml` 中的链接已同步更新。
- **新增 `Localizer` 手册并完善多语言文档 (遵循规则 4.2)**:
  - 以 4 国语言新增手册 `8.1 语言代码规范化与多语言资源文件查找` (`manual/*/localizer/01_language_codes_and_resource_lookup_*.md`)，并在 README 主要功能中新增 `8. 语言本地化器` 章节及手册目录条目。
  - 在手册 `2.3 多语言日志消息模板字典` 中补充 4 种语言的字典文件与日志语言决定优先级。
- **将文档中的 `agent_common.utils` 更正为实际模块路径 (遵循规则 4.2)**:
  - 将 README 与手册中指向不存在的 `agent_common.utils` 模块的写法改为 `agent_common.time_utils`、`agent_common.progress_tracker`、`agent_common.table_formatter`。
  - 将示例代码中运行时会引发 `ModuleNotFoundError` 的 `from agent_common.utils import ...` 改为 `from agent_common import ...`。
- **将语言跳转链接中的国旗表情替换为语言代码 (遵循规则 4.2)**:
  - 将 README 与 CHANGELOG 顶部语言跳转链接中的国旗表情（在部分环境中显示为国家代码 `KR`、`US`、`CN`、`JP`）替换为语言代码 `KO`、`EN`、`ZH`、`JA`。
  - 删除 README 各语言章节标题中的国旗表情，并将跳转锚点更新为与新标题一致（`#agent_common-软件包-中文` 等）。

### v0.4.95 (2026-10-04)

- **修正 `ProjectLogger.get_log_id_description` 局部变量名 (遵循规则 1.6.1, 1.6.2, 4.2)**:
  - 将缺少类型后缀且使用缩写的 `template_val` 改为与 `get_log_msg` 一致的 `template_str`。
  - 行为无变化。
- **将 SDK 延迟加载函数移入客户端类内部 (遵循规则 1.4.1, 4.2)**:
  - 将模块级函数 `_get_boto3`、`_get_gcs`、`_get_bigquery` 分别移入 `S3Client`、`GcsClient`、`BigQueryClient`，改为 `@classmethod`。
  - 将模块级缓存变量 (`_boto3_module`, `_boto_config_cls`, `_storage_module`, `_bigquery_module`, `_service_account_module`) 改为各类的类变量，并删除 `global` 声明。
  - 行为无变化。
- **新增并公开 GCP 认证解析专用类 `GcpCredentialResolver` (遵循规则 1.4.1, 1.4.7, 1.6.2, 4.2)**:
  - 删除模块级函数 `_resolve_gcp_credentials`，迁移至 `GcpCredentialResolver.resolve()`。4 级认证优先级保持不变。
  - `GcsClient`、`BigQueryClient` 通过组合 (Composition) 而非继承持有 `self.credential_resolver`，单独拆分任一客户端时不依赖另一个客户端。
  - 将 `google.oauth2.service_account` 的延迟加载统一到 `GcpCredentialResolver`。`GcsClient._get_gcs()`、`BigQueryClient._get_bigquery()` 不再返回元组，仅返回各自的模块。
  - 注册为公开 API (`from agent_common import GcpCredentialResolver`)，可在 GCS、BigQuery 之外的 GCP 服务中复用。
  - 整理缩写变量名: `val_str`, `cred_path`, `cred_err` → `env_credentials_path_str`, `credentials_file_path`, `credentials_error`。
  - 未安装 `google-auth` 时，`ImportError` 会在客户端 `_connect` 中被包装为 `ConnectionError`。
  - 新增 4 国语言手册 `3.6 GCP 服务账号认证解析器` (`06_gcp_credential_resolver_*.md`)，并同步更新 README 的主要功能、使用示例与手册目录。
- **移除 KST-as-UTC 时间戳模式 (遵循规则 4.2，兼容性变更)**:
  - 删除将本地时间数字以 `+00:00` 存储的 KST-as-UTC 模式。需要原样显示本地时间时，请使用 `DATETIME` 列与 `convert_to_bigquery_datetime`。
  - 已删除: 配置项 `bigquery.kst_as_utc_timestamp_bool`、属性 `BigQueryClient.kst_as_utc_timestamp_bool`、方法 `BigQueryClient.validate_and_sync_table_timestamp_mode()`。
  - 已删除的日志消息键: `table_timestamp_mode_legacy_warning`, `table_timestamp_mode_mismatch`, `table_get_failed`, `table_metadata_update_failed`。
  - `convert_to_bigquery_timestamp` 始终附带最终确定的时区偏移量返回（源数据自带值 → `default_tz_offset_str` → `timezone_offset_str` → 系统时区）。
- **全面修订手册 `3.5` 并整理文档编号 (遵循规则 4.2)**:
  - 将手册文件名由 `05_bigquery_timestamp_and_tz_sync_*.md` 改为 `05_bigquery_timestamp_and_datetime_conversion_*.md`，并围绕 `TIMESTAMP` 与 `DATETIME` 两个转换方法以 4 国语言重写，补充此前缺失的 `convert_to_bigquery_datetime` 规格与使用示例。
  - 将 README 主要功能中的 `3.6 BigQuery 标准 DATETIME 转换` 条目并入 `3.5`，使功能编号与手册文件 (01~06) 一一对应。

### v0.4.94 (2026-10-04)

- **修复 PyPI README 语言跳转锚点链接 (遵循规则 4.2)**:
  - 修复 v0.4.93 中 `#kr`、`#en`、`#zh`、`#jp` 链接失效的问题（原因: PyPI 渲染器会移除 HTML `<a id="...">` 标签的 `id` 属性）。
  - 沿用原先 KR/EN 已正常工作的方式，将 4 国语言链接统一为 Markdown 标题自动生成的锚点 (`#-agent_common-패키지-한국어`, `#-agent_common-package-english`, `#-agent_common-软件包-中文`, `#-agent_common-パッケージ-日本語`)。
  - 删除不再需要的 `<a id>` 标签。

### v0.4.93 (2026-10-04)

- **构建支持 PyPI 页面全览的 4 国语言一体化 README (遵循规则 4.2)**:
  - 针对 PyPI 仅渲染单个 README 文件的平台特性，将韩文 (KR)、英文 (EN)、中文 (ZH)、日文 (JP) 4 国语言文档完全整合至单个 `README.md` 文件（顺序: `kr` -> `en` -> `zh` -> `jp`）。
  - 配置顶部直达锚点导航 (`#kr`, `#en`, `#zh`, `#jp`)，并为所有用户手册建立 GitHub/PyPI 兼容的绝对 URL 链接体系。
  - 彻底清理冗余的 `README_*.md` 独立文件。
- **扩展 `pyproject.toml` 多语言项目链接 (`project.urls`) 至 4 国语言**:
  - 在 PyPI 侧边栏项目链接中，全面增补中文 (ZH) 与日文 (JP) 的变更历史 (`Changelog`) 及详细手册 (`Manual`) 链接。

### v0.4.92 (2026-10-04)

- **引入语言本地化模块 (`Localizer`) 并基于单一职责原则 (SRP) 解耦语言与日志配置 (遵循规则 1.4.1, 1.5.1, 4.2)**:
  - `Localizer`: 新增专门模块，负责多语言代码规范化、全局语言状态管理及通用多语言资源文件路径解析 (`resolve_localized_file`, `resolve_localized_path_from_list`)。
  - 从 `Localizer` 中彻底解耦并移除了 `logging` 配置字典、日志专用环境变量 (`AGENT_LOG_LANGUAGE`)、硬编码的 `logging_messages` 文件名及日志级别结构依赖。
  - `ConfigLoader`: 独立解析日志专用环境变量 (`AGENT_LOG_LANGUAGE`, `LOGGING_LANGUAGE`) 及 `logging.language_str` 配置 (`_resolve_logging_language`)，语言代码规整委托给 `Localizer`。
  - `ProjectLogger`: `APP_DEFAULT_SCHEMA_DICT` 默认日志语言确立为 `KR`，全权专责日志格式化、日志级别模板检索与摘要报表错误描述生成。
- **国家及语言代码规范统一 (`KR`, `JP`, `EN`, `ZH`)**:
  - 与使用手册路径 (`manual/kr/`, `manual/jp/`)、文件名 (`*_kr.md`, `*_jp.md`) 及 README (`README_KR.md`, `README_JP.md`) 保持严格一致，将默认语言代码从 `KO` 统一变更为 `KR`。
  - `default_agent_common.yml` 与 `config.yml` 中的 `logging.language_str` 默认值设置为 `KR`。
  - 新增 `logging_messages_kr.yml`、`logging_messages_zh.yml` 与 `logging_messages_jp.yml`，全面补齐 4 国语言 (KR, EN, ZH, JP) 标准日志消息模板。
  - 创建 `CHANGELOG_KR.md` 并更新所有文档的多语言导航栏，彻底消除 `KO` 重复文件。
- **独立发布模块 (`load_util.py`, `ig_gcs_bigquery_insert.py`) 语言固定为 `KR`**:
  - 在独立运行环境中将日志语言严格固定为 `KR`，精简多余的多语言判断分支与启发式代码。

### v0.4.91 (2026-10-03)

- **日志标准规范整理、消除外壳函数与模块同步 (遵循规则 1.3.1, 1.4.6, 1.5.3, 1.6.1, 4.2)**:
  - `logging.format_str`: 统一为 Python 标准 `LogRecord` 内置属性 (`%(asctime)s`, `%(levelname)s`, `%(name)s`, `%(filename)s:%(lineno)d`, `%(message)s`) 以及唯一自定义注入属性 `%(caller_str)s`。
  - `SingleLineFlattenFormatter`: 彻底永久删除重复拷贝 Python 标准属性的表面封装方法 `formatMessage` (遵循规则 1.4.6)。
  - `logging.log_file_str`: 将路径模板参数规范为标准类型后缀 `{app_name_str}` 与 `{log_level_str}`，彻底移除不必要的防御性大小写变体 (`APP_NAME`, `LOG_LEVEL`, `app_name`, `log_level`) 与临时变量。
  - 从 `_safe_log_record_factory` 和记录器属性中全面移除遗留非标别名 (`record.className`, `record.caller`, `fallback_class_name`)，统一为 `record.class_name_str`, `record.caller_str`, `fallback_class_name_str`。
  - `ProjectLogger.configure`: 彻底移除早期硬编码的第三方日志级别压制代码 (`metricflow`, `metricflow_semantics`, `urllib3`, `httpx`)。
  - 彻底使 `load_util.py` 与 `agent_common/logger.py` 保持 100% 同步，根除硬编码后备常量 (违背快速失败规则 1.3.1)。

### v0.4.90 (2026-10-01)

- **新增 `BigQueryClient.get_existing_records_metadata` 方法 (遵循规则 1.4, 1.5, 4.2)**:
  - 在 BigQuery 表中根据给定的主键 (PK) 列表快速批量查询元数据（状态码 `asstStusCd`、修改时间 `orignAmndHms` 等），并以 `{pk_str: {列名: 值}}` 字典格式返回。
  - 采用基于 `UNNEST(@pk_list)` 的 5,000 条分片批量查询架构，防止 BigQuery API 请求载荷超限 (HTTP 413)。
  - 严格对接预定义的标准日志模板 (`db_existing_records_loaded`, `existing_records_metadata_fetch_failed`)。

### v0.4.89 (2026-10-01)

- **配置加载器与包装递归函数过度资源消耗 (CWE-674) 防御 (遵循规则 1.3, 1.4, 4.2)**:
  - 为 `ReadOnlyConfig.register_schema` 与 `ReadOnlyConfig.apply_cli_overrides` 增加最大递归深度限制 (`max_depth_int=10`) 及显式基底条件提前返回 (Early Return)。
  - 在 `ConfigLoader._deep_merge` 和 `ConfigLoader._interpolate_env_vars` 内部递归逻辑中设定最大探测深度 (`max_depth_int=20`)，彻底杜绝栈溢出与死循环隐患。

### v0.4.88 (2026-10-01)

- **新增 `BigQueryClient.convert_to_bigquery_datetime` 方法 (遵循规则 1.4, 4.2)**:
  - 针对 BigQuery `DATETIME` 类型规范，将多种格式的源时间字符串（ISO 8601、空格分隔、14位/8位数字）转换为标准墙上时间 (`YYYY-MM-DD HH:MM:SS`)。
  - 剔除会导致解析错误的显式时区偏移，并将带时区的数据规范化转换为韩国标准时间 (KST) 后写入。

### v0.4.87 (2026-10-01)

- **根除 `_SafeNamespace` 无限递归 (`RecursionError`) 缺陷 (遵循规则 1.3, 1.4, 4.2)**:
  - 解决 `_SafeNamespace.__getattr__` 调用 `hasattr(self, "_data")` 时因缺少属性而循环触发 `__getattr__` 导致的栈溢出崩溃。
  - 全面切换为直接访问 `self.__dict__.get("_data")`，并在实例初始化时显式设置默认属性 `self._data = None`。

### v0.4.86 (2026-10-01)

- **`SingleLineFlattenFormatter` 与日志层单一职责原则 (SRP) 解耦 (遵循规则 1.4.1, 4.2)**:
  - 将原本混合在 `SingleLineFlattenFormatter` 内的调用栈检索与 `caller` / `className` 提取逻辑完全移交至日志工厂层 (`_safe_log_record_factory`)。
  - 确保生成 `LogRecord` 时始终填充 `caller` 与 `className`，防止格式化器因缺失字段引发 `KeyError`。
  - `SingleLineFlattenFormatter` 纯粹专注于换行符扁平化 (`\n` -> 空格) 与最终字符串格式化。

### v0.4.85 (2026-10-01)

- **新增 `TimeUtils.format_elapsed_time` 耗时格式化实用方法 (遵循规则 1.4, 4.2)**:
  - 将秒级任务耗时转换为高可读性时间字符串（例如: `1h 23m 45.67s`, `2m 15.30s`, `4.25s`）。

### v0.4.84 (2026-09-30)

- **`_SafeNamespace(dict)` 整合与全面贯彻快速失败 (遵循规则 1.5.3, 1.4.6, 4.2)**:
  - 移除大小写模糊匹配和缺失键静默返回空字符串的防御逻辑，缺失字段时显式抛出 `AttributeError` / `KeyError`。
  - 将其重构为继承自 `dict` 的映射类，统一兼顾局部变量字典与点号属性访问。
  - 在 `agent_common` 顶层包中正式公开 (`__all__`)，避免应用端重复声明。

### v0.4.83 (2026-09-29)

- **消除 `utils.py` 循环引用缺陷，基于单一职责原则拆分模块 (`time_utils.py`, `progress_tracker.py`, `table_formatter.py`)**:
  - `TimeUtils`: 专职系统本地时区动态探测、全球标准时区解析与日期解析的核心基础设施模块。
  - `ProgressTracker`: 专职批处理实时进度跟踪、速率与 ETA 估算、里程碑警报记录的模块。
  - `TableFormatter`: 专职 Markdown 与控制台表格全角/半角对齐的格式化模块。
  - 规范模块导入路径，彻底清除遗留模块反向引用。

### v0.4.82 (2026-09-28)

- **新增输入参数与日期校验标准日志模板 (`validation` 分组)**:
  - `invalid_date_format`: 日期格式错误提示 (`key_str`, `val_str`, `message_str`)。
  - `invalid_date_range`: 日期范围错误提示 (`start_date_str`, `end_date_str`, `message_str`)。
- **正式注册配置文件自动生成/校正与 BigQuery 表元数据日志模板**:
  - `config_auto_create_failed`, `config_auto_repair_failed`: 配置自愈失败模板。
  - `table_get_failed`, `table_metadata_update_failed`, `table_timestamp_mode_mismatch`: 表元数据模板。
  - `storage_clean_failed`: 统一为基于 `storage_type_str` 的通用清理键。
- **统一所有日志占位符与函数入参的显式类型后缀 (`_str`, `_int` 等)**。

### v0.4.81 (2026-09-28)

- **新增表级 `WRITE_TRUNCATE` 倒计时警报及分块批量加载通用日志模板**:
  - `table_truncate_countdown`, `table_truncate_tick`, `table_truncate_countdown_completed`: 防大面积数据误删倒计时模板。
  - `db_bulk_load_batch_started`, `db_bulk_load_batch_completed`: 海量行分块批量加载追踪模板。

### v0.4.80 (2026-09-23)

- **BigQueryClient 新增基于 WHERE 条件的安全删除方法 (`delete_rows`)**:
  - 支持执行 `DELETE FROM ... WHERE ...` DML 并返回受影响行数 (`affected_rows_int`)。
  - **全表清空防御 (Fail-Safe)**: 传入空条件或恒真条件 (`1=1`, `TRUE`, `''=''`) 时立即抛出 `ValueError` 阻断执行。

### v0.4.78 (2026-09-21)

- **AI 研发请求指引及统一 LLM 客户端用户手册**:
  - 增加向 AI 表达需求、PyPI/GitHub 链接与功能编号的提示词示例。
  - 新增统一 LLM 客户端双语手册，全面涵盖配置、外部 API、本地 GGUF、环境变量覆盖与异常处理。
  - 规范 Groq 监督员 AI 与 Antigravity Stop 钩子审查规范。

---

更早期的历史版本记录请参阅 [CHANGELOG_KR.md](CHANGELOG_KR.md) 或 [CHANGELOG_EN.md](CHANGELOG_EN.md)。
