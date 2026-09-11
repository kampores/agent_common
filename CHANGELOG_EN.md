# Version History (Changelog)

> [ 🇰🇷 Korean Version (한국어 체인지로그) ](https://github.com/kampores/agent_common/blob/main/CHANGELOG.md)

### v0.4.61 (2026-09-11)
- **Registered Log ID `extension_matrix_summary_report` for File Extension 2-Stage Matrix Summary Report (Rules 1.1.1, 3.1)**:
  - `logging_messages_ko.yml` & `logging_messages_en.yml`:
    - Added `extension_matrix_summary_report: "{summary}"` template under `WARNING.lifecycle` section.
    - Resolved the issue where the summary matrix table was not formatted and only the log ID string itself was printed due to missing log ID definition.

### v0.4.57 (2026-09-10)
- **Eliminated Legacy `EcsClient = S3Client` Class Alias and Unified Client Naming (Rules 1.4.5, 1.4.6, 1.6.3)**:
  - `clients.py`:
    - Removed the redundant `EcsClient = S3Client` backward compatibility alias now that migration to universal `S3Client` is complete, eliminating unnecessary aliasing layers and unifying client references to `S3Client`.
  - `__init__.py`:
    - Removed `EcsClient` from top-level package imports and `__all__` export list.
  - `README.md`:
    - Cleaned up documentation notes regarding `EcsClient` backward compatibility alias under `S3Client`.

### v0.4.56 (2026-09-10)
- **Added In-Memory JSON Key (`GCP_KEYFILE_JSON`) Support and 100% File Path Backward Compatibility in `GcsClient` and `BigQueryClient` (Rules 1.1.1, 1.4.1, 1.5.1)**:
  - `clients.py`:
    - Introduced common helper `_resolve_gcp_credentials` implementing a 3-tier priority resolution (1st: `GCP_KEYFILE_JSON` / `GOOGLE_KEYFILE_JSON` in-memory JSON ➔ 2nd: `credentials_path_str` file path ➔ 3rd: Google ADC).
    - Enables secure injection of `keyfile_dict` from Airflow K8s Secret / Connection (`google_cloud_default`) directly in memory via `Credentials.from_service_account_info` without writing files to disk.
    - Preserves 100% backward compatibility with local file-based development environments (`Credentials.from_service_account_file`).
    - Added automatic override of project ID in `BigQueryClient` via `GCP_PROJECT_ID` or `GOOGLE_CLOUD_PROJECT`.

### v0.4.55 (2026-09-10)
- **Added Universal Environment Variable Interpolation (`${VAR:-default}`) in `ConfigLoader` (Rules 1.1.1, 1.4.1, 1.5.1)**:
  - `config_loader.py`:
    - Added `_ENV_VAR_PATTERN` regex and `_replace_env_match` helper to recursively interpolate environment variable templates (`${VAR_NAME}` and `${VAR_NAME:-default}`) across all YAML configuration files and settings dictionaries (`_interpolate_env_vars`).
    - Empowers declarative, secure injection of sensitive credentials (API keys, secrets, URLs) from external orchestrators (Airflow, Kubernetes, Docker) across all agents and data pipelines without domain-specific hardcoding.

### v0.4.52 (2026-09-09)
- **Added `matched_condition_str` Injection Support in `BigQueryClient.merge_table_from_json_data` (Rules 1.5.1, 1.6.1)**:
  - `clients.py`:
    - Added `matched_condition_str: str | None = None` parameter to `BigQueryClient.merge_table_from_json_data`.
    - Dynamically assemble the BigQuery MERGE SQL `WHEN MATCHED` clause as `WHEN MATCHED {matched_condition_str} THEN`, empowering callers to inject domain conditions (such as source document modification timestamp comparisons) cleanly and generically.

### v0.4.51 (2026-09-09)
- **Elimination of 19 Redundant Pass-Through Getter Properties in `LlmClient` (Rules 1.4.5, 1.4.6)**:
  - `llm.py`:
    - Completely removed 19 unused pass-through `@property` getters (`provider_str`, `enabled_bool`, `api_key_env_str`, `base_url_str`, `chat_completions_path_str`, `api_format_str`, `model_str`, `llm_id_int`, `client_env_str`, `user_env_str`, `timeout_seconds_int`, `max_tokens_int`, `temperature_float`, `model_path_str`, `n_ctx_int`, `n_threads_int`, `n_batch_int`, `n_gpu_layers_int`, `verbose_bool`) from `LlmClient`.
    - Eliminated ~95 lines of redundant wrapper boilerplate and standardized internal configuration access directly through immutable `self.model_config`, achieving structural conciseness and adhering to YAGNI and anti-pass-through rules.

### v0.4.50 (2026-09-09)
- **Elimination of Defensive Fuzzy Matching and Legacy Key Fallbacks in `ProjectLogger.configure` (Rule 1.5.3)**:
  - `logger.py`:
    - Completely eliminated triple-fallback chains and fuzzy app name search loops across `logging.level_dict`.
    - Standardized on direct canonical key lookups (`logging.format_str`, `logging.datefmt_str`, `logging.file_logging_bool`, `logging.log_file_str`).
    - Removed defensive type casts (`str(...)`, `bool(...)`), strictly adhering to Fail-Fast principles.

### v0.4.49 (2026-09-09)
- **Elimination of Defensive Fuzzy Suffix Matching Loops in `ReadOnlyConfig` and Full Fail-Fast Enforcement (Rule 1.5.3)**:
  - `config_loader.py`:
    - Completely removed bidirectional fuzzy suffix hunting loops (`for suffix_str in ("_str", "_int", ...): ...`) in `ReadOnlyConfig.__getattr__` and `__contains__`.
    - Standardized on direct key lookups (`data[key_str]`), ensuring that misspelled or non-canonical keys raise `AttributeError` immediately (Fail-Fast).
    - Eliminated intermediate alias variable `effective_key_str`, passing canonical `key_str` directly into `coerce_type_by_key_suffix`.

### v0.4.48 (2026-09-09)
- **Elimination of Defensive `**kwargs: Any` and Fallback Logic in Client (`clients.py`) and LLM (`llm.py`) Modules (Rules 1.3.1, 1.5.2, 1.6.1)**:
  - `clients.py`:
    - `S3Client.__init__`, `list_objects`, `get_object_stream`, `get_object_size`, `transfer_to_gcs`: Completely eliminated `**kwargs: Any` and defensive fallback code (`kwargs.get("prefix")`, `kwargs.get("endpoint_url")`), enforcing explicit, type-suffixed arguments (`endpoint_url_str`, `prefix_str`, etc.).
    - `GcsClient.__init__`, `get_blob_size`, `upload_stream`: Removed `**kwargs: Any` and bound strictly to canonical parameters (`bucket_name_str`, `blob_name_str`, etc.).
    - `BigQueryClient.__init__`, `load_table_from_json_data`, `insert_rows_json_data`, `query`, `get_existing_keys`: Removed `**kwargs: Any` and fallback handling for legacy aliases like `write_disp`.
  - `llm.py`:
    - `LlmClient.__init__`, `generate`: Fully removed `**kwargs: Any` and defensive wrappers (`kwargs.get("prompt")`), ensuring immediate `TypeError` (Fail-Fast) when unexpected arguments are provided.

### v0.4.47 (2026-09-09)
- **Direct Immutable Config Access for `LlmClient` and Elimination of Redundant `self` Config Cloning & Defensive Casting (Rules 1.4.2, 1.4.5, 1.6.1)**:
  - `llm.py`:
    - Eliminated redundant cloning of 19 static model configuration fields into `self` inside `LlmClient.__init__` (`self.provider_str = str(...)`, `self.max_tokens_int = int(...)`), standardizing on direct access via `self.model_config` (ReadOnlyConfig) and `config.llm_pool[self.model_name_str]`.
    - Removed defensive right-hand casting wrappers like `int(os.getenv(..., str(self.max_tokens_int)))` to ensure unadulterated type evaluation and enforce Fail-Fast principles.
    - Trimmed `APP_DEFAULT_SCHEMA_DICT["llm"]` by removing 19 artificial `default_*` fallback keys, significantly reducing schema bloat.
    - Added backwards-compatible accessor properties on `LlmClient` backed directly by `model_config`.
  - `llmpool.yml`:
    - Standardized all model profile keys with strict type suffixes (`provider_str`, `enabled_bool`, `api_key_env_str`, `base_url_str`, `chat_completions_path_str`, `model_str`, `timeout_seconds_int`, `max_tokens_int`, `temperature_float`, `api_format_str`, `llm_id_int`, `client_env_str`, `user_env_str`, `model_path_str`, `n_ctx_int`, `n_threads_int`, `n_batch_int`, `n_gpu_layers_int`, `verbose_bool`).
  - `config_loader.py`:
    - Enhanced `ReadOnlyConfig.__getattr__` and `__contains__` with bidirectional suffix lookup for improved resilience and backward compatibility.

### v0.4.46 (2026-09-09)
- **Elimination of Defensive Right-Hand Type Casting Wrappers (`str(...)`) and Fail-Fast Enforcement (Rules 1.3.1 & 1.5.2)**:
  - `logger.py`: Removed redundant `str(name)` casting in `ProjectLogger.__init__`, directly assigning `name or ""` to avoid masking non-string inputs and guarantee early error detection.

### v0.4.45 (2026-09-09)
- **Strict Type-Suffix Standardization and Elimination of Hardcoding in LLM (`llm.py`) and Logging (`logger.py`) Modules (Rules 1.1, 1.6.1, 1.7.5)**:
  - `llm.py`:
    - Enforced mandatory type suffixes on all configuration keys in `APP_DEFAULT_SCHEMA_DICT` (`default_provider_str`, `default_enabled_bool`, `default_timeout_seconds_int`, `default_max_tokens_int`, `default_temperature_float`, `vertex_model_str`, `gemini_model_str`, `ollama_model_str`, `ollama_endpoint_str`, `router_model_str`, `sql_generator_model_str`, `validator_model_str`), eliminating code hardcoding.
    - Automated global configuration schema registration upon module import (`config._source.register_schema(APP_DEFAULT_SCHEMA_DICT)`).
    - Fully standardized `LlmClient` class annotations, instance fields (`last_generated_by_str`), and method parameters (`purpose_str`, `prompt_str`, `system_prompt_str`, `model_name_str`, `provider_str`, `timeout_seconds_int`, `max_tokens_int`, `temperature_float`) to strict type suffixes while maintaining backwards-compatible keyword arguments.
  - `logger.py`:
    - `ProjectLogger.configure`: Enhanced to inspect type-suffixed config properties (`logging.level_dict`, `logging.level_str`, `logging.format_str`, `logging.datefmt_str`, `logging.file_logging_bool`, `logging.log_file_str`) with seamless fallback to legacy keys.
  - `README.md`: Synchronized Korean and English `LlmClient` code examples with suffixed argument names (`purpose_str`, `prompt_str`, `system_prompt_str`, `last_generated_by_str`).

### v0.4.44 (2026-09-09)
- **Comprehensive Elimination of Untyped Alias Constants and Redundant Bindings across All Modules**:
  - `llm.py`: Deleted untyped alias variables `_LOCAL_LLMS = _LOCAL_LLMS_DICT` and `APP_DEFAULT_SCHEMA = APP_DEFAULT_SCHEMA_DICT`, unifying cache references to `_LOCAL_LLMS_DICT`.
  - `config_loader.py`, `logger.py`, `tool_parser.py`: Deleted module-level `APP_DEFAULT_SCHEMA = APP_DEFAULT_SCHEMA_DICT` aliases and cleaned up `logger.__all__`.
  - `date_time_utils.py`: Completely removed 5 untyped class constant aliases (`FORMAT_DATE_YYYYMMDD`, `FORMAT_DATETIME_STD`, `FORMAT_DATETIME_NO_TZ`, `FORMAT_DATETIME_KST`, `FORMAT_DATETIME_COMPACT`), and updated all callers (`logger.py`, `tool_parser.py`, `utils.py`) to canonical `_STR` constants.
  - `medallion/tool/code/date_check_to_code.py`: Removed legacy function alias bindings (`date_check`, `evaluate_date_status`).

### v0.4.43 (2026-09-09)
- **Full Standardization of Local Variables, Arguments, and Loop Targets with Strict Type Suffixes across `clients.py` (Rules 1.6.1 & 1.6.2)**:
  - `BigQueryClient.insert_rows_json_data`: Replaced `table_target` -> `table_target_any`, `rows_to_insert` -> `rows_to_insert_list`, `errors` -> `insert_errors_list`, `err_details` -> `error_details_list`, `idx` -> `row_index_int`, `e`/`loc`/`rsn` -> `single_error_dict`, `location_str`, `reason_str`, `combined_err_msg` -> `combined_error_message_str`, and `clean_insert_err` -> `clean_insert_error_str`.
  - `BigQueryClient.load_table_from_json_data`: Replaced `table_target` -> `table_target_any`, `rows_to_insert` -> `rows_to_insert_list`, `write_disp` -> `write_disposition_effective_str`, `job_config` -> `job_config_obj`, `load_job` -> `load_job_obj`, `sub_err_list`/`s_err`/`loc` -> `sub_error_list`, `sub_error_item_dict`, `location_str`, and `clean_err` -> `clean_error_str`.
  - `BigQueryClient.query`, `get_existing_keys`, `merge_table_from_json_data`: Replaced `query_job` -> `query_job_obj`, `results` -> `query_results_obj`, `job_config` -> `job_config_obj`, `p_job` -> `post_job_obj`, `clean_err_str` -> `clean_error_str`.
  - `BigQueryClient.convert_to_bigquery_timestamp`: Replaced `tz_pattern` -> `tz_pattern_str`, `tz_match` -> `tz_match_obj`, `tz_suffix` -> `tz_suffix_str`, `raw_tz` -> `raw_tz_str`, and `dt_part` -> `datetime_part_str`.
  - `S3Client`, `GcsClient`: Standardized `paginator` -> `paginator_obj`, `pages` -> `pages_iterable`, `page`/`obj` -> `page_dict`/`object_item_dict`, `response` -> `response_dict`, `blob` -> `blob_obj`, `resolved_stream` -> `resolved_stream_any`.
  - Module-level lazy load cache variables: Clarified to `_boto3_module`, `_boto_config_cls`, `_storage_module`, `_bigquery_module`, `_service_account_module`.

### v0.4.42 (2026-09-09)
- **Complete Elimination of Duplicate Untyped Alias Instance Variables in `clients.py` and Full Enforcement of Rule 1.6.1**:
  - `BigQueryClient`: Deleted all redundant alias variables without type suffixes (`self.project_id`, `self.dataset_id`, `self.table_id`, `self.credentials_path`, `self.timeout_seconds`, `self.ignore_unknown_values`, `self.timezone_offset`) and unused internal flag (`self._use_streaming_only`).
  - `S3Client`, `GcsClient`: Cleaned up all redundant alias instance fields (`self.endpoint_url`, `self.access_key`, `self.secret_key`, `self.bucket_name`, `self.credentials_path`, `self.timeout_seconds`).
  - Removed unused module-level `APP_DEFAULT_SCHEMA` alias from top of `clients.py`.
  - Application layer (`app/`): Synchronized all client attribute lookups in `ecs_to_bigquery.py`, `ecs_to_gcs.py`, `ecs_to_gcsbigquery_merge.py`, and `table_transformer.py` to use canonical type-suffixed attributes (`dataset_id_str`, `table_id_str`, `project_id_str`, `bucket_name_str`).

### v0.4.41 (2026-09-09)
- **Full Restoration of Strict Type Suffixes (`_int`, `_str`, `_bool`) in `clients.py` and Removal of Redundant Casting Wrappers**:
  - `clients.py`: Restored mandatory type suffixes (`timeout_seconds_int`, `chunk_size_int`, `ignore_unknown_values_bool`, `timezone_offset_str`, `max_retries_int`) in `APP_DEFAULT_SCHEMA_DICT` per Rule 1.6.1.
  - `BigQueryClient`, `GcsClient`: Standardized constructor parameters, instance fields, and method arguments with explicit type suffixes (`_str`, `_int`, `_bool`) while maintaining backwards-compatible properties and `**kwargs`.
  - Removed redundant manual wrappers (`bool()`, `int()`, `str()`) by leveraging `ReadOnlyConfig`'s native suffix-based type coercion (`coerce_type_by_key_suffix`).

### v0.4.40 (2026-09-09)
- **Elimination of Speculative Suffix Fuzzy Matching & Strict 1:1 Key Resolution (Fail-Fast)**:
  - `ReadOnlyConfig.__getattr__`: Removed fuzzy `suffixes` scanning loop that silently papered over mismatched keys (`_str`, `_int`, etc.). Unmatched keys now immediately raise `AttributeError` (Fail-Fast).
  - `ReadOnlyConfig.__contains__`: Streamlined `in` operator to strict `key_str in data` lookup without speculative suffix mutation.
  - `ConfigLoader.ensure_config_file`: Removed fuzzy suffix checks during self-healing dictionary merges to ensure exact 1:1 key fidelity between schema and YAML files.
  - `ConfigLoader.setting`: Eliminated speculative suffix traversal in dotted key paths.
  - `app/app_schema.py`: Perfectly matched schema dictionary keys with `config/config.yml` to prevent unintended self-healing additions.

### v0.4.39 (2026-09-09)
- **Standardization of Schema Constants (`APP_DEFAULT_SCHEMA_DICT`) and Strict Type Suffixes (`_str`, `_int`, `_bool`, `_list`, `_dict`)**:
  - Renamed schema dictionary constants across all `agent_common` modules (`clients`, `logger`, `config_loader`, `llm`, `tool_parser`) to `APP_DEFAULT_SCHEMA_DICT` with backward-compatible `APP_DEFAULT_SCHEMA` aliases.
  - Added `_STR` suffixes to `DateTimeUtils` format constants (`FORMAT_DATE_YYYYMMDD_STR`, `FORMAT_DATETIME_STD_STR`, etc.).
  - `ConfigLoader`: Avoided forced registration of package-level schemas in `__init__` to eliminate unintended template injection into application `config.yml`, providing transparent fallback for internal templates via `APP_DEFAULT_SCHEMA_DICT`.
  - Application Schema (`app/app_schema.py`): Enforced comprehensive type suffixes on all keys across `_BASE_*_SCHEMA_DICT` and `ECS_TO_*_SCHEMA_DICT` (`prefix_str`, `target_folders_list`, `date_prefix_str`, `path_regex_str`, `table_id_str`, `max_retries_int`, `chunk_size_int`, `timeout_seconds_int`, etc.).

### v0.4.38 (2026-09-09)
- **Elimination of Speculative Fallback Chains & Enforcement of Direct Dot-Notation Configuration (`config`)**:
  - `ToolParser`: Removed hardcoded fallback (`"medallion/tool"`) and speculative directory search lists (`cand_dirs_list = [...]`). Enforced direct access via `config.transfer.tool_dir_str`.
  - `BigQueryClient`: Removed in-code hardcoded defaults (`setting(..., True)`, `setting(..., "+09:00")`) and defensive `getattr(self, "timezone_offset_str", "+09:00")`. Switched to direct `config.bigquery.ignore_unknown_values` and `config.bigquery.timezone_offset` access.
  - `LlmClient`: Completely abolished speculative `prompts.* or llm.*` fallback chains in favor of direct declarative settings `config.llm.system_prompt_str`, `config.llm.router_model_str`, and `config.llm.sql_generator_model_str`.
  - `ProjectLogger`: Removed duplicate hardcoded fallback arguments in `loader.setting()` calls.
  - `ConfigLoader.ensure_config_file`: Removed hardcoded template fallback strings in `setting()` calls.
  - Higher-level Application (`app/`): Cleaned up defensive `getattr(config.transfer, "save_error_json_bool", False)` patterns to direct `config.transfer.save_error_json_bool`.

### v0.4.37 (2026-09-09)
- **Deprecation of Package-level Synthetic Schema (`default_schema.py`) to Preserve Modularity and Lazy Loading**:
  - In alignment with `agent_common`'s lightweight modularity design (allowing users to import only specific components like `logger` or `clients`), completely removed the forced synthetic schema module (`default_schema.py`) and top-level `APP_DEFAULT_SCHEMA`/`AGENT_COMMON_DEFAULT_SCHEMA` exports.
  - Retained module-specific baseline schemas within each file, preventing unnecessary cross-module coupling and overhead.
  - Revised architecture rule (1.7.5): Library packages define module schemas independently without forced package-wide aggregation.

### v0.4.36 (2026-09-08)
- **Standardized Program Logger Name (`%(name)s`) and Automatic Stack-based Caller (`%(caller)s`, `%(className)s`) Extraction**:
  - Unified logger names (`name`) to the application/program identifier (`ProjectLogger.configure(app_name_str=...)`) for enterprise monitoring and centralized logging collectors (Cloud Logging, BigQuery, ELK).
  - Automatically inspected Python runtime call stack frames during logging to detect `self.__class__.__name__` inside class methods, populating `caller` (`ClassName.method()`) and `className` without manual boilerplates.
  - Automatically formatted top-level functions or script entry points without a leading dot (`function()`).
  - Standardized default log format: `[%(asctime)s][%(levelname)s][%(name)s][%(filename)s:%(lineno)d %(caller)s] %(message)s`.

### v0.4.35 (2026-09-08)
- **Modular `APP_DEFAULT_SCHEMA` Declarative Configuration Architecture**:
  - Implemented per-module `APP_DEFAULT_SCHEMA` constants across all source files (`logger`, `config_loader`, `clients`, `tool_parser`, `llm`) matching `agent_common`'s non-main library structure.
  - Added `default_schema.py` synthesizing module schemas and exposing `APP_DEFAULT_SCHEMA` and `AGENT_COMMON_DEFAULT_SCHEMA` at package root, automatically merged into `ConfigLoader._registered_schemas`.
- **Consolidation into Standard `log_file` with Dynamic `{log_level}` Directory Creation**:
  - Deprecated subjective dual paths (`out_file` for error vs `debug_file` for warning/debug) in favor of unified `logging.log_file`.
  - Added support for `{log_level}` (lowercase) and `{LOG_LEVEL}` (uppercase) placeholders, automatically creating level-specific directories (`warning/`, `error/`, etc.) during runtime execution.
  - Maintained 100% backward compatibility fallback for existing `out_file` and `debug_file` configurations.
- **Strict Prohibition of Abbreviated Identifiers & Full Descriptive Naming Principle (Rules 1.6.2 & 1.7.5)**:
  - Eliminated ambiguous abbreviated variables in `logger.py`, refactoring to descriptive names with mandatory type suffixes (`output_error_log_file_str`, `debug_log_file_str`, `default_log_file_str`, `target_log_file_path_str`, `file_logging_enabled_bool`).
  - Completely prevents confusion where missing settings are assumed due to ambiguous names, avoiding redundant key creation.

### v0.4.34 (2026-09-08)
- **Introduction of Universal `S3Client` for AWS S3 & Dell ECS with 100% `EcsClient` Backward Compatibility**:
  - Generalized `EcsClient` into `S3Client` supporting standard AWS S3 as well as on-premise Dell ECS and other S3-compatible object storages (MinIO, Ceph).
  - Made `endpoint_url_str` optional (`None` default): connects to AWS default S3 endpoints when omitted, and connects to custom Dell ECS/MinIO endpoints when specified.
  - Added `region_name_str` parameter to support Signature Version 4 requirements for AWS S3.
  - Added support for AWS IAM Role and environment-based credentials by allowing `access_key_str` and `secret_key_str` to be omitted.
  - Provided `EcsClient = S3Client` module-level alias and legacy keyword arguments mapping (`endpoint_url`, `access_key`, `secret_key`, `bucket_name`, `timeout_seconds`, `ecs_key`, `size`, etc.) ensuring zero breaking changes for existing code.
- **Added `s3` Extras in Optional Dependencies**:
  - Added `s3 = ["boto3>=1.26.0"]` under `[project.optional-dependencies]` in `pyproject.toml` while retaining `ecs` for existing setups.

### v0.4.33 (2026-09-07)
- **Lazy Loading of Cloud Storage SDKs & Ultra-Lightweight Package Footprint**:
  - Refactored heavy cloud SDK dependencies (`boto3`, `google-cloud-storage`, `google-cloud-bigquery`) in `EcsClient`, `GcsClient`, and `BigQueryClient` to load on-demand upon `_connect()` and query execution rather than at module import time.
  - Ensures safe and error-free import of `agent_common` core and `clients` modules in lean environments without cloud SDKs installed.
  - Provides clear diagnostic `ImportError` messages guiding users to install missing dependencies (e.g., `'pip install boto3'` or `'pip install agent_common[clients]'`).
  - Preserved IDE autocomplete and static type analysis via `TYPE_CHECKING` blocks.
- **Optional Dependencies (Extras) Specification**:
  - Moved all cloud storage SDKs to `[project.optional-dependencies]` (`clients`, `ecs`, `gcp`, `all`) in `pyproject.toml`.
  - Base installation (`pip install agent_common`) now requires only `PyYAML`, achieving an ultra-compact installation footprint.
- **Complete Removal of Unused `requests` Dependency**:
  - Fully eliminated unused `requests` from dependencies in strict alignment with AGENTS.md rule 1.2.1 (standard library prioritization via `urllib.request` to minimize CVE exposure).

### v0.4.32 (2026-09-06)
- **Generalization & Public Module-Level Promotion of Type Suffix Coercion Function (`coerce_type_by_key_suffix`)**:
  - Promoted `ReadOnlyConfig._coerce_type_by_key_suffix` private static method to a first-class module-level public function `coerce_type_by_key_suffix(key_str, val_any)`.
  - Enables direct import and standalone execution across arbitrary YAML, JSON, dictionaries, and custom data processing pipelines beyond just `config.yml`.
  - Preserves 100% backward compatibility with existing class-level references (`ReadOnlyConfig.coerce_type_by_key_suffix` and `_coerce_type_by_key_suffix`).
- **Eliminated Silent Failures & Enforced Strict Fail-Fast Policy via `logger.exception`**:
  - Removed legacy antipattern where `int(val_any)` or `float(val_any)` failures silently returned raw invalid strings.
  - Eliminated hardcoded error message formatting in Python code (enforcing DRY and No Hardcoding standards) and consolidated duplicate type failure templates into a single standardized log ID (`config_type_coercion_failed`) in `logging_messages_*.yml`.
  - Extracted centralized helper `_raise_coercion_error` invoking `logger.exception("config_type_coercion_failed", ...)` to track origin tracebacks and update error telemetry before raising explicit `ValueError` / `TypeError`.
- **Introduced Recursive Type Guarantee Helper for Nested Mappings (`coerce_dict_by_key_suffix`)**:
  - Added `coerce_dict_by_key_suffix(data_dict)` to recursively walk and sanitize deeply nested dictionaries and list items according to key suffix rules in a single step.
- **Extended `ReadOnlyConfig` to Support Arbitrary Configuration Files**:
  - Parameterized source file name (`ReadOnlyConfig(data, source_name_str="config.yml")`) so that attribute lookup failures on custom configurations (`rule.yml`, `mapping.yml`) produce precise diagnostic `AttributeError` messages reflecting the actual source name.
- **Top-Level Package Exports**:
  - Re-exported `coerce_type_by_key_suffix` and `coerce_dict_by_key_suffix` in `agent_common.__all__`.

### v0.4.31 (2026-09-04)
- **Full Sanitization & Generalization of Proprietary Identifiers for Public Distribution**:
  - Sanitized internal closed-network assets, private script names, and internal logging folder paths across all logger manuals (`manual/kr/logger/` & `manual/en/logger/`) into standardized enterprise virtual pipeline examples (`data_extractor`, `stream_processor`, `db_loader`, `logs/pipeline/...`, `Cloud_Data_Sync`).
- **Enhanced Practical Dynamic File Routing and Path Templating in `02_project_logger_configure.md`**:
  - Detailed the intelligent routing mechanism directing logs to isolated `out_file` for `ERROR`/`CRITICAL` runs and standard `debug_file` for normal operations.
  - Added full dynamic evaluation samples combining `{app_name}` substitution and `%Y/%m/%d/%Y%m%dT%H%M%S` ISO compact timestamp folders.
- **GitHub-Compatible Mermaid Diagram Syntax Standardization**:
  - Applied double-quoted node text (`["..."]`) and standard edge syntax (`-->|"..."|`) across all 10 Korean and English logger manuals to prevent GitHub diagram rendering errors.
- **Standardization of Telemetry Log Identifiers to Lowercase `snake_case`**:
  - Sanitized error and exclusion log codes in `04_execution_result_and_error_tracking.md` and `05_summary_report_generation.md` to standard lowercase `snake_case`.
- **Added Missing `from pathlib import Path` Import in `llm.py`**:
  - Fixed missing `Path` import used in `LlmClient.__init__` type hint (`config_dir: str | Path | None`) to prevent potential NameError during runtime type inspection.

### v0.4.30 (2026-09-04)
- **Detailed Feature User Manuals for `agent_common.logger` (10 documents in Korean & English) and README Integration**:
  - Authored comprehensive architecture and code reference manuals across 5 core logging capabilities under `manual/kr/logger/` and `manual/en/logger/`:
    1. `01_single_line_flatten_formatter.md`: `SingleLineFlattenFormatter`, `[Origin: ...]` frame extraction and single-line stream flattening optimized for centralized log collectors (Logstash, Fluentd, CloudWatch)
    2. `02_project_logger_configure.md`: `ProjectLogger.configure()`, console/file handler routing, date-partitioned directories, level-based file splitting (`out_file`, `debug_file`), and third-party noise suppression
    3. `03_multilingual_message_catalog.md`: `logging_messages_ko.yml`/`en.yml`, dynamic runtime language switching (`set_language`), `safe_kwargs` formatting, and project-level catalog extension guide
    4. `04_execution_result_and_error_tracking.md`: Success/Failure/Exclusion 3-tier outcome classification, instance & class-global multithreaded telemetry, and lowercase `snake_case` log identifier standardization
    5. `05_summary_report_generation.md`: `ProjectLogger.log_summary()`, 80-column execution summary block, throughput (items/s), transfer rate (MB/s), human-readable error explanations (`get_log_id_description`), and `ProgressTracker` integration
- **Addition of 2.1~2.5 Links to README.md Feature Lists and Detailed Feature Manuals Tables**:
  - Updated both Korean and English sections and tables in `README.md` with direct links and executive summaries for all 5 new logger manuals.

### v0.4.29 (2026-09-04)
- **Bilingual Description Modernization in `pyproject.toml`**:
  - Restructured package one-line summary `description` in Korean and English to accurately reflect the framework's core modern capabilities (`자율 에이전트 및 데이터 파이프라인을 위한 경량 설정·로깅·도구 프레임워크 (Lightweight configuration, logging, and tooling framework for autonomous agents and data pipelines)`).

### v0.4.28 (2026-09-04)
- **Sanitization of Internal GenAI Hub Endpoint Domain and Docstring in `llmpool.yml` and `llm.py`**:
  - Sanitized internal private cloud domain and endpoint URLs in `src/agent_common/config/llmpool.yml` to standard sample endpoints (`https://genaihub.example.com/v1/messages`).
  - Removed internal domain identifier from `_generate_fabrix` docstring in `src/agent_common/llm.py`.

### v0.4.27 (2026-09-04)
- **Complete Sanitization of Proprietary Identifiers and Affiliation Removal for Public Release**:
  - Sanitized closed-network private assets, internal IPs, private database table IDs, and internal storage paths across all manuals, code docstrings, and README examples in accordance with public open-source standards (GitHub / PyPI).
  - Removed company affiliation and company email domain from all file headers and documentation, unifying contact info to personal developer email.
- **Comprehensive Refinement of `06_ensure_config_self_healing.md` (Korean & English) on Core Architecture Philosophy**:
  - Formalized that the primary objective of `ensure_config_file` is the externalization and visibility of all constants into configuration files, establishing that self-healing is merely the operational mechanism.
  - Added in-depth practical guidance for declaring baseline configuration schemas (`default_schema`) at the application entry point and in-place forcible injection of missing constants.
  - Added multi-program constant sharing and schema composition pattern (`app_schema.py`) guide for complex projects where multiple CLI entry points share common infrastructure constants under a single `config.yml`.
  - Added critical anti-pattern warning against defining standalone constants in-code or mid-stream, which negates the purpose of externalization.
  - Updated Mermaid constant injection workflow and refined manual descriptions and hierarchical numbering (`1.1` ~ `1.6`) in `README.md`.

### v0.4.26 (2026-09-04)
- **Enhancement of `manual/en/config_loader/02_readonly_dot_notation.md` and Korean Manual**:
  - Added full reference `config/config.yml` example schema with 1:1 Python dot-notation mapping guide.
  - Documented 3 production patterns for custom configuration directories/paths (`config_dir`), dynamic directory switching, and in-memory test dictionaries.
- **Conversion of README Manual Links to Absolute GitHub URLs for PyPI Rendering**:
  - Updated all 12 manual links (both Korean and English) in `README.md` to absolute GitHub repository URLs (`https://github.com/...`) to ensure seamless navigation directly from PyPI's package description page.

### v0.4.25 (2026-09-04)
- **Detailed Feature User Manuals for `config_loader` (12 documents in Korean & English) and README/PyPI Integration**:
  - Authored comprehensive architecture and code reference manuals across 6 core capabilities under `manual/kr/config_loader/` and `manual/en/config_loader/`:
    1. `01_hierarchical_yaml_merge.md`: 5-stage merge order, recursive `_deep_merge` algorithm, and 3-tier project root auto-detection
    2. `02_readonly_dot_notation.md`: Immutable dot-notation access (`ReadOnlyConfig`), runtime mutation prevention (Read-Only), and dictionary interoperability
    3. `03_type_coercion_and_guarantee.md`: Type-suffix (`_int`, `_float`, `_bool`, `_str`, `_list`, `_dict`) automatic runtime casting and type safety guarantees
    4. `04_fail_fast_require_setting.md`: `require_setting` mandatory setting validation during startup, diagnostic error logging, and fail-fast termination
    5. `05_network_proxy_control.md`: Automatic synchronization of `NO_PROXY` environment variable from `proxy.no_proxy` configuration
    6. `06_ensure_config_self_healing.md`: Materializing all in-code constants to configuration files, automatic scaffolding of missing `config.yml`, and in-place missing key injection
  - Updated `README.md` bullet points with direct links to user manuals and introduced bilingual `### 📖 Detailed Feature Manuals` summary navigation tables.
  - Updated `MANIFEST.in` with `graft manual` and `recursive-include manual *.md` for inclusion in source distribution (`sdist`) packages.
  - Added `Manual (Korean)` and `Manual (English)` GitHub tree links to `[project.urls]` in `pyproject.toml`.

### v0.4.24 (2026-09-04)
- **Multi-language Logging Template Dictionary (`logging_messages_en.yml`) and Config-driven Language Selection (`logging.language`)**:
  - Authored a dedicated English log message template dictionary (`src/agent_common/config/logging_messages_en.yml`) covering all log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) and domain groups with natural, professional translations.
  - Reorganized `logging_messages.yml` into explicit `logging_messages_ko.yml` to clearly establish bilingual dictionary assets.
  - Enhanced `ConfigLoader` to dynamically load either `"KO"` (Korean, default) or `"EN"` (English, case-insensitive) template dictionaries based on `config.yml`'s `logging.language` (or `logging.lang`).
  - Added `ConfigLoader.set_language()` and `ProjectLogger.set_language()` methods/properties for dynamic runtime language switching.
  - Supported project-level dictionary override merging with `config/logging_messages_en.yml`, `config/logging_messages_ko.yml`, and `config/logging_messages.yml`.
