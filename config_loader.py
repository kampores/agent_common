# 작성일: 2026-06-18
# 설계자: 김유상
# 설계자 소속: 경포씨엔씨
# 설계자 이메일: bakkus@kpcnc.co.kr, bakkus@daum.net

"""
설정 파일(.yml)을 로컬 및 원격 통합 경로에서 동적으로 읽어들이고 병합하는 설정 로더 클래스 및 모듈입니다.
"""

from __future__ import annotations

import os
import re
import sys
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from agent_common.logger import ProjectLogger

import yaml
from agent_common.utils import DateTimeUtils


class ReadOnlyConfig:
    """YAML 설정 딕셔너리를 감싸서 점 표기법(Dot-notation, 속성 접근) 및 불변성(Read-Only)을 제공하는 설정 래퍼 클래스입니다.

    도메인 의미: config.ecs.endpoint_url, config.transfer.max_workers 형태로
    설정값을 직관적으로 조회할 수 있으며, 런타임에 설정값이 임의로 변조되는 것을 방지합니다.
    """

    def __init__(self, data: dict[str, Any] | Any) -> None:
        """딕셔너리 데이터를 기반으로 ReadOnlyConfig 인스턴스를 초기화합니다."""
        object.__setattr__(self, "_data", data if isinstance(data, dict) else {})

    def __getattr__(self, key: str) -> Any:
        """점 표기법(속성)으로 설정값을 조회하며 하위 딕셔너리는 ReadOnlyConfig로 자동 래핑합니다."""
        data: dict[str, Any] = object.__getattribute__(self, "_data")
        if key not in data:
            raise AttributeError(f"config.yml에 정의되지 않은 설정 항목입니다: '{key}'")
        val = data[key]
        if isinstance(val, dict):
            return ReadOnlyConfig(val)
        if isinstance(val, list):
            return [ReadOnlyConfig(item) if isinstance(item, dict) else item for item in val]
        return val

    def __getitem__(self, key: str) -> Any:
        """딕셔너리 키 인덱싱 표기법(config['ecs'])으로 조회합니다."""
        return self.__getattr__(key)

    def get(self, key: str, default: Any = None) -> Any:
        """키에 해당하는 설정값을 반환하며, 미존재 시 default 값을 반환합니다."""
        data: dict[str, Any] = object.__getattribute__(self, "_data")
        if key not in data:
            return default
        val = data[key]
        if isinstance(val, dict):
            return ReadOnlyConfig(val)
        if isinstance(val, list):
            return [ReadOnlyConfig(item) if isinstance(item, dict) else item for item in val]
        return val

    def __contains__(self, key: str) -> bool:
        """설정 키 존재 여부(in 연산자)를 확인합니다."""
        data: dict[str, Any] = object.__getattribute__(self, "_data")
        return key in data

    def __setattr__(self, key: str, value: Any) -> None:
        """설정값 임의 수정을 차단합니다 (불변성 유지)."""
        raise TypeError("config 설정값은 런타임에 수정할 수 없습니다 (Read-Only).")

    def __setitem__(self, key: str, value: Any) -> None:
        """설정값 임의 수정을 차단합니다 (불변성 유지)."""
        raise TypeError("config 설정값은 런타임에 수정할 수 없습니다 (Read-Only).")

    def __delattr__(self, key: str) -> None:
        """설정값 임의 삭제를 차단합니다 (불변성 유지)."""
        raise TypeError("config 설정값은 런타임에 삭제할 수 없습니다 (Read-Only).")

    def __delitem__(self, key: str) -> None:
        """설정값 임의 삭제를 차단합니다 (불변성 유지)."""
        raise TypeError("config 설정값은 런타임에 삭제할 수 없습니다 (Read-Only).")

    def to_dict(self) -> dict[str, Any]:
        """내부 원본 딕셔너리를 반환합니다."""
        return object.__getattribute__(self, "_data")

    def __repr__(self) -> str:
        """객체 문자열 표현을 반환합니다."""
        data: dict[str, Any] = object.__getattribute__(self, "_data")
        return f"ReadOnlyConfig({data!r})"

    def __str__(self) -> str:
        """객체 문자열 표현을 반환합니다."""
        data: dict[str, Any] = object.__getattribute__(self, "_data")
        return str(data)


