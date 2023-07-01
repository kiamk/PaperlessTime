#scheduled and acutal worked time
#add function to get the amount of hours an employee worked in the last pay period
#   make sure to handle employees not clocking out
#welcome page redirects to /c/welcome/p/signup/ and not the proper welcome page so fix that
from flask import Flask, render_template, flash, request, redirect, url_for, session, current_app
from flask_wtf import FlaskForm
from functools import wraps
from wtforms import StringField, SubmitField, PasswordField, DateTimeLocalField, SelectField, IntegerField, DateField
from wtforms.validators import InputRequired
from dbmgmt import dbmgmt
import sqlite3
from flask_login import UserMixin, AnonymousUserMixin, login_user, LoginManager, login_required, logout_user, current_user
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
#uncomment path with home when running on python anywhere to make sure files open properly
#path = "/home/kaiserk/mysite/"
path = ""

#create config file reader and a flag for if the config file is not found. when not found prompt the user to use the form assosiated with making one

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "index"

#returns a list of employee name strings which is pulled from the database
def getEmployeeNameList(companyName):
    conn = sqlite3.connect(path + 'databases/' + companyName + 'PaperlessTime.db')
    cur = conn.cursor()
    db = dbmgmt(conn, cur)
    employeeList = list(db.pull_employee_name_list())
    for x in range(len(employeeList)):
        employeeList[x] = employeeList[x][0]
    conn.close()
    employeeList.insert(0, 'Select an Employee')
    return(employeeList)

# anonymous user class with the new is_authenticated
class anonymous(AnonymousUserMixin):
    position = 0

    def is_authenticated(self):
        return False

login_manager.anonymous_user = anonymous

# create Employee class
class employee(UserMixin):
    def __init__(self, employee_info):
        self.id = employee_info[0]
        self.name = employee_info[1]
        self.username = employee_info[2]
        self.password = employee_info[3]
        self.email = employee_info[4]
        self.phone_number = employee_info[5]
        self.company = employee_info[6]
        self.position = employee_info[7]
        self.clock_in_history = employee_info[8]
        self.smsOptIn = employee_info[9]

    def __str__(self):
        return f"{self.id}, {self.name}, {self.username}, {self.password},\
                {self.email}, {self.phone_number}, {self.position}, {self.clock_in_history}, {self.smsOptIn}, {self.company}"


    def is_authenticated(self):
        companyName = request.path.rsplit('/p')[0].split('/c/')[1]
        return self.is_active and companyName == self.company

    def get_id(self):
        return(json.dumps([self.company, self.id]))

    def get_clock_tuple(self):
        return tuple([self.id, self.clock_in_history])

def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_app.config.get("LOGIN_DISABLED"):
            pass
        elif not current_user.is_authenticated():
            flash("Please login to access this page")
            return redirect(url_for('cIndex', companyName = request.path.rsplit('/p')[0].split('/c/')[1]))

        # flask 1.x compatibility
        # current_app.ensure_sync is only available in Flask >= 2.0
        if callable(getattr(current_app, "ensure_sync", None)):
            return current_app.ensure_sync(func)(*args, **kwargs)
        return func(*args, **kwargs)

    return decorated_view

# create new employee form
class newempform(FlaskForm):
    name = StringField('name (first last)', validators=[InputRequired()])
    username = StringField('username', validators=[InputRequired()])
    password = PasswordField('password', validators=[InputRequired()])
    email = StringField('email', validators=[InputRequired()])
    phone_number = StringField('phone number (ex: 5556667777)', validators=[InputRequired()])
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
    #add handeler for if the end date is before the start date
    end = DateTimeLocalField('employee end date and time', validators=[InputRequired()], format='%Y-%m-%dT%H:%M')
    scheduleEmployee = SubmitField("Schedule Employee")

# create settings form
class settingsForm(FlaskForm):
    payPeriodLength = IntegerField('Please enter the number of days long the pay period is ex:1')
    daysAfterPayPeriod = IntegerField('Please enter the number of days ex: 1')
    payPeriodStart = DateField('start of pay period')
    employeeName = SelectField('employee name')
    employeePosition = SelectField('employee permission', choices=[('', 'Select Employee Position'), ('0', 'Employee'), ('1', 'Manager')])
    removeEmployee = SelectField('employee to be removed')
    submit = SubmitField("Submit")

