# app/roles/routes.py
# rutas de gestion de roles (solo administrador)

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models import Role
from app.decorators import admin_required

roles_bp = Blueprint(
    "roles",
    __name__,
    template_folder="templates"
)

# ------------------------------------------------------------
# listar roles
# ------------------------------------------------------------
@roles_bp.route("/")
@login_required
@admin_required
def index():
    roles = Role.query.all()
    return render_template("roles/index.html", roles=roles)

# ------------------------------------------------------------
# crear nuevo rol
# ------------------------------------------------------------
@roles_bp.route("/create", methods=["GET", "POST"])
@login_required
@admin_required
def create():
    if request.method == "POST":
        nombre = request.form["nombre"]
        if Role.query.filter_by(nombre=nombre).first():
            flash("Ese rol ya existe", "danger")
            return redirect(url_for("roles.create"))
        db.session.add(Role(nombre=nombre))
        db.session.commit()
        flash("Rol creado correctamente", "success")
        return redirect(url_for("roles.index"))
    return render_template("roles/create.html")

# ------------------------------------------------------------
# eliminar rol (solo si no tiene usuarios asociados)
# ------------------------------------------------------------
@roles_bp.route("/delete/<int:id>")
@login_required
@admin_required
def delete(id):
    rol = Role.query.get_or_404(id)
    if rol.usuarios:
        flash("no se puede eliminar un rol con usuarios asignados", "danger")
    else:
        db.session.delete(rol)
        db.session.commit()
        flash("rol eliminado", "info")
    return redirect(url_for("roles.index"))