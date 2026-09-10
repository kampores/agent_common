# 작성일: 2026-07-20
# 설계자: 김유상 수석
# 설계자 이메일: bakkus@daum.net

"""
AWS S3, Dell ECS(S3 호환), Google Cloud Storage(GCS), Google Cloud BigQuery(BQ) 등 
스토리지 및 데이터베이스 시스템과의 연결 및 데이터 입출력을 담당하는 공용 클라이언트 모듈입니다.
"""

from __future__ import annotations

import os
import re
import time
import json
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    import boto3
    from botocore.client import Config as BotoConfig
    from google.cloud import storage, bigquery
    from google.oauth2 import service_account

from agent_common.config_loader import ConfigLoader, config
from agent_common.logger import ProjectLogger

# ==============================================================================
# 스토리지 및 데이터베이스 클라이언트 모듈 기본 설정 스키마 (No Hardcoding & Self-Healing 보장)
# ==============================================================================
APP_DEFAULT_SCHEMA_DICT: dict[str, Any] = {
    "transfer": {
        "timeout_seconds_int": 120,
        "chunk_size_int": 8388608,
    },
    "bigquery": {
        "ignore_unknown_values_bool": True,
        "timezone_offset_str": "+09:00",
        "max_retries_int": 3,
    },
}


# 서드파티 SDK 지연 로딩(Lazy Loading) 캐시 변수
_boto3_module: Any = None
_boto_config_cls: Any = None
_storage_module: Any = None
_bigquery_module: Any = None
_service_account_module: Any = None



def _get_boto3() -> Tuple[Any, Any]:
    """
    boto3 및 BotoConfig 모듈을 지연 임포트(Lazy Load)하여 반환합니다.

    :return: (boto3 모듈, BotoConfig 클래스) 튜플
    :raises ImportError: boto3 패키지가 설치되어 있지 않은 경우 발생
    """
    global _boto3_module, _boto_config_cls
    if _boto3_module is None or _boto_config_cls is None:
        try:
            import boto3
            from botocore.client import Config as BotoConfig
            _boto3_module = boto3
            _boto_config_cls = BotoConfig
        except ImportError as exc:
            raise ImportError(
                "AWS S3 및 Dell ECS 기능을 사용하려면 'boto3' 패키지가 필요합니다. "
                "'pip install boto3' 또는 'pip install agent_common[clients]'로 설치해 주십시오."
            ) from exc
    return _boto3_module, _boto_config_cls


def _get_gcs() -> Tuple[Any, Any]:
    """
    google.cloud.storage 및 google.oauth2.service_account 모듈을 지연 임포트(Lazy Load)하여 반환합니다.

    :return: (storage 모듈, service_account 모듈) 튜플
    :raises ImportError: google-cloud-storage 또는 google-auth 패키지가 설치되어 있지 않은 경우 발생
    """
    global _storage_module, _service_account_module
    if _storage_module is None or _service_account_module is None:
        try:
            from google.cloud import storage
            from google.oauth2 import service_account
            _storage_module = storage
            _service_account_module = service_account
        except ImportError as exc:
            raise ImportError(
                "Google Cloud Storage(GCS) 기능을 사용하려면 'google-cloud-storage' 패키지가 필요합니다. "
                "'pip install google-cloud-storage' 또는 'pip install agent_common[clients]'로 설치해 주십시오."
            ) from exc
    return _storage_module, _service_account_module


def _get_bigquery() -> Tuple[Any, Any]:
    """
    google.cloud.bigquery 및 google.oauth2.service_account 모듈을 지연 임포트(Lazy Load)하여 반환합니다.

    :return: (bigquery 모듈, service_account 모듈) 튜플
    :raises ImportError: google-cloud-bigquery 또는 google-auth 패키지가 설치되어 있지 않은 경우 발생
    """
    global _bigquery_module, _service_account_module
    if _bigquery_module is None or _service_account_module is None:
        try:
            from google.cloud import bigquery
            from google.oauth2 import service_account
            _bigquery_module = bigquery
            _service_account_module = service_account
        except ImportError as exc:
            raise ImportError(
                "Google Cloud BigQuery 기능을 사용하려면 'google-cloud-bigquery' 패키지가 필요합니다. "
                "'pip install google-cloud-bigquery' 또는 'pip install agent_common[clients]'로 설치해 주십시오."
            ) from exc
    return _bigquery_module, _service_account_module



