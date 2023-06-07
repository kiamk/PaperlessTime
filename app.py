#Kiam Kaiser
#CS498
#Professor Scott Spetka
from flask import Flask, render_template, flash, request, redirect, url_for, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DateTimeLocalField, SelectField
from wtforms.validators import InputRequired
from dbmgmt import dbmgmt
import sqlite3
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import secrets
import smtplib
import json
import os
import time
import datetime
import requests
import random

# changing timezone for pythonanywhere comment out these two lines when not running local
#os.environ["TZ"] = "America/New_York"
#time.tzset()

#create config file reader and a flag for if the config file is not found. when not found prompt the user to use the form assosiated with making one

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "index"

#returns a list of employee name strings which is pulled from the database
def getEmployeeList():
    conn = sqlite3.connect('PaperlessTime.db')
    cur = conn.cursor()
    db = dbmgmt(conn, cur)
    employeeList = list(db.pull_employee_list())
    for x in range(len(employeeList)):
        employeeList[x] = employeeList[x][0]
    conn.close()
    return(employeeList)


# create Employee class
class employee(UserMixin):
    def __init__(self, employee_info):
        self.id = employee_info[0]
        self.name = employee_info[1]
        self.username = employee_info[2]
        self.password = employee_info[3]
        self.email = employee_info[4]
        self.phone_number = employee_info[5]
        self.position = employee_info[6]
        self.clock_in_history = employee_info[7]

    def __str__(self):
        return f"{self.id}, {self.name}, {self.username}, {self.password},\
                {self.email}, {self.phone_number}, {self.position}, {self.clock_in_history}"

    def get_clock_tuple(self):
        return tuple([self.id, self.clock_in_history])
# create new employee form
class newempform(FlaskForm):
    name = StringField('name (first last)', validators=[InputRequired()])
    username = StringField('username', validators=[InputRequired()])
    password = PasswordField('password', validators=[InputRequired()])
    email = StringField('email', validators=[InputRequired()])
    phone_number = StringField('phone number (ex: 5189151238)', validators=[InputRequired()])
    submit = SubmitField("Submit")

# create login form
class loginform(FlaskForm):
    username = StringField('username', validators=[InputRequired()])
    password = PasswordField('password', validators=[InputRequired()])
    login = SubmitField("Login")

# create schedule employee form
class scheduleEmployeeForm(FlaskForm):
    employeeName = SelectField('employee name', validators=[InputRequired()])
    start = DateTimeLocalField('employee start date and time', validators=[InputRequired()], format='%Y-%m-%dT%H:%M')
    end = DateTimeLocalField('employee end date and time', validators=[InputRequired()], format='%Y-%m-%dT%H:%M')
    scheduleEmployee = SubmitField("Schedule Employee")

def send_message():
  resp = requests.post('http://textbelt.com/text', {
    'phone': '5189155775',
    'message': 'user added',
    'key': 'textbelt'
  })

#change the below to referencing a setup info document and keeping a 14 day counter based on that info
#   ie. if the first pay period starts on 05/01/23 then the next pay period starts on 05/15/23
#           maybe this doc has a last pay period start entry so 14 days can just be counted from then if the program is turned off

