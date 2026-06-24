# app/main/routes.py
# rutas principales de la aplicacion

from flask import Blueprint, render_template

# creacion del blueprint
main_bp = Blueprint(
    "main",
    __name__,
    template_folder="templates"   # carpeta dentro de app/main
)

@main_bp.route("/")
def index():
    return render_template("main/index.html")

@main_bp.route("/dashboard")
def dashboard():
    # ruta de ejemplo para el panel principal
    return render_template("main/dashboard.html")