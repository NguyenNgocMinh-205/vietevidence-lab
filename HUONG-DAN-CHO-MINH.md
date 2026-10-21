# Hiểu dự án của mình

## Một câu dễ nhớ

Tôi kiểm tra AI đọc tài liệu tiếng Việt có trả lời đúng thiết bị, đúng phiên bản và biết dừng khi tài liệu thiếu thông tin hay không.

## Ví dụ

Tài liệu ghi thiết bị A, bản R4 dùng 3.3 V. Một dòng khác ghi thiết bị B dùng 5.1 V. Khi hỏi A/R4, AI phải chọn 3.3 V và trích đúng dòng. Nếu xóa dòng về A/R4, AI nên nói không đủ thông tin, dù vẫn thấy số 5.1 V của B.

Đó là lý do không chỉ chấm "AI có trả lời hay không" mà phải xem trả lời có đúng và có được tài liệu hỗ trợ hay không.

## Mình đã có gì

Một bộ dữ liệu giả lập có quy tắc tạo và đáp án, một nhánh thử tài liệu tự nhiên từ XQuAD, chương trình gọi mô hình chạy trên máy, dữ liệu phản hồi thật, cách chấm, các so sánh và báo cáo. Chưa có công bố khoa học, kiểm chứng thực địa hoặc nhãn được một người độc lập duyệt.

Dự án được chuẩn bị với sự hỗ trợ lớn của AI. Khi giới thiệu, hãy nói rõ bạn là sinh viên đang học cách làm nghiên cứu có thể tái lập, đang tiếp tục tự kiểm tra và mở rộng. Không cần nhận là đã tự viết từng dòng hoặc là chuyên gia nghiên cứu lâu năm.

## Vì sao có hai bộ tài liệu

- Tài liệu thiết bị giả lập: biết chính xác đã ghi gì và xóa gì. Dễ kiểm tra bằng chương trình, nhưng đơn giản hơn tài liệu thật.
- XQuAD: đoạn văn tự nhiên đa dạng hơn. Các bản bị xóa bằng chứng cần người đọc lại; kết quả ở nhánh này chỉ có tính thăm dò.

## Ba cách hỏi

1. Hỏi ngắn dựa trên tài liệu.
2. Nhắc chỉ trả lời khi có bằng chứng và trích câu hỗ trợ.
3. Nhắc kiểm tra đúng thiết bị, phiên bản, thông số trước khi trả lời.

Cả ba cùng phải trả về một mẫu dữ liệu có câu trả lời và trích dẫn. Vì vậy mình đang so sánh độ mạnh của lời nhắc kiểm tra bằng chứng, chưa chứng minh tác dụng riêng của việc "có trích dẫn" so với hoàn toàn không yêu cầu trích dẫn.

## Cách đọc điểm

- Đúng khi có đáp án: càng cao càng tốt.
- Trả lời dù thiếu thông tin: càng thấp càng tốt.
- Từ chối nhầm: càng thấp càng tốt.
- Điểm cân bằng: thưởng cả trả lời đúng lẫn từ chối đúng. Luôn nói "không biết" không thể đạt điểm hoàn hảo.
- Khoảng tin cậy: thể hiện kết quả còn dao động do số hồ sơ ít; không phải xác suất được Google nhận.

## Việc bạn nên tự làm tiếp

Mở màn hình kết quả, chọn vài ca sai và đọc tài liệu/câu trả lời. Chạy lại một ca bằng nút thử AI tại chỗ. Sau đó tự chạy lại nghiên cứu trên một bản sao và ghi những gì bạn hiểu vào nhật ký. Khi kiểm tra nhãn, chỉ điền tên/ngày xác nhận sau khi thực sự đọc và xác nhận từng ca trong `data/review.csv`.

Nếu được hỏi vì sao cần Antigravity: bạn muốn dùng nó để phát triển công cụ thí nghiệm, kiểm thử, quản lý dữ liệu và phân tích lỗi khi mở rộng sang tài liệu kỹ thuật thật. Hiện chưa có kết quả từ mô hình Google trong nghiên cứu này.

## Điều dự án không giải quyết thay mình

Nó không tự tạo ra thầy cô hướng dẫn, tư cách thành viên phòng nghiên cứu hoặc bảo đảm được cấp ưu đãi. Vai trò sinh viên và tình trạng chưa có nhóm nghiên cứu vẫn phải khai đúng.
