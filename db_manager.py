import os
import sqlite3
from contextlib import closing
from datetime import datetime, time, timedelta, timezone


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_NAME = os.path.join(DB_DIR, "tayo_bus.db")
VALID_CCTV_CHANNELS = (1, 2, 3)

os.makedirs(DB_DIR, exist_ok=True)


def get_connection():
    """Open a SQLite connection with row access and foreign keys enabled."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _seed_default_data(conn):
    conn.executemany(
        """
        INSERT OR IGNORE INTO buses (bus_code, plate_number)
        VALUES (?, ?)
        """,
        (
            ("TAYO-01", "DUMMY-001"),
            ("TAYO-02", "DUMMY-002"),
            ("TAYO-03", "DUMMY-003"),
        ),
    )
    conn.executemany(
        """
        INSERT OR IGNORE INTO drivers (driver_code, name)
        VALUES (?, ?)
        """,
        (
            ("DRV-001", "Pak Budi"),
            ("DRV-002", "Pak Joko"),
            ("DRV-003", "Pak Ahmad"),
            ("DRV-004", "Pak Suryo"),
        ),
    )

    shifts = (
        ("Shift 1", "06:00:00", "14:00:00"),
        ("Shift 2", "14:00:00", "22:00:00"),
        ("Shift 3", "22:00:00", "06:00:00"),
    )
    for shift_name, start_time, end_time in shifts:
        exists = conn.execute(
            "SELECT 1 FROM shifts WHERE shift_name = ? LIMIT 1",
            (shift_name,),
        ).fetchone()
        if exists is None:
            conn.execute(
                """
                INSERT INTO shifts (shift_name, start_time, end_time)
                VALUES (?, ?, ?)
                """,
                (shift_name, start_time, end_time),
            )


def init_db():
    """Create the schema, enable WAL, and insert default data if missing."""
    with closing(get_connection()) as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS buses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bus_code TEXT UNIQUE NOT NULL,
                    plate_number TEXT NOT NULL,
                    status TEXT DEFAULT 'Active'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS drivers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS shifts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shift_name TEXT NOT NULL,
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bus_id INTEGER NOT NULL,
                    driver_id INTEGER NOT NULL,
                    shift_id INTEGER NOT NULL,
                    cctv_channel INTEGER NOT NULL,
                    date DATE DEFAULT (DATE('now')),
                    status TEXT DEFAULT 'ON_GOING',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bus_id) REFERENCES buses(id),
                    FOREIGN KEY (driver_id) REFERENCES drivers(id),
                    FOREIGN KEY (shift_id) REFERENCES shifts(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS passenger_counts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    cctv_channel INTEGER NOT NULL,
                    in_count INTEGER DEFAULT 0,
                    out_count INTEGER DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sessions_channel_status
                ON sessions (cctv_channel, status, id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_passenger_counts_session
                ON passenger_counts (session_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_passenger_counts_timestamp
                ON passenger_counts (timestamp)
                """
            )
            _seed_default_data(conn)


def _parse_shift_time(value):
    return time.fromisoformat(str(value))


def _find_current_shift(shifts, current_time):
    for shift in shifts:
        start = _parse_shift_time(shift["start_time"])
        end = _parse_shift_time(shift["end_time"])
        if start <= end:
            is_current = start <= current_time < end
        else:
            is_current = current_time >= start or current_time < end
        if is_current:
            return shift
    raise RuntimeError("No shift is configured for the current time")


def _get_shifts(conn):
    shifts = conn.execute(
        "SELECT id, shift_name, start_time, end_time FROM shifts ORDER BY id"
    ).fetchall()
    if not shifts:
        raise RuntimeError("No shifts are configured; call init_db() first")
    return shifts


def _shift_period_date(now, shift):
    start = _parse_shift_time(shift["start_time"])
    end = _parse_shift_time(shift["end_time"])
    if start > end and now.time() < start:
        return now.date() - timedelta(days=1)
    return now.date()


def get_current_shift(now=None):
    """Return the ID of the shift active at the supplied or current local time."""
    now = now or datetime.now()
    with closing(get_connection()) as conn:
        shift = _find_current_shift(_get_shifts(conn), now.time())
        return shift["id"]


