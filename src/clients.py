# 작성일: 2026-07-20
# 설계자: 경포씨엔씨
# 설계자 소속: 김유상
# 설계자 이메일: bakkus@kpcnc.co.kr, bakkus@daum.net

"""
Dell ECS(S3), Google Cloud Storage(GCS), Google Cloud BigQuery(BQ) 등 
스토리지 및 데이터베이스 시스템과의 연결 및 데이터 입출력을 담당하는 공용 클라이언트 모듈입니다.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Generator

import boto3
from botocore.client import Config as BotoConfig
from google.cloud import storage
from google.cloud import bigquery
from google.oauth2 import service_account

from agent_common.error_handler import ErrorHandler
from agent_common.config_loader import setting


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
        logger: logging.Logger,
        error_messages: Dict[str, str],
        timeout_seconds: int | None = None,
    ):
        # endpoint_url: Dell ECS API 서버 주소 (예: http://10.39.79.21:9020)
        self.endpoint_url: str = endpoint_url
        # access_key: S3 연결에 사용하는 인증 키 ID
        self.access_key: str = access_key
        # secret_key: S3 연결에 사용하는 비밀번호
        self.secret_key: str = secret_key
        # bucket_name: 조회의 대상이 되는 ECS 버킷명
        self.bucket_name: str = bucket_name
        # logger: 프로그램 전체 로깅을 담당하는 로거 인스턴스
        self.logger: logging.Logger = logger
        # error_messages: 설정에서 인계된 다국어/템플릿 메시지 맵
        self.error_messages: Dict[str, str] = error_messages
        # timeout_seconds: 필수 설정값 조회 (누락 시 소스코드 상수로 fallback하지 않고 Fail-Fast 수행)
        resolved_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else (setting("transfer.timeout_seconds") or setting("timeout_seconds"))
        )
        if not resolved_timeout or str(resolved_timeout).strip() == "":
            msg = self.error_messages.get(
                "missing_required_config", "필수 설정 정보가 누락되었습니다: {key}"
            ).format(key="timeout_seconds")
            self.logger.critical(msg)
            raise ValueError(msg)

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
            msg = self.error_messages.get(
                "ecs_connection_failed", "Dell ECS 연결에 실패했습니다: {error}"
            ).format(error=str(e))
            raise ConnectionError(msg) from e

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
            msg = self.error_messages.get(
                "ecs_list_failed", "ECS 오브젝트 목록 조회에 실패했습니다: {error}"
            ).format(error=str(e))
            self.logger.error(msg)
            raise RuntimeError(msg) from e

    def get_object_stream(self, key: str) -> Any:
        """
        특정 파일의 파일 스트림 객체(StreamingBody)를 ECS로부터 획득합니다.
        """
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"]
        except Exception as e:
            raise RuntimeError(f"ECS 파일 스트림 획득 실패: {key}, 에러: {str(e)}") from e

    def get_object_size(self, key: str) -> int | None:
        """
        Dell ECS 오브젝트의 파일 크기(bytes)를 헤더(head_object)로 빠르게 조회합니다.
        """
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=key)
            return response.get("ContentLength")
        except Exception:
            return None


class GcsClient:
    """
    Google Cloud Storage(GCS) 버킷 연결 및 파일 스트림 업로드를 담당하는 공용 클라이언트 클래스.
    """

    def __init__(
        self,
        bucket_name: str,
        credentials_path: str,
        logger: logging.Logger,
        error_messages: Dict[str, str],
        timeout_seconds: int | None = None,
    ):
        # bucket_name: 대상 GCS 버킷명
        self.bucket_name: str = bucket_name
        # credentials_path: GCP 서비스 계정 키 JSON 경로 (비어있으면 기본 Application Default Credentials 사용)
        self.credentials_path: str = credentials_path
        # logger: 프로그램 전체 로깅을 담당하는 로거 인스턴스
        self.logger: logging.Logger = logger
        # error_messages: 설정에서 인계된 다국어/템플릿 메시지 맵
        self.error_messages: Dict[str, str] = error_messages
        # timeout_seconds: 필수 설정값 조회 (누락 시 소스코드 상수로 fallback하지 않고 Fail-Fast 수행)
        resolved_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else (setting("transfer.timeout_seconds") or setting("timeout_seconds"))
        )
        if not resolved_timeout or str(resolved_timeout).strip() == "":
            msg = self.error_messages.get(
                "missing_required_config", "필수 설정 정보가 누락되었습니다: {key}"
            ).format(key="timeout_seconds")
            self.logger.critical(msg)
            raise ValueError(msg)

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
                if not Path(self.credentials_path).exists():
                    raise FileNotFoundError(f"인증키 파일을 찾을 수 없습니다: {self.credentials_path}")
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                self.client = storage.Client(credentials=credentials)
            else:
                self.client = storage.Client()

            # 버킷에 대한 접근 권한 및 존재 여부 검사 (타임아웃 적용)
            self.bucket = self.client.get_bucket(self.bucket_name, timeout=self.timeout_seconds)
        except Exception as e:
            # 공용 에러 핸들러 네트워크 예외 기록 수행
            ErrorHandler.handle_network_error(e, f"GCS 버킷 연결 ({self.bucket_name})")
            msg = self.error_messages.get(
                "gcs_connection_failed", "GCS 연결에 실패했습니다: {error}"
            ).format(error=str(e))
            raise ConnectionError(msg) from e

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
            self.logger.warning("GCS blob 메타데이터 조회 중 오류 발생 (%s): %s", destination_blob_name, e)
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
            raise RuntimeError(f"GCS 업로드 실패: {destination_blob_name}, 에러: {str(e)}") from e



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
        logger: logging.Logger,
        error_messages: Dict[str, str],
        timeout_seconds: int | None = None,
        ignore_unknown_values: bool | None = None,
    ):
        # project_id: GCP 프로젝트 ID
        self.project_id: str = project_id
        # dataset_id: BigQuery 데이터셋 ID
        self.dataset_id: str = dataset_id
        # table_id: BigQuery 테이블 ID
        self.table_id: str = table_id
        # credentials_path: GCP 서비스 계정 키 JSON 경로
        self.credentials_path: str = credentials_path
        # logger: 프로그램 전체 로깅을 담당하는 로거 인스턴스
        self.logger: logging.Logger = logger
        # error_messages: 설정에서 인계된 다국어/템플릿 메시지 맵
        self.error_messages: Dict[str, str] = error_messages
        # timeout_seconds: 필수 설정값 조회 (누락 시 소스코드 상수로 fallback하지 않고 Fail-Fast 수행)
        resolved_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else (setting("transfer.timeout_seconds") or setting("timeout_seconds"))
        )
        if not resolved_timeout or str(resolved_timeout).strip() == "":
            msg = self.error_messages.get(
                "missing_required_config", "필수 설정 정보가 누락되었습니다: {key}"
            ).format(key="timeout_seconds")
            self.logger.critical(msg)
            raise ValueError(msg)

        self.timeout_seconds: int = int(resolved_timeout)
        # ignore_unknown_values: 미정의 JSON 키 무시/건너뛰기 여부 (config.yml에서 동적 로드)
        self.ignore_unknown_values: bool = (
            ignore_unknown_values
            if ignore_unknown_values is not None
            else bool(setting("bigquery.ignore_unknown_values", True))
        )
        # client: google-cloud-bigquery 클라이언트 인스턴스
        self.client: Any = None
        self._connect()

    def _connect(self):
        """
        Google Cloud BigQuery 클라이언트를 초기화하고 연결 및 테이블 스키마 상태를 검증합니다.
        """
        try:
            if self.credentials_path and self.credentials_path.strip() != "":
                if not Path(self.credentials_path).exists():
                    raise FileNotFoundError(f"인증키 파일을 찾을 수 없습니다: {self.credentials_path}")
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                self.client = bigquery.Client(
                    project=self.project_id, credentials=credentials
                )
            else:
                self.client = bigquery.Client(project=self.project_id)
            
            # BigQuery Table 객체를 조회하여 스키마 타입(JSON, TIMESTAMP 등) 사전 캐싱
            table_ref = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
            try:
                self.table_obj = self.client.get_table(table_ref)
            except Exception as table_err:
                self.logger.warning("BigQuery 테이블 객체 조회 실패 (기본 문자열 레퍼런스로 대체): %s", table_err)
                self.table_obj = table_ref
        except Exception as e:
            ErrorHandler.handle_network_error(e, f"BigQuery 연결 (Project: {self.project_id})")
            msg = self.error_messages.get(
                "bigquery_connection_failed", "BigQuery 연결에 실패했습니다: {error}"
            ).format(error=str(e))
            raise ConnectionError(msg) from e

    def insert_json_data(self, json_data: Any, timeout: int | None = None, ignore_unknown_values: bool | None = None):
        """
        JSON 객체(dict 또는 list)를 BigQuery 테이블에 적재합니다.
        1차적으로 load_table_from_json(배치 로드 Job)을 시도하며, 실패 시 fallback으로 insert_rows_json(스트리밍 로드)을 수행합니다.
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

        # 1. load_table_from_json (Batch Load Job) 우선 시도
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
            clean_err = str(load_err).replace("\n", " ").replace("\r", " ")
            self.logger.warning(
                "BigQuery load_table_from_json 배치 적재 실패 (insert_rows_json 스트리밍 적재로 fallback 시도): %s",
                clean_err,
            )

        # 2. 예외 발생 시 fallback: insert_rows_json (Streaming Insert) 시도
        try:
            errors = self.client.insert_rows_json(
                table_target,
                rows_to_insert,
                ignore_unknown_values=skip_unknown,
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
            msg = self.error_messages.get(
                "bigquery_insert_failed",
                "BigQuery 데이터 적재 실패: {table_id}, 에러: {error}",
            ).format(table_id=self.table_id, error=clean_insert_err)
            raise RuntimeError(msg) from e

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
            self.logger.warning("BigQuery 기존 적재 키 조회 중 오류 발생 (초기 적재이거나 컬럼 미존재 가능): %s", e)
            return set()

