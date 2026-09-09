# AGENTS.md

## 1. Coding Rules

### 1.1. No Hardcoding & Configuration/Secret Separation

1.1.1. Do not embed configuration values, file paths, API URLs, credentials (passwords/API keys), UI labels, or log/error messages directly into source code. Thoroughly separate code and data by loading them from environment variables or dedicated configuration files (e.g., YAML). (Simple log formats for debugging are permitted.)

1.1.2. Manage patterned datasets and heuristic rules (regex patterns, decision thresholds) in dedicated dictionary-structured configuration files (e.g., YAML).

### 1.2. Standard Library First & Vulnerability (CVE) Minimization

1.2.1. Prioritize Python standard libraries (`urllib.request`, `json`, `csv`, `pathlib`) over third-party packages to prevent security vulnerability (CVE) detection, avoiding heavy HTTP client packages (e.g., `requests`).

1.2.2. When third-party packages are required, explicitly specify security-patched versions and ensure periodic `pip-audit` verification.

### 1.3. Fail-Fast & Program Stability

1.3.1. Required configuration values must be defined in configuration files. If missing, do not fallback to code constants; report via logs and terminate immediately (Fail-Fast). (Optional settings may use default fallbacks: `""`, `[]`, `{}`, `None`, `0`, `Exception`.)

1.3.2. Program termination due to missing configuration must only occur during the early execution phase (startup/CLI launch). Once startup completes, handle exceptions during request/task processing to prevent abnormal termination and recover gracefully.

### 1.4. Object-Oriented Design, Direct Immutable Config Access & DRY

1.4.1. Design cohesive classes adhering to the Single Responsibility Principle (SRP). Inner/nested functions inside methods or functions are strictly prohibited.

1.4.2. **Direct Immutable Config Access vs Instance State Separation**:
- Directly access global read-only configuration via `config` dot-notation (e.g., `config.ecs.base_folder`, `config.gcs.path_template`). Do not redundantly clone static configurations into `self`.
- Bind object references (`self.rule_evaluator`, `self.logger`) and dynamic runtime state to `self` in `__init__`.

1.4.3. Access/mutate external object data exclusively through accessor methods (Getters/Setters).

1.4.4. **DRY Principle (3+ Repetitions Rule)**: When identical/similar logic repeats 3 or more times, proactively extract it into a dedicated method or common function.

1.4.5. **Code Conciseness & Structural Optimization**: Strive to reduce unnecessary verbosity and character count through clean structural improvements and proper modularization, without compromising semantic clarity, type safety, or architectural principles.

1.4.6. **No Superficial Shell / Pass-through Functions (껍데기 함수 금지)**: Prohibit creating trivial wrapper or forwarding functions that merely delegate calls to another function without adding meaningful logic, validation, or structural abstraction. Consolidate logic directly into the substantive target function to eliminate unnecessary call layers and keep the architecture direct and uncluttered.

### 1.5. Common Module Architecture, No Speculative Coding & Strict Prohibition of Defensive Coding

1.5.1. Universal features (logging, config, errors) must be centralized in `agent_common`. Shared domain logic must be extracted into dedicated program-group common modules. Do not use `print()` for runtime logging in production.

1.5.2. Never write speculative logic, heuristic fallback code, or assume unverified file/schema structures when domain rules or data contracts are ambiguous. Always ask the user directly for explicit clarification before implementing.

1.5.3. **Strict Prohibition of Defensive Coding (방어 코드 작성 엄격 금지 및 Fail-Fast 실현)**:
- **No `**kwargs: Any` or `kwargs.get(...)` for Backward Compatibility / Defensiveness**: Strictly prohibit declaring `**kwargs: Any` or using `kwargs.get()` in functions and methods to absorb undeclared, legacy, or misspelled arguments. Declare only explicit, strictly type-suffixed parameters (`_str`, `_int`, `_bool`, `_list`, `_dict`). Let unexpected arguments raise `TypeError` immediately (Fail-Fast). (The only permissible use of `**kwargs` is for dynamic message formatting in structured loggers, e.g., `logger.info(msg, key=val)`.)
- **No Defensive Right-Hand Type Casting (방어적 우향 형변환 금지)**: Do not wrap variables or function parameters in defensive type conversion functions (`str(...)`, `int(...)`, `bool(...)`) to suppress type discrepancies. Such wrappers mask defects (e.g., converting `None` to `"None"`, or `"false"` to `True`). Ensure unadulterated types flow through the code so contract violations fail fast.
- **No Defensive Null/Empty Fallback Variables (방어적 대체 변수 및 중간 임시 변수 양산 금지)**: Prohibit creating defensive fallback copies inside functions (e.g., `folders_list = target_folders_list if target_folders_list is not None else []` or `[e for e in (effective_list or ["default"])]`). Pass and use canonical parameters directly; do not generate redundant alias variables that clutter logic and cause `NameError` defects.
- **No Permissive / Fuzzy Key Match Fallbacks (퍼지 매칭 및 변형 키 탐색 금지)**: Prohibit implementing permissive key lookup mechanisms (e.g., automatically stripping or attaching type suffixes, case-insensitive key hunting) to accommodate incorrect callers. Every caller and configuration consumer must reference the exact, canonical key name.

### 1.6. Strict Variable Type Suffix Naming & Exception Handling

1.6.1. **Mandatory Type-Suffix Variable Naming**: Append exact data type names as suffixes (`_<type_name>`) to variable names, parameters, and logging keys (e.g., `_str`, `_int`, `_float`, `_list`, `_dict`, `_bool` such as `ecs_key_str`, `total_count_int`).

