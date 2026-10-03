# agent_common (中文)

**[📦 PyPI 软件包](https://pypi.org/project/agent-common/) · [💻 GitHub 源码与用户手册](https://github.com/kampores/agent_common)**

> [ 🇰🇷 한국어 (README_KR.md) ](README_KR.md) | [ 🇺🇸 English (README_EN.md) ](README_EN.md) | [ 🇨🇳 中文 (README_ZH.md) ](README_ZH.md) | [ 🇯🇵 日本語 (README_JP.md) ](README_JP.md)

---

## 🇨🇳 agent_common 软件包概览

面向企业级智能体（Agent）服务与数据迁移/生成管道的通用 Python 核心库，提供统一日志记录、分层配置加载、云端与数据库基础设施客户端、动态工具解析器及集中异常处理。

---

### 📌 核心功能

#### 1. 配置加载器与不可变配置对象 (`agent_common.config_loader`)
- **1.1. [分层 YAML 解析与深度合并 (Deep Merge)](manual/zh/config_loader/01_hierarchical_yaml_merge_zh.md)**: 动态合并包内置默认配置 (`agent_common/config/*.yml`) 与各独立项目配置 (`config/*.yml`)。
- **1.2. [不可变点属性访问 (`ReadOnlyConfig`)](manual/zh/config_loader/02_readonly_dot_notation_zh.md)**: 直观的点操作符属性访问 (`config.ecs.endpoint_url`, `config.transfer.max_workers_int`)，彻底杜绝运行时配置意外篡改。
- **1.3. [基于类型后缀的自动类型转换与类型保证](manual/zh/config_loader/03_type_coercion_and_guarantee_zh.md)**:
  - `_int`: 自动整型转换与类型保证。
  - `_float`: 自动浮点型转换与类型保证。
  - `_bool`: 严格布尔型转换与类型保证（支持 Python `bool` 或不区分大小写的 `"true"`/`"false"`，传入 `0`、`1` 等非布尔值时快速失败拦截）。
  - `_str`: 自动字符串转换与 `.strip()` 空格清理。
  - `_list` / `_dict`: 保证列表 / 不可变字典 (`ReadOnlyConfig`) 包装。
  - 提供独立函数 `coerce_type_by_key_suffix` 与嵌套字典批量转换 `coerce_dict_by_key_suffix`，全面支持任意外部配置文件 (`rule.yml`, `mapping.yml`) 和数据流。
  - 严格快速失败 (Fail-Fast) 保证：类型不匹配时立即抛出详细诊断异常 (`ValueError`/`TypeError`)，绝不静默降级为原始值。
- **1.4. [快速失败必需配置验证 (`require_setting()`)](manual/zh/config_loader/04_fail_fast_require_setting_zh.md)**: 程序启动阶段若缺少必要配置项，立即输出详细诊断日志并安全终止进程。
- **1.5. [网络代理控制 (`_apply_no_proxy`)](manual/zh/config_loader/05_network_proxy_control_zh.md)**: 自动将 `proxy.no_proxy` 配置同步至 `NO_PROXY` 环境变量，绕过内部通信代理。
- **1.6. [常量外部化与自愈模板校正 (`ensure_config_file()`)](manual/zh/config_loader/06_ensure_config_self_healing_zh.md)**: 将代码中所有常量外部化为配置文件，自动生成 `config.yml` 并强制注入/补齐缺失的配置键。

#### 2. 单行日志格式化器与项目日志器 (`agent_common.logger`)
- **2.1. [单行扁平化格式化器与源头位置追踪 (`SingleLineFlattenFormatter`)](manual/zh/logger/01_single_line_flatten_formatter_zh.md)**: 扁平化多行日志与 Traceback 异常，提取 `[Origin: ...]` 根源调用栈，针对集中式日志收集器（Logstash、Fluentd、CloudWatch）优化。
- **2.2. [批量日志环境配置与处理器控制 (`ProjectLogger.configure`)](manual/zh/logger/02_project_logger_configure_zh.md)**: 控制台与文件日志处理器动态创建，按日期分目录归档，按执行日志级别自动分流 (`{log_level_str}` 统一日志路径)。
- **2.3. [多语言日志消息字典与基于代码的日志记录 (`logging_messages_*.yml`)](manual/zh/logger/03_multilingual_message_catalog_zh.md)**: 依据配置自动联动中文/英文/韩文消息字典，支持运行时动态语言切换与安全的模板占位符替换。
- **2.4. [任务进度统计与异常/跳过分类实时汇总 (`record_result`)](manual/zh/logger/04_execution_result_and_error_tracking_zh.md)**: 成功、失败、跳过 (Skip) 三级状态分类，支持实例级与类全局多线程遥测。
- **2.5. [自动生成任务执行总结报告 (`log_summary`)](manual/zh/logger/05_summary_report_generation_zh.md)**: 确保“总计 = 成功 + 失败 + 跳过”严格一致，自动生成对齐的标准 Markdown 表格，包含耗时、处理吞吐量、传输速率与错误诊断。

#### 3. 存储与数据库基础设施客户端 (`agent_common.clients`)
- **3.1. [AWS S3 与 Dell ECS 对象存储客户端 (`S3Client`)](manual/zh/clients/01_s3_ecs_storage_client_zh.md)**: 连接 AWS S3 及 Dell ECS（S3 兼容）存储，初始化即执行 `head_bucket` 快速失败校验，海量对象分页迭代器 (`list_objects`)，元数据快速查询 (`get_object_size`)，流式读取 (`get_object_stream`)，GCS 实时流式传输与相同文件智能跳过 (`transfer_to_gcs`)。
- **3.2. [Google Cloud Storage 流式客户端与多层级认证 (`GcsClient`)](manual/zh/clients/02_gcs_cloud_storage_client_zh.md)**: 4 级 GCP 认证回退体系 (`GOOGLE_APPLICATION_CREDENTIALS_JSON` 内存 JSON -> `GOOGLE_APPLICATION_CREDENTIALS` 文件 -> `credentials_path_str` -> Google ADC)，存储桶连通性早验，分块流式上传零临时文件占用 (`upload_stream`)。
- **3.3. [BigQuery 批量加载与流式插入客户端 (`BigQueryClient`)](manual/zh/clients/03_bigquery_batch_and_streaming_load_zh.md)**: 快速失败架构与表元数据缓存 (`get_table`)，JSON 批量加载作业 (`load_table_from_json_data`) 深度展开嵌套错误，实时流式写入 (`insert_rows_json_data`)，同步 SQL 查询 (`query`)，防重唯一键集合提取 (`get_existing_keys`)。
- **3.4. [BigQuery 高性能内联 MERGE (Upsert) 引擎 (`merge_table_from_json_data`)](manual/zh/clients/04_bigquery_inline_merge_upsert_zh.md)**: 无需临时暂存表，基于 `UNNEST(JSON_QUERY_ARRAY(@json_payload))` 执行内联 MERGE INTO，主键自动更新/插入，保留初始列值 (`preserve_columns_list`)，列类型推断与显式转换，防 HTTP 413 载荷超限默认 100 行自动切片。
- **3.5. [BigQuery 时区偏移转换与表时区模式校验·同步 (`convert_to_bigquery_timestamp`)](manual/zh/clients/05_bigquery_timestamp_and_tz_sync_zh.md)**: 将各类源日期字符串规范化为标准 BigQuery 时间戳，时区偏移优先级 (`timezone_offset_str`)，韩国时间保持模式 (`kst_as_utc_timestamp_bool`)，表元数据自动同步与不匹配快速失败拦截。

#### 4. 动态工具加载器与模板评估器 (`agent_common.tool_parser`) & 内置工具 (`agent_common.tool`)
- **4.1. [双层 Tool 目录层级发现与动态加载 (`ToolParser.load_tool_function`)](manual/zh/tool_parser/01_dual_tool_hierarchy_discovery_zh.md)**:
  - **优先级 1 (内置工具)**: `agent_common/tool/` 下属模块（企业标准内置工具）。
  - **优先级 2 (项目工具)**: `config.yml` 中 `transfer.tool_dir_str` 指定的本地路径（如 `medallion/tool/`）。
- **4.2. [声明式模板替换与表达式评估 (`ToolParser.eval`)](manual/zh/tool_parser/02_declarative_template_eval_zh.md)**:
  - 变量命名空间绑定: `{ecs.key}`, `{sys.today}`, `{json.title}`。
  - 动态工具函数调用: `"{code.date_check_to_code(contentInfo.enddate)}"`, `"{path.get_json_name(ecs.key)}"`.
  - 管道符 (`|`) 链式降级与默认值: `"{meta.title|json.title|'默认标题'}"`.
- **4.3. [安全命名空间导航 (`_SafeNamespace`)](manual/zh/tool_parser/03_safe_namespace_navigation_zh.md)**:
  - 点 (.) 与中括号索引统一访问，不区分大小写，缺失键返回 `""` 避免 `KeyError`，嵌套集合安全递归包装。
- **4.4. [内置通用日期时间工具 (`DateTimeUtils`)](manual/zh/tool_parser/04_builtin_datetime_utils_zh.md)**:
  - 表规则与模板评估专用日期工具，时区核心运算委托给 `TimeUtils` 协同分工。

#### 5. 进度跟踪器、表格格式化器与时间工具 (`agent_common.utils`)
- **5.1. [主机系统时区探测、全球标准时区解析与日期规范化 (`TimeUtils`)](manual/zh/utils/01_time_utils_and_timezone_resolution_zh.md)**: 动态自动探测主机系统时区，解析全球 30+ 常见标准时区缩写，计算 ISO 8601 偏移量，提供时区感知转换核心 `parse_datetime`。
- **5.2. [多线程实时进度跟踪与里程碑警报 (`ProgressTracker`)](manual/zh/utils/02_progress_tracker_and_milestones_zh.md)**: 多线程实时进度跟踪 (`[N/Total] (P%)`)，处理吞吐量与预计剩余时间 (ETA) 计算，常规 `INFO` 与 10% 整数倍里程碑 `WARNING` 升级记录。
- **5.3. [Unicode 全角字符宽度计算与 Markdown/控制台表格对齐格式化器 (`TableFormatter`)](manual/zh/utils/03_unicode_table_formatter_zh.md)**: 基于东亚字符宽度 (`unicodedata.east_asian_width`) 精确计算，实现汉字/全角(2格)与英文(1格)在控制台与 Markdown 表格中的对齐。

#### 6. 通用错误与异常处理器 (`agent_common.error_handler`)
- 提供网络中断、配置缺失及运行时异常的一致日志记录与规范处理。

#### 7. 统一 LLM 客户端与推理引擎 (`agent_common.llm`)
- **7.1. [模型配置文件管理与文本生成](manual/zh/llm/01_model_profiles_and_generation_zh.md)**
- **7.2. [外部聊天 API 与 Fabrix 集成](manual/zh/llm/02_external_api_and_fabrix_zh.md)**
- **7.3. [本地 GGUF 推理与模型缓存](manual/zh/llm/03_local_gguf_inference_zh.md)**
- **7.4. [执行模式与条件化本地切换](manual/zh/llm/04_provider_and_local_fallback_zh.md)**
- **7.5. [推理结果与异常处理](manual/zh/llm/05_inference_results_and_errors_zh.md)**
- **7.6. [Groq 监督员 AI 与 Antigravity Stop 钩子](manual/zh/llm/06_groq_supervisor_and_stop_hook_zh.md)**

---

### 🛠️ 使用示例 (Usage Examples)

#### 1. 点属性访问全局 `config` 与类型保证
```python
from agent_common.config_loader import config

# 1) 基于类型后缀自动强制转换保证
max_workers: int = config.transfer.max_workers_int       # 保证 int 类型
host: str = config.database.host_str                     # 保证 str 类型并自动执行 .strip()
is_active: bool = config.transfer.is_active_bool         # 保证 bool 类型

# 2) 分层属性点访问
api_url: str = config.services.api_endpoint_url
db_port: int = config.database.port_int
```

#### 2. 通过 ToolParser 动态评估规则
```python
from agent_common.tool_parser import ToolParser

# 初始化 ToolParser (自动发现内置工具与项目工具)
tool_parser = ToolParser()

# 准备上下文上下文映射字典
context_dict = {
    "storage": {"key": "/data/incoming/20260804/sample_document.json"},
    "document": {"expiry_date": "2024-12-31"},
    "sys": tool_parser.build_sys_context(),
}

# 1) 评估工具函数调用模板
date_val = tool_parser.eval("{date.get_today_yyyymmdd()}", context_dict)

# 2) 评估系统命名空间与日期模板
today_val = tool_parser.eval("{sys.today}", context_dict)
```

#### 3. 使用 ProgressTracker 实时追踪进度
```python
from agent_common.utils import ProgressTracker
from agent_common.logger import ProjectLogger

logger = ProjectLogger("MyTask")
tracker = ProgressTracker(total_items_int=1000, logger_obj=logger, item_name_str="文件")

for file_info in file_list:
    try:
        # 处理业务逻辑
        tracker.increment_success(bytes_int=len(data))
    except Exception as e:
        tracker.increment_failure(error_msg_str=str(e))

# 输出最终总结报告
tracker.log_summary()
```

#### 4. 使用 LlmClient 进行统一文本/SQL生成
```python
from agent_common.llm import LlmClient

# 1) 按指定目的或模型初始化客户端
llm_client = LlmClient(purpose_str="sql_generator")

# 2) 调用所选配置的提供商进行生成
prompt_str = "用户需求: 请编写统计 2026 年 8 月每日新增订阅用户数的 SQL 查询。"
response_str = llm_client.generate(
    prompt_str=prompt_str,
    system_prompt_str="你是一名精通 BigQuery SQL 编写的专业 AI 助手。"
)

print(f"生成结果 ({llm_client.last_generated_by_str}):\n{response_str}")
```

#### 5. 存储与 BigQuery 客户端操作示例
```python
from agent_common.clients import S3Client, GcsClient, BigQueryClient

# S3 -> GCS 智能流式传输 (相同文件自动跳过)
s3_client = S3Client(bucket_name_str="source-lake")
gcs_client = GcsClient(bucket_name_str="target-lake")

for obj in s3_client.list_objects(prefix_str="raw/events/"):
    s3_client.transfer_to_gcs(
        gcs_client_obj=gcs_client,
        s3_key_str=obj["Key"],
        gcs_blob_name_str=f"lake/{obj['Key'].lstrip('/')}",
        size_int=obj["Size"],
    )

# BigQuery 高性能内联 MERGE (Upsert)
bq_client = BigQueryClient(project_id_str="my-project", dataset_id_str="dw", table_id_str="tb_user")
bq_client.merge_table_from_json_data(
    json_data_any=[{"user_id": "U01", "name": "张三", "created_at": "2026-01-01 00:00:00+09:00"}],
    pk_key_str="user_id",
    preserve_columns_list=["created_at"],
)
```

---

### 📖 详细功能用户手册 (User Manuals)

| 编号 | 模块 / 主题 | 详细手册链接 | 核心要点说明 |
| :---: | :--- | :---: | :--- |
| **1.1** | **分层 YAML 解析 & 深度合并** | [01_hierarchical_yaml_merge_zh.md](manual/zh/config_loader/01_hierarchical_yaml_merge_zh.md) | 5 阶段配置加载合并顺序，递归 `_deep_merge` 算法，项目根目录自动探测 |
| **1.2** | **不可变点属性访问 (`ReadOnlyConfig`)** | [02_readonly_dot_notation_zh.md](manual/zh/config_loader/02_readonly_dot_notation_zh.md) | 点属性操作符访问，严格杜绝运行时篡改 (Read-Only)，不可变结构设计 |
| **1.3** | **类型后缀自动转换 & 类型安全保证** | [03_type_coercion_and_guarantee_zh.md](manual/zh/config_loader/03_type_coercion_and_guarantee_zh.md) | `_int`, `_float`, `_bool`, `_str`, `_list`, `_dict` 运行时自动类型转换及安全保证 |
| **1.4** | **快速失败必需配置验证** | [04_fail_fast_require_setting_zh.md](manual/zh/config_loader/04_fail_fast_require_setting_zh.md) | 启动阶段检测缺失配置，输出清晰诊断日志并即时中止进程 |
| **1.5** | **网络代理控制** | [05_network_proxy_control_zh.md](manual/zh/config_loader/05_network_proxy_control_zh.md) | 自动将 `proxy.no_proxy` 配置同步至 `NO_PROXY` 环境变量并绕过代理 |
| **1.6** | **常量外部化与自愈模板校正** | [06_ensure_config_self_healing_zh.md](manual/zh/config_loader/06_ensure_config_self_healing_zh.md) | 代码中所有常量配置化（外部化），自动生成 `config.yml` 并强制注入缺失配置项 |
| **2.1** | **单行扁平化格式化器 & 根源追踪** | [01_single_line_flatten_formatter_zh.md](manual/zh/logger/01_single_line_flatten_formatter_zh.md) | `SingleLineFlattenFormatter`，`[Origin: ...]` 堆栈调用帧提取，适配日志收集器 |
| **2.2** | **批量日志配置 & 处理器控制** | [02_project_logger_configure_zh.md](manual/zh/logger/02_project_logger_configure_zh.md) | `ProjectLogger.configure()`，控制台/文件处理器动态分配，按日志级别路径归档 |
| **2.3** | **多语言消息字典 & 基于代码的日志** | [03_multilingual_message_catalog_zh.md](manual/zh/logger/03_multilingual_message_catalog_zh.md) | `logging_messages_*.yml`，运行时语言平滑切换，`safe_kwargs` 安全模板占位符 |
| **2.4** | **执行结果统计 & 错误分类实时汇总** | [04_execution_result_and_error_tracking_zh.md](manual/zh/logger/04_execution_result_and_error_tracking_zh.md) | 成功/失败/跳过 (Skip) 三级状态分类，实例与类全局多线程统计指标汇总 |
| **2.5** | **任务执行总结报告自动生成** | [05_summary_report_generation_zh.md](manual/zh/logger/05_summary_report_generation_zh.md) | `ProjectLogger.log_summary()`，80 列标准对齐摘要块，吞吐量/带宽，错误归因解析 |
| **3.1** | **AWS S3 & Dell ECS 存储集成** | [01_s3_ecs_storage_client_zh.md](manual/zh/clients/01_s3_ecs_storage_client_zh.md) | S3/ECS 连接连通性早验，海量对象分页遍历，流式直传 GCS 与相同文件跳过 |
| **3.2** | **GCS 流式上传 & 4 级认证体系** | [02_gcs_cloud_storage_client_zh.md](manual/zh/clients/02_gcs_cloud_storage_client_zh.md) | 4 级服务账号凭证优先级，连接验证，元数据获取，零磁盘暂存分块流式上传 |
| **3.3** | **BigQuery 批量加载 & 流式插入** | [03_bigquery_batch_and_streaming_load_zh.md](manual/zh/clients/03_bigquery_batch_and_streaming_load_zh.md) | JSON 批量加载 vs 流式 API，嵌套错误解包，防重已有唯一键集合提取 |
| **3.4** | **BigQuery 内联 MERGE (Upsert) 引擎** | [04_bigquery_inline_merge_upsert_zh.md](manual/zh/clients/04_bigquery_inline_merge_upsert_zh.md) | 无需中间临时表的内联 MERGE，UNNEST 参数化绑定，动态类型转换，100 条分片 |
| **3.5** | **BigQuery 时区转换 & 模式校验·同步** | [05_bigquery_timestamp_and_tz_sync_zh.md](manual/zh/clients/05_bigquery_timestamp_and_tz_sync_zh.md) | ISO 与压缩日期字符串规范化，UTC/KST 模式，表元数据自动同步与快速失败拦截 |
| **4.1** | **双层 Tool 目录结构发现 & 动态加载** | [01_dual_tool_hierarchy_discovery_zh.md](manual/zh/tool_parser/01_dual_tool_hierarchy_discovery_zh.md) | 内置 (优先 1) 与项目本地 (优先 2) 发现机制，3 阶段函数内省，`_tool_cache` 预校验 |
| **4.2** | **声明式模板替换 & 表达式评估** | [02_declarative_template_eval_zh.md](manual/zh/tool_parser/02_declarative_template_eval_zh.md) | `ToolParser.eval()`，工具函数直调，点号命名空间绑定，管道符 (`\|`) 兜底降级 |
| **4.3** | **安全命名空间导航 (`_SafeNamespace`)** | [03_safe_namespace_navigation_zh.md](manual/zh/tool_parser/03_safe_namespace_navigation_zh.md) | 点/中括号通用解析，不区分大小写，缺字段静默返回 `""`，递归封装嵌套容器 |
| **4.4** | **内置通用日期时间工具 (`DateTimeUtils`)** | [04_builtin_datetime_utils_zh.md](manual/zh/tool_parser/04_builtin_datetime_utils_zh.md) | 规则与模板专用日期工具，时区底层计算委托 `TimeUtils`，生成 ISO 与紧凑日期 |
| **5.1** | **主机时区探测 & 全球标准时区解析** | [01_time_utils_and_timezone_resolution_zh.md](manual/zh/utils/01_time_utils_and_timezone_resolution_zh.md) | `TimeUtils`，动态探测系统/容器时区，解析全球 30+ 标准时区，datetime 规范化 |
| **5.2** | **多线程实时进度跟踪 & 里程碑记录** | [02_progress_tracker_and_milestones_zh.md](manual/zh/utils/02_progress_tracker_and_milestones_zh.md) | `ProgressTracker`，实时百分比 (`%`)、吞吐率、预计剩余时间，`WARNING` 里程碑 |
| **5.3** | **Unicode 全角字符宽度计算与表格对齐** | [03_unicode_table_formatter_zh.md](manual/zh/utils/03_unicode_table_formatter_zh.md) | `TableFormatter`，基于 `east_asian_width` 计算，汉字全角(2格)与英文(1格)对齐 |
| **7.1** | **模型配置文件管理与文本生成** | [01_model_profiles_and_generation_zh.md](manual/zh/llm/01_model_profiles_and_generation_zh.md) | `agent_common.llm` |
| **7.2** | **外部聊天 API 与 Fabrix 集成** | [02_external_api_and_fabrix_zh.md](manual/zh/llm/02_external_api_and_fabrix_zh.md) | `agent_common.llm` |
| **7.3** | **本地 GGUF 推理与模型缓存** | [03_local_gguf_inference_zh.md](manual/zh/llm/03_local_gguf_inference_zh.md) | `agent_common.llm` |
| **7.4** | **执行模式与条件化本地切换** | [04_provider_and_local_fallback_zh.md](manual/zh/llm/04_provider_and_local_fallback_zh.md) | `agent_common.llm` |
| **7.5** | **推理结果与异常处理** | [05_inference_results_and_errors_zh.md](manual/zh/llm/05_inference_results_and_errors_zh.md) | `agent_common.llm` |
| **7.6** | **Groq 监督员 AI 与 Antigravity Stop 钩子** | [06_groq_supervisor_and_stop_hook_zh.md](manual/zh/llm/06_groq_supervisor_and_stop_hook_zh.md) | `agent_common.llm` |

---

### 🚀 安装与构建指南 (Installation and Build Guide)

#### 📦 构建 Wheel 安装包 (.whl)
打包新版本并在 `agent_common` 目录或通过 `scripts/build_agent_common_whl.py` 执行以下命令：

##### 1. 离线/内网隔离环境（完全无外网）
使用 `--no-index`, `--no-build-isolation`, `--no-deps` 彻底切断外部 PyPI 访问：

```bash
# 推荐：在根目录下运行自动构建脚本
python scripts/build_agent_common_whl.py

# 或直接运行 pip wheel
pip wheel ./agent_common --no-index --no-build-isolation --no-deps -w whls/
```

##### 2. 联网开发环境

```bash
# 使用 pip wheel
pip wheel ./agent_common --no-deps -w whls/

# 或使用 build 模块
python -m build agent_common --wheel -o whls/
```

#### 安装 Wheel 软件包
```bash
# 开发环境 (Editable 可编辑模式 - 核心轻量安装)
pip install -e agent_common

# 开发环境 (包含云端客户端 extras)
pip install -e "agent_common[clients]"

# 生产环境 (安装 Wheel 包)
pip install dist/agent_common-0.4.78-py3-none-any.whl
```

#### 🌐 官方 PyPI 镜像分发（仅限维护者）

```bash
# 1. 更新构建工具
pip install build twine

# 2. 构建分发包 (同时生成 sdist 与 wheel)
python -m build

# 3. 校验分发归档完整性
python -m twine check dist/*

# 4. 上传至 PyPI
python -m twine upload dist/agent_common-0.4.92*
```

---

### 📋 版本变更历史 (Changelog)

详细版本变更历史请参阅 [CHANGELOG_ZH.md](CHANGELOG_ZH.md) 文件。

