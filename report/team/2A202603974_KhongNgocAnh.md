# Báo cáo cá nhân — 2A202603974_KhongNgocAnh

## 1. Thông tin thành viên

- Họ tên: Khổng Ngọc Anh
- MSSV: 2A202603974
- Email: ngocanhkhong1512@gmail.com
- GitHub: https://github.com/kanartificial

## 2. Phần việc phụ trách

- **Shape C — Orchestrator + Handoff (`src/lab8/shapes/orchestrator.py`):** Triển khai kiến trúc Orchestrator điều phối các investigator chỉ đọc (`read-only investigators`), giữ ranh giới bảo mật giữa parent context và worker, và gọi cổng host `durability.issue_refund` để ghi ledger.
- **CP2 & CP3 cho Shape C:** Xử lý đầy đủ các nhánh nghiệp vụ (`needs_info`, `escalated`, `denied`, `resolved`, `failed`), truyền `crash_at` và lan truyền `InjectedCrash`, đảm bảo Trace Contract v1 trên mọi nhánh return.

## 3. Đóng góp cụ thể

- **Commit chính:** `a6ed582` (`orchestrator with handoff and crash check`), merge vào `main` qua PR #1 (`e22aa7e`).
- **Triển khai `src/lab8/shapes/orchestrator.py`:**
  - Đọc claim qua `get_claim_view` (không lấy `parent_secret`, `raw_headers_json`).
  - Lập kế hoạch/soạn phản hồi bằng `mock_llm.complete`, không tin số ngày trễ hay mã đơn ghi trong nội dung ticket.
  - Tạo gói handoff hợp lệ theo chuẩn `handoff.v1` bằng `lab8.handoff.make_handoff` với danh sách tool chỉ đọc (`lookup_order`, `lookup_policy`, `lookup_refund_history`), không đưa dữ liệu nhạy cảm vào `facts`, và chạy qua `lab8.runtime.run_readonly_investigators`.
  - Tính mức bồi thường bằng `compute_compensation(conn, order)` từ dữ liệu đơn hàng do investigator trả về và truyền **quote đầy đủ** vào `durability.issue_refund(conn, claim_id, proposal, crash_at=crash_at)` để host kiểm tra approval, trần hoàn tiền theo đơn (T13, T14) và idempotency (T11).
  - Ghi trace đã sanitize (`handoff`, `investigator`, `quote`, `decision`, `crash`) qua `lab8.trace.Trace` và `lab8.shapes.common.finish()`, flush trace và không bắt `InjectedCrash` khi crash xảy ra (T12).
- **Kiểm thử đã chạy cho Shape C:**
  - `python -m pytest -q -m student -o addopts= -k orchestrator` → **62 passed** (bao gồm `T01`–`T14`, `T11` retry idempotency, `T12` crash/resume).
  - `python -m pytest -q` → **54 passed** (cổng host xanh).
  - `python -m lab8.benchmark --shapes orchestrator --cases tests/instructor/hidden_claims.jsonl --world tests/instructor/hidden_world_state.json --labels tests/instructor/hidden_labels.json --seeds 11,22,33,44,55 --out reports/hidden_grade.json` → pass rate **1.000**, pass^5 **1.000**, seed variance **0.000000**.

## 4. Bằng chứng

- Commit triển khai Shape C: `https://github.com/kanartificial/K5-L3B-DAY08-Tetris-FromWorkflowsToAgents/commit/a6ed582` (merge PR #1: `e22aa7e`)
- File code chính: `src/lab8/shapes/orchestrator.py`
- Kết quả trên `src/reports/benchmark.json` (14 public claims × 5 seeds = 70 trials cho `orchestrator`):
  - `pass_rate`: `1.0` (`70/70`)
  - `pass_5`: `1.0` (`14/14`)
  - `seed_variance`: `0.0`
  - `cost_per_success_vnd`: `57.19`
  - `mean_steps`: `3.71`
- Run id tiêu biểu: `R-orchestrator-C-001-s11`

## 5. Công cụ AI đã dùng

- Sử dụng trợ lý AI trong IDE để đối chiếu contract (`docs/contracts.md`, `docs/business_rules.md`), kiểm tra luồng handoff/crash của Shape C và rà soát trace contract.
- Cách tự kiểm tra:
  - Chạy trực tiếp `python -m lab8.smoke`, `python -m pytest -q`, `python -m pytest -q -m student -o addopts= -k orchestrator` và `python -m pytest -q -m student -o addopts= -k "t12 and orchestrator"`.
  - Đối chiếu số liệu từ `src/reports/benchmark.json` và đầu ra lệnh chạy thực tế, không chỉnh sửa thủ công file JSON hay test harness.

## 6. Tự đánh giá

- Hoàn thành đầy đủ Shape C (`orchestrator`) đạt 100% pass rate và 100% pass^5 trên cả bộ public (70/70 trials) và hidden (200/200 trials), không rò rỉ secret/PII và giữ an toàn khi crash/retry.
- Nắm rõ ranh giới bảo mật giữa orchestrator và read-only investigator thông qua allowlist `handoff.v1`, cũng như lý do vì sao thao tác ghi tiền và kiểm duyệt phải nằm trong một transaction của host thay vì để model quyết định.
