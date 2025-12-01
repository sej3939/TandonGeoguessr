from flask import Flask, render_template, url_for, redirect, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, timedelta
import mysql.connector
import ssl
app = Flask(__name__)
app.secret_key = "idkstring"
MAX_ROUNDS = 3 #number of rounds per game

# ==========================
# Database Helper
# ==========================

# Connection to Aiven Database stuff
def database():
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    return mysql.connector.connect(
        host="tandongeo-tandongeoguessr.k.aivencloud.com",
        port=12357,
        user="user",
        password="randompass",
        database="defaultdb",)

# ==========================
# User + Game Helper Functions
# ==========================

def currentUser():
    if "user_id" not in session:
        return None
    db = database()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""Select player_id, username from player where player_id = %s""", (session["user_id"],))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        db.close()
        return None
    cursor.execute("""SELECT max(total_score) as best_score from game_session where player_id =%s""",   (session['user_id'],))
    row = cursor.fetchone()
    user["best_score"]= row["best_score"] or 0
    cursor.close()
    db.close()
    return user

# shortcut to get current week
def currentWeek():
    today = date.today()
    weekday = today.weekday()
    daysSinceSunday = (weekday + 1) % 7
    weekStart = today - timedelta(days=daysSinceSunday)
    weekEnd = weekStart + timedelta(days=6)
    return weekStart, weekEnd

def start_new_game():
    user = currentUser()
    if not user:
        return None

    db = database()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """INSERT INTO game_session (player_id, total_score) VALUES (%s, %s)""",
        (user["player_id"], 0),
    )
    session_id = cursor.lastrowid
    db.commit()

    cursor.close()
    db.close()

    session["mode"] = "normal"
    session["current_session_id"] = session_id
    session["current_round"] = 1

    return session_id

def start_custom_game_session(custom_game_id):
    """Create a custom_game_session + load its photo pool into the Flask session."""
    user = currentUser()
    if not user:
        return None

    db = database()
    cursor = db.cursor(dictionary=True)

    # Get the photo pool for this custom game in a stable order
    cursor.execute(
        """
        SELECT cpp.photo_id
        FROM custom_photo_pool cpp
        WHERE cpp.custom_game_id = %s
        ORDER BY cpp.custom_photo_pool_id ASC
        """,
        (custom_game_id,),
    )
    rows = cursor.fetchall()

    if not rows:
        cursor.close()
        db.close()
        return None

    photo_ids = [row["photo_id"] for row in rows]

    # Create a new custom_game_session with total_score = 0
    cursor.execute(
        """
        INSERT INTO custom_game_session (custom_game_id, player_id, total_score)
        VALUES (%s, %s, %s)
        """,
        (custom_game_id, user["player_id"], 0),
    )
    custom_session_id = cursor.lastrowid
    db.commit()

    cursor.close()
    db.close()

    # Remember this custom game in the Flask session
    session["mode"] = "custom"
    session["custom_game_id"] = custom_game_id
    session["custom_session_id"] = custom_session_id
    session["custom_photo_ids"] = photo_ids
    session["custom_max_rounds"] = len(photo_ids)
    session["current_round"] = 1

    return custom_session_id

def start_custom_game(custom_game_id):
    user = currentUser()
    if not user:
        return None

    db = database()
    cursor = db.cursor(dictionary=True)

    # Get the ordered list of photo_ids for this custom game
    cursor.execute("""
        SELECT p.photo_id
        FROM custom_photo_pool AS cp
        JOIN photo AS p ON cp.photo_id = p.photo_id
        WHERE cp.custom_game_id = %s
        ORDER BY p.photo_id
    """, (custom_game_id,))
    rows = cursor.fetchall()

    if not rows:
        cursor.close()
        db.close()
        return None

    photo_ids = [row["photo_id"] for row in rows]

    # Create a new game_session
    cursor.execute(
        """INSERT INTO game_session (player_id, total_score) VALUES (%s, %s)""",
        (user["player_id"], 0),
    )
    session_id = cursor.lastrowid
    db.commit()
    cursor.close()
    db.close()

    # Remember this game in the Flask session
    session["current_session_id"] = session_id
    session["current_round"] = 1
    session["mode"] = "custom"
    session["custom_game_id"] = custom_game_id
    session["custom_photo_ids"] = photo_ids
    session["custom_max_rounds"] = len(photo_ids)

    return session_id

def get_or_create_custom_leaderboard(custom_game_id, cursor):
    """Return custom_leaderboard_id for this game; create row if it doesn't exist."""
    cursor.execute(
        """
        SELECT custom_leaderboard_id
        FROM custom_leaderboard
        WHERE custom_game_id = %s
        ORDER BY custom_leaderboard_id DESC
        LIMIT 1
        """,
        (custom_game_id,),
    )
    row = cursor.fetchone()
    if row:
        return row["custom_leaderboard_id"]

    # Create a simple leaderboard for this custom game
    cursor.execute(
        """
        INSERT INTO custom_leaderboard (custom_game_id, start_date, end_date, entry_count)
        VALUES (%s, NOW(), NULL, 0)
        """,
        (custom_game_id,),
    )
    return cursor.lastrowid

