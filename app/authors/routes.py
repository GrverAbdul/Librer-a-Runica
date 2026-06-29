# app/authors/routes.py
# rutas del modulo autores: lista publica, gestion solo admin

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models import Author
from app.decorators import admin_required

authors_bp = Blueprint(
    "authors",
    __name__,
    template_folder="templates"   # carpeta app/authors/templates
)

# ------------------------------------------------------------
# listar autores (acceso publico)
# ------------------------------------------------------------
@authors_bp.route("/")
def index():
    # obtener todos los autores ordenados por nombre
    autores = Author.query.order_by(Author.nombre).all()
    return render_template("authors/index.html", autores=autores)

# ------------------------------------------------------------
# crear autor (solo admin)
# ------------------------------------------------------------
@authors_bp.route("/create", methods=["GET", "POST"])
@login_required
@admin_required
def create():
    if request.method == "POST":
        nombre = request.form["nombre"]
        nacionalidad = request.form.get("nacionalidad", "")
        biografia = request.form.get("biografia", "")

        # validar que no exista un autor con el mismo nombre
        existente = Author.query.filter_by(nombre=nombre).first()
        if existente:
            flash("ya existe un autor con ese nombre", "danger")
            return redirect(url_for("authors.create"))

        nuevo_autor = Author(
            nombre=nombre,
            nacionalidad=nacionalidad,
            biografia=biografia
        )
        db.session.add(nuevo_autor)
        db.session.commit()

        flash("autor creado correctamente", "success")
        return redirect(url_for("authors.index"))

    # metodo GET: mostrar formulario vacio
    return render_template("authors/create.html")

# ------------------------------------------------------------
# editar autor (solo admin)
# ------------------------------------------------------------
@authors_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit(id):
    autor = Author.query.get_or_404(id)

    if request.method == "POST":
        autor.nombre = request.form["nombre"]
        autor.nacionalidad = request.form.get("nacionalidad", "")
        autor.biografia = request.form.get("biografia", "")

        # verificar que no se duplique el nombre (excluyendo el autor actual)
        duplicado = Author.query.filter(
            Author.nombre == autor.nombre,
            Author.id != autor.id
        ).first()
        if duplicado:
            flash("ya existe otro autor con ese nombre", "danger")
            return redirect(url_for("authors.edit", id=id))

        db.session.commit()
        flash("autor actualizado correctamente", "success")
        return redirect(url_for("authors.index"))

    # GET: mostrar formulario con datos actuales
    return render_template("authors/edit.html", autor=autor)

# ------------------------------------------------------------
# eliminar autor (solo admin)
# ------------------------------------------------------------
@authors_bp.route("/delete/<int:id>")
@login_required
@admin_required
def delete(id):
    autor = Author.query.get_or_404(id)
    db.session.delete(autor)
    db.session.commit()
    flash("autor eliminado correctamente", "info")
    return redirect(url_for("authors.index"))