from flask import Flask, render_template, url_for, redirect, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, timedelta

import mysql.connector
import ssl
app = Flask(__name__)
app.secret_key = "idkstring"
MAX_ROUNDS = 3 #number of rounds per game

# Connection to Aiven Database stuff
def database():
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    return mysql.connector.connect(
        host="tandongeo-tandongeoguessr.k.aivencloud.com",
        port=12357,
        user="avnadmin",
        password="AVNS_UH0FJDbDS1pBn2vW2xs",
        database="defaultdb",)

# shortcut to get current week
def currentWeek():
    today = date.today()
    weekday = today.weekday()
    daysSinceSunday = (weekday + 1) % 7
    weekStart = today - timedelta(days=daysSinceSunday)
    weekEnd = weekStart + timedelta(days=6)
    return weekStart, weekEnd

# Shortcut to paste logged in user to the top right of the screen ( Username, Bestscore )
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



#Home Page
@app.route("/")
def home():
    user = currentUser()
    if not user:
        return redirect(url_for("signin"))
    weekStart, weekEnd = currentWeek()
    return render_template("TandonGeoguessrHome.html", username = user["username"], best_score = user["best_score"], date1 = weekStart, date2 = weekEnd)
@app.route("/TandonGeoguessrHome.html")


def home_redirect():
    return redirect(url_for("home"))
#Displays The Dates of the leaderboard week
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
@app.route("/TandonGeoguessrLeaderboard.html")


def leaderboard_redirect():
    return redirect(url_for("leaderboard"))

#Create a new game_session row for the logged-in user, store its session_id and current_round in the Flask session, and return the new session_id
def start_new_game():
    user = currentUser()
    if not user:
        return None

    db = database()
    cursor = db.cursor(dictionary=True)

    # Create a new game_session with total_score initialized to 0
    cursor.execute("""INSERT INTO game_session (player_id, total_score) VALUES (%s, %s)""", (user["player_id"], 0),)
    session_id = cursor.lastrowid
    db.commit()

    cursor.close()
    db.close()

    #Remember this game in the Flask session
    session["current_session_id"] = session_id
    session["current_round"] = 1

    return session_id

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
        current_round=current_round,
        max_rounds=MAX_ROUNDS,
        photo=photo,
    )

