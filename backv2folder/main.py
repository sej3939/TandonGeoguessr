from flask import Flask, render_template, url_for, redirect, request, session
from werkzeug.security import generate_password_hash, check_password_hash

import mysql.connector
import ssl
app = Flask(__name__)
app.secret_key = "idkstring"
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
#Logout Route ( Need to add url button )
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("signin"))
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
    db = database()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""SELECT start_date, end_date FROM leaderboard ORDER by end_date desc LIMIT 1""")
    week = cursor.fetchone()
    cursor.close()
    db.close()
    return render_template("TandonGeoguessrHome.html", username = user["username"], best_score = user["best_score"], date1 = week['start_date'], date2 = week['end_date'])
@app.route("/TandonGeoguessrHome.html")
def home_redirect():
    return redirect(url_for("home"))
#Displays The Dates of the leaderboard week ( not the current / need to fix )
@app.route("/leaderboard")
def leaderboard():
    user = currentUser()
    db = database()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""SELECT p.username, le.max_score FROM leaderboard_entry AS le JOIN player AS p ON le.player_id = p.player_id ORDER BY le.max_score DESC """)
    rows = cursor.fetchall()
    cursor.execute("""SELECT start_date, end_date FROM leaderboard ORDER BY end_date DESC LIMIT 1""")
    week = cursor.fetchone()
    cursor.close()
    db.close()
    return render_template("TandonGeoguessrLeaderboard.html", username = user["username"], best_score = user["best_score"], data=rows, date1=week['start_date'], date2=week['end_date'])
@app.route("/TandonGeoguessrLeaderboard.html")
def leaderboard_redirect():
    return redirect(url_for("leaderboard"))


@app.route("/play")
def play():
    user = currentUser()
    #db = database()
    return render_template("TandonGeoguessrPlay.html", username = user["username"], best_score = user["best_score"])

@app.route("/TandonGeoguessrPlay.html")
def play_redirect():
    return redirect(url_for("play"))

@app.route("/result")
def result():
    return render_template("TandonGeoguessrRoundResult.html")
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
    # SignUp HTML file doesn't currently work with this
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

@app.route("/TandonGeoguessrSignUp.html")
def signup_redirect():
    return redirect(url_for("signup"))

if __name__ == "__main__":
    app.run(debug=True)
