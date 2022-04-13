from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
import requests
import os

# TODO your active tasks and commit changes shows only if there are task on the queue
# TODO login user
# TODO delete old tasks

API_SERVER = os.environ.get("API_SERVER")
API_SECRET_KEY = os.environ.get("API_SECRET_KEY")
DATABASE_URI = os.environ.get("DATABASE_URI")
username = "ramon"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Tables Configuration
class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    username = db.Column(db.String(500), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Tasks(db.Model):
    task_id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(120), nullable=False)
    active = db.Column(db.Boolean, unique=True, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# FE
@app.route("/", methods=['GET', 'POST'])
def home():
    url_endpoint1 = API_SERVER + ":5000/get_user_tasks"
    parameters1 = {
        "username": username
    }
    response = requests.get(url_endpoint1, params=parameters1)
    response.raise_for_status()
    tasks_data = response.json()
    if request.method == "POST":
        try:
            request.form['task']
        except KeyError:
            print("No task to add")
            print(request.form)
            url_endpoint3 = API_SERVER + ":5000/finish_task"

            for value in request.form:
                parameters3 = {
                    "username": username,
                    "task_id": value
                }
                response = requests.put(url_endpoint3, params=parameters3)
                response.raise_for_status()
                task_finished = response.json()
                print(task_finished)
            response = requests.get(url_endpoint1, params=parameters1)
            response.raise_for_status()
            tasks_data = response.json()
            return render_template("index.html", tasks=tasks_data)
        else:
            url_endpoint = API_SERVER + ":5000/add_new_task"
            parameters = {
                "username": username,
                "task": request.form['task']
            }
            response = requests.post(url_endpoint, params=parameters)
            response.raise_for_status()
            tasks_post = response.json()
            response = requests.get(url_endpoint1, params=parameters1)
            response.raise_for_status()
            tasks_data = response.json()
            return render_template("index.html", tasks=tasks_data)
    return render_template("index.html", tasks=tasks_data)


# API BE
# Get all users on the database
@app.route("/get_all_users")
def get_all_users():
    users = db.session.query(Users).all()
    return jsonify(users=[user.to_dict() for user in users])


# Get all the tasks on the database
@app.route("/get_all_tasks")
def get_all_tasks():
    tasks = db.session.query(Tasks).all()
    return jsonify(tasks=[task.to_dict() for task in tasks])


# Get the tasks of a specific user from the username
@app.route("/get_user_tasks", methods=['GET'])
def get_user_tasks():
    username = request.args['username']
    tasks = db.session.query(Tasks.task, Tasks.active, Tasks.task_id).join(Users, Users.user_id == Tasks.user_id).filter(Users.username == username)
    user_tasks = []
    for row in tasks:
        user_tasks.append({"task": row[0], "active": row[1], "task_id": row[2]})
    return jsonify(user_tasks)


#  Create a new task for user username
@app.route("/add_new_task", methods=["POST"])
def add_new_task():
    user_temp = db.session.query(Users).filter(Users.username == request.args["username"]).first()
    new_task = Tasks(
        task=request.args["task"],
        active=True,
        user_id=user_temp.user_id
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify(success={"Success": f"{request.args['task']} added to queue"})


#  Mark task as done
@app.route("/finish_task", methods=["PUT"])
def finish_task():
    task_id = request.args['task_id']
    task_to_update = Tasks.query.filter_by(task_id=task_id).first()
    try:
        task_to_update.active = False
    except:
        return jsonify(error={"Error ": f"{task_id} does not exist"}), 404
    else:
        db.session.commit()
        return jsonify(success={"Success": f"{task_to_update.task} finished"}), 200


if __name__ == '__main__':
    app.run()