def update_custom_leaderboard(custom_game_id, player_id, total_score):
    """Insert/update the player's best score on this custom game's leaderboard."""
    db = database()
    cursor = db.cursor(dictionary=True)

    custom_leaderboard_id = get_or_create_custom_leaderboard(custom_game_id, cursor)

    # Does this player already have an entry?
    cursor.execute(
        """
        SELECT custom_leaderboard_entry_id, max_score
        FROM custom_leaderboard_entry
        WHERE custom_leaderboard_id = %s AND player_id = %s
        """,
        (custom_leaderboard_id, player_id),
    )
    row = cursor.fetchone()

    if row is None:
        cursor.execute(
            """
            INSERT INTO custom_leaderboard_entry
                (custom_leaderboard_id, player_id, max_score, ranking)
            VALUES (%s, %s, %s, %s)
            """,
            (custom_leaderboard_id, player_id, total_score, 0),
        )
    elif total_score > row["max_score"]:
        cursor.execute(
            """
            UPDATE custom_leaderboard_entry
            SET max_score = %s
            WHERE custom_leaderboard_entry_id = %s
            """,
            (total_score, row["custom_leaderboard_entry_id"]),
        )

    cursor.execute(
        """
        SELECT custom_leaderboard_entry_id
        FROM custom_leaderboard_entry
        WHERE custom_leaderboard_id = %s
        ORDER BY max_score DESC
        """,
        (custom_leaderboard_id,),
    )

    entries = cursor.fetchall()
    rank = 1
    for e in entries:
        cursor.execute(
            """
            UPDATE custom_leaderboard_entry
            SET ranking = %s
            WHERE custom_leaderboard_entry_id = %s
            """,
            (rank, e["custom_leaderboard_entry_id"]),
        )
        rank += 1

    db.commit()
    cursor.close()
    db.close()

# ==========================
# Authentication Routes
# ==========================

@app.route("/signup", methods = ["GET","POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username") 
        email = request.form.get("email")
        raw_password = request.form.get("password")
        hashed_password = generate_password_hash(raw_password)
        db = database()
        cursor = db.cursor(dictionary=True)

        cursor.execute("INSERT INTO player (username, password, email) VALUES (%s, %s, %s)", (username, hashed_password, email))
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for("signin"))
    return render_template("TandonGeoguessrSignUp.html")

