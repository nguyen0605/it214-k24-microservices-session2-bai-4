from models import init_databases
from borrowing_service import BorrowingService
import unittest
from unittest.mock import patch

# Mock response class để giả lập kết quả HTTP Request của Microservice
class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

def mock_requests_get(url, *args, **kwargs):
    if "/books/101" in url:
        return MockResponse({"id": 101, "title": "Design Patterns", "author": "GoF"}, 200)
    elif "/books/102" in url:
        return MockResponse({"id": 102, "title": "Clean Code", "author": "Robert C. Martin"}, 200)
    elif "/members/201" in url:
        return MockResponse({"id": 201, "name": "Alice Nguyen", "email": "alice@gmail.com"}, 200)
    elif "/members/202" in url:
        return MockResponse({"id": 202, "name": "Bob Tran", "email": "bob@gmail.com"}, 200)
    return MockResponse({}, 404)

@patch('requests.get', side_effect=mock_requests_get)
def run_demo(mock_get):
    print("=== BẮT ĐẦU CHƯƠNG TRÌNH PHÂN TÁCH DATABASE & TÁI THIẾT KẾ ===")
    
    # Khởi tạo các DB vật lý riêng lẻ mô phỏng cho Database-per-service
    print("\n1. Khởi tạo cơ sở dữ liệu riêng lẻ cho từng service...")
    init_databases()
    print(" - Đã tạo books.db thành công!")
    print(" - Đã tạo members.db thành công!")
    print(" - Đã tạo borrowings.db thành công!")

    # Khởi tạo service và thực hiện lấy thông tin mượn sách thông qua REST API
    print("\n2. Thực hiện truy vấn thông tin mượn sách qua BorrowingService (gọi API thay thế JOIN)...\n")
    service = BorrowingService()
    
    # Lấy thông tin lượt mượn ID = 1
    detail_1 = service.get_borrowing_detail(1)
    print("Kết quả truy vấn Borrowing ID = 1:")
    print(f" - Tên Sách: {detail_1['book_title']}")
    print(f" - Tên Thành Viên: {detail_1['member_name']}")
    print(f" - Ngày Mượn: {detail_1['borrow_date']}")
    print("-------------------------------------------")
    
    # Lấy thông tin lượt mượn ID = 2
    detail_2 = service.get_borrowing_detail(2)
    print("Kết quả truy vấn Borrowing ID = 2:")
    print(f" - Tên Sách: {detail_2['book_title']}")
    print(f" - Tên Thành Viên: {detail_2['member_name']}")
    print(f" - Ngày Mượn: {detail_2['borrow_date']}")
    print("===========================================================")

if __name__ == "__main__":
    run_demo()
