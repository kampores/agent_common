# 작성일: 2026-08-16
# 설계자: 경포씨엔씨
# 설계자 소속: 김유상
# 설계자 이메일: bakkus@kpcnc.co.kr, bakkus@daum.net

"""
프로젝트 전역에서 공통으로 사용하는 날짜, 시간, 문자열 포맷팅 및 표준 규격 유틸리티 모듈입니다.
"""

from __future__ import annotations

import time
from typing import Optional


class DateTimeUtils:
    """
    날짜 및 시간 규격을 표준화하여 제공하는 공용 유틸리티 클래스입니다.
    """

    FORMAT_DATE_YYYYMMDD: str = "%Y%m%d"
    FORMAT_DATETIME_STD: str = "%Y-%m-%d %H:%M:%S"
    FORMAT_DATETIME_COMPACT: str = "%Y%m%d%H%M%S"

    @classmethod
    def get_today_yyyymmdd(cls) -> str:
        """
        현재 일자를 YYYYMMDD 형식의 8자리 문자열로 반환합니다.

        :return: 'YYYYMMDD' 형식의 당일 날짜 문자열 (예: '20260816')
        """
        return time.strftime(cls.FORMAT_DATE_YYYYMMDD)

    @classmethod
    def get_now_formatted(cls, fmt_str: Optional[str] = None) -> str:
        """
        현재 일시를 표준 형식(기본값: YYYY-MM-DD HH:MM:SS) 문자열로 반환합니다.

        :param fmt_str: 사용할 strftime 포맷 문자열 (기본값: '%Y-%m-%d %H:%M:%S')
        :return: 포맷팅된 현재 일시 문자열 (예: '2026-08-16 22:15:00')
        """
        target_fmt_str: str = fmt_str or cls.FORMAT_DATETIME_STD
        return time.strftime(target_fmt_str)

    @classmethod
    def get_now_compact(cls) -> str:
        """
        현재 일시를 14자리 압축 형식(YYYYMMDDHHMMSS) 문자열로 반환합니다.

        :return: 'YYYYMMDDHHMMSS' 형식의 타임스탬프 문자열
        """
        return time.strftime(cls.FORMAT_DATETIME_COMPACT)
