# agent_common (English)

**[📦 PyPI Package](https://pypi.org/project/agent-common/) · [💻 GitHub Source & Manuals](https://github.com/kampores/agent_common)**

> [ 🇰🇷 한국어 (README_KR.md) ](README_KR.md) | [ 🇺🇸 English (README_EN.md) ](README_EN.md) | [ 🇨🇳 中文 (README_ZH.md) ](README_ZH.md) | [ 🇯🇵 日本語 (README_JP.md) ](README_JP.md)

---

## 🇺🇸 agent_common Package Overview

A comprehensive Python common library providing unified logging, hierarchical configuration loaders, cloud and database infrastructure clients, dynamic tool parsers, and centralized error handling for enterprise agent services and data migration pipelines.

---

### 📌 Key Features

#### 1. Configuration Loader & Immutable Config Object (`agent_common.config_loader`)
- **1.1. [Hierarchical YAML Parsing & Deep Merge](manual/en/config_loader/01_hierarchical_yaml_merge_en.md)**: Dynamically merges base package configurations (`agent_common/config/*.yml`) with project-specific configurations (`config/*.yml`).
- **1.2. [Immutable Dot-Notation Access (`ReadOnlyConfig`)](manual/en/config_loader/02_readonly_dot_notation_en.md)**: Intuitive attribute-based lookup (`config.ecs.endpoint_url`, `config.transfer.max_workers_int`) while preventing unintended runtime mutations.
- **1.3. [Type Guarantee & Automatic Coercion via Type Suffixes](manual/en/config_loader/03_type_coercion_and_guarantee_en.md)**:
  - `_int`: Automatic integer conversion and type guarantee.
  - `_float`: Automatic floating-point conversion and type guarantee.
  - `_bool`: Strict boolean conversion and type guarantee (Python `bool` or case-insensitive `"true"`, `"false"`; unsupported values like `0`, `1` fail fast).
  - `_str`: Automatic string conversion and `.strip()` whitespace trimming.
  - `_list` / `_dict`: Guaranteed list / immutable dictionary (`ReadOnlyConfig`) wrapping.
  - Standalone functions `coerce_type_by_key_suffix` and recursive batch coercion `coerce_dict_by_key_suffix` for arbitrary external configuration files (`rule.yml`, `mapping.yml`) and data mappings.
  - Strict Fail-Fast guarantee: type-suffix mismatches immediately raise diagnostic exceptions (`ValueError`/`TypeError`) instead of silently falling back to raw values.
- **1.4. [Fail-Fast Required Setting Validation (`require_setting()`)](manual/en/config_loader/04_fail_fast_require_setting_en.md)**: Immediate process termination with diagnostic output if required settings are missing during startup.
- **1.5. [Network Proxy Control (`_apply_no_proxy`)](manual/en/config_loader/05_network_proxy_control_en.md)**: Automatic synchronization of `NO_PROXY` environment variable from `proxy.no_proxy` configuration.
- **1.6. [Externalizing All Constants & Self-Healing Templates (`ensure_config_file()`)](manual/en/config_loader/06_ensure_config_self_healing_en.md)**: Materializing all in-code constants to configuration files, automatic scaffolding, and in-place missing key injection.

#### 2. Single-Line Log Formatter & Project Logger (`agent_common.logger`)
- **2.1. [Single-Line Flatten Formatter & Origin Tracking (`SingleLineFlattenFormatter`)](manual/en/logger/01_single_line_flatten_formatter_en.md)**: Flattens log records, extracts `[Origin: ...]` caller frames, and optimizes for centralized log aggregators (Logstash, Fluentd, CloudWatch).
- **2.2. [Batch Logging Configuration & Handler Control (`ProjectLogger.configure`)](manual/en/logger/02_project_logger_configure_en.md)**: Dynamic console/file handler initialization, date-based directories, and level-based directory creation (`log_file_str` with `{log_level_str}`).
- **2.3. [Multilingual Message Catalog & Code-Based Logging (`logging_messages_*.yml`)](manual/en/logger/03_multilingual_message_catalog_en.md)**: Dynamic bilingual dictionary loading (`KO`/`EN`), runtime language switching, and safe template parameter substitution.
- **2.4. [Real-Time Metric Tracking & Error/Exclusion Classification (`record_result`)](manual/en/logger/04_execution_result_and_error_tracking_en.md)**: Three-tier outcome model (Success, Failure, Excluded/Skip) and dual instance/class-global multithreaded telemetry.
- **2.5. [Automatic Summary Report Generation (`log_summary`)](manual/en/logger/05_summary_report_generation_en.md)**: Emits structured 80-column execution summary reports with duration, throughput (items/s), transfer rate (MB/s), and decoded error diagnostics.

#### 3. Storage and Database Infrastructure Clients (`agent_common.clients`)
- **3.1. [AWS S3 & Dell ECS Object Storage Client (`S3Client`)](manual/en/clients/01_s3_ecs_storage_client_en.md)**: Connects to AWS S3 and Dell ECS (S3-compatible) storage, early `head_bucket` Fail-Fast verification, high-throughput paginated iterator (`list_objects`), fast header metadata lookup (`get_object_size`), in-memory streaming body extraction (`get_object_stream`), real-time streaming pipeline upload to GCS with smart duplicate skipping (`transfer_to_gcs`).
- **3.2. [Google Cloud Storage Streaming Client & Multi-Tier Auth (`GcsClient`)](manual/en/clients/02_gcs_cloud_storage_client_en.md)**: Four-tier GCP credential resolution hierarchy (`GOOGLE_APPLICATION_CREDENTIALS_JSON` in-memory JSON -> `GOOGLE_APPLICATION_CREDENTIALS` file -> `credentials_path_str` -> Google ADC), instant bucket reachability validation, blob metadata lookup (`get_blob_size`), zero-disk chunked streaming uploads (`upload_stream`).
- **3.3. [BigQuery Batch Loading & Streaming Ingestion (`BigQueryClient`)](manual/en/clients/03_bigquery_batch_and_streaming_load_en.md)**: Fail-fast schema caching (`get_table`), JSON batch load jobs (`load_table_from_json_data`) with unpacked nested error diagnostics (`errors`, `location`, `reason`), real-time streaming ingestion (`insert_rows_json_data`), general SQL query execution (`query`), unique key deduplication set lookup (`get_existing_keys`).
- **3.4. [BigQuery High-Performance Inline MERGE (Upsert) Engine (`merge_table_from_json_data`)](manual/en/clients/04_bigquery_inline_merge_upsert_en.md)**: Executes direct inline MERGE INTO via `UNNEST(JSON_QUERY_ARRAY(@json_payload))` without temporary staging tables, automatic primary key routing, original column preservation (`preserve_columns_list`), schema type inference and casting (`column_types_dict`), reserved keyword and Unicode column backtick escaping, HTTP 413 payload limit protection via default 100-row chunking.
- **3.5. [BigQuery Timestamp Conversion & Timezone Mode Synchronization (`convert_to_bigquery_timestamp`)](manual/en/clients/05_bigquery_timestamp_and_tz_sync_en.md)**: Normalizes ISO 8601, whitespace, and 14-digit/8-digit timestamps to standard BigQuery formats, timezone offset precedence (`timezone_offset_str`), display convenience mode (`kst_as_utc_timestamp_bool`), automated table metadata synchronization with fail-fast mismatch blocking.

#### 4. Dynamic Tool Loader & Template Evaluator (`agent_common.tool_parser`) & Built-in Tools (`agent_common.tool`)
- **4.1. [Dual Tool Hierarchy Discovery & Dynamic Loading (`ToolParser.load_tool_function`)](manual/en/tool_parser/01_dual_tool_hierarchy_discovery_en.md)**:
  - **Priority 1 (Built-in Tools)**: Modules under `agent_common/tool/` (standard enterprise tools).
  - **Priority 2 (Project Tools)**: Local path configured in `config.yml` under `transfer.tool_dir_str` (e.g., `medallion/tool/`).
- **4.2. [Declarative Template Evaluation & Expression Resolution (`ToolParser.eval`)](manual/en/tool_parser/02_declarative_template_eval_en.md)**:
  - Variable namespace binding: `{ecs.key}`, `{sys.today}`, `{json.title}`.
  - Dynamic tool function invocation: `"{code.date_check_to_code(contentInfo.enddate)}"`, `"{path.get_json_name(ecs.key)}"`.
  - Pipe (`|`) fallback chains and default values: `"{meta.title|json.title|'Default Title'}"`.
- **4.3. [Safe Namespace Lookup & Case-Insensitive Access (`_SafeNamespace`)](manual/en/tool_parser/03_safe_namespace_navigation_en.md)**:
  - Unified dot-notation and bracket indexing, resilient case-insensitive key resolution.
  - Returns empty string (`""`) on missing keys without raising `KeyError`; recursive wrapping of nested dictionaries and lists.
- **4.4. [Built-in DateTime Tool (`DateTimeUtils`)](manual/en/tool_parser/04_builtin_datetime_utils_en.md)**:
  - Business rule and template formatting tool delegating core timezone calculations to `TimeUtils`.

#### 5. Progress Tracker & Common Utilities (`agent_common.utils`)
- **5.1. [System Timezone Detection, Global Timezone Resolution & Datetime Normalization (`TimeUtils`)](manual/en/utils/01_time_utils_and_timezone_resolution_en.md)**: Dynamic host OS system timezone detection, 30+ world timezone parsing, ISO 8601 offset calculation, and `parse_datetime` normalization core utility.
- **5.2. [Multithreaded Progress Tracking & Milestone Telemetry (`ProgressTracker`)](manual/en/utils/02_progress_tracker_and_milestones_en.md)**: Real-time multithreaded progress tracking (`[N/Total] (P%)`), throughput/ETA calculation, and tiered logging (standard `INFO` vs 10% milestone `WARNING` level elevation).
- **5.3. [Unicode East Asian Width Alignment & Table Formatter (`TableFormatter`)](manual/en/utils/03_unicode_table_formatter_en.md)**: Precision terminal and Markdown table column width alignment utility calculating Unicode East Asian character display widths (`unicodedata.east_asian_width`).

#### 6. Common Error & Exception Handler (`agent_common.error_handler`)
- Consistent exception logging and handling for network failures, configuration errors, and runtime exceptions.

#### 7. Unified LLM Client & Inference Engine (`agent_common.llm`)
- **7.1. [Model Profiles and Text Generation](manual/en/llm/01_model_profiles_and_generation_en.md)**
- **7.2. [External Chat APIs and Fabrix](manual/en/llm/02_external_api_and_fabrix_en.md)**
- **7.3. [Local GGUF Inference and Model Caching](manual/en/llm/03_local_gguf_inference_en.md)**
- **7.4. [Provider Selection and Conditional Local Fallback](manual/en/llm/04_provider_and_local_fallback_en.md)**
- **7.5. [Inference Results and Error Handling](manual/en/llm/05_inference_results_and_errors_en.md)**
- **7.6. [Groq Supervisor and Antigravity Stop Hook](manual/en/llm/06_groq_supervisor_and_stop_hook_en.md)**

---

### 🛠️ Usage Examples

#### 1. Dot-Notation Global `config` & Type Guarantees
```python
from agent_common.config_loader import config

# 1) Guaranteed type coercion via type suffixes
max_workers: int = config.transfer.max_workers_int       # Guaranteed int
host: str = config.database.host_str                     # Guaranteed str with .strip()
is_active: bool = config.transfer.is_active_bool         # Guaranteed bool

# 2) Hierarchical attribute access
api_url: str = config.services.api_endpoint_url
db_port: int = config.database.port_int
```

#### 2. Dynamic Rule Evaluation via ToolParser
```python
from agent_common.tool_parser import ToolParser

# Initialize ToolParser (auto-discovers built-in and project tools)
tool_parser = ToolParser()

# Prepare context dictionary
context_dict = {
    "storage": {"key": "/data/incoming/20260804/sample_document.json"},
    "document": {"expiry_date": "2024-12-31"},
    "sys": tool_parser.build_sys_context(),
}

# 1) Evaluate tool function call template
date_val = tool_parser.eval("{date.get_today_yyyymmdd()}", context_dict)
# -> "20260824"

# 2) Evaluate system namespace & date templates
today_val = tool_parser.eval("{sys.today}", context_dict)
# -> "20260824"
```

#### 3. Real-time Progress Tracking with ProgressTracker
```python
from agent_common.utils import ProgressTracker
from agent_common.logger import ProjectLogger

logger = ProjectLogger("MyTask")
tracker = ProgressTracker(total_items_int=1000, logger_obj=logger, item_name_str="file")

for file_info in file_list:
    try:
        # Processing logic
        tracker.increment_success(bytes_int=len(data))
    except Exception as e:
        tracker.increment_failure(error_msg_str=str(e))

# Output final execution summary report
tracker.log_summary()
```

#### 4. Unified Text/SQL Generation with LlmClient
```python
from agent_common.llm import LlmClient

# 1) Initialize client with configured purpose or model name
llm_client = LlmClient(purpose_str="sql_generator")

# 2) Generate text using the selected profile's provider_str
prompt_str = "User request: Generate daily subscriber statistics SQL for August 2026."
response_str = llm_client.generate(
    prompt_str=prompt_str,
    system_prompt_str="You are an expert AI for BigQuery SQL generation."
)

print(f"Generated result ({llm_client.last_generated_by_str}):\n{response_str}")
```

#### 5. Storage and BigQuery Client Usage
```python
from agent_common.clients import S3Client, GcsClient, BigQueryClient

# S3 -> GCS Smart Transfer
s3_client = S3Client(bucket_name_str="source-lake")
gcs_client = GcsClient(bucket_name_str="target-lake")

for obj in s3_client.list_objects(prefix_str="raw/events/"):
    s3_client.transfer_to_gcs(
        gcs_client_obj=gcs_client,
        s3_key_str=obj["Key"],
        gcs_blob_name_str=f"lake/{obj['Key'].lstrip('/')}",
        size_int=obj["Size"],
    )

# BigQuery Inline MERGE (Upsert)
bq_client = BigQueryClient(project_id_str="my-project", dataset_id_str="dw", table_id_str="tb_user")
bq_client.merge_table_from_json_data(
    json_data_any=[{"user_id": "U01", "name": "John Doe", "created_at": "2026-01-01 00:00:00+09:00"}],
    pk_key_str="user_id",
    preserve_columns_list=["created_at"],
)
```

---

### 📖 Detailed Feature Manuals

| # | Module / Topic | User Manual Link | Key Highlights |
| :---: | :--- | :---: | :--- |
| **1.1** | **Hierarchical YAML Parsing & Deep Merge** | [01_hierarchical_yaml_merge_en.md](manual/en/config_loader/01_hierarchical_yaml_merge_en.md) | 5-stage merge order, recursive `_deep_merge` algorithm, auto project root discovery |
| **1.2** | **Immutable Dot-Notation Access (`ReadOnlyConfig`)** | [02_readonly_dot_notation_en.md](manual/en/config_loader/02_readonly_dot_notation_en.md) | Dot-notation attribute lookup, strict runtime mutation prevention (Read-Only) |
| **1.3** | **Type Guarantee & Automatic Coercion** | [03_type_coercion_and_guarantee_en.md](manual/en/config_loader/03_type_coercion_and_guarantee_en.md) | `_int`, `_float`, `_bool`, `_str`, `_list`, `_dict` runtime casting and type safety |
| **1.4** | **Fail-Fast Required Setting Validation** | [04_fail_fast_require_setting_en.md](manual/en/config_loader/04_fail_fast_require_setting_en.md) | Startup phase mandatory validation, diagnostic output, and fail-fast termination |
| **1.5** | **Network Proxy Control** | [05_network_proxy_control_en.md](manual/en/config_loader/05_network_proxy_control_en.md) | Automatic synchronization of `NO_PROXY` from `proxy.no_proxy` configuration |
| **1.6** | **Constant Externalization & Self-Healing Templates** | [06_ensure_config_self_healing_en.md](manual/en/config_loader/06_ensure_config_self_healing_en.md) | Materializing all in-code constants, automatic scaffolding, and in-place missing key injection |
| **2.1** | **Single-Line Formatter & Origin Tracking** | [01_single_line_flatten_formatter_en.md](manual/en/logger/01_single_line_flatten_formatter_en.md) | `SingleLineFlattenFormatter`, `[Origin: ...]` frame extraction, centralized log collector optimization |
| **2.2** | **Batch Logging Setup & Handler Control** | [02_project_logger_configure_en.md](manual/en/logger/02_project_logger_configure_en.md) | `ProjectLogger.configure()`, console/file handler routing, level-based paths, unified path template |
| **2.3** | **Multilingual Catalog & Code-Based Logging** | [03_multilingual_message_catalog_en.md](manual/en/logger/03_multilingual_message_catalog_en.md) | `logging_messages_ko.yml`/`en.yml`, runtime language switching, safe template variable formatting |
| **2.4** | **Result Telemetry & Error Classification** | [04_execution_result_and_error_tracking_en.md](manual/en/logger/04_execution_result_and_error_tracking_en.md) | Success/Failure/Exclusion 3-tier classification, instance & class-global multithreaded counters |
| **2.5** | **Automatic Summary Report Generation** | [05_summary_report_generation_en.md](manual/en/logger/05_summary_report_generation_en.md) | `ProjectLogger.log_summary()`, 80-column summary block, throughput/bandwidth, decoded error explanations |
| **3.1** | **AWS S3 & Dell ECS Storage Integration** | [01_s3_ecs_storage_client_en.md](manual/en/clients/01_s3_ecs_storage_client_en.md) | S3/ECS connection, Fail-Fast verification, paginated listing, direct GCS streaming and duplicate skip |
| **3.2** | **GCS Streaming Upload & 4-Tier Auth** | [02_gcs_cloud_storage_client_en.md](manual/en/clients/02_gcs_cloud_storage_client_en.md) | 4-tier GCP credential precedence, connection validation, metadata retrieval, in-memory stream upload |
| **3.3** | **BigQuery Batch Loading & Streaming Ingestion** | [03_bigquery_batch_and_streaming_load_en.md](manual/en/clients/03_bigquery_batch_and_streaming_load_en.md) | JSON batch load jobs vs streaming API, nested error diagnostics unpacking, deduplication key lookup |
| **3.4** | **BigQuery Inline MERGE (Upsert) Engine** | [04_bigquery_inline_merge_upsert_en.md](manual/en/clients/04_bigquery_inline_merge_upsert_en.md) | Pure inline MERGE without staging tables, UNNEST parameter binding, dynamic type casting, 100-row chunks |
| **3.5** | **BigQuery Timestamp Conversion & TZ Sync** | [05_bigquery_timestamp_and_tz_sync_en.md](manual/en/clients/05_bigquery_timestamp_and_tz_sync_en.md) | ISO/compact timestamp normalization, Standard-UTC vs KST-as-UTC modes, table metadata auto-sync & Fail-Fast |
| **4.1** | **Dual Tool Hierarchy Discovery & Dynamic Loading** | [01_dual_tool_hierarchy_discovery_en.md](manual/en/tool_parser/01_dual_tool_hierarchy_discovery_en.md) | Built-in (Priority 1) vs Local (Priority 2) discovery, 3-step function introspection, `_tool_cache`, `scan_rules_for_tool_functions` pre-flight validation |
| **4.2** | **Declarative Template Evaluation & Expression Resolution** | [02_declarative_template_eval_en.md](manual/en/tool_parser/02_declarative_template_eval_en.md) | `ToolParser.eval()`, direct tool calls, dot-notation namespaces, pipe (`\|`) fallbacks, signature-aware parameter binding, and automatic context injection |
| **4.3** | **Safe Namespace Lookup & Case-Insensitive Access** | [03_safe_namespace_navigation_en.md](manual/en/tool_parser/03_safe_namespace_navigation_en.md) | `_SafeNamespace`, case-insensitive lookups, silent empty-string (`""`) fallback on missing keys, recursive nested collection wrapping |
| **4.4** | **Built-in DateTime Tool (`DateTimeUtils`)** | [04_builtin_datetime_utils_en.md](manual/en/tool_parser/04_builtin_datetime_utils_en.md) | Business template formatting tool, `TimeUtils` delegation architecture, `YYYYMMDD`, BigQuery ISO timestamps, and compact datetime strings |
| **5.1** | **System Timezone Detection & Global Timezone Resolution** | [01_time_utils_and_timezone_resolution_en.md](manual/en/utils/01_time_utils_and_timezone_resolution_en.md) | `TimeUtils`, dynamic host OS/container timezone detection, 30+ global timezone abbreviation parser, timezone-aware datetime normalization |
| **5.2** | **Multithreaded Progress Tracking & Milestone Telemetry** | [02_progress_tracker_and_milestones_en.md](manual/en/utils/02_progress_tracker_and_milestones_en.md) | `ProgressTracker`, real-time percentage (`%`), throughput, ETA, standard `INFO` vs 10% milestone `WARNING` level elevation |
| **5.3** | **Unicode East Asian Width Alignment & Table Formatter** | [03_unicode_table_formatter_en.md](manual/en/utils/03_unicode_table_formatter_en.md) | `TableFormatter`, precise East Asian character display width calculation, monospace and Markdown table vertical border alignment |
| **7.1** | **Model Profiles and Text Generation** | [01_model_profiles_and_generation_en.md](manual/en/llm/01_model_profiles_and_generation_en.md) | `agent_common.llm` |
| **7.2** | **External Chat APIs and Fabrix** | [02_external_api_and_fabrix_en.md](manual/en/llm/02_external_api_and_fabrix_en.md) | `agent_common.llm` |
| **7.3** | **Local GGUF Inference and Model Caching** | [03_local_gguf_inference_en.md](manual/en/llm/03_local_gguf_inference_en.md) | `agent_common.llm` |
| **7.4** | **Provider Selection and Conditional Local Fallback** | [04_provider_and_local_fallback_en.md](manual/en/llm/04_provider_and_local_fallback_en.md) | `agent_common.llm` |
| **7.5** | **Inference Results and Error Handling** | [05_inference_results_and_errors_en.md](manual/en/llm/05_inference_results_and_errors_en.md) | `agent_common.llm` |
| **7.6** | **Groq Supervisor and Antigravity Stop Hook** | [06_groq_supervisor_and_stop_hook_en.md](manual/en/llm/06_groq_supervisor_and_stop_hook_en.md) | `agent_common.llm` |

---

### 🚀 Installation and Build Guide

#### 📦 Wheel Package Build (.whl)
Run the following commands within the `agent_common` directory or using `scripts/build_agent_common_whl.py`:

##### 1. Air-gapped / Offline Environment
Use `--no-index`, `--no-build-isolation`, and `--no-deps` to build offline without external PyPI access:
```bash
# Recommended: Run build script from root
python scripts/build_agent_common_whl.py

# Or build wheel directly
pip wheel ./agent_common --no-index --no-build-isolation --no-deps -w whls/
```

##### 2. Online Environment
```bash
# Using pip wheel
pip wheel ./agent_common --no-deps -w whls/

# Or using build module
python -m build agent_common --wheel -o whls/
```

#### Installing the Wheel Package
```bash
# Development (Editable mode - lightweight core)
pip install -e agent_common

# Development (With cloud client extras)
pip install -e "agent_common[clients]"

# Production (Wheel package)
pip install dist/agent_common-0.4.78-py3-none-any.whl
```

#### 🌐 Official PyPI Distribution (Maintainers Only)

```bash
# 1. Update build tools
pip install build twine

# 2. Build distributions (sdist & wheel)
python -m build

# 3. Validate distribution archives
python -m twine check dist/*

# 4. Upload to PyPI
python -m twine upload dist/agent_common-0.4.92*
```

---

### 📋 Version History (Changelog)

For detailed version history, please refer to [CHANGELOG_EN.md](CHANGELOG_EN.md).

