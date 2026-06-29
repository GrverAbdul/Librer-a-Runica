# app/books/routes.py
# rutas del modulo libros: lista publica, gestion solo admin
# incluye subida de imagenes con arrastrar y soltar (drag & drop)

import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
# para limpiar nombres de archivo
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Book, Category, Author, Publisher
from app.decorators import admin_required, role_required

books_bp = Blueprint(
    "books",
    __name__,
    template_folder="templates"
)

# ------------------------------------------------------------
# listar libros (acceso publico)
# ------------------------------------------------------------
@books_bp.route("/")
def index():
    # obtener todos los libros ordenados por titulo, incluyendo relaciones
    libros = Book.query.order_by(Book.titulo).all()
    return render_template("books/index.html", libros=libros)

# ------------------------------------------------------------
# detalle de un libro (publico)
# ------------------------------------------------------------
@books_bp.route("/<int:id>")
def detail(id):
    libro = Book.query.get_or_404(id)
    return render_template("books/detail.html", libro=libro)

# ------------------------------------------------------------
# crear libro (admin y empleados)
# ------------------------------------------------------------
@books_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required('administrador', 'empleado')  # permite a ambos roles
def create():
    # cargar las listas de opciones para los select (autores, categorias, editoriales)
    categorias = Category.query.order_by(Category.nombre).all()
    autores = Author.query.order_by(Author.nombre).all()
    editoriales = Publisher.query.order_by(Publisher.nombre).all()

    if request.method == "POST":
        # recibir datos del formulario
        titulo = request.form["titulo"]
        isbn = request.form["isbn"]
        precio = request.form.get("precio", type=float)
        stock = request.form.get("stock", type=int, default=0)
        descripcion = request.form.get("descripcion", "")
        categoria_id = request.form.get("categoria_id", type=int)
        autor_id = request.form.get("autor_id", type=int)
        editorial_id = request.form.get("editorial_id", type=int)

        # validaciones basicas
        if not all([titulo, isbn, precio is not None, categoria_id, autor_id, editorial_id]):
            flash("completa todos los campos obligatorios", "danger")
            return redirect(url_for("books.create"))

        # verificar isbn unico
        if Book.query.filter_by(isbn=isbn).first():
            flash("ya existe un libro con ese isbn", "danger")
            return redirect(url_for("books.create"))

        # --- manejo de la imagen (drag & drop en el input file) ---
        imagen = None
        # 'imagen' es el name del input file en el formulario
        if 'imagen' in request.files:
            archivo = request.files['imagen']
            # si el usuario selecciono un archivo (puede arrastrarlo o hacer clic)
            if archivo.filename != '':
                # obtener extension segura (ej: jpg, png)
                extension = archivo.filename.rsplit('.', 1)[-1].lower()
                # generar un nombre unico usando uuid para evitar colisiones
                nombre_unico = f"{uuid.uuid4().hex}.{extension}"
                # ruta donde se guardara la imagen
                ruta_guardado = os.path.join('static', 'uploads', 'covers', nombre_unico)
                # guardar el archivo en el servidor
                archivo.save(ruta_guardado)
                # almacenar el nombre del archivo en la base de datos
                imagen = nombre_unico
        # -----------------------------------------------

        # crear el nuevo libro con todos los datos (incluyendo la imagen si se subio)
        nuevo_libro = Book(
            titulo=titulo,
            isbn=isbn,
            precio=precio,
            stock=stock,
            descripcion=descripcion,
            imagen=imagen,          # None si no se subio imagen
            categoria_id=categoria_id,
            autor_id=autor_id,
            editorial_id=editorial_id
        )
        db.session.add(nuevo_libro)
        db.session.commit()

        flash("libro creado correctamente", "success")
        return redirect(url_for("books.index"))

    # GET: mostrar formulario vacio con las listas de opciones
    return render_template("books/create.html",
                           categorias=categorias,
                           autores=autores,
                           editoriales=editoriales)

