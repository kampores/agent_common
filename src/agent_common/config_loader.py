# 작성일: 2026-06-18
# 설계자: 김유상
# 설계자 소속: 경포씨엔씨
# 설계자 이메일: bakkus@kpcnc.co.kr, bakkus@daum.net

"""설정 파일(.yml)을 로컬 및 원격 통합 경로에서 동적으로 읽어들이고 병합하는 설정 로더 모듈입니다."""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# 호출하는 메인 프로젝트의 루트 디렉토리 경로를 계산합니다.
# 기본적으로 현재 작업 디렉토리(Current Working Directory)를 기준으로 삼습니다.
ROOT = Path(os.getcwd()).resolve()

# 설정 파일이 위치한 기본 디렉토리 (도메인 의미: 전역 설정 또는 스크립트별 개별 설정을 담은 YAML 파일의 위치)
CONFIG_DIR = ROOT / "config"


def configure(config_dir: str | Path) -> None:
    """설정 파일들을 로드할 디렉토리를 명시적으로 지정한다.

    지정 후 캐시를 비워 새로운 설정값들이 반환되도록 초기화한다.
    """
    global CONFIG_DIR
    CONFIG_DIR = project_path(config_dir)
    get_settings.cache_clear()


@lru_cache(maxsize=1)
def get_settings() -> dict[str, Any]:
    """설정 디렉토리 하위의 모든 YAML 설정 파일을 알파벳 순서로 병합하여 반환한다.
    
    호출 프로젝트의 config 디렉토리 설정들을 로드하여 병합합니다.
    """
    settings: dict[str, Any] = {}
    
    # 호출 프로젝트 고유 설정 로드 및 병합
    if CONFIG_DIR.exists():
        for path in sorted(CONFIG_DIR.glob("*.yml")):
            _deep_merge(settings, _load_yaml_mapping(path))
            
    return settings


def setting(path: str, default: Any = None) -> Any:
    """점 표기법 경로(예: 'api.port')를 사용해 병합된 설정값을 조회한다."""
    current: Any = get_settings()
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def project_path(path: str | Path) -> Path:
    """프로젝트 루트를 기준으로 한 상대 경로를 절대 경로로 변환하여 반환한다."""
    value = Path(path)
    if value.is_absolute():
        return value
    return ROOT / value


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    """지정된 YAML 파일을 파싱하여 최상위 매핑 딕셔너리로 읽어들인다."""
    with path.open("r", encoding="utf-8") as handle:
        settings = yaml.safe_load(handle) or {}
    if not isinstance(settings, dict):
        raise ValueError(f"Settings file must contain a YAML mapping: {path}")
    return settings


def _deep_merge(target: dict[str, Any], incoming: dict[str, Any]) -> None:
    """두 딕셔너리를 재귀적으로 병합하며 중복 키는 덮어쓴다."""
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value