class confirmForm(FlaskForm):
    confirm = StringField('Type \"yes\" to confirm', validators=[InputRequired()])
    submit = SubmitField("Submit")


#creating the function to send the email and text
#ensure that in the gmail account being used to send the emails 2fa is enabled and that an app password is used
#use the buisniness account of the business if able to
#store the business owner carrier in the config file
#send email to the users regarding a chatroom notification
def send_message(phone_number, message):
    email = "noreply.paperlesstime@gmail.com"
    passwd = "qdpuonlclqyynosj"

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(email, passwd)

    server.sendmail(email, str(phone_number) + '@mms.att.net', message)

#sending email
def send_email(recipient, subject, message):
    email = "noreply.paperlesstime@gmail.com"
    passwd = "qdpuonlclqyynosj"

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(email, passwd)

#returns date object of the start of the last pay period
def curPayPrdStart(companyName):
    try:
            file = open(path + "companyConfigs/" + companyName + "Config", 'r')
            payPrdInfo = json.load(file)
            file.close()
            file = open(path + "companyConfigs/" + companyName + "Config", 'w')
    except:
        file = open(path + "companyConfigs/" + companyName + "Config", 'w')
        payPrdInfo = {"payPeriodLength": "0", "daysAfterPayPeriod": "0", "payPeriodStart": "2000-01-01"}
    
    
    ppStart = datetime.datetime.strptime(payPrdInfo["payPeriodStart"], '%Y-%m-%d').date()
    
    ppLength = int(payPrdInfo["payPeriodLength"])
    while ppLength > 0:
        if ppStart + datetime.timedelta(days = ppLength) < (datetime.date.today() - datetime.timedelta(days = 14)):
            ppStart = ppStart + datetime.timedelta(days = ppLength)
        else:
            break
    
    json.dump(payPrdInfo, file)
    file.close()
    
    return ppStart

print("curPayPrdStart = " + str(curPayPrdStart("DemoCompany")))

#returns an array of the schedule events for the current year or creates a new file if one has not been made yet
def getSchedule(companyName = ""):
    today = datetime.datetime.now()
    filename = companyName + today.strftime("%Y") + "Schedule.json"

    #if the file does not exist create a new empty file
    try:
        file = open(path + "schedules/" + filename, 'r')
    except:
        file = open(path + "schedules/" + filename, 'w')
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
def getScheduleStr(companyName = ""):
    today = datetime.datetime.now()
    filename = companyName + today.strftime("%Y") + "Schedule.json"

    #if the file does not exist create a new empty file
    try:
        file = open(path + "schedules/" + filename, 'r')
    except:
        file = open(path + "schedules/" + filename, 'w')
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

