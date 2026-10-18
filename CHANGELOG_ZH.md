# 版本变更历史 (Changelog)

> [ KO 한국어 (CHANGELOG_KO.md) ](CHANGELOG_KO.md) | [ EN English (CHANGELOG_EN.md) ](CHANGELOG_EN.md) | [ ZH 中文 (CHANGELOG_ZH.md) ](CHANGELOG_ZH.md) | [ JA 日本語 (CHANGELOG_JA.md) ](CHANGELOG_JA.md)

### v0.4.101 (2026-10-16)

- **`Localizer` 与 `ConfigLoader` 支持 BCP 47 标准连字符 ('-') 区域设置规范化 (遵循规则 1.1.3, 1.5.3, 4.2)**:
  - `Localizer.normalize_language`: 引入 BCP 47 标准连字符 (`-`) 分隔符及子标签/编码分离逻辑，准确将 `"en-US"`、`"ko-KR"`、`"zh-CN"`、`"ja-JP"` 等标准区域设置规范化为主语言代码。移除多余的 `str()` 防御性类型转换 (遵循规则 1.5.3)。
  - `Localizer.resolve_language`: 支持环境变量解析中的连字符 (`-`) 分割，解决标准环境变量下回退至默认语言的问题。
  - `ConfigLoader._resolve_logging_language`: 日志专用环境变量解析支持连字符 (`-`) 分割。
- **`Localizer` 支持大写后缀 (`_KO.yml`, `_EN.yml` 等) 与子目录 (`localize/{lang}/`) 资源查找 (遵循规则 1.4.4, 1.4.5, 4.2)**:
  - `Localizer.resolve_localized_file`: 通过不区分大小写的 `stem` 比较确保 Linux/Windows 跨平台文件查找一致性，并支持扫描语言子目录 (`localize/{lang}/`)。
- **多语言资源目录结构重构与组件解耦 (`localize/{ko,en,ja,zh}/`) (遵循规则 1.1.1, 1.1.2, 4.2)**:
  - 在 `agent_common/src/agent_common/localize/` 下建立独立语言子目录 (`ko`, `en`, `ja`, `zh`)，将通用日志模板 (`logging_messages_{lang}.yml`) 与进度跟踪器配置/标签 (`progress_tracker_{lang}.yml`) 彻底解耦为独立文件。
  - `ConfigLoader.get_settings()`: 自动遍历活跃语言目录下的所有 `.yml` 文件并进行深度合并 (deep merge)。
  - `pyproject.toml`: 更新 package-data 配置以确保 wheel 包含 `localize/**/*.yml` 目录资源。
- **`ProgressTracker` 彻底移除硬编码字典并接入外部多语言配置 (遵循规则 1.1.1, 1.1.2, 1.4.2, 4.2)**:
  - 彻底删除 Python 源码内部的硬编码语言字典 (`DEFAULT_TASK_NAMES_DICT`, `PROGRESS_LABELS_DICT`)。
  - 直接读取 `config.progress_tracker` 动态属性 (`default_task_name_str`, `milestone_title_str`, `progress_label_str`, `speed_label_str`, `unit_str`, `eta_label_str`)，实现实时本地化。
- **改进 `ProjectLogger.get_log_id_description()` 多语言模板标签解析 (遵循规则 1.1.3, 1.5.3, 4.2)**:
  - 预先去除圆括号 `()` 及补充说明，防止内嵌冒号导致错误截断。
  - 基于冒号 (`:`, `：`) 与标准句号 (`\.\s+`, `\.$`, `。`) 截断，避免破坏文件名后缀 (`config.yml`) 并精简标题。
  - 通过标准化多语言消息字典 (`logging_messages_{ko,en,ja,zh}.yml`) 4 大错误模板的标点规范（韩语/英语：`. `，日语/中文：`。`），废除特定语言硬编码正则表达式，干净剔除方括号标签 (`[...]`) 并保留 `{}` 占位符。
- **`ProjectLogger` 支持可选 `service_name_str` 实例绑定 (遵循规则 1.4.2, 1.6.1, 4.2)**:
  - 构造函数新增可选 (Optional) 参数 `service_name_str: str = ""`，支持为特定服务专用 Logger 预先绑定服务名。
  - `get_log_msg()` 与 `get_log_id_description()` 自动替换 `self.service_name_str`，提供完整且自然的摘要标签。
