# 작성일: 2026-07-20
# 설계자: 경포씨엔씨
# 설계자 소속: 김유상
# 설계자 이메일: bakkus@kpcnc.co.kr, bakkus@daum.net

"""
Dell ECS(S3), Google Cloud Storage(GCS), Google Cloud BigQuery(BQ) 등 
스토리지 및 데이터베이스 시스템과의 연결 및 데이터 입출력을 담당하는 공용 클라이언트 모듈입니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Generator

import boto3
from botocore.client import Config as BotoConfig
from google.cloud import storage, bigquery
from google.oauth2 import service_account

from agent_common.error_handler import ErrorHandler
from agent_common.config_loader import ConfigLoader
from agent_common.logger import ProjectLogger


class EcsClient:
    """
    Dell ECS (S3 호환) 저장소와의 연결 및 데이터 조회를 담당하는 공용 클라이언트 클래스.
    """

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        timeout_seconds: int | None = None,
    ):
        # endpoint_url: Dell ECS API 서버 주소 (예: http://xxx.yyy.zzz.uuu:0000)
        self.endpoint_url: str = endpoint_url
        # access_key: S3 연결에 사용하는 인증 키 ID
        self.access_key: str = access_key
        # secret_key: S3 연결에 사용하는 비밀번호
        self.secret_key: str = secret_key
        # bucket_name: 조회의 대상이 되는 ECS 버킷명
        self.bucket_name: str = bucket_name
        # logger: _logger 백킹 필드 초기화
        self._logger: ProjectLogger | None = ProjectLogger(f"agent_common.{self.__class__.__name__}")
        # config_loader: self 인스턴스 소유 ConfigLoader 객체 생성
        self.config_loader: ConfigLoader = ConfigLoader()
        # timeout_seconds: [Fail-Fast 정책 준수] 필수 설정값 조회 (누락 시 require_setting에서 sys.exit(1)로 즉시 강제 종료)
        resolved_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else self.config_loader.require_setting("transfer.timeout_seconds")
        )
        self.timeout_seconds: int = int(resolved_timeout)
        # client: boto3 s3 클라이언트 인스턴스
        self.client: Any = None
        self._connect()

    def _connect(self):
        """
        boto3 S3 클라이언트를 사용하여 Dell ECS 접속을 초기화하고 연결을 검증합니다.
        """
        try:
            self.client = boto3.client(
                "s3",
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                endpoint_url=self.endpoint_url,
                config=BotoConfig(
                    signature_version="s3v4",
                    connect_timeout=self.timeout_seconds,
                    read_timeout=self.timeout_seconds,
                    retries={"max_attempts": 2},
                ),
            )
        except Exception as e:
            # 공용 에러 핸들러 네트워크 예외 기록 수행
            ErrorHandler.handle_network_error(e, f"Dell ECS 연결 ({self.endpoint_url})")
            raise ConnectionError(self.logger.error("connection_failed", service_name="Dell ECS", error=str(e))) from e

    def list_objects(self, prefix: str = "") -> Generator[Dict[str, Any], None, None]:
        """
        지정된 버킷 및 프리픽스 범위 하위의 ECS 오브젝트 목록을 안전하게 조회(페이징)합니다.
        """
        try:
            paginator = self.client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)
            for page in pages:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        yield obj
        except Exception as e:
            raise RuntimeError(self.logger.error("list_failed", storage_type="ECS", error=str(e))) from e

    def get_object_stream(self, key: str) -> Any:
        """
        특정 파일의 파일 스트림 객체(StreamingBody)를 ECS로부터 획득합니다.
        """
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"]
        except Exception as e:
            raise RuntimeError(self.logger.error("transfer_failed", file_name=key, error=str(e))) from e

    def get_object_size(self, key: str) -> int | None:
        """
        Dell ECS 오브젝트의 파일 크기(bytes)를 헤더(head_object)로 빠르게 조회합니다.
        """
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=key)
            return response.get("ContentLength")
        except Exception:
            return None

    def transfer_to_gcs(
        self,
        gcs_client: GcsClient,
        ecs_key: str,
        gcs_blob_name: str,
        size: int,
    ) -> bool:
        """
        단일 파일에 대해 GCS 존재 여부 및 용량을 사전 검사하여, 동일 용량 파일 존재 시 복사를 건너뛰고(Skip),
        신규 파일이거나 용량이 다른 경우 ECS 스트림을 열고 GCS로 실시간 전송하며,
        구간별 통계 시간 및 단일 행 표준 로깅을 공통 처리합니다.

        :param gcs_client: 목적지 GCS 클라이언트 인스턴스
        :param ecs_key: 소스 ECS 객체 키 경로
        :param gcs_blob_name: 목적지 GCS 블롭 경로명
        :param size: 파일 바이트 크기
        :return: 전송 성공 또는 Skip 시 True, 실패 시 False
        """
        import time
        total_start = time.time()
        context_info = f"[ECS_Key={ecs_key} GCS_Blob={gcs_blob_name} Size={size}]"

        try:
            # 1. GCS 목적지의 기존 파일 존재 여부 및 바이트 크기 조회
            check_start = time.time()
            existing_size = gcs_client.get_blob_size(gcs_blob_name)
            check_elapsed = time.time() - check_start

            # 이미 GCS에 존재하고 용량이 동일한 경우 복사 건너뛰기
            if existing_size is not None and existing_size == size:
                self.logger.info("transfer_skipped", file_name=ecs_key, dst_type="GCS")
                self.logger.info(
                    "elapsed_time",
                    action_name="GCS 파일 검사",
                    details=f"[CheckTime={check_elapsed:.2f}s Status=Skipped]",
                    context_info=context_info,
                )
                return True

            # 2. ECS S3 StreamingBody 스트림 객체 생성 시간 측정
            ecs_start = time.time()
            stream = self.get_object_stream(ecs_key)
            ecs_stream_time = time.time() - ecs_start

            # 3. GCS 업로드 스트림 시간 측정
            gcs_start = time.time()
            gcs_client.upload_stream(stream, gcs_blob_name, size)
            gcs_upload_time = time.time() - gcs_start

            total_elapsed = time.time() - total_start
            self.logger.info("transfer_completed", file_name=ecs_key, size_bytes=size)
            self.logger.info(
                "elapsed_time",
                action_name="GCS 파일 전송",
                details=f"[TotalElapsed={total_elapsed:.2f}s CheckTime={check_elapsed:.2f}s ECSStreamTime={ecs_stream_time:.2f}s GCSUploadTime={gcs_upload_time:.2f}s]",
                context_info=context_info,
            )
            return True
        except Exception as e:
            total_elapsed = time.time() - total_start
            self.logger.error("transfer_failed", file_name=ecs_key, error=str(e))
            self.logger.error(
                "elapsed_time",
                action_name="GCS 파일 전송 오류",
                details=f"[TotalElapsed={total_elapsed:.2f}s]",
                context_info=context_info,
            )
            return False


class GcsClient:
    """
    Google Cloud Storage(GCS) 버킷 연결 및 파일 스트림 업로드를 담당하는 공용 클라이언트 클래스.
    """

    def __init__(
        self,
        bucket_name: str,
        credentials_path: str,
        timeout_seconds: int | None = None,
    ):
        # bucket_name: 대상 GCS 버킷명
        self.bucket_name: str = str(bucket_name).strip()
        # credentials_path: GCP 서비스 계정 키 JSON 경로
        self.credentials_path: str = credentials_path if credentials_path is not None else ""
        # logger: _logger 백킹 필드 초기화
        self._logger: ProjectLogger | None = ProjectLogger(f"agent_common.{self.__class__.__name__}")
        # config_loader: self 인스턴스 소유 ConfigLoader 객체 생성
        self.config_loader: ConfigLoader = ConfigLoader()
        # timeout_seconds: [Fail-Fast 정책 준수] 필수 설정값 조회 (누락 시 require_setting에서 sys.exit(1)로 즉시 강제 종료)
        resolved_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else self.config_loader.require_setting("transfer.timeout_seconds")
        )
        self.timeout_seconds: int = int(resolved_timeout)
        # client: google-cloud-storage 클라이언트 인스턴스
        self.client: Any = None
        # bucket: 연결 완료된 GCS Bucket 객체
        self.bucket: Any = None
        self._connect()

    def _connect(self):
        """
        Google Cloud Storage 클라이언트를 초기화하고 해당 버킷의 연결/접근 권한 상태를 검증합니다.
        """
        try:
            if self.credentials_path and self.credentials_path.strip() != "":
                cred_path = Path(self.credentials_path)
                if not cred_path.is_absolute():
                    cred_path = self.config_loader.project_path(cred_path)
                if not cred_path.exists():
                    raise FileNotFoundError(
                        f"인증키 파일을 찾을 수 없습니다: {cred_path} (config.yml 설정값: '{self.credentials_path}')"
                    )
                credentials = service_account.Credentials.from_service_account_file(
                    str(cred_path)
                )
                self.client = storage.Client(credentials=credentials)
            else:
                self.client = storage.Client()

            # 버킷에 대한 접근 권한 및 존재 여부 검사 (타임아웃 적용)
            self.bucket = self.client.get_bucket(self.bucket_name, timeout=self.timeout_seconds)
        except Exception as e:
            # 공용 에러 핸들러 네트워크 예외 기록 수행
            ErrorHandler.handle_network_error(e, f"GCS 버킷 연결 ({self.bucket_name})")
            raise ConnectionError(self.logger.error("connection_failed", service_name="GCS", error=str(e))) from e

    def get_blob_size(self, destination_blob_name: str) -> int | None:
        """GCS 목적지 blob의 존재 여부 및 바이트 크기(bytes)를 조회한다.

        Args:
            destination_blob_name: 조회할 GCS 오브젝트 blob 경로명

        Returns:
            int | None: blob이 존재하면 바이트 크기를 반환하며, 미존재 시 None을 반환한다.
        """
        try:
            blob = self.bucket.get_blob(destination_blob_name, timeout=self.timeout_seconds)
            if blob is not None:
                return blob.size
            return None
        except Exception as e:
            self.logger.warning("storage_meta_error", storage_type="GCS", target_name=destination_blob_name, error=str(e))
            return None

    def upload_stream(self, stream: Any, destination_blob_name: str, size: int, timeout: int | None = None):
        """
        입력되는 스트림 데이터를 GCS 목적지 blob에 직접 스트리밍 업로드합니다.
        """
        upload_timeout = timeout if timeout is not None else self.timeout_seconds
        try:
            blob = self.bucket.blob(destination_blob_name)
            # size 인수를 반드시 제공하며 지정된 timeout 내 업로드를 완료하도록 처리
            blob.upload_from_file(stream, size=size, timeout=upload_timeout)
        except Exception as e:
            raise RuntimeError(self.logger.error("transfer_failed", file_name=destination_blob_name, error=str(e))) from e



class BigQueryClient:
    """
    Google Cloud BigQuery(BQ) 테이블 연결 및 JSON 데이터 스트리밍 적재를 담당하는 공용 클라이언트 클래스.
    """

    def __init__(
        self,
        project_id: str,
        dataset_id: str,
        table_id: str,
        credentials_path: str,
        timeout_seconds: int | None = None,
        ignore_unknown_values: bool | None = None,
    ):
        # project_id: GCP 프로젝트 ID
        self.project_id: str = project_id
        # dataset_id: BigQuery 데이터셋 ID
        self.dataset_id: str = dataset_id
        # table_id: BigQuery 테이블 ID
        self.table_id: str = table_id
        # credentials_path: GCP 서비스 계정 키 JSON 경로 (비어있으면 기본 ADC 사용)
        self.credentials_path: str = credentials_path
        # logger: _logger 백킹 필드 초기화
        self._logger: ProjectLogger | None = ProjectLogger(f"agent_common.{self.__class__.__name__}")
        # config_loader: self 인스턴스 소유 ConfigLoader 객체 생성
        self.config_loader: ConfigLoader = ConfigLoader()
        # timeout_seconds: [Fail-Fast 정책 준수] 필수 설정값 조회 (누락 시 require_setting에서 sys.exit(1)로 즉시 강제 종료)
        resolved_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else self.config_loader.require_setting("transfer.timeout_seconds")
        )
        self.timeout_seconds: int = int(resolved_timeout)
        # ignore_unknown_values: 옵션 설정값 조회 (기본값: True)
        self.ignore_unknown_values: bool = (
            ignore_unknown_values
            if ignore_unknown_values is not None
            else bool(self.config_loader.setting("bigquery.ignore_unknown_values", True))
        )
        # _use_streaming_only: load_table_from_json 권한 문제 등으로 실패 시 즉시 스트리밍 전용 모드로 전환 플래그
        self._use_streaming_only: bool = False
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
    def logger(self, val: ProjectLogger) -> None:
        self._logger = val

    def _connect(self):
        """
        Google Cloud BigQuery 클라이언트를 초기화하고 연결 및 테이블 스키마 상태를 검증합니다.
        """
        try:
            if self.credentials_path and self.credentials_path.strip() != "":
                cred_path = Path(self.credentials_path)
                if not cred_path.is_absolute():
                    cred_path = self.config_loader.project_path(cred_path)
                if not cred_path.exists():
                    raise FileNotFoundError(
                        f"인증키 파일을 찾을 수 없습니다: {cred_path} (config.yml 설정값: '{self.credentials_path}')"
                    )
                credentials = service_account.Credentials.from_service_account_file(
                    str(cred_path)
                )
                self.client = bigquery.Client(credentials=credentials, project=self.project_id)
            else:
                self.client = bigquery.Client(project=self.project_id)
            
            # BigQuery Table 객체를 조회하여 스키마 타입(JSON, TIMESTAMP 등) 사전 캐싱
            table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
            try:
                self.table_obj = self.client.get_table(table_ref)
            except Exception as table_err:
                self.logger.warning("table_fetch_failed", service_name="BigQuery", fallback_ref=table_ref, error=str(table_err))
                self.table_obj = table_ref
        except Exception as e:
            ErrorHandler.handle_network_error(e, f"BigQuery 연결 (Project: {self.project_id})")
            raise ConnectionError(self.logger.error("connection_failed", service_name="BigQuery", error=str(e))) from e

    def insert_json_data(self, json_data: Any, timeout: int | None = None, ignore_unknown_values: bool | None = None):
        """
        JSON 객체(dict 또는 list)를 BigQuery 테이블에 적재합니다.
        1차적으로 load_table_from_json(배치 로드 Job)을 시도하며, 실패 시 fallback으로 insert_rows_json(스트리밍 로드)을 수행합니다.
        한 번 배치 로드가 실패하면 이후 호출부터는 insert_rows_json 전용 모드로 전환됩니다.
        """
        insert_timeout = timeout if timeout is not None else self.timeout_seconds
        skip_unknown = (
            ignore_unknown_values
            if ignore_unknown_values is not None
            else self.ignore_unknown_values
        )
        table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
        table_target = self.table_obj if getattr(self, "table_obj", None) else table_ref

        if isinstance(json_data, dict):
            rows_to_insert = [json_data]
        elif isinstance(json_data, list):
            rows_to_insert = json_data
        else:
            raise ValueError(f"지원하지 않는 JSON 데이터 포맷 구조입니다: {type(json_data)}")

        # 1. load_table_from_json (Batch Load Job) 우선 시도 (스트리밍 전용 모드가 아닐 때만)
        if not self._use_streaming_only:
            try:
                job_config = bigquery.LoadJobConfig(
                    source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                    ignore_unknown_values=skip_unknown,
                )
                if hasattr(self, "table_obj") and isinstance(self.table_obj, bigquery.Table):
                    job_config.schema = self.table_obj.schema

                load_job = self.client.load_table_from_json(
                    rows_to_insert,
                    table_target,
                    job_config=job_config,
                    timeout=insert_timeout,
                )
                load_job.result(timeout=insert_timeout)
                return
            except Exception as load_err:
                self._use_streaming_only = True
                clean_err = str(load_err).replace("\n", " ").replace("\r", " ")
                sub_err_list = []
                if hasattr(load_err, "errors") and getattr(load_err, "errors"):
                    for s_err in getattr(load_err, "errors"):
                        loc = s_err.get("location", "unknown_field") if isinstance(s_err, dict) else "unknown"
                        msg_str = s_err.get("message", str(s_err)) if isinstance(s_err, dict) else str(s_err)
                        sub_err_list.append(f"[Loc={loc}] {msg_str}")
                detailed_info = " | SubErrors: " + " ; ".join(sub_err_list) if sub_err_list else ""
                self.logger.warning(
                    "permission_fallback_applied",
                    service_name="BigQuery",
                    action_name="load_table_from_json 배치 적재",
                    fallback_mode="insert_rows_json 스트리밍 전용",
                )

        # 2. 예외 발생 시 fallback: insert_rows_json (Streaming Insert) 시도
        try:
            errors = self.client.insert_rows_json(
                table_target,
                rows_to_insert,
:                ignore_unknown_values=skip_unknown,
                timeout=insert_timeout,
            )
            if errors:
                err_details = []
                for err_item in errors:
                    idx = err_item.get("index", 0)
                    for e in err_item.get("errors", []):
                        loc = e.get("location", "unknown_field")
                        msg_str = e.get("message", "")
                        rsn = e.get("reason", "")
                        err_details.append(f"[Row={idx} Field={loc} Reason={rsn}] {msg_str}")
                combined_err_msg = " | ".join(err_details) if err_details else str(errors)
                raise RuntimeError(f"BigQuery API insert 반환 상세 에러: {combined_err_msg}")
        except Exception as e:
            clean_insert_err = str(e).replace("\n", " ").replace("\r", " ")
            raise RuntimeError(self.logger.error("insert_failed", service_name="BigQuery", target_name=self.table_id, error=clean_insert_err)) from e

    def get_existing_keys(self, field_name: str = "recvPath") -> set[str]:
        """
        BigQuery 테이블에서 특정 필드(기본값: recvPath)의 기존 값들을 조회하여 set 구조로 반환합니다.

        :param field_name: 기존 값을 조회할 컬럼명 (기본값: recvPath 또는 ecs_key)
        :return: 이미 적재된 키 값들의 set 집합
        """
        table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
        query = f"SELECT DISTINCT {field_name} FROM `{table_ref}` WHERE {field_name} IS NOT NULL"
        try:
            query_job = self.client.query(query, timeout=self.timeout_seconds)
            results = query_job.result()
            return {str(row[field_name]) for row in results if row[field_name] is not None}
        except Exception as e:
            self.logger.warning("existing_keys_fetch_failed", service_name="BigQuery", error=str(e))
            return set()
