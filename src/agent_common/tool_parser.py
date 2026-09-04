# 작성일: 2026-08-21
# 설계자: 김유상 수석
# 설계자 이메일: bakkus@daum.net

"""
이원화된 Tool 디렉터리(1차: 애플리케이션 로컬 tool, 2차: agent_common 내장 tool) 계층 탐색,
동적 도구 함수 로드 및 { } 템플릿 구문 치환 평가를 전담하는 공용 ToolParser 모듈입니다.
"""

from typing import Dict, Any, Optional, Set
from collections.abc import Callable
from pathlib import Path
import os
import re
import inspect
import importlib

from agent_common.logger import ProjectLogger
from agent_common.config_loader import ConfigLoader
from agent_common.utils import DateTimeUtils


class _SafeNamespace:
    """
    딕셔너리 및 중첩 객체에 대해 점(.) 속성 접근 및 안전한 키 탐색을 지원하는 래퍼 클래스입니다.
    """

    def __init__(self, data_obj: Any):
        self._data = data_obj

    def __getattr__(self, name_str: str) -> Any:
        if isinstance(self._data, dict):
            if name_str in self._data:
                val_any = self._data[name_str]
                return _SafeNamespace(val_any) if isinstance(val_any, (dict, list)) else val_any
            name_lower_str = name_str.lower()
            for k_str, v_val in self._data.items():
                if k_str.lower() == name_lower_str:
                    return _SafeNamespace(v_val) if isinstance(v_val, (dict, list)) else v_val
        return ""

    def __getitem__(self, item_key: Any) -> Any:
        if isinstance(self._data, dict):
            if item_key in self._data:
                val_any = self._data[item_key]
                return _SafeNamespace(val_any) if isinstance(val_any, (dict, list)) else val_any
            item_lower_str = str(item_key).lower()
            for k_str, v_val in self._data.items():
                if k_str.lower() == item_lower_str:
                    return _SafeNamespace(v_val) if isinstance(v_val, (dict, list)) else v_val
            return ""
        elif isinstance(self._data, list):
            try:
                val_any = self._data[item_key]
                return _SafeNamespace(val_any) if isinstance(val_any, (dict, list)) else val_any
            except (IndexError, TypeError):
                return ""
        return ""

    def __str__(self) -> str:
        return str(self._data) if self._data is not None else ""

    def __bool__(self) -> bool:
        return bool(self._data)


