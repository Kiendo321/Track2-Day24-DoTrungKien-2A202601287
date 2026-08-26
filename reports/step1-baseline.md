# Báo cáo Phân tích Baseline — Bước 1

## 1. Sơ đồ hoạt động và Luồng gọi Tool của Agent (`_naive_loop`)

Hàm `_naive_loop` trong `agent/loop.py` (L27-L55) thực thi luồng xử lý chưa có kiểm soát bảo mật như sau:

```mermaid
flowchart TD
    classDef user fill:#2d3748,stroke:#cbd5e0,color:#fff,stroke-width:2px;
    classDef untrusted fill:#9b2c2c,stroke:#feb2b2,color:#fff,stroke-width:2px;
    classDef llm fill:#dd6b20,stroke:#fbd38d,color:#fff,stroke-width:2px;
    classDef pii fill:#742a2a,stroke:#feb2b2,color:#fff,stroke-width:2px;
    classDef exfil fill:#97266d,stroke:#fed7e2,color:#fff,stroke-width:2px;
    classDef safe fill:#276749,stroke:#9ae6b4,color:#fff,stroke-width:2px;

    User(["👤 Người dùng<br><i>(Input Prompt)</i>"]):::user -->|1. Prompt Request| Loop["⚙️ Agent Loop Baseline<br><code>_naive_loop(message, llm)</code>"]

    subgraph Leg1["Chân 1: Untrusted Content"]
        Loop -->|2. search_docs()| Corpus[("📁 Ticket Corpus<br><code>corpus/*.md</code>")]:::untrusted
        Corpus -->|Nội dung Ticket + Payload Injection| Loop
    end

    subgraph LLMBrain["Xử lý LLM & Hijack"]
        Loop -->|3. find_injection()| LLM["🧠 LLM Context Window<br><i>(Bị Prompt Injection kiểm soát)</i>"]:::llm
    end

    LLM -->|4. Extract customer_id & target_url| Decision{Phát hiện<br>Injection?}

    subgraph Leg2["Chân 2: Private Data Access"]
        Decision -->|CÓ: Tuân theo lệnh Attacker| ReadCust["🔍 tools.read_customer()"]:::pii
        ReadCust -->|5. Truy vấn PII| CustDB[("🔒 Private Customer DB<br><code>data/customers.json</code>")]:::pii
        CustDB -->|Trả về CCCD, SĐT, STK...| ReadCust
    end

    subgraph Leg3["Chân 3: Exfiltration Vector"]
        ReadCust -->|6. http_post()| Sink["⚠️ Exfil Sink Server<br><code>http://localhost:9999/reconcile</code>"]:::exfil
    end

    Decision -->|KHÔNG| Summarize["📝 llm.summarize()"]:::safe
    Summarize -->|Trả về câu tóm tắt| User
```

---

## 2. Trả lời 3 câu hỏi đánh giá an toàn Baseline

### Câu hỏi 1: Agent này có identity riêng không (per-run, per-agent id)?
* **Kết luận**: **KHÔNG**.
* **Trích dẫn code**: 
  - Tại `agent/loop.py` - Dòng 27:
    ```python
    def _naive_loop(message: str, llm) -> str:
    ```
  - **Phân tích**: Hàm chỉ nhận `message` và `llm`. Không khởi tạo, lưu trữ hay truyền tham số định danh như `agent_id`, `session_id`, `run_id` hay `user_id`. Tiến trình chạy hoàn toàn ẩn danh, không thể truy vết ai/tiến trình nào đã kích hoạt thao tác.

---

### Câu hỏi 2: Ai quyết định nó được gọi `http_post`?
* **Kết luận**: **Nội dung bị Prompt Injection do Attacker kiểm soát (Untrusted LLM Output)**.
* **Trích dẫn code**:
  - Tại `agent/loop.py` - Dòng 34:
    ```python
    injected = llm.find_injection(combined_text)
    ```
  - Tại `agent/loop.py` - Dòng 35 & 44:
    ```python
    if injected is not None:
        ...
        tools.http_post(injected.target_url, {"records": collected})
    ```
  - **Phân tích**: Quyết định gọi `http_post` và tham số `target_url` đều trích xuất trực tiếp từ văn bản `combined_text` thu thập bởi `search_docs`. Không có bất kỳ bộ kiểm soát chính sách (PEP - Policy Enforcement Point), kiểm tra phân quyền hay xác nhận từ hệ thống/người dùng trước khi gửi request.

---

### Câu hỏi 3: Nếu nó gửi sai dữ liệu ra ngoài, bạn biết bằng cách nào?
* **Kết luận**: **HOÀN TOÀN KHÔNG THỂ BIẾT ở phía Agent** (chỉ phát hiện được nếu xem log của server nhận bên ngoài `sink/sink.py`).
* **Trích dẫn code**:
  - Toàn bộ hàm `_naive_loop` từ `agent/loop.py` - Dòng 27 đến 54 không hề có bất kỳ câu lệnh ghi log hay kiểm toán nào (không có Audit Log / Audit Ledger).
  - Khối `try...except` duy nhất tại Dòng 45-51:
    ```python
    except Exception as exc:
        if "Connection refused" in str(exc) or "Max retries" in str(exc):
            raise SystemExit(...)
    ```
    Đây chỉ là bẫy lỗi kĩ thuật để báo người dùng bật sink server khi chạy thử nghiệm, không phải là cơ chế ghi log lịch sử hay bằng chứng kiểm toán bảo mật.

---

## 3. Tóm tắt lỗ hổng kiến trúc (Lethal Trifecta Vulnerability)

1. **Thiếu Isolation**: Luồng đọc dữ liệu không tin cậy (`search_docs`) và luồng đọc dữ liệu nhạy cảm (`read_customer`) bị nhập chung vào cùng một chu trình điều khiển của LLM.
2. **Thiếu Authorization / PEP**: Không có lớp kiểm soát chính sách ngăn chặn lệnh gửi dữ liệu ra ngoài hệ thống (`http_post`).
3. **Thiếu Auditability**: Không ghi lại nhật ký thực thi (Tamper-evident Audit Ledger), dẫn đến không thể chứng minh việc tuân thủ hoặc phát hiện vi phạm rò rỉ PII.