@app.route("/submit_guess", methods=["POST"])
def submit_guess():
    user = currentUser()
    if not user:
        return redirect(url_for("signin"))

    # Get current game + round + photo from the session
    session_id = session.get("current_session_id")
    current_round = session.get("current_round")
    photo_id = session.get("current_photo_id")

    if not session_id or not photo_id or not current_round:
        # Something went wrong, restart the game
        return redirect(url_for("play"))

    # Get guess values from the form
    guessed_building = request.form.get("guessed_building")
    guessed_floor = request.form.get("guessed_floor")
    guessed_room = request.form.get("guessed_room")

    db = database()
    cursor = db.cursor(dictionary=True)

    # Get the correct answer from the photo table
    cursor.execute("SELECT room, floor, building FROM photo WHERE photo_id = %s",(photo_id,),)
    correct = cursor.fetchone()

    # scoring logic (3 = 1000, 2 = 600, 1 = 300, 0 = 0)
    building_match = guessed_building == correct["building"]
    floor_match = guessed_floor == correct["floor"]
    room_match = guessed_room == correct["room"]

    # Count how many fields are correct
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

    # Insert row into guess table
    cursor.execute("""INSERT INTO guess(session_id, photo_id, guessed_room, guessed_floor, guessed_building, is_correct, proximity_score) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (
            session_id,
            photo_id,
            guessed_room,
            guessed_floor,
            guessed_building,
            is_correct,
            proximity_score,
        ),
    )

    # Update total_score in game_session
    cursor.execute(
        """UPDATE game_session SET total_score = total_score + %s WHERE session_id = %s""",
        (proximity_score, session_id),
    )

    db.commit()
    cursor.close()
    db.close()

    # Save info needed for the result page into the session
    session["last_round_score"] = proximity_score
    session["last_guess_building"] = guessed_building
    session["last_guess_floor"] = guessed_floor
    session["last_guess_room"] = guessed_room

    if correct:
        session["last_correct_building"] = correct["building"]
        session["last_correct_floor"] = correct["floor"]
        session["last_correct_room"] = correct["room"]

    # Move to next round
    session["current_round"] = current_round + 1

    return redirect(url_for("result"))

@app.route("/TandonGeoguessrPlay.html")
def play_redirect():
    return redirect(url_for("play"))

@app.route("/result")
def result():
    user = currentUser()
    if not user:
        return redirect(url_for("signin"))

    session_id = session.get("current_session_id")
    if not session_id:
        return redirect(url_for("home"))

    # Get the latest total_score from game_session
    db = database()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT total_score FROM game_session WHERE session_id = %s",
        (session_id,),
    )
    game = cursor.fetchone()
    total_score = game["total_score"] if game else 0

    # Figure out which round we just finished
    current_round = session.get("current_round", 1)
    finished_round = max(current_round - 1, 1)
    is_final_round = finished_round >= MAX_ROUNDS

    # If game is over, update leaderboard_entry
    weekStart, weekEnd = currentWeek()
    if is_final_round:
        cursor.execute("""SELECT leaderboard_id FROM leaderboard where start_date = %s and end_date = %s""",
                       (weekStart, weekEnd))
        lb = cursor.fetchone()
        if not lb:
            cursor.execute("""INSERT into leaderboard (start_date, end_date) VALUES (%s,%s)""", (weekStart, weekEnd))
            leaderboard_id = cursor.lastrowid
        else:
            leaderboard_id = lb["leaderboard_id"]
        cursor.execute("""SELECT max_score from leaderboard_entry WHERE player_id = %s AND leaderboard_id = %s""",(user["player_id"],leaderboard_id),)
        row = cursor.fetchone()
        if row is None:
            # No existing entry means we need to insert new row
            cursor.execute(
                """INSERT INTO leaderboard_entry (leaderboard_id, player_id, max_score, ranking) VALUES (%s, %s, %s, %s)""",
                (leaderboard_id, user["player_id"], total_score, 0),
            )
        elif total_score > row["max_score"]:
            # Existing entry but new score is higher means we need to update
            cursor.execute(
                """UPDATE leaderboard_entry SET max_score = %s WHERE player_id = %s AND leaderboard_id = %s""",
                (total_score, user["player_id"], leaderboard_id),
            )
    db.commit()
    cursor.close()
    db.close()

    return render_template(
        "TandonGeoguessrRoundResult.html",
        username=user["username"],
        best_score=user["best_score"],
        total_score=total_score,
        round_score=session.get("last_round_score", 0),
        current_round=finished_round,
        max_rounds=MAX_ROUNDS,
        is_final_round=is_final_round,
        guessed_building=session.get("last_guess_building"),
        guessed_floor=session.get("last_guess_floor"),
        guessed_room=session.get("last_guess_room"),
        correct_building=session.get("last_correct_building"),
        correct_floor=session.get("last_correct_floor"),
        correct_room=session.get("last_correct_room"),
    )


@app.route("/TandonGeoguessrRoundResult.html")
def result_redirect():
    return redirect(url_for("result"))

#
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

@app.route("/TandonGeoguessrSignIn.html")
def signin_redirect():
    return redirect(url_for("signin"))

@app.route("/signup", methods = ["GET","POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username") 
        email = request.form.get("email")
        raw_password = request.form.get("password")
        hashed_password = generate_password_hash(raw_password)
        db = database()
        cursor = db.cursor(dictionary=True)
        
        # This currently doesn't work because the hashed password has a character length up to 255, so the password field has to be changed to VARCHAR(255). 
        cursor.execute("INSERT INTO player (username, password, email) VALUES (%s, %s, %s)", (username, hashed_password, email))
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for("signin"))
    return render_template("TandonGeoguessrSignUp.html")

@app.route("/TandonGeoguessrSignUp.html")
def signup_redirect():
    return redirect(url_for("signup"))

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
@app.route("/TandonGeoguessrSettings.html")
def settings_redirect():
    return redirect(url_for("settings"))
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("signin"))
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
        return render_template("TandonGeoguessrSettings.html",username = user["username"],best_score= user["best_score"], error="Wrong Password", success = None)

    #If entered Password is matching, it deletes the account from leaderboards and itself
    cursor.execute("""DELETE g from guess g join game_session gs on g.session_id = gs.session_id where gs.player_id = %s""",(user["player_id"],))
    cursor.execute("""DELETE from game_session where player_id =%s""", (user["player_id"],),)
    cursor.execute("""DELETE from leaderboard_entry where player_id = %s""", (user["player_id"],),)
    cursor.execute("""DELETE from player where player_id = %s""",(user["player_id"],),)
    db.commit()
    cursor.close()
    db.close()
    session.clear()
    return redirect(url_for("signin"))
if __name__ == "__main__":
    app.run(debug=True)


