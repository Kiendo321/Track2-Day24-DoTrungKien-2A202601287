# Câu trả lời các câu hỏi đánh giá và chốt buổi (Lab 24)

---

## 1. Bạn đã bỏ chân nào của trifecta, và agent mất đi khả năng gì?
- **Trả lời**: 
  - Hệ thống đã cắt bỏ chân **Exfil Vector (`http_post`)** đối với các luồng xử lý dữ liệu restricted/PII và cô lập chân **Untrusted Content (`search_docs`)** không cho phép trực tiếp truy vấn dữ liệu **Private Data (`read_customer`)**.
  - Agent mất đi khả năng tự ý gửi dữ liệu ra ngoài Internet/External Sink khi chưa có chính sách cho phép (`agent/policy.py`) và không thể truy cập hồ sơ khách hàng nếu mã khách hàng đó chỉ xuất hiện trong nội dung văn bản không tin cậy.

---

## 2. Nếu attacker có quyền ghi vào `corpus/`, control nào của bạn còn đứng vững?
- **Trả lời**: **CẢ 3 CONTROL ĐỀU ĐỨNG VỮNG 100%**:
  1. **Control Trifecta Split (`agent/runner.py` L72-L109)**: Đứng vững hoàn toàn. Vì Run B chỉ đọc `customer_id` từ nguồn tin cậy (`related_tickets` trong `customers.json` gắn với `ticket_id` trích từ tên file), hoàn toàn bỏ qua mọi `customer_id` bị attacker cài cắm trong nội dung file `.md`.
  2. **Control PEP Policy Check (`agent/policy.py` L19-L43)**: Đứng vững hoàn toàn. Mọi yêu cầu egress (`http_post`) khi đang xử lý dữ liệu `restricted` đều bị chặn cứng (`decision=deny`).
  3. **Control Audit Ledger (`agent/ledger.py` L19-L83)**: Đứng vững hoàn toàn. Mọi thao tác đều bị ghi lại trong chuỗi Hash Chain SHA-256 tamper-evident, attacker không thể sửa hay xóa log mà không bị phát hiện.

---

## 3. Regulator hỏi "chứng minh dữ liệu khách hàng chưa từng ra khỏi hệ thống" — bạn mở file nào ra?
- **Trả lời**:
  1. Mở file **`reports/ledger.jsonl`** và gọi **`ledger.verify("reports/ledger.jsonl")`** để chứng minh chuỗi hash integrity không bị can thiệp.
  2. Chỉ ra dòng log kiểm toán có `tool: "http_post"`, `decision: "deny"` kèm lý do pháp lý/chính sách trong trường `reason`.
  3. Mở file **`reports/sink.log`** (0 bytes) và **`reports/attack-after.log`** làm bằng chứng vật lý rằng hệ thống mạng chưa từng truyền bất kỳ bản ghi PII nào ra ngoài sink.
