#Kiam Kaiser
#CS498
#Professor Scott Spetka
from flask import Flask, render_template, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import InputRequired
from dbmgmt import dbmgmt
import sqlite3
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import secrets
import smtplib
import os
import time

# changing timezone for pythonanywhere comment out these two lines when not running local
#os.environ["TZ"] = "America/New_York"
#time.tzset()

firstwedsbeforepay = "12/21/22"

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "index"

# create Employee class
class employee(UserMixin):
    def __init__(self, employee_info):
        self.id = employee_info[0]
        self.name = employee_info[1]
        self.username = employee_info[2]
        self.password = employee_info[3]
        self.email = employee_info[4]
        self.phone_number = employee_info[5]
        self.clock_in_history = employee_info[6]

    def __str__(self):
        return f"{self.id}, {self.name}, {self.username}, {self.password},\
                {self.email}, {self.phone_number}, {self.clock_in_history}"

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

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('capstone.db')
    cur = conn.cursor()
    db = dbmgmt(conn, cur)
    emp_info = db.id_pull_employee_info(user_id)
    if emp_info == 0:
        return None
    return employee(emp_info)

# add_employee page
@app.route("/add_employee", methods=['GET', 'POST'])
def add_employee():
    # initializing db object
    conn = sqlite3.connect('capstone.db')
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
    conn = sqlite3.connect('capstone.db')
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

    return render_template("index.html", username = username, password = password, form = loginform())

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/schedule")
@login_required
def schedule():
    return render_template("notready.html")

@app.route("/chatroom")
@login_required
def chatroom():
    return render_template("notready.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Successfully Logged Out")
    return redirect(url_for('index'))

@app.route("/clock_in")
@login_required
def clock_in():
    conn = sqlite3.connect('capstone.db')
    cur = conn.cursor()
    db = dbmgmt(conn, cur)
    clock_in_indicator = db.clock_in(current_user.get_clock_tuple())
    if clock_in_indicator == 0:
        flash("You forgot to clock out last shift please notify an administrator")
        return redirect(url_for("dashboard"))
    elif clock_in_indicator == 1:
        return redirect(url_for("dashboard"))
    else:
        flash("System error! not clocked in please notify an administrator")
        return redirect(url_for("index"))

@app.route("/clock_out")
@login_required
def clock_out():
    conn = sqlite3.connect('capstone.db')
    cur = conn.cursor()
    db = dbmgmt(conn, cur)
    clock_in_indicator = db.clock_out(current_user.get_clock_tuple())
    if clock_in_indicator == 0:
        flash("You forgot to clock in this shift please notify an administrator")
        return redirect(url_for("dashboard"))
    elif clock_in_indicator == 1:
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

# Main Run Loop
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)