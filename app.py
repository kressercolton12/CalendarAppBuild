from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "app.sqlite")

db = SQLAlchemy(app)
ma = Marshmallow(app)

class Month(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    start_day = db.Column(db.Integer, nullable=False)
    days_in_month = db.Column(db.Integer, nullable=False)
    days_in_previous_month = db.Column(db.Integer, nullable=False)
    reminders = db.relationship("Reminder", backref="month", cascade="all, delete, delete-orphan")

    def __init__(self, name, year, start_day, days_in_month, days_in_previous_month):
        self.name = name 
        self.year = year 
        self.start_day = start_day 
        self.days_in_month = days_in_month 
        self.days_in_previous_month = days_in_previous_month

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String, nullable=False)
    date = db.Column(db.Integer, nullable=False)
    month_id = db.Column(db.Integer, db.ForeignKey("month.id"), nullable=False)

    def __init__(self, text, date, month_id):
        self.text = text
        self.date = date
        self.month_id = month_id

class ReminderSchema(ma.Schema):
    class Meta:
        fields = ('id', 'text', 'date', 'month_id')

reminder_schema = ReminderSchema()
multi_reminder_schema = ReminderSchema(many=True)

class MonthSchema(ma.Schema):
    class Meta:
        fields = ("id", "name", "year", "start_day", "days_in_month", "days_in_previous_month", "reminders")
    reminders = ma.Nested(multi_reminder_schema)

month_schema = MonthSchema()
multi_month_schema = MonthSchema(many=True)


@app.route("/month/add", methods=["POST"])
def add_month():
    if request.content_type != "application/json":
        return jsonify("Error Adding to the Calendar")
    
    post_data = request.get_json()
    name = post_data.get("name")
    year = post_data.get("year")
    start_day = post_data.get("start_day")
    days_in_month = post_data.get("days_in_month")
    days_in_previous_month = post_data.get("days_in_previous_month")

    existing_month_check = db.session.query(Month).filter(Month.name == year).first()
    if existing_month_check is not None:
        return jsonify("Error: Month already exists, please try again!")
    
    new_record = Month(name, year, start_day, days_in_month, days_in_previous_month)
    db.session.add(new_record)
    db.session.commit()

    return jsonify(month_schema.dump(new_record))

@app.route('/month/add/multi', methods=["POST"])
def add_multiple_months():
    if request.content_type != 'application/json':
        return jsonify("When adding multiple months please ensure you are adding the data the right way!")
    
    post_data = request.get_json()
    data = post_data.get("data")

    new_months = []

    for month in data:
        name = month.get('name')
        year = month.get('year')
        start_day = month.get('start_day')
        days_in_month = month.get('days_in_month')
        days_in_previous_month = month.get('days_in_previous_month')

        exisiting_month_check = db.session.query(Month).filter(Month.name == name).filter(Month.year == year).first()
        if exisiting_month_check is not None:
            return jsonify("One of the months in the year already exists! Try again!")
        else:
            new_month = Month(name, year, start_day, days_in_month, days_in_previous_month)
            db.session.add(new_month)
            db.session.commit()
            new_months.append(new_month)
    return jsonify(multi_month_schema.dump(new_months))   

@app.route('/month/delete/<id>', methods=["DELETE"])
def delete_month(id):
    dm = db.session.query(Month).filter(Month.id == id).first()
    db.session.delete(dm)
    db.session.commit()
    return jsonify(month_schema.dump(dm), "Month was deleted!")   

@app.route('/month/get')
def get_all_months():
    gam = db.session.query(Month).all()
    return jsonify(multi_month_schema.dump(gam))

@app.route('/month/get/<id>')
def gom(id):
    month = db.session.query(Month).filter(Month.id == id).first()
    return jsonify(month_schema.dump(month))
      
@app.route('/month/get/<year>/<name>')
def monthsearch(year, name):
    month_search = db.session.query(Month).filter(Month.year == year).filter(Month.name == name).first()
    return jsonify(month_schema.dump(month_search))

@app.route('/reminder/add', methods=["POST"])
def add_reminder():
    if request.content_type != "application/json":
        return jsonify("Unable to add Reminder, Try again!")
    
    post_data = request.get_json()
    text = post_data.get ("text")
    date = post_data.get ("date")
    month_id = post_data.get ("month_id")

    existing_reminder_check = db.session.query(Reminder).filter(reminder.date == date).filter(Reminder.month_id == month_id).first()
    if existing_reminder_check is not None:
        return jsonify("Reminder Field is already used, try again!")
    new_reminder = Reminder(text, date, month_id)
    db.session.add(new_reminder)
    db.session.commit()

    return jsonify(reminder_schema.dump(new_reminder))

@app.route('/reminder/update/<month_id>/<date>', methods=["PUT"])
def ur(month_id, date):
    if request.content_type != "application/json":
        return jsonify("Unable to update reminders at this time!")
    put_data = request.get_json()
    text = put_data.get('text')

    reminder = db.session.query(Reminder).filter(Reminder.month_id == month_id).filter(Reminder.date == date).first()
    reminder.text = text
    db.session.commit()

    return jsonify(reminder_schema.dump(reminder))

@app.route('/reminder/delete/<month_id>/<date>', methods=["DELETE"])
def dr(month_id, date):
    reminder = db.session.query(Reminder).filter(Reminder.month_id == month_id).filter(Reminder.date == date).first()
    db.session.delete(reminder)
    db.session.commit()

    return jsonify("Reminder has been erased!", reminder_schema.dump(reminder))



if __name__ == "__main__":
    app.run(debug = True)