def get_current_shift_id():
    """Backward-compatible alias for get_current_shift()."""
    return get_current_shift()


def _rollover_sessions(conn, now):
    shifts = _get_shifts(conn)
    current_shift = _find_current_shift(shifts, now.time())
    current_shift_id = current_shift["id"]
    shift_date = _shift_period_date(now, current_shift)
    active_sessions = conn.execute(
        """
        SELECT id, bus_id, driver_id, shift_id, cctv_channel, date
        FROM sessions
        WHERE status = 'ON_GOING'
        ORDER BY id DESC
        """
    ).fetchall()

    sessions_by_channel = {}
    for session in active_sessions:
        sessions_by_channel.setdefault(session["cctv_channel"], []).append(session)

    created_count = 0
    for channel, sessions in sessions_by_channel.items():
        current_sessions = [
            session
            for session in sessions
            if session["shift_id"] == current_shift_id
            and session["date"] == shift_date.isoformat()
        ]
        keep_session = current_sessions[0] if current_sessions else None

        for session in sessions:
            if keep_session is None or session["id"] != keep_session["id"]:
                conn.execute(
                    "UPDATE sessions SET status = 'COMPLETED' WHERE id = ?",
                    (session["id"],),
                )

        if keep_session is None:
            previous_session = sessions[0]
            conn.execute(
                """
                INSERT INTO sessions
                    (bus_id, driver_id, shift_id, cctv_channel, date, status)
                VALUES (?, ?, ?, ?, ?, 'ON_GOING')
                """,
                (
                    previous_session["bus_id"],
                    previous_session["driver_id"],
                    current_shift_id,
                    channel,
                    shift_date.isoformat(),
                ),
            )
            created_count += 1
    return created_count

def rollover_sessions(now=None):
    """Complete stale active sessions and open sessions for the current shift."""
    now = now or datetime.now()
    with closing(get_connection()) as conn:
        with conn:
            return _rollover_sessions(conn, now)


def _validate_channel(cctv_channel):
    if (
        isinstance(cctv_channel, bool)
        or not isinstance(cctv_channel, int)
        or cctv_channel not in VALID_CCTV_CHANNELS
    ):
        raise ValueError("cctv_channel must be 1, 2, or 3")


def start_new_session(bus_id, driver_id, cctv_channel, shift_id=None):
    """Membuka sesi operasional baru untuk suatu CCTV / Bus.
    Jika shift_id tidak diisi, sistem akan mencarinya secara otomatis.
    """
    if shift_id is None:
        shift_id = get_current_shift_id()
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # Nonaktifkan sesi sebelumnya untuk CCTV yang sama
    cursor.execute('''
        UPDATE sessions SET status = 'COMPLETED' 
        WHERE cctv_channel = ? AND status = 'ON_GOING'
    ''', (cctv_channel,))
    
    # Buat sesi baru
    cursor.execute('''
        INSERT INTO sessions (bus_id, driver_id, shift_id, cctv_channel, status)
        VALUES (?, ?, ?, ?, 'ON_GOING')
    ''', (bus_id, driver_id, shift_id, cctv_channel))
    
    conn.commit()
    conn.close()


