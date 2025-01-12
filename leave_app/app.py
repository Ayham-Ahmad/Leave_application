from flask import Flask, render_template, request, redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import DateTime, desc

# Initialize the Flask app
app = Flask(__name__)

# Configure and link the SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = r"sqlite:///C:/Users/Ayham/Downloads/Leave_application-main/Leave_application-main/leave_app/leave.db" 
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

userID = None

# Define the database models
# Define the Application database model
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employeeID = db.Column(db.Integer, nullable=False)
    startDate = db.Column(DateTime, nullable=False)
    endDate = db.Column(DateTime, nullable=False)
    reason = db.Column(db.String(9), nullable=False)
    status = db.Column(db.String(8), default='pending')
    submission = db.Column(DateTime, default=datetime.utcnow)
    

# Define the users database model
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(8), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
        

# Define the leave balance database model
class Balance(db.Model):
    balancesID = db.Column(db.Integer, primary_key=True)
    employeeID = db.Column(db.Integer)
    annual= db.Column(db.Integer, nullable=False)
    sick = db.Column(db.Integer, nullable=False)
    maternity = db.Column(db.Integer, nullable=False)
    emergency = db.Column(db.Integer, nullable=False)
    vacation = db.Column(db.Integer, nullable=False)
    paidTime = db.Column(db.Integer, nullable=False)


# Define the history database model
class History(db.Model):
    ApplicationID = db.Column(db.Integer, primary_key=True)
    resultDate = db.Column(DateTime, default=datetime.utcnow)

class Cookies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rememberMe = db.Column(db.Boolean)
    userID = db.Column(db.Integer)

# Define routes
@app.route("/", methods=['GET', 'POST'])
def index():

    global userType
    
    if request.method == 'POST':
        userType = request.form['type']
        # print(userType, 'noway')
        return redirect(url_for('login'))
    
    return render_template(
        "html/index.html",
        title="Home",
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    global userID  # Use the global variable

    error = False
    checked = False
    rememberMe = False

    cookie = Cookies.query.first()
    user = None

    if cookie and cookie.rememberMe:
        user = Users.query.filter_by(id=cookie.userID).first()
        checked = True

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        rememberMe = request.form.get('rememberMe')

        user = Users.query.filter_by(username=username).first()

        if user and user.password == password:  
            userID = user.id
            if rememberMe:
                cookie.rememberMe = True
                checked = True
                cookie.userID = user.id
            else:
                cookie.rememberMe = False
                checked = False
                cookie.userID = None
            db.session.commit()

            if user.type == 'employee':
                return redirect(url_for('employee_fun'))
            elif user.type in ['manager', 'hr']:
                return redirect(url_for('hr_fun'))

        error = True

    return render_template(
        "html/login.html",
        title="Login",
        custom_css="login",
        error=error,
        checked=checked,
        user=user
    )


@app.route('/login/employee_fun', methods=['GET', 'POST'])
def employee_fun():
    # Get the user from the database using the global userID
    user = Users.query.filter_by(id=userID).first()

    if not user:
        return redirect(url_for('login'))  # Redirect if no user is logged in

    if request.method == 'POST':
        function = request.form['function']

        if function == 'application_form':
            return redirect(url_for('application_form'))
        elif function == 'leave_balance':
            return redirect(url_for('leave_balance'))
        elif function == 'view_history':
            return redirect(url_for('employee_history'))

    return render_template(
        "html/employee_fun.html",
        title="Employee Functions",
        name=user.name
    )

@app.route('/login/hr_fun', methods=['GET', 'POST'])
def hr_fun():

    user = Users.query.filter_by(id=userID).first()

    print("outside")
    if request.method == 'POST':
        function = request.form['function']
        print(function)

        if function == 'request_list':
            return redirect(url_for('request_list'))
        elif function == 'hr_history':
            print("inside ")
            return redirect(url_for('hr_history'))
    
    return render_template(
        "html/hr_fun.html",
        title="Manager/HR History",
        name=user.name
    )

@app.route('/login/employee_fun/application_form', methods=['GET', 'POST'])
def application_form():

    global userID

    if request.method == 'POST':
        startDate = request.form['startDate']
        endDate = request.form['endDate']
        reason = request.form['reason']

        startDate, endDate = convert_data_to_objects(startDate, endDate)

        try:
            new_form = Application(startDate=startDate, endDate=endDate, reason=reason, employeeID=userID)

            db.session.add(new_form)
            db.session.commit()
            print(f"Application form added successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"An error occurred while adding application form: {e}")
        

        return redirect(url_for("submission"))
        

    return render_template(
        "html/application_form.html",
        title="Application Form",
        userID=userID
    )

@app.route("/login/employee_fun/application_form/submission")
def submission():
    return render_template(
        "html/submission.html",
        title="Submission",
    )

@app.route('/login/employee_fun/leave_balance', methods=['GET', 'POST'])
def leave_balance():

    leave_balance = Balance.query.filter_by(employeeID=userID).first()

    return render_template(
        "html/leave_balance.html",
        title="Leave balance",
        leave_balance=leave_balance    
    )

@app.route('/login/employee_fun/employee_history', methods=['GET', 'POST'])
def employee_history():
    history = Application.query.filter_by(employeeID=userID)\
                           .order_by(desc(Application.submission))\
                           .all()

    return render_template(
        "html/employee_history.html",
        title="Employee History",
        history=history if history else [] 
    )


@app.route('/login/hr_fun/request_list', methods=['GET', 'POST'])
def request_list():
    requests = db.session.query(Application, Users, Balance) \
                    .join(Users, Application.employeeID == Users.id) \
                    .join(Balance, Application.employeeID == Balance.employeeID) \
                    .filter(Application.status == 'pending') \
                    .order_by(Application.submission.desc()) \
                    .group_by(Application.id)\
                    .all()


    if request.method == 'POST':
        selected_ids = request.form.getlist('selected_ids')
        status = request.form['status']

        # Update the selected forms
        forms = Application.query.filter(Application.id.in_(selected_ids)).all()
        for form in forms:
            form.status = status
            if form.status == 'approved':
                balance = Balance.query.filter_by(employeeID=form.employeeID).first()
                if balance:
                    days = (form.endDate - form.startDate).days
                    if form.reason == 'annual':
                        balance.annual -= days
                    elif form.reason == 'sick':
                        balance.sick -= days
                    elif form.reason == 'maternity':
                        balance.maternity -= days
                    elif form.reason == 'emergency':
                        balance.emergency -= days
                    elif form.reason == 'vacation':
                        balance.vacation -= days
                    elif form.reason == 'paidTime':
                        balance.paidTime -= days

            # Update history for the selected forms
            history_entries = History.query.filter_by(ApplicationID=form.id).all()
            for hist in history_entries:
                hist.ApplicationID = form.id

        db.session.commit()
        return redirect(url_for('request_list'))

    return render_template(
        "html/request_list.html",
        title="Request List",
        requests=requests,
    )


@app.route('/login/hr_fun/hr_history')
def hr_history():

    history = db.session.query(Application, Users)\
                        .join(Users, Application.employeeID == Users.id)\
                        .filter(Application.status != 'pending')\
                        .order_by(desc(Application.submission))\
                        .all()

    return render_template(
        "html/hr_history.html",
        title="Manager/HR History",
        history=history
    )


# Convert date and time strings to datetime and time objects
def convert_data_to_objects(startDate, endDate):

    startDate = datetime.strptime(startDate, '%Y-%m-%d').date()
    endDate = datetime.strptime(endDate, '%Y-%m-%d').date()

    return startDate, endDate
    

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print(__name__)
    app.run(debug=True)
