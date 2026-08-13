# agent_common 패키지

중앙 에이전트 및 데이터 이관/생성 서비스를 위한 공통 로깅, 설정 로더, 인프라 클라이언트 및 에러 처리 라이브러리 패키지입니다.

---

## 📌 주요 제공 기능

1. **설정 로더 (`agent_common.config_loader`)**
   - 계층적 YAML 설정 파싱 및 병합 (Deep Merge)
   - 패키지 내 기본 설정(`agent_common/config/*.yml`)과 개별 프로젝트 설정 오버라이드 지원
   - `setting("key.path")` 형태의 점 표기법 설정 조회 기능 및 `NO_PROXY` 자동 반영

2. **단일 행 로깅 포매터 및 로거 (`agent_common.logger`)**
   - `SingleLineFlattenFormatter`: 모든 로그 및 Traceback 예외 메시지를 1줄로 평탄화하여 중앙 로그 수집(Logstash, Fluentd 등)에 최적화
   - `ProjectLogger`: 콘솔 및 파일 로그 핸들러 동적 생성 및 일자별 로그 분리 관리

3. **스토리지 및 데이터베이스 클라이언트 (`agent_common.clients`)**
   - `EcsClient`: Dell ECS S3 저장소 접속, 목록 조회 및 파일 스트리밍 획득
   - `GcsClient`: Google Cloud Storage 연결 및 파일 스트리밍 업로드
   - `BigQueryClient`: Google Cloud BigQuery 연결 및 JSON 데이터 스트리밍 입력(`insert_rows_json`)

4. **공용 에러 및 예외 핸들러 (`agent_common.error_handler`)**
   - 네트워크 장애, 설정 오류, 런타임 예외에 대한 일관된 로깅 및 핸들링 제공

---

## 🚀 설치 및 사용 방법

### 📦 Wheel 패키지 빌드 (.whl 생성)

새로운 버전으로 패키징하여 `.whl` 파일을 빌드할 경우 `agent_common` 디렉터리 내에서 아래 명령을 실행합니다.

#### 1. 사내 폐쇄망 환경 (인터넷 차단, 완전히 오프라인 빌드)
폐쇄망에서는 외부 PyPI 접속을 완전히 차단하기 위해 `--no-index` 옵션과 빌드 도구 격리 방지(`--no-build-isolation`), 의존성 설치 제외(`--no-deps`) 옵션을 함께 지정합니다.

```bash
# 루트 디렉터리에서 실행 시 (권장)
pip wheel ./agent_common --no-index --no-build-isolation --no-deps -w whls/

# agent_common 디렉터리 내부에서 실행 시
pip wheel . --no-index --no-build-isolation --no-deps -w ../whls/
```

#### 2. 인터넷 연동망 환경 (온라인 빌드)

* **방법 A: `pip wheel` 이용**
  ```bash
  pip wheel . --no-deps -w dist/
  ```

* **방법 B: `build` 모듈 이용**
  ```bash
  # build 도구 설치 (최초 1회)
  pip install build

  # Wheel (.whl) 빌드
  python -m build --wheel
  ```

* **방법 C: `uv` 이용**
  ```bash
  uv build --wheel
  ```

*빌드가 완료되면 `dist/` 디렉터리에 `agent_common-0.2.3-py3-none-any.whl` 파일이 생성됩니다. 생성된 `.whl` 파일은 폐쇄망 배포용 `whls/` 폴더로 복사하여 사용할 수 있습니다.*

### Editable 모드 설치 (개발 환경)
```bash
pip install -e agent_common
```

### Wheel 패키지 설치 (폐쇄망 환경)
```bash
pip install whls/agent_common-0.2.3-py3-none-any.whl
```

---

## 📋 버전 변경 이력 (Changelog)

자세한 버전 변경 이력은 [CHANGELOG.md](CHANGELOG.md) 파일을 참고하세요.

