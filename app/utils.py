# app/utils.py
# funciones auxiliares para calculos geograficos

from math import radians, cos, sin, asin, sqrt
from app.models import Sucursal
import json
from app.models import ZonaCobertura

def calcular_distancia(lat1, lon1, lat2, lon2):
    """formula de haversine: devuelve la distancia en kilometros entre dos coordenadas"""
    r = 6371  # radio de la tierra en km

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return r * c

def obtener_sucursal_mas_cercana(lat, lon):
    """devuelve el objeto Sucursal mas cercano a las coordenadas dadas"""
    sucursales = Sucursal.query.all()
    if not sucursales:
        return None

    sucursal_cercana = None
    distancia_minima = float('inf')

    for sucursal in sucursales:
        distancia = calcular_distancia(lat, lon, sucursal.latitud, sucursal.longitud)
        if distancia < distancia_minima:
            distancia_minima = distancia
            sucursal_cercana = sucursal

    return sucursal_cercana

def punto_en_poligono(lat, lon, geojson_str):
    """
    Verifica si un punto (lat, lon) está dentro de un polígono GeoJSON.
    Utiliza el algoritmo de ray casting.
    """
    try:
        geom = json.loads(geojson_str)
        coords = geom['coordinates'][0]  # primer anillo del polígono
        n = len(coords)
        inside = False
        x, y = lon, lat
        for i in range(n):
            x1, y1 = coords[i][0], coords[i][1]
            x2, y2 = coords[(i+1) % n][0], coords[(i+1) % n][1]
            # Verificar si el rayo cruza el segmento
            if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
                inside = not inside
        return inside
    except Exception:
        return False

#para verificar si el cliente está dentro de la zona de cobertura
def cliente_esta_en_cobertura(cliente):
    """
    Retorna True si el cliente está dentro de al menos una zona de cobertura.
    """
    zonas = ZonaCobertura.query.all()
    for zona in zonas:
        if punto_en_poligono(cliente.latitud, cliente.longitud, zona.geojson):
            return True
    return False
