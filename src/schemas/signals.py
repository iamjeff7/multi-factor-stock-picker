"""Shared signal registration schemas."""

from __future__ import annotations

from pydantic import BaseModel

from core.types import SignalId


class SignalRegistration(BaseModel):
    signal_id: SignalId
    signal_name: str
    signal_category: str
    signal_version: str
    enabled: bool = True
