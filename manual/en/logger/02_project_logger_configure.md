# 2.2. Batch Logging Environment Configuration & Handler Control (`ProjectLogger.configure`)

> **Module**: `agent_common.logger.ProjectLogger`  
> **Key Method**: `ProjectLogger.configure(config_dir=None, default_log_file="logs/app.log", app_name=None, file_logging=None)`

---

## 1. Overview & Enterprise Motivation

Python's built-in `logging` module presents notable challenges in distributed architectures and containerized microservices:

1. **Duplicate Handler Collisions**: Multiple modules calling `addHandler()` produce repeated, duplicated log lines.
2. **Scattered Output Management**: Developers need console logs locally, while production environments (Kubernetes, Airflow Pods) often require stdout streams or structured date-partitioned file logs.
3. **Third-Party Debug Log Noise**: High-volume diagnostic logs from packages like `urllib3`, `httpx`, and `botocore` flood output streams and mask critical business events.
4. **Volume Mounting Permissions & Crashes**: Process crashes when target log directories on mounted volumes lack write permissions.

`ProjectLogger.configure()` acts as an enterprise **centralized logging factory**, standardizing the logging environment across the application with a single call.

---

## 2. Architecture & Pipeline

```mermaid
flowchart TD
    A["Invoke ProjectLogger.configure(app_name, file_logging, ...)"] --> B["Load Hierarchical Config via ConfigLoader"]
    B --> C["Determine Log Level (String or app_name mapping)"]
    B --> D["Instantiate Formatter (SingleLineFlattenFormatter)"]
    D --> E["Instantiate StreamHandler for Console"]
    
    A --> F{"Evaluate file_logging Flag"}
    F -->|"False"| J["Attach Console Handler Only"]
    F -->|"True"| G{"Determine Target File by Log Level"}
    
    G -->|"ERROR or Higher"| G1["Use out_file Path"]
    G -->|"WARNING or Lower"| G2["Use debug_file Path"]
    G -->|"Default / Other"| G3["Use log_file Path"]
    
    G1 --> H["Substitute %Y%m%d and {app_name}"]
    G2 --> H
    G3 --> H
    H --> I{"Create Directory & Open FileHandler"}
    I -->|"Success"| I1["Append FileHandler to Handlers List"]
    I -->|"Permission/OS Error"| I2["Emit Warning to stderr & Retain Console Logging"]
    
    E --> K["Apply logging.basicConfig(force=True)"]
    I1 --> K
    J --> K
    I2 --> K
    K --> L["Suppress Third-Party Loggers (metricflow, urllib3, httpx -> WARNING)"]
```

---

## 3. Key Capabilities

### 3.1. Dynamic App-Name Based Log Level Resolution
In `config.yml`, configure per-application log levels using a dictionary:

```yaml
logging:
  level:
    default: "INFO"
    data_exporter: "DEBUG"
    api_server: "WARNING"
```

### 3.2. Level-Based File Routing (`out_file` vs `debug_file`)

`ProjectLogger.configure()` intelligently routes log file destinations based on the resolved `logging.level`:

- **`ERROR`, `CRITICAL` Level (Failure Monitoring Mode)**:
  - Automatically routed to `logging.out_file` to isolate system errors and critical failure logs for on-call engineers.
- **`DEBUG`, `INFO`, `WARNING` Level (Standard Tracing Mode)**:
  - Automatically routed to `logging.debug_file` capturing informational and diagnostic logs.
- **Default / Other**:
  - Saved to `logging.file` if specific level routing keys are omitted.

#### Enterprise Data Pipeline Routing Configuration Example:
```yaml
logging:
  # Program-specific log levels (WARNING and below routes to debug_file)
  level:
    data_extractor: "WARNING"
    stream_processor: "WARNING"
    db_loader: "WARNING"
    
  # Isolated destination for ERROR and CRITICAL runs
  out_file: "logs/pipeline/out/%Y/%m/%d/{app_name}_out_%Y%m%dT%H%M%S.log"
  
  # Standard destination for DEBUG, INFO, and WARNING runs
  debug_file: "logs/pipeline/debug/%Y/%m/%d/{app_name}_debug_%Y%m%dT%H%M%S.log"
```

> 💡 **Behavioral Example**:
> - When `data_extractor` runs with `WARNING` level, logs are written to the `debug_file` path under `logs/pipeline/debug/...`.
> - If the process or CLI flag elevates the level to `ERROR`, logs are automatically redirected to `out_file` under `logs/pipeline/out/...`, enabling clear separation between normal operations and error triage.

