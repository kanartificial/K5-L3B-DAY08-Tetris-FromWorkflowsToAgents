# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R4|
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) |Rethinking Evaluation of MAS Efficiency, EMNLP 2026, slide 44 và 59. Loại bằng chứng: nghiên cứu về phương pháp đánh giá hiệu quả hệ thống Multi-Agent. |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Kết luận về hiệu quả của các hệ thống Multi-Agent có thể bị ảnh hưởng bởi cách thiết kế và đo lường quá trình đánh giá. Vì vậy, cần kiểm soát các yếu tố đánh giá trước khi kết luận kiến trúc nào hiệu quả hơn.|
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Thí nghiệm LogiX-VN sử dụng MockLLM, bộ dữ liệu public gồm 14 claims, 5 seeds (11, 22, 33, 44, 55), cùng tool, evaluator và bảng giá mô phỏng. Kết quả chỉ phản ánh môi trường benchmark của lab, không đại diện trực tiếp cho LLM production.|
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Khi thay đổi topology từ Workflow sang Single ReAct hoặc Orchestrator, pass rate dự kiến không tăng đáng kể vì các shape đều sử dụng chung business rules và host. Tuy nhiên, cost/success và số bước thực hiện dự kiến tăng do phát sinh thêm model calls. Swarm có thể có cost thấp hơn nhưng độ ổn định thấp hơn khi gặp các trường hợp phụ thuộc vào dữ liệu kiểm chứng.|
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … |Giữ cố định: MockLLM, tools, seeds (11, 22, 33, 44, 55), corpus (14 claims), pricing, evaluator, as_of và môi trường thực thi. Biến thay đổi duy nhất: topology của Agent (Workflow, Single ReAct, Orchestrator, Swarm). So sánh trên cùng bộ benchmark và các trial độc lập với SQLite riêng. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass |Lỗi dự kiến: một kiến trúc có thể đạt pass rate cao nhưng tiêu tốn nhiều chi phí hơn hoặc có độ ổn định thấp hơn. Đo bằng pass rate, pass^5, seed variance, cost/success, mean steps và p95 steps. Đồng thời kiểm tra approval bypass và secret leakage để đảm bảo an toàn. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
- Run id / file report: `src/reports/benchmark.json`. Mỗi trial có run_id riêng theo định dạng `R-{shape}-{claim_id}-s{seed}`.
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: Hypothesis được ủng hộ một phần. Cả Workflow, Single ReAct và Orchestrator đều đạt pass rate 100%, trong khi Swarm đạt khoảng 98.57%. Tuy nhiên, chi phí mô phỏng và số bước thực hiện khác nhau rõ rệt giữa các kiến trúc. Kết quả cho thấy tăng mức độ tự chủ không đồng nghĩa với tăng độ chính xác.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`. Bộ dữ liệu chỉ gồm 14 claims public nên chưa đủ để khẳng định kết quả tổng quát. Chi phí token là chi phí mô phỏng theo bảng giá cấu hình, không phải chi phí API thực tế. Ngoài ra, các topology có cách tổ chức prompt và gọi tool khác nhau nên chưa thể quy toàn bộ chênh lệch cho riêng topology.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
