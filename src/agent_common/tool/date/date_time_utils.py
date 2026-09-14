# 작성일: 2026-08-21
# 설계자: 김유상 수석
# 설계자 이메일: bakkus@daum.net

"""
표준화된 날짜, 시간 규격 포맷팅 및 타임스탬프 생성을 전담하는 agent_common 내장 Tool 클래스 모듈입니다.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional


class DateTimeUtils:
    """
    날짜 및 시간 규격을 표준화하여 제공하는 공용 유틸리티 Tool 클래스입니다.
    기본 타임존으로 한국 표준시(KST, UTC+9)를 적용하여 실행 환경(OS 타임존) 간 불일치를 방지합니다.
    """

    FORMAT_DATE_YYYYMMDD_STR: str = "%Y%m%d"
    FORMAT_DATETIME_STD_STR: str = "%Y-%m-%d %H:%M:%S+09:00"
    FORMAT_DATETIME_NO_TZ_STR: str = "%Y-%m-%d %H:%M:%S"
    FORMAT_DATETIME_KST_STR: str = "%Y-%m-%d %H:%M:%S+09:00"
    FORMAT_DATETIME_COMPACT_STR: str = "%Y%m%d%H%M%S"

    DEFAULT_TIMEZONE_OFFSET_HOURS_INT: int = 9
    DEFAULT_TIMEZONE_OBJ: timezone = timezone(timedelta(hours=9))

    @classmethod
    def get_now_datetime(cls, tz_obj: Optional[timezone] = None) -> datetime:
        """
        현재 시각을 지정된 타임존(기본값: KST, UTC+9)이 적용된 timezone-aware datetime 객체로 반환합니다.

        :param tz_obj: 적용할 timezone 객체 (미지정 시 KST 적용)
        :return: 타임존이 적용된 현재 datetime 객체
        """
        effective_tz_obj: timezone = tz_obj if tz_obj is not None else cls.DEFAULT_TIMEZONE_OBJ
        return datetime.now(effective_tz_obj)

    @classmethod
    def get_today_yyyymmdd(cls, tz_obj: Optional[timezone] = None) -> str:
        """
        지정된 타임존(기본값: KST) 기준의 현재 일자를 YYYYMMDD 형식의 8자리 문자열로 반환합니다.

        :param tz_obj: 적용할 timezone 객체 (미지정 시 KST 적용)
        :return: 'YYYYMMDD' 형식의 당일 날짜 문자열 (예: '20260821')
        """
        target_datetime_obj: datetime = cls.get_now_datetime(tz_obj=tz_obj)
        return target_datetime_obj.strftime(cls.FORMAT_DATE_YYYYMMDD_STR)

    @classmethod
    def get_now_formatted(cls, fmt_str: Optional[str] = None, tz_obj: Optional[timezone] = None) -> str:
        """
        지정된 타임존(기본값: KST) 기준의 현재 일시를 포맷팅된 문자열로 반환합니다.
        포맷을 미지정하거나 기본 표준 포맷(FORMAT_DATETIME_STD_STR 또는 FORMAT_DATETIME_KST_STR)인 경우
        정확한 타임존 오프셋(+09:00 등)을 동적으로 결합하여 반환합니다.

        :param fmt_str: 사용할 strftime 포맷 문자열 (기본값: '%Y-%m-%d %H:%M:%S+09:00')
        :param tz_obj: 적용할 timezone 객체 (미지정 시 KST 적용)
        :return: 포맷팅된 현재 일시 문자열 (예: '2026-08-21 13:10:00+09:00')
        """
        target_datetime_obj: datetime = cls.get_now_datetime(tz_obj=tz_obj)

        if fmt_str == cls.FORMAT_DATETIME_NO_TZ_STR:
            return target_datetime_obj.strftime(cls.FORMAT_DATETIME_NO_TZ_STR)

        if fmt_str is None or fmt_str in (cls.FORMAT_DATETIME_STD_STR, cls.FORMAT_DATETIME_KST_STR):
            offset_raw_str: str = target_datetime_obj.strftime("%z")
            formatted_offset_str: str = f"{offset_raw_str[:3]}:{offset_raw_str[3:]}" if len(offset_raw_str) == 5 else "+09:00"
            date_time_part_str: str = target_datetime_obj.strftime(cls.FORMAT_DATETIME_NO_TZ_STR)
            return f"{date_time_part_str}{formatted_offset_str}"

        return target_datetime_obj.strftime(fmt_str)

    @classmethod
    def get_now_compact(cls, tz_obj: Optional[timezone] = None) -> str:
        """
        지정된 타임존(기본값: KST) 기준의 현재 일시를 14자리 압축 형식(YYYYMMDDHHMMSS) 문자열로 반환합니다.

        :param tz_obj: 적용할 timezone 객체 (미지정 시 KST 적용)
        :return: 'YYYYMMDDHHMMSS' 형식의 타임스탬프 문자열 (예: '20260821131000')
        """
        target_datetime_obj: datetime = cls.get_now_datetime(tz_obj=tz_obj)
        return target_datetime_obj.strftime(cls.FORMAT_DATETIME_COMPACT_STR)
