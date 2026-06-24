# app/app.py
# fabrica de aplicaciones flask, inicializa extensiones y registra blueprints

from flask import Flask
from flask_migrate import Migrate
from app.config import Config
from app.extensions import db, bcrypt, login_manager
# importa todos los modelos para que Alembic los detecte
import app.models
import click
from app.models import Role, User

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

    # -------------------------------------------------------------
    # comando personalizado para sembrar la base de datos
    # -------------------------------------------------------------
    @app.cli.command("seed")
    # parainsertar roles y usuario admin flask seed desde terminal
    def seed():
        """creación los roles basicos y un usuario administrador."""
        # crear roles si no existen
        if not Role.query.filter_by(nombre="administrador").first():
            db.session.add(Role(nombre="administrador"))
        if not Role.query.filter_by(nombre="cliente").first():
            db.session.add(Role(nombre="cliente"))
        db.session.commit()

        # crear usuario admin por defecto si no existe
        if not User.query.filter_by(username="admin").first():
            from app.extensions import bcrypt
            admin_role = Role.query.filter_by(nombre="administrador").first()
            hashed_pw = bcrypt.generate_password_hash("123").decode("utf-8")
            admin_user = User(
                username="admin",
                email="admin@libreria.com",
                password=hashed_pw,
                rol_id=admin_role.id
            )
            db.session.add(admin_user)
            db.session.commit()
            print("usuario admin creado (admin / 123)")
        print("datos sembrados correctamente.")

    # importar y registrar blueprints
    from app.main.routes import main_bp
    from app.auth.routes import auth_bp
    from app.categories.routes import categories_bp
    
    # registro de los blueprints con sus prefijos
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(categories_bp, url_prefix="/categories")
    
    return app

