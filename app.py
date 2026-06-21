import os
import datetime
import sqlite3
from flask import Flask, request, redirect, url_for, session, render_template_string
from markupsafe import escape
from database import get_db, log_event
import auth

app = Flask(__name__)
app.secret_key = "berliner_bank_dev_secret_2025_b207"

# --- HTML Template ---
BASE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Berliner Bank</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #f5f4f0;
            --surface: #ffffff;
            --border: #d8d5cc;
            --text: #1a1a18;
            --muted: #6b6860;
            --accent: #1a3a2a;
            --accent-light: #e8f0eb;
            --danger-bg: #fdf0f0;
            --danger: #8b1a1a;
            --warning-bg: #fdf8e8;
            --warning: #7a5c00;
        }
        body {
            background-color: var(--bg);
            color: var(--text);
            font-family: 'IBM Plex Sans', sans-serif;
        }
        .topbar {
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            padding: 0.9rem 0;
        }
        .brand {
            font-family: 'IBM Plex Mono', monospace;
            font-weight: 600;
            font-size: 1.1rem;
            color: var(--accent);
            letter-spacing: -0.02em;
        }
        .brand span {
            color: var(--muted);
            font-weight: 400;
        }
        .card-panel {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 2rem 2.25rem;
        }
        .label {
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--muted);
            margin-bottom: 0.35rem;
        }
        .form-control {
            border: 1px solid var(--border);
            border-radius: 5px;
            font-size: 0.92rem;
            padding: 0.55rem 0.8rem;
            background: var(--bg);
            color: var(--text);
        }
        .form-control:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(26,58,42,0.08);
            background: #fff;
        }
        .btn-primary {
            background: var(--accent);
            color: #fff;
            border: none;
            border-radius: 5px;
            font-weight: 600;
            font-size: 0.9rem;
            padding: 0.6rem 1.25rem;
        }
        .btn-primary:hover { background: #254d38; color: #fff; }
        .btn-ghost {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--muted);
            border-radius: 5px;
            font-size: 0.88rem;
            padding: 0.5rem 1rem;
        }
        .btn-ghost:hover { border-color: var(--accent); color: var(--accent); }
        table th {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--muted);
            border-bottom: 1px solid var(--border) !important;
            padding: 0.6rem 0.75rem;
            background: transparent;
        }
        table td {
            font-size: 0.9rem;
            border-bottom: 1px solid #f0ede6 !important;
            padding: 0.85rem 0.75rem;
            vertical-align: middle;
        }
        .badge-ok {
            background: var(--accent-light);
            color: var(--accent);
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25em 0.6em;
            border-radius: 3px;
        }
        .badge-bad {
            background: var(--danger-bg);
            color: var(--danger);
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25em 0.6em;
            border-radius: 3px;
        }
        .badge-warn {
            background: var(--warning-bg);
            color: var(--warning);
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25em 0.6em;
            border-radius: 3px;
        }
        .mono { font-family: 'IBM Plex Mono', monospace; }
        .divider { border-top: 1px solid var(--border); margin: 1.5rem 0; }
    </style>
</head>
<body>
    <div class="topbar mb-4">
        <div class="container" style="max-width:780px;">
            <div class="d-flex justify-content-between align-items-center">
                <span class="brand">Berliner<span>Bank</span></span>
                {% if 'username' in session %}
                    <span class="mono text-muted" style="font-size:0.78rem;">&#128274; Secure Session</span>
                {% endif %}
            </div>
        </div>
    </div>
    <div class="container pb-5" style="max-width:780px;">
        {{ content | safe }}
    </div>
