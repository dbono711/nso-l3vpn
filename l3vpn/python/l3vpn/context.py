# -*- mode: python; python-indent: 4 -*-
"""Docstring Missing."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ServiceContext:
    log: Any
    root: Any
    service: Any
