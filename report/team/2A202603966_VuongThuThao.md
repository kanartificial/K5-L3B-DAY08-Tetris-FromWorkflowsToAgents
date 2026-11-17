# Báo cáo cá nhân — 2A202603966_VuongThuThao

Đổi tên file theo quy tắc `MSSV_HoTen.md`.

Ví dụ: `20241234_NguyenVanAn.md`.

## 1. Thông tin thành viên

- Họ tên: Vương Thu Thảo
- MSSV: 2A202603966
- Email: 
- GitHub: ThuThaoVuong

## 2. Phần việc phụ trách

Shape, module hoặc phần báo cáo bạn phụ trách.

- Workflow – Shape A: Phụ trách triển khai kiến trúc Workflow xử lý yêu cầu hoàn tiền (`src/lab8/shapes/workflow.py`).

- Research: Phụ trách tìm hiểu, tổng hợp nội dung nghiên cứu và xây dựng Research Card tại report/team/research_card.md, tập trung vào việc so sánh các kiến trúc Agent và đánh giá các yếu tố ảnh hưởng đến hiệu quả thực thi.

- Tìm hiểu ranh giới giữa xử lý bằng Python code và xử lý bằng LLM trong kiến trúc Workflow

## 3. Đóng góp cụ thể

Commit chính (hash), test đã thêm hoặc sửa, quyết định kỹ thuật bạn đưa ra.

- Workflow: Triển khai Workflow (Shape A) bằng Python, xây dựng luồng xử lý hoàn tiền theo các bước cố định, kết nối các module dùng chung như Budget, Trace và Host.

- Research: Tìm hiểu, tổng hợp tài liệu và xây dựng Research Card, đề xuất giả thuyết, phương pháp thực nghiệm và các metric đánh giá hiệu quả Agent.

- Kiểm thử: Kiểm tra Workflow thông qua các test chung của hệ thống, đối chiếu kết quả với yêu cầu nghiệp vụ.

- Commit chính: 73244da – setup workflow.
## 4. Bằng chứng

Link commit, tên test, run id hoặc trích đoạn report liên quan.

- Commit triển khai Workflow: `https://github.com/kanartificial/K5-L3B-DAY08-Tetris-FromWorkflowsToAgents/commit/73244daab718db1d4f199ff9adce26c9b93a60b1`

- File code chính: `src/lab8/shapes/workflow.py`.

- File nghiên cứu: `report/team/research_card.md`.

## 5. Công cụ AI đã dùng

Công cụ, dùng vào việc gì, và bạn đã tự kiểm tra kết quả thế nào (xem [RULES.md](../../RULES.md)).

- ChatGPT: Hỗ trợ giải thích yêu cầu bài lab, phân tích kiến trúc Workflow, gợi ý cách tổ chức luồng xử lý, hỗ trợ nội dung báo cáo.

- Cách tự kiểm tra:
  - Đối chiếu code được đề xuất với các interface và module có sẵn trong source code.
  - Kiểm tra luồng xử lý trong workflow.py, đặc biệt là các bước kiểm tra claim, order, compensation và gọi Host.
  - Đối chiếu các quyết định kỹ thuật với docs/architecture.md, docs/business_rules.md và docs/contracts.md.
  - Sử dụng các test có sẵn để kiểm tra tính đúng đắn của hệ thống.
  - Đối chiếu số liệu benchmark với file JSON được sinh ra, không tự tạo hoặc chỉnh sửa số liệu.

## 6. Tự đánh giá

- Hoàn thành phần triển khai Workflow theo kiến trúc xử lý tuần tự bằng Python, đảm bảo các bước nghiệp vụ rõ ràng và có thể theo dõi thông qua Trace.
- Hiểu rõ hơn về ranh giới trách nhiệm giữa Agent, Workflow và Host, đặc biệt đối với các thao tác nhạy cảm như phê duyệt và ghi nhận hoàn tiền.