class S3Client:
    """
    AWS S3 및 Dell ECS(S3 호환) 저장소와의 연결, 데이터 조회 및 전송을 담당하는 공용 클라이언트 클래스.
    """

    def __init__(
        self,
        endpoint_url_str: str | None = None,
        access_key_str: str | None = None,
        secret_key_str: str | None = None,
        bucket_name_str: str = "",
        timeout_seconds_int: int | None = None,
        region_name_str: str | None = None,
    ):
        """
        AWS S3 또는 Dell ECS 클라이언트를 초기화합니다.

        :param endpoint_url_str: S3 엔드포인트 URL (Dell ECS 등 온프레미스 사용 시 지정, AWS S3 기본 사용 시 None 또는 생략)
        :param access_key_str: S3 접속 Access Key ID (AWS IAM Role 사용 시 None 가능)
        :param secret_key_str: S3 접속 Secret Access Key (AWS IAM Role 사용 시 None 가능)
        :param bucket_name_str: 조회의 대상이 되는 S3/ECS 버킷명 (필수)
        :param timeout_seconds_int: 네트워크 연결 및 읽기 타임아웃 초 (미지정 시 설정 파일 transfer.timeout_seconds 참조)
        :param region_name_str: AWS 리전명 (예: 'ap-northeast-2', Dell ECS의 경우 생략 가능)
        :raises ValueError: 필수 파라미터인 bucket_name이 누락된 경우 발생
        :raises ConnectionError: 저장소 연결 또는 버킷 접근 권한 검증에 실패한 경우 발생
        """
        self.endpoint_url_str: str | None = endpoint_url_str
        self.access_key_str: str | None = access_key_str
        self.secret_key_str: str | None = secret_key_str
        if not bucket_name_str:
            raise ValueError("S3/ECS 버킷명(bucket_name_str)은 필수 입력 항목입니다.")
        self.bucket_name_str: str = bucket_name_str.strip()
        self.region_name_str: str | None = region_name_str

        # logger 초기화
        self.logger: ProjectLogger = ProjectLogger(f"agent_common.{self.__class__.__name__}")
        # config_loader: self 인스턴스 소유 ConfigLoader 객체 생성
        self.config_loader: ConfigLoader = ConfigLoader()

        resolved_timeout_int = (
            timeout_seconds_int
            if timeout_seconds_int is not None
            else self.config_loader.require_setting("transfer.timeout_seconds_int")
        )
        self.timeout_seconds_int: int = int(resolved_timeout_int)

        # client: boto3 s3 클라이언트 인스턴스
        self.client: Any = None
        self._connect()

    def _connect(self) -> None:
        """
        boto3 S3 클라이언트를 사용하여 AWS S3 / Dell ECS 접속을 초기화하고 연결 및 버킷 접근을 검증합니다 (Fail-Fast).

        :raises ConnectionError: 엔드포인트 연결 실패 또는 버킷 접근 권한 검증 실패 시 발생
        """
        boto3_module, boto_config_cls = _get_boto3()
        try:
            client_kwargs_dict: Dict[str, Any] = {
                "service_name": "s3",
                "config": boto_config_cls(
                    signature_version="s3v4",
                    connect_timeout=self.timeout_seconds_int,
                    read_timeout=self.timeout_seconds_int,
                    retries={"max_attempts": 2},
                ),
            }
            if self.endpoint_url_str:
                client_kwargs_dict["endpoint_url"] = self.endpoint_url_str
            if self.region_name_str:
                client_kwargs_dict["region_name"] = self.region_name_str
            if self.access_key_str and self.secret_key_str:
                client_kwargs_dict["aws_access_key_id"] = self.access_key_str
                client_kwargs_dict["aws_secret_access_key"] = self.secret_key_str

            self.client = boto3_module.client(**client_kwargs_dict)

            # S3/ECS 버킷 접근 권한 및 엔드포인트 연결 상태 검증 (Fail-Fast)
            self.client.head_bucket(Bucket=self.bucket_name_str)
        except Exception as exc:
            target_service_str: str = "Dell ECS" if self.endpoint_url_str else "AWS S3"
            raise ConnectionError(
                self.logger.exception("connection_failed", service_name=target_service_str, error=str(exc))
            ) from exc

    def list_objects(self, prefix_str: str = "") -> Generator[Dict[str, Any], None, None]:
        """
        지정된 버킷 및 프리픽스 범위 하위의 S3/ECS 오브젝트 목록을 안전하게 조회(페이징)합니다.

        :param prefix_str: 조회할 오브젝트 키 프리픽스
        :return: 오브젝트 메타데이터 딕셔너리 제너레이터
        :raises RuntimeError: 목록 조회 실패 시 발생
        """
        try:
            paginator_obj: Any = self.client.get_paginator("list_objects_v2")
            pages_iterable: Any = paginator_obj.paginate(Bucket=self.bucket_name_str, Prefix=prefix_str)
            for page_dict in pages_iterable:
                if "Contents" in page_dict:
                    for object_item_dict in page_dict["Contents"]:
                        yield object_item_dict
        except Exception as exc:
            storage_type_str: str = "Dell ECS" if self.endpoint_url_str else "AWS S3"
            raise RuntimeError(self.logger.exception("list_failed", storage_type=storage_type_str, error=str(exc))) from exc

    def get_object_stream(self, key_str: str = "") -> Any:
        """
        특정 파일의 파일 스트림 객체(StreamingBody)를 S3/ECS로부터 획득합니다.

        :param key_str: 대상 오브젝트 키 경로
        :return: StreamingBody 스트림 객체
        :raises RuntimeError: 스트림 조회 실패 시 발생
        """
        try:
            response_dict: dict[str, Any] = self.client.get_object(Bucket=self.bucket_name_str, Key=key_str)
            return response_dict["Body"]
        except Exception as exc:
            raise RuntimeError(self.logger.exception("transfer_failed", file_name=key_str, error=str(exc))) from exc

    def get_object_size(self, key_str: str = "") -> int | None:
        """
        S3/ECS 오브젝트의 파일 크기(bytes)를 헤더(head_object)로 빠르게 조회합니다.

        :param key_str: 대상 오브젝트 키 경로
        :return: 파일 크기(바이트) 또는 조회 실패 시 None
        """
        try:
            response_dict: dict[str, Any] = self.client.head_object(Bucket=self.bucket_name_str, Key=key_str)
            return response_dict.get("ContentLength")
        except Exception:
            return None

    def transfer_to_gcs(
        self,
        gcs_client_obj: GcsClient,
        s3_key_str: str = "",
        gcs_blob_name_str: str = "",
        size_int: int = 0,
    ) -> bool:
        """
        단일 파일에 대해 GCS 존재 여부 및 용량을 사전 검사하여, 동일 용량 파일 존재 시 복사를 건너뛰고(Skip),
        신규 파일이거나 용량이 다른 경우 S3/ECS 스트림을 열고 GCS로 실시간 전송하며,
        구간별 통계 시간 및 단일 행 표준 로깅을 공통 처리합니다.

        :param gcs_client_obj: 목적지 GCS 클라이언트 인스턴스
        :param s3_key_str: 소스 S3/ECS 객체 키 경로
        :param gcs_blob_name_str: 목적지 GCS 블롭 경로명
        :param size_int: 파일 바이트 크기
        :return: 전송 성공 또는 Skip 시 True, 실패 시 False
        """
        total_start_float: float = time.time()
        context_info_str: str = f"[S3_Key={s3_key_str} GCS_Blob={gcs_blob_name_str} Size={size_int}]"

        try:
            # 1. GCS 목적지의 기존 파일 존재 여부 및 바이트 크기 조회
            check_start_float: float = time.time()
            existing_size_int: int | None = gcs_client_obj.get_blob_size(gcs_blob_name_str)
            check_elapsed_float: float = time.time() - check_start_float

            # 이미 GCS에 존재하고 용량이 동일한 경우 복사 건너뛰기
            if existing_size_int is not None and existing_size_int == size_int:
                self.logger.info("transfer_skipped", file_name=s3_key_str, dst_type="GCS")
                self.logger.info(
                    "elapsed_time",
                    action_name="GCS 파일 검사",
                    details=f"[CheckTime={check_elapsed_float:.2f}s Status=Skipped]",
                    context_info=context_info_str,
                )
                return True

            # 2. S3/ECS StreamingBody 스트림 객체 생성 시간 측정
            stream_start_float: float = time.time()
            stream_obj: Any = self.get_object_stream(s3_key_str)
            stream_elapsed_float: float = time.time() - stream_start_float

            # 3. GCS 업로드 스트림 시간 측정
            upload_start_float: float = time.time()
            gcs_client_obj.upload_stream(stream_obj, gcs_blob_name_str, size_int)
            upload_elapsed_float: float = time.time() - upload_start_float

            total_elapsed_float: float = time.time() - total_start_float
            self.logger.info("transfer_completed", file_name=s3_key_str, size_bytes=size_int)
            self.logger.info(
                "elapsed_time",
                action_name="GCS 파일 전송",
                details=(
                    f"[TotalElapsed={total_elapsed_float:.2f}s CheckTime={check_elapsed_float:.2f}s "
                    f"S3StreamTime={stream_elapsed_float:.2f}s GCSUploadTime={upload_elapsed_float:.2f}s]"
                ),
                context_info=context_info_str,
            )
            return True
        except Exception as exc:
            total_elapsed_float = time.time() - total_start_float
            self.logger.exception("transfer_failed", file_name=s3_key_str, error=str(exc))
            self.logger.error(
                "elapsed_time",
                action_name="GCS 파일 전송 오류",
                details=f"[TotalElapsed={total_elapsed_float:.2f}s]",
                context_info=context_info_str,
            )
            return False


