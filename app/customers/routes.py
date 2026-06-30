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
        flash("No tienes un perfil de cliente. Contacta al administrador.", "warning")
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

# ------------------------------------------------------------
# establecer ubicacion en el mapa
# ------------------------------------------------------------
@customers_bp.route("/set-location", methods=["GET", "POST"])
@login_required
def set_location():
    cliente = Customer.query.filter_by(usuario_id=current_user.id).first()
    if not cliente:
        flash("No tienes un perfil de cliente.", "danger")
        return redirect(url_for("main.index"))

    if request.method == "POST":
        lat = request.form.get("latitud", type=float)
        lng = request.form.get("longitud", type=float)
        direccion = request.form.get("direccion", "")
        if lat is not None and lng is not None:
            cliente.latitud = lat
            cliente.longitud = lng
            cliente.direccion = direccion # guardar dirección
            db.session.commit()
            flash("¡Ubicación guardada correctamente!", "success")
            return redirect(url_for("customers.profile"))
        else:
            flash("No se recibieron coordenadas válidas.", "danger")

    return render_template("customers/set_location.html", cliente=cliente)