# app/mapas/routes.py
# rutas del modulo de mapas y georreferenciacion

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from app.decorators import role_required
from app.models import Customer, Sucursal, ZonaCobertura, Order
import requests
from app.extensions import db
mapas_bp = Blueprint(
    "mapas",
    __name__,
    template_folder="templates"
)

# ------------------------------------------------------------
# pagina principal del mapa
# ------------------------------------------------------------
@mapas_bp.route("/")
def index():
    sucursales = Sucursal.query.all()
    zonas = ZonaCobertura.query.all()
    return render_template("mapas/index.html", sucursales=sucursales, zonas=zonas)

# ------------------------------------------------------------
# api que devuelve las sucursales en formato geojson
# ------------------------------------------------------------
@mapas_bp.route("/api/sucursales")
def api_sucursales():
    sucursales = Sucursal.query.all()
    features = []
    for s in sucursales:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [s.longitud, s.latitud]
            },
            "properties": {
                "nombre": s.nombre,
                "direccion": s.direccion or "",
                "telefono": s.telefono or ""
            }
        })
    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })

# ------------------------------------------------------------
# api que devuelve las zonas de cobertura en formato geojson
# ------------------------------------------------------------
@mapas_bp.route("/api/zonas")
def api_zonas():
    zonas = ZonaCobertura.query.all()
    features = []
    for z in zonas:
        # se asume que el campo geojson contiene directamente un objeto geojson
        import json
        geom = json.loads(z.geojson)
        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "nombre": z.nombre,
                "descripcion": z.descripcion or ""
            }
        })
    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })

# ------------------------------------------------------------
# api que calcula la mejor ruta con osrm
# ------------------------------------------------------------
@mapas_bp.route("/api/ruta")
def api_ruta():
    # obtiene coordenadas de origen y destino desde los parámetros de la url
    # formato: /api/ruta?lat1=-16.500&lon1=-68.150&lat2=-16.510&lon2=-68.120
    lat1 = request.args.get("lat1", -16.500, type=float)
    lon1 = request.args.get("lon1", -68.150, type=float)
    lat2 = request.args.get("lat2", -16.510, type=float)
    lon2 = request.args.get("lon2", -68.120, type=float)

    # construir la url de osrm (servicio público)
    url = f"https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
    params = {
        "overview": "full",          # devuelve geometría completa
        "geometries": "geojson",     # formato geojson
        "steps": "false"             # no necesitamos instrucciones paso a paso
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "routes" not in data or len(data["routes"]) == 0:
            return jsonify({"error": "No se pudo calcular la ruta"}), 400

        ruta = data["routes"][0]
        distancia_metros = ruta["distance"]   # en metros
        duracion_segundos = ruta["duration"]  # en segundos
        geometria = ruta["geometry"]["coordinates"]  # array de [lon, lat]

        # convertir a formato que espera leaflet: [lat, lon]
        ruta_coords = [[coord[1], coord[0]] for coord in geometria]

        return jsonify({
            "ruta": ruta_coords,
            "distancia_km": round(distancia_metros / 1000, 2),
            "tiempo_min": round(duracion_segundos / 60, 1)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# ------------------------------------------------------------
# api que devuelve las coordenadas de todos los clientes para el mapa de calor
# ------------------------------------------------------------
@mapas_bp.route("/api/clientes")
def api_clientes():
    clientes = Customer.query.filter(
        Customer.latitud.isnot(None),
        Customer.longitud.isnot(None)
    ).all()
    # Formato: array de [lat, lng]
    puntos = [[c.latitud, c.longitud] for c in clientes]
    return jsonify(puntos)

@mapas_bp.route("/calor")
@login_required
@role_required('administrador', 'empleado')
def calor():
    return render_template("mapas/calor.html")

# ------------------------------------------------------------
# api que devuelve las coordenadas de entregas completadas
# ------------------------------------------------------------
@mapas_bp.route("/api/entregas")
def api_entregas():
    from app.models import Order, Customer
    # Obtener todos los pedidos entregados cuyos clientes tengan coordenadas
    entregas = db.session.query(Customer.latitud, Customer.longitud).join(
        Order, Order.cliente_id == Customer.id
    ).filter(
        Order.estado == "entregado",
        Customer.latitud.isnot(None),
        Customer.longitud.isnot(None)
    ).all()
    # Formato: array de [lat, lng]
    puntos = [[lat, lng] for lat, lng in entregas]
    return jsonify(puntos)