### 3.3. Dynamic Path Templating & Recursive Directory Creation

The `out_file`, `debug_file`, and `file` template strings support dynamic placeholders and date specifiers:

1. **`{app_name}` Placeholder**:
   - Replaced by the application name passed to `ProjectLogger.configure(app_name="data_extractor")` (or the script filename).
2. **`%Y/%m/%d` Hierarchical Date Partitioning**:
   - Parsed via `datetime.now().strftime(...)` to automatically organize logs into year/month/day directory trees.
3. **`%Y%m%dT%H%M%S` ISO Compact Timestamp**:
   - Assigns a unique execution timestamp (e.g. `20260904T230715`), ensuring subsequent runs on the same date do not overwrite prior logs.
4. **Recursive Parent Directory Creation (`mkdir(parents=True, exist_ok=True)`)**:
   - Automatically builds missing nested directories (e.g. `logs/pipeline/debug/2026/09/04/`) before creating the file handler.

#### Dynamic Path Resolution Example:
```text
[Template in config.yml]
debug_file: "logs/pipeline/debug/%Y/%m/%d/{app_name}_debug_%Y%m%dT%H%M%S.log"

[Runtime Invocation]
ProjectLogger.configure(app_name="data_extractor", file_logging=True)
Execution Timestamp: 2026-09-04 23:07:15

[Resolved Log File Path]
logs/pipeline/debug/2026/09/04/data_extractor_debug_20260904T230715.log
```

### 3.4. Graceful Degradation on Permission/OS Errors
If directory creation fails due to `PermissionError` or `OSError` in containerized environments, `ProjectLogger` logs a warning to `sys.stderr` and falls back to console logging without crashing the process.

### 3.5. Noise Suppression for Third-Party Libraries
Automatically mutes verbose libraries (`metricflow`, `urllib3`, `httpx`) to `WARNING` level.

---

## 4. Configuration Specification (`config/config.yml`)

```yaml
logging:
  # Program-specific or global log levels
  level:
    data_extractor: "WARNING"
    stream_processor: "WARNING"
    db_loader: "WARNING"
    default: "INFO"
  
  # Message template dictionary language (KO or EN)
  language: "KO"
  
  format: "[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d %(funcName)s()] %(message)s"
  datefmt: "%Y-%m-%d %H:%M:%S"
  file_logging: true
  
  # Production routing templates (enterprise pipeline standard)
  out_file: "logs/pipeline/out/%Y/%m/%d/{app_name}_out_%Y%m%dT%H%M%S.log"
  debug_file: "logs/pipeline/debug/%Y/%m/%d/{app_name}_debug_%Y%m%dT%H%M%S.log"
  
  # Fallback log file path
  file: "logs/%Y%m%d/{app_name}.log"
```

---

## 5. Practical Code Examples

### 5.1. Standard Initialization Entrypoint

```python
from agent_common.logger import ProjectLogger

def main():
    # 1. Initialize logging configuration once at process startup
    ProjectLogger.configure(
        app_name="data_migrator",
        file_logging=True,
        default_log_file="logs/migrator.log"
    )

    # 2. Obtain logger instances in business modules
    logger = ProjectLogger("DataMigrator")
    logger.info("Pipeline initialized successfully")

if __name__ == "__main__":
    main()
```

### 5.2. Integration with Airflow & CLI Flags

```python
import argparse
from agent_common.logger import ProjectLogger

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument("--file-log", "-fl", dest="file_log", action="store_true", default=None)
group.add_argument("--no-file-log", "-nfl", dest="file_log", action="store_false")
args = parser.parse_args()

# Pass CLI preference directly (defaults to config.yml when None)
ProjectLogger.configure(app_name="batch_job", file_logging=args.file_log)
```

---

## 6. Operational Best Practices

1. **Invocation Point**:
   - Call `configure()` exclusively at the entry point of your application (`main()` or CLI startup).
2. **Containerized Deployments**:
   - In Kubernetes or Docker environments, prefer `--no-file-log` (`file_logging: false`) to avoid filling local container storage and defer log collection to container runtime drivers.
3. **Idempotence & `force=True`**:
   - `ProjectLogger.configure()` uses `logging.basicConfig(..., force=True)`, resetting ad-hoc handlers added during module imports.
