# Decision record

- Shape chọn: workflow
- Commit hash: 9bd80fc
- Run id dẫn chứng: R-workflow-C-001-s11
- Pass rate / pass^5 / seed min-max / variance: 100% (70/70) / 100% (14/14 claims) / 100%–100% / 0
- Cost per success (mô phỏng, VND): 27.857
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 20 targeted tests passed (authorization, approval binding, handoff secret, trace contract); chưa có kết quả tách riêng cho từng loại

## Vì sao shape này

Nhóm chọn Workflow sau khi so sánh bốn kiến trúc trên cùng 14 public claims và 5 seed (11, 22, 33, 44, 55). Workflow đạt pass rate 100%, pass^5 100%, seed variance bằng 0 và chi phí mô phỏng thấp nhất, khoảng 27.857 VND cho mỗi lần thành công. Single Agent và Orchestrator cũng đạt 100% nhưng có chi phí cao hơn, lần lượt khoảng 51.3543 và 57.19 VND. Swarm đạt 98.57%, có một trường hợp thất bại tại C-002, seed 55. Workflow phù hợp với quy trình hoàn tiền có quy tắc xác định, yêu cầu phê duyệt và side effect cần kiểm soát.

## Có đáng đổi lấy multi-agent không

Nhóm quyết định chưa chuyển sang multi-agent vì chưa có bằng chứng cải thiện correctness so với Workflow, trong khi chi phí cao hơn hoặc độ ổn định thấp hơn. Nhóm chỉ xem xét thay đổi khi benchmark mở rộng chứng minh multi-agent cải thiện đáng kể khả năng xử lý các trường hợp phức tạp, vẫn đáp ứng các yêu cầu safety và có chi phí chấp nhận được.

## Trace và bằng chứng

Các bằng chứng gồm `src/reports/benchmark.json`, `src/reports/crash.json`, run `R-workflow-C-001-s11` và các kiểm thử authorization, approval binding, handoff secret, trace contract.

Trace cần thể hiện quyết định xử lý claim, lời gọi tool, kiểm tra policy, approval, side effect, lỗi và trạng thái cuối. Không ghi API key, token, password hoặc secret vào trace. Các event và field thực tế cần được đối chiếu với trace contract.

Nếu trace được lưu ngoài phạm vi scanner, nhóm cần kiểm tra trực tiếp vị trí đó hoặc mở rộng phạm vi quét; kết quả scanner hiện tại không đủ để chứng minh toàn bộ hệ thống không rò rỉ secret.

## Giới hạn

Benchmark sử dụng MockLLM, không phải model sản xuất. Chi phí được mô phỏng bằng VND. Latency: `unavailable`.

Kết quả trên 14 public claims và 5 seed không bảo đảm hiệu năng trên hidden evaluation. Nhóm không sửa JSON hoặc thay đổi kết quả để đạt ngưỡng 0.75.