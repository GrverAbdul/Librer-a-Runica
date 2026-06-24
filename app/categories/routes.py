# app/categories/routes.py
# rutas del modulo categorias: listar, crear, editar y eliminar

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models import Category

# creacion del blueprint
categories_bp = Blueprint(
    "categories",
    __name__,
    template_folder="templates"   # las plantillas estan en app/categories/templates
)

# ------------------------------------------------------------
# listar todas las categorias
# ------------------------------------------------------------
@categories_bp.route("/")
@login_required                     # solo usuarios autenticados
def index():
    # obtener todas las categorias ordenadas por nombre
    categorias = Category.query.order_by(Category.nombre).all()
    return render_template("categories/index.html", categorias=categorias)

# ------------------------------------------------------------
# crear una nueva categoria (formulario y guardado)
# ------------------------------------------------------------
@categories_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form.get("descripcion", "")

        # verificar si la categoria ya existe (nombre unico)
        existente = Category.query.filter_by(nombre=nombre).first()
        if existente:
            flash("ya existe una categoria con ese nombre", "danger")
            return redirect(url_for("categories.create"))

        # crear el nuevo objeto categoria
        nueva_categoria = Category(
            nombre=nombre,
            descripcion=descripcion
        )
        db.session.add(nueva_categoria)
        db.session.commit()

        flash("categoria creada correctamente", "success")
        return redirect(url_for("categories.index"))

    # si es GET, mostrar el formulario vacio
    return render_template("categories/create.html")

# ------------------------------------------------------------
# editar una categoria existente
# ------------------------------------------------------------
@categories_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    categoria = Category.query.get_or_404(id)

    if request.method == "POST":
        categoria.nombre = request.form["nombre"]
        categoria.descripcion = request.form.get("descripcion", "")

        # verificar que no se duplique el nombre (excluyendo la actual)
        duplicado = Category.query.filter(
            Category.nombre == categoria.nombre,
            Category.id != categoria.id
        ).first()
        if duplicado:
            flash("ya existe otra categoria con ese nombre", "danger")
            return redirect(url_for("categories.edit", id=id))

        db.session.commit()
        flash("categoria actualizada correctamente", "success")
        return redirect(url_for("categories.index"))

    # GET: mostrar formulario con los datos actuales
    return render_template("categories/edit.html", categoria=categoria)

# ------------------------------------------------------------
# eliminar una categoria
# ------------------------------------------------------------
@categories_bp.route("/delete/<int:id>")
@login_required
def delete(id):
    categoria = Category.query.get_or_404(id)
    db.session.delete(categoria)
    db.session.commit()
    flash("categoria eliminada correctamente", "info")
    return redirect(url_for("categories.index"))