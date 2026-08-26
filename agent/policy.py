"""BƯỚC 3b — PEP (Policy Enforcement Point) tại tool call (15').

Cổng chặn TRƯỚC KHI tool thật sự execute.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyContext:
    data_classification: str  # "public" | "internal" | "restricted"
    request_purpose: str      # ví dụ "reconciliation", "support-reply"
    agent_owner: str          # định danh agent/run gọi tool này
    delegation_depth: int     # 0 = trực tiếp từ user, >0 = agent-to-agent
    egress_enabled: bool      # run hiện tại có được phép egress network không


def check(context: PolicyContext) -> tuple[bool, str]:
    """Kiểm tra điều kiện chính sách truy cập dữ liệu và hạ tầng.

    Trả về (allow: bool, reason: str).
    Cả allow=True và allow=False đều BẮT BUỘC có reason không rỗng.
    """
    # Rule 1: Restricted data + egress_enabled -> Deny
    if context.data_classification == "restricted" and context.egress_enabled:
        return (
            False,
            f"DENY: Truy cập dữ liệu restricted bị cấm khi egress_enabled=True (agent_owner={context.agent_owner})",
        )

    # Rule 2: Delegation depth quá sâu -> Deny
    if context.delegation_depth > 5:
        return (
            False,
            f"DENY: Delegation depth ({context.delegation_depth}) vượt quá giới hạn an toàn (max 5)",
        )

    # Đầy đủ điều kiện cho phép
    return (
        True,
        f"ALLOW: Thao tác hợp lệ với classification={context.data_classification}, purpose={context.request_purpose}",
    )
