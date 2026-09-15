# 작성일: 2026-08-21
# 설계자: 김유상 수석
# 설계자 소속: 경포씨엔씨
# 설계자 이메일: bakkus@kpcnc.co.kr, bakkus@daum.net

"""
테이블 변환 룰(table_rules.yml) 및 템플릿 구문 치환({DateTimeUtils.get_today_yyyymmdd}, {DateTimeUtils.get_now_compact})에서
표준 날짜/시간 문자열 생성을 제공하는 agent_common 내장 Tool 클래스 모듈입니다.
시스템 타임존 감지 및 전 세계 시간 해석은 agent_common.utils.TimeUtils의 코어 인프라에 위임합니다.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from agent_common.utils import TimeUtils


class DateTimeUtils:
    """
    테이블 변환 룰 및 템플릿 평가 전용 경량 날짜/시간 도구(Tool) 클래스입니다.
    TimeUtils의 코어 타임존/시간 연산을 기반으로, 데이터 파이프라인에서 실제 사용되는
    당일 일자, 표준 타임스탬프, 압축 일시 문자열 생성을 전담합니다.
    """

    FORMAT_DATE_YYYYMMDD_STR: str = "%Y%m%d"
    FORMAT_DATETIME_NO_TZ_STR: str = "%Y-%m-%d %H:%M:%S"
    FORMAT_DATETIME_COMPACT_STR: str = "%Y%m%d%H%M%S"

    @classmethod
    def get_now_datetime(cls, tz_obj: Optional[timezone] = None) -> datetime:
        """
        현재 시각을 지정된 타임존(미지정 시 TimeUtils로 자동 감지된 기본 타임존)이 적용된 timezone-aware datetime 객체로 반환합니다.

        :param tz_obj: 적용할 timezone 객체 (미지정 시 기본 타임존 적용)
        :return: 타임존이 적용된 현재 datetime 객체
        """
        effective_tz_obj: timezone = tz_obj if tz_obj is not None else TimeUtils.resolve_timezone()
        return datetime.now(effective_tz_obj)

    @classmethod
    def get_today_yyyymmdd(cls, tz_obj: Optional[timezone] = None) -> str:
        """
        지정된 타임존(미지정 시 기본 타임존 자동 감지) 기준의 현재 일자를 YYYYMMDD 형식의 8자리 문자열로 반환합니다.

        :param tz_obj: 적용할 timezone 객체 (미지정 시 기본 타임존 적용)
        :return: 'YYYYMMDD' 형식의 당일 날짜 문자열 (예: '20260914')
        """
        target_datetime_obj: datetime = cls.get_now_datetime(tz_obj=tz_obj)
        return target_datetime_obj.strftime(cls.FORMAT_DATE_YYYYMMDD_STR)

    @classmethod
    def get_now_timestamp(cls, tz_obj: Optional[timezone] = None) -> str:
        """
        현재 시각을 타임존 오프셋이 포함된 표준 ISO 8601 타임스탬프 문자열('YYYY-MM-DD HH:MM:SS+09:00' 또는 '+00:00')로 반환합니다.
        (BigQuery TIMESTAMP 및 데이터 파이프라인 표준 규격)

        :param tz_obj: 적용할 timezone 객체 (미지정 시 시스템 자동 감지 기본 타임존)
        :return: 표준 타임스탬프 문자열 (예: '2026-09-14 20:48:59+09:00' 또는 '2026-09-14 11:48:59+00:00')
        """
        target_datetime_obj: datetime = cls.get_now_datetime(tz_obj=tz_obj)
        return target_datetime_obj.isoformat(sep=" ", timespec="seconds")

    @classmethod
    def get_now_no_tz(cls, tz_obj: Optional[timezone] = None) -> str:
        """
        콘솔 로그 및 마크다운 요약표 화면 표시용으로 타임존 오프셋이 제외된 순수 일시 문자열('YYYY-MM-DD HH:MM:SS')을 반환합니다.

        :param tz_obj: 적용할 timezone 객체 (미지정 시 시스템 자동 감지 기본 타임존)
        :return: 타임존 없는 일시 문자열 (예: '2026-09-14 20:48:59')
        """
        target_datetime_obj: datetime = cls.get_now_datetime(tz_obj=tz_obj)
        return target_datetime_obj.strftime(cls.FORMAT_DATETIME_NO_TZ_STR)

    @classmethod
    def get_now_compact(cls, tz_obj: Optional[timezone] = None) -> str:
        """
        지정된 타임존(미지정 시 기본 타임존 자동 감지) 기준의 현재 일시를 14자리 압축 형식(YYYYMMDDHHMMSS) 문자열로 반환합니다.

        :param tz_obj: 적용할 timezone 객체 (미지정 시 기본 타임존 적용)
        :return: 'YYYYMMDDHHMMSS' 형식의 타임스탬프 문자열 (예: '20260914194000')
        """
        target_datetime_obj: datetime = cls.get_now_datetime(tz_obj=tz_obj)
        return target_datetime_obj.strftime(cls.FORMAT_DATETIME_COMPACT_STR)

    @classmethod
    def parse_datetime(cls, dt_input_any: Any, default_tz_obj: Optional[timezone] = None) -> Optional[datetime]:
        """
        다양한 형태(datetime 객체, ISO 8601 일시 문자열 등)의 일시 데이터를 timezone-aware datetime 객체로 파싱 및 정규화합니다.
        실제 파싱 및 타임존 보정 로직은 TimeUtils.parse_datetime에 위임합니다.

        :param dt_input_any: 파싱할 대상 일시 객체 또는 문자열 (None 시 None 반환)
        :param default_tz_obj: 타임존 누락 시 적용할 기본 timezone 객체 (미지정 시 자동 감지)
        :return: 정규화된 timezone-aware datetime 객체 (변환 실패 또는 빈 값일 경우 None)
        """
        return TimeUtils.parse_datetime(dt_input_any=dt_input_any, default_tz_obj=default_tz_obj)