def save_counting_event(cctv_channel, in_increment, out_increment):
    """Save a counting event against the active session for its CCTV channel."""
    _validate_channel(cctv_channel)
    for name, increment in (
        ("in_increment", in_increment),
        ("out_increment", out_increment),
    ):
        if (
            isinstance(increment, bool)
            or not isinstance(increment, int)
            or increment < 0
        ):
            raise ValueError(f"{name} must be a non-negative integer")

    now = datetime.now()
    with closing(get_connection()) as conn:
        with conn:
            _rollover_sessions(conn, now)
            session = conn.execute(
                """
                SELECT id
                FROM sessions
                WHERE cctv_channel = ? AND status = 'ON_GOING'
                ORDER BY id DESC
                LIMIT 1
                """,
                (cctv_channel,),
            ).fetchone()
            cursor = conn.execute(
                """
                INSERT INTO passenger_counts
                    (session_id, cctv_channel, in_count, out_count)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session["id"] if session else None,
                    cctv_channel,
                    in_increment,
                    out_increment,
                ),
            )
            return cursor.lastrowid


def log_counting_event(cctv_channel, in_inc, out_inc):
    """Backward-compatible alias for save_counting_event()."""
    return save_counting_event(cctv_channel, in_inc, out_inc)


def get_today_summary():
    """Return today's total passenger entries and exits across all channels."""
    now = datetime.now()
    today_start = datetime.combine(now.date(), time.min).astimezone(timezone.utc)
    tomorrow_start = datetime.combine(
        now.date() + timedelta(days=1), time.min
    ).astimezone(timezone.utc)
    with closing(get_connection()) as conn:
        with conn:
            _rollover_sessions(conn, now)
            row = conn.execute(
                """
                SELECT
                    COALESCE(SUM(in_count), 0) AS total_in,
                    COALESCE(SUM(out_count), 0) AS total_out
                FROM passenger_counts
                WHERE timestamp >= ? AND timestamp < ?
                """,
                (
                    today_start.strftime("%Y-%m-%d %H:%M:%S"),
                    tomorrow_start.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            ).fetchone()
            return dict(row)


def get_summary_by_cctv(cctv_channel):
    """Return current-shift totals for one CCTV channel."""
    _validate_channel(cctv_channel)
    now = datetime.now()
    with closing(get_connection()) as conn:
        with conn:
            _rollover_sessions(conn, now)
            session = conn.execute(
                """
                SELECT id
                FROM sessions
                WHERE cctv_channel = ? AND status = 'ON_GOING'
                ORDER BY id DESC
                LIMIT 1
                """,
                (cctv_channel,),
            ).fetchone()
            if session is None:
                return {
                    "cctv_channel": cctv_channel,
                    "total_in": 0,
                    "total_out": 0,
                }

            row = conn.execute(
                """
                SELECT
                    COALESCE(SUM(in_count), 0) AS total_in,
                    COALESCE(SUM(out_count), 0) AS total_out
                FROM passenger_counts
                WHERE session_id = ?
                """,
                (session["id"],),
            ).fetchone()
            return {"cctv_channel": cctv_channel, **dict(row)}


def get_live_stats():
    """Return all-time passenger totals grouped by CCTV channel."""
    now = datetime.now()
    with closing(get_connection()) as conn:
        with conn:
            _rollover_sessions(conn, now)
            rows = conn.execute(
                """
                SELECT
                    cctv_channel,
                    SUM(in_count) AS total_in,
                    SUM(out_count) AS total_out
                FROM passenger_counts
                GROUP BY cctv_channel
                ORDER BY cctv_channel
                """
            ).fetchall()
            return [dict(row) for row in rows]


def get_active_session_info(cctv_channel):
    """Return driver, bus, and shift details for a channel's active session."""
    _validate_channel(cctv_channel)
    now = datetime.now()
    with closing(get_connection()) as conn:
        with conn:
            _rollover_sessions(conn, now)
            row = conn.execute(
                """
                SELECT
                    s.id AS session_id,
                    b.bus_code,
                    b.plate_number,
                    d.name AS driver_name,
                    sh.shift_name,
                    s.cctv_channel
                FROM sessions s
                JOIN buses b ON s.bus_id = b.id
                JOIN drivers d ON s.driver_id = d.id
                JOIN shifts sh ON s.shift_id = sh.id
                WHERE s.cctv_channel = ? AND s.status = 'ON_GOING'
                ORDER BY s.id DESC
                LIMIT 1
                """,
                (cctv_channel,),
            ).fetchone()
            return dict(row) if row else None


def get_active_driver_info(cctv_channel):
    """Return the active driver's name, bus code, and shift name."""
    info = get_active_session_info(cctv_channel)
    if info is None:
        return None
    return {
        "driver_name": info["driver_name"],
        "bus_code": info["bus_code"],
        "shift_name": info["shift_name"],
    }


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_NAME}")
