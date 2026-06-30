# app/cart/routes.py
# rutas del carrito de compras (requiere inicio de sesion)

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Cart, CartDetail, Book

cart_bp = Blueprint(
    "cart",
    __name__,
    template_folder="templates"
)

# ------------------------------------------------------------
# ver carrito
# ------------------------------------------------------------
@cart_bp.route("/")
@login_required
def index():
    # obtener o crear el carrito del usuario actual
    carrito = Cart.query.filter_by(usuario_id=current_user.id).first()
    if not carrito:
        carrito = Cart(usuario_id=current_user.id)
        db.session.add(carrito)
        db.session.commit()

    # calcular el total sumando los subtotales de cada item
    total = sum(item.subtotal for item in carrito.items)

    return render_template("cart/cart.html", carrito=carrito, total=total)
# ------------------------------------------------------------
# agregar libro al carrito
# ------------------------------------------------------------
@cart_bp.route("/add/<int:book_id>")
@login_required
def add(book_id):
    libro = Book.query.get_or_404(book_id)
    # obtener o crear carrito
    carrito = Cart.query.filter_by(usuario_id=current_user.id).first()
    if not carrito:
        carrito = Cart(usuario_id=current_user.id)
        db.session.add(carrito)
        db.session.commit()

    # verificar si el libro ya está en el carrito
    item = CartDetail.query.filter_by(carrito_id=carrito.id, libro_id=libro.id).first()
    if item:
        item.cantidad += 1
        item.subtotal = item.cantidad * libro.precio
    else:
        item = CartDetail(
            carrito_id=carrito.id,
            libro_id=libro.id,
            cantidad=1,
            subtotal=libro.precio
        )
        db.session.add(item)
    db.session.commit()
    flash(f"'{libro.titulo}' agregado al carrito", "success")
    return redirect(request.referrer or url_for("books.index"))

# ------------------------------------------------------------
# actualizar cantidad de un item
# ------------------------------------------------------------
@cart_bp.route("/update/<int:item_id>", methods=["POST"])
@login_required
def update(item_id):
    item = CartDetail.query.get_or_404(item_id)
    nueva_cantidad = request.form.get("cantidad", type=int)
    if nueva_cantidad and nueva_cantidad > 0:
        item.cantidad = nueva_cantidad
        item.subtotal = item.cantidad * item.libro.precio
        db.session.commit()
        flash("carrito actualizado", "info")
    else:
        flash("cantidad no válida", "warning")
    return redirect(url_for("cart.index"))

# ------------------------------------------------------------
# eliminar item del carrito
# ------------------------------------------------------------
@cart_bp.route("/remove/<int:item_id>")
@login_required
def remove(item_id):
    item = CartDetail.query.get_or_404(item_id)
    # verificar que pertenece al carrito del usuario actual
    if item.carrito.usuario_id != current_user.id:
        flash("acción no permitida", "danger")
        return redirect(url_for("cart.index"))
    db.session.delete(item)
    db.session.commit()
    flash("producto eliminado del carrito", "info")
    return redirect(url_for("cart.index"))