# app/app.py
# fabrica de aplicaciones flask, inicializa extensiones y registra blueprints

from flask import Flask
from flask_migrate import Migrate
from app.config import Config
from app.extensions import db, bcrypt, login_manager
# importa todos los modelos para que Alembic los detecte
import app.models
migrate = Migrate()

def create_app():
    # crear la instancia de la aplicacion
    app = Flask(__name__)

    # cargar configuracion desde la clase config (y variables de entorno)
    app.config.from_object(Config)

    # inicializar extensiones con la aplicacion
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # registra el cargador de usuarios para flask-login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # importar y registrar blueprints
    from app.main.routes import main_bp
    from app.auth.routes import auth_bp
    from app.categories.routes import categories_bp
    
    # registro de los blueprints con sus prefijos
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(categories_bp, url_prefix="/categories")
    
    return app