class ToolParser:
    """
    이원화된 도구(Tool) 계층 동적 로드 및 템플릿 치환 표현식 평가 전담 공용 클래스
    """

    def __init__(
        self,
        config_loader_obj: Optional[ConfigLoader] = None,
        config_dir_path: str | Path | None = None
    ):
        """
        ToolParser 생성자

        :param config_loader_obj: ConfigLoader 인스턴스 (옵션)
        :param config_dir_path: 커스텀 설정 디렉토리 경로 (옵션)
        """
        self.logger = ProjectLogger(self.__class__.__name__)
        self.config_loader: ConfigLoader = config_loader_obj or ConfigLoader(config_dir=config_dir_path)
        self._tool_cache: Dict[str, Callable] = {}

    def build_sys_context(self) -> Dict[str, Any]:
        """
        표준 시스템 런타임 변수 네임스페이스(sys.*)를 조립하여 반환합니다.
        (sys.now, sys.now_compact, sys.today, sys.timestamp_compact 등 포함)

        :return: 시스템 컨텍스트 딕셔너리
        """
        now_compact_str: str = DateTimeUtils.get_now_compact()
        today_str: str = DateTimeUtils.get_today_yyyymmdd()
        now_dt_str: str = DateTimeUtils.get_now_formatted(DateTimeUtils.FORMAT_DATETIME_NO_TZ)

        return {
            "sys": {
                "now": now_dt_str,
                "now_compact": now_compact_str,
                "timestamp_compact": now_compact_str,
                "today": today_str,
                "date_compact": today_str,
            }
        }

    def load_tool_function(self, func_name_str: str) -> Optional[Callable]:
        """
        동적 tool 함수를 2단계 이원화 계층 순으로 탐색하여 로드합니다.
        [1순위] agent_common 패키지 내장 tool 디렉토리 (agent_common/tool/)
        [2순위] 애플리케이션 로컬 tool 디렉토리 (config의 transfer.tool_dir, 예: medallion/tool/)

        :param func_name_str: 로드할 tool 함수명 (예: 'get_now_compact', 'DateTimeUtils.get_now_compact', 'convert_abolition_code')
        :return: 로드된 파이썬 함수 객체 (미존재 시 None)
        """
        if not func_name_str:
            return None

        if func_name_str in self._tool_cache:
            return self._tool_cache[func_name_str]

        # [1순위] agent_common 패키지 내장 도구 디렉토리 탐색 (agent_common/tool/)
        builtin_tool_dir = Path(__file__).resolve().parent / "tool"
        if builtin_tool_dir.exists():
            for py_file in builtin_tool_dir.rglob("*.py"):
                rel_parts = py_file.relative_to(builtin_tool_dir.parent).with_suffix("").parts
                mod_name_str = f"agent_common.{'.'.join(rel_parts)}"
                try:
                    mod = importlib.import_module(mod_name_str)
                    # 1. 모듈 레벨 함수 탐색
                    if hasattr(mod, func_name_str):
                        fn = getattr(mod, func_name_str)
                        if callable(fn):
                            self._tool_cache[func_name_str] = fn
                            return fn

                    # 2. 클래스.메서드 형태 탐색 (예: DateTimeUtils.get_now_compact)
                    if "." in func_name_str:
                        cls_name, m_name = func_name_str.split(".", 1)
                        if hasattr(mod, cls_name):
                            cls_obj = getattr(mod, cls_name)
                            if hasattr(cls_obj, m_name):
                                fn = getattr(cls_obj, m_name)
                                if callable(fn):
                                    self._tool_cache[func_name_str] = fn
                                    return fn

                    # 3. 모듈 내 클래스 내부 메서드 자동 탐색 (예: DateTimeUtils 안의 get_now_compact)
                    target_func_name = func_name_str.split(".")[-1]
                    for attr_name in dir(mod):
                        attr_val = getattr(mod, attr_name)
                        if isinstance(attr_val, type) and hasattr(attr_val, target_func_name):
                            fn = getattr(attr_val, target_func_name)
                            if callable(fn):
                                self._tool_cache[func_name_str] = fn
                                return fn
                except Exception:
                    pass

        # [2순위] 애플리케이션 로컬 도구 디렉토리 탐색 (예: medallion/tool/)
        tool_dir_setting_str: str = str(
            self.config_loader.setting("transfer.tool_dir", "medallion/tool")
        ).strip().strip("/")

        cand_dirs_list: list[Path] = [
            self.config_loader.project_path(tool_dir_setting_str),
            self.config_loader.project_path("medallion/tool"),
            self.config_loader.project_path("tool"),
        ]

        for cand_dir in cand_dirs_list:
            if cand_dir.exists():
                for py_file in cand_dir.rglob("*.py"):
                    if py_file.stem == func_name_str or py_file.stem == func_name_str.split(".")[-1]:
                        rel_parts = py_file.relative_to(self.config_loader.ROOT).with_suffix("").parts
                        mod_name_str = ".".join(rel_parts)
                        try:
                            mod = importlib.import_module(mod_name_str)
                            if hasattr(mod, func_name_str):
                                fn = getattr(mod, func_name_str)
                                self._tool_cache[func_name_str] = fn
                                return fn
                            target_func_name = func_name_str.split(".")[-1]
                            if hasattr(mod, target_func_name):
                                fn = getattr(mod, target_func_name)
                                self._tool_cache[func_name_str] = fn
                                return fn
                        except Exception as import_err:
                            self.logger.warning(
                                "tool_load_failed",
                                func_name=func_name_str,
                                module=mod_name_str,
                                error=str(import_err)
                            )

        return None

    def execute_tool_call(self, func_name_str: str, args_list: list[Any], kwargs_dict: Dict[str, Any]) -> Any:
        """
        로드된 tool 함수를 인자 검증 및 언패킹하여 안전하게 실행합니다.

        :param func_name_str: 실행할 함수명
        :param args_list: 위치 인자 리스트
        :param kwargs_dict: 키워드 인자 딕셔너리
        :return: 함수 실행 반환값
        """
        tool_func = self.load_tool_function(func_name_str)
        if not tool_func:
            raise ValueError(f"Tool 함수 '{func_name_str}'를 찾을 수 없습니다.")

        try:
            sig = inspect.signature(tool_func)
            params = sig.parameters
            has_var_keyword = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
            has_var_positional = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params.values())

            if has_var_keyword and has_var_positional:
                return tool_func(*args_list, **kwargs_dict)
            elif has_var_keyword:
                return tool_func(*args_list, **kwargs_dict)
            else:
                bound_kwargs = {k: v for k, v in kwargs_dict.items() if k in params}
                return tool_func(*args_list, **bound_kwargs)
        except Exception as exec_err:
            self.logger.exception("tool_execution_failed", func_name=func_name_str, error=str(exec_err))
            raise

    def eval(self, template_str: Optional[str], context_dict: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        { } 템플릿 문자열을 해석하고 네임스페이스 변수 치환 및 Tool 함수 호출을 수행하여 최종 문자열을 반환합니다.

        :param template_str: 평가 대상 템플릿 문자열 (예: '{sys.now_compact}', '{get_now_compact()}', '{ecs.key}')
        :param context_dict: 컨텍스트 딕셔너리 (생략 시 기본 sys 컨텍스트 사용)
        :return: 평가 완료된 결과 문자열 (None 또는 원본)
        """
        if template_str is None:
            return None
        if not isinstance(template_str, str):
            return str(template_str)

        tmpl_val_str: str = template_str.strip()
        if not tmpl_val_str:
            return ""

        # 기본 sys 컨텍스트 병합
        merged_ctx: Dict[str, Any] = self.build_sys_context()
        if isinstance(context_dict, dict):
            # context_dict 가 sys 를 포함하면 우선 병합
            for k, v in context_dict.items():
                if k == "sys" and isinstance(v, dict):
                    merged_ctx["sys"].update(v)
                else:
                    merged_ctx[k] = v

        # 1. 단일 {func_name(...)} 형식인 경우 직통 실행
        tool_call_match = re.match(r"^\{([a-zA-Z0-9_]+)\((.*)\)\}$", tmpl_val_str)
        if tool_call_match:
            func_name_str = tool_call_match.group(1)
            raw_args_str = tool_call_match.group(2).strip()

            tool_func = self.load_tool_function(func_name_str)
            if tool_func:
                args: list = []
                kwargs: dict = {}
                if raw_args_str:
                    # 간단한 인자 해석
                    for arg_part in raw_args_str.split(","):
                        arg_clean = arg_part.strip()
                        if "=" in arg_clean:
                            k, v = arg_clean.split("=", 1)
                            kwargs[k.strip()] = self._resolve_arg_val(v.strip(), merged_ctx)
                        else:
                            args.append(self._resolve_arg_val(arg_clean, merged_ctx))

                # 컨텍스트 자동 주입
                kwargs["ctx"] = merged_ctx
                res_val = self.execute_tool_call(func_name_str, args, kwargs)
                return str(res_val) if res_val is not None else ""

        # 2. {namespace.key} 및 복합 템플릿 치환
        result_str: str = re.sub(
            r"\{([^{}]+)\}",
            lambda match_obj: self._resolve_placeholder_token(match_obj.group(1).strip(), merged_ctx),
            tmpl_val_str,
        )
        return result_str

    def _resolve_placeholder_token(self, token_str: str, merged_ctx_dict: Dict[str, Any]) -> str:
        """
        단일 플레이스홀더 토큰 문자열(파이프 폴백 포함)을 평가하여 치환할 문자열을 반환합니다.

        :param token_str: 중괄호 내부의 토큰 문자열 (예: "sys.today", "key1|key2|'default'")
        :param merged_ctx_dict: 평가에 사용할 병합된 컨텍스트 딕셔너리
        :return: 평가 완료된 치환 문자열
        """
        # 파이프(|) 폴백 지원: {key1|key2|'default'}
        for sub_token_str in token_str.split("|"):
            sub_clean_str: str = sub_token_str.strip()
            if (sub_clean_str.startswith("'") and sub_clean_str.endswith("'")) or (sub_clean_str.startswith('"') and sub_clean_str.endswith('"')):
                return sub_clean_str[1:-1]

            # 함수 호출 토큰인 경우
            func_m = re.match(r"^([a-zA-Z0-9_]+)\((.*)\)$", sub_clean_str)
            if func_m:
                f_name_str: str = func_m.group(1)
                if self.load_tool_function(f_name_str):
                    try:
                        f_res_val: Any = self.execute_tool_call(f_name_str, [], {"ctx": merged_ctx_dict})
                        if f_res_val is not None and str(f_res_val) != "":
                            return str(f_res_val)
                    except Exception:
                        pass

            # 네임스페이스 점 접근 탐색
            val_any: Any = self._get_ctx_val(merged_ctx_dict, sub_clean_str)
            if val_any is not None and str(val_any) != "":
                return str(val_any)

        return ""

    def _resolve_arg_val(self, arg_str: str, ctx_dict: Dict[str, Any]) -> Any:
        """인자 표현식 해석 (따옴표 문자열 또는 컨텍스트 키)"""
        if (arg_str.startswith("'") and arg_str.endswith("'")) or (arg_str.startswith('"') and arg_str.endswith('"')):
            return arg_str[1:-1]
        val = self._get_ctx_val(ctx_dict, arg_str)
        return val if val is not None else arg_str

    def _get_ctx_val(self, ctx_dict: Dict[str, Any], key_path_str: str) -> Any:
        """점(.) 경로를 통한 딕셔너리 안전 접근"""
        if not key_path_str:
            return None
        parts = key_path_str.split(".")
        curr = ctx_dict
        for p in parts:
            if isinstance(curr, dict):
                curr = curr.get(p)
            else:
                return None
            if curr is None:
                return None
        return curr

    def scan_rules_for_tool_functions(self, rule_node_any: Any, found_funcs_set: Set[str]) -> None:
        """
        룰 데이터 구조를 재귀적으로 스캔하여 사용된 모든 Tool 함수명을 수집합니다.
        (Fail-Fast 사전 검증용)

        :param rule_node_any: 룰 데이터 노드 (dict, list, str 등)
        :param found_funcs_set: 발견된 함수명을 저장할 set 집합
        """
        if isinstance(rule_node_any, str):
            for match in re.finditer(r"\{([a-zA-Z0-9_]+)\(", rule_node_any):
                found_funcs_set.add(match.group(1))
        elif isinstance(rule_node_any, dict):
            for v in rule_node_any.values():
                self.scan_rules_for_tool_functions(v, found_funcs_set)
        elif isinstance(rule_node_any, list):
            for item in rule_node_any:
                self.scan_rules_for_tool_functions(item, found_funcs_set)
