# app/main/routes.py
# rutas principales de la aplicacion

from flask import Blueprint, render_template
from app.models import Book
from sqlalchemy.sql.expression import func

# creacion del blueprint
main_bp = Blueprint(
    "main",
    __name__,
    template_folder="templates"   
    # carpeta dentro de app/main
)

@main_bp.route("/")
def index():
        # obtener hasta 6 libros aleatorios para mostrar en la portada
    libros_aleatorios = Book.query.order_by(func.random()).limit(6).all()
    return render_template("main/index.html", libros_aleatorios=libros_aleatorios)

@main_bp.route("/dashboard")
def dashboard():
    # ruta de ejemplo para el panel principal
    return render_template("main/dashboard.html")