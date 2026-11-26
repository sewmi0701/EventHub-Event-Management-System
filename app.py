from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection
import mysql.connector
from decimal import Decimal, InvalidOperation
from datetime import datetime
app = Flask(__name__)
import os
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "eventhub-local-only-change-before-deployment"
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
from flask import send_from_directory

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/style.css")
def stylesheet():
    return send_from_directory(".", "style.css")

@app.route("/login.html")
def login_page():
    return send_from_directory(".", "login.html")

@app.route("/home.html")
def home_page():
    return send_from_directory(".", "home.html")

@app.route("/home.css")
def home_css():
    return send_from_directory(".", "home.css")

@app.route("/home.js")
def home_js():
    return send_from_directory(".", "home.js")

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid request."
        }), 400
    name = str(data.get("full_name") or "").strip()
    email = str(data.get("email") or "").strip().lower()
    password = data.get("password")
    if not isinstance(password, str):
        return jsonify({
            "success": False,
            "message": "Password is required."
        }), 400
    if not name or not email or len(password) < 8:
        return jsonify({
            "success": False,
            "message": "Enter valid details and a password of at least 8 characters."
        }), 400
    if len(name) > 100 or len(email) > 150 or "@" not in email:
        return jsonify({
            "success": False,
            "message": "Please enter valid name and email."
        }), 400
    password_hash = generate_password_hash(password)
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = """
            INSERT INTO users
            (full_name, email, password_hash, role)
            VALUES (%s, %s, %s, 'user')
        """
        cursor.execute(query, (name, email, password_hash))
        connection.commit()
        return jsonify({
            "success": True,
            "message": "Account registered successfully!"
        }), 201
    except mysql.connector.IntegrityError:
        return jsonify({
            "success": False,
            "message": "This email is already registered."
        }), 409
    except mysql.connector.Error:
        app.logger.exception("Database registration error")
        return jsonify({
            "success": False,
            "message": "Registration failed. Please try again."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid request."
        }), 400
    email = str(data.get("email") or "").strip().lower()
    password = data.get("password")
    if not email or not isinstance(password, str):
        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT user_id, full_name, password_hash, role
            FROM users
            WHERE email = %s
            """,
            (email,)
        )
        user = cursor.fetchone()
        if not user or not check_password_hash(
            user["password_hash"], password
        ):
            return jsonify({
                "success": False,
                "message": "Invalid email or password."
            }), 401
        session.clear()
        session["user_id"] = user["user_id"]
        session["role"] = user["role"]
        session["name"] = user["full_name"]
        redirect_pages = {
            "user": "/home.html",
            "admin": "/admin/dashboard.html",
            "organizer": "/organizer/dashboard.html"
        }
        return jsonify({
            "success": True,
            "message": "Login successful!",
            "redirect": redirect_pages.get(
                user["role"], "/home.html"
            )
        }), 200
    except mysql.connector.Error:
        app.logger.exception("Login database error")
        return jsonify({
            "success": False,
            "message": "Login failed. Please try again."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({
        "success": True,
        "message": "Logged out successfully!",
        "redirect": "/login.html"
    })
from functools import wraps
from flask import redirect, url_for
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login.html")
        return f(*args, **kwargs)
    return decorated_function
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login.html")
        if session.get("role") != "admin":
            return "Access denied: Admins only.", 403
        return f(*args, **kwargs)
    return decorated_function

@app.route("/admin/dashboard.html")
@admin_required
def admin_dashboard():
    return send_from_directory(
        "admin", "dashboard.html"
    )

@app.route("/admin/admin.css")
@admin_required
def admin_stylesheet():
    return send_from_directory(
        "admin", "admin.css"
    )

@app.route("/admin/add-event.html")
@admin_required
def admin_add_event():
    return send_from_directory(
        "admin", "add-event.html"
    )

@app.route("/admin/add-event.js")
@admin_required
def admin_add_event_js():
    return send_from_directory(
        "admin", "add-event.js"
    )
from functools import wraps
def event_creator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({
                "success": False,
                "message": "Please login first."
            }), 401
        if session.get("role") not in ("admin", "organizer"):
            return jsonify({
                "success": False,
                "message": "Access denied."
            }), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route("/api/events", methods=["POST"])
@event_creator_required
def create_event():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid event data."
        }), 400
    title = str(data.get("title") or "").strip()
    category = str(data.get("category") or "").strip()
    event_date = str(data.get("event_date") or "").strip()
    event_time = str(data.get("event_time") or "").strip()
    location = str(data.get("location") or "").strip()
    description = str(data.get("description") or "").strip()
    try:
        max_participants = int(data.get("max_participants"))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid participant limit."
        }), 400
    if not all([
        title, category, event_date,
        event_time, location, description
    ]):
        return jsonify({
            "success": False,
            "message": "Please fill in all required fields."
        }), 400
    if max_participants < 1 or max_participants > 100000:
        return jsonify({
            "success": False,
            "message": "Invalid participant limit."
        }), 400
    from datetime import datetime
    try:
        event_datetime = datetime.strptime(
            f"{event_date} {event_time}",
            "%Y-%m-%d %H:%M"
        )
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid event date or time."
        }), 400
    if event_datetime <= datetime.now():
        return jsonify({
            "success": False,
            "message": "Event must be in the future."
        }), 400
    if (len(title) > 150 or len(category) > 50
            or len(location) > 255):
        return jsonify({
            "success": False,
            "message": "One or more fields are too long."
        }), 400
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        # Validate ticket price from the event form.
        try:
            ticket_price = Decimal(
                str(data.get("ticket_price", 0))
            )
            if (
                not ticket_price.is_finite()
                or ticket_price < 0
                or ticket_price > Decimal("999999.99")
                or ticket_price.as_tuple().exponent < -2
            ):
                raise ValueError()
        except (InvalidOperation, ValueError, TypeError):
            return jsonify({
                "success": False,
                "message": "Invalid ticket price."
            }), 400
        # Save event with ticket price
        query = """
            INSERT INTO events
            (
                organizer_id,
                title,
                category,
                event_date,
                event_time,
                location,
                description,
                max_participants,
                ticket_price,
                image_path,
                status
            )
            VALUES
            (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                NULL, 'published'
            )
        """
        cursor.execute(query, (
            session["user_id"],
            title,
            category,
            event_date,
            event_time,
            location,
            description,
            max_participants,
            ticket_price
        ))
        connection.commit()
        return jsonify({
            "success": True,
            "message": "Event published successfully!",
            "event_id": cursor.lastrowid
        }), 201
    except mysql.connector.Error:
        app.logger.exception("Event creation failed")
        return jsonify({
            "success": False,
            "message": "Could not save event."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route("/api/events", methods=["GET"])
def get_events():
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                event_id,
                title,
                category,
                CAST(event_date AS CHAR) AS event_date,
                LEFT(CAST(event_time AS CHAR), 5) AS event_time,
                location,
                description,
                max_participants,
                image_path,
                ticket_price
            FROM events
           
WHERE status = 'published'
  AND TIMESTAMP(event_date, event_time) > NOW()

            ORDER BY event_date ASC, event_time ASC
        """)
        events = cursor.fetchall()
        return jsonify({
            "success": True,
            "events": events
        }), 200
    except mysql.connector.Error:
        app.logger.exception("Failed to load events")
        return jsonify({
            "success": False,
            "message": "Could not load events."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
# Display uploaded event images

@app.route("/uploads/events/<filename>")
def event_image(filename):
    return send_from_directory("uploads/events", filename)
# Upload an image for an existing event

@app.route("/api/events/<int:event_id>/image", methods=["POST"])
@event_creator_required
def upload_event_image(event_id):
    from uuid import uuid4
    image = request.files.get("image")
    if not image or not image.filename:
        return jsonify({
            "success": False,
            "message": "Please select an image."
        }), 400
    extension = os.path.splitext(image.filename)[1].lower()
    if extension not in (".jpg", ".jpeg", ".png", ".webp"):
        return jsonify({
            "success": False,
            "message": "Only JPG, PNG and WEBP images are allowed."
        }), 400
    content = image.read(10 * 1024 * 1024 + 1)
    if not content or len(content) > 10 * 1024 * 1024:
        return jsonify({
            "success": False,
            "message": "Image must be 10 MB or smaller."
        }), 400
    # Check file signatures, not just filenames
    if extension in (".jpg", ".jpeg"):
        valid = content.startswith(b"\xff\xd8\xff")
    elif extension == ".png":
        valid = content.startswith(b"\x89PNG\r\n\x1a\n")
    else:
        valid = (
            content[:4] == b"RIFF"
            and content[8:12] == b"WEBP"
        )
    if not valid:
        return jsonify({
            "success": False,
            "message": "Invalid image format."
        }), 400
    connection = None
    cursor = None
    file_path = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """SELECT event_id FROM events
               WHERE event_id = %s AND organizer_id = %s""",
            (event_id, session["user_id"])
        )
        if cursor.fetchone() is None:
            return jsonify({
                "success": False,
                "message": "Event not found or access denied."
            }), 404
        upload_folder = os.path.join(
            app.root_path, "uploads", "events"
        )
        os.makedirs(upload_folder, exist_ok=True)
        filename = f"{uuid4().hex}{extension}"
        file_path = os.path.join(upload_folder, filename)
        with open(file_path, "wb") as f:
            f.write(content)
        image_url = f"/uploads/events/{filename}"
        cursor.execute(
            "UPDATE events SET image_path = %s WHERE event_id = %s",
            (image_url, event_id)
        )
        connection.commit()
        return jsonify({
            "success": True,
            "message": "Image uploaded successfully!",
            "image_path": image_url
        }), 200
    except (mysql.connector.Error, OSError):
        app.logger.exception("Image upload failed")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({
            "success": False,
            "message": "Could not upload image."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route("/api/events/<int:event_id>", methods=["GET"])
def get_event_details(event_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                event_id,
                title,
                category,
                CAST(event_date AS CHAR) AS event_date,
                LEFT(CAST(event_time AS CHAR), 5) AS event_time,
                location,
                description,
                max_participants,
                image_path,
                ticket_price
            FROM events
            WHERE event_id = %s
              AND status = 'published'
        """, (event_id,))
        event = cursor.fetchone()
        if not event:
            return jsonify({
                "success": False,
                "message": "Event not found."
            }), 404
        return jsonify({
            "success": True,
            "event": event
        }), 200
    except mysql.connector.Error:
        app.logger.exception("Event details error")
        return jsonify({
            "success": False,
            "message": "Could not load event."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route("/event-details.html")
def event_details_page():
    return send_from_directory(".", "event-details.html")

@app.route("/api/bookings", methods=["POST"])
def create_booking():
    from datetime import datetime
    # Check participant login
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login to book an event."
        }), 401
    if session.get("role") != "user":
        return jsonify({
            "success": False,
            "message": "Only participants can book events."
        }), 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid booking request."
        }), 400
    event_id = data.get("event_id")
    if type(event_id) is not int or event_id <= 0:
        return jsonify({
            "success": False,
            "message": "Invalid event ID."
        }), 400
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        connection.start_transaction()
        cursor = connection.cursor()
        # Lock event while checking capacity
        cursor.execute("""
            SELECT event_id, max_participants, status,
                   TIMESTAMP(event_date, event_time), ticket_price
            FROM events
            WHERE event_id = %s
            FOR UPDATE
        """, (event_id,))
        event = cursor.fetchone()
        if not event or event[2] != "published":
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Event is not available."
            }), 404
        if event[3] <= datetime.now():
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "This event has already started."
            }), 400
        # A paid ticket can only be created through the demo checkout route.
        # This check is on the server, not just a hidden browser button.
        if Decimal(str(event[4])) > 0:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Paid event: please use the demo checkout."
            }), 402
        # Check existing booking
        cursor.execute("""
            SELECT booking_id, status
            FROM bookings
            WHERE user_id = %s AND event_id = %s
            FOR UPDATE
        """, (session["user_id"], event_id))
        existing = cursor.fetchone()
        if existing and existing[1] == "confirmed":
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "You have already booked this event."
            }), 409
        # Check available seats
        cursor.execute("""
            SELECT COUNT(*)
            FROM bookings
            WHERE event_id = %s AND status = 'confirmed'
        """, (event_id,))
        booked_count = cursor.fetchone()[0]
        if booked_count >= event[1]:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Sorry, this event is full."
            }), 409
        if existing:
            # Allow previously cancelled booking to be rebooked
            booking_id = existing[0]
            cursor.execute("""
                UPDATE bookings
                SET status = 'confirmed',
                    booking_date = CURRENT_TIMESTAMP
                WHERE booking_id = %s
            """, (booking_id,))
        else:
            cursor.execute("""
                INSERT INTO bookings (user_id, event_id, status)
                VALUES (%s, %s, 'confirmed')
            """, (session["user_id"], event_id))
            booking_id = cursor.lastrowid
        connection.commit()
        return jsonify({
            "success": True,
            "message": "Booking confirmed successfully!",
            "booking_id": booking_id
        }), 201
    except mysql.connector.Error:
        if connection and connection.is_connected():
            connection.rollback()
        app.logger.exception("Booking failed")
        return jsonify({
            "success": False,
            "message": "Could not complete booking."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route("/api/my-bookings", methods=["GET"])
def my_bookings():
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401
    if session.get("role") != "user":
        return jsonify({
            "success": False,
            "message": "Only participants can view bookings."
        }), 403
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                b.booking_id,
                b.status,
                LEFT(CAST(b.booking_date AS CHAR), 16) AS booking_date,
                e.event_id,
                e.title,
                e.category,
                CAST(e.event_date AS CHAR) AS event_date,
                LEFT(CAST(e.event_time AS CHAR), 5) AS event_time,
                e.location,
                e.image_path,
                e.ticket_price
            FROM bookings b
            JOIN events e
                ON b.event_id = e.event_id
            WHERE b.user_id = %s
            ORDER BY b.booking_date DESC
        """, (session["user_id"],))
        bookings = cursor.fetchall()
        return jsonify({
            "success": True,
            "bookings": bookings
        }), 200
    except mysql.connector.Error:
        app.logger.exception("Failed to load bookings")
        return jsonify({
            "success": False,
            "message": "Could not load bookings."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route("/my-bookings.html")
def my_bookings_page():
    if "user_id" not in session:
        return redirect("/login.html")
    if session.get("role") != "user":
        return "Access denied: Participants only.", 403
    return send_from_directory(".", "my-bookings.html")

@app.route("/api/auth/status", methods=["GET"])
def auth_status():
    if "user_id" not in session:
        return jsonify({
            "logged_in": False,
            "role": None
        })
    return jsonify({
        "logged_in": True,
        "role": session.get("role"),
        "name": session.get("name", "")
    })

@app.route("/api/bookings/<int:booking_id>/cancel", methods=["POST"])
def cancel_booking(booking_id):
    from datetime import datetime
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401
    if session.get("role") != "user":
        return jsonify({
            "success": False,
            "message": "Participants only."
        }), 403
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        connection.start_transaction()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT b.status,
                   TIMESTAMP(e.event_date, e.event_time)
            FROM bookings b
            JOIN events e ON b.event_id = e.event_id
            WHERE b.booking_id = %s AND b.user_id = %s
            FOR UPDATE
        """, (booking_id, session["user_id"]))
        booking = cursor.fetchone()
        if not booking:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Booking not found."
            }), 404
        if booking[0] == "cancelled":
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Booking already cancelled."
            }), 409
        if booking[1] <= datetime.now():
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Cannot cancel an event that has started."
            }), 400
        cursor.execute("""
            UPDATE bookings
            SET status = 'cancelled'
            WHERE booking_id = %s AND user_id = %s
        """, (booking_id, session["user_id"]))
        connection.commit()
        return jsonify({
            "success": True,
            "message": "Booking cancelled successfully!"
        }), 200
    except mysql.connector.Error:
        if connection and connection.is_connected():
            connection.rollback()
        app.logger.exception("Booking cancellation failed")
        return jsonify({
            "success": False,
            "message": "Could not cancel booking."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route("/ticket.html")
def ticket_page():
    if "user_id" not in session:
        return redirect("/login.html")
    if session.get("role") != "user":
        return "Access denied: Participants only.", 403
    return send_from_directory(".", "ticket.html")

@app.route("/api/tickets/<int:booking_id>/qr")
def generate_ticket_qr(booking_id):
    import qrcode
    from io import BytesIO
    from itsdangerous import URLSafeSerializer
    from flask import send_file
    if "user_id" not in session:
        return jsonify({
            "message": "Please login first."
        }), 401
    if session.get("role") != "user":
        return jsonify({
            "message": "Participants only."
        }), 403
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT b.booking_id
            FROM bookings b
            JOIN events e ON b.event_id = e.event_id
            WHERE b.booking_id = %s
              AND b.user_id = %s
              AND b.status = 'confirmed'
              AND e.status = 'published'
        """, (booking_id, session["user_id"]))
        if cursor.fetchone() is None:
            return jsonify({
                "message": "Valid ticket not found."
            }), 404
        signer = URLSafeSerializer(
            app.secret_key,
            salt="eventhub-ticket-v1"
        )
        token = signer.dumps({
            "booking_id": booking_id
        })
        verification_url = (
            request.host_url.rstrip("/")
            + "/verify-ticket/"
            + token
        )
        qr = qrcode.make(verification_url)
        image = BytesIO()
        qr.save(image, format="PNG")
        image.seek(0)
        return send_file(
            image,
            mimetype="image/png"
        )
    except mysql.connector.Error:
        app.logger.exception("QR generation failed")
        return jsonify({
            "message": "Could not generate QR code."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route("/verify-ticket/<token>")
def verify_ticket(token):
    from itsdangerous import URLSafeSerializer, BadSignature
    from flask import render_template_string
    signer = URLSafeSerializer(
        app.secret_key,
        salt="eventhub-ticket-v1"
    )
    # Check QR verification signature
    try:
        data = signer.loads(token)
    except BadSignature:
        data = None
    booking_id = (
        data.get("booking_id")
        if isinstance(data, dict)
        else None
    )
    valid = False
    event_name = ""
    if type(booking_id) is int and booking_id > 0:
        connection = None
        cursor = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("""
                SELECT e.title, b.status, e.status
                FROM bookings b
                JOIN events e ON b.event_id = e.event_id
                WHERE b.booking_id = %s
            """, (booking_id,))
            booking = cursor.fetchone()
            if booking:
                event_name = booking[0]
                valid = (
                    booking[1] == "confirmed"
                    and booking[2] == "published"
                )
        except mysql.connector.Error:
            app.logger.exception("Ticket verification failed")
            return "Verification temporarily unavailable.", 500
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1">
        <title>Ticket Verification | EventHub</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f3f4ff;
                text-align: center;
                padding: 60px 20px;
            }
            .card {
                background: white;
                max-width: 450px;
                margin: auto;
                padding: 40px 25px;
                border-radius: 18px;
                box-shadow: 0 8px 30px #0001;
            }
            h2 { color: #4935df; }
            .valid { color: #15803d; }
            .invalid { color: #dc2626; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>EventHub</h2>
            {% if valid %}
                <h1 class="valid">✅ Valid Ticket</h1>
                <p><strong>{{ event_name }}</strong></p>
                <p>Booking ID: #{{ booking_id }}</p>
                <p>Status: Confirmed</p>
            {% else %}
                <h1 class="invalid">❌ Invalid Ticket</h1>
                <p>This ticket is invalid or cancelled.</p>
            {% endif %}
        </div>
    </body>
    </html>
    """,
        valid=valid,
        event_name=event_name,
        booking_id=booking_id
    ), 200 if valid else 404

@app.route("/organizer/dashboard.html")
def organizer_dashboard():
    if "user_id" not in session:
        return redirect("/login.html")
    if session.get("role") != "organizer":
        return "Access denied: Organizers only.", 403
    return send_from_directory(
        "organizer", "dashboard.html"
    )

@app.route("/api/organizer/events", methods=["GET"])
def organizer_events():
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401
    if session.get("role") != "organizer":
        return jsonify({
            "success": False,
            "message": "Organizers only."
        }), 403
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                e.event_id,
                e.title,
                e.category,
                CAST(e.event_date AS CHAR) AS event_date,
                LEFT(CAST(e.event_time AS CHAR), 5) AS event_time,
                e.location,
                e.status,
                e.image_path,
                (SELECT COUNT(*)
                 FROM bookings b
                 WHERE b.event_id = e.event_id
                   AND b.status = 'confirmed')
                    AS booking_count,
                CASE
                    WHEN e.status = 'published'
                     AND TIMESTAMP(
                         e.event_date,
                         e.event_time
                     ) > NOW()
                    THEN 1
                    ELSE 0
                END AS is_upcoming
            FROM events e
            WHERE e.organizer_id = %s
            ORDER BY e.event_date DESC
        """, (session["user_id"],))
        events = cursor.fetchall()
        return jsonify({
            "success": True,
            "events": events,
            "stats": {
                "my_events": len(events),
                "total_bookings": sum(
                    e["booking_count"] for e in events
                ),
                "upcoming_events": sum(
                    e["is_upcoming"] for e in events
                )
            }
        }), 200
    except mysql.connector.Error:
        app.logger.exception("Organizer events error")
        return jsonify({
            "success": False,
            "message": "Could not load organizer events."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route("/organizer/add-event.html")
def organizer_add_event_page():
    if "user_id" not in session:
        return redirect("/login.html")
    if session.get("role") != "organizer":
        return "Access denied: Organizers only.", 403
    return send_from_directory(
        "organizer", "add-event.html"
    )

@app.route("/organizer/admin.css")
def organizer_stylesheet():
    if session.get("role") != "organizer":
        return "Access denied.", 403
    return send_from_directory("admin", "admin.css")

@app.route("/organizer/add-event.js")
def organizer_event_script():
    if session.get("role") != "organizer":
        return "Access denied.", 403
    return send_from_directory("admin", "add-event.js")
# =========================================
# ORGANIZER - EVENT MANAGEMENT
# =========================================

@app.route("/organizer/manage-events.html")
def organizer_manage_events_page():
    if "user_id" not in session:
        return redirect("/login.html")
    if session.get("role") != "organizer":
        return "Access denied: Organizers only.", 403
    return send_from_directory(
        "organizer", "manage-events.html"
    )

@app.route(
    "/api/organizer/management/<int:event_id>",
    methods=["GET", "PUT", "DELETE"]
)
def organizer_manage_event(event_id):
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401
    if session.get("role") != "organizer":
        return jsonify({
            "success": False,
            "message": "Organizers only."
        }), 403
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        # Detect participant-limit column if available
        cursor.execute("SHOW COLUMNS FROM events")
        columns = {row["Field"] for row in cursor.fetchall()}
        capacity_column = next(
            (
                name for name in (
                    "max_participants",
                    "capacity",
                    "participant_limit"
                )
                if name in columns
            ),
            None
        )
        capacity_sql = (
            f", `{capacity_column}` AS max_participants"
            if capacity_column
            else ", NULL AS max_participants"
        )
        cursor.execute(f"""
            SELECT
                event_id,
                title,
                category,
CAST(event_date AS CHAR) AS event_date,
LEFT(CAST(event_time AS CHAR), 5) AS event_time,
                location,
                description,
                status
                {capacity_sql}
            FROM events
            WHERE event_id = %s
              AND organizer_id = %s
            FOR UPDATE
        """, (event_id, session["user_id"]))
        event = cursor.fetchone()
        if not event:
            return jsonify({
                "success": False,
                "message": "Event not found or access denied."
            }), 404
        # View event details
        if request.method == "GET":
            return jsonify({
                "success": True,
                "event": event
            }), 200
        if event["status"] != "published":
            return jsonify({
                "success": False,
                "message": "Only published events can be modified."
            }), 409
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM bookings
            WHERE event_id = %s
              AND status = 'confirmed'
        """, (event_id,))
        confirmed_bookings = cursor.fetchone()["total"]
        # Cancel event and notify participants
        if request.method == "DELETE":
            notification_title = "Event Cancelled"
            notification_message = (
                f"The event '{event['title']}' "
                f"scheduled for {event['event_date']} "
                f"at {event['event_time']} "
                "has been cancelled by the organizer."
            )
            cursor.execute("""
                INSERT INTO notifications
                    (
                        user_id,
                        event_id,
                        notification_type,
                        title,
                        message
                    )
                SELECT
                    b.user_id,
                    %s,
                    'event_cancelled',
                    %s,
                    %s
                FROM bookings b
                WHERE b.event_id = %s
                  AND b.status = 'confirmed'
            """, (
                event_id,
                notification_title,
                notification_message,
                event_id
            ))
            cursor.execute("""
                UPDATE bookings
                SET status = 'cancelled'
                WHERE event_id = %s
                  AND status = 'confirmed'
            """, (event_id,))
            cursor.execute("""
                UPDATE events
                SET status = 'cancelled'
                WHERE event_id = %s
                  AND organizer_id = %s
            """, (event_id, session["user_id"]))
            connection.commit()
            return jsonify({
                "success": True,
                "message": (
                    "Event cancelled and participants notified."
                )
            }), 200
        # Edit event
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({
                "success": False,
                "message": "Invalid event data."
            }), 400
        fields = (
            "title",
            "category",
            "event_date",
            "event_time",
            "location",
            "description"
        )
        values = {
            field: str(data.get(field) or "").strip()
            for field in fields
        }
        if any(not value for value in values.values()):
            return jsonify({
                "success": False,
                "message": "Please fill all required fields."
            }), 400
        if (
            len(values["title"]) > 150
            or len(values["category"]) > 80
            or len(values["location"]) > 200
            or len(values["description"]) > 5000
        ):
            return jsonify({
                "success": False,
                "message": "One or more fields are too long."
            }), 400
        from datetime import datetime
        try:
            new_datetime = datetime.strptime(
                values["event_date"] + " " +
                values["event_time"],
                "%Y-%m-%d %H:%M"
            )
        except ValueError:
            return jsonify({
                "success": False,
                "message": "Invalid event date or time."
            }), 400
        if new_datetime <= datetime.now():
            return jsonify({
                "success": False,
                "message": "Event date must be in the future."
            }), 400
        schedule_changed = (
            values["event_date"] != event["event_date"]
            or values["event_time"] != event["event_time"]
            or values["location"] != event["location"]
        )
        if confirmed_bookings > 0 and schedule_changed:
            notification_title = "Event Schedule Updated"
            notification_message = (
                f"The event '{event['title']}' has been updated. "
                f"Previous: {event['event_date']} "
                f"at {event['event_time']}, "
                f"Location: {event['location']}. "
                f"New: {values['event_date']} "
                f"at {values['event_time']}, "
                f"Location: {values['location']}."
            )
            cursor.execute("""
                INSERT INTO notifications
                    (
                        user_id,
                        event_id,
                        notification_type,
                        title,
                        message
                    )
                SELECT
                    b.user_id,
                    %s,
                    'event_updated',
                    %s,
                    %s
                FROM bookings b
                WHERE b.event_id = %s
                  AND b.status = 'confirmed'
            """, (
                event_id,
                notification_title,
                notification_message,
                event_id
            ))
        update_parts = [
            "title = %s",
            "category = %s",
            "event_date = %s",
            "event_time = %s",
            "location = %s",
            "description = %s"
        ]
        update_values = [
            values["title"],
            values["category"],
            values["event_date"],
            values["event_time"],
            values["location"],
            values["description"]
        ]
        if (
            capacity_column
            and data.get("max_participants") is not None
        ):
            try:
                capacity = int(data["max_participants"])
            except (ValueError, TypeError):
                return jsonify({
                    "success": False,
                    "message": "Invalid participant limit."
                }), 400
            if capacity < 1 or capacity < confirmed_bookings:
                return jsonify({
                    "success": False,
                    "message": "Participant limit is too small."
                }), 400
            update_parts.append(
                f"`{capacity_column}` = %s"
            )
            update_values.append(capacity)
        update_values.extend([
            event_id,
            session["user_id"]
        ])
        cursor.execute(f"""
            UPDATE events
            SET {", ".join(update_parts)}
            WHERE event_id = %s
              AND organizer_id = %s
        """, tuple(update_values))
        connection.commit()
        return jsonify({
            "success": True,
            "message": "Event updated successfully."
        }), 200
    except Exception:
        if connection:
            connection.rollback()
        app.logger.exception("Organizer management error")
        return jsonify({
            "success": False,
            "message": "Server error while managing event."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route(
    "/api/organizer/management/<int:event_id>/participants",
    methods=["GET"]
)
def organizer_event_participants(event_id):
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401
    if session.get("role") != "organizer":
        return jsonify({
            "success": False,
            "message": "Organizers only."
        }), 403
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT event_id
            FROM events
            WHERE event_id = %s
              AND organizer_id = %s
        """, (event_id, session["user_id"]))
        if not cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "Event not found or access denied."
            }), 404
        # Support either name or full_name in users table
        cursor.execute("SHOW COLUMNS FROM users")
        user_columns = {
            row["Field"]
            for row in cursor.fetchall()
        }
        if "full_name" in user_columns:
            name_sql = "u.full_name"
        elif "name" in user_columns:
            name_sql = "u.name"
        elif "username" in user_columns:
            name_sql = "u.username"
        else:
            name_sql = "CAST(u.user_id AS CHAR)"
        cursor.execute(f"""
            SELECT
                b.booking_id,
                b.status,
                {name_sql} AS participant_name,
                u.email
            FROM bookings b
            JOIN users u
                ON b.user_id = u.user_id
            WHERE b.event_id = %s
            ORDER BY b.booking_id DESC
        """, (event_id,))
        participants = cursor.fetchall()
        return jsonify({
            "success": True,
            "participants": participants
        }), 200
    except Exception:
        app.logger.exception("Participants API error")
        return jsonify({
            "success": False,
            "message": "Could not load participants."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
# ========================================
# PARTICIPANT NOTIFICATIONS
# ========================================

@app.route("/notifications.html")
def participant_notifications_page():
    if "user_id" not in session:
        return redirect("/login.html")
    if session.get("role") != "user":
        return "Participants only.", 403
    return send_from_directory(".", "notifications.html")

@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login."
        }), 401
    if session.get("role") != "user":
        return jsonify({
            "success": False,
            "message": "Participants only."
        }), 403
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                notification_id,
                event_id,
                notification_type,
                title,
                message,
                is_read,
CAST(created_at AS CHAR) AS created_at
            FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC, notification_id DESC
            LIMIT 100
""", (session["user_id"],))
        notifications = cursor.fetchall()
        return jsonify({
            "success": True,
            "notifications": notifications,
            "unread_count": sum(
                1 for n in notifications if not n["is_read"]
            )
        }), 200
    except Exception:
        app.logger.exception("Notifications load error")
        return jsonify({
            "success": False,
            "message": "Could not load notifications."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route(
    "/api/notifications/<int:notification_id>/read",
    methods=["POST"]
)
def mark_notification_read(notification_id):
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login."
        }), 401
    if session.get("role") != "user":
        return jsonify({
            "success": False,
            "message": "Participants only."
        }), 403
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE notifications
            SET is_read = 1
            WHERE notification_id = %s
              AND user_id = %s
        """, (
            notification_id,
            session["user_id"]
        ))
        if cursor.rowcount == 0:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Notification not found."
            }), 404
        connection.commit()
        return jsonify({
            "success": True,
            "message": "Notification marked as read."
        }), 200
    except Exception:
        if connection:
            connection.rollback()
        app.logger.exception("Notification update error")
        return jsonify({
            "success": False,
            "message": "Could not update notification."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
# ==============================================
# ADMIN EVENT CONTROL
# ==============================================
from datetime import datetime

@app.route("/admin/event-control.html")
def admin_event_control_page():
    if "user_id" not in session:
        return redirect("/login.html")
    if session.get("role") != "admin":
        return "Admins only.", 403
    return send_from_directory(
        "admin", "event-control.html"
    )

@app.route("/api/admin/control/events", methods=["GET"])
def admin_control_list_events():
    if session.get("role") != "admin":
        return jsonify({
            "success": False,
            "message": "Admins only."
        }), 403
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                e.event_id,
                e.title,
                e.category,
                CAST(e.event_date AS CHAR) AS event_date,
                LEFT(CAST(e.event_time AS CHAR), 5)
                    AS event_time,
                e.location,
                e.description,
                e.status,
                (
                    SELECT COUNT(*)
                    FROM bookings b
                    WHERE b.event_id = e.event_id
                      AND b.status = 'confirmed'
                ) AS booking_count
            FROM events e
            ORDER BY e.event_date DESC, e.event_id DESC
        """)
        events = cursor.fetchall()
        return jsonify({
            "success": True,
            "events": events
        }), 200
    except Exception:
        app.logger.exception("Admin events error")
        return jsonify({
            "success": False,
            "message": "Could not load events."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route(
    "/api/admin/control/events/<int:event_id>",
    methods=["PUT", "DELETE"]
)
def admin_control_modify_event(event_id):
    if session.get("role") != "admin":
        return jsonify({
            "success": False,
            "message": "Admins only."
        }), 403
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        connection.autocommit = False
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                title,
                CAST(event_date AS CHAR) AS event_date,
                LEFT(CAST(event_time AS CHAR), 5)
                    AS event_time,
                location,
                status
            FROM events
            WHERE event_id = %s
            FOR UPDATE
        """, (event_id,))
        old = cursor.fetchone()
        if not old:
            return jsonify({
                "success": False,
                "message": "Event not found."
            }), 404
        if old["status"] != "published":
            return jsonify({
                "success": False,
                "message": "Only published events can be modified."
            }), 409
        # Cancel an event
        if request.method == "DELETE":
            message = (
                f"The event '{old['title']}' scheduled for "
                f"{old['event_date']} at "
                f"{old['event_time']} has been "
                "cancelled by the administrator."
            )
            cursor.execute("""
                INSERT INTO notifications (
                    user_id,
                    event_id,
                    notification_type,
                    title,
                    message
                )
                SELECT
                    user_id,
                    %s,
                    'event_cancelled',
                    'Event Cancelled',
                    %s
                FROM bookings
                WHERE event_id = %s
                  AND status = 'confirmed'
            """, (event_id, message, event_id))
            cursor.execute("""
                UPDATE bookings
                SET status = 'cancelled'
                WHERE event_id = %s
                  AND status = 'confirmed'
            """, (event_id,))
            cursor.execute("""
                UPDATE events
                SET status = 'cancelled'
                WHERE event_id = %s
            """, (event_id,))
            connection.commit()
            return jsonify({
                "success": True,
                "message": "Event cancelled. Participants notified."
            }), 200
        # Edit an event
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({
                "success": False,
                "message": "Invalid event data."
            }), 400
        fields = (
            "title", "category", "event_date",
            "event_time", "location", "description"
        )
        values = {
            key: str(data.get(key) or "").strip()
            for key in fields
        }
        if any(not value for value in values.values()):
            return jsonify({
                "success": False,
                "message": "All fields are required."
            }), 400
        limits = {
            "title": 150,
            "category": 80,
            "location": 200,
            "description": 5000
        }
        if any(
            len(values[key]) > maximum
            for key, maximum in limits.items()
        ):
            return jsonify({
                "success": False,
                "message": "One or more fields are too long."
            }), 400
        try:
            new_date = datetime.strptime(
                values["event_date"] + " " +
                values["event_time"],
                "%Y-%m-%d %H:%M"
            )
        except ValueError:
            return jsonify({
                "success": False,
                "message": "Invalid date or time."
            }), 400
        if new_date <= datetime.now():
            return jsonify({
                "success": False,
                "message": "Event must be in the future."
            }), 400
        schedule_changed = (
            values["event_date"] != old["event_date"]
            or values["event_time"] != old["event_time"]
            or values["location"] != old["location"]
        )
        if schedule_changed:
            message = (
                f"The event '{old['title']}' has changed. "
                f"Previous: {old['event_date']} at "
                f"{old['event_time']}, "
                f"Location: {old['location']}. "
                f"New: {values['event_date']} at "
                f"{values['event_time']}, "
                f"Location: {values['location']}."
            )
            cursor.execute("""
                INSERT INTO notifications (
                    user_id,
                    event_id,
                    notification_type,
                    title,
                    message
                )
                SELECT
                    user_id,
                    %s,
                    'event_updated',
                    'Event Schedule Updated',
                    %s
                FROM bookings
                WHERE event_id = %s
                  AND status = 'confirmed'
            """, (event_id, message, event_id))
        cursor.execute("""
            UPDATE events
            SET
                title = %s,
                category = %s,
                event_date = %s,
                event_time = %s,
                location = %s,
                description = %s
            WHERE event_id = %s
        """, (
            values["title"],
            values["category"],
            values["event_date"],
            values["event_time"],
            values["location"],
            values["description"],
            event_id
        ))
        connection.commit()
        return jsonify({
            "success": True,
            "message": "Event updated successfully."
        }), 200
    except Exception:
        if connection:
            connection.rollback()
        app.logger.exception("Admin event modification error")
        return jsonify({
            "success": False,
            "message": "Could not modify event."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route(
    "/api/admin/control/events/<int:event_id>/participants",
    methods=["GET"]
)
def admin_control_participants(event_id):
    if session.get("role") != "admin":
        return jsonify({
            "success": False,
            "message": "Admins only."
        }), 403
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT event_id
            FROM events
            WHERE event_id = %s
        """, (event_id,))
        if not cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "Event not found."
            }), 404
        cursor.execute("""
            SELECT
                b.booking_id,
                b.status,
                u.email
            FROM bookings b
            JOIN users u ON u.user_id = b.user_id
            WHERE b.event_id = %s
            ORDER BY b.booking_id DESC
        """, (event_id,))
        return jsonify({
            "success": True,
            "participants": cursor.fetchall()
        }), 200
    except Exception:
        app.logger.exception("Admin participants error")
        return jsonify({
            "success": False,
            "message": "Could not load participants."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

# ================================================================
# DEMO-ONLY TICKET PRICING AND CHECKOUT
# These routes DO NOT charge real cards, accounts, or money.
# ================================================================

@app.route("/event-prices.html")
def event_prices_page():
    if "user_id" not in session:
        return redirect("/login.html")
    if session.get("role") not in ("admin", "organizer"):
        return "Access denied.", 403
    return send_from_directory(".", "event-prices.html")


@app.route("/pay-demo.html")
def pay_demo_page():
    if "user_id" not in session:
        return redirect("/login.html")
    if session.get("role") != "user":
        return "Participants only.", 403
    return send_from_directory(".", "pay-demo.html")


@app.route("/api/demo-payment/event/<int:event_id>", methods=["GET"])
def demo_payment_event(event_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT event_id, title, status, ticket_price
            FROM events WHERE event_id = %s
        """, (event_id,))
        event = cursor.fetchone()
        if event is None:
            return jsonify({
                "success": False,
                "message": "Event not found."
            }), 404
        return jsonify({
            "success": True,
            "event_id": event_id,
            "title": event["title"],
            "status": event["status"],
            "price": float(event["ticket_price"]),
            "currency": "LKR"
        }), 200
    except mysql.connector.Error:
        app.logger.exception("Demo event price lookup failed")
        return jsonify({
            "success": False,
            "message": "Could not load event price."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route(
    "/api/demo-payment/event/<int:event_id>/price", methods=["POST"]
)
def set_demo_event_price(event_id):
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401
    if session.get("role") not in ("admin", "organizer"):
        return jsonify({
            "success": False,
            "message": "Admins and organizers only."
        }), 403

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid price request."
        }), 400
    try:
        price = Decimal(str(data.get("price")))
        if (
            not price.is_finite()
            or price < 0
            or price > Decimal("999999.99")
            or price.as_tuple().exponent < -2
        ):
            raise ValueError()
    except (InvalidOperation, ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Enter a valid LKR ticket price."
        }), 400

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT event_id, organizer_id, status
            FROM events WHERE event_id = %s FOR UPDATE
        """, (event_id,))
        event = cursor.fetchone()
        if not event:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Event not found."
            }), 404
        if (
            session["role"] == "organizer"
            and event["organizer_id"] != session["user_id"]
        ):
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "You cannot change another organizer's event."
            }), 403
        if event["status"] != "published":
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Only published events can be priced."
            }), 409
        cursor.execute("""
            SELECT COUNT(*) AS total FROM bookings
            WHERE event_id = %s AND status = 'confirmed'
        """, (event_id,))
        if cursor.fetchone()["total"] > 0:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Price cannot change after confirmed bookings."
            }), 409
        cursor.execute("""
            UPDATE events SET ticket_price = %s WHERE event_id = %s
        """, (price, event_id))
        connection.commit()
        return jsonify({
            "success": True,
            "message": "Ticket price saved successfully."
        }), 200
    except mysql.connector.Error:
        if connection and connection.is_connected():
            connection.rollback()
        app.logger.exception("Demo ticket price update failed")
        return jsonify({
            "success": False,
            "message": "Could not save ticket price."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route("/api/demo-payment/pay", methods=["POST"])
def complete_demo_payment():
    # Explicit simulation: creates a demo payment record only.
    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401
    if session.get("role") != "user":
        return jsonify({
            "success": False,
            "message": "Participants only."
        }), 403

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or type(data.get("event_id")) is not int:
        return jsonify({
            "success": False,
            "message": "Invalid event ID."
        }), 400
    event_id = data["event_id"]
    if event_id <= 0:
        return jsonify({
            "success": False,
            "message": "Invalid event ID."
        }), 400

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        connection.start_transaction()
        cursor = connection.cursor(dictionary=True)
        # Lock the event to avoid two checkouts consuming the final seat.
        cursor.execute("""
            SELECT event_id, status, max_participants, ticket_price,
                   TIMESTAMP(event_date, event_time) AS starts_at
            FROM events WHERE event_id = %s FOR UPDATE
        """, (event_id,))
        event = cursor.fetchone()
        if not event or event["status"] != "published":
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Event unavailable."
            }), 404
        if event["starts_at"] <= datetime.now():
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "This event has already started."
            }), 409
        if Decimal(str(event["ticket_price"])) <= 0:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "This is a free event. Use Book Now."
            }), 400

        cursor.execute("""
            SELECT booking_id, status FROM bookings
            WHERE user_id = %s AND event_id = %s FOR UPDATE
        """, (session["user_id"], event_id))
        existing = cursor.fetchone()
        if existing and existing["status"] == "confirmed":
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "You already booked this event."
            }), 409
        cursor.execute("""
            SELECT COUNT(*) AS total FROM bookings
            WHERE event_id = %s AND status = 'confirmed'
        """, (event_id,))
        if cursor.fetchone()["total"] >= event["max_participants"]:
            connection.rollback()
            return jsonify({
                "success": False,
                "message": "Event is fully booked."
            }), 409

        if existing:
            booking_id = existing["booking_id"]
            cursor.execute("""
                UPDATE bookings
                SET status = 'confirmed', booking_date = CURRENT_TIMESTAMP
                WHERE booking_id = %s AND user_id = %s
            """, (booking_id, session["user_id"]))
        else:
            cursor.execute("""
                INSERT INTO bookings (user_id, event_id, status)
                VALUES (%s, %s, 'confirmed')
            """, (session["user_id"], event_id))
            booking_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO demo_payments
                (user_id, event_id, booking_id, amount, status)
            VALUES (%s, %s, %s, %s, 'demo_paid')
        """, (
            session["user_id"], event_id,
            booking_id, event["ticket_price"]
        ))
        connection.commit()
        return jsonify({
            "success": True,
            "message": "Demo checkout completed (no real charge).",
            "booking_id": booking_id,
            "payment_status": "demo_paid"
        }), 201
    except mysql.connector.Error:
        if connection and connection.is_connected():
            connection.rollback()
        app.logger.exception("Demo checkout failed")
        return jsonify({
            "success": False,
            "message": "Demo checkout failed. Check demo_payments table."
        }), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route("/events.html")
def all_events_page():
    return send_from_directory(app.root_path, "events.html")


# EventHub Admin Dashboard - live statistics (protected, read-only)
@app.route("/api/admin/dashboard/stats", methods=["GET"])
def admin_dashboard_stats():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Please log in."}), 401
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Admins only."}), 403

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS total FROM events")
        total_events = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM users")
        total_users = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM bookings")
        total_bookings = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total FROM events
            WHERE status = 'published'
              AND TIMESTAMP(event_date, event_time) > NOW()
        """)
        upcoming_events = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT event_id, title,
                   CAST(event_date AS CHAR) AS event_date,
                   location, status
            FROM events
            WHERE status = 'published'
            ORDER BY created_at DESC, event_id DESC
            LIMIT 5
        """)
        recent_events = cursor.fetchall()

        return jsonify({
            "success": True,
            "total_events": int(total_events),
            "total_users": int(total_users),
            "total_bookings": int(total_bookings),
            "upcoming_events": int(upcoming_events),
            "recent_events": recent_events,
        }), 200

    except Exception:
        app.logger.exception("Admin dashboard statistics failed")
        return jsonify({
            "success": False,
            "message": "Could not load dashboard statistics. Check server logs."
        }), 500
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


# -------- EventHub Manage Users (admin-only) --------
@app.route("/admin/manage-users.html", methods=["GET"])
def eventhub_admin_manage_users_page():
    if "user_id" not in session:
        return redirect("/login.html")
    if session.get("role") != "admin":
        return "Access denied: Admins only.", 403
    return send_from_directory("admin", "manage-users.html")


@app.route("/api/admin/users", methods=["GET"])
def eventhub_admin_users_list():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "message": "Admin login required."}), 403
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        # Verify the current admin role against the database (not only the session).
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (session["user_id"],))
        current_admin = cursor.fetchone()
        if not current_admin or current_admin["role"] != "admin":
            return jsonify({"success": False, "message": "Admin access denied."}), 403
        cursor.execute("""
            SELECT user_id, full_name, email, role,
                   CAST(created_at AS CHAR) AS created_at
            FROM users
            ORDER BY user_id ASC
        """)
        return jsonify({"success": True, "users": cursor.fetchall()}), 200
    except Exception:
        app.logger.exception("Manage users: listing failed")
        return jsonify({"success": False, "message": "Unable to load users."}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


@app.route("/api/admin/users/<int:user_id>/role", methods=["PUT"])
def eventhub_admin_user_change_role(user_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "message": "Admin login required."}), 403
    # Require same-origin JavaScript request, not a cross-site form submission.
    if request.headers.get("X-EventHub-Admin") != "role-update":
        return jsonify({"success": False, "message": "Invalid update request."}), 403
    origin = request.headers.get("Origin")
    if origin and origin.rstrip("/") != request.host_url.rstrip("/"):
        return jsonify({"success": False, "message": "Invalid request origin."}), 403
    payload = request.get_json(silent=True)
    role = payload.get("role") if isinstance(payload, dict) else None
    if role not in ("user", "organizer"):
        return jsonify({"success": False, "message": "Role must be Participant or Organizer."}), 400
    if user_id == session["user_id"]:
        return jsonify({"success": False, "message": "You cannot change your own role."}), 403

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (session["user_id"],))
        current_admin = cursor.fetchone()
        if not current_admin or current_admin["role"] != "admin":
            return jsonify({"success": False, "message": "Admin access denied."}), 403
        cursor.execute("SELECT role FROM users WHERE user_id = %s FOR UPDATE", (user_id,))
        target = cursor.fetchone()
        if not target:
            return jsonify({"success": False, "message": "User not found."}), 404
        if target["role"] == "admin":
            return jsonify({"success": False, "message": "Admin accounts are protected."}), 403
        cursor.execute(
            "UPDATE users SET role = %s WHERE user_id = %s AND role IN ('user', 'organizer')",
            (role, user_id),
        )
        connection.commit()
        return jsonify({
            "success": True, "message": "User role updated. The user must sign in again for the new role.",
        }), 200
    except Exception:
        if connection is not None:
            connection.rollback()
        app.logger.exception("Manage users: role update failed")
        return jsonify({"success": False, "message": "Could not update user role."}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
# -------- End EventHub Manage Users --------

if __name__ == "__main__":
    app.run(debug=True)
