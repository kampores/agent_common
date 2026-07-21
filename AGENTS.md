# AGENTS.md

## Coding Rules

- **No Hardcoding**: 
  1. Do not embed configuration values, file paths, model names, API URLs, credentials, business constants, UI labels, or user-facing warning/error messages directly into the source code. Instead, separate code and data by loading them from environment variables or dedicated configuration files (e.g., YAML). (However, simple log formats for developer debugging and tracing can be declared in the code.)
  2. Manage sensitive configurations such as passwords or API keys via environment variables.
  3. Manage exception messages, patterned large-scale datasets, heuristic rules, regex patterns, or decision thresholds by organizing them in separate, dedicated dictionary-structured configuration files (e.g., YAML).
- **Fail-Fast and Program Stability**:
  1. Required configuration values for execution must be defined in the configuration file. If a required value is missing, do not fallback to code constants or run blindly; instead, report the missing configuration via logs/CLI and fail fast by immediately terminating the program. However, for optional settings, it is permitted to define and use fallbacks such as an empty string (`""`), an empty list (`[]`), `None` (null), or numeric `0` constants directly in the code.
  2. Program termination due to missing configuration values must only occur during the early execution phase (e.g., server startup lifespan events or CLI launch). Once startup is complete, handle exceptions during request or task processing so that the process does not terminate abnormally, and returns stable error responses or recovers gracefully.
- **Object-Oriented Design**: Apply object-oriented design principles when adding or modifying complex or non-trivial behaviors. Design highly cohesive classes with clearly separated responsibilities (following the Single Responsibility Principle) and avoid writing oversized, procedural functions.
- **Common Module Architecture**: Once the total size of the project's codebase exceeds 2,000 lines of code, design independent classes for `logging`, `config`, and `error` handling inside a `common` package (or directory) to centralize and share their usage across modules. Do not use the `print()` function for runtime logging in production.

## Korean Commenting Rules

- All source code and documentation files containing Korean characters must be saved with UTF-8 encoding.
- Code comments and docstrings must be written in Korean.
- Write a detailed docstring in Korean for all classes and functions, explaining their role, purpose, and design intent.
- Write clear Korean comments for class variables to describe their domain meaning, allowed value ranges, and role in subsequent data flows. Avoid trivial comments that merely repeat the variable name or its type.

## Python File Header Rules

- At the beginning of each Python file (`.py`), record the file creation date, designer (author) name, affiliation, and contact email addresses as comments.
- Place this header comment block at the very top of the file, before the module docstring, import statements, or any executable code.
- Write a module-level docstring in Korean immediately following the header comment block to describe the file's purpose, role, and main functionality.
- Follow this header format strictly:

```python
# 작성일: YYYY-MM-DD
# 설계자: 이름
# 설계자 소속: 회사명
# 설계자 이메일: name@example_corp.com, name@example_personnel.com

"""
이 파일의 목적과 주요 기능 및 설계 의도에 대한 상세한 한글 설명입니다.
"""
```


## Logging Rules

- **Single Line Output**: Output all log records as a single line (Single Line) to facilitate automated log parsing, ingestion, and indexing by external logging systems (e.g., Logstash, Fluentd, CloudWatch).
- **Newline Handling**: Replace any newline characters (`\n`, `\r`) in the log message or serialized data (e.g., SQL queries, LLM responses, exceptions) with spaces or escape sequences to ensure the entire log entry remains flat on a single line.
- **Context Preservation**: For easier debugging and error tracing, log the correlation context (e.g., request parameters or natural language queries) together with the execution results (e.g., generated SQL or warning lists) in the same single-line log context.

## Virtual Environment Rules

- **Use Root Virtual Environment for General Tasks**: When executing general scripts, utility tasks, or installing additional packages via `pip install` that are not specific to any subproject, use the root virtual environment located at the workspace root (e.g., `venv312` or `.venv` at the workspace root) to avoid contaminating subproject-specific virtual environments.
