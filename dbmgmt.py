#Kiam Kaiser
#CS498
#Professor Scott Spetka
import sqlite3
import datetime
import re
import json
from werkzeug.security import generate_password_hash, check_password_hash


class dbmgmt():
    # add a way to retroactivly update missing days
    # ----------------------------------defining variables-------------------------
    # Variable name key:
    #   sel = selected
    #   emp = employee
    conn = sqlite3.connect('PaperlessTime.db')
    cur = conn.cursor()
    # test variables
    clock_in_array = [(int(datetime.datetime.now().strftime("%Y%m%d%H%M%S")), 1),
                      (int(datetime.datetime.now().strftime("%Y%m%d%H%M%S")), 0),
                      (0, 0)]
    test_employee_w_id = (0, 'bob flanner', 'bflanner', '123', 'bflanner@yahoo.com', 5185555555, clock_in_array,)
    test_employee = ('Aaron Smith', 'Asmith', '456', 'aaronsmith@yahoo.com', '518-218-0700', 0)


    def __init__(self, conn, cur):
        self.conn = conn
        self.cur = cur
        
        # Creating the table for employees if it does not exist
        #position: 0 = employee, 1 = manager, 2 = owner
        #smsOptIn: 0 for no, 1 for yes
        cur.execute("""CREATE TABLE IF NOT EXISTS employees(
        employee_id INT PRIMARY KEY,
        name TEXT,
        username TEXT,
        password TEXT,
        email TEXT,
        phone_number INT,
        company TEXT,
        position INT,
        clock_in_history LONG VARCHAR,
        smsOptIn INT
        );
        """)

    #check if employees has entries, if not it is time to create the owner account
    def check_content(self):
        self.cur.execute("SELECT * FROM employees WHERE employee_id=1")
        if self.cur.fetchall():
            return 1
        else:
            return 0

    # add a new employee to the employee table. return 0 if fail and 1 if success
    # add_new_employee(name TEXT, username TEXT, password TEXT, email TEXT, phone_number INT, position INT)
    def add_new_employee(self, employee_info):
        # the 7 lines below pull the prior empid from the database and turn it into an int
        self.cur.execute("""CREATE TABLE IF NOT EXISTS employees(
            employee_id INT PRIMARY KEY,
            name TEXT,
            username TEXT,
            password TEXT,
            email TEXT,
            phone_number INT,
            company TEXT,
            position INT,
            clock_in_history LONG VARCHAR,
            smsOptIn INT
        );
        """)
        self.cur.execute("SELECT employee_id FROM employees;")
        empid = self.cur.fetchall()
        
        #try to find the previous user empid and if there is no previous user set empid to 0
        try:
            empid = str(empid[len(empid)-1])
            empid = empid.replace('(', '')
            empid = empid.replace(',', '')
            empid = empid.replace(')', '')
            empid = int(empid)
        except(IndexError):
            empid = 0
        

        # The 14 lines below ensure that the same employee will not be entered twice return 0 if fail
        self.cur.execute("SELECT name FROM employees;")
        empname = self.cur.fetchall()
        i = 0
        for name in empname:
            empname[i] = str(name)
            empname[i] = empname[i].replace('(', '')
            empname[i] = empname[i].replace(',', '')
            empname[i] = empname[i].replace(')', '')
            empname[i] = empname[i].replace("'", '')
            empname[i] = empname[i].lower()
            if str(employee_info[0]).lower().replace(' ', '') == empname[i].replace(' ', ''):
                print("A user with this name already exists")
                return(0)
            i += 1

        # The 14 lines below ensure that the same username will not be entered twice return 2 if fail
        self.cur.execute("SELECT username FROM employees;")
        empname = self.cur.fetchall()
        i = 0
        for name in empname:
            empname[i] = str(name)
            empname[i] = empname[i].replace('(', '')
            empname[i] = empname[i].replace(',', '')
            empname[i] = empname[i].replace(')', '')
            empname[i] = empname[i].replace("'", '')
            empname[i] = empname[i].lower()
            if str(employee_info[1]).lower().replace(' ', '') == empname[i].replace(' ', ''):
                print("A user with this username already exists")
                return(2)
            i += 1

        # the lines below hash the password to ensure it is secure
        password_hash = generate_password_hash(employee_info[2])

        # the lines below ensure that the tuple is properly formatted and add the correct employee_id
        list_employee_info = list(employee_info)
        list_employee_info[1] = list_employee_info[1].lower()
        list_employee_info[2] = password_hash
        if type(list_employee_info[4]) != int:
            list_employee_info[4] = re.sub(r'[^0-9]', '', list_employee_info[4])
        list_employee_info.insert(0, empid+1)
        
        self.cur.execute("SELECT * FROM employees")
        if self.cur.fetchall():
            #line below is for position set to employee if the database is not empty
            list_employee_info.append(0)
        else:
            #line below is for position, set to owner if the database was previously empty
            list_employee_info.append(2)
        #line below converts an array of clock in info to JSON to be stored in the database
        list_employee_info.append(json.dumps([(0, 0), ]))
        #line below is for smsOptIn
        list_employee_info.append(1)
        employee_info = tuple(list_employee_info)
        self.cur.execute("""
            INSERT INTO employees(employee_id, name, username, password, email, phone_number, company, position, clock_in_history, smsOptIn)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""", employee_info)
        self.conn.commit()
        return(1)

    # pulls a list of employee names in the form of a tuple
    def pull_employee_name_list(self):
        self.cur.execute("SELECT name FROM employees")
        sel_emp = self.cur.fetchall()
        
        return sel_emp

    # pulls employee info and returns that info in the form of a tuple given login info as a tuple
    def pull_employee_info(self, login_info):
        self.cur.execute("SELECT * FROM employees WHERE username = ?", (login_info[0], ))
        sel_emp = self.cur.fetchall()
        try:
            sel_emp = list(sel_emp[0])
        except IndexError:
            print("This username could not be found")
            return 0

        if not check_password_hash(sel_emp[3], login_info[1]):
            print("This password could not be found")
            return 1

        #converting clock in history from JSON to an array
        sel_emp[8] = json.loads(sel_emp[8])
        return sel_emp


    # pulls employee info and returns that info in the form of a tuple given employee id
    def id_pull_employee_info(self, given_id):
        self.cur.execute("SELECT * FROM employees WHERE employee_id = ?", given_id)
        sel_emp = self.cur.fetchall()
        try:
            sel_emp = list(sel_emp[0])
        except IndexError:
            print("The employee with that id could not be found")
            return 0
        sel_emp[8] = json.loads(sel_emp[8])
        return sel_emp
    
    # pulls employee info and returns that info in the form of a tuple given employee name
    def name_pull_employee_info(self, given_name):
        self.cur.execute("SELECT * FROM employees WHERE name = " + "\'" + given_name + "\'")
        sel_emp = self.cur.fetchall()
        try:
            sel_emp = list(sel_emp[0])
        except IndexError:
            print("The employee with that name could not be found")
            return 0
        sel_emp[8] = json.loads(sel_emp[8])
        return sel_emp


    # updates the entire employee row given a tuple with contains all of an employees info
    def update_employee_info(self, emp_info):
        # add section to ensure updated info doesnt override existing
        emp_info = list(emp_info)
        emp_info[7] = json.dumps(emp_info[7])
        
        #adding empployee_id to the end of the list for the SQLite call at the end
        emp_info.append(emp_info[0])

        # The 14 lines below ensure that an employee will not be updated to have the same name as another
        self.cur.execute("SELECT name FROM employees;")
        empname = self.cur.fetchall()
        i = 0
        for name in empname:
            empname[i] = str(name)
            empname[i] = empname[i].replace('(', '')
            empname[i] = empname[i].replace(',', '')
            empname[i] = empname[i].replace(')', '')
            empname[i] = empname[i].replace("'", '')
            empname[i] = empname[i].lower()
            if str(emp_info[1]).lower().replace(' ', '') == empname[i].replace(' ', ''):
                self.cur.execute("SELECT employee_id FROM employees WHERE name = ?", (empname[i], ))
                empnum = str(self.cur.fetchone())
                empnum = empnum.replace('(', '').replace(',', '').replace(')', '')
                if int(emp_info[0]) != int(empnum):
                    print("A user cannot be updated so that it has the same name as another existing user")
                    return ()
            i += 1

        self.cur.execute("""
            UPDATE employees
            SET employee_id = ?, name = ?, username = ?, password = ?, email = ?, phone_number = ?, company, clock_in_history = ?, position = ?, smsOptIn = ?
            WHERE employee_id = ?""", emp_info)
        self.conn.commit()


    # updates only the clock in history for a user given a tuple with the employee_id and clock in history
    # 0 with the tuple shows a clock-in event, 1 shows a clock out event, 3 shows a clocked-in but never clocked-out event
    # (forgot to clock out), 4 shows a clocked out but never clocked in (forgot to clock in)
    def clock_in(self, emp_info):
        emp_info = list(emp_info)
        if emp_info[1][0][1] == 0:
            emp_info[1][0][1] = 3
            return 0
        emp_info[1].insert(0, (int(datetime.datetime.now().strftime("%Y%m%d%H%M%S")), 0))
        emp_info = (json.dumps(emp_info[1]), emp_info[0])
        self.cur.execute("UPDATE employees SET clock_in_history = ? WHERE employee_id = ?", emp_info)
        self.conn.commit()
        return 1


    def clock_out(self, emp_info):
        emp_info = list(emp_info)
        if emp_info[1][0][1] == 1:
            print("You forgot to clock in this shift please talk to the boss")
            emp_info[1][0][1] = 4
            return 0
        emp_info[1].insert(0, (int(datetime.datetime.now().strftime("%Y%m%d%H%M%S")), 1))
        emp_info = (json.dumps(emp_info[1]), emp_info[0])
        self.cur.execute("UPDATE employees SET clock_in_history = ? WHERE employee_id = ?", emp_info)
        self.conn.commit()
        return 1

    #delete an employee given the employee name
    def delete_employee(self, emp_info):
        self.cur.execute("DELETE FROM employees WHERE employee_id = ?", (emp_info[0], ))
        self.conn.commit()
        


# -------------------section for manually managing the database below --------------------
#conn = sqlite3.connect('PaperlessTime.db')
#cur = conn.cursor()

#cur.execute("UPDATE employees SET position = 2 WHERE employee_id = 1")
#conn.commit()
#db = dbmgmt(conn, cur)