#returns the start of the pay period when called on the wednesday before payday
def getpayprdstart():
    #ensuring that pay period start date is accurate for a two week pay period where the email is sent on the wednesday
    #   after the pay period ends
    today = datetime.datetime.now()
    if (int(today.strftime("%d")) - 17) > 0:
        return today.strftime("%m") + "/" + str(int(today.strftime("%d")) - 17) + "/" + today.strftime("%y")
    else:
        if int(today.strftime("%m") - 1) > 0:
            #each elif is for each month
            if int(today.strftime("%m") - 1) == 1:
                return str(int(today.strftime("%m")) - 1) + "/" + str(31 + int(today.strftime("%d")) - 17) +\
                "/" + today.strftime("%y")
            elif int(today.strftime("%m") - 1) == 2:
                if int(today.strftime("%y")) % 4 == 0:
                    return str(int(today.strftime("%m")) - 1) + "/" +\
                    str(29 + int(today.strftime("%d")) - 17) + "/" + today.strftime("%y")
                else:
                    return str(int(today.strftime("%m")) - 1) + "/" +\
                    str(28 + int(today.strftime("%d")) - 17) + "/" + today.strftime("%y")
            elif int(today.strftime("%m") - 1) == 3:
                return str(int(today.strftime("%m")) - 1) + "/" + str(31 + int(today.strftime("%d")) - 17) +\
                "/" + today.strftime("%y")
            elif int(today.strftime("%m") - 1) == 4:
                return str(int(today.strftime("%m")) - 1) + "/" + str(30 + int(today.strftime("%d")) - 17) +\
                "/" + today.strftime("%y")
            elif int(today.strftime("%m") - 1) == 5:
                return str(int(today.strftime("%m")) - 1) + "/" + str(31 + int(today.strftime("%d")) - 17) +\
                "/" + today.strftime("%y")
            elif int(today.strftime("%m") - 1) == 6:
                return str(int(today.strftime("%m")) - 1) + "/" + str(30 + int(today.strftime("%d")) - 17) +\
                "/" + today.strftime("%y")
            elif int(today.strftime("%m") - 1) == 7:
                return str(int(today.strftime("%m")) - 1) + "/" + str(31 + int(today.strftime("%d")) - 17) +\
                "/" + today.strftime("%y")
            elif int(today.strftime("%m") - 1) == 8:
                return str(int(today.strftime("%m")) - 1) + "/" + str(31 + int(today.strftime("%d")) - 17) +\
                "/" + today.strftime("%y")
            elif int(today.strftime("%m") - 1) == 9:
                return str(int(today.strftime("%m")) - 1) + "/" + str(30 + int(today.strftime("%d")) - 17) +\
                "/" + today.strftime("%y")
            elif int(today.strftime("%m") - 1) == 10:
                return str(int(today.strftime("%m")) - 1) + "/" + str(31 + int(today.strftime("%d")) - 17) +\
                "/" + today.strftime("%y")
            elif int(today.strftime("%m") - 1) == 11:
                return str(int(today.strftime("%m")) - 1) + "/" + str(30 + int(today.strftime("%d")) - 17) +\
                "/" + today.strftime("%y")
        else:
            return "12/" + str(31 + int(today.strftime("%d")) - 17) + "/" + str(int(today.strftime("%y") - 1))

#creating the function to send the email
#ensure that in the gmail account being used to send the emails 2fa is enabled and that an app password is used
def sendemail(targetemail, msg):
    #opening connection to email server
    try:
        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.starttls()
        smtp.login(user="kkaisercapstone@gmail.com", password="zdczmecfkrwfiwnn")
    except Exception as e:
        print(e)

    payprdstart = getpayprdstart()
    msg = "Subject: Employee Hours Worked for the pay period starting on " + payprdstart + "\n\n" + msg
    smtp.sendmail("kkaisercapstone@gmail.com", targetemail, msg)

    smtp.close()

#returns an array of the schedule events for the current year or creates a new file if one has not been made yet
def getSchedule():
    today = datetime.datetime.now()
    filename = today.strftime("%Y") + "Schedule.json"
    
    #if the file does not exist create a new empty file
    try:
        file = open("schedules/" + filename, 'r')
    except:
        file = open("schedules/" + filename, 'w')
        file.close()
        return
    
    #if the file is empty set scedule to empty
    try:
        schedule = json.load(file)
    except:
        schedule = []
        
    file.close()
    return(schedule)

#returns a string of the schedule where ' are replaced with " so the formatting is correct to be sent to the calendar
def getScheduleStr():
    today = datetime.datetime.now()
    filename = today.strftime("%Y") + "Schedule.json"
    
    #if the file does not exist create a new empty file
    try:
        file = open("schedules/" + filename, 'r')
    except:
        file = open("schedules/" + filename, 'w')
        file.close()
        return
    
    #if the file is empty set scedule to empty
    try:
        schedule = json.load(file)
    except:
        schedule = []
    file.close()
    scheduleStr = json.dumps(schedule)
    #replacing python single quotes with double
    scheduleStr = scheduleStr.replace("\'", "\"")
    return(scheduleStr)

