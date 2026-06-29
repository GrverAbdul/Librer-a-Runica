# app/users/routes.py
# rutas de gestion de usuarios (solo administrador)

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models import User, Role
from app.decorators import admin_required

users_bp = Blueprint(
    "users",
    __name__,
    template_folder="templates"
)

# ------------------------------------------------------------
# listar todos los usuarios
# ------------------------------------------------------------
@users_bp.route("/")
@login_required
@admin_required
def index():
    usuarios = User.query.order_by(User.username).all()
    return render_template("users/index.html", usuarios=usuarios)

# ------------------------------------------------------------
# editar usuario (cambiar rol)
# ------------------------------------------------------------
@users_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit(id):
    usuario = User.query.get_or_404(id)
    roles = Role.query.all()

    if request.method == "POST":
        # evitar cambiar el rol del propio admin (opcional)
        nuevo_rol_id = request.form.get("rol_id", type=int)
        if nuevo_rol_id:
            usuario.rol_id = nuevo_rol_id
            db.session.commit()
            flash("rol actualizado correctamente", "success")
        return redirect(url_for("users.index"))

    return render_template("users/edit.html", usuario=usuario, roles=roles)

# ------------------------------------------------------------
# eliminar usuario (excepto al admin actual para no quedarse sin acceso)
# ------------------------------------------------------------
@users_bp.route("/delete/<int:id>")
@login_required
@admin_required
def delete(id):
    usuario = User.query.get_or_404(id)
    if usuario.username == "admin":
        flash("no se puede eliminar al administrador principal", "danger")
    else:
        db.session.delete(usuario)
        db.session.commit()
        flash("usuario eliminado correctamente", "info")
    return redirect(url_for("users.index"))