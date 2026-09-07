import sqlite3
import os

def init_databases():
    # Setup Books Database
    if os.path.exists("books.db"): os.remove("books.db")
    conn = sqlite3.connect("books.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE books (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT
        )
    """)
    cursor.execute("INSERT INTO books (id, title, author) VALUES (101, 'Design Patterns', 'GoF')")
    cursor.execute("INSERT INTO books (id, title, author) VALUES (102, 'Clean Code', 'Robert C. Martin')")
    conn.commit()
    conn.close()

    # Setup Members Database
    if os.path.exists("members.db"): os.remove("members.db")
    conn = sqlite3.connect("members.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE members (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT
        )
    """)
    cursor.execute("INSERT INTO members (id, name, email) VALUES (201, 'Alice Nguyen', 'alice@gmail.com')")
    cursor.execute("INSERT INTO members (id, name, email) VALUES (202, 'Bob Tran', 'bob@gmail.com')")
    conn.commit()
    conn.close()

    # Setup Borrowings Database (No physical JOIN to other databases)
    if os.path.exists("borrowings.db"): os.remove("borrowings.db")
    conn = sqlite3.connect("borrowings.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE borrowings (
            id INTEGER PRIMARY KEY,
            book_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,
            borrow_date TEXT NOT NULL
        )
    """)
    cursor.execute("INSERT INTO borrowings (id, book_id, member_id, borrow_date) VALUES (1, 101, 201, '2023-10-01')")
    cursor.execute("INSERT INTO borrowings (id, book_id, member_id, borrow_date) VALUES (2, 102, 202, '2023-10-02')")
    conn.commit()
    conn.close()
