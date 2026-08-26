"""BƯỚC 3a — PII gate TRƯỚC KHI vào context/store.

Thực hiện nhận diện và ẩn danh (redact) dữ liệu PII bằng Regex:
- VN_CCCD: 12 chữ số liên tiếp (tránh đụng hàng với STK 12 chữ số).
- VN_PHONE: 10 chữ số bắt đầu bằng 0.
- VN_BANK_ACCOUNT: 8-16 chữ số đi cùng STK hoặc số tài khoản.
- EMAIL: định dạng email chuẩn.
"""
from __future__ import annotations

import re


def detect(text: str) -> list[dict]:
    entities: list[dict] = []

    # 1. EMAIL
    for m in re.finditer(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text):
        entities.append({"type": "EMAIL", "start": m.start(), "end": m.end()})

    # 2. VN_BANK_ACCOUNT (sau STK hoặc số tài khoản)
    for m in re.finditer(r"(?:STK|số tài khoản)\s+(\d{8,16})", text, re.IGNORECASE):
        entities.append({"type": "VN_BANK_ACCOUNT", "start": m.start(1), "end": m.end(1)})

    def _is_occupied(start: int, end: int) -> bool:
        return any(not (end <= ent["start"] or start >= ent["end"]) for ent in entities)

    # 3. VN_CCCD (12 chữ số liên tiếp, không nằm trong bank account)
    for m in re.finditer(r"\b\d{12}\b", text):
        if not _is_occupied(m.start(), m.end()):
            entities.append({"type": "VN_CCCD", "start": m.start(), "end": m.end()})

    # 4. VN_PHONE (10 chữ số bắt đầu bằng 0, không nằm trong bank account)
    for m in re.finditer(r"\b0\d{9}\b", text):
        if not _is_occupied(m.start(), m.end()):
            entities.append({"type": "VN_PHONE", "start": m.start(), "end": m.end()})

    return sorted(entities, key=lambda x: x["start"])


def redact(text: str) -> str:
    entities = detect(text)
    # Thay thế từ vị trí cuối về đầu để không làm lệch offset ký tự
    for ent in sorted(entities, key=lambda x: x["start"], reverse=True):
        replacement = f"[REDACTED_{ent['type']}]"
        text = text[: ent["start"]] + replacement + text[ent["end"] :]
    return text
