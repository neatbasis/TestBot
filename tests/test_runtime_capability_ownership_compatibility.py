from __future__ import annotations

from testbot import sat_chatbot_memory_v2 as runtime
from testbot.runtime_capability_service import CapabilitySnapshotData, RuntimeCapabilityStatusData


def test_legacy_runtime_capability_types_alias_service_owned_models() -> None:
    assert runtime.RuntimeCapabilityStatus is RuntimeCapabilityStatusData
    assert runtime.CapabilitySnapshot is CapabilitySnapshotData
