# Berliner Bank

A secure banking web application built for the B207 Cyber Security individual project (Idea 3: Message Authentication Codes).

## Features
- User registration and login with multi-factor authentication
- Password hashing with PBKDF2-HMAC-SHA256 (100,000 iterations, unique salt per user)
- Fund transfers between accounts
- HMAC-SHA256 signed transactions with tamper detection
- Account lockout after 3 failed login attempts
- Profile management and password reset
- Audit logging of all security events

## Tech Stack
Python, Flask, SQLite, Bootstrap

## Setup

python setup.py
python app.py


Then open http://127.0.0.1:5000 in your browser.

## Project Structure
- `app.py` — Flask routes and page templates
- `auth.py` — password hashing, HMAC signing, MFA logic
- `database.py` — database schema and audit logging
- `setup.py` — one-command environment setup