@app.route("/signin", methods =["GET","POST"])
def signin():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        raw_password = request.form.get("password")
        db = database()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""SELECT player_id, username, password FROM player where email=%s""",(email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()
        
        # Since we're hashing now, the manually-inserted accounts currently in the db cannot be logged into because their hashed passwords aren't stored.
        if user and check_password_hash(user["password"], raw_password):
            session['user_id']=user['player_id']
            session['username']=user['username']
            return redirect(url_for("home"))
        return render_template("TandonGeoguessrSignIn.html", error = "Wrong Password or Email")
    return render_template("TandonGeoguessrSignIn.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("signin"))


# ==========================
# Normal Game Routes
# ==========================


@app.route("/")
def home():
    user = currentUser()
    if not user:
        return redirect(url_for("signin"))
    weekStart, weekEnd = currentWeek()
    return render_template("TandonGeoguessrHome.html", username = user["username"], best_score = user["best_score"], date1 = weekStart, date2 = weekEnd)

@app.route("/leaderboard")
def leaderboard():
    user = currentUser()
    if not user:
        return redirect(url_for("signin"))
    weekStart, weekEnd = currentWeek()
    db = database()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""SELECT leaderboard_id FROM leaderboard where start_date = %s and end_date = %s""", (weekStart,weekEnd))
    lb = cursor.fetchone()
    if not lb:
        cursor.execute("""INSERT into leaderboard (start_date, end_date) VALUES (%s,%s)""", (weekStart,weekEnd))
        leaderboard_id = cursor.lastrowid
    else:
        leaderboard_id = lb["leaderboard_id"]
    cursor.execute("""SELECT leaderboard_id, start_date, end_date FROM leaderboard order by start_date desc""")
    weeks = cursor.fetchall()
    selectedID = request.args.get("leaderboard_id",type=int)
    if selectedID == None:
        selectedID = leaderboard_id
    selected_week = None
    for w in weeks:
        if w["leaderboard_id"] == selectedID:
            selected_week = w
            break
    cursor.execute("""SELECT p.username, le.max_score FROM leaderboard_entry AS le JOIN player AS p ON le.player_id = p.player_id WHERE le.leaderboard_id =%s ORDER BY le.max_score DESC """, (selectedID,),)
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("TandonGeoguessrLeaderboard.html", username = user["username"], best_score = user["best_score"], data=rows, date1=selected_week["start_date"] , date2=selected_week["end_date"] , weeks = weeks, selected_week = selectedID)

@app.route("/settings", methods=["GET","POST"])
def settings():
    user = currentUser()
    if not user:
        return redirect(url_for("signin"))
    error = None
    success = None
    if request.method == "POST":
        currentPassword = request.form.get("currentPassword")
        newPassword = request.form.get("newPassword")

        #Ensure User does not leave any entries blank
        if not currentPassword or not newPassword:
            error = "Fill in all fields"
        else:
            db = database()
            cursor = db.cursor(dictionary=True)
            cursor.execute("""SELECT password FROM player where player_id =%s""", (user["player_id"],),)
            row = cursor.fetchone()

            #Checks if Password entered matches password saved
            if not row or not check_password_hash(row["password"],currentPassword):
                error = "Wrong Password"
                cursor.close()
                db.close()
            else:

                #Updates Password in database to newly entered password
                hashed_password = generate_password_hash(newPassword)
                cursor.execute("""UPDATE player set password = %s where player_id = %s""",(hashed_password,user["player_id"]),)
                db.commit()
                cursor.close()
                db.close()
                success = "Password Changed"
        return render_template("TandonGeoguessrSettings.html",username=user["username"],best_score=user["best_score"],error = error,success = success)
    return render_template("TandonGeoguessrSettings.html", username=user["username"],best_score=user["best_score"], error=error, success=success)

