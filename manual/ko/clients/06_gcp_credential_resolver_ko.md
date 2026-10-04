# 3.6. GCP 서비스 계정 인증 해석기 (`GcpCredentialResolver`)

> **소속 모듈**: `agent_common.clients.GcpCredentialResolver` (`from agent_common import GcpCredentialResolver`)  
> **핵심 메서드**: `resolve()`  
> **의존 패키지**: `google-auth`

---

## 1. 개요

`GcpCredentialResolver`는 GCP 서비스 계정 인증 객체(`google.auth.credentials.Credentials`)를 해석하는 일만 전담하는 독립 클래스입니다.

`GcsClient`와 `BigQueryClient`는 이 클래스를 상속하지 않고 **합성(Composition)** 으로 보유합니다(`self.credential_resolver`). 따라서 두 클라이언트 중 하나만 분리해서 쓰더라도 다른 클라이언트에 의존하지 않으며, `agent_common`이 클라이언트를 제공하지 않는 다른 GCP 서비스(Pub/Sub, Secret Manager 등)에서도 동일한 인증 규칙을 그대로 재사용할 수 있습니다.

---

## 2. 4단계 인증 우선순위

`resolve()`는 아래 순서로 먼저 해당하는 방식을 사용합니다. 흐름도는 [3.2. GcsClient 매뉴얼](02_gcs_cloud_storage_client_ko.md)을 참고하세요.

| 순위 | 인증 원천 | 동작 |
| :---: | :--- | :--- |
| 1 | `GOOGLE_APPLICATION_CREDENTIALS_JSON` 환경변수 | 키 파일을 디스크에 두지 않고, 환경변수의 JSON 문자열로 인증 객체 생성 |
| 2 | `GOOGLE_APPLICATION_CREDENTIALS` 환경변수 | Google 공식 표준 환경변수가 가리키는 키 파일(`.json`) 로드 |
| 3 | `credentials_path_str` | 생성자에 전달한 키 파일 경로 로드 (보통 `config.yml` 설정값) |
| 4 | 없음 | `None` 반환 → 각 GCP 클라이언트가 ADC(Application Default Credentials) 사용 |

2순위와 3순위의 경로가 상대 경로이면 프로젝트 루트(`ConfigLoader.project_path`) 기준으로 보정됩니다.

---

## 3. 주요 메서드 규격

### 3.1. 생성자 (`__init__`)
```python
def __init__(self, credentials_path_str: str, config_loader_obj: ConfigLoader)
```
- `credentials_path_str`: 서비스 계정 키 파일 경로. 지정하지 않으려면 `""`를 전달합니다.
- `config_loader_obj`: 상대 경로를 프로젝트 루트 기준으로 보정할 때 사용하는 `ConfigLoader` 인스턴스.

### 3.2. 인증 해석 (`resolve`)
```python
def resolve(self) -> Any
```
- 반환값: `google.auth.credentials.Credentials` 인스턴스, 또는 해당하는 인증 원천이 없으면 `None`.
- `google.oauth2.service_account` 모듈은 처음 호출될 때 한 번만 지연 로딩되어 클래스에 캐시됩니다.

---

## 4. 사용 예시

### 4.1. 다른 GCP 서비스에서 단독 사용
```python
from google.cloud import pubsub_v1

from agent_common import ConfigLoader, GcpCredentialResolver

credential_resolver = GcpCredentialResolver(
    credentials_path_str="config/secrets/gcp_sa_key.json",
    config_loader_obj=ConfigLoader(),
)
credentials = credential_resolver.resolve()

# credentials가 None이면 Google 클라이언트가 ADC를 사용합니다.
publisher_client = pubsub_v1.PublisherClient(credentials=credentials)
```

### 4.2. 환경변수만으로 인증 (키 파일 없이)
```bash
export GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type": "service_account", "project_id": "my-project", ...}'
```

```python
from agent_common import ConfigLoader, GcpCredentialResolver

# 경로를 비워 두면 환경변수 → ADC 순서로 해석합니다.
credentials = GcpCredentialResolver(credentials_path_str="", config_loader_obj=ConfigLoader()).resolve()
```

### 4.3. 자체 GCP 클라이언트 클래스에 합성하기
`GcsClient`, `BigQueryClient`와 같은 방식입니다. 부모 클래스를 두지 않으므로 클래스 하나만 떼어 가도 동작합니다.
```python
from typing import Any

from google.cloud import secretmanager

from agent_common import ConfigLoader, GcpCredentialResolver


class SecretManagerClient:
    """Secret Manager 조회를 담당하는 클라이언트 클래스."""

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

## 5. 예외 처리 가이드

| 발생 예외 | 주요 발생 원인 | 조치 방안 |
| :--- | :--- | :--- |
| `ImportError: 'google-auth' 패키지가 필요합니다` | `google-auth` 미설치 상태 | `pip install agent_common[clients]` 또는 `pip install google-auth` 실행 |
| `ValueError: GOOGLE_APPLICATION_CREDENTIALS_JSON 인메모리 JSON 인증 객체 생성에 실패했습니다` | 환경변수의 JSON 문법 오류 또는 필수 키 누락 | 환경변수에 주입된 JSON 문자열과 이스케이프 상태 점검 |
| `FileNotFoundError: 인증키 파일을 찾을 수 없습니다` | 2순위 또는 3순위 경로에 파일이 없음 | 메시지에 표시된 경로와 원천(환경변수 / `config.yml`) 확인 |

`GcsClient`, `BigQueryClient`를 통해 호출될 때는 위 예외가 연결 단계에서 `ConnectionError`로 감싸져 전달되며, 원래 예외는 `__cause__`와 로그의 트레이스백에서 확인할 수 있습니다.
