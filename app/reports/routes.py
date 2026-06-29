# app/reports/routes.py
# rutas de reportes basicos para el administrador

from flask import Blueprint, render_template, request, flash, url_for, redirect
from flask_login import login_required
from app.decorators import admin_required, role_required
from app.extensions import db
from app.models import Book, Order

reports_bp = Blueprint(
    "reports",
    __name__,
    template_folder="templates"
)

# ------------------------------------------------------------
# reporte de ventas
# ------------------------------------------------------------
@reports_bp.route("/sales")
@login_required
@role_required('administrador', 'empleado')
def sales():
    # calcular total de ventas sumando la columna 'total' de todos los pedidos
    total_ventas = db.session.query(db.func.sum(Order.total)).scalar() or 0
    # contar todos los pedidos
    total_pedidos = Order.query.count()
    # obtener los ultimos 10 pedidos ordenados por fecha descendente
    ultimos_pedidos = Order.query.order_by(Order.fecha.desc()).limit(10).all()

    return render_template("reports/sales.html",
                           total_ventas=total_ventas,
                           total_pedidos=total_pedidos,
                           ultimos_pedidos=ultimos_pedidos)

# ------------------------------------------------------------
# reporte de inventario
# ------------------------------------------------------------
@reports_bp.route("/inventory")
@login_required
@role_required('administrador', 'empleado')
def inventory():
    # libros con stock menor a 5 (bajo)
    stock_bajo = Book.query.filter(Book.stock < 5).all()
    # tambien podemos mostrar todos los libros con su stock
    todos_libros = Book.query.order_by(Book.stock).all()

    return render_template("reports/inventory.html",
                           stock_bajo=stock_bajo,
                           todos_libros=todos_libros)

# ------------------------------------------------------------
# actualizar stock desde el reporte de inventario
# ------------------------------------------------------------
@reports_bp.route("/update-stock/<int:book_id>", methods=["POST"])
@login_required
@role_required('administrador', 'empleado')
def update_stock(book_id):
    libro = Book.query.get_or_404(book_id)
    nuevo_stock = request.form.get("stock", type=int)
    if nuevo_stock is not None and nuevo_stock >= 0:
        libro.stock = nuevo_stock
        db.session.commit()
        flash(f"stock de '{libro.titulo}' actualizado a {nuevo_stock}", "success")
    else:
        flash("stock no válido", "danger")
    return redirect(url_for("reports.inventory"))