@app.route("/deleteAccount",methods=["POST"])
def deleteAccount():
    user = currentUser()
    if not user:
        return redirect(url_for("signin"))
    deletePassword = request.form.get("deletePassword")
    db = database()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""SELECT password FROM player where player_id =%s""", (user["player_id"],), )
    row = cursor.fetchone()

    #Checks If User Entered Password is the same as the one saved, if not, it does not delete account and does nothing
    if not row or not check_password_hash(row["password"], deletePassword):
        error = "Wrong Password"
        cursor.close()
        db.close()
        return redirect(url_for("settings",error="Wrong Password"))

    #If entered Password is matching, it deletes the account from leaderboards and itself
    cursor.execute("""DELETE g from guess g join game_session gs on g.session_id = gs.session_id where gs.player_id = %s""",(user["player_id"],))
    cursor.execute("""DELETE from game_session where player_id =%s""", (user["player_id"],),)
    cursor.execute("""DELETE from leaderboard_entry where player_id = %s""", (user["player_id"],),)
    cursor.execute("""DELETE cle FROM custom_leaderboard_entry AS cle JOIN custom_leaderboard AS cl ON cle.custom_leaderboard_id = cl.custom_leaderboard_id JOIN custom_game AS cg ON cl.custom_game_id = cg.custom_game_id WHERE cg.player_id = %s""", (user["player_id"],))
    cursor.execute("""DELETE cl FROM custom_leaderboard AS cl JOIN custom_game AS cg ON cl.custom_game_id = cg.custom_game_id WHERE cg.player_id = %s""", (user["player_id"],))
    cursor.execute("""DELETE cgs FROM custom_game_session AS cgs JOIN custom_game AS cg ON cgs.custom_game_id = cg.custom_game_id WHERE cg.player_id = %s""", (user["player_id"],))
    cursor.execute("""DELETE cpp FROM custom_photo_pool AS cpp JOIN custom_game AS cg ON cpp.custom_game_id = cg.custom_game_id WHERE cg.player_id = %s""", (user["player_id"],))
    cursor.execute("""DELETE FROM custom_game WHERE player_id = %s""", (user["player_id"],))
    cursor.execute("""DELETE FROM player WHERE player_id = %s""", (user["player_id"],))

    db.commit()
    cursor.close()
    db.close()
    session.clear()
    return redirect(url_for("signin"))

@app.route("/play")
def play():
    user = currentUser()
    if not user:
        return redirect(url_for("signin"))

    # Check if there is an active game in the session
    session_id = session.get("current_session_id")
    current_round = session.get("current_round")

    # If no active game or we've finished all rounds, start a new game
    if session_id is None or current_round is None or current_round > MAX_ROUNDS:
        session_id = start_new_game()
        current_round = 1

    # Fetch a random photo from the database
    db = database()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""SELECT photo_id, photo_data, room, floor, building FROM photo ORDER BY RAND() LIMIT 1""")
    photo = cursor.fetchone()
    cursor.close()
    db.close()

    # Remember which photo this round is using
    session["current_photo_id"] = photo["photo_id"]

    return render_template(
        "TandonGeoguessrPlay.html",
        username=user["username"],
        best_score=user["best_score"],
        current_round=current_round,
        max_rounds=MAX_ROUNDS,
        photo=photo,
    )