def _resolve_gcp_credentials(
    credentials_path_str: str,
    config_loader_obj: ConfigLoader,
    service_account_module: Any,
) -> Any:
    """
    GCP 서비스 계정 인증 자격 증명을 3단계 우선순위에 따라 해결하여 반환합니다.
    1순위: GCP_KEYFILE_JSON 또는 GOOGLE_KEYFILE_JSON 환경변수 (인메모리 JSON)
    2순위: credentials_path_str 파일 경로 (.json 키 파일)
    3순위: None (Google ADC 기본 인증 활용)

    :param credentials_path_str: 로컬 키 파일 경로 문자열 (미지정 시 "")
    :param config_loader_obj: 프로젝트 루트 경로 계산용 ConfigLoader 인스턴스
    :param service_account_module: google.oauth2.service_account 모듈
    :return: google.auth.credentials.Credentials 인스턴스 또는 None
    :raises FileNotFoundError: 2순위 파일 경로가 지정되었으나 존재하지 않는 경우 발생
    :raises ValueError: 1순위 환경변수 JSON 파싱 실패 시 발생
    """
    # 1순위: 환경변수(GCP_KEYFILE_JSON, GOOGLE_KEYFILE_JSON) 인메모리 JSON 검사
    env_keyfile_json_str: Optional[str] = (
        os.environ.get("GCP_KEYFILE_JSON") or os.environ.get("GOOGLE_KEYFILE_JSON")
    )
    if env_keyfile_json_str and env_keyfile_json_str.strip():
        try:
            key_info_dict: dict[str, Any] = json.loads(env_keyfile_json_str.strip())
        except Exception as json_err:
            raise ValueError(f"GCP_KEYFILE_JSON 환경변수의 JSON 파싱에 실패했습니다: {json_err}") from json_err

        try:
            return service_account_module.Credentials.from_service_account_info(key_info_dict)
        except Exception as cred_err:
            raise ValueError(f"GCP 서비스 계정 키 인증 객체 생성에 실패했습니다: {cred_err}") from cred_err

    # 2순위: credentials_path_str 지정 파일 경로 검사
    if credentials_path_str and credentials_path_str.strip():
        cred_path: Path = Path(credentials_path_str)
        if not cred_path.is_absolute():
            cred_path = config_loader_obj.project_path(cred_path)
        if not cred_path.exists():
            raise FileNotFoundError(
                f"인증키 파일을 찾을 수 없습니다: {cred_path} (config.yml 설정값: '{credentials_path_str}')"
            )
        return service_account_module.Credentials.from_service_account_file(str(cred_path))

    # 3순위: None 반환 -> storage.Client() / bigquery.Client()가 ADC(기본 인증) 사용
    return None


