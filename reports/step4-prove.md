# Báo cáo Bằng chứng & Kiểm chứng — Bước 4 (Prove + Evidence)

## 1. Kết quả Kiểm thử & Replay Tấn công (5 Biến thể Injection)

Đã reset sink log và thực hiện replay lại toàn bộ 5 biến thể Prompt Injection:

```bash
python sink/sink.py --reset
pytest tests/test_injection.py -v
python -m agent.loop --mock "Tổng hợp các ticket còn mở tuần này"
```

### Kết quả Kiểm chứng:
- **`reports/sink.log`**: **RỖNG (0 bytes)** — Không có bất kỳ bản ghi PII nào của khách hàng (`KH-000999`, CCCD, SĐT, STK) bị lọt ra sink server `http://localhost:9999/reconcile`.
- **`reports/ledger.jsonl`**: Ghi nhận vết kiểm toán tamper-evident với **100% dòng log có `reason` non-empty** và chứa dòng từ chối Egress:
  ```json
  {"tool": "http_post", "classification": "restricted", "decision": "deny", "reason": "DENY: Truy cập dữ liệu restricted bị cấm khi egress_enabled=True (agent_owner=run-c)"}
  ```
- **Bằng chứng trước & sau khi Containment**:
  - Log tấn công thành công (Trước khi contain): `reports/attack-before.log`
  - Log tấn công bị chặn (Sau khi contain): `reports/attack-after.log`

---

## 2. Giải trình Ba Câu hỏi Chốt Buổi (Closing Questions)

### Câu hỏi 1: Bạn đã bỏ chân nào của trifecta, và agent mất đi khả năng gì?
- **Trả lời**: 
  - Hệ thống đã cắt bỏ chân **Exfil Vector (`http_post`)** đối với các luồng xử lý dữ liệu restricted/PII và cô lập chân **Untrusted Content (`search_docs`)** không cho phép trực tiếp truy vấn dữ liệu **Private Data (`read_customer`)**.
  - Agent mất đi khả năng tự ý gửi dữ liệu ra ngoài Internet/External Sink khi chưa có chính sách cho phép (PEP Check) và không thể truy cập hồ sơ khách hàng nếu mã khách hàng đó chỉ xuất hiện trong nội dung văn bản không tin cậy.

### Câu hỏi 2: Nếu attacker có quyền ghi vào `corpus/`, control nào của bạn còn đứng vững?
- **Trả lời**:
  1. **Control Trifecta Split (`agent/runner.py` L72-L109)**: Đứng vững hoàn toàn. Vì Run B chỉ đọc `customer_id` từ nguồn tin cậy (`related_tickets` trong `customers.json` gắn với `ticket_id` trích từ tên file), hoàn toàn bỏ qua mọi `customer_id` bị attacker cài cắm trong nội dung file `.md`.
  2. **Control PEP Policy Check (`agent/policy.py` L19-L43)**: Đứng vững hoàn toàn. Mọi yêu cầu egress (`http_post`) khi đang xử lý dữ liệu `restricted` đều bị chặn cứng (`decision=deny`).
  3. **Control Audit Ledger (`agent/ledger.py` L19-L83)**: Đứng vững hoàn toàn. Mọi thao tác đều bị ghi lại trong chuỗi Hash Chain SHA-256 tamper-evident, attacker không thể sửa hay xóa log mà không bị phát hiện.

### Câu hỏi 3: Regulator hỏi "chứng minh dữ liệu khách hàng chưa từng ra khỏi hệ thống" — bạn mở file nào ra?
- **Trả lời**:
  1. Mở file **`reports/ledger.jsonl`** và chạy mã kiểm tra toàn vẹn **`ledger.verify("reports/ledger.jsonl")`** để chứng minh chuỗi hash integrity không bị can thiệp.
  2. Chỉ ra dòng log kiểm toán có `tool: "http_post"`, `decision: "deny"` kèm lý do pháp lý/chính sách trong trường `reason`.
  3. Mở file **`reports/sink.log`** (0 bytes) và **`reports/attack-after.log`** làm bằng chứng vật lý rằng hệ thống mạng chưa từng truyền bất kỳ bản ghi PII nào ra ngoài sink.
