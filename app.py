import os
import datetime
import sqlite3
from flask import Flask, request, redirect, url_for, session, render_template_string
from markupsafe import escape
from database import get_db, log_event
import auth

app = Flask(__name__)
app.secret_key = "berliner_bank_dev_secret_2025_b207"

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
        return
    

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