class GcsClient:
    """
    Google Cloud Storage(GCS) 버킷 연결 및 파일 스트림 업로드를 담당하는 공용 클라이언트 클래스.
    """

    def __init__(
        self,
        bucket_name_str: str = "",
        credentials_path_str: str = "",
        timeout_seconds_int: int | None = None,
    ):
        """
        Google Cloud Storage(GCS) 클라이언트를 초기화합니다.

        :param bucket_name_str: 대상 GCS 버킷명
        :param credentials_path_str: GCP 서비스 계정 인증 키 JSON 경로 (미지정 시 ADC 사용)
        :param timeout_seconds_int: 네트워크 연결 및 스트림 업로드 타임아웃 제한 시간(초)
        """
        if not bucket_name_str:
            raise ValueError("GCS 버킷명(bucket_name_str)은 필수 입력 항목입니다.")
        self.bucket_name_str: str = bucket_name_str.strip()
        self.credentials_path_str: str = credentials_path_str.strip() if credentials_path_str else ""

        # logger: 로거 초기화
        self.logger: ProjectLogger = ProjectLogger(f"agent_common.{self.__class__.__name__}")
        # config_loader: self 인스턴스 소유 ConfigLoader 객체 생성
        self.config_loader: ConfigLoader = ConfigLoader()

        resolved_timeout_int = (
            timeout_seconds_int
            if timeout_seconds_int is not None
            else self.config_loader.require_setting("transfer.timeout_seconds_int")
        )
        self.timeout_seconds_int: int = int(resolved_timeout_int)

        # client: google-cloud-storage 클라이언트 인스턴스
        self.client: Any = None
        # bucket: 연결 완료된 GCS Bucket 객체
        self.bucket: Any = None
        self._connect()

    def _connect(self) -> None:
        """
        Google Cloud Storage 클라이언트를 초기화하고 해당 버킷의 연결/접근 권한 상태를 검증합니다 (Fail-Fast).
        """
        storage_module, service_account_module = _get_gcs()
        try:
            credentials = _resolve_gcp_credentials(
                credentials_path_str=self.credentials_path_str,
                config_loader_obj=self.config_loader,
                service_account_module=service_account_module,
            )
            if credentials is not None:
                self.client = storage_module.Client(credentials=credentials)
            else:
                self.client = storage_module.Client()

            # 버킷에 대한 접근 권한 및 존재 여부 검사 (타임아웃 적용)
            self.bucket = self.client.get_bucket(self.bucket_name_str, timeout=self.timeout_seconds_int)
        except Exception as e:
            raise ConnectionError(self.logger.exception("connection_failed", service_name="GCS", error=str(e))) from e

    def get_blob_size(self, destination_blob_name_str: str = "") -> int | None:
        """GCS 목적지 blob의 존재 여부 및 바이트 크기(bytes)를 조회한다.

        :param destination_blob_name_str: 조회할 GCS 오브젝트 blob 경로명
        :return: blob이 존재하면 바이트 크기를 반환하며, 미존재 시 None을 반환한다.
        """
        try:
            blob_obj: Any = self.bucket.get_blob(destination_blob_name_str, timeout=self.timeout_seconds_int)
            if blob_obj is not None:
                return blob_obj.size
            return None
        except Exception as e:
            self.logger.exception("storage_meta_error", storage_type="GCS", target_name=destination_blob_name_str, error=str(e))
            return None

    def upload_stream(
        self,
        stream_any: Any = None,
        destination_blob_name_str: str = "",
        size_int: int = 0,
        timeout_int: int | None = None,
    ) -> None:
        """
        입력되는 스트림 데이터를 GCS 목적지 blob에 직접 스트리밍 업로드합니다.

        :param stream_any: 업로드할 원천 스트림 데이터 객체
        :param destination_blob_name_str: GCS 목적지 저장 blob 경로
        :param size_int: 업로드할 스트림의 정확한 바이트 크기
        :param timeout_int: 업로드 제한 시간 (초 단위, 미지정 시 self.timeout_seconds_int 사용)
        """
        upload_timeout_int: int = (
            timeout_int
            if timeout_int is not None
            else self.timeout_seconds_int
        )
        try:
            blob_obj: Any = self.bucket.blob(destination_blob_name_str)
            # size 인수를 반드시 제공하며 지정된 timeout 내 업로드를 완료하도록 처리
            blob_obj.upload_from_file(stream_any, size=size_int, timeout=upload_timeout_int)
        except Exception as e:
            raise RuntimeError(self.logger.exception("transfer_failed", file_name=destination_blob_name_str, error=str(e))) from e



