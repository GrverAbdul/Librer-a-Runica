# app/customers/routes.py
# gestion del perfil de cliente (cada usuario ve el suyo, admin puede listar)

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Customer
from app.decorators import admin_required, role_required

customers_bp = Blueprint(
    "customers",
    __name__,
    template_folder="templates"
)

# ------------------------------------------------------------
# ver / editar el propio perfil
# ------------------------------------------------------------
@customers_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    cliente = Customer.query.filter_by(usuario_id=current_user.id).first()
    if not cliente:
        flash("no tienes un perfil de cliente. contacta al administrador.", "warning")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        cliente.nombre = request.form["nombre"]
        cliente.apellido = request.form["apellido"]
        cliente.telefono = request.form.get("telefono", "")
        cliente.direccion = request.form.get("direccion", "")
        db.session.commit()
        flash("perfil actualizado", "success")
        return redirect(url_for("customers.profile"))

    return render_template("customers/profile.html", cliente=cliente)

# ------------------------------------------------------------
# (admin y empleados) listar todos los clientes
# ------------------------------------------------------------
@customers_bp.route("/")
@login_required
@role_required('administrador', 'empleado')
def index():
    clientes = Customer.query.all()
    return render_template("customers/index.html", clientes=clientes)