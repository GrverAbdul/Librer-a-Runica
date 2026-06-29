# app/publishers/routes.py
# rutas del modulo editoriales: lista publica, gestion solo admin

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models import Publisher
from app.decorators import admin_required

publishers_bp = Blueprint(
    "publishers",
    __name__,
    template_folder="templates"
)

# ------------------------------------------------------------
# listar editoriales (acceso publico)
# ------------------------------------------------------------
@publishers_bp.route("/")
def index():
    editoriales = Publisher.query.order_by(Publisher.nombre).all()
    return render_template("publishers/index.html", editoriales=editoriales)

# ------------------------------------------------------------
# crear editorial (solo admin)
# ------------------------------------------------------------
@publishers_bp.route("/create", methods=["GET", "POST"])
@login_required
@admin_required
def create():
    if request.method == "POST":
        nombre = request.form["nombre"]
        pais = request.form.get("pais", "")
        telefono = request.form.get("telefono", "")

        existente = Publisher.query.filter_by(nombre=nombre).first()
        if existente:
            flash("ya existe una editorial con ese nombre", "danger")
            return redirect(url_for("publishers.create"))

        nueva_editorial = Publisher(
            nombre=nombre,
            pais=pais,
            telefono=telefono
        )
        db.session.add(nueva_editorial)
        db.session.commit()

        flash("editorial creada correctamente", "success")
        return redirect(url_for("publishers.index"))

    return render_template("publishers/create.html")

# ------------------------------------------------------------
# editar editorial (solo admin)
# ------------------------------------------------------------
@publishers_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit(id):
    editorial = Publisher.query.get_or_404(id)

    if request.method == "POST":
        editorial.nombre = request.form["nombre"]
        editorial.pais = request.form.get("pais", "")
        editorial.telefono = request.form.get("telefono", "")

        duplicado = Publisher.query.filter(
            Publisher.nombre == editorial.nombre,
            Publisher.id != editorial.id
        ).first()
        if duplicado:
            flash("ya existe otra editorial con ese nombre", "danger")
            return redirect(url_for("publishers.edit", id=id))

        db.session.commit()
        flash("editorial actualizada correctamente", "success")
        return redirect(url_for("publishers.index"))

    return render_template("publishers/edit.html", editorial=editorial)

# ------------------------------------------------------------
# eliminar editorial (solo admin)
# ------------------------------------------------------------
@publishers_bp.route("/delete/<int:id>")
@login_required
@admin_required
def delete(id):
    editorial = Publisher.query.get_or_404(id)
    db.session.delete(editorial)
    db.session.commit()
    flash("editorial eliminada correctamente", "info")
    return redirect(url_for("publishers.index"))