class BigQueryClient:
    """
    Google Cloud BigQuery(BQ) 테이블 연결 및 JSON 데이터 스트리밍 적재를 담당하는 공용 클라이언트 클래스.
    """

    def __init__(
        self,
        project_id_str: str = "",
        dataset_id_str: str = "",
        table_id_str: str = "",
        credentials_path_str: str = "",
        timeout_seconds_int: int | None = None,
        ignore_unknown_values_bool: bool | None = None,
    ):
        """
        Google Cloud BigQuery(BQ) 클라이언트를 초기화합니다.

        :param project_id_str: GCP 프로젝트 ID
        :param dataset_id_str: BigQuery 데이터셋 ID
        :param table_id_str: BigQuery 테이블 ID
        :param credentials_path_str: GCP 서비스 계정 키 JSON 경로 (비어있으면 기본 ADC 사용)
        :param timeout_seconds_int: 작업 제한 시간(초)
        :param ignore_unknown_values_bool: 미정의 필드 무시 여부 (None 시 config 참조)
        """
        self.project_id_str: str = project_id_str
        self.dataset_id_str: str = dataset_id_str
        self.table_id_str: str = table_id_str
        self.credentials_path_str: str = credentials_path_str

        # logger: _logger 백킹 필드 초기화
        self._logger: ProjectLogger | None = ProjectLogger(f"agent_common.{self.__class__.__name__}")
        # config_loader: self 인스턴스 소유 ConfigLoader 객체 생성
        self.config_loader: ConfigLoader = ConfigLoader()

        resolved_timeout_int = (
            timeout_seconds_int
            if timeout_seconds_int is not None
            else self.config_loader.require_setting("transfer.timeout_seconds_int")
        )
        self.timeout_seconds_int: int = int(resolved_timeout_int)

        self.ignore_unknown_values_bool: bool = (
            ignore_unknown_values_bool
            if ignore_unknown_values_bool is not None
            else config.bigquery.ignore_unknown_values_bool
        )

        # timezone_offset_str: BigQuery TIMESTAMP 컬럼 적재 시 기본 적용할 타임존 오프셋 (_str 접미사로 자동 str 보증)
        self.timezone_offset_str: str = config.bigquery.timezone_offset_str

        # client: google-cloud-bigquery 클라이언트 인스턴스
        self.client: Any = None
        self._connect()

    @property
    def logger(self) -> ProjectLogger:
        """ProjectLogger 인스턴스 지연 초기화 프로퍼티 (AttributeError 100% 방지)"""
        if getattr(self, "_logger", None) is None:
            self._logger = ProjectLogger(f"agent_common.{self.__class__.__name__}")
        return self._logger

    @logger.setter
    def logger(self, val_logger_obj: ProjectLogger) -> None:
        self._logger = val_logger_obj

    def _connect(self) -> None:
        """
        Google Cloud BigQuery 클라이언트를 초기화하고 연결 및 테이블 스키마 상태를 검증합니다 (Fail-Fast).
        """
        bigquery_module, service_account_module = _get_bigquery()
        try:
            effective_project_id_str: str = (
                os.environ.get("GCP_PROJECT_ID")
                or os.environ.get("GOOGLE_CLOUD_PROJECT")
                or self.project_id_str
            )
            credentials = _resolve_gcp_credentials(
                credentials_path_str=self.credentials_path_str,
                config_loader_obj=self.config_loader,
                service_account_module=service_account_module,
            )
            if credentials is not None:
                self.client = bigquery_module.Client(credentials=credentials, project=effective_project_id_str)
            else:
                self.client = bigquery_module.Client(project=effective_project_id_str)
            
            # BigQuery Table 객체를 조회하여 스키마 타입(JSON, TIMESTAMP 등) 사전 캐싱 및 연결 상태 검증 (Fail-Fast)
            table_ref_str = f"{effective_project_id_str}.{self.dataset_id_str}.{self.table_id_str}"
            self.table_obj = self.client.get_table(table_ref_str)
        except Exception as e:
            raise ConnectionError(self.logger.exception("connection_failed", service_name="BigQuery", error=str(e))) from e

    def load_table_from_json_data(
        self,
        json_data_any: Any,
        timeout_int: int | None = None,
        ignore_unknown_values_bool: bool | None = None,
        write_disposition_str: str | None = None,
    ) -> None:
        """
        self.client.load_table_from_json(배치 로드 Job)만을 사용하여 JSON 객체(dict 또는 list)를 BigQuery 테이블에 적재합니다.

        :param json_data_any: 적재할 단일 dict 또는 dict 리스트
        :param timeout_int: 작업 제한 시간(초)
        :param ignore_unknown_values_bool: 미정의 필드 무시 여부
        :param write_disposition_str: BigQuery 쓰기 옵션 ('WRITE_TRUNCATE', 'WRITE_APPEND', 'WRITE_EMPTY' 등)
        """
        insert_timeout_int: int = (
            timeout_int
            if timeout_int is not None
            else self.timeout_seconds_int
        )
        skip_unknown_bool: bool = (
            ignore_unknown_values_bool
            if ignore_unknown_values_bool is not None
            else self.ignore_unknown_values_bool
        )
        table_ref_str: str = f"{self.project_id_str}.{self.dataset_id_str}.{self.table_id_str}"
        table_target_any: Any = self.table_obj if getattr(self, "table_obj", None) else table_ref_str
        rows_to_insert_list: list[dict[str, Any]] | None = (
            [json_data_any] if isinstance(json_data_any, dict) else (json_data_any if isinstance(json_data_any, list) else None)
        )
        if rows_to_insert_list is None:
            raise ValueError(f"지원하지 않는 JSON 데이터 포맷 구조입니다: {type(json_data_any)}")

        bigquery_module, _ = _get_bigquery()
        try:
            write_disposition_effective_str: str = (
                write_disposition_str
                if write_disposition_str
                else bigquery_module.WriteDisposition.WRITE_APPEND
            )
            job_config_obj: Any = bigquery_module.LoadJobConfig(
                source_format=bigquery_module.SourceFormat.NEWLINE_DELIMITED_JSON,
                write_disposition=write_disposition_effective_str,
                ignore_unknown_values=skip_unknown_bool,
            )
            if hasattr(self, "table_obj") and isinstance(self.table_obj, bigquery_module.Table):
                job_config_obj.schema = self.table_obj.schema

            load_job_obj: Any = self.client.load_table_from_json(
                rows_to_insert_list,
                table_target_any,
                job_config=job_config_obj,
                timeout=insert_timeout_int,
            )
            load_job_obj.result(timeout=insert_timeout_int)
        except Exception as load_exc:
            sub_error_list: list[str] = []
            if hasattr(load_exc, "errors") and getattr(load_exc, "errors"):
                for sub_error_item_dict in getattr(load_exc, "errors"):
                    location_str: str = (
                        sub_error_item_dict.get("location", "unknown_field")
                        if isinstance(sub_error_item_dict, dict)
                        else "unknown"
                    )
                    message_str: str = (
                        sub_error_item_dict.get("message", str(sub_error_item_dict))
                        if isinstance(sub_error_item_dict, dict)
                        else str(sub_error_item_dict)
                    )
                    sub_error_list.append(f"[Loc={location_str}] {message_str}")
            detailed_info_str: str = " | SubErrors: " + " ; ".join(sub_error_list) if sub_error_list else ""
            clean_error_str: str = str(load_exc) + detailed_info_str
            self.logger.exception(
                "load_table_from_json_failed",
                service_name="BigQuery",
                target_name=self.table_id_str,
                error=clean_error_str,
            )
            raise RuntimeError(
                self.logger.error(
                    "load_table_from_json_failed",
                    service_name="BigQuery",
                    target_name=self.table_id_str,
                    error=clean_error_str,
                )
            ) from load_exc

    def insert_rows_json_data(
        self,
        json_data_any: Any,
        timeout_int: int | None = None,
        ignore_unknown_values_bool: bool | None = None,
    ) -> None:
        """
        self.client.insert_rows_json(스트리밍 적재 API)만을 사용하여 JSON 객체(dict 또는 list)를 BigQuery 테이블에 적재합니다.

        :param json_data_any: 적재할 단일 dict 또는 dict 리스트
        :param timeout_int: 작업 제한 시간(초)
        :param ignore_unknown_values_bool: 미정의 필드 무시 여부
        """
        insert_timeout_int: int = (
            timeout_int
            if timeout_int is not None
            else self.timeout_seconds_int
        )
        skip_unknown_bool: bool = (
            ignore_unknown_values_bool
            if ignore_unknown_values_bool is not None
            else self.ignore_unknown_values_bool
        )
        table_ref_str: str = f"{self.project_id_str}.{self.dataset_id_str}.{self.table_id_str}"
        table_target_any: Any = self.table_obj if getattr(self, "table_obj", None) else table_ref_str

        rows_to_insert_list: list[dict[str, Any]] | None = (
            [json_data_any] if isinstance(json_data_any, dict) else (json_data_any if isinstance(json_data_any, list) else None)
        )
        if rows_to_insert_list is None:
            raise ValueError(f"지원하지 않는 JSON 데이터 포맷 구조입니다: {type(json_data_any)}")

        try:
            insert_errors_list: list[dict[str, Any]] = self.client.insert_rows_json(
                table_target_any,
                rows_to_insert_list,
                ignore_unknown_values=skip_unknown_bool,
                timeout=insert_timeout_int,
            )
            if insert_errors_list:
                error_details_list: list[str] = []
                for error_item_dict in insert_errors_list:
                    row_index_int: int = error_item_dict.get("index", 0)
                    for single_error_dict in error_item_dict.get("errors", []):
                        location_str: str = single_error_dict.get("location", "unknown_field")
                        message_str: str = single_error_dict.get("message", "")
                        reason_str: str = single_error_dict.get("reason", "")
                        error_details_list.append(f"[Row={row_index_int} Field={location_str} Reason={reason_str}] {message_str}")
                combined_error_message_str: str = " | ".join(error_details_list) if error_details_list else str(insert_errors_list)
                raise RuntimeError(f"BigQuery API insert 반환 상세 에러: {combined_error_message_str}")
        except Exception as insert_exc:
            clean_insert_error_str: str = str(insert_exc)
            raise RuntimeError(self.logger.exception("insert_failed", service_name="BigQuery", target_name=self.table_id_str, error=clean_insert_error_str)) from insert_exc

    def query(self, query_str: str, timeout_int: int | None = None) -> list[dict[str, Any]]:
        """
        임의의 BigQuery SQL 쿼리(예: 공통 코드 테이블 SELECT 등)를 실행하고,
        조회된 결과 행들을 딕셔너리 리스트([dict, ...])로 반환합니다.

        :param query_str: 실행할 SQL 쿼리 문자열
        :param timeout_int: 쿼리 타임아웃 제한 시간(초)
        :return: 딕셔너리 리스트 형태의 쿼리 결과
        """
        query_timeout_int: int = (
            timeout_int
            if timeout_int is not None
            else self.timeout_seconds_int
        )
        try:
            query_job_obj: Any = self.client.query(query_str, timeout=query_timeout_int)
            query_results_obj: Any = query_job_obj.result(timeout=query_timeout_int)
            rows_list: list[dict[str, Any]] = [dict(row.items()) for row in query_results_obj]
            return rows_list
        except Exception as query_exc:
            clean_error_str: str = str(query_exc)
            self.logger.warning("query_execution_failed", service_name="BigQuery", query=query_str, error=clean_error_str)
            raise RuntimeError(
                self.logger.error("query_execution_failed", service_name="BigQuery", error=clean_error_str)
            ) from query_exc

    def get_existing_keys(self, field_name_str: str = "recvPath") -> set[str]:
        """
        BigQuery 테이블에서 특정 필드(기본값: recvPath)의 기존 값들을 조회하여 set 구조로 반환합니다.

        :param field_name_str: 기존 값을 조회할 컬럼명 (기본값: recvPath 또는 ecs_key)
        :return: 이미 적재된 키 값들의 set 집합
        """
        table_ref_str: str = f"{self.project_id_str}.{self.dataset_id_str}.{self.table_id_str}"
        query_str: str = f"SELECT DISTINCT `{field_name_str}` FROM `{table_ref_str}` WHERE `{field_name_str}` IS NOT NULL"
        try:
            query_job_obj: Any = self.client.query(query_str, timeout=self.timeout_seconds_int)
            query_results_obj: Any = query_job_obj.result()
            return {str(row[field_name_str]) for row in query_results_obj if row[field_name_str] is not None}
        except Exception as fetch_exc:
            self.logger.exception("existing_keys_fetch_failed", service_name="BigQuery", error=str(fetch_exc))
            return set()

    def merge_table_from_json_data(
        self,
        json_data_any: Any,
        pk_key_str: str = "id",
        preserve_columns_list: list[str] | None = None,
        column_types_dict: dict[str, str] | None = None,
        matched_condition_str: str | None = None,
        not_matched_condition_str: str | None = None,
        post_queries_list: list[dict[str, Any]] | None = None,
        chunk_size_int: int = 100,
        timeout_int: int | None = None,
    ) -> None:
        """
        BigQuery 타겟 테이블에 인라인 MERGE INTO(Upsert)를 수행합니다 (순수 범용 메서드).

        기존에 존재하는 행(PK 기준)은 UPDATE(preserve_columns 제외)하고, 존재하지 않는 행은 INSERT합니다.

        :param json_data_any: 병합 적재할 단일 dict 또는 dict 리스트
        :param pk_key_str: 테이블 병합 매칭 기준이 되는 기본키(Primary Key) 컬럼명 (기본값: 'id')
        :param preserve_columns_list: UPDATE 시 덮어쓰지 않고 최초 값을 보존할 컬럼명 리스트 (예: 최초 생성일시 등)
        :param column_types_dict: 컬럼별 명시적 SQL 타입 매핑 딕셔너리 (예: {"size": "INT64", "meta": "JSON"}). 미지정 시 데이터 타입 기반 자동 추론
        :param matched_condition_str: WHEN MATCHED 절에 추가할 조건식 (예: "AND (S.amndHMS > T.amndHMS OR T.amndHMS IS NULL)")
        :param not_matched_condition_str: WHEN NOT MATCHED 절에 추가할 조건식 (예: "AND S.status != 'DELETED'")
        :param post_queries_list: MERGE 완료 후 실행할 후속 쿼리 목록 ([{"sql": "UPDATE ...", "params": [...]}, ...])
        :param chunk_size_int: 쿼리 파라미터 크기 제한을 고려한 청크 분할 단위 (기본값: 100)
        :param timeout_int: 쿼리 실행 타임아웃 제한 시간(초)
        :return: None
        :raises ValueError: 지원하지 않는 입력 데이터 타입일 경우 발생
        :raises RuntimeError: MERGE 쿼리 실행 실패 시 발생
        """
        if not json_data_any:
            return

        rows_list: list[dict[str, Any]] | None = (
            [json_data_any] if isinstance(json_data_any, dict) else (json_data_any if isinstance(json_data_any, list) else None)
        )
        if rows_list is None:
            raise ValueError(f"지원하지 않는 JSON 데이터 포맷 구조입니다: {type(json_data_any)}")

        if not rows_list:
            return

        merge_timeout_int: int = timeout_int if timeout_int is not None else self.timeout_seconds_int
        target_table_ref_str: str = f"{self.project_id_str}.{self.dataset_id_str}.{self.table_id_str}"
        preserve_cols_set: set[str] = set(preserve_columns_list or [])
        preserve_cols_set.add(pk_key_str)

        sample_row_dict: dict[str, Any] = rows_list[0]
        cols_list: list[str] = list(sample_row_dict.keys())
        explicit_types_dict: dict[str, str] = column_types_dict or {}

        # 1. UPDATE 대상 컬럼 구성
        update_cols_list: list[str] = [c for c in cols_list if c not in preserve_cols_set]
        update_set_clause_str: str = ",\n        ".join([f"T.`{c}` = S.`{c}`" for c in update_cols_list])

        # 2. INSERT 대상 컬럼 및 값 매핑
        insert_cols_str: str = ", ".join([f"`{c}`" for c in cols_list])
        insert_vals_str: str = ", ".join([f"S.`{c}`" for c in cols_list])

        # 3. UNNEST SELECT 절 캐스팅 동적 생성 (명시적 타입 또는 파이썬 데이터 타입 기반 자동 추론)
        select_expressions_list: list[str] = []
        for col_str in cols_list:
            val_any = sample_row_dict.get(col_str)
            safe_col_path_str: str = col_str.replace('"', '\\"')
            if col_str in explicit_types_dict:
                sql_type_str: str = explicit_types_dict[col_str].upper()
                if sql_type_str in ("JSON", "RECORD", "STRUCT"):
                    expr_str: str = f"PARSE_JSON(JSON_QUERY(item, '$.\"{safe_col_path_str}\"')) AS `{col_str}`"
                elif sql_type_str.startswith("TIMESTAMP"):
                    expr_str = f"TIMESTAMP(JSON_VALUE(item, '$.\"{safe_col_path_str}\"')) AS `{col_str}`"
                elif sql_type_str.startswith("DATETIME"):
                    expr_str = f"DATETIME(JSON_VALUE(item, '$.\"{safe_col_path_str}\"')) AS `{col_str}`"
                elif sql_type_str.startswith("DATE"):
                    expr_str = f"DATE(JSON_VALUE(item, '$.\"{safe_col_path_str}\"')) AS `{col_str}`"
                elif sql_type_str.startswith("TIME"):
                    expr_str = f"TIME(JSON_VALUE(item, '$.\"{safe_col_path_str}\"')) AS `{col_str}`"
                elif sql_type_str.startswith("INT") or sql_type_str.startswith("NUMERIC") or sql_type_str.startswith("FLOAT") or sql_type_str.startswith("BIG"):
                    expr_str = f"SAFE_CAST(JSON_VALUE(item, '$.\"{safe_col_path_str}\"') AS {sql_type_str}) AS `{col_str}`"
                elif sql_type_str.startswith("BOOL"):
                    expr_str = f"SAFE_CAST(JSON_VALUE(item, '$.\"{safe_col_path_str}\"') AS BOOL) AS `{col_str}`"
                else:
                    expr_str = f"JSON_VALUE(item, '$.\"{safe_col_path_str}\"') AS `{col_str}`"
            elif isinstance(val_any, (dict, list)):
                expr_str = f"PARSE_JSON(JSON_QUERY(item, '$.\"{safe_col_path_str}\"')) AS `{col_str}`"
            elif isinstance(val_any, bool):
                expr_str = f"SAFE_CAST(JSON_VALUE(item, '$.\"{safe_col_path_str}\"') AS BOOL) AS `{col_str}`"
            elif isinstance(val_any, int) and not isinstance(val_any, bool):
                expr_str = f"SAFE_CAST(JSON_VALUE(item, '$.\"{safe_col_path_str}\"') AS INT64) AS `{col_str}`"
            elif isinstance(val_any, float):
                expr_str = f"SAFE_CAST(JSON_VALUE(item, '$.\"{safe_col_path_str}\"') AS FLOAT64) AS `{col_str}`"
            else:
                expr_str = f"JSON_VALUE(item, '$.\"{safe_col_path_str}\"') AS `{col_str}`"
            select_expressions_list.append(expr_str)
        unnest_select_clause_str: str = ",\n      ".join(select_expressions_list)

        # 4. 신규 INSERT 및 수정 UPDATE 방어 조건절 구성 (호출자 주입식)
        matched_clause_str: str = f"WHEN MATCHED {matched_condition_str} THEN" if matched_condition_str else "WHEN MATCHED THEN"
        not_matched_clause_str: str = f"WHEN NOT MATCHED {not_matched_condition_str} THEN" if not_matched_condition_str else "WHEN NOT MATCHED THEN"

        merge_sql_template_str: str = f"""
MERGE `{target_table_ref_str}` T
USING (
    SELECT
      {unnest_select_clause_str}
    FROM UNNEST(JSON_QUERY_ARRAY(@json_payload)) AS item
) S
ON T.`{pk_key_str}` = S.`{pk_key_str}`
{matched_clause_str}
  UPDATE SET
    {update_set_clause_str}
{not_matched_clause_str}
  INSERT ({insert_cols_str})
  VALUES ({insert_vals_str})
"""

        total_rows_int: int = len(rows_list)
        total_chunks_int: int = (total_rows_int + chunk_size_int - 1) // chunk_size_int

        self.logger.info(
            "db_inline_merge_started",
            service_name="BigQuery",
            target_table=target_table_ref_str,
            total_rows=total_rows_int,
            chunk_size=chunk_size_int,
            total_chunks=total_chunks_int,
            pk_key=pk_key_str,
        )

        bigquery_module, _ = _get_bigquery()
        try:
            for chunk_idx_int in range(total_chunks_int):
                start_idx_int: int = chunk_idx_int * chunk_size_int
                end_idx_int: int = min(start_idx_int + chunk_size_int, total_rows_int)
                chunk_rows_list: list[dict[str, Any]] = rows_list[start_idx_int:end_idx_int]

                json_payload_str: str = json.dumps(chunk_rows_list, ensure_ascii=False, default=str)
                job_config_obj: Any = bigquery_module.QueryJobConfig(
                    query_parameters=[
                        bigquery_module.ScalarQueryParameter("json_payload", "STRING", json_payload_str)
                    ]
                )

                chunk_start_float: float = time.time()
                query_job_obj: Any = self.client.query(
                    merge_sql_template_str,
                    job_config=job_config_obj,
                    timeout=merge_timeout_int
                )
                query_job_obj.result(timeout=merge_timeout_int)
                chunk_elapsed_float: float = time.time() - chunk_start_float

                self.logger.info(
                    "db_inline_merge_chunk_completed",
                    service_name="BigQuery",
                    chunk_index=f"{chunk_idx_int + 1}/{total_chunks_int}",
                    processed_rows=len(chunk_rows_list),
                    elapsed_time=f"{chunk_elapsed_float:.2f}s",
                )

            # 5. 후속 쿼리(연쇄 업데이트 등)가 주입된 경우 동적 실행
            if post_queries_list:
                for post_idx_int, post_item_dict in enumerate(post_queries_list):
                    post_sql_str: str = post_item_dict.get("sql", "")
                    post_params_list: list[Any] = post_item_dict.get("params") or []
                    if post_sql_str:
                        post_job_config_obj: Any = bigquery_module.QueryJobConfig(query_parameters=post_params_list) if post_params_list else None
                        post_job_obj: Any = self.client.query(post_sql_str, job_config=post_job_config_obj, timeout=merge_timeout_int)
                        post_job_obj.result(timeout=merge_timeout_int)

            self.logger.info("db_inline_merge_all_completed", service_name="BigQuery", target_table=target_table_ref_str, total_rows=total_rows_int)
        except Exception as merge_exc:
            clean_error_str: str = str(merge_exc)
            raise RuntimeError(
                self.logger.exception(
                    "db_table_merge_failed",
                    service_name="BigQuery",
                    target_name=self.table_id_str,
                    error=clean_error_str,
                )
            ) from merge_exc

    def convert_to_bigquery_timestamp(self, val_any: Any, default_tz_offset_str: Optional[str] = None) -> Optional[str]:
        """
        다양한 원천 날짜/시간 문자열(YYYYMMDD, YYYYMMDDHHMMSS, ISO8601 등)을 BigQuery 표준 타임스탬프(YYYY-MM-DD HH:MM:SS{tz}) 포맷으로 변환합니다.
        원천 데이터에 타임존 오프셋이 명시되어 있지 않은 경우 config.yml의 bigquery.timezone_offset(기본값: '+09:00')을 적용합니다.

        :param val_any: 변환 대상 날짜/시간 데이터 (str, datetime, int 등)
        :param default_tz_offset_str: 타임존 오프셋이 없을 시 적용할 기본 오프셋 (미지정 시 config.yml 설정값 사용)
        :return: BigQuery 표준 타임스탬프 문자열 (변환 실패 시 None 반환)
        """
        if val_any is None:
            return None
        val_str = str(val_any).strip()
        if not val_str or val_str.lower() in ("none", "null", "{}") or "{" in val_str:
            return None

        applied_tz_offset_str: str = default_tz_offset_str if default_tz_offset_str is not None else self.timezone_offset_str

        # 타임존 오프셋 추출 정규식 (+09:00, +0900, -05:00, Z 등)
        tz_pattern_str: str = r"(?P<tz>Z|[+-]\d{2}:?\d{2})$"
        tz_match_obj: Any = re.search(tz_pattern_str, val_str)
        tz_suffix_str: str = applied_tz_offset_str
        if tz_match_obj:
            raw_tz_str: str = tz_match_obj.group("tz")
            if raw_tz_str == "Z":
                tz_suffix_str = "Z"
            elif len(raw_tz_str) == 5 and raw_tz_str[0] in "+-":
                tz_suffix_str = f"{raw_tz_str[:3]}:{raw_tz_str[3:]}"
            else:
                tz_suffix_str = raw_tz_str
            val_str = val_str[:tz_match_obj.start()].strip()

        # 1. YYYY-MM-DD HH:MM:SS (또는 T 구분자)
        match_obj = re.search(r"(\d{4}[-/]\d{2}[-/]\d{2}[ T]\d{2}:\d{2}:\d{2})", val_str)
        if match_obj:
            datetime_part_str: str = match_obj.group(1).replace("T", " ").replace("/", "-")
            return f"{datetime_part_str}{tz_suffix_str}"

        # 2. YYYY-MM-DD HH:MM
        match_obj = re.search(r"(\d{4}[-/]\d{2}[-/]\d{2}[ T]\d{2}:\d{2})", val_str)
        if match_obj:
            datetime_part_str = match_obj.group(1).replace("T", " ").replace("/", "-")
            return f"{datetime_part_str}:00{tz_suffix_str}"

        # 3. YYYY-MM-DD
        match_obj = re.search(r"(\d{4}[-/]\d{2}[-/]\d{2})", val_str)
        if match_obj:
            datetime_part_str = match_obj.group(1).replace("/", "-")
            return f"{datetime_part_str} 00:00:00{tz_suffix_str}"

        # 4. YYYYMMDDHHMMSS (14자리 숫자)
        match_obj = re.search(r"(\d{14})", val_str)
        if match_obj:
            num_str: str = match_obj.group(1)
            return f"{num_str[:4]}-{num_str[4:6]}-{num_str[6:8]} {num_str[8:10]}:{num_str[10:12]}:{num_str[12:14]}{tz_suffix_str}"

        # 5. YYYYMMDD (8자리 숫자)
        match_obj = re.search(r"(\d{8})", val_str)
        if match_obj:
            num_str = match_obj.group(1)
            return f"{num_str[:4]}-{num_str[4:6]}-{num_str[6:8]} 00:00:00{tz_suffix_str}"

        return None