class ConfigLoader:
    """설정 파일(.yml)을 로컬 및 원격 통합 경로에서 동적으로 읽어들이고 병합하는 설정 로더 클래스입니다.

    도메인 의미: 공통 패키지 및 애플리케이션 프로젝트의 YAML 설정 파일들을 계층적으로 병합(Deep Merge)하며,
    점 표기법(Dot-notation) 기반의 설정값 조회, 도메인별 스키마 등록 및 자동 보정(Self-healing),
    Fail-Fast 필수 설정 검증(require_setting)을 제공합니다.
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
            except (ValueError, OSError):
                # 대화형 REPL, python -c 등 특수 환경에서 유효하지 않은 argv[0] 경로 무시 (1번 cwd로 탐색)
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
        self._registered_schemas: dict[str, Any] = {}

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

    def register_schema(self, schema_dict: dict[str, Any]) -> None:
        """개별 프로그램에서 요구하는 도메인 기본 설정 스키마/키 딕셔너리를 등록합니다.
        
        등록된 기본값은 config.yml 에 해당 키가 정의되지 않았을 때 fallback 베이스로 자동 적용됩니다.
        """
        if isinstance(schema_dict, dict):
            self._deep_merge(self._registered_schemas, schema_dict)
            self._cached_settings = None

    def ensure_config_file(self, config_file_name: str = "config.yml", default_schema: Optional[dict[str, Any]] = None) -> Path:
        """설정 파일의 실체 존재 여부를 검증하고, 미존재 시 기본 스키마 템플릿으로 자동 생성하거나
        기존 파일 내 누락된 키를 보정(Self-healing)합니다.
        
        :param config_file_name: 대상 설정 파일명 (기본값: 'config.yml')
        :param default_schema: 파일 생성 시 기록할 기본 딕셔너리 스키마 (옵션)
        :return: 대상 설정 파일의 절대 Path 객체
        """
        target_path = self.config_dir / config_file_name
        self.config_dir.mkdir(parents=True, exist_ok=True)

        merged_defaults = {}
        if self._registered_schemas:
            self._deep_merge(merged_defaults, self._registered_schemas)
        if default_schema and isinstance(default_schema, dict):
            self._deep_merge(merged_defaults, default_schema)

        if not target_path.exists():
            # 1. 파일이 아예 없으면 기본 스키마로 파일 신규 생성
            initial_data = merged_defaults if merged_defaults else {"app": {"name": "app"}}
            now_dt_str = DateTimeUtils.get_now_formatted()
            header_tmpl = self.setting("templates.config_notice_header", "")
            if header_tmpl:
                header_comment = header_tmpl.format(config_file_name=config_file_name, now_dt_str=now_dt_str)
                if not header_comment.endswith("\n"):
                    header_comment += "\n"
            else:
                header_comment = ""

            try:
                yaml_str = yaml.dump(initial_data, allow_unicode=True, sort_keys=False)
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(header_comment + yaml_str)
                self.logger.info("config_file_auto_created", file_path=str(target_path))
            except Exception as e:
                self.logger.exception("config_auto_create_failed", file_path=str(target_path), error=str(e))
        else:
            # 2. 파일이 존재할 경우 누락된 키가 있으면 자동 보정
            if merged_defaults:
                try:
                    current_data = self._load_yaml_mapping(target_path)
                    repaired_keys: list[str] = []
                    for k, v in merged_defaults.items():
                        if k not in current_data:
                            current_data[k] = v
                            repaired_keys.append(k)
                        elif isinstance(v, dict) and isinstance(current_data[k], dict):
                            for sub_k, sub_v in v.items():
                                if sub_k not in current_data[k]:
                                    current_data[k][sub_k] = sub_v
                                    repaired_keys.append(f"{k}.{sub_k}")

                    if repaired_keys:
                        now_dt_str = DateTimeUtils.get_now_formatted()
                        repair_tmpl = self.setting("templates.config_repair_inline_comment", "# [자동 추가: {now_dt_str}]")
                        inline_comment = repair_tmpl.format(now_dt_str=now_dt_str)

                        yaml_str = yaml.dump(current_data, allow_unicode=True, sort_keys=False)
                        lines = yaml_str.splitlines()
                        repaired_leaf_keys = {k.split(".")[-1] for k in repaired_keys}

                        new_lines = []
                        for line in lines:
                            stripped = line.strip()
                            is_target = False
                            for lk in repaired_leaf_keys:
                                if (stripped == f"{lk}:" or stripped.startswith(f"{lk}: ")) and "#" not in stripped:
                                    is_target = True
                                    break
                            if is_target:
                                new_lines.append(f"{line}  {inline_comment}")
                            else:
                                new_lines.append(line)

                        final_yaml_str = "\n".join(new_lines) + "\n"
                        with open(target_path, "w", encoding="utf-8") as f:
                            f.write(final_yaml_str)
                        self.logger.info("config_file_auto_repaired", file_path=str(target_path), repaired_keys=repaired_keys)
                except Exception as repair_err:
                    self.logger.exception("config_auto_repair_failed", file_path=str(target_path), error=str(repair_err))

        self._cached_settings = None
        return target_path

    def get_settings(self) -> dict[str, Any]:
        """설정 디렉토리 하위의 모든 YAML 설정 파일을 알파벳 순서로 병합하여 반환한다.
        
        1차: agent_common 패키지 내부 기본 설정 (agent_common/config)
        2차: 등록된 도메인 스키마 기본값 (register_schema)
        3차: 개별 프로젝트 config 디렉토리의 YAML 파일들 (Deep Merge Override)
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

        # 2. 등록된 도메인 스키마 기본값 병합
        if self._registered_schemas:
            self._deep_merge(settings, self._registered_schemas)
                
        # 3. 호출 프로젝트 고유 설정 로드 및 오버라이드 (.yml 및 .yaml 확장자 모두 탐색)
        if self.config_dir.exists():
            yml_files = sorted(set(list(self.config_dir.glob("*.yml")) + list(self.config_dir.glob("*.yaml"))))
            for path in yml_files:
                mapping = self._load_yaml_mapping(path)
                loaded_files.append(f"{path.name}:{list(mapping.keys())}")
                self._deep_merge(settings, mapping)

        self._loaded_files_summary: str = ", ".join(loaded_files) if loaded_files else "읽어들인 YAML 파일 없음"

        # 4. proxy, no_proxy 설정을 NO_PROXY 환경 변수로 적용한다.
        self._apply_no_proxy(settings)

        self._cached_settings = settings
        return settings

    def _apply_no_proxy(self, settings: dict[str, Any]) -> None:
        """proxy.no-proxy 설정 값을 NO_PROXY 환경 변수로 적용한다."""
        no_proxy_value = settings.get("proxy", {}).get("no_proxy")
        if no_proxy_value:
            existing = os.environ.get("NO_PROXY", "")
            if existing:
                os.environ["NO_PROXY"] = f"{existing},{no_proxy_value}"
            else:
                os.environ["NO_PROXY"] = str(no_proxy_value)

    def setting(self, path: str, default: Any = None) -> Any:
        """
        점 표기법 경로(예: 'api.port', 'transfer.lodin_dstlc_cd')를 사용해 병합된 설정값을 조회합니다.

        :param path: 점 표기법 설정 경로 문자열
        :param default: 설정값이 없거나 유효하지 않을 때 반환할 기본 fallback 값 (기본값: None)
        :return: 조회된 설정값 또는 기본값
        """
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

        :param path: 점 표기법 필수 설정 경로 (예: 'schema_config.pk_key')
        :param message: 설정값 누락 시 추가 안내 설명 메시지 (옵션)
        :param config_file: 해당 설정값이 정의되어야 하는 설정 파일명 (기본값: 'config.yml')
        :return: 설정 파일에 정의된 필수 설정값
        """
        cfg_name = str(config_file).strip() if (config_file and isinstance(config_file, str)) else "config.yml"
        
        # 1. 파일 경로 정규화 (절대 경로, 프로젝트 루트 기준 경로, config_dir 기준 경로 순차 탐색)
        if Path(cfg_name).is_absolute():
            target_path = Path(cfg_name)
        elif (self.ROOT / cfg_name).exists() or any(p in cfg_name for p in ("/", "\\")):
            target_path = self.project_path(cfg_name)
        else:
            target_path = self.config_dir / cfg_name

        # 2. 대상 데이터 소스 로드 (기본 config.yml 일 경우 get_settings() 캐시 활용, 별도 파일일 경우 직접 로드)
        if target_path == (self.config_dir / "config.yml") or cfg_name == "config.yml":
            current: Any = self.get_settings()
        else:
            if not target_path.exists():
                current = None
            else:
                try:
                    current = self._load_yaml_mapping(target_path)
                except Exception as read_err:
                    current = None
                    message = f"{message} (파일 파싱 오류: {read_err})" if message else f"파일 파싱 오류: {read_err}"

        # 3. 점(.) 표기법 경로 탐색
        if isinstance(current, dict):
            for key in path.split("."):
                if not isinstance(current, dict) or key not in current:
                    current = None
                    break
                current = current[key]
        else:
            current = None

        if current is None or (isinstance(current, str) and not current.strip()):
            desc_info = f" ({message})" if message else ""
            exists_status = "파일 존재함" if target_path.exists() else "파일 없음"

            all_settings = self.get_settings()
            loaded_keys = list(all_settings.keys()) if isinstance(all_settings, dict) else []
            files_summary = getattr(self, "_loaded_files_summary", "미조회")
            full_cfg_info = f"{target_path} [{exists_status}] (로드된 파일별 키: [{files_summary}], 최종 병합 키: {loaded_keys})"

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
        """
        프로젝트 루트를 기준으로 한 상대 경로를 절대 경로로 변환하여 반환합니다.

        :param path: 절대 경로 또는 프로젝트 루트 기준 상대 경로
        :return: 정규화된 절대 Path 객체
        """
        value = Path(path)
        if value.is_absolute():
            return value
        return self.ROOT / value

    @staticmethod
    def _load_yaml_mapping(path: Path) -> dict[str, Any]:
        """
        지정된 YAML 파일을 파싱하여 최상위 매핑 딕셔너리로 읽어들입니다 (UTF-8 / BOM 지원).

        :param path: 파싱할 대상 YAML 파일 절대 경로
        :return: 파싱된 딕셔너리 객체
        """
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
        """
        두 딕셔너리를 재귀적으로 병합하며 중복 키는 덮어씁니다 (Deep Merge).

        :param target: 병합 대상 기준 딕셔너리 (인플레이스 수정됨)
        :param incoming: 덮어쓸 신규 딕셔너리
        """
        for key, value in incoming.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                ConfigLoader._deep_merge(target[key], value)
            else:
                target[key] = value

    @property
    def config(self) -> ReadOnlyConfig:
        """현재 병합된 전체 설정을 읽기 전용 점 표기법(Dot-notation) 객체로 반환합니다 (Getter)."""
        return ReadOnlyConfig(self.get_settings())


# 전역 기본 싱글톤 인스턴스 생성
_default_loader = ConfigLoader()

ROOT = ConfigLoader.ROOT
PACKAGE_DIR = ConfigLoader.PACKAGE_DIR
CONFIG_DIR = _default_loader.config_dir

# 전역에서 바로 import 하여 점 표기법(config.ecs.endpoint_url)으로 쓸 수 있는 읽기 전용 설정 객체
config: ReadOnlyConfig = _default_loader.config

