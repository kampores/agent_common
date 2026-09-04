# 1.2. Immutable Dot-Notation Lookup & Runtime Protection (ReadOnlyConfig)

> **Module**: `agent_common.config_loader.ReadOnlyConfig`, `agent_common.config_loader.ConfigLoader`  
> **Global Instance**: `from agent_common.config_loader import config`

---

## 1. Overview & Architectural Intent

Traditional dictionary-based configuration access (`config['ecs']['endpoint_url']`) introduces several reliability and maintainability liabilities in enterprise codebases:
1. **Typo Vulnerability**: Typographical errors in string keys cannot be detected during static linting or code review.
2. **Reduced Readability**: Excessive brackets and quotation marks clutter the business logic.
3. **Runtime Mutation Risks**: Any module or background thread could accidentally execute `config['key'] = new_val`, causing race conditions and subtle cross-module bugs.

`ReadOnlyConfig` resolves these issues by wrapping configurations in an **immutable, dot-notation accessible** proxy object.

---

## 2. Example Configuration File (`config/config.yml`)

`ReadOnlyConfig` maps YAML documents directly to Python object attributes using dot notation. Below is an example configuration file:

```yaml
# config/config.yml (Project Configuration File)
ecs:
  endpoint_url: "http://10.200.10.10:9020"
  bucket_name_str: "pak-unstr-prod"
  max_retries_int: 3
  timeout_seconds_int: 30

gcs:
  bucket_name_str: "gcp-prod-data-lake"
  prefix_str: "raw_data/pak"
  ecscopy_bool: true

bigquery:
  project_id: "company-data-platform"
  dataset_id: "enterprise_dw"
  table_id: "customer_activity_logs"

transfer:
  max_workers_int: 8
  is_active_bool: "yes"  # Automatically converted to bool(True)
  allowed_types_list:    # Guaranteed list structure
    - "json"
    - "parquet"
```

---

## 3. Core Capabilities

### 3.1. Intuitive Dot-Notation Traversal
Access settings cleanly like object attributes: `config.ecs.endpoint_url`, `config.transfer.max_workers_int`.

- Nested dictionaries (`dict`) are recursively wrapped in `ReadOnlyConfig` instances upon access.
- Dictionaries inside nested lists (`list`) are also wrapped automatically, ensuring consistent dot-notation down the tree.
- Key suffix type coercion (`_int`, `_float`, `_bool`, `_str`, `_list`, `_dict`) is automatically applied.

### 3.2. Strict Immutability (Read-Only Enforcement)
Any attempt to mutate or delete configuration keys at runtime raises a `TypeError`:

```python
def __setattr__(self, key: str, value: Any) -> None:
    raise TypeError("config 설정값은 런타임에 수정할 수 없습니다 (Read-Only).")

def __setitem__(self, key: str, value: Any) -> None:
    raise TypeError("config 설정값은 런타임에 수정할 수 없습니다 (Read-Only).")

def __delattr__(self, key: str) -> None:
    raise TypeError("config 설정값은 런타임에 삭제할 수 없습니다 (Read-Only).")

def __delitem__(self, key: str) -> None:
    raise TypeError("config 설정값은 런타임에 삭제할 수 없습니다 (Read-Only).")
```

### 3.3. Full Dictionary Compatibility
`ReadOnlyConfig` seamlessly supports standard Python idioms:

- **Bracket Indexing**: `config['ecs']['endpoint_url']` produces the exact same result as `config.ecs.endpoint_url`.
- **Membership Check (`in` operator)**: `'ecs' in config`, `'endpoint_url' in config.ecs`.
- **Dictionary Extraction**: `config.to_dict()` extracts the underlying native `dict` for passing to external SDKs (Boto3, Google Cloud Client, etc.).

---

## 4. Practical Usage Examples

### 4.1. Standard Lookup Patterns

```python
from agent_common.config_loader import config

# 1. Dot-notation attribute access (Mapped from Section 2 config.yml)
endpoint_str: str = config.ecs.endpoint_url          # "http://10.200.10.10:9020"
bucket_str: str = config.gcs.bucket_name_str         # "gcp-prod-data-lake"
max_workers: int = config.transfer.max_workers_int    # 8 (int guaranteed)
is_active: bool = config.transfer.is_active_bool     # True (bool guaranteed)

# 2. Key existence check with 'in'
if "bigquery" in config and "dataset_id" in config.bigquery:
    dataset_name = config.bigquery.dataset_id        # "enterprise_dw"

# 3. Native dictionary export for external libraries
ecs_client_kwargs: dict = config.ecs.to_dict()
```