</body>
</html>
"""


@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("dashboard"))

    form = """
    <div class="row justify-content-center">
    <div class="col-md-7">
    <div class="card-panel">
        <h4 class="fw-bold mb-1">Sign In</h4>
        <p class="text-muted small mb-4">Access your Berliner Bank account securely.</p>

        <form action="/login" method="POST">
            <div class="mb-3">
                <div class="label">Username</div>
                <input type="text" name="username" class="form-control" required autocomplete="off">
            </div>
            <div class="mb-3">
                <div class="label">Password</div>
                <input type="password" name="password" class="form-control" required>
            </div>
            <div class="mb-4">
                <div class="label">MFA Code</div>
                <input type="text" name="mfa_code" class="form-control mono"
                       placeholder="6-digit code" maxlength="6" required autocomplete="off">
            </div>
            <button type="submit" class="btn btn-primary w-100">Sign In</button>
        </form>

        <div class="divider"></div>
        <p class="text-center small text-muted mb-0">
            No account yet? <a href="/register" class="text-dark fw-semibold text-decoration-none">Register here</a>
        </p>
    </div>
    </div>
    </div>
    """
    return render_template_string(BASE, content=form)


@app.route("/register")
def register_page():
    form = """
    <div class="row justify-content-center">
    <div class="col-md-7">
    <div class="card-panel">
        <h4 class="fw-bold mb-1">Open an Account</h4>
        <p class="text-muted small mb-3">Create your secure Berliner Bank profile.</p>

        <div class="p-3 rounded mb-4" style="background:#f0f7f2; border:1px solid #c5dccb; font-size:0.82rem; color:#2d5a3d;">
            <strong>Password rules:</strong> minimum 8 characters, at least one uppercase letter,
            one lowercase letter, and one number.
        </div>

        <form action="/register" method="POST">
            <div class="mb-3">
                <div class="label">Username</div>
                <input type="text" name="username" class="form-control" required autocomplete="off">
            </div>
            <div class="mb-4">
                <div class="label">Password</div>
                <input type="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary w-100">Create Account</button>
        </form>

        <div class="text-center mt-3">
            <a href="/" class="small text-muted text-decoration-none">Back to login</a>
        </div>
    </div>
    </div>
    </div>
    """
    return render_template_string(BASE, content=form)


@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")

    # Basic input validation
    if not username or not password:
        return "Username and password are required.", 400

    if not auth.check_password_strength(password):
        return "Password does not meet the security requirements.", 400

    db = get_db()

    existing = db.execute("SELECT username FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        db.close()
        return "Username already taken.", 409

    pwd_hash, salt = auth.hash_password(password)
    mfa_seed = f"BB_SEED_{os.urandom(8).hex().upper()}"
    created_at = datetime.datetime.now().strftime("%d %b %Y")

    try:
        db.execute(
            "INSERT INTO users (username, password_hash, salt, mfa_seed, balance, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (username, pwd_hash, salt, mfa_seed, 1000.0, created_at)
        )
        db.commit()
        log_event("REGISTER", f"New account created: {username}")
    except sqlite3.Error as e:
        db.rollback()
        db.close()
        return f"Database error during registration: {e}", 500

    mfa_code = auth.get_mfa_code(mfa_seed)
    db.close()

    success = f"""
    <div class="row justify-content-center">
    <div class="col-md-7">
    <div class="card-panel text-center">
        <div style="font-size:2.5rem; margin-bottom:0.75rem;">&#10003;</div>
        <h4 class="fw-bold mb-1">Account Created</h4>
        <p class="text-muted small mb-4">Your Berliner Bank account is ready.</p>

        <div class="p-4 rounded mb-4" style="background:#f0f7f2; border:1px solid #c5dccb; display:inline-block; width:100%;">
            <div class="label mb-2">Your MFA Code</div>
            <div class="mono fw-bold" style="font-size:2.5rem; letter-spacing:0.25em; color:#1a3a2a;">{mfa_code}</div>
            <p class="small text-muted mt-3 mb-0">
                Save this code — you will need to enter it every time you log in.
                It does not change, so keep it somewhere safe.
            </p>
        </div>

        <a href="/" class="btn btn-primary px-4">Go to Login</a>
    </div>
    </div>
    </div>
    """
    return render_template_string(BASE, content=success)


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")
    mfa_code = request.form.get("mfa_code", "").strip()

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if not user:
        log_event("LOGIN_FAIL", f"No account found for: {username}")
        db.close()
        return "Invalid credentials.", 401

    
    if user["locked_until"]:
        lock_expiry = datetime.datetime.fromisoformat(user["locked_until"])
        if datetime.datetime.now() < lock_expiry:
            log_event("LOCKOUT_BLOCKED", f"Login blocked - account locked: {username}")
            db.close()
            remaining = int((lock_expiry - datetime.datetime.now()).total_seconds() / 60) + 1
            return f"Account is locked due to repeated failed logins. Try again in ~{remaining} minute(s).", 423

    
    computed_hash, _ = auth.hash_password(password, user["salt"])
    if computed_hash != user["password_hash"]:
        failures = user["failed_logins"] + 1
        if failures >= 3:
            lockout = (datetime.datetime.now() + datetime.timedelta(minutes=15)).isoformat()
            db.execute(
                "UPDATE users SET failed_logins = ?, locked_until = ? WHERE username = ?",
                (failures, lockout, username)
            )
            log_event("ACCOUNT_LOCKED", f"Account locked after {failures} failures: {username}")
        else:
            db.execute("UPDATE users SET failed_logins = ? WHERE username = ?", (failures, username))
            log_event("LOGIN_FAIL", f"Wrong password for: {username} (attempt {failures})")
        db.commit()
        db.close()
        return "Invalid credentials.", 401

    
    if not auth.verify_mfa(user["mfa_seed"], mfa_code):
        log_event("MFA_FAIL", f"MFA mismatch for: {username}")
        db.close()
        return "Invalid MFA code.", 401

    
    db.execute("UPDATE users SET failed_logins = 0, locked_until = NULL WHERE username = ?", (username,))
    db.commit()
    db.close()

    session["username"] = username
    log_event("LOGIN_OK", f"Session started for: {username}")
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("index"))

    username = session["username"]
    db = get_db()
    user = db.execute("SELECT balance FROM users WHERE username = ?", (username,)).fetchone()
    txns = db.execute(
        "SELECT * FROM transactions WHERE sender = ? OR recipient = ? ORDER BY id DESC",
        (username, username)
    ).fetchall()
    db.close()

    rows = ""
    for t in txns:
        
        valid = auth.verify_transaction(t["sender"], t["recipient"], t["amount"], t["timestamp"], t["mac"])

        sig_badge = '<span class="badge-ok">&#10003; Valid</span>' if valid else '<span class="badge-bad">&#9888; Tampered</span>'

        if t["risk_flag"] == "HIGH_VALUE":
            risk = '<span class="badge-warn">High Value</span>'
        else:
            risk = '<span class="text-muted small">Normal</span>'

        
        ts = t["timestamp"][:16].replace("T", " ")
        rows += f"""
        <tr>
            <td class="text-muted mono" style="font-size:0.82rem;">{ts}</td>
            <td>{escape(t['sender'])} &rarr; {escape(t['recipient'])}</td>
            <td class="fw-semibold mono">&euro;{t['amount']:.2f}</td>
            <td>{risk}</td>
            <td>{sig_badge}</td>
        </tr>
        """

    page = f"""
    <!-- Balance & profile card -->
    <div class="card-panel mb-3">
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <div class="label">Logged in as</div>
                <div class="fw-bold mono" style="font-size:1.1rem;">{username}</div>
            </div>
            <div class="text-end">
                <div class="label">Available Balance</div>
                <div class="fw-bold mono" style="font-size:1.75rem;">&euro;{user['balance']:.2f}</div>
            </div>
        </div>
    </div>

    <!-- Transfer form -->
    <div class="card-panel mb-3">
        <h6 class="fw-bold mb-3">Transfer Funds</h6>
        <form action="/transfer" method="POST">
            <div class="row g-3">
                <div class="col-md-6">
                    <div class="label">Recipient Username</div>
                    <input type="text" name="recipient" class="form-control" required autocomplete="off">
                </div>
                <div class="col-md-6">
                    <div class="label">Amount (&euro;)</div>
                    <input type="number" step="0.01" min="0.01" name="amount" class="form-control" required>
                </div>
                <div class="col-12">
                    <button type="submit" class="btn btn-primary w-100">Sign &amp; Send Transfer</button>
                </div>
            </div>
        </form>
    </div>

    <!-- Transaction history -->
    <div class="card-panel">
        <h6 class="fw-bold mb-3">Transaction History</h6>
        <div class="table-responsive">
            <table class="table mb-0">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Parties</th>
                        <th>Amount</th>
                        <th>Risk</th>
                        <th>MAC Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows if rows else '<tr><td colspan="5" class="text-center text-muted py-4">No transactions yet.</td></tr>'}
                </tbody>
            </table>
        </div>
        <div class="divider mb-0"></div>
        <div class="d-flex justify-content-between pt-3">
            <a href="/profile" class="small text-muted text-decoration-none fw-medium">My Profile</a>
            <a href="/logout" class="small text-danger text-decoration-none fw-medium">Log Out</a>
        </div>
    </div>
    """
    return render_template_string(BASE, content=page)


@app.route("/profile")
def profile():
    if "username" not in session:
        return redirect(url_for("index"))

    username = session["username"]
    db = get_db()
    user = db.execute("SELECT username, balance, created_at FROM users WHERE username = ?", (username,)).fetchone()
    tx_count = db.execute(
        "SELECT COUNT(*) as cnt FROM transactions WHERE sender = ? OR recipient = ?",
        (username, username)
    ).fetchone()["cnt"]
    db.close()

    joined = user["created_at"] if user["created_at"] else "N/A"

    page = f"""
    <div class="row justify-content-center">
    <div class="col-md-8">

    <div class="card-panel mb-3">
        <div class="d-flex justify-content-between align-items-start mb-4">
            <div>
                <h4 class="fw-bold mb-1">My Profile</h4>
                <p class="text-muted small mb-0">Account details and security settings.</p>
            </div>
            <a href="/dashboard" class="btn-ghost btn">← Dashboard</a>
        </div>

        <div class="row g-3 mb-2">
            <div class="col-sm-4">
                <div class="label">Username</div>
                <div class="fw-semibold mono">{escape(username)}</div>
            </div>
            <div class="col-sm-4">
                <div class="label">Account Balance</div>
                <div class="fw-semibold mono">&euro;{user['balance']:.2f}</div>
            </div>
            <div class="col-sm-4">
                <div class="label">Member Since</div>
                <div class="fw-semibold">{joined}</div>
            </div>
        </div>

        <div class="divider"></div>

        <div class="row g-3">
            <div class="col-sm-4">
                <div class="label">Total Transactions</div>
                <div class="fw-semibold">{tx_count}</div>
            </div>
            <div class="col-sm-4">
                <div class="label">MFA Status</div>
                <div><span class="badge-ok">&#10003; Enabled</span></div>
            </div>
            <div class="col-sm-4">
                <div class="label">Account Status</div>
                <div><span class="badge-ok">&#10003; Active</span></div>
            </div>
        </div>
    </div>

    <div class="card-panel">
        <h6 class="fw-bold mb-1">Change Password</h6>
        <p class="text-muted small mb-3">
            You must enter your current MFA code to confirm the change.
        </p>
        <form action="/reset_password" method="POST">
            <div class="mb-3">
                <div class="label">New Password</div>
                <input type="password" name="new_password" class="form-control" required>
            </div>
            <div class="mb-4">
                <div class="label">Confirm New Password</div>
                <input type="password" name="confirm_password" class="form-control" required>
            </div>
            <div class="mb-4">
                <div class="label">MFA Code (required to confirm)</div>
                <input type="text" name="mfa_code" class="form-control mono"
                       placeholder="6-digit code" maxlength="6" required autocomplete="off">
            </div>
            <button type="submit" class="btn btn-primary w-100">Update Password</button>
        </form>
    </div>

    </div>
    </div>
    """
    return render_template_string(BASE, content=page)


@app.route("/reset_password", methods=["POST"])
def reset_password():
    if "username" not in session:
        return redirect(url_for("index"))

    username = session["username"]
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")
    mfa_code = request.form.get("mfa_code", "").strip()

    if new_password != confirm_password:
        return "Passwords do not match.", 400

    if not auth.check_password_strength(new_password):
        return "New password does not meet the security requirements (min 8 chars, uppercase, lowercase, number).", 400

    db = get_db()
    user = db.execute("SELECT mfa_seed FROM users WHERE username = ?", (username,)).fetchone()

    
    if not auth.verify_mfa(user["mfa_seed"], mfa_code):
        log_event("RESET_FAIL", f"Password reset rejected - MFA mismatch for: {username}")
        db.close()
        return "Invalid MFA code. Password was not changed.", 401

    new_hash, new_salt = auth.hash_password(new_password)

    db.execute(
        "UPDATE users SET password_hash = ?, salt = ? WHERE username = ?",
        (new_hash, new_salt, username)
    )
    db.commit()
    db.close()

    log_event("PASSWORD_RESET", f"Password successfully updated for: {username}")

    confirmation = """
    <div class="row justify-content-center">
    <div class="col-md-6">
    <div class="card-panel text-center">
        <div style="font-size:2.5rem; margin-bottom:0.75rem;">&#10003;</div>
        <h4 class="fw-bold mb-1">Password Updated</h4>
        <p class="text-muted small mb-4">Your new password has been saved securely.</p>
        <a href="/dashboard" class="btn btn-primary px-4">Back to Dashboard</a>
    </div>
    </div>
    </div>
    """
    return render_template_string(BASE, content=confirmation)


@app.route("/transfer", methods=["POST"])
def transfer():
    if "username" not in session:
        return redirect(url_for("index"))

    sender = session["username"]
    recipient = request.form.get("recipient", "").strip().lower()

    try:
        amount = float(request.form.get("amount", 0))
    except ValueError:
        return "Invalid amount.", 400

    if amount <= 0:
        return "Amount must be greater than zero.", 400

    if sender == recipient:
        return "Cannot transfer to your own account.", 400

    db = get_db()

    sender_row = db.execute("SELECT balance FROM users WHERE username = ?", (sender,)).fetchone()
    if sender_row["balance"] < amount:
        db.close()
        return "Insufficient balance.", 400

    recipient_row = db.execute("SELECT username FROM users WHERE username = ?", (recipient,)).fetchone()
    if not recipient_row:
        db.close()
        return "Recipient account not found.", 404

   
    risk = "HIGH_VALUE" if amount > 1000.0 else "NORMAL"

    timestamp = datetime.datetime.now().isoformat()

    
    mac = auth.sign_transaction(sender, recipient, amount, timestamp)

    try:
        db.execute("UPDATE users SET balance = balance - ? WHERE username = ?", (amount, sender))
        db.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, recipient))
        db.execute(
            "INSERT INTO transactions (sender, recipient, amount, timestamp, mac, risk_flag) VALUES (?, ?, ?, ?, ?, ?)",
            (sender, recipient, amount, timestamp, mac, risk)
        )
        db.commit()
        log_event("TRANSFER", f"{sender} -> {recipient}: €{amount:.2f} | Risk: {risk}")
    except sqlite3.Error as e:
        db.rollback()
        db.close()
        return f"Transfer failed due to a database error: {e}", 500
    finally:
        db.close()

    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    username = session.get("username", "unknown")
    session.clear()
    log_event("LOGOUT", f"Session ended for: {username}")
    return redirect(url_for("index"))


if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  Berliner Bank - Local Development Server")
    print("  http://127.0.0.1:5000")
    print("=" * 55 + "\n")
    app.run(debug=True, port=5000)
