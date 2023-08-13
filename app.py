from cs50 import SQL
from datetime import date
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from random import choice
from validation import enforce_password
from werkzeug.security import check_password_hash, generate_password_hash

# Configure Flask application
app = Flask(__name__)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Configure SQLite database using CS50 library
db = SQL('sqlite:///journely.db')

# Global lists of moods and goals to easily change all instances across the app
MOODS = [
    'happy',
    'content',
    'neutral',
    'discontent',
    'unhappy'
]

# If changing goals, sql db and execute queries will need to be changed as well
GOALS = [
    'sleep',
    'exercise',
    'outdoors',
    'gratitude',
    'meditation'
]

# If changing a goal, change the text that gets passed to the HTML as well
GOALS_TEXT = [
    'Slept Well',
    'Exercised',
    'Spent Time Outdoors',
    'Fostered Gratitude',
    'Meditated'
]


@app.after_request
def after_request(response):
    """Disable response caching, copied from CS50 Finance project"""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Expires'] = 0
    response.headers['Pragma'] = 'no-cache'
    return response


#TODO
@app.route('/')
def index():
    """Show current day's journal form"""
    # Redirect if user is not logged in
    if 'username' not in session:
        return redirect('/login')

    username = session['username']

    # TODO add more messages. Implement dynamism? Like adjust messages based on user's past data?
    # Lists of random messages to greet the user with
    greeting_messages = [
        f'Hello again, {username}.',
        f'Welcome back, {username}.',
        f'Good to see you, {username}.',
        f'Good day, {username}.'
    ]
    prompt_messages = [
        'Let\'s see how you\'re doing.',
        'Hope your day is well.',
        'Let\'s check in with your self.',
        'Ready to log your day?',
        'Let\'s add to your journal.',
        'Time for a check-in.'
    ]

    # Randomly select two messages from the lists
    flash(choice(greeting_messages), category='greeting')
    flash(choice(prompt_messages), category='prompt')

    # If journal entry was already submitted for day, pre-check form items when page is revisited
    current_date = date.today()
    existing_entry = db.execute('SELECT mood, sleep, exercise, outdoors, gratitude, meditation FROM journal WHERE username = ? AND date = ?;', username, current_date)

    # Variables to store existing entry values if journal entry was already submitted
    mood_checked = ''
    goals_checked = []

    if existing_entry:
        flash('Your journal entry has been recorded for the day. Would you like to make some changes?')

        # db.execute will return a single-item list of a dict. Remove list wrapper
        existing_entry = existing_entry[0]

        # Pop the mood value from the journal entry
        mood_checked = existing_entry.pop('mood')

        # Create list of previously checked goals so we know what checkboxes to pre-check when rendering HTML
        for goal, checked in existing_entry.items():
            if checked:
                goals_checked.append(goal)

    return render_template(
        'index.html', date=current_date, moods=MOODS, mood_checked=mood_checked, goals=zip(GOALS, GOALS_TEXT), goals_checked=goals_checked)


@app.route('/delete_account', methods=['GET', 'POST'])
def deregister():
    """ Delete user's account from database """
    if request.method == 'POST':
        username = session['username']
        password = request.form.get('password')

        # Verify password
        user = db.execute('SELECT * FROM users WHERE username = ?;', username)
        if not check_password_hash(user[0]['hash'], password):
            flash('Password given does not match the one on file')
            return redirect('/delete_account')

        # Log user out before deleting db entry
        session.clear()

        # Remove user from database
        db.execute('DELETE FROM users WHERE username = ?;', username)

        flash('Your account was successfully deleted')
        return redirect('/')

    elif request.method == 'GET':
        # If user is not logged in, redirect to login
        if 'username' not in session:
            return redirect('/login')
        else:
            return render_template('deregister.html')