### 4.2. Mutation Prevention (Defensive Runtime Behavior)

```python
from agent_common.config_loader import config

try:
    # Attempting to mutate a configuration attribute
    config.ecs.endpoint_url = "http://malicious-url:9020"
except TypeError as e:
    print(f"Mutation blocked: {e}")
    # Output: config 설정값은 런타임에 수정할 수 없습니다 (Read-Only).

try:
    # Attempting to mutate via bracket syntax
    config['ecs']['endpoint_url'] = "http://malicious-url:9020"
except TypeError as e:
    print(f"Mutation blocked: {e}")
```

### 4.3. Clear Diagnostic on Missing Properties

```python
from agent_common.config_loader import config

try:
    val = config.ecs.non_existent_key
except AttributeError as e:
    print(f"Lookup error: {e}")
    # Output: config.yml에 정의되지 않은 설정 항목입니다: 'non_existent_key'
```

---

## 5. Custom Configuration Directory & Paths

By default, `from agent_common.config_loader import config` automatically discovers and loads from the project root's `config/` directory (`config/config.yml`).

However, for **multi-environment deployments (dev/staging/prod)**, **dedicated batch jobs**, or **external mounted volumes**, you can point to custom directories using any of the following 3 approaches:

### Approach 1: Pass Custom Directory to `ConfigLoader` (Recommended)

Instantiate a dedicated `ConfigLoader` with `config_dir` (supporting relative or absolute paths) and wrap it in `ReadOnlyConfig`:

```python
from pathlib import Path
from agent_common.config_loader import ConfigLoader, ReadOnlyConfig

# 1) Relative path from project root (e.g., environments/prod/config/)
prod_loader = ConfigLoader(config_dir="environments/prod/config")
prod_config = ReadOnlyConfig(prod_loader)

print(prod_config.ecs.endpoint_url)

# 2) Absolute OS path (e.g., container volume /etc/app/config/)
external_loader = ConfigLoader(config_dir=Path("/etc/app/config"))
external_config = ReadOnlyConfig(external_loader)

print(external_config.bigquery.project_id)
```

### Approach 2: Dynamically Update via `config_dir` Property / Setter

You can reassign `config_dir` at runtime. Updating `config_dir` automatically invalidates internal caches, triggering an immediate reload on the next access:

```python
from agent_common.config_loader import ConfigLoader, ReadOnlyConfig

loader = ConfigLoader()

# Update configuration directory dynamically (automatically clears cache)
loader.config_dir = "custom_configs/batch_job"
# Or call setter method: loader.config_dir_set("custom_configs/batch_job")

batch_config = ReadOnlyConfig(loader)
print(batch_config.transfer.max_workers_int)
```

### Approach 3: In-Memory Dictionary for Unit Tests (pytest / Mock)

For test suites and mock setups, you can pass a pure Python `dict` directly to `ReadOnlyConfig` without touching the filesystem:

```python
from agent_common.config_loader import ReadOnlyConfig

# Mock data for unit tests
mock_data = {
    "ecs": {
        "endpoint_url": "http://mock-ecs:9020",
        "timeout_seconds_int": 5
    },
    "transfer": {
        "max_workers_int": "2",  # Automatically coerced to int(2)
        "dry_run_bool": "true"    # Automatically coerced to bool(True)
    }
}

# Create ReadOnlyConfig directly from dictionary
test_config = ReadOnlyConfig(mock_data)

# Leverage identical dot-notation and type guarantees as in production
assert test_config.ecs.endpoint_url == "http://mock-ecs:9020"
assert test_config.transfer.max_workers_int == 2
assert test_config.transfer.dry_run_bool is True
```

---

## 6. AGENTS.md Architecture Alignment

- **Rule 1.4.2 (Direct Immutable Config Access)**:  
  Do not redundantly clone static configurations into `self` instance variables in class `__init__`.  
  Always access global read-only configuration directly via `config.<namespace>.<property>` to preserve a single source of truth.
- **Environment Isolation**:  
  When executing batch scripts across multiple environments, avoid mutating global state; instantiate isolated `ConfigLoader(config_dir="...")` instances instead.
