# Kết luận ban đầu - đọc trước khi giới thiệu dự án

Đã ghi nhận đủ 816 lượt gọi mô hình theo giao thức chốt trước. Có 2 phản hồi bị lỗi/không hợp lệ do dừng ở giới hạn độ dài; vẫn giữ trong dữ liệu và cách chấm. Không có kết quả từ mô hình Gemini hoặc Antigravity.

## Phát hiện ở 16 hồ sơ thiết bị giữ riêng để kiểm tra

- Qwen3 8B với cách hỏi ngắn trả lời đúng 48/48 trường hợp đủ thông tin, nhưng vẫn trả lời ở 4/16 trường hợp thiếu thông tin. Điểm cân bằng là 87.5%.
- Khi nhắc bằng chứng hoặc nhắc kiểm tra, cùng mô hình trả lời ở 6/16 trường hợp thiếu thông tin; không cải thiện đều so với cách hỏi ngắn. Không nên tuyên bố lời nhắc dài hơn luôn tốt hơn.
- Qwen2.5 1.5B với cách hỏi ngắn trả lời đúng 40/48 trường hợp đủ thông tin, nhưng vẫn trả lời cả 16/16 trường hợp thiếu thông tin. Điều này giải thích vì sao chỉ báo cáo độ đúng trên các câu có đáp án là chưa đủ.
- Bộ lọc nguyên văn giúp một số cấu hình Qwen2.5 giảm trả lời thiếu bằng chứng, nhưng vẫn để lọt câu sai và có thể từ chối câu đúng. Nó chưa phải bộ xác minh ngữ nghĩa.
- Một luật trích xuất viết riêng cho dạng hồ sơ này đạt 100%. Đây là dấu hiệu bộ giả lập còn dễ và hẹp; chưa có cơ sở coi mô hình ngôn ngữ là cần thiết cho riêng các mẫu này.

Các tỷ lệ chỉ mô tả mẫu thử nhỏ này. Phải đọc cùng số lượng ca và khoảng tin cậy theo hồ sơ gốc trong báo cáo. Đây không phải đánh giá toàn diện chất lượng các mô hình Qwen và không thể suy ra tỷ lệ Google nhận đơn.

## Điều cần làm tiếp để tăng giá trị nghiên cứu

Phần nghiên cứu quan trọng tiếp theo là kiểm tra giới hạn của các biện pháp trên tài liệu tự nhiên: đúng câu trích dẫn chưa chắc đúng đối tượng, thiếu đáp án trực tiếp chưa chắc thiếu bằng chứng gián tiếp. Cần người đọc lại nhãn, nguồn tài liệu kỹ thuật có quyền sử dụng, tập kiểm tra mới và mô hình từ các họ khác.

Nhánh XQuAD được lưu riêng vì các nhãn thiếu bằng chứng vẫn chỉ là nhãn tạm. Không gộp số liệu của nó với bộ giả lập để tạo một điểm tổng trông đẹp hơn.
