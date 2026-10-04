# 3.6. GCP Service Account Credential Resolver (`GcpCredentialResolver`)

> **Module**: `agent_common.clients.GcpCredentialResolver` (`from agent_common import GcpCredentialResolver`)  
> **Key Methods**: `resolve()`  
> **Dependencies**: `google-auth`

---

## 1. Overview

`GcpCredentialResolver` is a standalone class whose only job is to resolve a GCP service account credential object (`google.auth.credentials.Credentials`).

`GcsClient` and `BigQueryClient` do not inherit from it; they hold it by **composition** (`self.credential_resolver`). Either client can therefore be extracted on its own without depending on the other, and the same credential rules can be reused for GCP services that `agent_common` does not ship a client for (Pub/Sub, Secret Manager, and so on).

---

## 2. Four-Tier Credential Precedence

`resolve()` uses the first source that applies, in the order below. See the [3.2. GcsClient manual](02_gcs_cloud_storage_client_en.md) for the flow diagram.

| Tier | Credential source | Behavior |
| :---: | :--- | :--- |
| 1 | `GOOGLE_APPLICATION_CREDENTIALS_JSON` environment variable | Builds the credential from the JSON string in the variable, with no key file on disk |
| 2 | `GOOGLE_APPLICATION_CREDENTIALS` environment variable | Loads the key file (`.json`) that Google's standard variable points to |
| 3 | `credentials_path_str` | Loads the key file path passed to the constructor (usually a `config.yml` value) |
| 4 | None | Returns `None`, so each GCP client falls back to ADC (Application Default Credentials) |

Relative paths in tiers 2 and 3 are resolved against the project root (`ConfigLoader.project_path`).

---

## 3. Method Reference

### 3.1. Constructor (`__init__`)
```python
def __init__(self, credentials_path_str: str, config_loader_obj: ConfigLoader)
```
- `credentials_path_str`: Path to the service account key file. Pass `""` to leave it unset.
- `config_loader_obj`: The `ConfigLoader` instance used to resolve relative paths against the project root.

### 3.2. Resolve Credentials (`resolve`)
```python
def resolve(self) -> Any
```
- Returns a `google.auth.credentials.Credentials` instance, or `None` when no credential source applies.
- The `google.oauth2.service_account` module is lazy-loaded once on first call and cached on the class.

---

## 4. Usage Examples

### 4.1. Standalone Use with Another GCP Service
```python
from google.cloud import pubsub_v1

from agent_common import ConfigLoader, GcpCredentialResolver

credential_resolver = GcpCredentialResolver(
    credentials_path_str="config/secrets/gcp_sa_key.json",
    config_loader_obj=ConfigLoader(),
)
credentials = credential_resolver.resolve()

# When credentials is None, the Google client uses ADC.
publisher_client = pubsub_v1.PublisherClient(credentials=credentials)
```

### 4.2. Environment Variables Only (No Key File)
```bash
export GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type": "service_account", "project_id": "my-project", ...}'
```

```python
from agent_common import ConfigLoader, GcpCredentialResolver

# With an empty path, resolution goes environment variables -> ADC.
credentials = GcpCredentialResolver(credentials_path_str="", config_loader_obj=ConfigLoader()).resolve()
```

### 4.3. Composing It into Your Own GCP Client Class
This is the same approach `GcsClient` and `BigQueryClient` use. There is no parent class, so the class works when extracted on its own.
```python
from typing import Any

from google.cloud import secretmanager

from agent_common import ConfigLoader, GcpCredentialResolver


class SecretManagerClient:
    """Client class responsible for Secret Manager lookups."""

    def __init__(self, credentials_path_str: str = ""):
        self.config_loader: ConfigLoader = ConfigLoader()
        self.credential_resolver: GcpCredentialResolver = GcpCredentialResolver(
            credentials_path_str=credentials_path_str,
            config_loader_obj=self.config_loader,
        )
        self.client: Any = secretmanager.SecretManagerServiceClient(
            credentials=self.credential_resolver.resolve()
        )
```

---

## 5. Error Handling Guide

Exception messages are emitted in Korean; the leading text is shown below as it appears.

| Exception | Common cause | Resolution |
| :--- | :--- | :--- |
| `ImportError: ... 'google-auth' 패키지가 필요합니다` | `google-auth` is not installed | Run `pip install agent_common[clients]` or `pip install google-auth` |
| `ValueError: GOOGLE_APPLICATION_CREDENTIALS_JSON 인메모리 JSON 인증 객체 생성에 실패했습니다` | Malformed JSON or missing required keys in the environment variable | Check the JSON string and its escaping in the environment variable |
| `FileNotFoundError: 인증키 파일을 찾을 수 없습니다` | No file at the tier 2 or tier 3 path | Check the path and source (environment variable / `config.yml`) shown in the message |

When called through `GcsClient` or `BigQueryClient`, these exceptions are wrapped in `ConnectionError` during the connection step. The original exception is available on `__cause__` and in the logged traceback.
