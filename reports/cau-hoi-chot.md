# Câu trả lời các câu hỏi đánh giá và chốt buổi (Lab 24)

---

## BƯỚC 1 — BÁO CÁO ĐÁNH GIÁ BASELINE

### 1. Agent này có identity riêng không (per-run, per-agent id)?
- **Trả lời**: **KHÔNG**.
- **Đoạn code chứng minh**: [`agent/loop.py` - Dòng 27](file:///d:/VinAI_20K/Day24-Track2-Data-governance-security/agent/loop.py#L27):
  ```python
  def _naive_loop(message: str, llm) -> str:
  ```
- **Phân tích**: Hàm chỉ nhận `message` và `llm`. Không khởi tạo, lưu trữ hay truyền tham số định danh như `agent_id`, `session_id`, `run_id` hay `user_id`. Tiến trình chạy hoàn toàn ẩn danh, không thể truy vết ai/tiến trình nào đã kích hoạt thao tác.

---

### 2. Ai quyết định nó được gọi `http_post`?
- **Trả lời**: **Nội dung bị Prompt Injection do Attacker kiểm soát (Untrusted LLM Output)**.
- **Đoạn code chứng minh**: [`agent/loop.py` - Dòng 34 & 44](file:///d:/VinAI_20K/Day24-Track2-Data-governance-security/agent/loop.py#L34-L44):
  ```python
  injected = llm.find_injection(combined_text)
  if injected is not None:
      ...
      tools.http_post(injected.target_url, {"records": collected})
  ```
- **Phân tích**: Quyết định gọi `http_post` và tham số `target_url` đều trích xuất trực tiếp từ văn bản `combined_text` thu thập bởi `search_docs`. Không có bất kỳ bộ kiểm soát chính sách (PEP - Policy Enforcement Point), kiểm tra phân quyền hay xác nhận từ hệ thống/người dùng trước khi gửi request.

---

### 3. Nếu nó gửi sai dữ liệu ra ngoài, bạn biết bằng cách nào?
- **Trả lời**: **HOÀN TOÀN KHÔNG THỂ BIẾT ở phía Agent** (chỉ phát hiện được nếu xem log của server nhận bên ngoài `sink/sink.py`).
- **Đoạn code chứng minh**: Toàn bộ hàm `_naive_loop` từ [`agent/loop.py` - Dòng 27 đến 54](file:///d:/VinAI_20K/Day24-Track2-Data-governance-security/agent/loop.py#L27-L54) không hề có bất kỳ câu lệnh ghi log hay kiểm toán bảo mật nào (không có Audit Log / Audit Ledger).

---

## BƯỚC 4 — BA CÂU HỎI CHỐT BUỔI (CLOSING QUESTIONS)

### 1. Bạn đã bỏ chân nào của trifecta, và agent mất đi khả năng gì?
- **Trả lời**: 
  - Hệ thống đã cắt bỏ chân **Exfil Vector (`http_post`)** đối với các luồng xử lý dữ liệu restricted/PII và cô lập chân **Untrusted Content (`search_docs`)** không cho phép trực tiếp truy vấn dữ liệu **Private Data (`read_customer`)**.
  - Agent mất đi khả năng tự ý gửi dữ liệu ra ngoài Internet/External Sink khi chưa có chính sách cho phép (PEP Check) và không thể truy cập hồ sơ khách hàng nếu mã khách hàng đó chỉ xuất hiện trong nội dung văn bản không tin cậy.

---

### 2. Nếu attacker có quyền ghi vào `corpus/`, control nào của bạn còn đứng vững?
- **Trả lời**: **CẢ 3 CONTROL ĐỀU ĐỨNG VỮNG 100%**:
  1. **Control Trifecta Split ([`agent/runner.py`](file:///d:/VinAI_20K/Day24-Track2-Data-governance-security/agent/runner.py#L64-L105))**: Đứng vững hoàn toàn. Vì Run B chỉ đọc `customer_id` từ nguồn tin cậy (`related_tickets` trong `customers.json` gắn với `ticket_id` trích từ tên file), hoàn toàn bỏ qua mọi `customer_id` bị attacker cài cắm trong nội dung file `.md`.
  2. **Control PEP Policy Check ([`agent/policy.py`](file:///d:/VinAI_20K/Day24-Track2-Data-governance-security/agent/policy.py#L39-L57))**: Đứng vững hoàn toàn. Mọi yêu cầu egress (`http_post`) khi đang xử lý dữ liệu `restricted` đều bị chặn cứng (`decision=deny`).
  3. **Control Audit Ledger ([`agent/ledger.py`](file:///d:/VinAI_20K/Day24-Track2-Data-governance-security/agent/ledger.py#L20-L80))**: Đứng vững hoàn toàn. Mọi thao tác đều bị ghi lại trong chuỗi Hash Chain SHA-256 tamper-evident, attacker không thể sửa hay xóa log mà không bị phát hiện.

---

### 3. Regulator hỏi "chứng minh dữ liệu khách hàng chưa từng ra khỏi hệ thống" — bạn mở file nào ra?
- **Trả lời**:
  1. Mở file **[`reports/ledger.jsonl`](file:///d:/VinAI_20K/Day24-Track2-Data-governance-security/reports/ledger.jsonl)** và chạy mã kiểm tra toàn vẹn **`ledger.verify("reports/ledger.jsonl")`** để chứng minh chuỗi hash integrity không bị can thiệp.
  2. Chỉ ra dòng log kiểm toán có `tool: "http_post"`, `decision: "deny"` kèm lý do pháp lý/chính sách trong trường `reason`.
  3. Mở file **[`reports/sink.log`](file:///d:/VinAI_20K/Day24-Track2-Data-governance-security/reports/sink.log)** (0 bytes) và **[`reports/attack-after.log`](file:///d:/VinAI_20K/Day24-Track2-Data-governance-security/reports/attack-after.log)** làm bằng chứng vật lý rằng hệ thống mạng chưa từng truyền bất kỳ bản ghi PII nào ra ngoài sink.