- **新增标准任务执行结果汇总报告器 (`StandardSummaryReporter`) 并轻量化解耦 `ProjectLogger` (遵循规则 1.1.1, 1.4.1, 1.4.2, 1.7.5, 4.2)**:
  - `ProjectLogger`: 遵循单一职责原则 (SRP) 进行轻量化重构，专注于核心日志记录与指标遥测 (`record_result`, `record_excluded`, `get_result_counts`, `get_error_counts`)。
  - `StandardSummaryReporter`: 新增独立专用工具类，通用保证“总计 = 成功 + 失败 + 跳过 (Skip)”三级分类一致性，并将详细错误分类生成为 80 列标准对齐表格。
  - 多语言标签与模板完全外部化: 联动 `agent_common/src/agent_common/localize/{ko,en,ja,zh}/summary_reporter_{lang}.yml` 字典，全面支持 4 种语言（中文、韩文、英文、日文），代码内部零硬编码 (遵循规则 1.1.1)。
  - 基于 `TableFormatter` 针对东亚全角字符精确对齐 80 列竖线边框，无缝支持 `ProgressTracker` 遥测数据联动（耗时、处理吞吐量、传输速率）。
  - 提供单行快速输出 `log_summary(logger_obj, ...)` 与格式化字符串获取 `build_summary_report(...)`。原有实现已安全归档至 `backup/log_summary/log_summary_backup.py`。
- **`LlmClient` 整合实例 Logger 与本地模型缓存结构 (遵循规则 1.4.1, 1.5.4, 4.2)**:
  - 将独立辅助函数 `_get_local_llm` 整合为内部实例方法 `self._get_local_llm(...)`，由类属性 `LlmClient._LOCAL_LLMS_DICT` 统一管理缓存，直接复用 `self.logger`。
- **`ConfigLoader` 环境变量清除时恢复原始配置并防止缓存污染 (遵循规则 1.3.1, 1.5.3, 4.2)**:
  - 保存 `_raw_configured_logging_language_str`，确保在临时环境变量被清除后能正确恢复至配置文件的原语言。
- **修正 `README.md` 示例中的虚构参数 (遵循规则 1.5.3, 4.2)**:
  - 纠正了 `ProgressTracker` 示例中不存在的 `item_name_str="파일"` 与未支持的 `log_summary()`，规范为 `task_name_str="파일 처리"` 与 `tracker.update(...)`。

### v0.4.100 (2026-10-12)

- **修正多语言消息目录英文模板键拼写错误 (遵循规则 4.2)**:
  - 将 `logging_messages_en.yml` 中的 `db_load_max_retceeded` 键更正为 `db_load_max_retries_exceeded`，使英文日志环境下超过重试次数的异常日志模板能够正常映射。
- **统一 `Localizer` 与 `ConfigLoader` 的语言解析逻辑并修复缺陷 (遵循规则 1.4.1、1.4.6、1.5.3、1.6.1、4.2)**:
  - `ConfigLoader._resolve_logging_language`: 解析日志专用环境变量 (`AGENT_LOG_LANGUAGE`, `LOGGING_LANGUAGE`) 时支持 POSIX Locale 格式 (例如 `en_US.UTF-8` -> `en`) 分割处理，确保与 `Localizer` 规范化逻辑一致。彻底移除模糊键匹配 (`language`, `lang` 回退查找)，严格仅查询正规键 `logging.language_str` (遵循规则 1.5.3)。
  - `Localizer.resolve_language`: 评估环境变量时预先校验 `LANGUAGE_ALIAS_DICT` 中是否存在该语言，防止传入不受支持的语言字符串时过早回退到默认语言导致后续环境变量被忽略。
  - 新增 `ConfigLoader.language_str` Getter/Setter 属性 (遵循规则 1.6.1)。解决 `ConfigLoader.language` 属性忽略全局与环境变量设置的问题，统一归口至 `_resolve_logging_language`。
  - `Localizer.resolve_localized_path_from_list`: 避免在查找默认语言 (`KO`) 时对相同后缀候选进行重复文件匹配。
  - 清理形式化的转发函数与转发属性 (遵循规则 1.4.6):
    - `ProjectLogger`: 全面移除仅简单转发至 `ConfigLoader` 的 `set_language`, `language_set`, `language_str`, `language` 壳方法与属性，专注于核心日志职责 (SRP)。
    - `Localizer`: 移除 `resolve_catalog_file`, `resolve_project_catalog_file` 转发包装函数。
    - `ConfigLoader`: 移除 `_resolve_language`, `_resolve_logging_messages_file`, `_resolve_project_logging_messages_file` 转发包装函数，直接调用 `Localizer` 实体方法。

### v0.4.99 (2026-10-06)

