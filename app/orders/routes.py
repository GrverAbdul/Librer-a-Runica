# app/orders/routes.py
# gestion de pedidos (cliente, admin, empleado, seguimiento)

from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
import requests
from app.extensions import db
from app.models import Order, OrderDetail, Cart, CartDetail, Customer
from app.decorators import admin_required, role_required
from datetime import datetime
from zoneinfo import ZoneInfo

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
        flash("Completa tu perfil de cliente antes de hacer un pedido", "warning")
        return redirect(url_for("customers.profile"))
    # verificar que el cliente tenga ubicación
    if not cliente.latitud or not cliente.longitud:
        flash("Por favor establece tu ubicación de entrega en el mapa antes de hacer un pedido", "warning")
        return redirect(url_for("customers.set_location"))
    # verificar que el cliente esté dentro de la cobertura
    from app.utils import cliente_esta_en_cobertura
    if not cliente_esta_en_cobertura(cliente):
        flash("Lo sentimos, tu ubicación está fuera de nuestra área de cobertura. por favor elige otra dirección.", "danger")
        return redirect(url_for("customers.set_location"))
    # calcular total
    total = sum(item.subtotal for item in carrito.items)

    from app.utils import obtener_sucursal_mas_cercana
    sucursal = obtener_sucursal_mas_cercana(cliente.latitud, cliente.longitud)

    nuevo_pedido = Order(
        cliente_id=cliente.id,
        fecha=datetime.now(ZoneInfo("America/La_Paz")).replace(tzinfo=None),
        total=total,
        estado="pendiente",
        sucursal_id=sucursal.id if sucursal else None
    )
    db.session.add(nuevo_pedido)
    db.session.flush()

    # mover los items del carrito a detalles del pedido
    for item in carrito.items:
        detalle = OrderDetail(
            pedido_id=nuevo_pedido.id,
            libro_id=item.libro_id,
            cantidad=item.cantidad,
            precio=item.libro.precio
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
# historial de pedidos del usuario actual
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
# historial de un cliente específico (admin/empleado)
# ------------------------------------------------------------
@orders_bp.route("/history/<int:customer_id>")
@login_required
@role_required('administrador', 'empleado')
def customer_history(customer_id):
    cliente = Customer.query.get_or_404(customer_id)
    pedidos = Order.query.filter_by(cliente_id=cliente.id).order_by(Order.fecha.desc()).all()
    return render_template("orders/history.html", pedidos=pedidos, cliente=cliente)

# ------------------------------------------------------------
# detalle de un pedido
# ------------------------------------------------------------
@orders_bp.route("/<int:id>")
@login_required
def detail(id):
    pedido = Order.query.get_or_404(id)
    # verificar que sea el dueño o admin
    cliente = Customer.query.filter_by(usuario_id=current_user.id).first()
    if not (current_user.rol.nombre in ["administrador", "empleado"] or (cliente and pedido.cliente_id == cliente.id)):
        abort(403)
    return render_template("orders/detail.html", pedido=pedido)

# ------------------------------------------------------------
# seguimiento del pedido (mapa con repartidor)
# ------------------------------------------------------------
@orders_bp.route("/tracking/<int:id>")
@login_required
def tracking(id):
    pedido = Order.query.get_or_404(id)
    cliente = Customer.query.filter_by(usuario_id=current_user.id).first()
    if not (current_user.rol.nombre in ["administrador", "empleado"] or (cliente and pedido.cliente_id == cliente.id)):
        abort(403)

    if not pedido.sucursal or not pedido.cliente.latitud or not pedido.cliente.longitud:
        flash("Este pedido no tiene datos geográficos para mostrar la ruta.", "warning")
        return redirect(url_for("orders.detail", id=pedido.id))

    # Obtener ruta de OSRM para calcular distancia, tiempo y total de puntos
    url = f"https://router.project-osrm.org/route/v1/driving/{pedido.sucursal.longitud},{pedido.sucursal.latitud};{pedido.cliente.longitud},{pedido.cliente.latitud}?overview=full&geometries=geojson"
    distancia_km = 0
    tiempo_min = 0
    total_puntos = 0
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data["routes"]:
                ruta = data["routes"][0]
                distancia_km = round(ruta["distance"] / 1000, 2)
                tiempo_min = round(ruta["duration"] / 60, 1)
                total_puntos = len(ruta["geometry"]["coordinates"])
    except Exception as e:
        print(f"Error al obtener ruta: {e}")

    return render_template("orders/tracking.html",
                           pedido=pedido,
                           total_puntos=total_puntos,
                           distancia_km=distancia_km,
                           tiempo_min=tiempo_min)
# ------------------------------------------------------------
# API: obtener progreso actual de la simulación
# ------------------------------------------------------------
@orders_bp.route("/api/progress/<int:id>")
@login_required
def get_progress(id):
    pedido = Order.query.get_or_404(id)
    # cualquiera puede ver el progreso si tiene acceso al pedido
    return jsonify({
        "progreso": pedido.progreso_simulacion,
        "activa": pedido.simulacion_activa
    })

# ------------------------------------------------------------
# API: actualizar progreso de la simulación
# ------------------------------------------------------------
@orders_bp.route("/api/progress/<int:id>", methods=["POST"])
@login_required
def update_progress(id):
    pedido = Order.query.get_or_404(id)
    data = request.get_json()
    if data and "progreso" in data:
        pedido.progreso_simulacion = data["progreso"]
        db.session.commit()
        return jsonify({"status": "ok"})
    return jsonify({"error": "datos inválidos"}), 400

# ------------------------------------------------------------
# API: marcar pedido como entregado desde la simulación
# ------------------------------------------------------------
@orders_bp.route("/api/complete_simulation/<int:id>", methods=["POST"])
@login_required
def complete_simulation(id):
    pedido = Order.query.get_or_404(id)
    if pedido.estado == "enviado":
        pedido.estado = "entregado"
        pedido.fecha_entrega = datetime.now(ZoneInfo("America/La_Paz")).replace(tzinfo=None)
        pedido.simulacion_activa = False
        db.session.commit()
        return jsonify({"status": "entregado"})
    return jsonify({"error": "el pedido no está en estado enviado"}), 400

# ------------------------------------------------------------
# (admin/empleado) listar todos los pedidos
# ------------------------------------------------------------
@orders_bp.route("/admin")
@login_required
@role_required('administrador', 'empleado')
def admin_index():
    pedidos = Order.query.order_by(Order.fecha.desc()).all()
    return render_template("orders/admin_index.html", pedidos=pedidos)

# ------------------------------------------------------------
# cambiar estado del pedido (manual)
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
            pedido.fecha_envio = datetime.now(ZoneInfo("America/La_Paz")).replace(tzinfo=None)
            pedido.simulacion_activa = True
            pedido.progreso_simulacion = 0
        elif nuevo_estado == "entregado":
            pedido.fecha_entrega = pedido.fecha_entrega or datetime.now(ZoneInfo("America/La_Paz")).replace(tzinfo=None)
            pedido.simulacion_activa = False
        db.session.commit()
        flash("Estado actualizado", "success")
    else:
        flash("Estado no válido", "danger")
    return redirect(url_for("orders.admin_index"))