- **`ProjectLogger` Exclusion (Skip) Tracking by Log ID and Enhanced Summary Report (`log_summary`)**:
  - Added `record_exclusion()`, `get_excluded_counts()`, `reset_excluded_counts()`, and global aggregation (`_excluded_counts_dict`) in `ProjectLogger` to track exclusions by log ID.
  - Enhanced `record_excluded(log_id_or_count, count_int)` and `update(..., log_id_str)` to automatically track exclusion log IDs while maintaining 100% backward compatibility.
  - Refined `get_error_counts()` and `get_excluded_counts()` to prioritize global aggregation across multi-logger component instances (e.g., `TableDataTransformer` -> `EcsToBigquery`).
  - Added `- 처리 제외 세부 내역 (총 N건):` section to `log_summary()`, dynamically querying `logging_messages_*.yml` message templates to output `* <log_id> (<description>): N items`.
  - Added `excluded_counts_dict` and `error_counts_dict` forwarding to `ProgressTracker.log_summary()`.

### v0.4.23 (2026-09-03)
- **Bilingual Documentation (Korean/English) & GitHub Integration for README/CHANGELOG**:
  - Added language jump anchor links (`[ 🇰🇷 한국어 ]` / `[ 🇺🇸 English ]`) at the top of `README.md` to enhance navigation on PyPI and GitHub.
  - Symmetrically mirrored full package documentation in English and created dedicated `CHANGELOG_EN.md`.
  - Fixed broken relative `CHANGELOG.md` links on PyPI by linking to the official GitHub remote repository.
  - Configured `[project.urls]` (Repository, Changelog) in `pyproject.toml` and updated package manifest (`MANIFEST.in`).