# ------------------------------------------------------------
# editar libro
# ------------------------------------------------------------
@books_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required('administrador', 'empleado')
def edit(id):
    libro = Book.query.get_or_404(id)
    categorias = Category.query.order_by(Category.nombre).all()
    autores = Author.query.order_by(Author.nombre).all()
    editoriales = Publisher.query.order_by(Publisher.nombre).all()

    if request.method == "POST":
        # actualizar campos de texto
        libro.titulo = request.form["titulo"]
        libro.isbn = request.form["isbn"]
        libro.precio = request.form.get("precio", type=float)
        libro.stock = request.form.get("stock", type=int, default=0)
        libro.descripcion = request.form.get("descripcion", "")
        libro.categoria_id = request.form.get("categoria_id", type=int)
        libro.autor_id = request.form.get("autor_id", type=int)
        libro.editorial_id = request.form.get("editorial_id", type=int)

        # comprobar duplicado de isbn (excluyendo el libro actual)
        duplicado = Book.query.filter(
            Book.isbn == libro.isbn,
            Book.id != libro.id
        ).first()
        if duplicado:
            flash("ya existe otro libro con ese isbn", "danger")
            return redirect(url_for("books.edit", id=id))

        # --- manejo de la imagen en edicion ---
        if 'imagen' in request.files:
            archivo = request.files['imagen']
            if archivo.filename != '':
                # si se sube una nueva imagen, eliminar la anterior si existia
                if libro.imagen:
                    ruta_anterior = os.path.join('static', 'uploads', 'covers', libro.imagen)
                    if os.path.exists(ruta_anterior):
                        os.remove(ruta_anterior)
                # guardar la nueva imagen con nombre unico
                extension = archivo.filename.rsplit('.', 1)[-1].lower()
                nombre_unico = f"{uuid.uuid4().hex}.{extension}"
                ruta_guardado = os.path.join('static', 'uploads', 'covers', nombre_unico)
                archivo.save(ruta_guardado)
                libro.imagen = nombre_unico
            # si no se seleccionó archivo, se conserva la imagen actual (no se modifica)
        # -----------------------------------------------

        db.session.commit()
        flash("libro actualizado correctamente", "success")
        return redirect(url_for("books.index"))

    # GET: mostrar formulario con los datos actuales
    return render_template("books/edit.html",
                           libro=libro,
                           categorias=categorias,
                           autores=autores,
                           editoriales=editoriales)


# ------------------------------------------------------------
# libros filtrados por categoria
# ------------------------------------------------------------
@books_bp.route("/category/<int:category_id>")
def by_category(category_id):
    categoria = Category.query.get_or_404(category_id)
    libros = Book.query.filter_by(categoria_id=category_id).order_by(Book.titulo).all()
    return render_template("books/index.html", libros=libros, titulo=f"libros de {categoria.nombre}")

# ------------------------------------------------------------
# libros filtrados por autor
# ------------------------------------------------------------
@books_bp.route("/author/<int:author_id>")
def by_author(author_id):
    autor = Author.query.get_or_404(author_id)
    libros = Book.query.filter_by(autor_id=author_id).order_by(Book.titulo).all()
    return render_template("books/index.html", libros=libros, titulo=f"libros de {autor.nombre}")

# ------------------------------------------------------------
# libros filtrados por editorial
# ------------------------------------------------------------
@books_bp.route("/publisher/<int:publisher_id>")
def by_publisher(publisher_id):
    editorial = Publisher.query.get_or_404(publisher_id)
    libros = Book.query.filter_by(editorial_id=publisher_id).order_by(Book.titulo).all()
    return render_template("books/index.html", libros=libros, titulo=f"libros de {editorial.nombre}")

# ------------------------------------------------------------
# eliminar libro (solo admin)
# ------------------------------------------------------------
@books_bp.route("/delete/<int:id>")
@login_required
@admin_required
def delete(id):
    libro = Book.query.get_or_404(id)
    # eliminar la imagen asociada del disco si existe
    if libro.imagen:
        ruta_imagen = os.path.join('static', 'uploads', 'covers', libro.imagen)
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)
    db.session.delete(libro)
    db.session.commit()
    flash("libro eliminado correctamente", "info")
    return redirect(url_for("books.index"))