def addToSchedule():
    schedule = getSchedule()
    form = scheduleEmployeeForm()
    form.employeeName.choices = getEmployeeList()
    newScheduleEntry = {"title": "", "start": "", "end": "", "color": ""}
    
    if form.validate_on_submit():
        newScheduleEntry["title"] = form.employeeName.data
        newScheduleEntry["start"] = str(form.start.data)
        newScheduleEntry["end"] = str(form.end.data)
        
        conn = sqlite3.connect('PaperlessTime.db')
        cur = conn.cursor()
        db = dbmgmt(conn, cur)
        id = db.name_pull_employee_info(str(form.employeeName.data))[0]
        if id % 3 == 0:
            newScheduleEntry["color"] = "rgb(255," + str(9*id) + ", " + str(18*id) + ")"
        elif id % 3 == 1:
            newScheduleEntry["color"] = "rgb(" + str(9*id) + ",255, " + str(18*id) + ")"
        elif id % 3 == 2:
            newScheduleEntry["color"] = "rgb(" + str(9*id) + ", " + str(18*id) + ", " + "255)"
        
        
        if id * 15 > 240:
            if id * 15 > 480:
                if id * 15 > 720:
                    newScheduleEntry["color"] = "rgb(" + str(random.randint(25, 230)) + "," + str(random.randint(25, 230)) + "," + str(random.randint(25, 230)) + ")"
                else:
                   newScheduleEntry["color"] = "rgb(" + str(255-(id*15)) + ",15, 15)" 
            else:
               newScheduleEntry["color"] = "rgb(240," + str(255-(id*15)) + ", 15)" 
        else:
            newScheduleEntry["color"] = "rgb(240,240," + str(255-(id*15)) + ")"
        
        form = scheduleEmployeeForm(formdata = None)
        form.employeeName.choices = getEmployeeList()
    if (newScheduleEntry):
        schedule.append(newScheduleEntry)
    
    today = datetime.datetime.now()
    filename = today.strftime("%Y") + "Schedule.json"
    
    #the try loop below backs up the schedule before opening the current schedule in w mode as a protection against the schedule being lost
    try:
        file = open("schedules/" + filename, 'r')
        oldSchedule = json.load(file)
        file.close()
        file = open("schedules/scheduleBackup", 'w')
        json.dump(oldSchedule, file)
        file.close()
    except:
        file = open("schedules/" + filename, 'w')
        file.close()
        
    file = open("schedules/" + filename, 'w')
    json.dump(schedule, file)
    file.close()

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('PaperlessTime.db')
    cur = conn.cursor()
    db = dbmgmt(conn, cur)
    emp_info = db.id_pull_employee_info(user_id)
    if emp_info == 0:
        return None
    conn.close()
    return employee(emp_info)

# add_employee page
@app.route("/add_employee", methods=['GET', 'POST'])
def add_employee():
    # initializing db object
    conn = sqlite3.connect('PaperlessTime.db')
    cur = conn.cursor()
    db = dbmgmt(conn, cur)
    name = None
    username = None
    password = None
    email = None
    phone_number = None
    form = newempform()


    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        username = form.username.data
        form.username.data = ''
        password = form.password.data
        form.password.data = ''
        email = form.email.data
        form.email.data = ''
        phone_number = form.phone_number.data
        form.phone_number.data = ''
        form = newempform(formdata = None)
        new_emp_info = (name, username, password, email, phone_number)
        if new_emp_info != '':
            db_add_indicator = db.add_new_employee(new_emp_info)
            if db_add_indicator == 1:
                flash("The employee has been successfully added to the database, you may now login!")
                return redirect(url_for('index'))
            elif db_add_indicator == 0:
                flash("An employee with this name already exists!")
                return redirect(url_for('add_employee'))
            elif db_add_indicator == 2:
                flash("An employee with this username already exists!")
                return redirect(url_for('add_employee'))
        new_emp_info = None
        conn.close()


    return render_template("add_employee.html",
        name = name,
        username = username,
        password = password,
        email = email,
        phone_number = phone_number,
        form = newempform(formdata = None))