### v0.4.22 (2026-09-03)
- **Standard `src` Layout Migration and Package Size Optimization for Public PyPI Distribution**:
  - Isolated and relocated package source code (`*.py`) and resources (`config/`, `schemas/`, `tool/`) into standard `src/agent_common/` subdirectories.
  - Migrated `pyproject.toml` to standard package auto-discovery via `[tool.setuptools.packages.find] where = ["src"]`.
  - Updated `MANIFEST.in` and pruned large build artifacts (`whls/`, `dist/`, `build/`) from sdist and wheel distribution archives.
  - Minimized distribution package size (from dozens of MBs down to ~50KB) by excluding unnecessary local dependencies and build artifacts.

### v0.4.21 (2026-09-03)
- **Lowered Default Chunk Size in `BigQueryClient.merge_table_from_json_data` to Prevent BigQuery API 413 Payload Too Large Errors**:
  - Decreased `chunk_size_int` default from `500` to a safer `100`.
  - Prevented HTTP `413 (Payload Too Large)` errors caused by exceeding BigQuery SQL query parameter (`@json_payload`) size limits (1MB / 1,024KB), ensuring stable MERGE operations for large unstructured metadata.
  - Updated docstring default values.

### v0.4.20 (2026-09-02)
- **`ProjectLogger` Error & Progress Classification (Success/Failure/Excluded) Aggregation, `log_summary` Transferred to Logger SRP**:
  - Added `ProjectLogger.update(success_bool, excluded_bool, count_int)`, `record_result()`, `record_success()`, `record_failure()`, `record_excluded()`, and `get_result_counts()` to centralize progress count classification in the logger.
  - Improved `ProjectLogger.error()`, `exception()`, `critical()`, and `log_msg()` to automatically accumulate log IDs and failure counts into internal `error_counts_dict` / `failure_count_int`.
  - Integrated `get_log_id_description()` (extracting descriptions from `logging_messages.yml`) and `log_summary()` (generating final execution summary reports) into `ProjectLogger`.
  - Restructured `ProgressTracker.update(count_int=1, bytes_int=0, details_str="")` so that `ProgressTracker` acts as a lightweight tracker focusing solely on raw counts, bytes, percentage (%), and milestones.
  - Synchronized tracker and logger invocation interfaces in main pipeline applications (`ecs_to_gcs.py`, `ecs_to_bigquery.py`, `ecs_to_gcsbigquery_merge.py`).

