# 1.5. 네트워크 프록시 제어 (`_apply_no_proxy`)

> **소속 모듈**: `agent_common.config_loader.ConfigLoader`  
> **핵심 메서드**: `ConfigLoader._apply_no_proxy(settings)`

---

## 1. 개요 및 엔터프라이즈 배경

기업 폐쇄망이나 엔터프라이즈 하이브리드 클라우드 환경에서는 외부 인터넷 통신(외부 LLM API 호출 등)을 위해 전사 아웃바운드 프록시(`HTTP_PROXY`, `HTTPS_PROXY`)를 필수로 사용합니다.

그러나 사내 사설망에 위치한 **Dell ECS 오브젝트 스토리지**, **사내 온프레미스 데이터베이스**, 또는 **K8s/클라우드 내부 메타데이터 서버**로의 통신까지 외부 프록시를 경유하게 되면 다음과 같은 심각한 장애가 발생합니다:
1. 사내 내부 IP/도메인을 외부 프록시 서버가 해석하지 못해 `502 Bad Gateway` 또는 `Connection Refused` 발생
2. 대용량 오브젝트 데이터(GB~TB 단위)가 프록시 장비를 통과하면서 심각한 네트워크 병목 및 대역폭 고갈 유발

`ConfigLoader`는 이러한 문제를 자동화하기 위해 설정 파일(`config.yml`)에 선언된 `proxy.no_proxy` 목록을 감지하여 OS 환경변수 `NO_PROXY`에 **안전하게 자동 주입 및 동기화**합니다.

---

## 2. 동작 메커니즘 (`_apply_no_proxy`)

`ConfigLoader.get_settings()`가 실행될 때마다 내부적으로 `_apply_no_proxy`가 자동으로 호출됩니다:

```python
def _apply_no_proxy(self, settings: dict[str, Any]) -> None:
    """proxy.no_proxy 설정 값을 NO_PROXY 환경 변수로 적용한다."""
    no_proxy_value = settings.get("proxy", {}).get("no_proxy")
    if no_proxy_value:
        existing = os.environ.get("NO_PROXY", "")
        if existing:
            os.environ["NO_PROXY"] = f"{existing},{no_proxy_value}"
        else:
            os.environ["NO_PROXY"] = str(no_proxy_value)
```

### 핵심 특징:
1. **무손실 누적 병합 (Non-destructive Merge)**:
   - 이미 시스템 또는 상위 컨테이너(Docker, Airflow Pod)에 `NO_PROXY` 환경변수가 정의되어 있다면 이를 지우지 않고 쉼표(`,`)로 연결하여 안전하게 덧붙입니다.
2. **자동 라이프사이클 반영**:
   - 별도의 초기화 코드를 호출할 필요 없이 `from agent_common.config_loader import config`만으로 즉시 프로세스 전역에 적용됩니다.
3. **표준 라이브러리 연동**:
   - Python의 `urllib.request`, `requests`, `boto3`, `google-cloud-storage` 등 모든 주요 HTTP/네트워크 클라이언트 라이브러리가 OS `NO_PROXY` 환경변수를 표준으로 감지하므로 일관된 프록시 우회가 보장됩니다.

---

## 3. 설정 파일 작성 방법 (`config/config.yml`)

`config/config.yml`에 다음과 같이 `proxy` 섹션을 구성합니다:

```yaml
proxy:
  # 외부 통신용 프록시 (필요시 명시)
  http_proxy: "http://proxy.example.com:8080"
  https_proxy: "http://proxy.example.com:8080"
  
  # 프록시를 타지 않고 직접 연결할 내부 호스트/IP 목록 (쉼표로 구분)
  no_proxy: "localhost,127.0.0.1,192.168.1.100,192.168.1.101,.internal.example.com"
```

---

## 4. 실전 동작 및 검증 예시

```python
import os
from agent_common.config_loader import config

# 1. config 로드 시점에 _apply_no_proxy 가 자동 실행됨
current_no_proxy = os.environ.get("NO_PROXY")
print(f"현재 적용된 NO_PROXY: {current_no_proxy}")
# 출력: localhost,127.0.0.1,192.168.1.100,192.168.1.101,.internal.example.com

# 2. 내부 스토리지/API 직접 통신
# 호출 시 OS NO_PROXY에 등록된 내부 IP/호스트는 프록시를 거치지 않고 직접 고속 통신함
```

---

## 5. 운영 베스트 프랙티스

- **CIDR 대역 표기 주의**: 일부 파이썬 라이브러리(`urllib`)는 `192.168.0.0/16` 형태의 CIDR 표기를 완벽히 지원하지 못할 수 있으므로, 명시적인 IP 접두사(예: `.example.com`, `192.168.1.100`) 형태로 기재하는 것이 가장 안전합니다.
- **로컬 호스트 필수 포함**: `localhost,127.0.0.1`은 시스템 루프백 통신 장애를 방지하기 위해 항상 `no_proxy` 목록 맨 앞에 포함하십시오.
