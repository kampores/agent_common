# 版本变更历史 (Changelog)

> [ 🇰🇷 한국어 (CHANGELOG_KR.md) ](CHANGELOG_KR.md) | [ 🇺🇸 English (CHANGELOG_EN.md) ](CHANGELOG_EN.md) | [ 🇨🇳 中文 (CHANGELOG_ZH.md) ](CHANGELOG_ZH.md) | [ 🇯🇵 日本語 (CHANGELOG_JP.md) ](CHANGELOG_JP.md)

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
