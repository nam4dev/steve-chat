# Importing necessary modules from Flask and Flask-SocketIO libraries
from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import join_room, leave_room, send, SocketIO

# Importing random and ascii_uppercase from string module
import random
from string import ascii_uppercase

# Importing MySQL Connector module for database interaction
import mysql.connector

# Create a Flask application instance
app = Flask(__name__)

# Setting a secret key for session management
app.config["SECRET_KEY"] = "AgnusD3I"

# Creating a SocketIO instance with allowed origins
socketio = SocketIO(app, cors_allowed_origins="https://localhost:5000")

# Establishing a connection to the MySQL database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="AZ26dodo",
    port="3306",
    database="cs50_final"
)

# Creating a cursor object to interact with the database
myCursor = db.cursor()

# Function to generate a unique room code
def generate_unique_code(length):
    """
    Generate a unique room code.

    Args:
        length (int): The length of the room code to be generated.

    Returns:
        str: A unique room code.
    """
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        # Check if the generated code already exists in the database
        myCursor.execute("SELECT * FROM rooms WHERE code = %s", (code,))
        result = myCursor.fetchone()
        if not result:
            break

    return code

# Route for the home page
@app.route("/", methods=["POST", "GET"])
def home():
    """
    Route handler for the home page.

    This route handles form submissions for joining or creating chat rooms.
    """
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
            # Insert new room into the database
            myCursor.execute("INSERT INTO rooms (code, members) VALUES (%s, %s)", (room, 0))
            db.commit()
        elif code:
            # Check if the entered room code exists in the database
            myCursor.execute("SELECT * FROM rooms WHERE code = %s", (code,))
            result = myCursor.fetchone()
            if not result:
                return render_template("home.html", error="Room does not exist.", code=code, name=name)
            room = result[0]

        # Getting user IP address
        ip_address = request.remote_addr

        myCursor.execute("INSERT INTO users (username, room, ip_address) VALUES (%s, %s, %s)", (name, room, ip_address))
        db.commit()

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")

# Route for the chat room
@app.route("/room")
def room():
    """
    Route handler for the chat room.

    This route renders the chat room template and displays chat messages.
    """
    room = session.get("room")
    if room is None or session.get("name") is None:
        return redirect(url_for("home"))

    # Retrieve existing messages for the room from the database
    myCursor.execute("SELECT * FROM messages WHERE room = %s", (room,))
    messages = myCursor.fetchall()

    # Pass room code and messages to the template context
    return render_template("room.html", code=room, messages=messages)

# SocketIO event for receiving messages
@socketio.on("message")
def message(data):
    """
    SocketIO event for receiving messages.

    This event receives messages from clients and broadcasts them to the chat room.
    """
    room = session.get("room")
    if room is None:
        return

    content = {
        "name": session.get("name"),
        "message": data["data"]
    }

    # Insert new message into the database
    myCursor.execute("INSERT INTO messages (room, sender, content) VALUES (%s, %s, %s)", (room, content["name"], content["message"]))
    db.commit()

    send(content, to=room)
    print(f"{session.get('name')} said: {data['data']}")

# SocketIO event for client connection
@socketio.on("connect")
def connect(authorisation):
    """
    SocketIO event for client connection.

    This event handles client connections and updates room membership.
    """
    room = session.get("room")
    name = session.get("name")
    if room is None or name is None:
        return

    # Increment room members count in the database
    myCursor.execute("UPDATE rooms SET members = members + 1 WHERE code = %s", (room,))
    db.commit()

    join_room(room)
    send({"name": name, "messages": "has entered the chat"}, to=room)
    print(f"{name} joined room {room}")

# SocketIO event for client disconnection
@socketio.on("disconnect")
def disconnect():
    """
    SocketIO event for client disconnection.

    This event handles client disconnections and updates room membership.
    """
    room = session.get("room")
    name = session.get("name")
    if room is None or name is None:
        return

    # Decrement room members count in the database
    myCursor.execute("UPDATE rooms SET members = members - 1 WHERE code = %s", (room,))
    db.commit()

    leave_room(room)
    send({"name": name, "messages": "has left the chat"}, to=room)
    print(f"{name} left the chat {room}")

# Entry point of the Flask application
if __name__ == "__main__":
    socketio.run(app, debug=True)
