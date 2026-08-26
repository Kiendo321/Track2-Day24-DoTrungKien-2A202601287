# DPIA-lite (Đánh giá tác động bảo vệ dữ liệu cá nhân)

## 1. Dữ liệu gì

Liệt kê chi tiết các loại dữ liệu agent tiếp xúc theo từng tool:

- **`search_docs` (Untrusted Data Source)**:
  - Tiếp xúc với văn bản ticket trong `corpus/` (chứa tên, nội dung phản hồi của khách hàng và có thể chứa Prompt Injection Payload do Attacker cài cắm).
- **`read_customer` (Private Data Store)**:
  - Đọc hồ sơ khách hàng đầy đủ từ `data/customers.json`, bao gồm các trường PII nhạy cảm:
    - **`customer_id`**: Mã định danh khách hàng (VD: `KH-000999`).
    - **`name`**: Họ và tên khách hàng (VD: `Lê Thu Trang`).
    - **`cccd`**: Số Căn cước công dân (12 chữ số).
    - **`phone`**: Số điện thoại di động.
    - **`bank_account`**: Số tài khoản ngân hàng.
    - **`email`**: Địa chỉ email cá nhân.
    - **`related_tickets`**: Danh sách mã ticket liên quan.

---

## 2. Mục đích gì

- Agent truy cập dữ liệu để phục vụ yêu cầu hỗ trợ khách hàng và tổng hợp thông tin hỗ trợ kỹ thuật/đối soát theo prompt của người dùng (VD: *"Tóm tắt ticket về hoá đơn"*, *"Tổng hợp các ticket còn mở tuần này"*).
- `search_docs` dùng để tìm các ticket có nội dung liên quan đến yêu cầu.
- `read_customer` dùng để kiểm tra chi tiết hồ sơ chủ thể dữ liệu phục vụ đối soát nghiệp vụ.

---

## 3. Chảy đi đâu

- **Nội bộ hệ thống**:
  - Dữ liệu ticket từ `search_docs` và hồ sơ từ `read_customer` chảy vào context window của LLM để thực hiện tóm tắt.
  - Vết kiểm toán được lưu tại `reports/ledger.jsonl` (Append-only Audit Ledger).
- **Kênh Exfiltration thử nghiệm (Lab Sink)**:
  - Dữ liệu bị gửi qua HTTP POST tới `http://localhost:9999/reconcile` khi agent bị Prompt Injection điều khiển.
- **API Nhà cung cấp Model (Chuyển dữ liệu xuyên biên giới theo NĐ 356/2025)**:
  - Khi sử dụng tùy chọn `--model claude-...`, dữ liệu ticket từ `search_docs` sẽ được truyền qua kết nối HTTPS tới máy chủ API của Anthropic (đặt tại nước ngoài).
  - **Đánh giá tuân thủ NĐ 356/2025**: Đây là hành vi chuyển dữ liệu cá nhân ra nước ngoài. Hệ thống cần triển khai bộ lọc PII (`agent/pii.py`) trước khi gửi prompt tới LLM API và cơ chế kiểm soát Egress (`agent/policy.py`) để ngăn chặn truyền PII trái phép.
