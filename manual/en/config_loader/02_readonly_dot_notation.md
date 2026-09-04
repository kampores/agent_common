# 02. Immutable Dot-Notation Access (`ReadOnlyConfig`)

> **Module**: `agent_common.config_loader.ReadOnlyConfig`  
> **Global Instance**: `from agent_common.config_loader import config`

---

## 1. Overview & Architectural Intent

Traditional dictionary-based configuration access (`config['ecs']['endpoint_url']`) introduces several reliability and maintainability liabilities in enterprise codebases:
1. **Typo Vulnerability**: Typographical errors in string keys cannot be detected during static linting or code review.
2. **Reduced Readability**: Excessive brackets and quotation marks clutter the business logic.
3. **Runtime Mutation Risks**: Any module or background thread could accidentally execute `config['key'] = new_val`, causing race conditions and subtle cross-module bugs.

`ReadOnlyConfig` resolves these issues by wrapping configurations in an **immutable, dot-notation accessible** proxy object.

---

## 2. Core Capabilities

### 2.1. Intuitive Dot-Notation Traversal
Access settings cleanly like object attributes: `config.ecs.endpoint_url`, `config.transfer.max_workers_int`.

- Nested dictionaries (`dict`) are recursively wrapped in `ReadOnlyConfig` instances upon access.
- Dictionaries inside nested lists (`list`) are also wrapped automatically, ensuring consistent dot-notation down the tree.

### 2.2. Strict Immutability (Read-Only Enforcement)
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

### 2.3. Full Dictionary Compatibility
`ReadOnlyConfig` seamlessly supports standard Python idioms:

- **Bracket Indexing**: `config['ecs']['endpoint_url']` produces the exact same result as `config.ecs.endpoint_url`.
- **Membership Check (`in` operator)**: `'ecs' in config`, `'endpoint_url' in config.ecs`.
- **Dictionary Extraction**: `config.to_dict()` extracts the underlying native `dict` for passing to external SDKs (Boto3, Google Cloud Client, etc.).

---

## 3. Practical Usage Examples

### 3.1. Standard Lookup Patterns

```python
from agent_common.config_loader import config

# 1. Dot-notation attribute access
endpoint_str: str = config.ecs.endpoint_url
bucket_str: str = config.gcs.bucket_name_str

# 2. Key existence check with 'in'
if "bigquery" in config and "dataset_id" in config.bigquery:
    dataset_name = config.bigquery.dataset_id

# 3. Native dictionary export for external libraries
ecs_client_kwargs: dict = config.ecs.to_dict()
```

### 3.2. Mutation Prevention (Defensive Runtime Behavior)

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

### 3.3. Clear Diagnostic on Missing Properties

```python
from agent_common.config_loader import config

try:
    val = config.ecs.non_existent_key
except AttributeError as e:
    print(f"Lookup error: {e}")
    # Output: config.yml에 정의되지 않은 설정 항목입니다: 'non_existent_key'
```

---

## 4. AGENTS.md Architecture Alignment

- **Rule 1.4.2 (Direct Immutable Config Access)**:  
  Do not redundantly clone static configurations into `self` instance variables in class `__init__`.  
  Always access global read-only configuration directly via `config.<namespace>.<property>` to preserve a single source of truth.
