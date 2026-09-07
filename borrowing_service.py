import sqlite3
import requests
from concurrent.futures import ThreadPoolExecutor

class BorrowingService:
    def __init__(self, db_path="borrowings.db", book_service_url="http://localhost:8001", member_service_url="http://localhost:8002"):
        self.db_path = db_path
        self.book_service_url = book_service_url
        self.member_service_url = member_service_url
        # Sử dụng ThreadPoolExecutor để gọi API bất đồng bộ tối ưu hóa độ trễ
        self.executor = ThreadPoolExecutor(max_workers=4)

    def _fetch_book_title(self, book_id: int) -> str:
        """Gọi API đến book-service lấy tên sách"""
        try:
            # Thay vì request thực tế trên localhost (có thể lỗi khi demo offline),
            # ta dùng mocking hoặc fallback an toàn trong code demo
            response = requests.get(f"{self.book_service_url}/books/{book_id}", timeout=2.0)
            if response.status_code == 200:
                return response.json().get("title", "Unknown Book")
        except Exception:
            pass
        return f"Book Info (ID: {book_id})"

    def _fetch_member_name(self, member_id: int) -> str:
        """Gọi API đến member-service lấy tên thành viên"""
        try:
            response = requests.get(f"{self.member_service_url}/members/{member_id}", timeout=2.0)
            if response.status_code == 200:
                return response.json().get("name", "Unknown Member")
        except Exception:
            pass
        return f"Member Info (ID: {member_id})"

    def get_borrowing_detail(self, borrowing_id: int) -> dict:
        # Bước 1: Truy cập database riêng biệt của borrowing-service
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT book_id, member_id, borrow_date FROM borrowings WHERE id = ?", (borrowing_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise ValueError(f"Borrowing record with ID {borrowing_id} not found!")

        book_id, member_id, borrow_date = row

        # Bước 2: Gọi đồng thời cả 2 API để tránh nghẽn I/O (Giải quyết bài toán Latency)
        future_book = self.executor.submit(self._fetch_book_title, book_id)
        future_member = self.executor.submit(self._fetch_member_name, member_id)

        book_title = future_book.result()
        member_name = future_member.result()

        # Bước 3: Tổ hợp kết quả trả về cho client
        return {
            "borrowing_id": borrowing_id,
            "book_title": book_title,
            "member_name": member_name,
            "borrow_date": borrow_date
        }
