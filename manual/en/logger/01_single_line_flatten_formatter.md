# 2.1. Single-Line Flatten Formatter & Exception Origin Tracking (`SingleLineFlattenFormatter`)

> **Module**: `agent_common.logger.SingleLineFlattenFormatter`  
> **Base Class**: `logging.Formatter`  
> **Key Methods**: `SingleLineFlattenFormatter.format(record)`, `SingleLineFlattenFormatter.flatten_to_single_line(text)`

---

## 1. Overview & Enterprise Motivation

In modern cloud, Kubernetes (K8s), and distributed data pipeline (Airflow, Spark, Kafka) environments, centralized log aggregators such as **Logstash**, **Fluentd**, **AWS CloudWatch**, and **GCP Cloud Logging** are standard.

Most log collectors split log streams into records based on **newlines (`\n`)**. When Python applications raise multiline exception tracebacks, this default splitting causes severe operational issues:

1. **Log Fragmentation**: A single traceback is split into dozens of isolated, out-of-context log lines, rendering regex alerts and search queries ineffective.
2. **Delayed Root-Cause Analysis**: The actual line and file where the business logic failed (`Origin`) is buried at the bottom of a lengthy call stack across multiple screen scrolls.
3. **Spike in Ingestion Costs**: Each fragmented line receives its own ingestion metadata, timestamp, and indexing overhead.

`SingleLineFlattenFormatter` solves these challenges by combining **exception origin extraction** with structured multi-line / single-line stream formatting.

---

## 2. Architecture & Formatting Pipeline

```mermaid
flowchart TD
    A[logging.LogRecord Ingestion] --> B{exc_info Present?}
    B -- Yes (Exception Raised) --> C[traceback.extract_tb Stack Inspection]
    C --> D[Extract Innermost Frame<br/>origin_file, lineno, func_name]
    D --> E["Construct Origin Tag<br/>[Origin: file.py:L123 in func()]"]
    B -- No (Standard Log) --> F[Standard String Formatting]
    E --> G[Invoke super().format]
    F --> G
    G --> H{Traceback Newline Present?}
    H -- Yes --> I[Inject Origin into Header and Append Traceback]
    H -- No --> J[Append Origin or Return Formatted Record]
    I --> K[Return Final Log Message]
    J --> K
```

### Key Processing Stages:

1. **Exception Origin Frame Extraction**:
   - When `record.exc_info` is present, `traceback.extract_tb()` retrieves the last stack frame representing the exact failure location in business code.
   - Formats the tag as `[Origin: {origin_file}:L{lineno} in {func_name}()]` and inserts it immediately into the primary log line header.
2. **Preserved Traceback Fidelity**:
   - Integrates the Origin tag into the primary line while preserving complete traceback details for log collectors supporting multiline blocks.
3. **Single-Line Stream Flattening**:
   - Provides `flatten_to_single_line(text)` for environments requiring strict single-line JSON or newline-free streaming.

---

## 3. Core Implementation

```python
class SingleLineFlattenFormatter(logging.Formatter):
    """
    Custom log formatter formatting log records and exception tracebacks.
    Preserves multiline tracebacks while injecting origin metadata.
    """

    def flatten_to_single_line(self, text: str) -> str:
        """Converts newlines (\n, \r) to single spaces."""
        return text.replace("\n", " ").replace("\r", " ")

    def format(self, record: logging.LogRecord) -> str:
        # 0. Extract exception origin information ([Origin: filename:Llineno in funcName()])
        origin_prefix = ""
        if record.exc_info and len(record.exc_info) >= 3 and record.exc_info[2]:
            try:
                import traceback
                tb_list = traceback.extract_tb(record.exc_info[2])
                if tb_list:
                    last_frame = tb_list[-1]
                    origin_file = Path(last_frame.filename).name
                    origin_prefix = f"[Origin: {origin_file}:L{last_frame.lineno} in {last_frame.name}()] "
            except Exception:
                pass

        # 1. Base formatting
        s = super().format(record)

        # 2. Attach origin metadata
        if origin_prefix:
            if "\nTraceback" in s:
                head, tail = s.split("\nTraceback", 1)
                s = f"{head} {origin_prefix}\nTraceback{tail}"
            elif "\n" in s:
                head, tail = s.split("\n", 1)
                s = f"{head} {origin_prefix}\n{tail}"
            else:
                s = f"{s} {origin_prefix}"

        return s
```

---

## 4. Practical Code Examples

```python
import logging
from agent_common.logger import SingleLineFlattenFormatter

# 1. Instantiate formatter
log_format = "[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d %(funcName)s()] %(message)s"
date_fmt = "%Y-%m-%d %H:%M:%S"
formatter = SingleLineFlattenFormatter(fmt=log_format, datefmt=date_fmt)

# 2. Attach to handler
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger("DataService")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# 3. Simulate failure
def process_record(record_dict: dict) -> None:
    try:
        val = record_dict["payload"]
    except KeyError:
        logger.exception("Failed to process incoming record")

process_record({})
```

**Output Example**:
```text
[2026-09-04 22:30:00][ERROR][data_service.py:20 process_record()] Failed to process incoming record [Origin: data_service.py:18 in process_record()] 
Traceback (most recent call last):
  File "data_service.py", line 18, in process_record
    val = record_dict["payload"]
KeyError: 'payload'
```

> 💡 **Notice**: The exact origin file and line `[Origin: data_service.py:18 in process_record()]` are immediately visible on the very first line of the log message, allowing instant identification on log aggregation dashboards.

---

## 5. Operational Best Practices

1. **Leverage `ProjectLogger.configure()`**:
   - Rather than manually wiring `SingleLineFlattenFormatter`, invoke `ProjectLogger.configure()`, which automatically loads `logging.format` and `logging.datefmt` from configuration.
2. **Centralized Log Collector Config**:
   - When using Fluentd, configure the `multiline` parser or utilize single-line flattening if strict one-line JSON events are ingested.
