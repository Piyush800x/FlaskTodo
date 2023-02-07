from flask import Flask, render_template, request, Response, flash, session, redirect, url_for
from flask_mail import Mail, Message
import random
from datetime import datetime
from pymongo import MongoClient
import json
from bson import ObjectId
from passlib.hash import sha256_crypt

app = Flask(__name__)
app.secret_key = "akgjbuoiegbawuogb"
app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_PORT"] = 587
app.config["MAIL_USERNAME"] = "flasktodoapp@gmail.com"
app.config["MAIL_PASSWORD"] = "kokmkaquqadyrcdj"
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)
# app.config['RECAPTCHA_SITE_KEY'] = '6LeXZVckAAAAABuQYPYqDI-VUdg33gZ-Dojt4_np'
# app.config['RECAPTCHA_SECRET_KEY'] = '6LeXZVckAAAAAHIcPPEtzGFxyK3RBchwMpN6hH8q'
# recaptcha = ReCaptcha(app) 


try:
    mongo = f"mongodb+srv://piyush:e2ZQbOapSM3Xfpuc@flask.xmudilt.mongodb.net/?retryWrites=true&w=majority"
    cluster = MongoClient(mongo)
    db = cluster.todos
except:
    print("Can't connect to MONGODB")


@app.route('/', methods=["GET"])
def home():
    return render_template("index.html", message="")


@app.route("/createtodo", methods=["GET", "POST"])
def create_todo():
    try:
        name = request.form["name"]
        desc = request.form["todo"]
        date = f"{datetime.utcnow().date()}"
        json_data = {
            "title": name, 
            "todo": desc,
            "date": date
        }
        try:
            if "_id" in session:
                _id = session["_id"]
                dbResponse = db.todos.update_one({"_id": ObjectId(f"{_id}")}, {"$push": {"todos": json_data}})  
            else:
                return render_template("login.html", msg="Login to create your todos", message="")
        except Exception as e:    
            return render_template("login.html", msg="Login to create todos.")
        return render_template("index.html", message="Todo created successfully")
    except Exception as e:
        return Response(response=json.dumps({
            "message": "unknown error occured"
        }), status=300)


@app.route('/show', methods=["GET"])
def get_data():
    if request.method == "GET":
        try:
            if "_id" in session:
                _id = session["_id"]
            todos = list(db.todos.find({"_id": ObjectId(f"{_id}")}))
            return render_template("todos.html", len=len(todos[0]["todos"]), todos=todos)
        except Exception as e:
            return render_template("login.html", msg="Login to see your todos", message="")

    
@app.route("/createaccount", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        try:
            global name
            global passw 
            global date 
            global email
            name = request.form["username"]
            passw = request.form["pass"]
            passw2 = request.form["pass2"]
            email = request.form["email"]
            date = f"{datetime.utcnow().date()}"
            dbResponse = list(db.todos.find({"username": name}))
            dbResponse2 = list(db.todos.find({"email": email}))
            if passw == passw2:
                if len(dbResponse) > 0:
                    return render_template("create.html", message="Username already exists")
                if len(dbResponse2) > 0:
                    return render_template("create.html", message="Email already in use")
                else:
                    return send_otp(email, reason="create")
            else:
                return render_template("create.html", message="Passwords didn't matched")
        except Exception as e:
            return Response(response=json.dumps({
                    "message": "unknown error occured"
            }), status=300)
    if request.method == "GET":
        return render_template("create.html", message="")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["username"]
        passw = request.form["pass"]
        dbresponse = db.todos.find({"username": name})
        try:
            hashed = sha256_crypt.verify(passw, dbresponse[0]["password"])
            if hashed is True:
                _id = f"{dbresponse[0]['_id']}"
                session["_id"] = _id
                return render_template("index.html", message="Successfully logged in.", msg="")
            else:
                return render_template("login.html", message="Wrong password! Try again.", msg="")
        except Exception as e:
            return render_template("login.html", message="Username doesn't match", msg="")
    if request.method == "GET":
        return render_template("login.html", message="", msg="")


@app.route("/logout")
def logout():
    session.pop("_id", None)
    return redirect(url_for("login"))


@app.route("/delete", methods=["POST", "GET"])
def delete_todo():
    if request.method == "POST":
        if "_id" in session:
            _id = session["_id"]
            title = request.form["title"]
            todos = list(db.todos.find({"_id": ObjectId(f"{_id}")}))
            for i, todo in enumerate(todos[0]["todos"]):
                if todo["title"] == title:
                    dbRemove = db.todos.update_one({"_id": ObjectId(f"{_id}")}, {"$pull": {"todos": {"title": title}}})
                    return render_template("delete.html", message=f"{title} deleted")
                else:
                    continue
            else:
                return render_template("delete.html", message="Can't find your todo")
            
        else:
            return render_template("login.html", msg="Login to delete your todos", message="")

    if request.method == "GET":
        return render_template("delete.html")


@app.route("/verify", methods=["POST"])
def send_otp(email=None, reason="reset"):
    if request.method == "POST":
        if reason == "create":
            otp = random.randint(100000, 999999)
            session["otps"] = otp
            msg = Message("Welcome to Flask Todo", sender="Flask Todo", recipients=[email])
            msg.body = f"YOUR OTP: {otp}"
            mail.send(msg)
            return render_template("otp.html")
        if reason == "reset":
            email = request.form["email"]
            session["email"] = email
            dbResponse = list(db.todos.find({"email": email}))
            if len(dbResponse) > 0:
                otp2 = random.randint(100000, 999999)
                session["otpr"] = otp2
                msg = Message("Welcome to Flask Todo", sender="Flask Todo", recipients=[email])
                msg.body = f"YOUR PASSWORD RESET OTP: {otp2}"
                mail.send(msg)
                return render_template("reset.html")
            elif len(dbResponse) == 0:  
                return render_template("reset.html", message="Email not found")


@app.route("/reset_verify", methods=["POST"])
def reset_verify():
    if f"{session['otpr']}" == f"{request.form['otp']}":
        return render_template("setpass.html", message="")
    elif f"{session['otpr']}" != f"{request.form['otp']}":
        return render_template("reset.html", message="Wrong OTP")


@app.route("/reset_password", methods=["POST"])
def reset_password():
    passw1 = request.form["pass"]
    passw2 = request.form["pass2"]
    if passw1 == passw2:
        hashed = sha256_crypt.hash(passw1)
        if "email" in session:
            email = session["email"]
            dbUpdate = db.todos.update_one({"email": email}, {"$set": {"password": hashed}})
            session.pop("email", None)
            session.pop("otpr", None)
            return render_template("login.html", message="Password reset successful, Login now")
        else:
            return render_template("setpass.html", message="Invalid Method, try again")
    else:
        return render_template("setpass.html", message="Passwords didn't matched, try again")

@app.route("/create", methods=["POST"])
def verifying():
    global name
    global passw 
    global date 
    global email
    if f"{session['otps']}" == f"{request.form['otp']}":
        hashed = sha256_crypt.hash(passw)
        json_data = {
            "username": name,
            "password": hashed,
            "date": date, 
            "email": email,
            "todos": []
        }
        dbResponse = db.todos.insert_one(json_data)
        session.pop("otps", None)
        return render_template("login.html", message="Account created successfully, Login now")
    elif f'{session["otps"]}' != f"{request.form['otp']}":
        return render_template("otp.html", message="Wrong OTP")


@app.route("/forgot", methods=["POST", "GET"])
def forgot():
    return render_template("forgot.html")


if __name__ == '__main__':
    app.run(host="0.0.0.0")