def addToSchedule(companyName):
    schedule = getSchedule(companyName)
    form = scheduleEmployeeForm()
    form.employeeName.choices = getEmployeeNameList(companyName)
    newScheduleEntry = {"title": "", "start": "", "end": "", "color": ""}

    if form.validate_on_submit():
        newScheduleEntry["title"] = form.employeeName.data
        newScheduleEntry["start"] = str(form.start.data)
        newScheduleEntry["end"] = str(form.end.data)

        conn = sqlite3.connect(path + 'databases/' + companyName + 'PaperlessTime.db')
        cur = conn.cursor()
        db = dbmgmt(conn, cur)
        id = db.name_pull_employee_info(str(form.employeeName.data))
        #the if statement below creates seemingly random colors based on the employee id with little repitiion
        #also ensures that if the event icon is too bright that black text is used
        id = id + 1
        if id % 3 == 0:
            a = int(255/id)
            b = 0+(id*id*9)%200+55
            c = 0+(id*10)%255
            if a > 199 or b > 199 or c > 199:
                newScheduleEntry["textColor"] = "rgb(0,0,0)"
            elif a > 149:
                if b > 149 or c > 149:
                    newScheduleEntry["textColor"] = "rgb(0,0,0)"
            elif b > 149:
                if a > 149 or c > 149:
                    newScheduleEntry["textColor"] = "rgb(0,0,0)"
            elif c > 149:
                if a > 149 or b > 149:
                    newScheduleEntry["textColor"] = "rgb(0,0,0)"
            newScheduleEntry["color"] = "rgb(" + str(a) + "," + str(b) + ", " + str(c) + ")"
        elif id % 3 == 1:
            b = int(255/id)
            a = 0+(id*id*9)%200+55
            c = 0+(id*10)%255
            if a > 199 or b > 199 or c > 199:
                newScheduleEntry["textColor"] = "rgb(0,0,0)"
            elif a > 149:
                if b > 149 or c > 149:
                    newScheduleEntry["textColor"] = "rgb(0,0,0)"
            elif b > 149:
                if a > 149 or c > 149:
                    newScheduleEntry["textColor"] = "rgb(0,0,0)"
            elif c > 149:
                if a > 149 or b > 149:
                    newScheduleEntry["textColor"] = "rgb(0,0,0)"
            newScheduleEntry["color"] = "rgb(" + str(a) + "," + str(b) + ", " + str(c) + ")"
        elif id % 3 == 2:
            c = int(255/id)
            b = 0+(id*id*9)%200+55
            a = 0+(id*10)%255
            if a > 199 or b > 199 or c > 199:
                newScheduleEntry["textColor"] = "rgb(0,0,0)"
            elif a > 149:
                if b > 149 or c > 149:
                    newScheduleEntry["textColor"] = "rgb(0,0,0)"
            elif b > 149:
                if a > 149 or c > 149:
                    newScheduleEntry["textColor"] = "rgb(0,0,0)"
            elif c > 149:
                if a > 149 or b > 149:
                    newScheduleEntry["textColor"] = "rgb(0,0,0)"
            newScheduleEntry["color"] = "rgb(" + str(a) + "," + str(b) + ", " + str(c) + ")"

        form = scheduleEmployeeForm(formdata = None)
        form.employeeName.choices = getEmployeeNameList(companyName)
    if (newScheduleEntry):
        schedule.append(newScheduleEntry)

    today = datetime.datetime.now()
    filename = companyName + today.strftime("%Y") + "Schedule.json"

    #the try loop below backs up the schedule before opening the current schedule in w mode as a protection against the schedule being lost
    try:
        file = open(path + "schedules/" + filename, 'r')
        oldSchedule = json.load(file)
        file.close()
        file = open(path + "schedules/" + companyName + "scheduleBackup", 'w')
        json.dump(oldSchedule, file)
        file.close()
    except:
        file = open(path + "schedules/" + filename, 'w')
        file.close()

    file = open(path + "schedules/" + filename, 'w')
    json.dump(schedule, file)
    file.close()

@login_manager.user_loader
def load_user(sessionList):
    sessionList = json.loads(str(sessionList))
    conn = sqlite3.connect(path + 'databases/' + sessionList[0] + 'PaperlessTime.db')
    cur = conn.cursor()
    db = dbmgmt(conn, cur)
    emp_info = db.id_pull_employee_info(str(sessionList[1]))
    if emp_info == 0:
        return None
    conn.close()
    return employee(emp_info)

@app.before_request
def check_authorization():
    try:
        file = open(path + 'authorizedCompanies.json', 'r')
        authorizedCompanies = [x.lower() for x in json.load(file)]
    except:
        file = open(path + 'authorizedCompanies.json', 'w')
        json.dump(["democompany"], file)
        file.close()
        file = open(path + 'authorizedCompanies.json', 'r')
        authorizedCompanies = [x.lower() for x in json.load(file)]
    if(request.path[:3]) == '/c/':
        companyName = request.path.rsplit('/p')[0].split('/c/')[1]
    else:
        companyName = 'welcome'
    if not(companyName in authorizedCompanies) and not('signup' in request.path):
        return redirect(url_for('cSignup', companyName = companyName))
    file.close()

#page for no company name specified
@app.route("/")
def index():
    return render_template("welcome.html")

# ----------company pages below. these pages pull company config files. the small c in front of function names stands for company-----------------
# add_employee page
@app.route("/c/<companyName>/p/add_employee/", methods=['GET', 'POST'])
def cAdd_employee(companyName):
    # initializing db object
    conn = sqlite3.connect(path + 'databases/' + companyName + 'PaperlessTime.db')
    cur = conn.cursor()
    db = dbmgmt(conn, cur)
    name = None
    username = None
    password = None
    email = None
    phone_number = None
    form = newempform()
    databaseContent = db.check_content()

    if db.check_content() == 1 and not current_user.is_authenticated():
        flash("Please login to access this page")
        return redirect(url_for('cIndex', companyName = request.path.rsplit('/p')[0].split('/c/')[1]))
        

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
        new_emp_info = (name, username, password, email, phone_number, companyName)
        if new_emp_info != '':
            db_add_indicator = db.add_new_employee(new_emp_info)
            if db_add_indicator == 1:
                flash("The employee has been successfully added to the database and may now login!")
                return redirect(url_for('cIndex', companyName=companyName))
            elif db_add_indicator == 0:
                flash("An employee with this name already exists!")
                return redirect(url_for('cAdd_employee', companyName=companyName))
            elif db_add_indicator == 2:
                flash("An employee with this username already exists!")
                return redirect(url_for('cAdd_employee', companyName=companyName))


        new_emp_info = None
        conn.close()


    return render_template("add_employee.html",
        name = name,
        username = username,
        password = password,
        email = email,
        phone_number = phone_number,
        companyName = companyName,
        databaseContent = databaseContent,
        form = newempform(formdata = None))

