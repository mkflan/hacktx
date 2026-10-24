import sqlite3

from flask import Flask, jsonify, request

import db

app = Flask(__name__)
db.init_app(app)

@app.route("/")
def index():
    return jsonify(message="Hello from Flask!")

@app.route("/dashboard/<int:user_id>")
def display_user_dashboard(user_id):
    db_conn = db.get_db()

    user = db_conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if user is None:
        return jsonify(error="user not found"), 404

    interests = db_conn.execute("SELECT interests FROM users WHERE id = ?", (user_id)).fetchone()
    interests = [i.strip().lower() for i in interests["interests"].split(",") if i.strip()]
    
    # SERVE WEBPAGE WITH POPULATED DATA

    return

if __name__ == "__main__":
    app.run(debug=True)
