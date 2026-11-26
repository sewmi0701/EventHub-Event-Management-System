# EventHub — Web-Based Event Management System

EventHub is an academic, locally hosted event-management application with three user roles: **Administrator**, **Event Organizer**, and **Participant**. It is developed using **Python Flask**, **MySQL**, **HTML**, **CSS**, and **JavaScript**.

> **Important:** Payments are **simulated**. No real payment gateway is connected and no money is charged. The project is intended for local demonstration and coursework, not public production deployment.

## Features

### Administrator
- Sign in to an admin-only dashboard.
- Create events and upload event images.
- List, edit, and cancel events.
- View event bookings/participants.
- Notify affected participants when an event schedule changes or an event is cancelled.

### Event Organizer
- Sign in to an organizer-only dashboard.
- Create events with category, date, time, venue, description, capacity, image, and ticket price (free or paid).
- View statistics and manage owned events.
- Edit or cancel owned events and view their participants.
- Trigger in-app notifications to affected participants for changes/cancellations.

### Participant
- Register and sign in.
- Explore available events and see ticket pricing.
- Book free events, subject to event availability.
- Complete a **demo-only** checkout for paid events.
- View bookings and a QR-code booking confirmation.
- View event-update and cancellation notifications and mark them as read.

## Technology and requirements

- Windows or another OS supporting Python and MySQL
- Python 3.x with `venv` (developed locally using Python 3.14)
- MySQL or MariaDB (e.g., via XAMPP)
- A modern web browser

Python dependencies:

```powershell
pip install Flask mysql-connector-python Werkzeug "qrcode[pil]" itsdangerous
```

If the project contains a dependency lockfile, prefer installing from that file instead.

## Local setup (Windows / PowerShell)

1. Place the source files together in the project root, e.g. `E:\EventHub`.
2. Start MySQL/MariaDB in XAMPP.
3. Create the database `eventhub_db` and import the submitted **`db_structure.sql`** file in phpMyAdmin (it should include the required tables and sample records for the demonstration). Database schema must be exported from the working local database; it is not recreated by this README.
4. Configure `db.py` to use the correct MySQL connection settings for your local machine.
5. Create a virtual environment and install the packages:

```powershell
cd E:\EventHub
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install Flask mysql-connector-python Werkzeug "qrcode[pil]" itsdangerous
```

6. Set a persistent, private `FLASK_SECRET_KEY` environment variable before using the app outside a throwaway local test environment. The key must remain the same between restarts or signed sessions/QR links will become invalid. Do not publish it in source code.
7. Run the application:

```powershell
.\.venv\Scripts\python.exe -m py_compile app.py
.\.venv\Scripts\python.exe app.py
```

8. Open the application: `http://127.0.0.1:5000/`.

If the local service cannot be reached, keep the Flask terminal running and inspect the terminal errors.

## Important local pages

| Page | Local address |
| --- | --- |
| Register | `http://127.0.0.1:5000/` |
| Login | `http://127.0.0.1:5000/login.html` |
| Browse events | `http://127.0.0.1:5000/home.html` |
| Admin dashboard | `http://127.0.0.1:5000/admin/dashboard.html` |
| Organizer dashboard | `http://127.0.0.1:5000/organizer/dashboard.html` |
| Organizer event management | `http://127.0.0.1:5000/organizer/manage-events.html` |
| Demo payment | `/pay-demo.html?id=<event_id>` |
| My bookings | `http://127.0.0.1:5000/my-bookings.html` |
| Notifications | `http://127.0.0.1:5000/notifications.html` |

Admin and organizer routes require accounts with the corresponding roles.

## Database tables

The implementation uses the following tables:

- `users` — accounts, hashed passwords and roles.
- `events` — event details, organizer ownership, image path, status, capacity and `ticket_price`.
- `bookings` — participant/event bookings and status.
- `notifications` — event update/cancellation notifications and read state.
- `demo_payments` — *simulated* payment records linked to bookings.

**Final submission:** provide `db_structure.sql` exported from the local working `eventhub_db`, including table structures and the required sample records. Do **not** publish real users' personal information or private login hashes unnecessarily.

## Demonstration accounts

Do not put actual passwords in a public repository. For a classroom demonstration, create disposable sample users and document their temporary credentials **in the submission copy shared privately with the lecturer**:

| Role | Demo email | Password |
| --- | --- | --- |
| Participant | `participant-test@example.com` | `[enter the test password you set]` |
| Organizer | `organizer-test@example.com` | `[enter the test password you set]` |
| Administrator | `[enter your demo admin email]` | `[enter the demo admin password]` |

Public registration assigns the participant role. Assign test organizer/admin roles only through authorized local database administration or a secured provisioning process.

## Suggested test flow

1. Sign in as organizer and publish a free event and a paid event.
2. Sign in as participant and book the free event.
3. Complete the demo checkout for the paid event and inspect its QR ticket.
4. As organizer, change an event's date/time and check participant notifications.
5. Cancel a disposable test event and verify that affected bookings are cancelled and notifications are saved.
6. As admin, view event listings and participants.

The application must be tested against the specific database and source files on the lecturer's computer before presentation.

## Limitations and security notes

- Demo checkout records a simulated payment; it is **not** proof of a real payment or bank verification.
- QR verification checks a signed booking reference; it is not a one-time entry/check-in system.
- Localhost addresses work only on the computer running Flask unless separately deployed.
- Use a non-default, persistent secret key; never expose Flask's interactive debugger in production.
- Production deployment would also require CSRF protection for session-authenticated actions, secure HTTPS cookies, stronger operational monitoring, and payment-gateway-side verification.
- Refund workflows and real email/WhatsApp delivery are not included.

## Submission checklist

- [ ] Complete HTML/CSS/JavaScript/Python source
- [ ] `db_structure.sql` with tables and appropriate sample records
- [ ] `README.md` with privately supplied disposable demo credentials
- [ ] Short project report (PDF, up to five pages), with screenshots and ER diagram
- [ ] A local run-through on the submission machine
