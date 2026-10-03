# 작성일: 2026-08-16
# 설계자: 김유상
# 설계자 이메일: bakkus@daum.net

"""
모노스페이스 콘솔 및 마크다운 테이블에서 한글/한자 등 전각 문자의 2칸 표시 폭을
정밀 계산하여 표 세로줄 컬럼 너비를 칼같이 맞춰주는 공용 테이블 포매터 유틸리티 모듈입니다.
"""

from __future__ import annotations

import unicodedata
from typing import Any, Optional

from agent_common.config_loader import config

# ==============================================================================
# 테이블 포매터 모듈 기본 설정 스키마 (No Hardcoding & Self-Healing 보장)
# ==============================================================================
APP_DEFAULT_SCHEMA_DICT: dict[str, Any] = {
    "table_formatter": {
        "min_center_width_int": 5,        # 마크다운 :---: 중앙 정렬 최소 너비
        "min_default_width_int": 4,       # 마크다운 :--- 좌/우 정렬 최소 너비
        "center_colon_padding_int": 2,    # 마크다운 중앙 정렬 양쪽 콜론 수량
        "default_colon_padding_int": 1,   # 마크다운 좌/우 정렬 콜론 수량
    },
}


class TableFormatter:
    """
    모노스페이스 콘솔 및 마크다운 테이블에서 한글/한자 등 전각 문자의 2칸 표시 폭을
    정밀 계산하여 표 세로줄 컬럼 너비를 칼같이 맞춰주는 공용 테이블 포매터 유틸리티 클래스입니다.
    """

    @classmethod
    def calculate_display_width(cls, text_str: str) -> int:
        """
        문자열이 터미널/마크다운 뷰어에 표시될 때 차지하는 실제 시각적 컬럼 폭(Display Width)을 계산합니다.
        (ASCII 및 서유럽 반각 문자: 1칸, CJK 한글/한자/전각 기호: 2칸)

        :param text_str: 측정할 문자열
        :return: 시각적 셀 너비(칸 수)
        :raises None: 예외를 발생시키지 않음
        """
        total_width_int: int = 0
        for char_str in str(text_str):
            char_width_type_str: str = unicodedata.east_asian_width(char_str)
            # 'W'(Wide), 'F'(Fullwidth) 문자는 2칸 차지, 그 외(Narrow, Halfwidth, Neutral, Ambiguous)는 1칸
            if char_width_type_str in ("W", "F"):
                total_width_int += 2
            else:
                total_width_int += 1
        return total_width_int

    @classmethod
    def format_row(
        cls,
        cells_list: list[str],
        col_widths_list: list[int],
        alignments_list: Optional[list[str]] = None,
    ) -> str:
        """
        한 행(Row)의 셀 리스트와 목표 컬럼 너비 리스트를 전달받아
        정확한 공백 패딩을 적용한 마크다운 테이블 행 문자열('| cell1 | cell2 |')을 조립합니다.

        :param cells_list: 출력할 각 셀의 텍스트 리스트
        :param col_widths_list: 각 컬럼별 목표 시각적 표시 너비 리스트
        :param alignments_list: 각 컬럼별 정렬 방식 리스트 ('left', 'center', 'right', 미지정 시 전체 'left')
        :return: 정렬된 마크다운 테이블 행 문자열
        :raises None: 예외를 발생시키지 않음
        """
        aligned_cells_list: list[str] = []
        col_count_int: int = len(col_widths_list)

        for i in range(col_count_int):
            cell_str: str = cells_list[i] if i < len(cells_list) else ""
            width_int: int = col_widths_list[i]
            align_mode_str: str = alignments_list[i] if alignments_list and i < len(alignments_list) else "left"

            aligned_cell_str: str = cls.pad_cell(cell_str, width_int, align_mode_str)
            aligned_cells_list.append(aligned_cell_str)

        return "| " + " | ".join(aligned_cells_list) + " |"

    @classmethod
    def format_separator(
        cls,
        col_widths_list: list[int],
        alignments_list: Optional[list[str]] = None,
    ) -> str:
        """
        컬럼 너비 및 정렬 방식에 부합하는 마크다운 헤더 구분선('| :--- | :---: | ---: |')을 생성합니다.

        :param col_widths_list: 각 컬럼별 목표 시각적 표시 너비 리스트
        :param alignments_list: 각 컬럼별 정렬 방식 리스트
        :return: 마크다운 헤더 구분선 문자열
        :raises None: 예외를 발생시키지 않음
        """
        sep_parts_list: list[str] = []
        for i, width_int in enumerate(col_widths_list):
            align_mode_str: str = alignments_list[i] if alignments_list and i < len(alignments_list) else "left"
            if align_mode_str == "center":
                dashes_count_int: int = max(config.table_formatter.min_center_width_int, width_int)
                sep_parts_list.append(":" + "-" * (dashes_count_int - config.table_formatter.center_colon_padding_int) + ":")
            elif align_mode_str == "right":
                dashes_count_int = max(config.table_formatter.min_default_width_int, width_int)
                sep_parts_list.append("-" * (dashes_count_int - config.table_formatter.default_colon_padding_int) + ":")
            else:
                dashes_count_int = max(config.table_formatter.min_default_width_int, width_int)
                sep_parts_list.append(":" + "-" * (dashes_count_int - config.table_formatter.default_colon_padding_int))

        return "| " + " | ".join(sep_parts_list) + " |"

    @classmethod
    def pad_cell(
        cls,
        cell_text_str: str,
        target_width_int: int,
        align_mode_str: str = "left",
    ) -> str:
        """
        개별 셀 텍스트의 시각적 너비를 계산하여 목표 너비에 맞게 공백을 채워 넣습니다.

        :param cell_text_str: 패딩 대상 셀 문자열
        :param target_width_int: 목표 표시 너비
        :param align_mode_str: 정렬 방식 ('left', 'center', 'right')
        :return: 패딩이 완료된 셀 문자열
        :raises None: 예외를 발생시키지 않음
        """
        current_width_int: int = cls.calculate_display_width(cell_text_str)
        padding_spaces_int: int = max(0, target_width_int - current_width_int)

        if align_mode_str == "center":
            left_spaces_int: int = padding_spaces_int // 2
            right_spaces_int: int = padding_spaces_int - left_spaces_int
            return " " * left_spaces_int + cell_text_str + " " * right_spaces_int
        elif align_mode_str == "right":
            return " " * padding_spaces_int + cell_text_str
        else:
            return cell_text_str + " " * padding_spaces_int

    @classmethod
    def format_markdown_table(
        cls,
        headers_list: list[str],
        rows_list: list[list[str]],
        alignments_list: Optional[list[str]] = None,
    ) -> list[str]:
        """
        헤더와 행 데이터 목록을 받아 각 열(Column)의 최대 표시 너비에 맞춰
        정렬 방향별 공백 패딩을 적용한 마크다운 테이블 행 문자열 리스트를 생성합니다.

        :param headers_list: 테이블 헤더 열 레이블 리스트
        :param rows_list: 데이터 행별 셀 문자열 리스트
        :param alignments_list: 각 열별 정렬 방식 리스트 ('left' / ':---', 'center' / ':---:', 'right' / '---:'). 미지정 시 전체 'left'
        :return: 세로줄(|) 정렬이 완료된 마크다운 테이블 행 문자열 리스트
        :raises None: 예외를 발생시키지 않음
        """
        columns_count_int: int = len(headers_list)
        if columns_count_int == 0:
            return []

        # 열별 정렬 표준화 ('left', 'center', 'right')
        normalized_alignments_list: list[str] = []
        for col_idx_int in range(columns_count_int):
            if alignments_list and col_idx_int < len(alignments_list):
                align_str: str = alignments_list[col_idx_int].strip()
                if align_str in (":---:", "center"):
                    normalized_alignments_list.append("center")
                elif align_str in ("---:", ":--:", "right"):
                    normalized_alignments_list.append("right")
                else:
                    normalized_alignments_list.append("left")
            else:
                normalized_alignments_list.append("left")

        # 각 열의 최대 표시 너비 계산 (최소 너비: center는 min_center_width_int, left/right는 min_default_width_int)
        col_widths_list: list[int] = []
        for col_idx_int in range(columns_count_int):
            header_str: str = headers_list[col_idx_int]
            min_required_width_int: int = (
                config.table_formatter.min_center_width_int
                if normalized_alignments_list[col_idx_int] == "center"
                else config.table_formatter.min_default_width_int
            )
            max_width_int: int = max(cls.calculate_display_width(header_str), min_required_width_int)
            for row_items_list in rows_list:
                if col_idx_int < len(row_items_list):
                    cell_text_str: str = row_items_list[col_idx_int]
                    max_width_int = max(max_width_int, cls.calculate_display_width(cell_text_str))
            col_widths_list.append(max_width_int)

        header_row_str: str = cls.format_row(headers_list, col_widths_list, normalized_alignments_list)
        separator_row_str: str = cls.format_separator(col_widths_list, normalized_alignments_list)

        result_rows_list: list[str] = [header_row_str, separator_row_str]
        for row_items_list in rows_list:
            result_rows_list.append(cls.format_row(row_items_list, col_widths_list, normalized_alignments_list))

        return result_rows_list


__all__ = [
    "APP_DEFAULT_SCHEMA_DICT",
    "TableFormatter",
]