- **把 `BigQueryClient` DATETIME 转换的基准时区改为可配置 (遵循规则 1.1.1、1.3.1、4.2)**:
  - 新增配置 `bigquery.datetime_timezone_str` (默认值 `KST`): 写入 `DATETIME` 列的钟表时刻所依据的基准时区。可填写 `KST` 等时区缩写或 `+09:00` 形式的偏移量，为 `AUTO`/`SYSTEM` 时使用宿主系统的本地时区。
  - `convert_to_bigquery_datetime`: 带有偏移量的值不再换算为源代码中写死的 KST，而是换算为该配置所指定时区的时刻。默认值为 `KST`，因此不新增配置时结果与此前相同。
  - 在系统时间为 UTC 的环境 (如 Airflow Pod) 中把当前时间写入 `DATETIME` 列时，应传入带偏移量的 `DateTimeUtils.get_now_timestamp()` 的值，而不是不带偏移量的 `DateTimeUtils.get_now_no_tz()`，这样才会换算为基准时区的时刻。
  - 配置值在创建 `BigQueryClient` 时解析，因此格式不正确的值会在启动时以 `ValueError` 失败，而不是在处理数据行的过程中失败。
  - 在 `default_agent_common.yml` 与 `BigQueryClient.DEFAULT_SCHEMA_DICT` 中新增默认值。
  - 以 4 种语言更新手册 `3.5` 中的 DATETIME 时区处理说明，以及手册 `1.6` 中按类写入配置的表格。
- **修正 `BigQueryClient.merge_table_from_json_data` 中 `DATETIME`/`DATE`/`TIME` 列的转换表达式**:
  - 在 `column_types_dict` 中声明为 `DATETIME`、`DATE`、`TIME` 的列，改用 `CAST(JSON_VALUE(...) AS DATETIME)` 的形式转换，不再使用 `DATETIME(...)`、`DATE(...)`、`TIME(...)` 函数。这些函数不接受字符串表达式作为参数，因此从 JSON 中取出的字符串值必须用 `CAST` 转换。
  - `DATETIME` 等非字符串类型的列必须通过 `column_types_dict` 传入类型。不传入时字符串值会被推断为 `STRING`，MERGE 在赋值时会出现类型错误。

### v0.4.98 (2026-10-06)

- **分离 `GcsClient`、`BigQueryClient` 的认证阶段与连接阶段 (遵循规则 1.6.4、4.2，兼容性变更)**:
  - 构造函数先通过 `GcpCredentialResolver.resolve()` 完成认证，再把结果传给 `_connect(credentials_obj)` 进行连接。`_connect()` 的 `try` 块中只保留客户端创建以及存储桶、数据表的查询。
  - 兼容性: 认证阶段的异常 (`ImportError`、`ValueError`、`FileNotFoundError` 等) 不再被包装为 `ConnectionError`，而是以原始类型抛出。此前以 `ConnectionError` 捕获认证失败的代码需要修改。
  - 认证失败日志改由 `GcpCredentialResolver` 在抛出异常处记录一次，而不再由客户端记录。单独使用解析器时也会留下同样的日志，客户端不会重复记录。为此在解析器中新增 `self.logger`，并把 `_get_service_account` 由类方法改为实例方法 (模块缓存仍为类变量)。
  - 把源代码中以韩文书写的解析器异常消息移入日志消息字典 (4 种语言): `credential_package_missing` (`ImportError`)、`credential_json_invalid` (`ValueError`)、`credential_file_not_found` (`FileNotFoundError`)。异常消息随日志语言设置输出，认证失败的日志 ID 由 `connection_failed` 变为这三者之一。
  - 密钥文件不存在消息中的来源标注由 `config.yml 설정값` 改为参数名 `credentials_path_str`。
  - 以 4 种语言更新手册 `3.6` 的异常处理指南。
- **将 `S3Client.transfer_to_gcs` 的耗时日志合并到结果日志 (遵循规则 1.1.1、3.2、4.2)**:
  - 删除每个文件在结果日志之后单独输出的 `elapsed_time` 日志，把各阶段耗时 (`details_str`) 与传输上下文 (`context_info_str`) 一并写入结果日志。每个文件的日志由 2 行减为 1 行。
  - 删除源代码中以韩文书写的 `action_name_str` 值 ("GCS 파일 검사"、"GCS 파일 전송"、"GCS 파일 전송 오류")。此前即使日志语言设为 `EN`、`ZH`、`JA`，这一部分仍以韩文输出。
  - 新增模板 `transfer_completed_with_elapsed_time`、`transfer_skipped_with_elapsed_time`、`transfer_failed_with_elapsed_time`，即在原有句子末尾加上 `{details_str} {context_info_str}` 占位符 (4 种语言)。`transfer_to_gcs` 使用这三个日志 ID。
  - 原有的 `transfer_completed`、`transfer_skipped`、`transfer_failed` 模板保持不变。
  - 跳过日志中的 `Status=Skipped` 与消息正文重复，已删除。
  - 每次传输失败时 `transfer_to_gcs` 输出的 ERROR 日志由 2 条减为 1 条，失败累计次数相应减少；按错误类型的统计中显示 `transfer_failed_with_elapsed_time` 而不再是 `elapsed_time`。
  - `elapsed_time` 模板本身保留。
- **补充手册 `3.1` (遵循规则 4.2)**:
  - 按新的日志结构修改传输流程图中跳过步骤的说明 (韩文、英文、日文)。

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
