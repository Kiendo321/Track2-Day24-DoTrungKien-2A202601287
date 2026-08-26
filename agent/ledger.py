"""BƯỚC 3d — audit ledger append-only, tamper-evident (10').

JSONL, mỗi tool call một dòng.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _compute_hash(data: dict) -> str:
    """Tính SHA-256 từ nội dung dict (bỏ trường 'hash' nếu có, sort_keys=True)."""
    clean_data = {k: v for k, v in data.items() if k != "hash"}
    serialized = json.dumps(clean_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def append(entry: dict, path: Path) -> dict:
    """Append 1 dòng JSONL tamper-evident vào file path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    prev_hash = "0" * 64
    if path.exists() and path.stat().st_size > 0:
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            try:
                last_record = json.loads(lines[-1])
                prev_hash = last_record.get("hash", "0" * 64)
            except Exception:
                prev_hash = "0" * 64

    record = dict(entry)
    record["prev_hash"] = prev_hash
    record["hash"] = _compute_hash(record)

    line = json.dumps(record, ensure_ascii=False) + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)

    return record


def verify(path: Path) -> bool:
    """Kiểm tra tính toàn vẹn của file ledger.

    Trả về True nếu mọi dòng có reason non-empty, prev_hash chính xác và hash hợp lệ.
    """
    path = Path(path)
    if not path.exists():
        return True

    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return True

    expected_prev_hash = "0" * 64
    for record_raw in lines:
        try:
            record = json.loads(record_raw)
        except Exception:
            return False

        # 1. Kiểm tra reason non-empty
        reason = record.get("reason")
        if not reason or not str(reason).strip():
            return False

        # 2. Kiểm tra prev_hash
        if record.get("prev_hash") != expected_prev_hash:
            return False

        # 3. Kiểm tra hash tính lại
        stored_hash = record.get("hash")
        computed_hash = _compute_hash(record)
        if stored_hash != computed_hash:
            return False

        # Cập nhật expected_prev_hash cho dòng tiếp theo
        expected_prev_hash = stored_hash

    return True
