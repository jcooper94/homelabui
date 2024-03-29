# Standard Library Imports
import logging
from datetime import datetime, timedelta
import os
from pathlib import Path
import time
import threading

# Third-Party Library Imports
from flask import Flask, jsonify, redirect, render_template, url_for
from flask_bcrypt import Bcrypt
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length
import psutil
from uptime import uptime

# Local Imports
from software_list import get_apps
from bandwidth import get_bandwidth
from scrape import scrape_wikipedia_main_page
from storage import storage
from weather import get_weather_data
from bandwidth import get_bandwidth
# TO DO LIST :
#   - time day date
#   - pass data from docker to application list
#loop over app containers and create routes for url redirects

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
import os
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
app.config['SECRET_KEY'] = 'thisisasecretkey'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# with app.app_context():
#     db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')

# def file_is_old(file_path, hours_threshold=2):
#     file_path = Path(file_path)
#     return file_path.exists() and (datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime) > timedelta(hours=hours_threshold))

# file_path = "ui_data.json"

#         if file_is_old(file_path):
#             ui_data = get_weather_data()

#             with open(file_path, 'w') as file:
#                 file.write(str(ui_data))
#         else:
#             print("Data isn't old.")

# @app.route('/wiki')
# def wiki_route():
#     # File path
#     file_path = 'static/data/wiki_news.html'
#     # Check if the file exists and is older than 2 hours
#     if file_is_old(file_path):
#         # Run the method if the conditions are met
#         scrape_wikipedia_main_page()
#         return "Scraping Wikipedia Main Page..."
#     else:
#         return "File was modified within the last 2 hours."



@app.route('/storage')
def storageroute():
    storage_data = storage()
    return storage_data

@app.route('/bandwidth')
def bandwidthroute():
    bandwidth_usage = get_bandwidth()
    print(bandwidth_usage)
    return bandwidth_usage

@app.route('/uptime')
def server_up():
    server_up = uptime()
    return server_up

@app.route('/utilization')
def utilization():
    cpu = f"CPU utilization: {psutil.cpu_percent()}%"
    mem = f" \n Memory utilization: {psutil.virtual_memory().percent}%"
    return jsonify({'cpu': cpu, 'mem': mem})

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    try:
        if form.validate_on_submit():
            print("Form is valid")
            user = User.query.filter_by(username=form.username.data).first()
            print("User:", user)
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                print("Password is correct")
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                print("Password is incorrect")
        else:
            print("Form is not valid")
    except Exception as e:
        print("Error:", e)
    return render_template('login.html', form=form)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    apps = get_apps()
    bandwidth_data = get_bandwidth()
    return render_template('dashboard.html', apps=apps, bandwidth_data=bandwidth_data)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/plex')
def plex():
    return redirect("https://app.plex.tv/desktop/?_gl=1*1n8rd66*_ga*NTQwNTQwMTkzLjE3MDIwNjU1NTY.*_ga_G6FQWNSENB*MTcwMzA3NjA0Ny4zLjEuMTcwMzA3NjEyMi42MC4wLjA.#!/media/b58766b8d9e142033a9dea6f927eca5df97dead7/com.plexapp.plugins.library?source=2")

@app.route('/portainer')
def portainer():
    return redirect("https://192.168.1.144:9443/#!/auth")

@app.route('/overseerr')
def overseerr():
    return redirect("http://192.168.1.144:5055")

@app.route('/radarr')
def radarr():
    return redirect("http://192.168.1.144:7878/")

@app.route('/sonarr')
def sonarr():
    return redirect("http://192.168.1.144:8989/")

@app.route('/lidarr')
def lidarr():
    return redirect("http://192.168.1.144:8686/")

@app.route('/prowlarr')
def prowlarr():
    return redirect("http://192.168.1.144:9696")

@app.route('/qbittorrent')
def qbittorrent():
    return redirect("http://192.168.1.144:8085")

@app.route('/proxmox')
def proxmox():
    return redirect("http://192.168.1.199:8006")

@app.route('/opnsense')
def opnsense():
    return redirect("http://192.168.1.1")

@app.route('/syncthing')
def syncthing():
    return redirect("http://192.168.1.144:8384")

@app.route('/zealous_taussig')
def metube():
    return redirect("http://192.168.1.144:8081/")

# Set the base directory for the 'static' folder
base_dir = os.path.dirname(__file__)

# Define paths relative to /static/data without double slashes
wiki_news_path = os.path.normpath(os.path.join(base_dir, 'static', 'data', 'wiki_news.html'))
ui_data_path = os.path.normpath(os.path.join(base_dir, 'static', 'data', 'ui_data.json'))
update_interval = 14400  # 4 hours in seconds

def check_and_update_files():
    while True:
        if file_is_old(wiki_news_path):
            scrape_wikipedia_main_page()  # Run the scrape function when wiki_news.html is older than 4 hours

        if file_is_old(ui_data_path):
            ui_data = get_weather_data()

            with open(ui_data_path, 'w') as file:
                file.write(str(ui_data))
            print("UI data updated.")

        time.sleep(update_interval)

def file_is_old(file_path):
    # Implement the logic to check if the file is older than 4 hours
    current_time = time.time()
    file_modified_time = os.path.getmtime(file_path)
    return (current_time - file_modified_time) > update_interval

if __name__ == "__main__":
    if os.name == 'posix':
        app.run(host='192.168.1.144', port=9000)
    else:
        app.run()
        print('local development')
    # Start a thread for the periodic file checks and updates
    update_thread = threading.Thread(target=check_and_update_files)
    update_thread.start()
    # Keep the main thread running
    while True:
        time.sleep(1)