
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "movie_booking.db")


def get_connection():
    connection = sqlite3.connect(DATABASE, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                movie_id INTEGER NOT NULL,
                movie_name TEXT NOT NULL,
                showtime TEXT NOT NULL,
                seats TEXT NOT NULL,
                total INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS booked_seats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movie_id INTEGER NOT NULL,
                showtime TEXT NOT NULL,
                seat TEXT NOT NULL,
                UNIQUE(movie_id, showtime, seat)
            )
        """)

        connection.commit()
        print("Database initialized successfully!")

    finally:
        connection.close()


if __name__ == "__main__":
    init_db()
