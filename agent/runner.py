"""BƯỚC 3c — trifecta split + egress allowlist.

Thực hiện tách luồng thực thi (Trifecta Split):
- Run A: Đọc untrusted content (search_docs). Trích xuất ticket_id từ tên file.
- Run B: Tra cứu customer_id từ ticket_id qua related_tickets trong data/customers.json.
- PEP & Egress Control: Mọi tool call đều qua agent.policy.check() và được ghi ledger.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from agent import ledger, policy, tools
from agent.policy import PolicyContext

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
DEFAULT_LEDGER_PATH = REPORTS_DIR / "ledger.jsonl"
CUSTOMERS_FILE = BASE_DIR / "data" / "customers.json"


def _hash_args(args: dict) -> str:
    return hashlib.sha256(json.dumps(args, sort_keys=True).encode("utf-8")).hexdigest()


def handle(message: str, llm, log_dir: Path | None = None) -> str:
    ledger_path = (Path(log_dir) / "ledger.jsonl") if log_dir else DEFAULT_LEDGER_PATH
    now_str = datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # RUN A: search_docs (Untrusted Content Inspection)
    # ------------------------------------------------------------------
    ctx_a = PolicyContext(
        data_classification="internal",
        request_purpose="search-tickets",
        agent_owner="run-a",
        delegation_depth=0,
        egress_enabled=False,
    )
    allow_a, reason_a = policy.check(ctx_a)
    ledger.append(
        {
            "ts": now_str,
            "agent_id": "lab24-agent",
            "run_id": "run-a",
            "tool": "search_docs",
            "args_hash": _hash_args({"query": message}),
            "classification": "internal",
            "decision": "allow" if allow_a else "deny",
            "reason": reason_a,
        },
        ledger_path,
    )

    if not allow_a:
        return "Yêu cầu bị từ chối bởi chính sách an toàn."

    docs = tools.search_docs(message)

    # Trích xuất ticket_id tin cậy từ TÊN FILE (vd "ticket-007.md" -> 7, "ticket-901.md" -> 901)
    ticket_ids: set[int] = set()
    for d in docs:
        filename = d.get("id", "")
        nums = re.findall(r"\d+", filename)
        for num in nums:
            ticket_ids.add(int(num))

    # ------------------------------------------------------------------
    # RUN B: Trusted Customer Lookup & read_customer (Private Data Access)
    # ------------------------------------------------------------------
    customers_data = json.loads(CUSTOMERS_FILE.read_text(encoding="utf-8"))
    matched_customers = []
    for c in customers_data:
        rel_tickets = set(c.get("related_tickets", []))
        if rel_tickets & ticket_ids:
            matched_customers.append(c["customer_id"])

    collected = []
    for cust_id in matched_customers:
        ctx_b = PolicyContext(
            data_classification="restricted",
            request_purpose="read-customer-details",
            agent_owner="run-b",
            delegation_depth=1,
            egress_enabled=False,  # Run B KHÔNG có quyền Egress
        )
        allow_b, reason_b = policy.check(ctx_b)
        ledger.append(
            {
                "ts": now_str,
                "agent_id": "lab24-agent",
                "run_id": "run-b",
                "tool": "read_customer",
                "args_hash": _hash_args({"customer_id": cust_id}),
                "classification": "restricted",
                "decision": "allow" if allow_b else "deny",
                "reason": reason_b,
            },
            ledger_path,
        )

        if allow_b:
            try:
                collected.append(tools.read_customer(cust_id))
            except tools.ToolError:
                continue

    # ------------------------------------------------------------------
    # EGRESS GATEWAY: Phát hiện & Ngăn chặn Egress khi bị Inject
    # ------------------------------------------------------------------
    combined_text = "\n\n".join(d["text"] for d in docs)
    injected = llm.find_injection(combined_text)

    if injected is not None:
        ctx_c = PolicyContext(
            data_classification="restricted",
            request_purpose="http-post-exfil",
            agent_owner="run-c",
            delegation_depth=1,
            egress_enabled=True,  # Yêu cầu egress network với dữ liệu restricted -> Sẽ bị DENY
        )
        allow_c, reason_c = policy.check(ctx_c)
        ledger.append(
            {
                "ts": now_str,
                "agent_id": "lab24-agent",
                "run_id": "run-c",
                "tool": "http_post",
                "args_hash": _hash_args({"url": injected.target_url}),
                "classification": "restricted",
                "decision": "allow" if allow_c else "deny",
                "reason": reason_c,
            },
            ledger_path,
        )

        if allow_c:
            tools.http_post(injected.target_url, {"records": collected})

    return llm.summarize(docs)