### v0.4.19 (2026-09-02)
- **Renamed and Standardized `BigQueryClient.format_timestamp` to `BigQueryClient.convert_to_bigquery_timestamp`**:
  - Renamed the method to `convert_to_bigquery_timestamp` to explicitly convey its purpose of converting various raw datetime formats (YYYYMMDD, YYYYMMDDHHMMSS, ISO 8601, etc.) into standard BigQuery timestamp (`YYYY-MM-DD HH:MM:SS{tz}`) strings.
  - Synchronized call sites and references across `table_transformer.py` and downstream scripts.

### v0.4.18 (2026-09-01)
- **`BigQueryClient.merge_table_from_json_data` Directly Return `JSON_VALUE` in UNNEST SELECT and Enhanced SQL Type Casting**:
  - Removed unnecessary `STRING(...)` function wrapping over `JSON_VALUE(...)` return values to resolve `400 No matching signature for function STRING` SQL query syntax errors.
  - Enhanced type casting branches (`DATETIME(...)`, `DATE(...)`, `TIME(...)`, `SAFE_CAST(...)`) when explicit column types (`column_types_dict`) such as `DATETIME`, `DATE`, `TIME`, `INT/BIGINT/NUMERIC/FLOAT` are supplied.

### v0.4.17 (2026-09-01)
- **`BigQueryClient.merge_table_from_json_data` Full Backtick (`` ` ``) Quoting for Column Names and Identifiers**:
  - Applied backtick quoting across `ON` clauses (`T.`{pk}` = S.`{pk}``), `UPDATE SET` clauses (`T.`{col}` = S.`{col}``), `INSERT` column lists (`(`{col1}`, `{col2}`)`), `VALUES` lists (`(S.`{col1}`, S.`{col2}`)`), and UNNEST SELECT aliases (`AS `{col}``).
  - Prevented syntax conflicts with Korean column names, identifiers containing whitespace or special symbols, and BigQuery reserved keywords (`order`, `status`, `date`, `group`, etc.).
  - Applied double-quote escaping (`$.\"{col}\"`) within JSONPath expressions for unicode and special key parsing stability.

### v0.4.16 (2026-09-01)
- **`ProgressTracker` Log ID-based Exception Aggregation and Dynamic `logging_messages.yml` Summary Report (`log_summary`) Support**:
  - Added `self.error_counts_dict: dict[str, int]` and error accumulation method `record_error(error_type_str, count_int=1)`.
  - Added `merge_error_counts(other_error_counts_dict)` for aggregating error statistics across multi-stage pipelines.
  - Supported `update(..., error_type_str="")` parameter to update failure counts and error types simultaneously.
  - Dynamically resolved and sanitized message templates from `agent_common/config/logging_messages.yml` and `config/logging_messages.yml` via `ConfigLoader` without hardcoded dictionaries.

### v0.4.15 (2026-09-01)
- **`ProjectLogger` Program-specific Differentiated Logging Levels (`logging.level.<app_name>`) Support**:
  - When configuring a dictionary under `logging.level` in `config.yml` (`ecs_to_gcs`, `ecs_to_bigquery`, `ecs_to_gcsbigquery_merge`), matched application names (`app_name` or `sys.argv[0]`) to apply fine-grained logging levels.
  - Maintained full backwards compatibility with single string settings (`logging.level: "INFO"`).

### v0.4.14 (2026-08-31)
- **`ReadOnlyConfig` & `ConfigLoader` Type Guarantee and Automatic Type Coercion via Type Suffixes**:
  - `_int`: Guaranteed automatic integer conversion via `int()`
  - `_float`: Guaranteed automatic float conversion via `float()`
  - `_bool`: Guaranteed automatic boolean conversion (`"true"`, `"false"`, `1`, `0` string/numeric support)
  - `_str`: Guaranteed automatic string conversion and `.strip()` whitespace trimming
  - `_list` / `_dict`: Guaranteed list / immutable dictionary (`ReadOnlyConfig`) wrapping
  - Eliminated repetitive defensive type conversion code at invocation sites.

### v0.4.13 (2026-08-30)
- **`ReadOnlyConfig` & `ConfigLoader` Automatic `.strip()` for `_str` Suffix Settings**:
  - Automatically applied `.strip()` when retrieving configuration keys ending with `_str` in `ReadOnlyConfig.__getattr__`, `ConfigLoader.setting()`, and `ConfigLoader.require_setting()`.

### v0.4.12 (2026-08-30)
- **Cleaned Up Unused Functions, Intermediate Variables, and Redundant Imports in `ConfigLoader`**:
  - Removed pass-through wrapper `configure()` and redundant getter `config_dir_get()` (standardized to Python property `@property def config_dir`).
  - Consolidated global config binding directly into `config = ReadOnlyConfig(ConfigLoader())`.
  - Preserved `ensure_config_file()` for self-healing and automated configuration generation.

### v0.4.11 (2026-08-30)
- **Refactored `ReadOnlyConfig` & Global `config` Binding Structure (Adhering to AGENTS.md 1.4.6)**:
  - Eliminated redundant delegation pass-through properties in `ConfigLoader`.
  - Extended `ReadOnlyConfig` to accept `ConfigLoader` instances directly in addition to `dict`, allowing real-time dot-notation lookups (`config.ecs.base_folder`).

### v0.4.10 (2026-08-28)
- **Removed Redundant `get()` Method on `ReadOnlyConfig` and Standardized on Dot-notation**:
  - Unified configuration access strictly on `config.section.key` dot-notation and indexing (`config['section']`) in accordance with AGENTS.md 1.4.2 and Fail-Fast principles.

### v0.4.9 (2026-08-26)
- **Standardized Korean Terminology Across Comments and Docstrings**:
  - Standardized technical terms in `tool_parser.py`, `error_handler.py`, `config_loader.py`, and `logging_messages.yml`.

### v0.4.8 (2026-08-26)
- **`ProgressTracker` Zero Item Handling (`total_items_int=0`) and `ZeroDivisionError` Prevention**:
  - Handled 0 total items cleanly with `max(0, total_items_int)` for accurate summary reporting.
  - Used `max(1, self.total_items_int)` as divisor during percentage calculations to prevent `ZeroDivisionError`.

### v0.4.7 (2026-08-25)
- **Made `fastapi` Dependency Optional and Minimized Package Footprint**:
  - Switched `fastapi` imports in `error_handler.py` to dynamic `try-except` loading.
  - Excluded `fastapi` from required dependencies in `pyproject.toml` to prevent conflicts in air-gapped environments.

### v0.4.6 (2026-08-24)
- **Hardened Exception Handling in `ProjectLogger.configure` Directory and Handler Creation**:
  - Added robust exception handling (`PermissionError`, `OSError`) around log directory creation and file handler initialization.
  - Gracefully falls back to console output (`StreamHandler`) if log directory permissions fail.

### v0.4.5 (2026-08-24)
- **Added Groq Qwen 3.6 27B and GPT-OSS-20B Model Profiles in `llmpool.yml`**:
  - Added `groq_qwen_36_27b` (`qwen/qwen3.6-27b`) and `groq_gpt_oss_20b` (`openai/gpt-oss-20b`).

### v0.4.4 (2026-08-24)
- **Adhered to AGENTS.md 1.4.1 (Removed Inner Nested Functions in Methods)**:
  - Extracted nested helper functions in `ProjectLogger.get_log_msg` and `ToolParser.eval` into independent private class methods.

### v0.4.3 (2026-08-24)
- **Streamlined Groq Model Profiles in `llmpool.yml` & Standardized on `openai/gpt-oss-120b`**:
  - Removed unsupported legacy model profiles.
  - Standardized on `groq_gpt_oss` (`openai/gpt-oss-120b`).
  - Renamed parameter `code` to `msg_code_str` in `ProjectLogger.get_log_msg` to prevent `TypeError` collisions with `kwargs`.

### v0.4.2 (2026-08-24)
- **Built Groq Model Pool Integration Foundation**:
  - Added `groq_gpt_oss` profile and integrated Groq OpenAI-compatible endpoints.

### v0.4.1 (2026-08-21)
- **Fixed Undefined Variable in `BigQueryClient.load_table_from_json_data`**:
  - Safely bound `table_target` to `self.table_obj` or `table_ref`.
  - Standardized logger instance references to `self.logger` across all client classes.

### v0.4.0 (2026-08-21)
- **Added `ToolParser` and Dual-Hierarchy Tool Directory Architecture (Major Update)**:
  - Introduced `ToolParser`: Dynamic loader for dual tool hierarchies (Priority 1: Built-in `agent_common/tool`, Priority 2: Project `medallion/tool`) with `{ }` template evaluation engine.
  - Added built-in date tools in `agent_common/tool/date/`: `DateTimeUtils`, `get_now_compact`, `get_today`, `get_now_formatted`.
  - Extended standard system namespace `sys` with schema `agent_common/schemas/sys.json` (`{sys.now_compact}`, `{sys.timestamp_compact}`).
  - Exported `ToolParser` from top-level `agent_common` package (`from agent_common import ToolParser`).

### v0.3.80 (2026-08-21)
- **Standardized Source Code Header Designer & Organization Metadata**:
  - Standardized author and copyright header comments across all modules.

### v0.3.79 (2026-08-21)
- **Added General SELECT Query Execution Method (`query`) in `BigQueryClient`**:
  - Supported executing arbitrary SQL queries and returning rows as `list[dict[str, Any]]`.

### v0.3.78 (2026-08-20)
- **Simplified JSON Input Data Normalization and Branching in `BigQueryClient`**:
  - Cleaned up repetitive conditional logic in data loading and merge methods.

### v0.3.77 (2026-08-20)
- **Proactive Filtering of Deleted Assets (`asstStusCd == '09'`) and Log Templates for BigQuery Load**:
  - Added `bq_deleted_asst_stus_skipped` warning templates.
  - Implemented proactive filtering before GCS existence checks.

### v0.3.76 (2026-08-20)
- **Introduced `ProgressTracker` Utility & Batch Real-time Progress / Summary Report System**:
  - Created `ProgressTracker` class for tracking `[N/Total] (P%)`, throughput, elapsed time, and ETA.
  - Supported milestone log elevation to `WARNING` level at regular intervals (default 10%).
  - Output final execution summary report at job completion.

### v0.3.75 (2026-08-20)
- **Added File Logging Toggle (`logging.file_logging` & CLI `--file-log`/`--no-file-log`)**:
  - Enabled dynamic toggling of file logging handler creation.

### v0.3.74 (2026-08-20)
- **Added BigQuery TIMESTAMP Timezone Offset (`bigquery.timezone_offset`) Configuration**:
  - Defaulted to `+09:00` (KST) while preserving existing timezone offsets (`Z`, `+09:00`).

### v0.3.73 (2026-08-20)
- **Improved Call Site Source Location Tracking (`stacklevel=2`) in `ProjectLogger`**:
  - Output exact caller filename, line number, and function name instead of logger adapter internals.

### v0.3.72 (2026-08-19)
- **Added BigQuery Truncate Warning and Operation Cancellation Log Templates**:
  - Registered `table_truncate_warning` and `operation_cancelled_by_user` in `logging_messages.yml`.

### v0.3.71 (2026-08-19)
- **Removed Pass-through Wrapper Method `BigQueryClient.insert_json_data`**:
  - Standardized on explicit API methods (`load_table_from_json_data`, `insert_rows_json_data`, `merge_table_from_json_data`).

### v0.3.70 (2026-08-18)
- **Removed Hardcoding from `ConfigLoader.require_setting` and Isolated File Loading**:
  - Defaulted `config_file` to `None` and isolated custom path loads from global cache.

### v0.3.69 (2026-08-18)
- **Extended `ConfigLoader.require_setting` for Multi-path and Domain Rule Files**:
  - Supported verifying arbitrary relative or absolute rule paths outside `config/`.

### v0.3.68 (2026-08-18)
- **Hardened Logger and Exception Handling in `GcsClient`**:
  - Fixed logger attribute binding and connection error formatting.

### v0.3.67 (2026-08-17)
- **Eliminated Module-level Legacy Function Aliases & Standardized on `ConfigLoader` OOP**:
  - Cleaned up top-level aliases in favor of instance methods.

### v0.3.66 (2026-08-17)
- **Supported Automatic Discovery and Merging of YAML Configurations under `schemas/`**:
  - Auto-merged `schemas/**/*.yml` into hierarchical `config` object.

### v0.3.65 (2026-08-17)
- **Generalized Database Retry and Failure Log Templates (`db_load_*`)**:
  - Centralized generic database retry/fallback templates into `agent_common`.

### v0.3.64 (2026-08-17)
- **Unified `db_merge_load_failed` and `storage_client_init_failed` Templates**:
  - Generalized vendor-specific error messages.

### v0.3.63 (2026-08-17)
- **Standardized `{service_name}` Placeholder in DB Logging Templates**:
  - Parameterized database service name across all log messages.

### v0.3.62 (2026-08-17)
- **Added Generic Bulk Load Log Templates (`db_bulk_load_*`) to `agent_common`**:
  - Promoted bulk load lifecycle logs to common standards.

### v0.3.61 (2026-08-17)
- **Unified Client Initialization Log Template (`client_initialized`)**:
  - Single standard message template for all client initializations.

### v0.3.60 (2026-08-17)
- **Added `db_transfer_skipped` Generic Log Message Template**:
  - Registered skip logging for pre-transfer evaluations.

### v0.3.59 (2026-08-17)
- **Applied Strict Type Suffixes and Korean Docstrings to `clients.py`**:
  - Adhered to AGENTS.md 1.6 type suffix conventions.

### v0.3.58 (2026-08-17)
- **Clarified DB Table Merge Exception Key (`merge_failed` $\rightarrow$ `db_table_merge_failed`)**:
  - Improved diagnostic clarity for merge failures.

### v0.3.57 (2026-08-17)
- **Cleaned Up Duplicate Definitions and Docstring Typo in `clients.py`**:
  - Removed duplicate `merge_table_from_json_data` header.

### v0.3.56 (2026-08-17)
- **Removed Domain Column/Constant Hardcoding from `BigQueryClient.merge_table_from_json_data`**:
  - Converted into a purely generic, domain-agnostic MERGE utility with automatic type inference.

### v0.3.55 (2026-08-17)
- **Standardized Log Message Key Prefixes (`db_`, `storage_`)**:
  - Removed vendor dependencies from logging dictionary keys.

### v0.3.54 (2026-08-17)
- **Generalized Common Log Templates and Separated Domain Messages**:
  - Separated project-specific messages from universal common library templates.

### v0.3.53 (2026-08-17)
- **Comprehensive Audit and Registration of Missing Log Message Templates**:
  - Registered 100% of missing templates across ECS, GCS, and BigQuery operations.

### v0.3.52 (2026-08-17)
- **Hardened Exception Handling in `ConfigLoader._find_project_root`**:
  - Added protection for CLI/REPL environments.

### v0.3.51 (2026-08-17)
- **Standardized All Exception Logging on `logger.exception` in `clients.py`**:
  - Preserved complete stack trace and contextual information across all client calls.

### v0.3.50 (2026-08-17)
- **Applied `logger.exception` in `ConfigLoader` Self-healing Blocks**:
  - Captured full tracebacks during configuration file generation or repair failures.

### v0.3.49 (2026-08-16)
- **Added Self-healing and Auto-repair Logging Templates in `logging_messages.yml`**:
  - Added templates for config creation, repair notices, and failure warnings.

### v0.3.48 (2026-08-16)
- **Unified Datetime Formatting in `ConfigLoader` via `DateTimeUtils.get_now_formatted`**:
  - Removed ad-hoc `time.strftime` calls in favor of standardized utility.

### v0.3.47 (2026-08-16)
- **Introduced Standard Datetime Utility Class (`DateTimeUtils`)**:
  - `get_today_yyyymmdd()`, `get_now_formatted()`, `get_now_compact()`.

### v0.3.46 (2026-08-16)
- **Added `BigQueryClient.format_timestamp` for Standard Timestamp Formatting**:
  - Unified datetime conversion to BigQuery `YYYY-MM-DD HH:MM:SS` format.

### v0.3.45 (2026-08-16)
- **Added Defensive Deletion Checks and Cascading Deactivation in `merge_table_from_json_data`**:
  - Handled cascading updates for related attachments on parent deletion.

### v0.3.44 (2026-08-16)
- **Added Missing Standard Library and Type Hint Imports in `clients.py`**:
  - Resolved `time`, `json`, `List`, and `Optional` imports.

### v0.3.43 (2026-08-16)
- **Added Universal MERGE INTO (Upsert) Support in `BigQueryClient`**:
  - Implemented inline MERGE via `UNNEST(JSON_QUERY_ARRAY(@json_payload))` without requiring temporary table creation permissions.

### v0.3.42 (2026-08-16)
- **Restored Complete Parameter and Return Value Korean Docstrings in `ConfigLoader`**:
  - Enforced AGENTS.md rule 2.2 docstring specifications across all methods.

### v0.3.41 (2026-08-16)
- **Streamlined Config Auto-repair Comments to Inline Format**:
  - Replaced bulky header blocks with clean inline comments (`# [auto-repaired: YYYY-MM-DD]`).

### v0.3.40 (2026-08-16)
- **Added Repair Notice Header Blocks on Config Auto-repair**:
  - Recorded repaired key lists and repair timestamp.

### v0.3.39 (2026-08-16)
- **Separated Notice Header Templates into `default_agent_common.yml`**:
  - Eliminated hardcoded strings in source code.

### v0.3.38 (2026-08-16)
- **Added Notice Header Block on Config Auto-creation**:
  - Detailed auto-creation purpose and instructions on modifying connection parameters.

### v0.3.37 (2026-08-16)
- **Supported Domain-specific Schema Registration (`register_schema`) and Self-healing (`ensure_config_file`)**:
  - Enabled dynamic schema registration and auto-generation/repair of missing configuration keys.

### v0.3.36 (2026-08-15)
- **Introduced Dot-notation Read-only Config Class `ReadOnlyConfig` and Singleton `config`**:
  - Direct hierarchical attribute access (`config.ecs.endpoint_url`) with immutable runtime protection.

### v0.3.35 (2026-08-15)
- **Added `write_disposition` Support in `BigQueryClient.load_table_from_json_data`**:
  - Dynamic support for `WRITE_TRUNCATE` and `WRITE_APPEND`.

### v0.3.34 (2026-08-14)
- **Added Dynamic `{app_name}` Placeholder and ISO 8601 Timestamp Format in `ProjectLogger`**:
  - Supported program-specific log naming and ISO 8601 formatting.

### v0.3.33 (2026-08-13)
- **Differentiated Log Storage Directories (`out_file` vs `debug_file`) by Log Level**:
  - Separated `logs/link/out/` (ERROR+) and `logs/link/debug/` (WARNING-).

### v0.3.32 (2026-08-12)
- **Added Usage Example Comments for `load_table_from_json_failed` in `logging_messages.yml`**:
  - Documented exception handling patterns.

### v0.3.31 (2026-08-12)
- **Added Detailed Traceback Logging on BigQuery Load Failures**:
  - Captured full exception info in `logger.exception`.

### v0.3.30 (2026-08-12)
- **Explicitly Separated BigQuery Load Methods**:
  - Separated `load_table_from_json_data` (batch) and `insert_rows_json_data` (streaming).

### v0.3.29 (2026-08-12)
- **Switched to Multi-line Log Formatting**:
  - Preserved multi-line tracebacks for modern centralized log collectors.

### v0.3.27 (2026-08-10)
- **Bundled `json_process_error` Log Template in Base Package**:
  - Ensured built-in availability of JSON processing error messages.

### v0.3.26 (2026-08-10)
- **Added Configuration File Key Tracer (`_loaded_files_summary`) and `.yaml` Extension Support**:
  - Tracked loaded files and root keys in diagnostic logs.

### v0.3.25 (2026-08-10)
- **Removed Class-level Monkey-patching and Isolated `ConfigLoader` Instances**:
  - Converted to instance-level independent cache (`_cached_settings`).

### v0.3.24 (2026-08-10)
- **Enhanced Project Root Detection (`_find_project_root`) with 3-tier Fallback**:
  - Supported symlink resolution and `sys.argv[0]` parent tracking.

### v0.3.23 (2026-08-10)
- **Added Formatted Searched Candidate Path List (`SEARCHED_CANDIDATES`) in Fail-Fast Logs**:
  - Clarified searched filesystem paths and existence states.

### v0.3.22 (2026-08-10)
- **Applied Lazy Property for `logger` in Storage Clients**:
  - Prevented initialization `AttributeError` during client construction.

### v0.3.21 (2026-08-10)
- **Switched to Flat Layout and Specified `package-dir`**:
  - Simplified package structure and wheel bundling.

### v0.3.20 (2026-08-10)
- **Fixed Package Data Bundling for `logging_messages.yml`**:
  - Bundled template dictionaries properly in wheel distributions.

### v0.3.19 (2026-08-10)
- **Applied SafeDict in `ProjectLogger.get_log_msg`**:
  - Prevented raw key exposure and `KeyError` exceptions.

### v0.3.18 (2026-08-10)
- **Enhanced Absolute Path Tracking in `ConfigLoader.require_setting` Fail-Fast Logs**:
  - Printed full path diagnostics on missing required configuration.

### v0.3.17 (2026-08-10)
- **Dynamic Project Root Resolution for Subdirectory Execution**:
  - Resolved `config/config.yml` reliably when scripts run from subdirectories.

### v0.3.16 (2026-08-10)
- **Added Built-in Key Descriptions (`DEFAULT_KEY_DESCRIPTIONS`) in `require_setting`**:
  - Provided descriptive Korean context for missing essential settings.

### v0.3.15 (2026-08-10)
- **Hardened Template Formatting Safety in `ProjectLogger.get_log_msg`**:
  - Escaped braces and preserved parameters on formatting failure.

### v0.3.14 (2026-08-10)
- **Created Rule Evaluation Log Templates and Standardized Pipeline Logging**:
  - Added `rule_eval_success`, `rule_eval_failed`, `rule_not_found`.

### v0.3.13 (2026-08-10)
- **Added `ConfigLoader` Directory Accessors (`config_dir_get`, `config_dir_set`)**:
  - Supported explicit configuration directory mutation.

### v0.3.12 (2026-08-10)
- **Integrated Standard Logger Methods with Message Template Dictionary**:
  - Supported `logger.info("code", **kwargs)` direct template resolution.

### v0.3.11 (2026-08-09)
- **Refactored `ProjectLogger` to Canonical Adapter Pattern**:
  - Supported direct `ProjectLogger(name)` constructor instantiation.

### v0.3.10 (2026-08-09)
- **Parameterized Dynamic Field Names in `api_missing_field`**:
  - Replaced hardcoded field names with `{field_name}`.

### v0.3.9 (2026-08-09)
- **Standardized Logging in LLM Module (`llm.py`)**:
  - Replaced ad-hoc logging with centralized template codes.

### v0.3.8 (2026-08-09)
- **Generalized HTTP/REST API Service Logging Keys**:
  - Unified HTTP service error templates.

### v0.3.7 (2026-08-09)
- **Promoted `storage_meta_error` and Enabled Recursive Category Search in `get_log_msg`**:
  - Supported multi-category fallback searching.

### v0.3.6 (2026-08-09)
- **Hierarchical Sub-categorization in `logging_messages.yml`**:
  - Structured templates into `lifecycle`, `storage`, `fallback`, `permission`, `config`, `service`, `system`.

### v0.3.5 (2026-08-09)
- **Enhanced Code Call Guides and Comments in `logging_messages.yml`**:
  - Provided copy-paste invocation examples.

### v0.3.4 (2026-08-08)
- **Promoted System-wide Generic Log Templates to Common Library**:
  - Removed vendor dependencies from lifecycle log messages.

### v0.3.3 (2026-08-08)
- **Encapsulated `ConfigLoader` Class and Applied Dynamic Logger Names**:
  - Dynamically bound class names to logger instances.

### v0.3.2 (2026-08-08)
- **Created Multi-level Message Template Dictionary (`logging_messages.yml`)**:
  - Unified `errors.yml` into comprehensive template dictionary.

### v0.3.1 (2026-08-08)
- **Added `EcsClient.transfer_to_gcs` Streaming File Transfer Utility**:
  - Integrated ECS to GCS streaming transfer with milestone timings and logging.

### v0.3.0 (2026-08-08)
- **Added Fail-Fast Configuration Verification Method (`require_setting`)**:
  - Enforced early program termination on missing required configuration.

### v0.2.9 (2026-07-29)
- **Auto-fallback to Streaming Mode on Initial BigQuery Batch Failure**:
  - Handled permission limitations gracefully without repetitive warnings.

### v0.2.8 (2026-07-29)
- **Enhanced Exception Origin Tracking (`[Origin: filename:Llineno in funcName()]`)**:
  - Automatically attached initial exception raise site to log headers.

### v0.2.7 (2026-07-29)
- **Enhanced Caller Source Tracking and BigQuery Sub-error Tracing**:
  - Included detailed location and reason fields in error logs.

### v0.2.6 (2026-07-28)
- **Automatic Fallback from Batch Load to Streaming Insert**:
  - Robust BigQuery ingestion fallback.

### v0.2.5 (2026-07-27)
- **BigQuery Native JSON Type Schema Binding**:
  - Bound Table schemas to ensure accurate JSON column encoding.

### v0.2.4 (2026-07-27)
- **Detailed BigQuery Ingestion Failure Logging**:
  - Captured location, reason, and detailed diagnostic messages.

### v0.2.3 (2026-07-27)
- **Added `BigQueryClient.get_existing_keys` for Duplicate Check**:
  - Avoided duplicate loads via key inspection.

### v0.2.2 (2026-07-21)
- **Added Network Timeout Configuration and Fail-Fast Validation**:
  - Enforced `transfer.timeout_seconds` across ECS, GCS, and BigQuery clients.

### v0.2.1 (2026-07-20)
- **Unified Error Message Dictionaries and Fixed Package Directory Resolution**:
  - Auto-merged common error configurations.

### v0.2.0 (2026-07-20)
- **Added Infrastructure Client Modules & Single-line Log Flattening**:
  - Added `EcsClient`, `GcsClient`, `BigQueryClient`, and `SingleLineFlattenFormatter`.

### v0.1.0 (2026-06-18)
- **Initial Release**:
  - Core `config_loader`, `logging_config`, `error_handler`, and `llm` package modules.
