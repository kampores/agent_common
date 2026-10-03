# 작성일: 2026-10-04
# 설계자: 김유상 수석
# 설계자 소속: 경포씨엔씨
# 설계자 이메일: bakkus@kpcnc.co.kr, bakkus@daum.net

"""
다국어 언어 설정(Language Localization) 및 언어별 리소스 파일 경로 탐색을 전담하는 로컬라이저 모듈입니다.
로깅 레벨, 메시지 포매팅 등 로깅 고유 로직과 명확히 분리하여, 언어 코드 정규화,
전역 언어 설정 관리, 언어별 리소스 파일 경로 탐색 책임을 단일 책임 원칙(SRP)에 따라 전담합니다.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional


class Localizer:
    """
    다국어 언어 코드 정규화, 전역 언어 설정 관리, 언어별 리소스 파일 경로 탐색을
    전담하는 중앙 언어 로컬라이저 클래스입니다.
    """

    DEFAULT_LANGUAGE_STR: str = "KR"
    SUPPORTED_LANGUAGES_LIST: list[str] = ["KR", "EN", "ZH", "JP"]
    LANGUAGE_ALIAS_DICT: dict[str, str] = {
        "KR": "KR",
        "KO": "KR",
        "KOR": "KR",
        "KOREAN": "KR",
        "EN": "EN",
        "ENG": "EN",
        "ENGLISH": "EN",
        "US": "EN",
        "ZH": "ZH",
        "CN": "ZH",
        "CHI": "ZH",
        "CHINESE": "ZH",
        "JP": "JP",
        "JA": "JP",
        "JPN": "JP",
        "JAPANESE": "JP",
    }

    _global_language_override_str: Optional[str] = None

    def __init__(self, language_str: str = "KR") -> None:
        """
        Localizer 인스턴스를 초기화합니다.

        :param language_str: 기본 적용 언어 코드 문자열 (기본값: 'KR')
        """
        self.language_str: str = self.normalize_language(language_str)

    @classmethod
    def set_global_language(cls, language_str: str) -> None:
        """
        프로세스 전역 언어 오버라이드 설정을 지정합니다.

        :param language_str: 설정할 언어 코드 문자열
        :return: None
        """
        cls._global_language_override_str = cls.normalize_language(language_str)

    @classmethod
    def get_global_language(cls) -> Optional[str]:
        """
        현재 프로세스 전역 언어 오버라이드 설정을 반환합니다.

        :return: 전역 언어 코드 문자열 (미설정 시 None)
        """
        return cls._global_language_override_str

    @classmethod
    def clear_global_language(cls) -> None:
        """
        프로세스 전역 언어 오버라이드 설정을 초기화합니다.

        :return: None
        """
        cls._global_language_override_str = None

    @classmethod
    def normalize_language(cls, language_str: str) -> str:
        """
        입력된 언어 문자열을 공식 표준 언어 코드('KR', 'EN', 'ZH', 'JP')로 정규화합니다.
        'KO'/'KR' -> 'KR', 'JA'/'JP' -> 'JP', 'ZH'/'CN' -> 'ZH', 'EN'/'US' -> 'EN'

        :param language_str: 입력 언어 문자열
        :return: 정규화된 대문자 언어 코드 (미식별 시 기본 언어 'KR' 반환)
        """
        if not language_str:
            return cls.DEFAULT_LANGUAGE_STR
        clean_key_str: str = str(language_str).strip().upper()
        return cls.LANGUAGE_ALIAS_DICT.get(clean_key_str, cls.DEFAULT_LANGUAGE_STR)

    @classmethod
    def resolve_language(
        cls,
        explicit_lang_str: Optional[str] = None,
        default_lang_str: str = "KR",
    ) -> str:
        """
        명시적 오버라이드, 전역 오버라이드, 범용 환경 변수를 평가하여 최종 언어 코드를 결정합니다.
        (로깅 설정과의 결합을 배제한 순수 언어 환경 결정 로직)

        우선순위:
        1. 명시적 인자 (explicit_lang_str)
        2. 전역 오버라이드 (_global_language_override_str)
        3. 범용 환경 변수 (AGENT_LANGUAGE, APP_LANGUAGE, LANGUAGE, LANG)
        4. 기본값 (default_lang_str, 정규화 후 'KR')

        :param explicit_lang_str: 명시적 우선 지정 언어 코드
        :param default_lang_str: 대체 기본 언어 코드 (기본값: 'KR')
        :return: 최종 결정된 정규화 언어 코드 ('KR', 'EN', 'ZH', 'JP')
        """
        if explicit_lang_str:
            return cls.normalize_language(explicit_lang_str)
        if cls._global_language_override_str:
            return cls._global_language_override_str

        for env_key_str in ("AGENT_LANGUAGE", "APP_LANGUAGE", "LANGUAGE", "LANG"):
            env_val_str: Optional[str] = os.environ.get(env_key_str)
            if env_val_str:
                first_part_str: str = env_val_str.split(".")[0].split("_")[0]
                normalized_code_str: str = cls.normalize_language(first_part_str)
                if normalized_code_str in cls.SUPPORTED_LANGUAGES_LIST:
                    return normalized_code_str

        return cls.normalize_language(default_lang_str)

    @classmethod
    def resolve_localized_file(
        cls,
        dir_path: Path,
        prefix_str: str,
        language_str: str,
        extensions_list: Optional[list[str]] = None,
    ) -> Optional[Path]:
        """
        지정된 디렉토리에서 특정 접두사(prefix_str)를 가진 언어별 리소스 파일
        ({prefix}_{lang}.{ext} 등)을 탐색하여 반환합니다.

        :param dir_path: 탐색 대상 디렉토리 Path 객체
        :param prefix_str: 파일명 접두사 (예: 'logging_messages', 'messages', 'labels')
        :param language_str: 대상 언어 코드 문자열
        :param extensions_list: 탐색 대상 확장자 목록 (기본값: ['.yml', '.yaml'])
        :return: 발견된 파일 Path 객체 (미발견 시 None)
        """
        if not dir_path or not dir_path.exists():
            return None

        clean_lang_str: str = cls.normalize_language(language_str).lower()
        exts_list: list[str] = extensions_list or [".yml", ".yaml"]

        # 언어 코드별 호환 대체 접미사 구성 ('kr' <-> 'ko', 'jp' <-> 'ja', 'zh' <-> 'cn')
        lang_candidates_list: list[str] = [clean_lang_str]
        if clean_lang_str == "kr":
            lang_candidates_list.append("ko")
        elif clean_lang_str == "jp":
            lang_candidates_list.append("ja")
        elif clean_lang_str == "zh":
            lang_candidates_list.append("cn")

        default_lang_lower_str: str = cls.DEFAULT_LANGUAGE_STR.lower()
        if default_lang_lower_str not in lang_candidates_list:
            lang_candidates_list.append(default_lang_lower_str)
            if default_lang_lower_str == "kr":
                lang_candidates_list.append("ko")

        # 1. 언어별 파일 탐색 ({prefix}_{lang}.ext)
        for lang_suffix_str in lang_candidates_list:
            for ext_str in exts_list:
                candidate_path: Path = dir_path / f"{prefix_str}_{lang_suffix_str}{ext_str}"
                if candidate_path.exists():
                    return candidate_path

        # 2. 접미사 없는 기본 파일 탐색 ({prefix}.ext)
        for ext_str in exts_list:
            candidate_path: Path = dir_path / f"{prefix_str}{ext_str}"
            if candidate_path.exists():
                return candidate_path

        return None

    @classmethod
    def resolve_localized_path_from_list(
        cls,
        file_paths_list: list[Path],
        prefix_str: str,
        language_str: str,
    ) -> Optional[Path]:
        """
        제공된 파일 Path 목록 중에서 특정 접두사(prefix_str) 및 대상 언어에 부합하는 파일을 선택합니다.

        :param file_paths_list: 탐색 대상 파일 Path 목록
        :param prefix_str: 파일명 접두사 (예: 'logging_messages')
        :param language_str: 대상 언어 코드 문자열
        :return: 선택된 파일 Path 객체 (미발견 시 None)
        """
        clean_lang_str: str = cls.normalize_language(language_str).lower()
        lang_candidates_list: list[str] = [clean_lang_str]
        if clean_lang_str == "kr":
            lang_candidates_list.append("ko")
        elif clean_lang_str == "jp":
            lang_candidates_list.append("ja")
        elif clean_lang_str == "zh":
            lang_candidates_list.append("cn")

        # 1. 언어별 일치 파일 우선 탐색
        target_prefixes_list: list[str] = [f"{prefix_str}_{c}" for c in lang_candidates_list]
        for candidate_prefix_str in target_prefixes_list:
            for file_path in file_paths_list:
                file_stem_lower_str: str = file_path.stem.lower()
                if file_stem_lower_str == candidate_prefix_str:
                    return file_path

        # 2. 기본 언어(KR/KO) 파일 탐색
        default_prefixes_list: list[str] = [
            f"{prefix_str}_{cls.DEFAULT_LANGUAGE_STR.lower()}",
            f"{prefix_str}_ko",
        ]
        for candidate_prefix_str in default_prefixes_list:
            for file_path in file_paths_list:
                if file_path.stem.lower() == candidate_prefix_str:
                    return file_path

        # 3. 접미사 없는 기본 파일 탐색
        for file_path in file_paths_list:
            if file_path.stem.lower() == prefix_str:
                return file_path

        return None

    @classmethod
    def resolve_catalog_file(cls, config_dir_path: Path, language_str: str) -> Optional[Path]:
        """
        (하위 호환 전용) 로깅 메시지 카탈로그 파일 탐색을 일반화된 resolve_localized_file로 위임합니다.

        :param config_dir_path: 탐색할 디렉토리 Path 객체
        :param language_str: 언어 코드 문자열
        :return: 발견된 템플릿 파일 Path 객체 (미발견 시 None)
        """
        return cls.resolve_localized_file(
            dir_path=config_dir_path,
            prefix_str="logging_messages",
            language_str=language_str,
        )

    @classmethod
    def resolve_project_catalog_file(
        cls,
        project_files_list: list[Path],
        language_str: str,
    ) -> Optional[Path]:
        """
        (하위 호환 전용) 프로젝트 파일 목록에서 로깅 메시지 파일 선택을 resolve_localized_path_from_list로 위임합니다.

        :param project_files_list: 프로젝트 config 디렉토리 내 파일 Path 리스트
        :param language_str: 언어 코드 문자열
        :return: 선택된 파일 Path 객체 (미발견 시 None)
        """
        return cls.resolve_localized_path_from_list(
            file_paths_list=project_files_list,
            prefix_str="logging_messages",
            language_str=language_str,
        )
