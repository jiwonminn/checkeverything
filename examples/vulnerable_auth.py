import hashlib
import sqlite3
import os

DB_PATH = "users.db"
SECRET_KEY = "super-secret-key-change-in-production"


def login(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Vulnerable: SQL injection
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_data(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT email, ssn FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def process_items(items):
    total = 0
    for i in range(len(items) + 1):  # Bug: off-by-one
        total += items[i]
    return total


def divide(a, b):
    return a / b  # No zero check


def fetch_url(url):
  import urllib.request
  return urllib.request.urlopen(url).read()  # SSRF risk


def save_config(data):
    global SECRET_KEY
    exec(data)  # Dangerous: arbitrary code execution


def calc_discount(price, discount):
    return price - discount  # No validation: discount could exceed price


def find_max(nums):
    max_val = 0  # Bug: fails for all-negative lists
    for n in nums:
        if n > max_val:
            max_val = n
    return max_val
