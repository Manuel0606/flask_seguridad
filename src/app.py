from flask import Flask, render_template, request, redirect, url_for, flash
from config import *
from flask_login import LoginManager, login_user, logout_user, login_required
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from models.ModelUser import ModelUser
from models.entities.User import User

app = Flask(__name__)

csrf = CSRFProtect()

con_bd = EstablecerConexion()

limiter = Limiter(app=app, key_func=get_remote_address)

login_manager_app = LoginManager(app)

@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(con_bd, id)

@app.route('/')
def index():
    crearTablaUsers()
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10/minute")
def login():
    crearTablaUsers()
    if request.method == 'POST':
        # print(request.form['correo'])
        # print(request.form['password'])
        user = User(0, request.form['correo'], request.form['password'])
        logged_user = ModelUser.login(con_bd, user)
        if logged_user != None:
            if logged_user.password:
                login_user(logged_user)
                return redirect(url_for('home'))
            else:
                print('Contraseña invalida')
                return render_template('auth/login.html')
        else:
            print('Usuario no encontrado')
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html')

@app.route('/new_user')
def new_user():
  return render_template('auth/new.html')

@app.route('/signup', methods=['POST'])
def add_user():
  crearTablaUsers()
  cursor = con_bd.cursor()
  form = request.form
  correo = form['correo']
  password = User.passwordHash(form['password'])
  if correo and password:
    sql = """
    INSERT INTO
      users (
        correo,
        password
      )
      VALUES
      ( %s, %s);
    """
    cursor.execute(sql,(correo, password))
    con_bd.commit()
    return redirect(url_for('index'))
  else:
    return "Error"

@app.route('/home')
@login_required
def home():
    return render_template('home.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


def crearTablaUsers():
    cursor = con_bd.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(
        id serial NOT NULL,
        correo character varying(30),
        password character varying(160),
        CONSTRAINT pk_user_id PRIMARY KEY (ID)
        );
    ''')
    con_bd.commit()

def status_401(error):
    return redirect(url_for('login'))

def status_404(error):
    return "<h1>Página no encontrada</h1>", 404

if __name__ == '__main__':
    app.config.from_object(config['development'])
    csrf.init_app(app)
    app.register_error_handler(401, status_401)
    app.register_error_handler(404, status_404)
    app.run(port=5001)