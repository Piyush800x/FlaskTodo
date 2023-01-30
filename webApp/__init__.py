from flask import Flask, render_template, request, Response, flash, session, redirect, url_for
from datetime import datetime
from pymongo import MongoClient
import json
from bson import ObjectId
from passlib.hash import sha256_crypt

app = Flask(__name__)
app.secret_key = "akgjbuoiegbawuogb"
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
            name = request.form["username"]
            passw = request.form["pass"]
            passw2 = request.form["pass2"]
            date = f"{datetime.utcnow().date()}"
            dbResponse = list(db.todos.find({"username": name}))
            if passw == passw2:
                if len(dbResponse) > 0:
                    return render_template("create.html", message="Username already exists")
                else:
                    hashed = sha256_crypt.hash(passw)
                    json_data = {
                    "username": name,
                        "password": hashed,
                        "date": date, 
                        "todos": []
                    }
                    dbResponse = db.todos.insert_one(json_data)
                    return render_template("create.html", message="Account created successfully")
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


if __name__ == '__main__':
    app.run()