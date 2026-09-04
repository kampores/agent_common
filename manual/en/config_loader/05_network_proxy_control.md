# 1.5. Network Proxy Control (`_apply_no_proxy`)

> **Module**: `agent_common.config_loader.ConfigLoader`  
> **Key Method**: `ConfigLoader._apply_no_proxy(settings)`

---

## 1. Overview & Enterprise Context

Enterprise environments and hybrid clouds require outbound proxy servers (`HTTP_PROXY`, `HTTPS_PROXY`) to regulate internet-bound egress traffic (such as external LLM API requests).

However, routing traffic destined for **Dell ECS object storage**, **on-premise databases**, or **Kubernetes/cloud metadata endpoints** through an outbound proxy causes major operational disruptions:
1. External proxy appliances cannot resolve private IP addresses or internal domain names, returning `502 Bad Gateway` or `Connection Refused`.
2. Multi-gigabyte data streaming passing through intermediate proxy hardware creates severe bandwidth saturation and performance bottlenecks.

`ConfigLoader` solves this automatically by reading the `proxy.no_proxy` configuration from `config.yml` and **seamlessly synchronizing it with the OS `NO_PROXY` environment variable**.

---

## 2. Operation Mechanism (`_apply_no_proxy`)

During every execution of `ConfigLoader.get_settings()`, `_apply_no_proxy` runs automatically:

```python
def _apply_no_proxy(self, settings: dict[str, Any]) -> None:
    """proxy.no-proxy 설정 값을 NO_PROXY 환경 변수로 적용한다."""
    no_proxy_value = settings.get("proxy", {}).get("no_proxy")
    if no_proxy_value:
        existing = os.environ.get("NO_PROXY", "")
        if existing:
            os.environ["NO_PROXY"] = f"{existing},{no_proxy_value}"
        else:
            os.environ["NO_PROXY"] = str(no_proxy_value)
```

### Key Properties:
1. **Non-destructive Accumulation**:
   - If `NO_PROXY` is already defined in the host OS or parent container (Docker, Kubernetes Pod), the existing values are preserved and the new entries are appended via comma separator.
2. **Zero-Boilerplate Lifecycle**:
   - Requires no manual invocation. Importing `from agent_common.config_loader import config` automatically ensures proxy bypass rules are active for the entire process.
3. **Standard Library Compatibility**:
   - Standard Python network modules (`urllib.request`, `requests`, `boto3`, `google-cloud-storage`) automatically respect the `NO_PROXY` environment variable, ensuring uniform behavior across all HTTP clients.

---

## 3. Configuration Format (`config/config.yml`)

Configure the `proxy` block in `config/config.yml`:

```yaml
proxy:
  # Outbound proxies for external connectivity (if required)
  http_proxy: "http://proxy.example.com:8080"
  https_proxy: "http://proxy.example.com:8080"
  
  # Comma-separated list of internal hosts, IPs, and domain suffixes to bypass
  no_proxy: "localhost,127.0.0.1,192.168.1.100,192.168.1.101,.internal.example.com"
```

---

## 4. Verification Example

```python
import os
from agent_common.config_loader import config

# 1. NO_PROXY is automatically synchronized upon importing config
active_no_proxy = os.environ.get("NO_PROXY")
print(f"Active NO_PROXY: {active_no_proxy}")
# Output: localhost,127.0.0.1,192.168.1.100,192.168.1.101,.internal.example.com

# 2. Network calls to internal destinations connect directly without proxy overhead
```

---

## 5. Operational Best Practices

- **Avoid Broad CIDR Notations**: Because some standard Python networking components do not natively parse CIDR notations (e.g. `192.168.0.0/16`), prefer using specific IP addresses or domain suffixes (e.g. `.example.com`, `192.168.1.100`).
- **Always Include Loopback Addresses**: Ensure `localhost,127.0.0.1` are included to avoid breaking local inter-process communication.
