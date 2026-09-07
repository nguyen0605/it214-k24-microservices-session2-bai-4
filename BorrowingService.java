package com.librax.borrowing.service;

import com.librax.borrowing.dto.BookDto;
import com.librax.borrowing.dto.MemberDto;
import com.librax.borrowing.dto.BorrowingRecord;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@Service
public class BorrowingService {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Autowired
    private RestTemplate restTemplate;

    @Value("${services.book-service.url:http://book-service}")
    private String bookServiceUrl;

    @Value("${services.member-service.url:http://member-service}")
    private String memberServiceUrl;

    private final RowMapper<BorrowingRecord> borrowingRowMapper = (rs, rowNum) -> new BorrowingRecord(
            rs.getLong("id"),
            rs.getLong("book_id"),
            rs.getLong("member_id")
    );

    /**
     * Lấy thông tin chi tiết mượn sách đã được viết lại.
     * Giải quyết triệt để coupling bằng cách:
     * 1. Query thông tin thô từ cơ sở dữ liệu cục bộ borrowings_db.
     * 2. Sử dụng RestTemplate gọi API lấy thông tin tên sách và tên thành viên từ các microservices tương ứng.
     */
    public String getBorrowingDetail(Long borrowingId) {
        // Bước 1: Query database cục bộ của borrowing-service (chỉ bảng borrowings)
        String sql = "SELECT id, book_id, member_id FROM borrowings WHERE id = ?";
        BorrowingRecord record;
        try {
            record = jdbcTemplate.queryForObject(sql, borrowingRowMapper, borrowingId);
        } catch (Exception e) {
            return "Borrowing record not found for ID: " + borrowingId;
        }

        if (record == null) {
            return "Borrowing record not found";
        }

        // Bước 2: Gọi REST API sang book-service lấy thông tin sách với cơ chế dự phòng (Fallback)
        String bookTitle = "Unknown Book";
        try {
            String bookApiUrl = bookServiceUrl + "/books/" + record.getBookId();
            BookDto book = restTemplate.getForObject(bookApiUrl, BookDto.class);
            if (book != null && book.getTitle() != null) {
                bookTitle = book.getTitle();
            }
        } catch (Exception e) {
            // Ghi log lỗi và tiếp tục để tăng khả năng chống chịu lỗi (Fault Tolerance) của hệ thống
            System.err.println("Error calling book-service for bookId " + record.getBookId() + ": " + e.getMessage());
        }

        // Bước 3: Gọi REST API sang member-service lấy thông tin thành viên với cơ chế dự phòng
        String memberName = "Unknown Member";
        try {
            String memberApiUrl = memberServiceUrl + "/members/" + record.getMemberId();
            MemberDto member = restTemplate.getForObject(memberApiUrl, MemberDto.class);
            if (member != null && member.getName() != null) {
                memberName = member.getName();
            }
        } catch (Exception e) {
            System.err.println("Error calling member-service for memberId " + record.getMemberId() + ": " + e.getMessage());
        }

        // Trả về chuỗi thông tin chi tiết đầy đủ đúng nghiệp vụ
        return "Book Title: " + bookTitle + ", Member Name: " + memberName;
    }
}