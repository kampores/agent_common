# 작성일: 2026-08-16
# 설계자: 김유상 수석
# 설계자 소속: 경포씨엔씨
# 설계자 이메일: bakkus@kpcnc.co.kr, bakkus@daum.net

"""
호스트 시스템(OS/컨테이너) 로컬 타임존 동적 감지, 환경변수 설정 타임존,
그리고 전 세계 표준 타임존 해석 및 datetime 객체 생성을 전담하는 코어 시간 인프라 유틸리티 모듈입니다.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from typing import Any, Optional


class TimeUtils:
    """
    호스트 시스템(OS/컨테이너) 로컬 타임존 동적 감지, 환경변수 설정 타임존,
    그리고 전 세계 표준 타임존 해석 및 datetime 객체 생성을 전담하는 코어 시간 인프라 유틸리티 클래스입니다.
    """

    # 전 세계 주요 표준 타임존 약어 및 UTC 기준 오프셋 시간 매핑 딕셔너리
    WORLD_TIMEZONE_OFFSETS_DICT: dict[str, int | float] = {
        # UTC 및 표준시
        "UTC": 0,
        "GMT": 0,
        "Z": 0,
        # 아시아 / 태평양
        "KST": 9,        # 한국 표준시 (UTC+9)
        "JST": 9,        # 일본 표준시 (UTC+9)
        "CST_ASIA": 8,   # 중국 표준시 (UTC+8, 베이징/상하이)
        "HKT": 8,        # 홍콩 표준시 (UTC+8)
        "SGT": 8,        # 싱가포르 표준시 (UTC+8)
        "IST": 5.5,      # 인도 표준시 (UTC+5:30)
        "ICT": 7,        # 인도차이나 표준시 (UTC+7, 방콕/하노이)
        "AEST": 10,      # 호주 동부 표준시 (UTC+10)
        "AEDT": 11,      # 호주 동부 서머타임 (UTC+11)
        "ACST": 9.5,     # 호주 중부 표준시 (UTC+9:30)
        "ACDT": 10.5,    # 호주 중부 서머타임 (UTC+10:30)
        "AWST": 8,       # 호주 서부 표준시 (UTC+8)
        "NZST": 12,      # 뉴질랜드 표준시 (UTC+12)
        "NZDT": 13,      # 뉴질랜드 서머타임 (UTC+13)
        # 유럽
        "CET": 1,        # 중앙유럽 표준시 (UTC+1)
        "CEST": 2,       # 중앙유럽 서머타임 (UTC+2)
        "WET": 0,        # 서유럽 표준시 (UTC+0)
        "WEST": 1,       # 서유럽 서머타임 (UTC+1)
        "EET": 2,        # 동유럽 표준시 (UTC+2)
        "EEST": 3,       # 동유럽 서머타임 (UTC+3)
        "BST": 1,        # 영국 서머타임 (UTC+1)
        "MSK": 3,        # 모스크바 표준시 (UTC+3)
        # 북미 (미국 / 캐나다)
        "EST": -5,       # 미국 동부 표준시 (UTC-5)
        "EDT": -4,       # 미국 동부 서머타임 (UTC-4)
        "CST": -6,       # 미국 중부 표준시 (UTC-6)
        "CDT": -5,       # 미국 중부 서머타임 (UTC-5)
        "MST": -7,       # 미국 산악 표준시 (UTC-7)
        "MDT": -6,       # 미국 산악 서머타임 (UTC-6)
        "PST": -8,       # 미국 태평양 표준시 (UTC-8)
        "PDT": -7,       # 미국 태평양 서머타임 (UTC-7)
        "AKST": -9,      # 알래스카 표준시 (UTC-9)
        "AKDT": -8,      # 알래스카 서머타임 (UTC-8)
        "HST": -10,      # 하와이 표준시 (UTC-10)
    }

    @classmethod
    def get_system_timezone(cls) -> timezone:
        """
        현재 코드가 실행 중인 OS/컨테이너 호스트 시스템의 실제 로컬 타임존 객체를 동적으로 감지하여 반환합니다.
        (배치 서버: KST, Airflow 파드: UTC 등 실행 환경에 맞는 실제 로컬 타임존 반영)

        :return: 호스트 시스템 로컬 타임존을 나타내는 timezone 객체 (감지 불가 시 timezone.utc)
        """
        local_datetime_obj: datetime = datetime.now().astimezone()
        local_offset_delta_obj: Optional[timedelta] = local_datetime_obj.utcoffset()
        if local_offset_delta_obj is not None:
            return timezone(local_offset_delta_obj)
        return timezone.utc

    @classmethod
    def get_system_timezone_offset_str(cls) -> str:
        """
        현재 호스트 시스템의 로컬 타임존 오프셋을 ISO 8601 콜론 형식('+09:00', '+00:00', '-05:00' 등)으로 반환합니다.

        :return: ISO 8601 형식의 시스템 타임존 오프셋 문자열
        """
        local_datetime_obj: datetime = datetime.now().astimezone()
        return cls.format_timezone_offset(local_datetime_obj)

    @classmethod
    def resolve_timezone(cls, tz_input_any: Optional[timezone | str | int | float] = None) -> timezone:
        """
        지정된 타임존 입력값(None, timezone 객체, 세계시간 약어 문자열, ISO 오프셋 문자열, 수치형 오프셋)을
        표준 timezone 객체로 해석하여 반환합니다.
        입력값이 None인 경우 업계/플랫폼 표준 환경변수(TZ)를 확인하고,
        환경변수 미지정 시 호스트 시스템의 로컬 타임존(get_system_timezone)을 자동 감지합니다.

        :param tz_input_any: 해석 대상 타임존 (None, timezone, str, int, float)
        :return: 해석 완료된 표준 timezone 객체
        :raises ValueError: 지원하지 않거나 유효하지 않은 타임존 형식 유입 시 발생
        """
        if tz_input_any is None:
            tz_env_str: Optional[str] = os.environ.get("TZ")
            if tz_env_str and tz_env_str.strip():
                return cls.resolve_timezone(tz_env_str.strip())
            return cls.get_system_timezone()

        if isinstance(tz_input_any, timezone):
            return tz_input_any

        if isinstance(tz_input_any, (int, float)):
            hours_int: int = int(tz_input_any)
            minutes_int: int = int(round((tz_input_any - hours_int) * 60))
            return timezone(timedelta(hours=hours_int, minutes=minutes_int))

        if isinstance(tz_input_any, str):
            clean_str: str = tz_input_any.strip()
            upper_str: str = clean_str.upper()

            if upper_str in ("SYSTEM", "LOCAL", "AUTO"):
                return cls.get_system_timezone()

            if upper_str in cls.WORLD_TIMEZONE_OFFSETS_DICT:
                offset_val = cls.WORLD_TIMEZONE_OFFSETS_DICT[upper_str]
                return cls.resolve_timezone(offset_val)

            sign_int: int = -1 if clean_str.startswith("-") else 1
            pure_digits_str: str = clean_str.replace(":", "").lstrip("+-")
            if pure_digits_str.isdigit():
                if len(pure_digits_str) <= 2:
                    return timezone(timedelta(hours=sign_int * int(pure_digits_str)))
                elif len(pure_digits_str) == 4:
                    parsed_hours_int: int = int(pure_digits_str[:2])
                    parsed_minutes_int: int = int(pure_digits_str[2:])
                    return timezone(timedelta(hours=sign_int * parsed_hours_int, minutes=sign_int * parsed_minutes_int))

            raise ValueError(f"유효하지 않은 타임존 오프셋 또는 규격 형식입니다: '{tz_input_any}'")

        raise ValueError(f"지원하지 않는 타임존 입력 타입입니다: {type(tz_input_any)}")

    @classmethod
    def format_timezone_offset(cls, dt_obj: datetime) -> str:
        """
        datetime 객체의 타임존 오프셋을 '+09:00', '-05:00', '+00:00' 형태의 표준 ISO 8601 콜론 구분 문자열로 반환합니다.

        :param dt_obj: 타임존 오프셋을 추출할 datetime 객체
        :return: '+HH:MM' 또는 '-HH:MM' 형태의 타임존 오프셋 문자열
        """
        offset_raw_str: str = dt_obj.strftime("%z")
        if len(offset_raw_str) == 5 and offset_raw_str[0] in "+-":
            return f"{offset_raw_str[:3]}:{offset_raw_str[3:]}"
        return "+00:00"

    @classmethod
    def parse_datetime(cls, dt_input_any: Any, default_tz_obj: Optional[timezone] = None) -> Optional[datetime]:
        """
        다양한 형태(datetime 객체, ISO 8601 일시 문자열, naive/aware 등)의 일시 값을 표준 비교 및 연산이 가능한
        timezone-aware datetime 객체로 정규화하여 반환합니다.
        문자열 끝의 'Z'는 '+00:00'(UTC)으로 변환되며, 타임존 오프셋이 누락된 naive datetime의 경우
        지정된 default_tz_obj(미지정 시 cls.resolve_timezone() 기본 타임존)를 부여합니다.

        :param dt_input_any: 파싱 및 정규화할 일시 객체 또는 문자열 (None 시 None 반환)
        :param default_tz_obj: naive datetime에 적용할 기본 timezone 객체 (미지정 시 자동 감지)
        :return: 정규화된 timezone-aware datetime 객체 (변환 실패 또는 빈 값일 경우 None)
        :raises None: 파싱 중 발생하는 형식 오류는 None으로 안전하게 처리
        """
        if dt_input_any is None:
            return None

        effective_tz_obj: timezone = default_tz_obj if default_tz_obj is not None else cls.resolve_timezone()

        if isinstance(dt_input_any, datetime):
            if dt_input_any.tzinfo is not None:
                return dt_input_any
            return dt_input_any.replace(tzinfo=effective_tz_obj)

        dt_str: str = str(dt_input_any).strip()
        if not dt_str or dt_str.lower() in ("none", "null", ""):
            return None

        clean_dt_str: str = dt_str.replace("Z", "+00:00")
        try:
            parsed_dt_obj: datetime = datetime.fromisoformat(clean_dt_str)
            if parsed_dt_obj.tzinfo is None:
                parsed_dt_obj = parsed_dt_obj.replace(tzinfo=effective_tz_obj)
            return parsed_dt_obj
        except (ValueError, TypeError):
            return None


__all__ = [
    "TimeUtils",
]
