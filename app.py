
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash
)

from database import init_db, get_connection

app = Flask(__name__)
app.secret_key = "change-this-demo-secret-before-deployment"


movies = {
    1: {"name": "Baahubali", "price": 200},
    2: {"name": "Kalki 2898 AD", "price": 180},
    3: {"name": "RRR", "price": 150}
}

SHOWTIMES = ["10:00 AM", "2:00 PM", "6:00 PM", "9:00 PM"]

VALID_SEATS = {
    f"{row}{number}"
    for row in "ABCD"
    for number in range(1, 6)
}


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/book/<int:movie_id>", methods=["GET", "POST"])
def book(movie_id):
    movie = movies.get(movie_id)

    if movie is None:
        return "Movie not found", 404

    if request.method == "POST":
        showtime = request.form.get("showtime", "")
        raw_seats = request.form.get("seats", "")
        seats = raw_seats.split(",") if raw_seats else []

        if showtime not in SHOWTIMES:
            flash("Please select a valid showtime.")
            return redirect(url_for("book", movie_id=movie_id))

        if (
            not seats
            or len(seats) != len(set(seats))
            or any(seat not in VALID_SEATS for seat in seats)
        ):
            flash("Please select valid seats.")
            return redirect(
                url_for("book", movie_id=movie_id, showtime=showtime)
            )

        total = len(seats) * movie["price"]
        connection = get_connection()

        try:
            # Lock the database for this transaction before checking seats.
            connection.execute("BEGIN IMMEDIATE")

            placeholders = ",".join("?" for _ in seats)

            existing = connection.execute(
                f"""
                SELECT seat FROM booked_seats
                WHERE movie_id = ?
                  AND showtime = ?
                  AND seat IN ({placeholders})
                """,
                [movie_id, showtime, *seats]
            ).fetchall()

            if existing:
                connection.rollback()
                flash(
                    "These seats are already booked: "
                    + ", ".join(row["seat"] for row in existing)
                )
                return redirect(
                    url_for("book", movie_id=movie_id, showtime=showtime)
                )

            cursor = connection.execute(
                """
                INSERT INTO bookings
                    (movie_id, movie_name, showtime, seats, total)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    movie_id,
                    movie["name"],
                    showtime,
                    ", ".join(seats),
                    total
                )
            )

            booking_id = cursor.lastrowid

            for seat in seats:
                connection.execute(
                    """
                    INSERT INTO booked_seats
                        (movie_id, showtime, seat)
                    VALUES (?, ?, ?)
                    """,
                    (movie_id, showtime, seat)
                )

            connection.commit()

            return redirect(
                url_for("confirmation", booking_id=booking_id)
            )

        except Exception:
            connection.rollback()
            app.logger.exception("Booking failed")
            return "Booking failed. Please try again.", 500

        finally:
            connection.close()

    selected_showtime = request.args.get("showtime", SHOWTIMES[0])

    if selected_showtime not in SHOWTIMES:
        selected_showtime = SHOWTIMES[0]

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT seat FROM booked_seats
            WHERE movie_id = ? AND showtime = ?
            """,
            (movie_id, selected_showtime)
        ).fetchall()

        booked_seats = [row["seat"] for row in rows]

    finally:
        connection.close()

    return render_template(
        "booking.html",
        movie=movie,
        movie_id=movie_id,
        showtimes=SHOWTIMES,
        selected_showtime=selected_showtime,
        booked_seats=booked_seats
    )


@app.route("/confirmation/<int:booking_id>")
def confirmation(booking_id):
    connection = get_connection()

    try:
        booking = connection.execute(
            "SELECT * FROM bookings WHERE booking_id = ?",
            (booking_id,)
        ).fetchone()
    finally:
        connection.close()

    if booking is None:
        return "Booking not found", 404

    return render_template("confirmation.html", booking=booking)


@app.route("/my-bookings")
def my_bookings():
    connection = get_connection()

    try:
        bookings = connection.execute(
            "SELECT * FROM bookings ORDER BY booking_id DESC"
        ).fetchall()
    finally:
        connection.close()

    return render_template("my_bookings.html", bookings=bookings)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
