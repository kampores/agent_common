# 1.2. 不可变点记法查询与运行时保护 (ReadOnlyConfig)

> **所属模块**: `agent_common.config_loader.ReadOnlyConfig`, `agent_common.config_loader.ConfigLoader`  
> **核心全局实例**: `from agent_common.config_loader import config`

---

## 1. 概述与设计初衷

传统基于 Python 原生字典的配置读取方式（如 `config['ecs']['endpoint_url']`）存在诸多隐患：
1. **拼写错误隐蔽**: 字符串键拼写错误无法在静态类型检查或编译阶段暴露。
2. **代码可读性差**: 多层方括号与单双引号嵌套导致视觉干扰和复杂度上升。
3. **运行时篡改风险**: 任意模块或线程可能通过 `config['key'] = new_val` 意外修改全局共享配置，破坏系统其它组件的稳定性。

`ReadOnlyConfig` 是一个兼具**点记法（Dot-notation，属性访问）与严格不可变性（Immutability）**的高性能配置包装器，从根源上杜绝上述缺陷。

---

## 2. 示例配置文件 (`config/config.yml`)

`ReadOnlyConfig` 将如下结构的 YAML 配置文件映射为 Python 属性访问模式：

```yaml
# config/config.yml (示例项目配置文件)
ecs:
  endpoint_url: "https://storage.example.com"
  bucket_name_str: "app-storage-bucket"
  max_retries_int: 3
  timeout_seconds_int: 30

gcs:
  bucket_name_str: "gcp-prod-data-lake"
  prefix_str: "raw_data/events"
  ecscopy_bool: true

bigquery:
  project_id: "company-data-platform"
  dataset_id: "enterprise_dw"
  table_id: "customer_activity_logs"

transfer:
  max_workers_int: 8
  is_active_bool: "true"  # 经类型保障自动转为布尔值 True
  allowed_types_list:    # 保证列表结构
    - "json"
    - "parquet"
```

---

## 3. 核心功能与特性

### 3.1. 直观的点记法（Dot-Notation）层级导航
通过 `config.ecs.endpoint_url`、`config.transfer.max_workers_int` 像访问对象属性一样优雅简洁地读取配置值：
- 嵌套子字典（`dict`）在读取时自动递归包装为新的 `ReadOnlyConfig` 实例。
- 列表（`list`）中包含的字典元素同样会自动包装为 `ReadOnlyConfig`，确保一致的属性读取体验。
- 结合类型后缀（`_int`, `_float`, `_bool`, `_str`, `_list`, `_dict`）提供自动类型转换与保障。

### 3.2. 严格的只读不可变性（Read-Only）
为保障配置完整性，全面拦截所有属性赋值和删除操作：

```python
def __setattr__(self, key: str, value: Any) -> None:
    raise TypeError("config 配置项在运行时不可修改 (Read-Only)。")

def __setitem__(self, key: str, value: Any) -> None:
    raise TypeError("config 配置项在运行时不可修改 (Read-Only)。")

def __delattr__(self, key: str) -> None:
    raise TypeError("config 配置项在运行时不可删除 (Read-Only)。")

def __delitem__(self, key: str) -> None:
    raise TypeError("config 配置项在运行时不可删除 (Read-Only)。")
```

### 3.3. 与原生字典接口的高度兼容
在提供点记法的同时，完整支持 Python 字典标准操作：
- **键索引访问**: `config['ecs']['endpoint_url']`（结果与点记法完全一致）。
- **成员关系测试 (`in` 操作符)**: `'ecs' in config`, `'endpoint_url' in config.ecs`。
- **转换为纯字典**: 通过 `config.to_dict()` 可直接导出原生字典，无缝传递给第三方库（如 Boto3, BigQuery Client）。

---

## 4. 实战代码示例

### 4.1. 全局 `config` 基础查询模式

```python
from agent_common.config_loader import config

# 1. 点记法层级访问 (基于第 2 节的 config.yml)
endpoint_str: str = config.ecs.endpoint_url          # "https://storage.example.com"
bucket_str: str = config.gcs.bucket_name_str         # "gcp-prod-data-lake"
max_workers: int = config.transfer.max_workers_int    # 8 (int 类型保障)
is_active: bool = config.transfer.is_active_bool     # True (bool 类型保障)

# 2. 检查配置项是否存在 (in 操作符)
if "bigquery" in config and "dataset_id" in config.bigquery:
    dataset_name = config.bigquery.dataset_id        # "enterprise_dw"

# 3. 导出为原生字典供第三方 API 调用
ecs_kwargs: dict = config.ecs.to_dict()
```

