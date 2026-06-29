# app/dashboard/routes.py
# panel de administracion con metricas y grafico dinamico

from flask import Blueprint, render_template
from flask_login import login_required
from app.decorators import role_required
from app.extensions import db
from app.models import User, Book, Order, Customer

dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    template_folder="templates"
)

@dashboard_bp.route("/")
@login_required
@role_required('administrador', 'empleado')
def index():
    # --- Métricas generales ---
    total_usuarios = User.query.count()
    total_libros = Book.query.count()
    total_pedidos = Order.query.count()
    total_ventas = db.session.query(db.func.sum(Order.total)).scalar() or 0
    stock_bajo = Book.query.filter(Book.stock < 5).count()

    # --- Datos para el gráfico de pedidos por estado ---
    # Contamos cuántos pedidos hay en cada estado
    pendientes = Order.query.filter_by(estado='pendiente').count()
    enviados = Order.query.filter_by(estado='enviado').count()
    entregados = Order.query.filter_by(estado='entregado').count()

    return render_template("dashboard/index.html",
                           total_usuarios=total_usuarios,
                           total_libros=total_libros,
                           total_pedidos=total_pedidos,
                           total_ventas=total_ventas,
                           stock_bajo=stock_bajo,
                           pendientes=pendientes,
                           enviados=enviados,
                           entregados=entregados)