# home page
@app.route("/c/<companyName>/p/", methods=['GET', 'POST'])
def cIndex(companyName):
    username = None
    password = None

    # initializing db object
    conn = sqlite3.connect(path + "databases/" + companyName + 'PaperlessTime.db')
    cur = conn.cursor()
    db = dbmgmt(conn, cur)
    form = loginform()
    databaseContent = db.check_content()

    if form.validate_on_submit():
        username = form.username.data.lower()
        form.username.data = ''
        password = form.password.data
        form.password.data = ''
        login_info = (username, password, companyName)
        if login_info != '':
            db_login_indicator = db.pull_employee_info(login_info)
            if db_login_indicator != 0 and db_login_indicator != 1:
                # adding the one in front of company name as a holder encase company name is empty, this will be removed in the user innit
                emp = db.pull_employee_info(login_info)
                emp = employee(emp)
                login_user(emp)
                return redirect(url_for('cIndex', companyName = companyName))
            elif db_login_indicator == 0:
                flash("The username you entered could not be found!")
                return redirect(url_for('cIndex', companyName = companyName))
            elif db_login_indicator == 1:
                flash("The password you entered was incorrect!")
                return redirect(url_for('cIndex', companyName = companyName))
    conn.close()
    return render_template("index.html", username = username, password = password, databaseContent = databaseContent, companyName = companyName,
                            form = loginform(formdata=None))

@app.route("/c/<companyName>/p/dashboard/", methods=['GET', 'POST'])
@login_required
def cDashboard(companyName):
    #creating a schedule Json if there isnt one yet
    getSchedule(companyName)
    #send_message("5189155775", "test message")
    form = scheduleEmployeeForm()
    form.employeeName.choices = getEmployeeNameList(companyName)
    #ensuring that the form does not resubmit on refresh
    if form.validate_on_submit() and form.employeeName.data != 'Select an Employee':
        addToSchedule(companyName)
        return redirect(url_for('cDashboard'))
    elif(form.employeeName.data == 'Select an Employee'): flash("Error: No Employee Selected, Please Select an Employee")
    return render_template("dashboard.html", position = current_user.position, getScheduleStr = getScheduleStr(companyName), form=form, companyName=companyName)

@app.route("/c/<companyName>/p/schedule/", methods = ["GET", "POST"])
@login_required
def cSchedule(companyName):
    #creating a schedule Json if there isnt one yet
    getSchedule(companyName)
    form = scheduleEmployeeForm()
    form.employeeName.choices = getEmployeeNameList(companyName)
    #ensuring that the form does not resubmit on refresh
    if form.validate_on_submit() and form.employeeName.data != 'Select an Employee':
        addToSchedule(companyName)
        return redirect(url_for('cSchedule'))
    elif(form.employeeName.data == 'Select an Employee'): flash("Error: No Employee Selected, Please Select an Employee")
    return render_template("schedule.html", position = current_user.position, getScheduleStr = getScheduleStr(companyName), form=form, companyName=companyName)

@app.route("/c/<companyName>/p/chatroom/")
@login_required
def cChatroom(companyName):
    idList = []
    for id in range(2, 500):
        if id % 3 == 0:
            idList.append("rgb(" + str(int(255/id)) + "," + str(0+(id*id*9)%200+55) + ", " + str(0+(id*10)%255) + ")")
        elif id % 3 == 1:
            idList.append("rgb(" + str(0+(id*id*9)%200+55) + "," + str(int(255/id)) + ", " + str(0+(id*10)%255) + ")")
        elif id % 3 == 2:
            idList.append("rgb(" + str(0+(id*10)%255) + "," + str(0+(id*id*9)%200+55) + ", " + str(int(255/id)) + ")")
    return render_template("chatroom.html", idList = json.dumps(idList))

