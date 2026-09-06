# 작성일: 2026-06-18
# 설계자: 김유상 수석
# 설계자 이메일: bakkus@daum.net

"""
설정 파일(.yml)을 로컬 및 원격 통합 경로에서 동적으로 읽어들이고 병합하는 설정 로더 클래스 및 모듈입니다.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

import yaml
from agent_common.error_handler import ErrorHandler
from agent_common.utils import DateTimeUtils


def coerce_type_by_key_suffix(key_str: str, val_any: Any) -> Any:
    """키 접미사(_int, _str, _bool, _float, _list, _dict)에 따라 값을 보증된 파이썬 표준 데이터 타입으로 엄격히 변환합니다.

    도메인 의미: YAML, JSON 등 임의의 설정 파일이나 외부 데이터 소스에서 읽어들인 값의 타입을
    키의 타입 접미사 명명 규칙에 기반하여 검증 및 강제 변환(Coercion & Guarantee)합니다.
    [Fail-Fast 정책 준수] 접미사 규격과 일치하지 않는 유효하지 않은 값이 들어올 경우 침묵하며 원본을 반환하지 않고,
    logger.exception()을 호출하여 에러를 기록하고 안내 메시지와 함께 예외(ValueError/TypeError)를 발생시켜 빠른 실패(Fail-Fast)를 유도합니다.

    :param key_str: 설정 키 문자열
    :param val_any: 변환할 원본 값
    :return: 변환 및 보증된 파이썬 타입 값 (None 유입 시 None 반환)
    :raises ValueError: 정수(_int), 실수(_float), 불리언(_bool) 형식 변환 불가 시 발생
    :raises TypeError: 부적합한 타입(정수/실수에 복합타입, _bool에 비지원타입, _dict에 비매핑타입) 유입 시 발생
    """
    if val_any is None:
        return None

    if key_str.endswith("_int"):
        try:
            return int(val_any)
        except Exception as err:
            ErrorHandler.raise_coercion_error(
                key_str=key_str,
                val_any=val_any,
                expected_type_str="정수형(int)",
                guide_msg_str="정수형 값으로 입력해 주십시오.",
                cause_exc=err,
            )

    if key_str.endswith("_float"):
        try:
            return float(val_any)
        except Exception as err:
            ErrorHandler.raise_coercion_error(
                key_str=key_str,
                val_any=val_any,
                expected_type_str="실수형(float)",
                guide_msg_str="올바른 숫자형 값으로 입력해 주십시오.",
                cause_exc=err,
            )

    if key_str.endswith("_bool"):
        if isinstance(val_any, bool):
            return val_any
        if isinstance(val_any, str):
            # 대소문자 무관(Case-insensitive): 'true', 'TRUE', 'True' -> True / 'false', 'FALSE', 'False' -> False
            clean_str: str = val_any.strip().lower()
            if clean_str == "true":
                return True
            if clean_str == "false":
                return False
            ErrorHandler.raise_coercion_error(
                key_str=key_str,
                val_any=val_any,
                expected_type_str="불리언(bool)",
                guide_msg_str="True 또는 False 값으로 입력해 주십시오.",
                exc_cls=ValueError,
            )
        ErrorHandler.raise_coercion_error(
            key_str=key_str,
            val_any=val_any,
            expected_type_str="불리언(bool)",
            guide_msg_str="True 또는 False 값으로 입력해 주십시오.",
            exc_cls=TypeError,
        )

    if key_str.endswith("_str"):
        return str(val_any).strip()

    if key_str.endswith("_list"):
        if isinstance(val_any, list):
            return val_any
        if isinstance(val_any, (tuple, set)):
            return list(val_any)
        return [val_any]

    if key_str.endswith("_dict"):
        if isinstance(val_any, dict):
            return val_any
        if hasattr(val_any, "to_dict") and callable(val_any.to_dict):
            return val_any.to_dict()
        ErrorHandler.raise_coercion_error(
            key_str=key_str,
            val_any=val_any,
            expected_type_str="딕셔너리(dict)",
            guide_msg_str="딕셔너리 매핑 구조로 입력해 주십시오.",
            exc_cls=TypeError,
        )

    return val_any


def coerce_dict_by_key_suffix(data_dict: dict[str, Any]) -> dict[str, Any]:
    """딕셔너리 내부의 모든 키에 대해 키 접미사 규칙을 재귀적으로 적용하여 보증된 타입으로 일괄 변환한 새 딕셔너리를 반환합니다.

    도메인 의미: 외부 설정 파일(YAML, JSON)을 파싱한 원본 딕셔너리 전체의 타입 무결성을 한 번에 보증합니다.

    :param data_dict: 변환 대상 원본 딕셔너리
    :return: 타입 자동 보증이 적용된 신규 딕셔너리
    """
    if not isinstance(data_dict, dict):
        return data_dict

    result_dict: dict[str, Any] = {}
    for key_str, val_any in data_dict.items():
        if isinstance(val_any, dict):
            result_dict[key_str] = coerce_dict_by_key_suffix(val_any)
        elif isinstance(val_any, list):
            result_dict[key_str] = [
                coerce_dict_by_key_suffix(item_any) if isinstance(item_any, dict) else item_any
                for item_any in val_any
            ]
        else:
            result_dict[key_str] = coerce_type_by_key_suffix(key_str, val_any)
    return result_dict


class ReadOnlyConfig:
    """YAML 설정 딕셔너리 또는 ConfigLoader를 감싸서 점 표기법(Dot-notation, 속성 접근) 및 불변성(Read-Only)을 제공하는 설정 래퍼 클래스입니다.

    도메인 의미: config.ecs.endpoint_url, config.transfer.max_workers 형태로
    설정값을 직관적으로 조회할 수 있으며, 런타임에 설정값이 임의로 변조되는 것을 방지합니다.
    config.yml 뿐만 아니라 임의의 설정 파일(예: rule.yml, mapping.yml) 딕셔너리도 래핑하여 활용할 수 있습니다.
    """

    coerce_type_by_key_suffix = staticmethod(coerce_type_by_key_suffix)
    _coerce_type_by_key_suffix = staticmethod(coerce_type_by_key_suffix)

    def __init__(self, data_or_loader: dict[str, Any] | Any, source_name_str: str = "config.yml") -> None:
        """딕셔너리 데이터 또는 ConfigLoader 인스턴스를 기반으로 ReadOnlyConfig 인스턴스를 초기화합니다.

        :param data_or_loader: 딕셔너리 데이터 또는 ConfigLoader 인스턴스
        :param source_name_str: 설정 소스 식별자 또는 파일명 (기본값: 'config.yml')
        """
        object.__setattr__(self, "_source", data_or_loader)
        object.__setattr__(self, "_source_name_str", source_name_str)

    def _get_data(self) -> dict[str, Any]:
        """현재 연결된 데이터 소스로부터 최신 딕셔너리를 반환합니다."""
        src: Any = object.__getattribute__(self, "_source")
        if isinstance(src, dict):
            return src
        if hasattr(src, "get_settings") and callable(src.get_settings):
            return src.get_settings()
        return {}

    def __getattr__(self, key_str: str) -> Any:
        """점 표기법(속성)으로 설정값을 조회하며 하위 딕셔너리는 ReadOnlyConfig로 자동 래핑합니다.
        
        설정 키 접미사(_int, _str, _bool, _float, _list, _dict)에 맞춰 타입을 자동 보증하여 반환합니다.
        """
        data: dict[str, Any] = self._get_data()
        if key_str not in data:
            source_name_str: str = object.__getattribute__(self, "_source_name_str")
            raise AttributeError(f"{source_name_str}에 정의되지 않은 설정 항목입니다: '{key_str}'")
        val_any = data[key_str]
        source_name_str = object.__getattribute__(self, "_source_name_str")
        if isinstance(val_any, dict):
            return ReadOnlyConfig(val_any, source_name_str=source_name_str)
        if isinstance(val_any, list):
            return [ReadOnlyConfig(item, source_name_str=source_name_str) if isinstance(item, dict) else item for item in val_any]
        return coerce_type_by_key_suffix(key_str, val_any)

    def __getitem__(self, key_str: str) -> Any:
        """딕셔너리 키 인덱싱 표기법(config['ecs'])으로 조회합니다."""
        return self.__getattr__(key_str)

    def __contains__(self, key_str: str) -> bool:
        """설정 키 존재 여부(in 연산자)를 확인합니다."""
        data: dict[str, Any] = self._get_data()
        return key_str in data

    def __setattr__(self, key_str: str, value_any: Any) -> None:
        """설정값 임의 수정을 차단합니다 (불변성 유지)."""
        raise TypeError("config 설정값은 런타임에 수정할 수 없습니다 (Read-Only).")

    def __setitem__(self, key_str: str, value_any: Any) -> None:
        """설정값 임의 수정을 차단합니다 (불변성 유지)."""
        raise TypeError("config 설정값은 런타임에 수정할 수 없습니다 (Read-Only).")

    def __delattr__(self, key_str: str) -> None:
        """설정값 임의 삭제를 차단합니다 (불변성 유지)."""
        raise TypeError("config 설정값은 런타임에 삭제할 수 없습니다 (Read-Only).")

    def __delitem__(self, key_str: str) -> None:
        """설정값 임의 삭제를 차단합니다 (불변성 유지)."""
        raise TypeError("config 설정값은 런타임에 삭제할 수 없습니다 (Read-Only).")

    def to_dict(self) -> dict[str, Any]:
        """내부 원본 딕셔너리를 반환합니다."""
        return self._get_data()

    def __repr__(self) -> str:
        """객체 문자열 표현을 반환합니다."""
        data: dict[str, Any] = self._get_data()
        return f"ReadOnlyConfig({data!r})"

    def __str__(self) -> str:
        """객체 문자열 표현을 반환합니다."""
        data: dict[str, Any] = self._get_data()
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

    # 전역 런타임 언어 강제 설정값 ('KO' 또는 'EN')
    _global_language_override_str: Optional[str] = None

    def __init__(self, config_dir: str | Path | None = None):
        """ConfigLoader 인스턴스를 생성하고 self.logger 및 설정 디렉토리를 초기화합니다."""
        from agent_common.logger import ProjectLogger

        self._config_dir: Path = self.project_path(config_dir) if config_dir else self.ROOT / "config"
        self.logger: ProjectLogger = ProjectLogger(f"agent_common.{self.__class__.__name__}")
        self._registered_schemas: dict[str, Any] = {}
        self._cached_lang_str: Optional[str] = None

    @classmethod
    def set_language(cls, lang_str: str) -> None:
        """전역 로그 메시지 언어를 'KO' 또는 'EN'으로 설정합니다.

        :param lang_str: 설정할 언어 코드 ('KO' 또는 'EN', 대소문자 무관)
        """
        clean_lang_str: str = str(lang_str).strip().upper()
        cls._global_language_override_str = "EN" if clean_lang_str == "EN" else "KO"

    @property
    def language(self) -> str:
        """현재 적용 중인 로그 메시지 언어 코드 ('KO' 또는 'EN')를 반환합니다 (Getter)."""
        settings_dict: dict[str, Any] = self.get_settings()
        return str(settings_dict.get("logging", {}).get("language", "KO")).upper()

    @language.setter
    def language(self, lang_str: str) -> None:
        """로그 메시지 언어 코드를 동적으로 설정합니다 (Setter).

        :param lang_str: 설정할 언어 코드 ('KO' 또는 'EN', 대소문자 무관)
        """
        self.set_language(lang_str)
        self._cached_settings = None

    def config_dir_set(self, config_dir: str | Path) -> None:
        """설정 디렉토리 경로를 세팅하고 설정값 캐시를 초기화합니다 (Setter)."""
        self._config_dir = self.project_path(config_dir)
        self._cached_settings: dict[str, Any] | None = None

    @property
    def config_dir(self) -> Path:
        """설정 디렉토리 경로 프로퍼티 (Getter)."""
        return self._config_dir

    @config_dir.setter
    def config_dir(self, config_dir: str | Path) -> None:
        """설정 디렉토리 경로 프로퍼티 (Setter)."""
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

    def _resolve_language(self, settings_dict: dict[str, Any]) -> str:
        """설정 또는 환경 변수로부터 로그 메시지 언어('KO' 또는 'EN')를 결정합니다.

        :param settings_dict: 현재 로드된 설정 딕셔너리
        :return: 정규화된 언어 코드 ('KO' 또는 'EN')
        """
        if self._global_language_override_str:
            return self._global_language_override_str
        env_lang_str: Optional[str] = os.environ.get("AGENT_LOG_LANGUAGE") or os.environ.get("LOGGING_LANGUAGE")
        if env_lang_str:
            return "EN" if env_lang_str.strip().upper() == "EN" else "KO"
        logging_sec = settings_dict.get("logging")
        if isinstance(logging_sec, dict):
            cfg_lang_str = logging_sec.get("language") or logging_sec.get("lang")
            if cfg_lang_str:
                return "EN" if str(cfg_lang_str).strip().upper() == "EN" else "KO"
        return "KO"

    def _resolve_logging_messages_file(self, config_dir_path: Path, lang_str: str) -> Optional[Path]:
        """지정된 디렉토리에서 언어에 부합하는 logging_messages_*.yml 파일을 탐색합니다.

        :param config_dir_path: 탐색할 디렉토리 Path 객체
        :param lang_str: 언어 코드 ('KO' 또는 'EN')
        :return: 발견된 템플릿 파일 Path 객체 (미발견 시 None)
        """
        suffix_str: str = lang_str.lower()
        target_path: Path = config_dir_path / f"logging_messages_{suffix_str}.yml"
        if target_path.exists():
            return target_path
        target_yaml_path: Path = config_dir_path / f"logging_messages_{suffix_str}.yaml"
        if target_yaml_path.exists():
            return target_yaml_path
        fallback_path: Path = config_dir_path / "logging_messages.yml"
        if fallback_path.exists():
            return fallback_path
        fallback_yaml_path: Path = config_dir_path / "logging_messages.yaml"
        if fallback_yaml_path.exists():
            return fallback_yaml_path
        return None

    def _resolve_project_logging_messages_file(self, project_files_list: list[Path], lang_str: str) -> Optional[Path]:
        """프로젝트의 logging_messages 파일 목록에서 언어에 부합하는 파일을 선택합니다.

        :param project_files_list: 프로젝트 config 디렉토리 내 logging_messages 관련 파일 리스트
        :param lang_str: 언어 코드 ('KO' 또는 'EN')
        :return: 선택된 파일 Path 객체 (미발견 시 None)
        """
        suffix_str: str = lang_str.lower()
        for p in project_files_list:
            if p.name.lower() in (f"logging_messages_{suffix_str}.yml", f"logging_messages_{suffix_str}.yaml"):
                return p
        for p in project_files_list:
            if p.name.lower() in ("logging_messages.yml", "logging_messages.yaml"):
                return p
        return None

    def get_settings(self) -> dict[str, Any]:
        """설정 디렉토리 하위의 모든 YAML 설정 파일을 알파벳 순서로 병합하여 반환한다.
        
        1차: agent_common 패키지 내부 기본 설정 (agent_common/config)
        2차: 등록된 도메인 스키마 기본값 (register_schema)
        3차: 개별 프로젝트 config 디렉토리의 YAML 파일들 (Deep Merge Override)
        4차: 언어(KO/EN)에 대응하는 logging_messages 템플릿 사전 병합
        """
        if getattr(self, "_cached_settings", None) is not None:
            expected_lang_str: str = self._resolve_language(self._cached_settings)  # type: ignore
            if getattr(self, "_cached_lang_str", None) == expected_lang_str:
                return self._cached_settings  # type: ignore

        settings: dict[str, Any] = {}
        loaded_files: list[str] = []
        
        # 1. agent_common 패키지 내부 기본 설정 로드 (agent_common/config)
        # 단, logging_messages_*.yml 파일은 언어 판별 후 4차에서 선택 병합
        common_config_dir: Path = self.PACKAGE_DIR / "config"
        if common_config_dir.exists():
            for path in sorted(common_config_dir.glob("*.yml")):
                if path.name.startswith("logging_messages"):
                    continue
                mapping = self._load_yaml_mapping(path)
                self._deep_merge(settings, mapping)

        # 2. 등록된 도메인 스키마 기본값 병합
        if self._registered_schemas:
            self._deep_merge(settings, self._registered_schemas)
                
        # 3. 호출 프로젝트 고유 설정 로드 및 오버라이드 (.yml 및 .yaml 확장자 모두 탐색)
        project_logging_msg_files: list[Path] = []
        if self.config_dir.exists():
            yml_files = sorted(set(list(self.config_dir.glob("*.yml")) + list(self.config_dir.glob("*.yaml"))))
            for path in yml_files:
                if path.name.startswith("logging_messages"):
                    project_logging_msg_files.append(path)
                    continue
                mapping = self._load_yaml_mapping(path)
                loaded_files.append(f"{path.name}:{list(mapping.keys())}")
                self._deep_merge(settings, mapping)

        # 4. 언어 판별 (KO 또는 EN, 기본값: KO)
        selected_lang_str: str = self._resolve_language(settings)
        if "logging" not in settings or not isinstance(settings["logging"], dict):
            settings["logging"] = {}
        settings["logging"]["language"] = selected_lang_str

        # 5. 선택된 언어에 부합하는 logging_messages 템플릿 사전 병합
        # 5-1. agent_common 패키지 기본 템플릿 로드
        base_msg_file = self._resolve_logging_messages_file(common_config_dir, selected_lang_str)
        if base_msg_file and base_msg_file.exists():
            base_mapping = self._load_yaml_mapping(base_msg_file)
            self._deep_merge(settings, base_mapping)
            loaded_files.append(f"{base_msg_file.name}:{list(base_mapping.keys())}")

        # 5-2. 프로젝트 고유 logging_messages 템플릿 오버라이드 (해당 언어 우선 매핑)
        if project_logging_msg_files:
            proj_msg_file = self._resolve_project_logging_messages_file(project_logging_msg_files, selected_lang_str)
            if proj_msg_file and proj_msg_file.exists():
                proj_mapping = self._load_yaml_mapping(proj_msg_file)
                self._deep_merge(settings, proj_mapping)
                loaded_files.append(f"{proj_msg_file.name}:{list(proj_mapping.keys())}")

        self._loaded_files_summary: str = ", ".join(loaded_files) if loaded_files else "읽어들인 YAML 파일 없음"

        # 6. proxy, no_proxy 설정을 NO_PROXY 환경 변수로 적용한다.
        self._apply_no_proxy(settings)

        self._cached_settings = settings
        self._cached_lang_str = selected_lang_str
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
        점 표기법 경로(예: 'api.port', 'database.port_int')를 사용해 병합된 설정값을 조회합니다.
        설정 키 접미사(_int, _str, _bool, _float, _list, _dict)에 맞춰 타입을 자동 보증하여 반환합니다.

        :param path: 점 표기법 설정 경로 문자열
        :param default: 설정값이 없거나 유효하지 않을 때 반환할 기본 fallback 값 (기본값: None)
        :return: 조회된 설정값 또는 기본값
        """
        current: Any = self.get_settings()
        for key in path.split("."):
            if not isinstance(current, dict) or key not in current:
                if not path.startswith("logging_messages"):
                    self.logger.warning("config_default_fallback", key=path, default_val=default)
                return default
            current = current[key]
        last_key_str: str = path.split(".")[-1]
        return coerce_type_by_key_suffix(last_key_str, current)

    def require_setting(
        self, 
        path: str, 
        message: str = "", 
        config_file: str | Path | None = None
    ) -> Any:
        """
        [Fail-Fast 정책 준수]
        프로그램 기동에 필요한 필수 설정값을 점 표기법(예: 'schema_config.pk_key')으로 조회합니다.
        설정값이 누락되어 있거나 빈 값인 경우, 명시된 설정 파일명과 함께 오류 메시지를 CLI 및 로그로 출력하고
        프로세스를 즉시 강제 종료(sys.exit(1))하여 빠른 실패(Fail-Fast)를 유도합니다.
        설정 키 접미사(_int, _str, _bool, _float, _list, _dict)에 맞춰 타입을 자동 보증하여 반환합니다.

        :param path: 점 표기법 필수 설정 경로 (예: 'schema_config.pk_key')
        :param message: 설정값 누락 시 추가 안내 설명 메시지 (옵션)
        :param config_file: 특정 설정 파일 경로 (미지정 시 기본 config_dir 설정 전체 사용)
        :return: 설정 파일에 정의된 필수 설정값
        """
        # 1. 파일 경로 정규화 및 데이터 로드 격리
        if config_file is None:
            target_path = self.config_dir / "config.yml"
            data: Any = self.get_settings()
            raw_keys = list(data.keys()) if isinstance(data, dict) else []
        else:
            cfg_path = Path(config_file)
            target_path = cfg_path if cfg_path.is_absolute() else self.project_path(cfg_path)
            
            if not target_path.exists():
                data = None
                raw_keys = []
            else:
                try:
                    data = self._load_yaml_mapping(target_path)
                    raw_keys = list(data.keys()) if isinstance(data, dict) else []
                except Exception as read_err:
                    data = None
                    raw_keys = []
                    message = f"{message} (파일 해석 오류: {read_err})" if message else f"파일 해석 오류: {read_err}"

        # 2. 점(.) 표기법 경로 탐색
        current: Any = data
        if isinstance(current, dict):
            for key in path.split("."):
                if not isinstance(current, dict) or key not in current:
                    current = None
                    break
                current = current[key]
        else:
            current = None

        # 3. 누락 시 Fail-Fast 처리
        if current is None or (isinstance(current, str) and not current.strip()):
            desc_info = f" ({message})" if message else ""
            exists_status = "파일 존재함" if target_path.exists() else "파일 없음"
            full_cfg_info = f"{target_path} [{exists_status}] (조회된 파일 키: {raw_keys})"

            err_msg = self.logger.critical(
                "fail_fast_config_missing",
                path=path,
                desc_info=desc_info,
                config_file=full_cfg_info
            )
            print(err_msg, file=sys.stderr)

            sys.exit(1)

        last_key_str: str = path.split(".")[-1]
        return coerce_type_by_key_suffix(last_key_str, current)

    def project_path(self, path: str | Path | None = None) -> Path:
        """
        프로젝트 루트를 기준으로 한 상대 경로를 절대 경로로 변환하여 반환합니다.
        (path 미지정 시 프로젝트 루트 ROOT 경로 반환)

        :param path: 절대 경로 또는 프로젝트 루트 기준 상대 경로 (선택)
        :return: 정규화된 절대 Path 객체
        """
        if path is None or path == "":
            return self.ROOT
        value = Path(path)
        if value.is_absolute():
            return value
        return self.ROOT / value

    @staticmethod
    def _load_yaml_mapping(path: Path) -> dict[str, Any]:
        """
        지정된 YAML 파일을 해석하여 최상위 매핑 딕셔너리로 읽어들입니다 (UTF-8 / BOM 지원).

        :param path: 해석할 대상 YAML 파일 절대 경로
        :return: 해석된 딕셔너리 객체
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

# 전역에서 바로 import 하여 점 표기법(config.ecs.endpoint_url)으로 쓸 수 있는 읽기 전용 설정 객체
config: ReadOnlyConfig = ReadOnlyConfig(ConfigLoader())