1.6.2. **Strict Prohibition of Abbreviated Identifiers & Full Descriptive Naming Principle**:
- Strictly prohibit vague abbreviations or shortened names (e.g., `out_file`, `debug_file`, `tmp`, `dir`, `chk`) in variable names, constants, configuration (YAML) keys, and function arguments.
- Write full, descriptive names that fully convey their role, purpose, and domain context (e.g., `output_error_log_file_str`, `debug_log_file_str`, `default_log_file_str`).
- Prevent confusion and defects such as assuming a missing setting and redundantly duplicating variables/keys (e.g., recreating `log_file`).

1.6.3. Avoid reusing confusing, mismatched domain identifiers across different data contexts (e.g., never name a variable `oid` if it represents `asstId`).

1.6.4. Keep `try` blocks as small as possible. Specify explicit exception classes first, with top-level `Exception` at the bottom. Log errors with business context and traceback details exclusively using `logger.exception`.

### 1.7. Schema-Driven Input & Namespace Variable Management

1.7.1. **`schemas/` Specification**: Manage all external data sources (`ecs`, `sys`, `gcs`, `json`) as schema definition files (`ecs.json`, `sys.json` etc.) under `schemas/`.

1.7.2. **Namespace Declarative Template Referencing**: Prohibit hardcoded system substitutions (`type: system`) and implicit variables in mapping configs. Explicitly reference declarative schema namespace paths (e.g., `{ecs.key}`, `{sys.today}`, `{gcs.asst_path}`, `{json.*}`).

1.7.3. **Wildcard Support**: Support wildcard standards (`*`, `?`, `{json.*}`, `{json.meta_*}`) for metadata mapping to serialize data safely without key collisions.

1.7.4. **Single Responsibility for Context Building**: Delegate context creation to `RuleEvaluator.build_context()`.

1.7.5. **Mandatory Project-Wide Default Schema Definition & Self-Healing**:
- All projects and modules must eliminate source code hardcoding and declaratively define all operational configuration values and constants as a **Default Schema** dictionary. (The constant name is not restricted to `APP_DEFAULT_SCHEMA`; single-program projects may use `APP_DEFAULT_SCHEMA`, while multi-program environments can use clear domain-specific schema names such as `ECS_TO_GCS_SCHEMA`, `ECS_TO_BIGQUERY_SCHEMA` in `app_schema.py`.)
- Executable programs (entry points) must pass their respective default schema to `ConfigLoader.register_schema(schema)` and `ConfigLoader.ensure_config_file("config.yml", default_schema=schema)` at early startup to guarantee file auto-creation and missing-key self-healing.
- Common library packages without a main entry point (such as `agent_common`) must define module-specific default schemas in each file to preserve lazy loading and modularity (prohibit forced package-wide schema synthesis).

### 1.8. CLI Input Parameter Option Standardization

1.8.1. **Strict 1-Short & 1-Long Option Rule**: CLI argument parser options must declare exactly one short option and one long option (`add_argument("--<long-option>", "-<short-option>")`). Redundant alias options (3 or more options) are prohibited.

1.8.2. **1:1 Alignment with Airflow DAGs**: Option names must exactly match and align 1:1 with Airflow DAG parameters (e.g., `--lodin-dstlc-cd` / `-ld`, `--date` / `-d`, `--folder` / `-f`, `--limit` / `-l`, `--write-disposition` / `-wd`, `--target-type` / `-t`, `--file-log` / `-fl`, `--no-file-log` / `-nfl`).

---

## 2. Commenting & Docstring Rules

### 2.1. File Header Comment Template (UTF-8 Mandatory)

2.1.1. All source code and documentation containing Korean characters must be saved with **UTF-8 encoding**. Every Python file (`.py`) must begin with the standard header comment and module docstring:

```python
# 작성일: YYYY-MM-DD
# 설계자: 김유상 수석
# 설계자 이메일: bakkus@daum.net

"""
이 파일의 목적과 주요 기능에 대한 상세한 한글 설명입니다.
"""
```

### 2.2. Class & Function Korean Docstrings

2.2.1. Write clear Korean docstrings for all classes describing their role and responsibilities.

2.2.2. All functions and methods must provide Korean docstrings with parameter (`:param`), return value (`:return`), and exception (`:raises`) descriptions:

```python
def example_function(source_key_str: str, max_limit_int: int = 100) -> Optional[dict]:
    """
    지정된 원천 스토리지 키로부터 데이터를 읽어들여 변환 규칙을 적용한 뒤 결과 딕셔너리를 반환합니다.

    :param source_key_str: 읽어들일 대상 원천 스토리지의 파일/객체 경로 키
    :param max_limit_int: 1회 최대 처리 행 수 제한 (기본값: 100)
    :return: 변환 완료된 결과 데이터 딕셔너리 (실패 또는 대상 미존재 시 None)
    :raises ValueError: 필수 파라미터 누락 또는 유효하지 않은 경로 형식 유입 시 발생
    """
```

---

## 3. Logging Rules

3.1. **Korean Log Output**: All application runtime log messages (INFO, WARNING, ERROR) must be written in clear Korean.

3.2. **Newline & Context Preservation**: Format newline characters (`\n`, `\r`) cleanly and log correlation context (request parameters, queries) together with execution results in the same log context.

---

## 4. Virtual Environment & Wheel Package Versioning

4.1. **Use Root Virtual Environment**: Use the workspace root virtual environment (`.venv` or `venv{PYTHON_VERSION}`) for general tasks and utility executions.

4.2. **Mandatory Version Increment & Changelog**: When modifying package modules (e.g., `agent_common`) or building Wheels (`.whl`), bump the version in configuration files (e.g., `pyproject.toml`) and document the detailed changelog in `README.md` before building.
