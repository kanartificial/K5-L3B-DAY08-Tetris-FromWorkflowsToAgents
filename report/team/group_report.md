# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: Tetris
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`): `9bd80fc`

## 2. Mục tiêu và cách tiếp cận

Bài toán LogiX-VN yêu cầu xây dựng quy trình xử lý claim hoàn phí vận chuyển trên cùng một chữ ký `run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult` theo bốn kiến trúc có mức tự chủ tăng dần: **Workflow (A)**, **Single Agent ReAct (B)**, **Orchestrator + Read-only Investigators (C)** và **Swarm đối chứng (D)**. Nguyên tắc xuyên suốt của nhóm là giữ quyền quyết định số tiền, kiểm tra `principal_id`, policy hiện hành, approval và ghi SQLite ledger trong **code / host**, chỉ dùng model để lập kế hoạch hoặc soạn chữ, đồng thời không tin dữ liệu tự khai trong ticket.

Nhóm phân công song song theo module:
1. **Shape A (`workflow.py`) + Research Card:** Vương Thu Thảo.
2. **Shape B (`single.py`):** Võ Thị Kim Ý. 
3. **Shape C (`orchestrator.py`) + Handoff:** Khổng Ngọc Anh.
4. **CP3/CP4 verification, Benchmark & Decision ADR:** Lê Thị Ly.

Thứ tự triển khai đi từ cổng host (`pytest -q`), hoàn thiện lần lượt 3 shape (CP2), tích hợp `crash_at` / `InjectedCrash` và `make_handoff` (CP3), chạy crash suite 20 điểm (CP4), rồi benchmark 4 shape × 14 public claims × 5 seeds và tổng hợp quyết định kiến trúc (CP5).

## 3. Giải pháp

### Ranh giới code / model ([docs/architecture.md](../../docs/architecture.md))
- **Code / Host quyết định:** lọc theo `principal_id`, kiểm tra policy hiện hành (`is_current = 1` và `effective_date <= 2026-11-15`), tính tiền bồi thường (`compute_compensation`), kiểm tra approval gắn đúng `claim_id`, áp trần hoàn tiền theo đơn (trừ phần đã hoàn ở claim trước), đảm bảo idempotency (`refund:{claim_id}`) trong một transaction SQLite (`durability.issue_refund`), và truyền `crash_at` không bắt `InjectedCrash`.
- **Model (`MockLLM`) chỉ tham gia trong giới hạn:** lập kế hoạch hoặc soạn câu chữ trả lời; kết quả hoàn tiền không bao giờ lấy từ output của model.

### Mô tả ba shape nhóm viết
1. **Shape A — `workflow` ([src/lab8/shapes/workflow.py](../../src/lab8/shapes/workflow.py)):**
   - Thực thi chuỗi bước Python cố định: đọc claim bằng `get_claim_view` → kiểm `order_id` (`needs_info` nếu thiếu) → `lookup_order` (`escalated` nếu không `visible`) → tính quote đầy đủ bằng `compute_compensation` → nếu `proposal <= 0` trả `denied` (không gọi `issue_refund`), nếu `proposal > 0` gọi `durability.issue_refund(conn, claim_id, proposal, crash_at=crash_at)` và kết thúc bằng `common.finish()`.
   - Trace ghi các event theo từng bước xử lý (`claim_view`, `lookup_order`, `quote`, `issue_refund`/`decision`, `crash`).
2. **Shape B — `single` ([src/lab8/shapes/single.py](../../src/lab8/shapes/single.py)):**
   - Dùng `lab8.runtime.run_react(..., max_steps=8)` với vòng lặp `decide` chỉ được gọi tool đọc (`lookup_order`, `compute_compensation`, v.v.) và `MockLLM.complete`.
   - Sau vòng lặp, code của shape kiểm tra kết quả từ tool đọc và gọi `durability.issue_refund` với quote đầy đủ; model không thể gọi tool ghi.
   - Trace ghi quá trình quan sát/tool và quyết định cuối cùng trước khi trả về qua `common.finish()`.
3. **Shape C — `orchestrator` ([src/lab8/shapes/orchestrator.py](../../src/lab8/shapes/orchestrator.py)):**
   - Đọc claim bằng `get_claim_view` (loại bỏ `parent_secret`, `raw_headers_json`), lập kế hoạch bằng `MockLLM.complete(..., purpose="plan")`, xử lý sớm `unknown_claim` và `missing_order_id` (`needs_info`).
   - Dựng gói handoff theo chuẩn `handoff.v1` bằng `lab8.handoff.make_handoff` với `facts={}` và danh sách tool chỉ đọc `["lookup_order", "lookup_policy", "lookup_refund_history"]`, sau đó chạy qua `lab8.runtime.run_readonly_investigators`. `make_handoff` / `sanitize()` dùng allowlist cứng để chặn `parent_secret`, `raw_headers`, `CANARY_SECRET_*` và tool ghi.
   - Tính quote đầy đủ bằng `compute_compensation` từ `order` view do investigator trả về, gọi `durability.issue_refund` với `crash_at=crash_at` (flush trace và re-raise `InjectedCrash` khi crash).
   - Trace ghi các event đã sanitize: `handoff`, `investigator`, `quote`, `decision`, `crash`/`error`.

## 4. Kết quả

### Benchmark 4 shape trên bộ public (`src/reports/benchmark.json`, 14 claims × 5 seeds = 70 trials/shape)

| Shape | Pass rate | Pass^5 | Seed min–max | Seed variance | Cost/success (VND) | Mean steps | p95 steps |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| `workflow` | 1.000 (70/70) | 1.000 (14/14) | 1.000–1.000 | 0.000000 | 27.86 | 5.36 | 6.0 |
| `single` | 1.000 (70/70) | 1.000 (14/14) | 1.000–1.000 | 0.000000 | 51.35 | 5.64 | 6.0 |
| `orchestrator` | 1.000 (70/70) | 1.000 (14/14) | 1.000–1.000 | 0.000000 | 57.19 | 3.71 | 4.0 |
| `swarm` (đối chứng) | 0.986 (69/70) | 0.929 (13/14) | 0.929–1.000 | 0.000816 | 49.57 | 2.80 | 3.0 |

### Crash safety & kiểm thử an toàn (`src/reports/crash.json`)
- **Crash suite:** `20/20` điểm crash an toàn (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`, `amount_conflict_on_retry`, `retry_without_approval`, `swarm_after_effect_before_checkpoint`).
- **Host & Student tests:** `python -m pytest -q` đạt `54 passed`; `python -m pytest -q -m student -o addopts=` đạt `248 passed` (62/62 test cho mỗi shape `workflow`, `single`, `orchestrator`, `swarm`).

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md` (chọn `workflow` vì cùng đạt 100% correctness và 0 variance nhưng chi phí mô phỏng thấp nhất: `27.86 VND/success`). Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

- **Rủi ro truyền nhầm số tiền đã trừ phần hoàn trước (T13, T14):** Nếu shape tự lấy `quote - refunded_vnd` rồi truyền vào `durability.issue_refund`, host sẽ trừ thêm lần nữa. Nhóm xử lý bằng cách luôn truyền **quote đầy đủ** từ `compute_compensation` vào `issue_refund` và để host tính phần chênh trong transaction.
- **Rủi ro crash sau effect trước checkpoint (T12):** Nếu shape bắt `InjectedCrash` hoặc không truyền `crash_at`, kiểm thử crash không kích hoạt được hoặc không flush trace trước khi crash. Nhóm sửa bằng cách truyền thẳng `crash_at` vào `issue_refund`, ghi & flush trace khi bắt `InjectedCrash`, rồi `raise` lại exception.
- **Rủi ro rò rỉ secret/PII vào trace và handoff (T05, T10):** Không dùng `SELECT *` trên bảng `claims` hoặc `orders` để dump vào trace; luôn đọc qua `get_claim_view` / `lookup_order` và sanitize handoff qua `make_handoff`.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

- `MockLLM` không phải model sản xuất; `latency` là `unavailable` và chi phí VND chỉ là chi phí mô phỏng theo `config/pricing.yaml`.
- Bộ public chỉ gồm 14 claims nên không bao phủ hết biến thể ngôn ngữ tự nhiên thực tế; với `MockLLM`, các bài toán có quy tắc rõ ràng như hoàn phí LogiX-VN không hưởng lợi từ tăng mức tự chủ.
- **Điều kiện làm kết luận thay đổi:** Nếu bài toán mở rộng sang yêu cầu suy luận nhiều bước trên dữ liệu phi cấu trúc (nơi `workflow` không thể mã hóa hết luật bằng nhánh Python tĩnh) và mô hình mới chứng minh cải thiện đáng kể pass rate mà vẫn giữ `secret_leak = 0`, `approval_bypass = 0` với chi phí chấp nhận được, nhóm sẽ cân nhắc chuyển sang `single` hoặc `orchestrator`.

## 8. Tài liệu tham khảo

- [docs/business_rules.md](../../docs/business_rules.md) — Luật nghiệp vụ LogiX-VN
- [docs/contracts.md](../../docs/contracts.md) — Contract `RunResult` và `Trace contract v1`
- [docs/architecture.md](../../docs/architecture.md) — Bốn shape và ranh giới code / model
- [docs/metrics.md](../../docs/metrics.md) — Định nghĩa các chỉ số đánh giá
- `src/reports/benchmark.json` và `src/reports/crash.json` — Dữ liệu thực nghiệm của nhóm