@app.route('/journal')
def journal():
    # Redirect if user is not logged in
    if 'username' not in session:
        return redirect('/login')

    # Retrieve history of all user's previous entries
    history = db.execute('SELECT date, mood, sleep, exercise, outdoors, gratitude, meditation FROM journal WHERE username = ? ORDER BY date DESC;', session['username'])

    return render_template('journal.html', history=history)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Handle user login """
    if request.method == 'POST':
        # Get user-submitted login info
        username = request.form.get('username')
        password = request.form.get('password')

        # Ensure username and password aren't empty
        if not username:
            flash('Username field cannot be blank', category='error')
            return redirect('/login')
        elif not password:
            flash('Password field cannot be blank', category='error')
            return redirect('/login')

        # Ensure user exists and password is correct
        user = db.execute('SELECT * FROM users WHERE username = ?;', username)
        if not user:
            flash(f'No user named "{username}" is currently registered')
            return redirect('/login')
        elif not check_password_hash(user[0]['hash'], password):
            flash('Incorrect password')
            return redirect('/login')

        # Credentials verified, log user in
        session['username'] = user[0]['username']
        flash('Logged in successfully', category='info')
        return redirect('/')

    elif request.method == 'GET':
        # If user is already logged in, redirect to homepage
        if 'username' in session:
            return redirect('/')
        else:
            return render_template('login.html')


@app.route('/logout')
def logout():
    """ Log user out """
    session.clear()

    flash('You are logged out')
    return redirect('/')


@app.route('/recorded', methods=['POST'])
def recorded():
    # Get values from user-submitted journal entry
    mood = request.form.get('mood')
    checked_goals = request.form.getlist('goals')

    # Input validation
    if mood not in MOODS:
        flash('Please select one of the given moods')
        return redirect('/')

    # Filter out any goals the user might have added in
    checked_goals = [goal for goal in checked_goals if goal in GOALS]

    # Initialize dictionary to keep track of what fields user checked
    goals_selected = {}
    for goal in GOALS:
        goals_selected[goal] = 0

    # Change value to 1 for all checked goals
    for goal in checked_goals:
        goals_selected[goal] = 1

    # Convert to a simple list of 0's and 1's for SQL execution
    db_values = list(goals_selected.values())
    print(db_values)

    # Record entry in database
    username = session['username']
    current_date = date.today()
    if db.execute('SELECT 1 FROM journal WHERE username = ? AND date = ?;', username, current_date):
        # Entry already exists, update instead of inserting
        db.execute('UPDATE journal SET mood = ?, sleep = ?, exercise = ?, outdoors = ?, gratitude = ?, meditation = ? WHERE username = ? AND date = ?;', mood, db_values[0], db_values[1], db_values[2], db_values[3], db_values[4], username, current_date)
    else:
        db.execute('INSERT INTO journal (username, date, mood, sleep, exercise, outdoors, gratitude, meditation) VALUES (?, ?, ?, ?, ?, ?, ?, ?);', username, current_date, mood, db_values[0], db_values[1], db_values[2], db_values[3], db_values[4])

    return redirect('/journal')


#TODO
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get values from user-submitted registration form
        username = request.form.get('username')
        password = request.form.get('password')
        confirmation = request.form.get('confirmation')

        # Input validation
        if not username:
            flash('Username field cannot be blank', category='error')
            return redirect('/register')
        elif not password:
            flash('Password field cannot be blank', category='error')
            return redirect('/register')
        elif not confirmation:
            flash('Confirmation password field cannot be blank', category='error')
            return redirect('/register')
        elif password != confirmation:
            flash('Confirmation and password fields must be the same', category='error')
            return redirect('/register')

        # TODO enforce minimum password requirements
        # if enforce_password(password, min_characters=0, req_lower=False, req_upper=False, req_digit=False, req_symbol=False):
        #   do stuff

        # If username is already registered, alert user and abort registration
        if db.execute('SELECT 1 FROM users WHERE UPPER(username) = ?;', username.upper()):
            flash('A user is already reigstered with that username. Did you mean to log in?', category='info')
            return redirect('/register')

        # Hash password, store user in database, and log user in
        hash = generate_password_hash(password)
        db.execute('INSERT INTO users (username, hash) VALUES (?, ?);', username, hash)
        session['username'] = username

        # Return user to homepage
        return redirect('/')

    elif request.method == 'GET':
        # If user is already logged in, redirect to homepage
        if 'username' in session:
            return redirect('/')
        else:
            return render_template('register.html')