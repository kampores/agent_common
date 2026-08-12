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
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agent_common.logger import ProjectLogger

import yaml


class ConfigLoader:
    """설정 파일(.yml)을 로컬 및 원격 통합 경로에서 동적으로 읽어들이고 병합하는 설정 로더 클래스입니다.

    도메인 의미: 공통 패키지 및 애플리케이션 프로젝트의 YAML 설정 파일들을 계층적으로 병합(Deep Merge)하며,
    점 표기법(Dot-notation) 기반의 설정값 조회 및 Fail-Fast 필수 설정 검증(require_setting)을 제공합니다.
    """

    @staticmethod
    def _find_project_root() -> Path:
        """현재 작업 디렉토리(심볼릭 링크 미해제/해제 포함), 실행 메인 스크립트(sys.argv[0]) 및 상위 디렉토리를 탐색하여 config/config.yml 이 존재하는 최상위 프로젝트 루트를 반환한다."""
        candidates: list[Path] = []

        # 1. 작업 디렉토리 (심볼릭 링크 원본 경로 및 resolve 경로 모두 수집)
        raw_cwd = Path(os.getcwd())
        resolved_cwd = raw_cwd.resolve()
        candidates.extend([raw_cwd] + list(raw_cwd.parents))
        candidates.extend([resolved_cwd] + list(resolved_cwd.parents))

        # 2. 실행 메인 스크립트 (sys.argv[0] 예: app/ecs_to_gcs.py 의 상위 디렉터리 app/.. )
        if sys.argv and sys.argv[0]:
            try:
                raw_main = Path(sys.argv[0])
                resolved_main = raw_main.resolve()
                for m_path in [raw_main, resolved_main]:
                    m_dir = m_path.parent if m_path.is_file() or not m_path.exists() else m_path
                    candidates.extend([m_dir] + list(m_dir.parents))
            except Exception:
                pass

        # 3. agent_common 패키지 자체 위치 및 상위 위치
        pkg_dir = Path(__file__).resolve().parent
        candidates.extend([pkg_dir] + list(pkg_dir.parents))

        # 중복 제거 (순서 유지)
        seen = set()
        unique_candidates: list[Path] = []
        for p in candidates:
            str_p = str(p)
            if str_p not in seen:
                seen.add(str_p)
                unique_candidates.append(p)

        for p in unique_candidates:
            if p.resolve() == pkg_dir.resolve():
                continue
            if (p / "config" / "config.yml").exists():
                return p

        return raw_cwd

    # 호출하는 메인 프로젝트의 루트 디렉토리 경로를 계산합니다.
    ROOT: Path = _find_project_root.__func__()

    # agent_common 패키지 자체의 루트 디렉토리 경로를 계산합니다.
    PACKAGE_DIR: Path = Path(__file__).resolve().parent

    def __init__(self, config_dir: str | Path | None = None):
        """ConfigLoader 인스턴스를 생성하고 self.logger 및 설정 디렉토리를 초기화합니다."""
        from agent_common.logger import ProjectLogger

        self._config_dir: Path = self.project_path(config_dir) if config_dir else self.ROOT / "config"
        self.logger: ProjectLogger = ProjectLogger(f"agent_common.{self.__class__.__name__}")

    def config_dir_get(self) -> Path:
        """설정 디렉토리 경로를 반환합니다 (Getter)."""
        return self._config_dir

    def config_dir_set(self, config_dir: str | Path) -> None:
        """설정 디렉토리 경로를 세팅하고 설정값 캐시를 초기화합니다 (Setter)."""
        self._config_dir = self.project_path(config_dir)
        self._cached_settings: dict[str, Any] | None = None

    @property
    def config_dir(self) -> Path:
        """설정 디렉토리 경로 프로퍼티 (Getter)."""
        return self.config_dir_get()

    @config_dir.setter
    def config_dir(self, config_dir: str | Path) -> None:
        """설정 디렉토리 경로 프로퍼티 (Setter)."""
        self.config_dir_set(config_dir)

    def configure(self, config_dir: str | Path) -> None:
        """설정 파일들을 로드할 디렉토리를 명시적으로 지정한다.

        지정 후 캐시를 비워 새로운 설정값들이 반환되도록 초기화한다.
        """
        self.config_dir_set(config_dir)

    def get_settings(self) -> dict[str, Any]:
        """설정 디렉토리 하위의 모든 YAML 설정 파일을 알파벳 순서로 병합하여 반환한다.
        
        1차로 agent_common 패키지 내부의 기본 설정을 병합 로드하고,
        2차로 개별 에이전트 프로젝트의 config 디렉토리 설정들로 오버라이드(Deep Merge)합니다.

        도메인 의미: 병합된 설정에서 proxy, no_proxy 값을 읽어 NO_PROXY 환경 변수로 자동 적용하여,
        urllib 기반 HTTP 클라이언트가 localhost 및 내부 서비스 접근시 사내 프록시를 우회하도록 한다.
        """
        if getattr(self, "_cached_settings", None) is not None:
            return self._cached_settings  # type: ignore

        settings: dict[str, Any] = {}
        loaded_files: list[str] = []
        
        # 1. agent_common 패키지 내부 기본 설정 로드 (agent_common/config)
        common_config_dir = self.PACKAGE_DIR / "config"
        if common_config_dir.exists():
            for path in sorted(common_config_dir.glob("*.yml")):
                mapping = self._load_yaml_mapping(path)
                self._deep_merge(settings, mapping)
                
        # 2. 호출 프로젝트 고유 설정 로드 및 오버라이드 (.yml 및 .yaml 확장자 모두 탐색)
        if self.config_dir.exists():
            yml_files = sorted(set(list(self.config_dir.glob("*.yml")) + list(self.config_dir.glob("*.yaml"))))
            for path in yml_files:
                mapping = self._load_yaml_mapping(path)
                loaded_files.append(f"{path.name}:{list(mapping.keys())}")
                self._deep_merge(settings, mapping)

        self._loaded_files_summary: str = ", ".join(loaded_files) if loaded_files else "읽어들인 YAML 파일 없음"

        # 3. proxy,no_proxy 설정을 NO_PROXY 환경 변수로 적용한다.
        self._apply_no_proxy(settings)

        self._cached_settings = settings
        return settings

    def _apply_no_proxy(self, settings: dict[str, Any]) -> None:
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

    def setting(self, path: str, default: Any = None) -> Any:
        """점 표기법 경로(예: 'api.port')를 사용해 병합된 설정값을 조회한다."""
        current: Any = self.get_settings()
        for key in path.split("."):
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        return current

    def require_setting(
        self, 
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
        current: Any = self.get_settings()
        for key in path.split("."):
            if not isinstance(current, dict) or key not in current:
                current = None
                break
            current = current[key]

        if current is None or (isinstance(current, str) and not current.strip()):
            desc_info = f" ({message})" if message else ""
            cfg_name = config_file.strip() if (config_file and isinstance(config_file, str)) else "config.yml"
            
            # 탐색 대상 설정 파일의 절대 경로 및 실체 존재 여부를 명확히 추적
            if Path(cfg_name).is_absolute():
                target_path = Path(cfg_name)
            else:
                target_path = self.config_dir / cfg_name
            exists_status = "파일 존재함" if target_path.exists() else "파일 없음"

            all_settings = self.get_settings()
            loaded_keys = list(all_settings.keys()) if isinstance(all_settings, dict) else []
            files_summary = getattr(self, "_loaded_files_summary", "미조회")
            full_cfg_info = f"{target_path} [{exists_status}] (config_dir: '{self.config_dir}', 로드된 파일별 키: [{files_summary}], 최종 병합 키: {loaded_keys})"

            err_msg = self.logger.critical(
                "fail_fast_config_missing",
                path=path,
                desc_info=desc_info,
                config_file=full_cfg_info
            )
            print(err_msg, file=sys.stderr)

            sys.exit(1)

        return current

    def project_path(self, path: str | Path) -> Path:
        """프로젝트 루트를 기준으로 한 상대 경로를 절대 경로로 변환하여 반환한다."""
        value = Path(path)
        if value.is_absolute():
            return value
        return self.ROOT / value

    @staticmethod
    def _load_yaml_mapping(path: Path) -> dict[str, Any]:
        """지정된 YAML 파일을 파싱하여 최상위 매핑 딕셔너리로 읽어들인다 (UTF-8 / BOM 지원)."""
        try:
            with path.open("r", encoding="utf-8-sig") as handle:
                settings = yaml.safe_load(handle) or {}
        except Exception as e:
            raise RuntimeError(f"YAML 설정 파일 읽기 실패 [{path}]: {e}") from e

        if not isinstance(settings, dict):
            raise ValueError(f"YAML 설정 파일이 올바른 딕셔너리 구조가 아닙니다: {path} (실제 타입: {type(settings)})")
        return settings

    @staticmethod
    def _deep_merge(target: dict[str, Any], incoming: dict[str, Any]) -> None:
        """두 딕셔너리를 재귀적으로 병합하며 중복 키는 덮어쓴다."""
        for key, value in incoming.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                ConfigLoader._deep_merge(target[key], value)
            else:
                target[key] = value


# 전역 기본 싱글톤 인스턴스 생성
_default_loader = ConfigLoader()

ROOT = ConfigLoader.ROOT
PACKAGE_DIR = ConfigLoader.PACKAGE_DIR
CONFIG_DIR = _default_loader.config_dir

configure = _default_loader.configure
get_settings = _default_loader.get_settings
setting = _default_loader.setting
require_setting = _default_loader.require_setting
project_path = _default_loader.project_path
config_dir_get = _default_loader.config_dir_get
config_dir_set = _default_loader.config_dir_set