# home page
@app.route("/", methods=['GET', 'POST'])
def index():
    username = None
    password = None
    # initializing db object
    conn = sqlite3.connect('PaperlessTime.db')
    cur = conn.cursor()
    db = dbmgmt(conn, cur)
    form = loginform()

    if form.validate_on_submit():
        username = form.username.data.lower()
        form.username.data = ''
        password = form.password.data
        form.password.data = ''
        login_info = (username, password)
        if login_info != '':
            db_login_indicator = db.pull_employee_info(login_info)
            if db_login_indicator != 0 and db_login_indicator != 1:
                emp = employee(db.pull_employee_info(login_info))
                login_user(emp)
                return redirect(url_for('index'))
            elif db_login_indicator == 0:
                flash("The username you entered could not be found!")
                return redirect(url_for('index'))
            elif db_login_indicator == 1:
                flash("The password you entered was incorrect!")
                return redirect(url_for('index'))
    conn.close()
    return render_template("index.html", username = username, password = password, form = loginform())
        
@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    #creating a schedule Json if there isnt one yet
    getSchedule()
    form = scheduleEmployeeForm()
    form.employeeName.choices = getEmployeeList()
    #ensuring that the form does not resubmit on refresh
    if form.validate_on_submit():
        addToSchedule()
        return redirect(url_for('dashboard'))
    return render_template("dashboard.html", position = current_user.position, getScheduleStr = getScheduleStr(), form=form)

@app.route("/schedule", methods = ["GET", "POST"])
@login_required
def schedule():
    #creating a schedule Json if there isnt one yet
    getSchedule()
    form = scheduleEmployeeForm()
    form.employeeName.choices = getEmployeeList()
    #ensuring that the form does not resubmit on refresh
    if form.validate_on_submit():
        addToSchedule()
        return redirect(url_for('schedule'))
    return render_template("schedule.html", position = current_user.position, getScheduleStr = getScheduleStr(), form=form)

@app.route("/chatroom")
@login_required
def chatroom():
    idList = []
    for id in range(100):
        if id % 3 == 0:
            idList.append("rgb(255," + str(9*id) + ", " + str(18*id) + ")")
        elif id % 3 == 1:
            idList.append("rgb(" + str(9*id) + ",255, " + str(18*id) + ")")
        elif id % 3 == 2:
            idList.append("rgb(" + str(9*id) + ", " + str(18*id) + ", " + "255)")
    return render_template("chatroom.html", idList = json.dumps(idList))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Successfully Logged Out")
    return redirect(url_for('index'))

@app.route("/clock_in")
@login_required
def clock_in():
    conn = sqlite3.connect('PaperlessTime.db')
    cur = conn.cursor()
    db = dbmgmt(conn, cur)
    clock_in_indicator = db.clock_in(current_user.get_clock_tuple())
    conn.close()
    if clock_in_indicator == 0:
        flash("You forgot to clock out last shift please notify an administrator")
        return redirect(url_for("dashboard"))
    elif clock_in_indicator == 1:
        flash("You have succesfully clocked-in! Have a great day!")
        return redirect(url_for("dashboard"))
    else:
        flash("System error! not clocked in please notify an administrator")
        return redirect(url_for("index"))

@app.route("/clock_out")
@login_required
def clock_out():
    conn = sqlite3.connect('PaperlessTime.db')
    cur = conn.cursor()
    db = dbmgmt(conn, cur)
    clock_in_indicator = db.clock_out(current_user.get_clock_tuple())
    conn.close()
    if clock_in_indicator == 0:
        flash("You forgot to clock in this shift please notify an administrator")
        return redirect(url_for("dashboard"))
    elif clock_in_indicator == 1:
        flash("You have succesfully clocked-out! Have a great day!")
        return redirect(url_for("dashboard"))
    else:
        flash("System error! not clocked out please notify an administrator")
        return redirect(url_for("index"))

# ----------error pages--------------------
# invalid url
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# internal server error
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500

# ----------Main Run Loop-------------------
if __name__ == "__main__":
    from waitress import serve
    #uncomment the below line to run developer server
    app.run(host="127.0.0.1", port=8080, debug=True)
    
    #uncomment the below line to run deployment server
    #serve(app, host='0.0.0.0', port=8080)