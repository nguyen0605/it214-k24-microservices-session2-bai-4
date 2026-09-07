# LibraX - Phân tích và Tái thiết kế Tầng dữ liệu theo Database-per-service

Tài liệu này trình bày phân tích hiện trạng coupling dữ liệu của hệ thống LibraX, đề xuất giải pháp tách database thành Database-per-service, định hình kiến trúc xử lý bài toán mới phát sinh và mã nguồn tái cấu trúc lớp `BorrowingService` để loại bỏ các câu truy vấn JOIN trực tiếp.

---

## 1. Phân tích hiện trạng & Rủi ro Coupling

### Hiện trạng lỗi
Trong hệ thống LibraX hiện tại, mặc dù đã chia ứng dụng thành 4 microservices độc lập (`book-service`, `member-service`, `borrowing-service`, `notification-service`), nhưng tất cả vẫn đang kết nối trực tiếp vào một cơ sở dữ liệu MySQL duy nhất là `librax_db`.

Phương thức `getBorrowingDetail` trong `BorrowingService` đang chạy truy vấn:
```sql
SELECT b.title, m.name FROM borrowings br 
JOIN books b ON br.book_id = b.id 
JOIN members m ON br.member_id = m.id 
WHERE br.id = ?
```

### Rủi ro Coupling cụ thể
1. **Schema Coupling (Ràng buộc cấu trúc):** `borrowing-service` phụ thuộc trực tiếp vào cấu trúc bảng `books` và `members`. Nếu đội ngũ phát triển `book-service` thay đổi tên cột `title` thành `book_title` hoặc `member-service` thay đổi kiểu dữ liệu khóa chính `id`, ứng dụng `borrowing-service` sẽ lập tức bị lỗi thời gian chạy (Runtime Error).
2. **Bypass Business Logic:** Việc truy cập trực tiếp vào DB bỏ qua toàn bộ các logic nghiệp vụ, bảo mật, xác thực hoặc cơ chế caching được cài đặt tại tầng ứng dụng của `book-service` và `member-service`.
3. **Mất Tính Độc Lập Triển Khai (Deployment Dependency):** Các service mất đi khả năng deploy độc lập. Mọi thay đổi về database của một service đều yêu cầu sự phối hợp và triển khai đồng bộ giữa các team khác nhau, làm mất đi ưu điểm lớn nhất của mô hình Microservices.
4. **Trở ngại trong việc Scaling và Lựa chọn Công nghệ (No SQL Polyglot):** Khi tất cả gom chung một DB, ta không thể tối ưu hóa hiệu năng riêng cho từng service. Ví dụ, `book-service` có thể phù hợp lưu trữ dạng document (MongoDB/Elasticsearch), còn `borrowing-service` lại phù hợp SQL.

---

## 2. Sơ đồ Tách Database (Database-per-service)

Tách cơ sở dữ liệu dùng chung `librax_db` thành các database độc lập tương ứng với từng service quản lý:

```
+-----------------------+      +-----------------------+      +-------------------------+      +-------------------------------+
|     book-service      |      |    member-service     |      |    borrowing-service    |      |     notification-service      |
+-----------+-----------+      +-----------+-----------+      +------------+------------+      +---------------+--------------+
            |                              |                               |                                   |
            | (JDBC Conn)                  | (JDBC Conn)                   | (JDBC Conn)                       | (JDBC Conn)
+-----------v-----------+      +-----------v-----------+      +------------v------------+      +---------------v---------------+
|       books_db        |      |      members_db       |      |      borrowings_db      |      |       notifications_db        |
| - Table: books        |      | - Table: members      |      | - Table: borrowings     |      | - Table: notifications        |
+-----------------------+      +-----------------------+      +-------------------------+      +-------------------------------+
```

### Quy tắc quản lý mới:
- `borrowings_db.borrowings` chỉ lưu trữ các giá trị định danh thô dưới dạng ID logic: `book_id` và `member_id` (Không tạo khóa ngoại vật lý Foreign Key xuyên database).
- Việc lấy thông tin chi tiết (`title` và `name`) bắt buộc phải thông qua API gọi chéo giữa các service.

---

## 3. Các Bài Toán Mới Phát Sinh và Giải Pháp

Sau khi áp dụng Database-per-service, hai bài toán lớn nhất phát sinh là:

### Bài toán 1: Truy vấn phân tán chậm (Distributed Query Latency)
- **Vấn đề:** Thay vì một truy vấn JOIN ở tầng DB cực nhanh, giờ đây ta phải thực hiện ít nhất 3 bước: truy vấn cục bộ `borrowings`, sau đó gọi 2 cuộc gọi REST API qua mạng để lấy thông tin Sách và Thành viên. Điều này làm tăng độ trễ (latency).
- **Giải pháp xử lý:**
  1. **API Composition (Được triển khai trong code mẫu):** Thực hiện song song hoặc tuần tự các REST Call. Thích hợp cho tần suất thấp.
  2. **Caching:** Phía `borrowing-service` có thể cache lại thông tin `title` và `name` vào Redis cục bộ của nó. Khi thông tin bên `book-service` hay `member-service` thay đổi, họ sẽ phát đi sự kiện qua Message Broker (RabbitMQ/Kafka) để `borrowing-service` cập nhật hoặc xóa cache.
  3. **CQRS Pattern:** Xây dựng một read-model tổng hợp riêng phục vụ riêng các màn hình Dashboard/Query phức tạp.

### Bài toán 2: Đảm bảo tính nhất quán dữ liệu (Distributed Transactions)
- **Vấn đề:** Khi tạo một phiếu mượn sách, ta cần kiểm tra tài khoản thành viên (`member-service`) và trừ số lượng sách khả dụng (`book-service`). Không thể dùng `@Transactional` của JDBC nữa.
- **Giải pháp xử lý:** Sử dụng **Saga Pattern** (ví dụ: Choreography-based Saga bằng cách truyền tải Event qua Message Broker). Nếu việc mượn sách thất bại ở bất cứ bước nào, hệ thống phát đi event bù trừ để khôi phục trạng thái cũ một cách bất đồng bộ.

---

## 4. Cấu trúc thư mục mã nguồn
```
src/main/java/com/librax/borrowing/
├── config/
│   └── AppConfig.java                  # Đăng ký Bean RestTemplate
├── dto/
│   ├── BookDto.java                    # DTO chứa dữ liệu trả về từ book-service
│   ├── BorrowingRecord.java            # DTO map dữ liệu thô từ bảng borrowings
│   └── MemberDto.java                  # DTO chứa dữ liệu trả về từ member-service
└── service/
    └── BorrowingService.java           # Mã nguồn đã được cấu trúc lại hoàn chỉnh
```