@app.route("/submit_guess", methods=["POST"])
def submit_guess():
    user = currentUser()
    if not user:
        return redirect(url_for("signin"))

    mode = session.get("mode", "normal")

    # For normal vs custom, the "session id" we validate is different
    if mode == "custom":
        game_session_id = session.get("custom_session_id")
    else:
        game_session_id = session.get("current_session_id")

    current_round = session.get("current_round")
    photo_id = session.get("current_photo_id")

    if not game_session_id or not photo_id or not current_round:
        # Something went wrong, restart the appropriate game type
        if mode == "custom":
            custom_game_id = session.get("custom_game_id")
            if custom_game_id:
                return redirect(url_for("play_custom_game", custom_game_id=custom_game_id))
            return redirect(url_for("custom_games"))
        else:
            return redirect(url_for("play"))

    guessed_building = request.form.get("guessed_building")
    guessed_floor = request.form.get("guessed_floor")
    guessed_room = request.form.get("guessed_room")

    db = database()
    cursor = db.cursor(dictionary=True)

    # Correct answer
    cursor.execute(
        "SELECT room, floor, building, photo_data FROM photo WHERE photo_id = %s",
        (photo_id,),
    )
    correct = cursor.fetchone()

    building_match = guessed_building == correct["building"]
    floor_match = guessed_floor == correct["floor"]
    room_match = guessed_room == correct["room"]

    matches = int(building_match) + int(floor_match) + int(room_match)

    is_correct = 0
    if matches == 3:
        proximity_score = 1000
        is_correct = 1
    elif matches == 2:
        proximity_score = 600
    elif matches == 1:
        proximity_score = 300
    else:
        proximity_score = 0

    # Always record guess against the normal game_session (existing schema).
    # For custom games, we still use current_session_id for guess table,
    # but only custom_game_session drives custom leaderboard logic.
    session_id_for_guess = None
    if mode == "normal":
        session_id_for_guess = game_session_id
        cursor.execute("""SELECT 1 FROM game_session WHERE session_id = %s""",(session_id_for_guess,),)
        row = cursor.fetchone()
        if row is None:
            cursor.close()
            db.close()
            session.pop("current_session_id", None)
            session.pop("current_round", None)
            session.pop("current_photo_id", None)
            return redirect(url_for("play"))
    if session_id_for_guess is not None:
        cursor.execute(
            """
            INSERT INTO guess
                (session_id, photo_id, guessed_room, guessed_floor, guessed_building, is_correct, proximity_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session_id_for_guess,
                photo_id,
                guessed_room,
                guessed_floor,
                guessed_building,
                is_correct,
                proximity_score,
            ),
        )

    # Update total score in the *appropriate* session table
    if mode == "custom":
        cursor.execute(
            """
            UPDATE custom_game_session
            SET total_score = total_score + %s
            WHERE custom_session_id = %s
            """,
            (proximity_score, game_session_id),
        )
    else:
        cursor.execute(
            """
            UPDATE game_session
            SET total_score = total_score + %s
            WHERE session_id = %s
            """,
            (proximity_score, game_session_id),
        )

    db.commit()
    cursor.close()
    db.close()

    # Save info for result page
    session["last_round_score"] = proximity_score
    session["last_guess_building"] = guessed_building
    session["last_guess_floor"] = guessed_floor
    session["last_guess_room"] = guessed_room

    if correct:
        session["last_correct_building"] = correct["building"]
        session["last_correct_floor"] = correct["floor"]
        session["last_correct_room"] = correct["room"]
        session["last_photo_path"] = correct["photo_data"]

    # Next round
    session["current_round"] = current_round + 1

    return redirect(url_for("result"))
# Return all buildings
@app.route("/api/buildings")
def get_buildings():
    db = database()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT building FROM photo")
    results = cursor.fetchall()
    cursor.close()
    db.close()
    buildings = [row["building"] for row in results]
    return jsonify(buildings)

# Return floors for a specific building
@app.route("/api/floors")
def get_floors():
    building = request.args.get("building")
    if not building:
        return jsonify([])

    db = database()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT floor FROM photo WHERE building = %s ORDER BY FLOOR(floor) IS NULL, CAST(floor AS UNSIGNED);", (building,))
    results = cursor.fetchall()
    cursor.close()
    db.close()
    floors = [row["floor"] for row in results]
    return jsonify(floors)

# Return rooms for a specific building + floor (optional)
@app.route("/api/rooms")
def get_rooms():
    building = request.args.get("building")
    floor = request.args.get("floor")
    if not building or not floor:
        return jsonify([])

    db = database()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT room FROM photo WHERE building = %s AND floor = %s", (building, floor))
    results = cursor.fetchall()
    cursor.close()
    db.close()
    rooms = [row["room"] for row in results]
    return jsonify(rooms)

@app.route("/result")
def result():
    user = currentUser()
    if not user:
        return redirect(url_for("signin"))

    mode = session.get("mode", "normal")

    if mode == "custom":
        game_session_id = session.get("custom_session_id")
        custom_game_id = session.get("custom_game_id")
        max_rounds = session.get("custom_max_rounds", MAX_ROUNDS)
    else:
        game_session_id = session.get("current_session_id")
        custom_game_id = None
        max_rounds = MAX_ROUNDS

    if not game_session_id:
        return redirect(url_for("home"))

    db = database()
    cursor = db.cursor(dictionary=True)

    if mode == "custom":
        cursor.execute(
            "SELECT total_score FROM custom_game_session WHERE custom_session_id = %s",
            (game_session_id,),
        )
    else:
        cursor.execute(
            "SELECT total_score FROM game_session WHERE session_id = %s",
            (game_session_id,),
        )

    game = cursor.fetchone()
    cursor.close()
    db.close()

    total_score = game["total_score"] if game else 0

    current_round = session.get("current_round", 1)
    finished_round = max(current_round - 1, 1)
    is_final_round = finished_round >= max_rounds



    # If this is a custom game and we just finished, update its custom leaderboard
    if mode == "custom" and is_final_round and custom_game_id is not None:
        update_custom_leaderboard(custom_game_id, user["player_id"], total_score)

    photo_path = session.get("last_photo_path")

    return render_template(
        "TandonGeoguessrRoundResult.html",
        username=user["username"],
        best_score=user["best_score"],
        total_score=total_score,
        round_score=session.get("last_round_score", 0),
        current_round=finished_round,
        max_rounds=max_rounds,
        is_final_round=is_final_round,
        is_custom_mode=(mode == "custom"),
        custom_game_id=custom_game_id,
        guessed_building=session.get("last_guess_building"),
        guessed_floor=session.get("last_guess_floor"),
        guessed_room=session.get("last_guess_room"),
        correct_building=session.get("last_correct_building"),
        correct_floor=session.get("last_correct_floor"),
        correct_room=session.get("last_correct_room"),
        photo_path=photo_path,
    )


# ==========================
# Custom Game Routes
# ==========================

@app.route("/photo_browser", methods=["GET", "POST"])
def photo_browser():
    user = currentUser()
    db = database()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT DISTINCT building FROM photo ORDER BY building")
    buildings = [row["building"] for row in cursor.fetchall()]

    selected_building = request.args.get("building", "")

    if request.method == "POST":
        selected_photos = request.form.getlist("selected_photos")
        # Store IDs for use in next step
        session["custom_photo_ids"] = selected_photos
        cursor.close()
        db.close()
        return redirect(url_for("create_custom_game"))

    # GET request: filter photos if a building is selected
    if selected_building:
        cursor.execute("SELECT * FROM photo WHERE building = %s ORDER BY upload_date DESC", (selected_building,))
    else:
        cursor.execute("SELECT * FROM photo ORDER BY upload_date DESC")
    photos = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template(
        "PhotoBrowser.html",
        photos=photos,
        buildings=buildings,
        selected_building=selected_building,
        username=user["username"],
        best_score=user["best_score"],
    )

@app.route("/create_custom_game", methods=["GET", "POST"])
def create_custom_game():
    user = currentUser()
    if not user:
        return redirect(url_for("signin"))
    photo_ids = session.get("custom_photo_ids")
    if not photo_ids:
        return redirect(url_for("photo_browser"))
    db = database()
    cursor = db.cursor(dictionary=True)
    # Get full info for all selected photos
    format_strings = ','.join(['%s'] * len(photo_ids))
    cursor.execute(f"SELECT * FROM photo WHERE photo_id IN ({format_strings})", tuple(photo_ids))
    photos = cursor.fetchall()

    if request.method == "POST":
        cursor.execute("INSERT INTO custom_game (player_id) VALUES (%s)", (user["player_id"],))
        db.commit()
        custom_game_id = cursor.lastrowid
        # Bulk insert into custom_photo_pool
        for pid in photo_ids:
            cursor.execute("INSERT INTO custom_photo_pool (custom_game_id, photo_id) VALUES (%s, %s)", (custom_game_id, pid))
        db.commit()
        cursor.close()
        db.close()
        session.pop("custom_photo_ids", None)
        return redirect(url_for("custom_games"))  # will be implemented next

    cursor.close()
    db.close()
    return render_template(
        "CreateCustomGame.html",
        photos=photos,
        username=user["username"],
        best_score=user["best_score"],
    )

@app.route("/custom_games", methods=["GET", "POST"])
def custom_games():
    user = currentUser()
    if not user:
        return redirect(url_for("signin"))

    if request.method == "POST":
        selected_game_id = request.form.get("selected_game_id")
        if selected_game_id:
            return redirect(url_for("play_custom_game", custom_game_id=selected_game_id))
    
    search = request.args.get("search", "").strip()
    db = database()
    cursor = db.cursor(dictionary=True)
    if search:
        try:
            search_id = int(search)
        except ValueError:
            search_id = None
        if search_id:
            cursor.execute(
                "SELECT cg.custom_game_id, p.username FROM custom_game cg JOIN player p ON cg.player_id = p.player_id WHERE cg.custom_game_id = %s OR p.username LIKE %s ORDER BY cg.custom_game_id DESC",
                (search_id, f"%{search}%")
            )
        else:
            cursor.execute(
                "SELECT cg.custom_game_id, p.username FROM custom_game cg JOIN player p ON cg.player_id = p.player_id WHERE p.username LIKE %s ORDER BY cg.custom_game_id DESC",
                (f"%{search}%",)
            )
    else:
        cursor.execute(
            "SELECT cg.custom_game_id, p.username FROM custom_game cg JOIN player p ON cg.player_id = p.player_id ORDER BY cg.custom_game_id DESC"
        )
    games = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template(
        "CustomGameSearch.html",
        games=games,
        search=search,
        username=user["username"],
        best_score=user["best_score"],
    )

@app.route("/play_custom_game/<int:custom_game_id>")
def play_custom_game(custom_game_id):
    user = currentUser()
    if not user:
        return redirect(url_for("signin"))

    mode = session.get("mode")
    active_custom_game_id = session.get("custom_game_id")
    custom_session_id = session.get("custom_session_id")
    current_round = session.get("current_round")
    custom_photo_ids = session.get("custom_photo_ids")
    custom_max_rounds = session.get("custom_max_rounds")

    # If this is a fresh custom game, or we've switched to a different game, or finished:
    if (
        mode != "custom"
        or active_custom_game_id != custom_game_id
        or custom_session_id is None
        or custom_photo_ids is None
        or custom_max_rounds is None
        or current_round is None
        or current_round > custom_max_rounds
    ):
        custom_session_id = start_custom_game_session(custom_game_id)
        if not custom_session_id:
            # No photos or bad game id
            return redirect(url_for("custom_games"))
        custom_photo_ids = session["custom_photo_ids"]
        custom_max_rounds = session["custom_max_rounds"]
        current_round = session["current_round"]

    # Pick the correct photo for this round
    index = current_round - 1
    if index < 0 or index >= len(custom_photo_ids):
        # Something went weird; send to result
        return redirect(url_for("result"))

    photo_id = custom_photo_ids[index]

    db = database()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """SELECT photo_id, photo_data, room, floor, building
           FROM photo
           WHERE photo_id = %s""",
        (photo_id,),
    )
    photo = cursor.fetchone()
    cursor.close()
    db.close()

    if not photo:
        return redirect(url_for("result"))

    # Remember which photo is being used this round
    session["current_photo_id"] = photo["photo_id"]

    return render_template(
        "TandonGeoguessrPlay.html",
        username=user["username"],
        best_score=user["best_score"],
        current_round=current_round,
        max_rounds=custom_max_rounds,
        photo=photo,
    )

@app.route("/custom_leaderboard/<int:custom_game_id>")
def custom_leaderboard(custom_game_id):
    user = currentUser()
    if not user:
        return redirect(url_for("signin"))

    db = database()
    cursor = db.cursor(dictionary=True)

    # Get latest leaderboard for this custom game
    cursor.execute(
        """
        SELECT custom_leaderboard_id
        FROM custom_leaderboard
        WHERE custom_game_id = %s
        ORDER BY custom_leaderboard_id DESC
        LIMIT 1
        """,
        (custom_game_id,),
    )
    lb = cursor.fetchone()
    if not lb:
        # No leaderboard yet
        entries = []
    else:
        custom_leaderboard_id = lb["custom_leaderboard_id"]
        cursor.execute(
            """
            SELECT cle.custom_leaderboard_entry_id,
                   p.username,
                   cle.max_score,
                   cle.ranking
            FROM custom_leaderboard_entry cle
            INNER JOIN player p ON cle.player_id = p.player_id
            WHERE cle.custom_leaderboard_id = %s
            ORDER BY cle.ranking ASC, cle.max_score DESC
            """,
            (custom_leaderboard_id,),
        )
        entries = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "CustomLeaderboard.html",
        username=user["username"],
        best_score=user["best_score"],
        custom_game_id=custom_game_id,
        entries=entries,
    )

# ==========================
# Redirect Helper Routes
# ==========================

@app.route("/TandonGeoguessrSignUp.html")
def signup_redirect():
    return redirect(url_for("signup"))

@app.route("/TandonGeoguessrHome.html")
def home_redirect():
    return redirect(url_for("home"))


@app.route("/TandonGeoguessrLeaderboard.html")
def leaderboard_redirect():
    return redirect(url_for("leaderboard"))

@app.route("/TandonGeoguessrPlay.html")
def play_redirect():
    return redirect(url_for("play"))

@app.route("/TandonGeoguessrRoundResult.html")
def result_redirect():
    return redirect(url_for("result"))

@app.route("/TandonGeoguessrSignIn.html")
def signin_redirect():
    return redirect(url_for("signin"))

@app.route("/TandonGeoguessrSettings.html")
def settings_redirect():
    return redirect(url_for("settings"))


if __name__ == "__main__":
    app.run(debug=True)