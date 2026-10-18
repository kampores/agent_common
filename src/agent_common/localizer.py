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

    DEFAULT_LANGUAGE_STR: str = "KO"
    SUPPORTED_LANGUAGES_LIST: list[str] = ["KO", "EN", "ZH", "JA"]
    LANGUAGE_ALIAS_DICT: dict[str, str] = {
        "KO": "KO",
        "KOR": "KO",
        "KOREAN": "KO",
        "EN": "EN",
        "ENG": "EN",
        "ENGLISH": "EN",
        "ZH": "ZH",
        "CHI": "ZH",
        "CHINESE": "ZH",
        "JA": "JA",
        "JPN": "JA",
        "JAPANESE": "JA",
    }

    _global_language_override_str: Optional[str] = None

    def __init__(self, language_str: str = "KO") -> None:
        """
        Localizer 인스턴스를 초기화합니다.

        :param language_str: 기본 적용 언어 코드 문자열 (기본값: 'KO')
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
        입력된 언어 문자열을 ISO 639-1 언어 코드('KO', 'EN', 'ZH', 'JA')로 정규화합니다.
        BCP 47 표준 하이픈('-') 구분 로케일('en-US', 'ko-KR', 'zh-CN', 'ja-JP') 및
        별칭('KOR'/'KOREAN' -> 'KO', 'ENG'/'ENGLISH' -> 'EN', 'CHI'/'CHINESE' -> 'ZH', 'JPN'/'JAPANESE' -> 'JA')을 지원합니다.

        :param language_str: 입력 언어 문자열
        :return: 정규화된 대문자 언어 코드 (미식별 시 기본 언어 'KO' 반환)
        """
        if not language_str:
            return cls.DEFAULT_LANGUAGE_STR
        clean_key_str: str = language_str.strip().upper()
        if clean_key_str in cls.LANGUAGE_ALIAS_DICT:
            return cls.LANGUAGE_ALIAS_DICT[clean_key_str]

        # BCP 47 표준 하이픈('-') 및 로케일 서브태그/인코딩 분리
        primary_tag_str: str = clean_key_str.split(".")[0].split("-")[0].split("_")[0].strip()
        return cls.LANGUAGE_ALIAS_DICT.get(primary_tag_str, cls.DEFAULT_LANGUAGE_STR)

    @classmethod
    def resolve_language(
        cls,
        explicit_lang_str: Optional[str] = None,
        default_lang_str: str = "KO",
    ) -> str:
        """
        명시적 오버라이드, 전역 오버라이드, 범용 환경 변수를 평가하여 최종 언어 코드를 결정합니다.
        (로깅 설정과의 결합을 배제한 순수 언어 환경 결정 로직)

        우선순위:
        1. 명시적 인자 (explicit_lang_str)
        2. 전역 오버라이드 (_global_language_override_str)
        3. 범용 환경 변수 (AGENT_LANGUAGE, APP_LANGUAGE, LANGUAGE, LANG)
        4. 기본값 (default_lang_str, 정규화 후 'KO')

        :param explicit_lang_str: 명시적 우선 지정 언어 코드
        :param default_lang_str: 대체 기본 언어 코드 (기본값: 'KO')
        :return: 최종 결정된 정규화 언어 코드 ('KO', 'EN', 'ZH', 'JA')
        """
        if explicit_lang_str:
            return cls.normalize_language(explicit_lang_str)
        if cls._global_language_override_str:
            return cls._global_language_override_str

        for env_key_str in ("AGENT_LANGUAGE", "APP_LANGUAGE", "LANGUAGE", "LANG"):
            env_val_str: Optional[str] = os.environ.get(env_key_str)
            if env_val_str:
                first_part_str: str = env_val_str.split(".")[0].split("-")[0].split("_")[0].strip().upper()
                if first_part_str in cls.LANGUAGE_ALIAS_DICT:
                    return cls.LANGUAGE_ALIAS_DICT[first_part_str]

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

        exts_set: set[str] = set(extensions_list or [".yml", ".yaml"])
        valid_files_list: list[Path] = [
            file_path for file_path in dir_path.iterdir()
            if file_path.is_file() and file_path.suffix.lower() in exts_set
        ]
        for sub_dir in dir_path.iterdir():
            if sub_dir.is_dir():
                valid_files_list.extend(
                    file_path for file_path in sub_dir.iterdir()
                    if file_path.is_file() and file_path.suffix.lower() in exts_set
                )

        return cls.resolve_localized_path_from_list(
            file_paths_list=valid_files_list,
            prefix_str=prefix_str,
            language_str=language_str,
        )

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

        # 1. 대상 언어 파일 우선 탐색, 2. 기본 언어 파일 탐색 (중복 탐색 방지)
        candidates_tuple: tuple[str, ...] = (
            (f"{prefix_str}_{clean_lang_str}",)
            if clean_lang_str == cls.DEFAULT_LANGUAGE_STR.lower()
            else (f"{prefix_str}_{clean_lang_str}", f"{prefix_str}_{cls.DEFAULT_LANGUAGE_STR.lower()}")
        )
        for candidate_prefix_str in candidates_tuple:
            for file_path in file_paths_list:
                if file_path.stem.lower() == candidate_prefix_str:
                    return file_path

        # 3. 접미사 없는 기본 파일 탐색
        for file_path in file_paths_list:
            if file_path.stem.lower() == prefix_str:
                return file_path

        return None
