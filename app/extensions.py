# app/extensions.py
# inicializacion de las extensiones de flask

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

# objeto de base de datos (orm)
db = SQLAlchemy()

# objeto para encriptar contraseñas
bcrypt = Bcrypt()

# objeto para manejar el inicio de sesion
login_manager = LoginManager()
# vista a la que redirige si el usuario no esta autenticado
login_manager.login_view = "auth.login"
# mensaje de aviso
login_manager.login_message = "por favor inicia sesion para acceder a esta pagina."
# categoria del mensaje flash
login_manager.login_message_category = "warning"