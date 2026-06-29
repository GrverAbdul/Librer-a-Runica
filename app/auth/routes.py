# app/auth/routes.py
# rutas de autenticacion (login, registro, cierre de sesion)

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.extensions import db, bcrypt
from app.models import User, Role, Customer

auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="templates"   # carpeta dentro de app/auth
)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # verificar si el usuario o correo ya existen
        if User.query.filter_by(username=username).first():
            flash("el nombre de usuario ya existe", "danger")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("el correo electronico ya esta registrado", "danger")
            return redirect(url_for("auth.register"))

        # encriptar la contraseña
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # asignar el rol "cliente" por defecto a nuevos registros
        rol_cliente = Role.query.filter_by(nombre="cliente").first()
        if not rol_cliente:
            # si no existe el rol cliente, lo creamos (por si acaso)
            rol_cliente = Role(nombre="cliente")
            db.session.add(rol_cliente)
            db.session.commit()

        # crear nuevo usuario
        nuevo_usuario = User(
            username=username,
            email=email,
            password=hashed_password,
            rol_id=rol_cliente.id
        )

        db.session.add(nuevo_usuario)
        # crear perfil de cliente automático
        db.session.flush()   # para obtener el id del usuario recién creado
        perfil = Customer(usuario_id=nuevo_usuario.id)   # nombre y apellido se rellenan después
        db.session.add(perfil)
        db.session.commit()

        flash("registro exitoso. ahora puedes iniciar sesion.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # buscar el usuario por nombre de usuario
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("inicio de sesion correcto", "success")
            # redirigir a la pagina principal o al dashboard segun el rol
            return redirect(url_for("main.index"))
        else:
            flash("nombre de usuario o contraseña incorrectos", "danger")

    return render_template("auth/login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("sesion cerrada correctamente", "info")
    return redirect(url_for("main.index"))