### 4.2. 运行时篡改拦截（防御性机制）

```python
from agent_common.config_loader import config

try:
    # 尝试篡改配置属性
    config.ecs.endpoint_url = "http://malicious-url:9020"
except TypeError as e:
    print(f"成功拦截修改: {e}")
    # 输出: 成功拦截修改: config 配置项在运行时不可修改 (Read-Only)。

try:
    # 尝试通过字典索引赋值
    config['ecs']['endpoint_url'] = "http://malicious-url:9020"
except TypeError as e:
    print(f"成功拦截修改: {e}")
```

### 4.3. 访问未定义属性的快速失败 (Fail-Fast)

```python
from agent_common.config_loader import config

try:
    non_existent = config.ecs.unknown_property
except AttributeError as e:
    print(f"属性错误: {e}")
    # 输出: 属性错误: config.yml 中未定义该配置项: 'unknown_property'
```

---

## 5. 自定义 `config.yml` 路径的指定方法

默认情况下，`from agent_common.config_loader import config` 自动识别并加载项目根目录下的 `config/config.yml`。

在需要支持**多环境（dev/staging/prod）隔离**、**批处理/单元测试专用配置**或**容器挂载外部卷路径**时，可通过以下 3 种方式自定义配置路径：

### 方法 1. 在 `ConfigLoader` 构造函数中传递自定义路径（推荐）

通过给 `ConfigLoader(config_dir=...)` 传入相对路径或绝对路径，并由 `ReadOnlyConfig` 包装，即可创建独立的配置对象：

```python
from pathlib import Path
from agent_common.config_loader import ConfigLoader, ReadOnlyConfig

# 1) 指定相对项目根目录的路径 (如 environments/prod/config/)
prod_loader = ConfigLoader(config_dir="environments/prod/config")
prod_config = ReadOnlyConfig(prod_loader)

print(prod_config.ecs.endpoint_url)

# 2) 指定系统绝对路径 (如 Docker 挂载目录 /etc/app/config/)
external_loader = ConfigLoader(config_dir=Path("/etc/app/config"))
external_config = ReadOnlyConfig(external_loader)

print(external_config.bigquery.project_id)
```

### 方法 2. 通过 `config_dir` 属性动态修改

可在运行时更新现有 `ConfigLoader` 实例的目录。修改 `config_dir` 会自动使内部缓存失效，并即时重新加载指定目录下的 YAML 文件：

```python
from agent_common.config_loader import ConfigLoader, ReadOnlyConfig

loader = ConfigLoader()

# 通过属性 Setter 切换配置目录（自动清除内部缓存）
loader.config_dir = "custom_configs/batch_job"
# 或调用方法: loader.config_dir_set("custom_configs/batch_job")

batch_config = ReadOnlyConfig(loader)
print(batch_config.transfer.max_workers_int)
```

### 方法 3. 测试用内存字典直接传递

在单元测试（pytest）或 Mock 测试中，无需物理 YAML 文件，可直接向 `ReadOnlyConfig` 传递纯 Python 字典：

```python
from agent_common.config_loader import ReadOnlyConfig

# 单元测试专用 Mock 配置
mock_data = {
    "ecs": {
        "endpoint_url": "https://mock-storage.example.com",
        "timeout_seconds_int": 5
    },
    "transfer": {
        "max_workers_int": "2",  # 自动进行 _int 类型转换
        "dry_run_bool": "true"    # 自动进行 _bool 类型转换
    }
}

# 直接基于字典创建只读配置对象
test_config = ReadOnlyConfig(mock_data)

# 享有与生产环境完全相同的点记法与类型保障
assert test_config.ecs.endpoint_url == "https://mock-storage.example.com"
assert test_config.transfer.max_workers_int == 2       # int 保障
assert test_config.transfer.dry_run_bool is True       # bool 保障
```

---

## 6. 架构开发准则 (关联 AGENTS.md)

- **规则 1.4.2 (Direct Immutable Config Access)**:  
  严禁将静态只读的全局配置重复克隆到类内部的 `self` 实例属性中。  
  必须统一通过 `config.ecs.endpoint_url` 的形式直接引用全局 `config` 对象，保持单一真理源（Single Source of Truth）。
- **多环境隔离**:  
  在批处理脚本或多环境并发场景中，避免直接污染全局 `config`，应通过 `ConfigLoader(config_dir="...")` 显式创建隔离的专用配置实例。
