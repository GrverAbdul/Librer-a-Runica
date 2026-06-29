# app/orders/routes.py
# gestion de pedidos (cliente y admin)

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Order, OrderDetail, Cart, CartDetail, Customer
from app.decorators import admin_required, role_required
from datetime import datetime

orders_bp = Blueprint(
    "orders",
    __name__,
    template_folder="templates"
)

# ------------------------------------------------------------
# crear pedido desde el carrito
# ------------------------------------------------------------
@orders_bp.route("/checkout")
@login_required
def checkout():
    # obtener el carrito del usuario
    carrito = Cart.query.filter_by(usuario_id=current_user.id).first()
    if not carrito or not carrito.items:
        flash("el carrito está vacío", "warning")
        return redirect(url_for("cart.index"))

    # verificar que el usuario tenga un perfil de cliente completo
    cliente = Customer.query.filter_by(usuario_id=current_user.id).first()
    if not cliente or not cliente.nombre or not cliente.apellido:
        flash("completa tu perfil de cliente antes de hacer un pedido", "warning")
        return redirect(url_for("customers.profile"))

    # calcular total
    total = sum(item.subtotal for item in carrito.items)

    # crear el pedido
    nuevo_pedido = Order(
        cliente_id=cliente.id,
        fecha=datetime.utcnow(),
        total=total,
        estado="pendiente"
    )
    db.session.add(nuevo_pedido)
    db.session.flush()  # para obtener id

    # mover los items del carrito a detalles del pedido
    for item in carrito.items:
        detalle = OrderDetail(
            pedido_id=nuevo_pedido.id,
            libro_id=item.libro_id,
            cantidad=item.cantidad,
            precio=item.libro.precio  # precio al momento del pedido
        )
        db.session.add(detalle)
        # opcional: reducir stock
        item.libro.stock -= item.cantidad
        # eliminar item del carrito
        db.session.delete(item)

    db.session.commit()
    flash("pedido realizado con éxito", "success")
    return redirect(url_for("orders.history"))

# ------------------------------------------------------------
# historial de pedidos del usuario
# ------------------------------------------------------------
@orders_bp.route("/history")
@login_required
def history():
    cliente = Customer.query.filter_by(usuario_id=current_user.id).first()
    if not cliente:
        pedidos = []
    else:
        pedidos = Order.query.filter_by(cliente_id=cliente.id).order_by(Order.fecha.desc()).all()
    return render_template("orders/history.html", pedidos=pedidos)

# ------------------------------------------------------------
# detalle de un pedido (usuario o admin)
# ------------------------------------------------------------
@orders_bp.route("/<int:id>")
@login_required
def detail(id):
    pedido = Order.query.get_or_404(id)
    # verificar que sea el dueño o admin
    cliente = Customer.query.filter_by(usuario_id=current_user.id).first()
    if not (current_user.rol.nombre == "administrador" or (cliente and pedido.cliente_id == cliente.id)):
        abort(403)
    return render_template("orders/detail.html", pedido=pedido)

# ------------------------------------------------------------
# (admin) listar todos los pedidos
# ------------------------------------------------------------
@orders_bp.route("/admin")
@login_required
@role_required('administrador', 'empleado')
def admin_index():
    pedidos = Order.query.order_by(Order.fecha.desc()).all()
    return render_template("orders/admin_index.html", pedidos=pedidos)

# ------------------------------------------------------------
# (admin) cambiar estado del pedido
# ------------------------------------------------------------
@orders_bp.route("/update_status/<int:id>", methods=["POST"])
@login_required
@role_required('administrador', 'empleado')
def update_status(id):
    pedido = Order.query.get_or_404(id)
    nuevo_estado = request.form.get("estado")
    if nuevo_estado in ["pendiente", "enviado", "entregado"]:
        pedido.estado = nuevo_estado
        # registrar fechas según el estado
        if nuevo_estado == "enviado" and not pedido.fecha_envio:
            pedido.fecha_envio = datetime.utcnow()
        elif nuevo_estado == "entregado" and not pedido.fecha_entrega:
            pedido.fecha_entrega = datetime.utcnow()
        db.session.commit()
        flash("estado actualizado", "success")
    else:
        flash("estado no válido", "danger")
    return redirect(url_for("orders.admin_index"))