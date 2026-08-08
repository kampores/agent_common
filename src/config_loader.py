# 작성일: 2026-06-18
# 설계자: 김유상
# 설계자 소속: 경포씨엔씨
# 설계자 이메일: bakkus@kpcnc.co.kr, bakkus@daum.net

"""
설정 파일(.yml)을 로컬 및 원격 통합 경로에서 동적으로 읽어들이고 병합하는 설정 로더 클래스 및 모듈입니다.
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import yaml

from agent_common.logger import ProjectLogger


class ConfigLoader:
    """설정 파일(.yml)을 로컬 및 원격 통합 경로에서 동적으로 읽어들이고 병합하는 설정 로더 클래스입니다.

    도메인 의미: 공통 패키지 및 애플리케이션 프로젝트의 YAML 설정 파일들을 계층적으로 병합(Deep Merge)하며,
    점 표기법(Dot-notation) 기반의 설정값 조회 및 Fail-Fast 필수 설정 검증(require_setting)을 제공합니다.
    """

    # 호출하는 메인 프로젝트의 루트 디렉토리 경로를 계산합니다.
    ROOT: Path = Path(os.getcwd()).resolve()

    # agent_common 패키지 자체의 루트 디렉토리 경로를 계산합니다.
    PACKAGE_DIR: Path = Path(__file__).resolve().parent.parent

    # 설정 파일이 위치한 기본 디렉토리 (전역 설정 또는 스크립트별 개별 설정을 담은 YAML 파일의 위치)
    CONFIG_DIR: Path = ROOT / "config"

    @classmethod
    def configure(cls, config_dir: str | Path) -> None:
        """설정 파일들을 로드할 디렉토리를 명시적으로 지정한다.

        지정 후 캐시를 비워 새로운 설정값들이 반환되도록 초기화한다.
        """
        cls.CONFIG_DIR = cls.project_path(config_dir)
        global CONFIG_DIR
        CONFIG_DIR = cls.CONFIG_DIR
        cls.get_settings.cache_clear()

    @classmethod
    @lru_cache(maxsize=1)
    def get_settings(cls) -> dict[str, Any]:
        """설정 디렉토리 하위의 모든 YAML 설정 파일을 알파벳 순서로 병합하여 반환한다.
        
        1차로 agent_common 패키지 내부의 기본 설정을 병합 로드하고,
        2차로 개별 에이전트 프로젝트의 config 디렉토리 설정들로 오버라이드(Deep Merge)합니다.

        도메인 의미: 병합된 설정에서 proxy, no_proxy 값을 읽어 NO_PROXY 환경 변수로 자동 적용하여,
        urllib 기반 HTTP 클라이언트가 localhost 및 내부 서비스 접근시 사내 프록시를 우회하도록 한다.
        """
        settings: dict[str, Any] = {}
        
        # 1. agent_common 패키지 내부 기본 설정 로드
        common_config_dir = cls.PACKAGE_DIR / "config"
        if common_config_dir.exists():
            for path in sorted(common_config_dir.glob("*.yml")):
                cls._deep_merge(settings, cls._load_yaml_mapping(path))
                
        # 2. 호출 프로젝트 고유 설정 로드 및 오버라이드
        if cls.CONFIG_DIR.exists():
            for path in sorted(cls.CONFIG_DIR.glob("*.yml")):
                cls._deep_merge(settings, cls._load_yaml_mapping(path))

        # 3. proxy,no_proxy 설정을 NO_PROXY 환경 변수로 적용한다.
        cls._apply_no_proxy(settings)

        return settings

    @classmethod
    def _apply_no_proxy(cls, settings: dict[str, Any]) -> None:
        """proxy.no-proxy 설정 값을 NO_PROXY 환경 변수로 적용한다.
        
        도메인 의미: urllib.request.urlopen()은 NO_PROXY 환경 변수를 자동 참조하므로,
        설정 파일에 정의된 우회 대상 호스트를 환경 변수로 주입하면 HTTP 요청 시 프록시를 우회할 수 있다.
        이미 설정된 NO_PROXY 값이 있으면 기존 값과 병합한다.
        """
        no_proxy_value = settings.get("proxy", {}).get("no_proxy")
        if no_proxy_value:
            existing = os.environ.get("NO_PROXY", "")
            if existing:
                os.environ["NO_PROXY"] = f"{existing},{no_proxy_value}"
            else:
                os.environ["NO_PROXY"] = str(no_proxy_value)

    @classmethod
    def setting(cls, path: str, default: Any = None) -> Any:
        """점 표기법 경로(예: 'api.port')를 사용해 병합된 설정값을 조회한다."""
        current: Any = cls.get_settings()
        for key in path.split("."):
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        return current

    @classmethod
    def require_setting(
        cls, 
        path: str, 
        message: str = "", 
        config_file: str = "config.yml"
    ) -> Any:
        """
        [Fail-Fast 정책 준수]
        프로그램 기동에 필요한 필수 설정값을 점 표기법(예: 'schema_config.pk_key')으로 조회합니다.
        설정값이 누락되어 있거나 빈 값인 경우, 명시된 설정 파일명과 함께 오류 메시지를 CLI 및 로그로 출력하고
        프로세스를 즉시 강제 종료(sys.exit(1))하여 빠른 실패(Fail-Fast)를 유도합니다.

        :param path: 점 표기법 설정 경로 (예: 'schema_config.pk_key')
        :param message: 설정값 누락 시 추가 안내 설명 메시지 (옵션)
        :param config_file: 해당 설정값이 정의되어야 하는 설정 파일명 (기본값: 'config.yml')
        :return: 설정 파일에 정의된 필수 설정값
        """
        current: Any = cls.get_settings()
        for key in path.split("."):
            if not isinstance(current, dict) or key not in current:
                current = None
                break
            current = current[key]

        if current is None or (isinstance(current, str) and not current.strip()):
            desc_info = f" ({message})" if message else ""
            cfg_name = config_file.strip() if (config_file and isinstance(config_file, str)) else "config.yml"
            from agent_common.logger import get_log_msg
            err_msg = get_log_msg(
                "CRITICAL",
                "fail_fast_config_missing",
                path=path,
                desc_info=desc_info,
                config_file=cfg_name
            )
            print(err_msg, file=sys.stderr)

            log_target = ProjectLogger.get_logger(f"agent_common.{cls.__name__}")
            log_target.error(err_msg)

            sys.exit(1)

        return current

    @classmethod
    def project_path(cls, path: str | Path) -> Path:
        """프로젝트 루트를 기준으로 한 상대 경로를 절대 경로로 변환하여 반환한다."""
        value = Path(path)
        if value.is_absolute():
            return value
        return cls.ROOT / value

    @staticmethod
    def _load_yaml_mapping(path: Path) -> dict[str, Any]:
        """지정된 YAML 파일을 파싱하여 최상위 매핑 딕셔너리로 읽어들인다."""
        with path.open("r", encoding="utf-8") as handle:
            settings = yaml.safe_load(handle) or {}
        if not isinstance(settings, dict):
            raise ValueError(f"Settings file must contain a YAML mapping: {path}")
        return settings

    @staticmethod
    def _deep_merge(target: dict[str, Any], incoming: dict[str, Any]) -> None:
        """두 딕셔너리를 재귀적으로 병합하며 중복 키는 덮어쓴다."""
        for key, value in incoming.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                ConfigLoader._deep_merge(target[key], value)
            else:
                target[key] = value


# 하위 호환성을 위해 기존 모듈 수준 상수를 바인딩합니다.
ROOT = ConfigLoader.ROOT
PACKAGE_DIR = ConfigLoader.PACKAGE_DIR
CONFIG_DIR = ConfigLoader.CONFIG_DIR

# 하위 호환성을 위해 기존 모듈 수준 함수 별칭을 제공합니다.
configure = ConfigLoader.configure
get_settings = ConfigLoader.get_settings
setting = ConfigLoader.setting
require_setting = ConfigLoader.require_setting
project_path = ConfigLoader.project_path