@app.route("/c/<companyName>/p/logout/")
@login_required
def cLogout(companyName):
    logout_user()
    flash("Successfully Logged Out")
    return redirect(url_for('cIndex', companyName = companyName))

@app.route("/c/<companyName>/p/clock_in/")
@login_required
def cClock_in(companyName):
    conn = sqlite3.connect(path + 'databases/' + companyName + 'PaperlessTime.db')
    cur = conn.cursor()
    db = dbmgmt(conn, cur)
    clock_in_indicator = db.clock_in(current_user.get_clock_tuple())
    conn.close()
    if clock_in_indicator == 0:
        flash("You forgot to clock out last shift please notify an administrator")
        return redirect(url_for("cDashboard"))
    elif clock_in_indicator == 1:
        flash("You have succesfully clocked-in! Have a great day!")
        return redirect(url_for("cDashboard"))
    else:
        flash("System error! not clocked in please notify an administrator")
        return redirect(url_for("cIndex"))

@app.route("/c/<companyName>/p/clock_out/")
@login_required
def cClock_out(companyName):
    conn = sqlite3.connect(path + 'databases/' + companyName + 'PaperlessTime.db')
    cur = conn.cursor()
    db = dbmgmt(conn, cur)
    clock_in_indicator = db.clock_out(current_user.get_clock_tuple())
    conn.close()
    if clock_in_indicator == 0:
        flash("You forgot to clock in this shift please notify an administrator")
        return redirect(url_for("cDashboard"))
    elif clock_in_indicator == 1:
        flash("You have succesfully clocked-out! Have a great day!")
        return redirect(url_for("cDashboard"))
    else:
        flash("System error! not clocked out please notify an administrator")
        return redirect(url_for("cIndex"))

@app.route("/c/<companyName>/p/settings/", methods=['GET', 'POST'])
@login_required
def cSettings(companyName):
    #add seperate settings page for managers and employees to do things like turn off sms
    #also ensure the confirm modal works properly
    conn = sqlite3.connect(path + 'databases/' + companyName + 'PaperlessTime.db')
    cur = conn.cursor()
    db = dbmgmt(conn, cur)
    checkForm = confirmForm()
    form = settingsForm()
    form.employeeName.choices = getEmployeeNameList(companyName)
    form.removeEmployee.choices = getEmployeeNameList(companyName)
    if request.method == 'POST':
        configInfo = {"payPeriodLength": "", "daysAfterPayPeriod": "", "payPeriodStart": ""}
        try:
            file = open(path + "companyConfigs/" + companyName + "Config", 'r')
            configInfo = json.load(file)
            file.close()
            file = open(path + "companyConfigs/" + companyName + "Config", 'w')
        except:
            file = open(path + "companyConfigs/" + companyName + "Config", 'w')
        if form.payPeriodLength.data:
            configInfo["payPeriodLength"] = form.payPeriodLength.data
        if form.daysAfterPayPeriod.data:
            configInfo["daysAfterPayPeriod"] = form.daysAfterPayPeriod.data
        if form.payPeriodStart.data:
            configInfo["payPeriodStart"] = str(form.payPeriodStart.data)
        if form.employeeName.data != 'Select an Employee':
            if form.employeePosition.data:
                current_user.position = form.employeePosition.data
                db.update_employee_info()
            else:
                flash("please enter the new position for the employee")
        if form.removeEmployee.data != 'Select an Employee':
            modalActive = 1
            employeeToRemove = db.name_pull_employee_info(form.removeEmployee.data)
            db.delete_employee(employeeToRemove)

        json.dump(configInfo, file)
        file.close()
        form = settingsForm(formdata = None)
        flash("Settings Updated!")


    conn.close()
    return render_template("settings.html", form = form, companyName = companyName)

@app.route("/c/<companyName>/p/signup/")
def cSignup(companyName):
    return render_template('sign_up.html', companyName = companyName)

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
    app.run(host="0.0.0.0", port=8080, debug=True)

    #uncomment the below line to run deployment server
    #serve(app, host='0.0.0.0', port=8080)

    #potentially make it so that accessing kaiserk.pythonanywhere.com/mattressxpressny would go to that company app by loading a config file
    #that url variable would then stay as part of the url with request.path