# Compliance mapping

Bảng ánh xạ các yêu cầu tuân thủ với control kỹ thuật và đường dẫn file/bằng chứng thực tế trong repository:

| Requirement | Control | Evidence |
|---|---|---|
| Luật 91/2025 — quyền yêu cầu xoá | Chưa implement delete cascade (xem stretch goal #3) | — |
| NĐ 356/2025 — hồ sơ xuyên biên giới 60 ngày | Kiểm kê luồng dữ liệu & PII Gate lọc thông tin nhạy cảm trước LLM API | [`reports/dpia-lite.md`](file:///d:/VinAI_20K/Day24-Track2-Data-governance-security/reports/dpia-lite.md#L31-L36) §3, [`agent/pii.py`](file:///d:/VinAI_20K/Day24-Track2-Data-governance-security/agent/pii.py#L13-L40) |
| ASI03 — privilege abuse | Per-agent identity + PEP Policy check từng tool call | [`agent/policy.py`](file:///d:/VinAI_20K/Day24-Track2-Data-governance-security/agent/policy.py#L39-L57) L39-L57, [`agent/runner.py`](file:///d:/VinAI_20K/Day24-Track2-Data-governance-security/agent/runner.py#L70-L100) L70-L100 |
| ASI01 — goal hijack | Trifecta Split (tách luồng đọc untrusted content và luồng đọc private data) | [`agent/runner.py`](file:///d:/VinAI_20K/Day24-Track2-Data-governance-security/agent/runner.py#L64-L105) L64-L105, [`reports/attack-after.log`](file:///d:/VinAI_20K/Day24-Track2-Data-governance-security/reports/attack-after.log) |
| ISO 42001 Clause 5-6 | Policy-as-code có kiểm duyệt + Tamper-evident Audit Ledger append-only | [`agent/policy.py`](file:///d:/VinAI_20K/Day24-Track2-Data-governance-security/agent/policy.py#L39-L57), [`agent/ledger.py`](file:///d:/VinAI_20K/Day24-Track2-Data-governance-security/agent/ledger.py#L20-L80) L20-L80 |
