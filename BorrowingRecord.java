package com.librax.borrowing.dto;

public class BorrowingRecord {
    private Long id;
    private Long bookId;
    private Long memberId;

    public BorrowingRecord() {}

    public BorrowingRecord(Long id, Long bookId, Long memberId) {
        this.id = id;
        this.bookId = bookId;
        this.memberId = memberId;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getBookId() {
        return bookId;
    }

    public void setBookId(Long bookId) {
        this.bookId = bookId;
    }

    public Long getMemberId() {
        return memberId;
    }

    public void setMemberId(Long memberId) {
        this.memberId = memberId;
    }
}