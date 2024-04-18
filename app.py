# Importing necessary modules from Flask and Flask-SocketIO libraries
from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import join_room, leave_room, send, SocketIO

# Importing random and ascii_uppercase from string module
import random
from string import ascii_uppercase

# Creating a Flask application instance
app = Flask(__name__)

# Setting a secret key for the Flask app
app.config["SECRET_KEY"] = "lllololoolololol"

# Creating a SocketIO instance
socketio = SocketIO(app)

# Dictionary to store room information
rooms = {}

# Function to generate a unique room code
def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        if code not in rooms:
            break

    return code

# Route for the home page
@app.route("/", methods=["POST", "GET"])
def home():
    # Clearing the session
    session.clear()

    # Handling form submission
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        # Validation checks
        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)
        if join != False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)

        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")

# Route for the chat room
@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html")

# SocketIO event for client connection
@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return

    join_room(room)
    send({"name": name, "message": "has entered the chat"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

# SocketIO event for client disconnection
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]

    send({"name": name, "message": "has left the chat"}, to=room)
    print(f"{name} left the chat {room}")

# Entry point of the Flask application
if __name__ == "__main__":
    socketio.run(app, debug=True)
