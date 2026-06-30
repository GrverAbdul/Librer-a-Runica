# app/app.py
# fábrica de aplicaciones flask, inicializa extensiones y registra blueprints

from datetime import datetime
from flask import Flask, render_template
from flask_migrate import Migrate
from app.config import Config
from app.extensions import db, bcrypt, login_manager
# scheduler para la simulación de entregas en segundo plano
from apscheduler.schedulers.background import BackgroundScheduler
import app.models           # necesario para que alembic detecte los modelos
import requests as http_requests
from zoneinfo import ZoneInfo

migrate = Migrate()

def create_app():
    # crear la instancia de la aplicación
    app = Flask(__name__, static_folder='../static')

    # cargar configuración desde la clase Config (y variables de entorno)
    app.config.from_object(Config)

    # inicializar extensiones con la aplicación
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Inicializar el scheduler en segundo plano
    scheduler = BackgroundScheduler()
    scheduler.start()

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # -------------------------------------------------------------
    # comandos personalizados de flask
    # -------------------------------------------------------------
    import click
    from app.models import Role, User

    @app.cli.command("seed")
    def seed():
        """crea los roles básicos y un usuario administrador."""
        for nombre in ["administrador", "cliente", "empleado"]:
            if not Role.query.filter_by(nombre=nombre).first():
                db.session.add(Role(nombre=nombre))
        db.session.commit()

        # crear usuario admin por defecto si no existe
        if not User.query.filter_by(username="admin").first():
            admin_role = Role.query.filter_by(nombre="administrador").first()
            hashed_pw = bcrypt.generate_password_hash("123").decode("utf-8")
            admin_user = User(
                username="admin",
                email="admin@libreria.com",
                password=hashed_pw,
                rol_id=admin_role.id
            )
            db.session.add(admin_user)
            db.session.commit()
            print("usuario admin creado (admin / 123)")
        print("datos sembrados correctamente.")

    @app.cli.command("seed-books")
    def seed_books():
        """inserta 50 libros de prueba si la tabla está vacía."""
        from app.models import Book, Category, Author, Publisher
        import random

        if Book.query.first():
            print("Ya existen libros en la base de datos. No se insertaron duplicados.")
            return

        libros_data = [
            ("Cien años de soledad", "Gabriel García Márquez", "Editorial Sudamericana", "Ficción",
             "La historia de la familia Buendía en el mítico Macondo, un clásico del realismo mágico."),
            ("El nombre de la rosa", "Umberto Eco", "Bompiani", "Ficción",
             "Un monje investiga una serie de asesinatos en una abadía medieval, combinando misterio y erudición."),
            ("1984", "George Orwell", "Secker & Warburg", "Ficción",
             "Distopía totalitaria donde el Gran Hermano vigila cada aspecto de la vida de Winston Smith."),
            ("La Odisea", "Homero", "Gredos", "Ficción",
             "Las aventuras de Odiseo en su regreso a Ítaca tras la guerra de Troya, llena de mitos y monstruos."),
            ("Don Quijote de la Mancha", "Miguel de Cervantes", "Francisco de Robles", "Ficción",
             "Las desventuras de un hidalgo que enloquece leyendo libros de caballerías y sale a luchar contra molinos."),
            ("Crimen y castigo", "Fiódor Dostoyevski", "El Mensajero", "Ficción",
             "Raskólnikov, un estudiante pobre, asesina a una usurera y es atormentado por la culpa en San Petersburgo."),
            ("Orgullo y prejuicio", "Jane Austen", "T. Egerton", "Ficción",
             "Elizabeth Bennet y el señor Darcy superan malentendidos y prejuicios en la Inglaterra del siglo XIX."),
            ("Matar a un ruiseñor", "Harper Lee", "J.B. Lippincott", "Ficción",
             "La injusticia racial en el sur de Estados Unidos vista a través de los ojos de la pequeña Scout Finch."),
            ("El gran Gatsby", "F. Scott Fitzgerald", "Charles Scribner's Sons", "Ficción",
             "El misterioso Jay Gatsby y su obsesión por Daisy Buchanan en los locos años veinte."),
            ("Ulises", "James Joyce", "Shakespeare and Company", "Ficción",
             "Un día en la vida de Leopold Bloom en Dublín, repleto de monólogo interior y referencias homéricas."),
            ("La Divina Comedia", "Dante Alighieri", "Nueva Editorial", "Ficción",
             "Viaje alegórico por el Infierno, el Purgatorio y el Paraíso guiado por Virgilio y Beatriz."),
            ("Hamlet", "William Shakespeare", "Norton", "Ficción",
             "El príncipe de Dinamarca busca vengar la muerte de su padre en una tragedia de duda y locura."),
            ("En busca del tiempo perdido", "Marcel Proust", "Grasset", "Ficción",
             "Exploración de la memoria, el amor y el tiempo a través de la vida del narrador en la alta sociedad francesa."),
            ("La metamorfosis", "Franz Kafka", "Kurt Wolff", "Ficción",
             "Gregor Samsa despierta convertido en un insecto gigante, enfrentando el rechazo de su familia."),
            ("El retrato de Dorian Gray", "Oscar Wilde", "Lippincott's", "Ficción",
             "Un joven conserva su belleza mientras un retrato envejece por él, revelando los excesos de la vida."),
            ("Drácula", "Bram Stoker", "Archibald Constable", "Ficción",
             "El conde Drácula viaja a Inglaterra y desata el terror; el profesor Van Helsing intenta detenerlo."),
            ("Frankenstein", "Mary Shelley", "Lackington", "Ficción",
             "El científico Victor Frankenstein crea una criatura y sufre las consecuencias de jugar a ser Dios."),
            ("El código Da Vinci", "Dan Brown", "Doubleday", "Ficción",
             "Robert Langdon investiga un asesinato en el Louvre y descubre un secreto milenario escondido en obras de arte."),
            ("Los juegos del hambre", "Suzanne Collins", "Scholastic", "Ficción",
             "Katniss Everdeen lucha por sobrevivir en un reality sangriento televisado en un futuro distópico."),
            ("Harry Potter y la piedra filosofal", "J.K. Rowling", "Bloomsbury", "Ficción",
             "Un niño descubre que es mago y asiste a Hogwarts, donde enfrenta al malvado Voldemort."),
            ("El señor de los anillos", "J.R.R. Tolkien", "George Allen & Unwin", "Ficción",
             "La Comunidad del Anillo emprende un viaje para destruir el Anillo Único y salvar la Tierra Media."),
            ("Crónica de una muerte anunciada", "Gabriel García Márquez", "La Oveja Negra", "Ficción",
             "Reconstrucción de un asesinato que todo el pueblo sabía que iba a ocurrir pero nadie pudo evitar."),
            ("El amor en los tiempos del cólera", "Gabriel García Márquez", "Sudamericana", "Ficción",
             "Florentino Ariza espera más de cincuenta años para volver a estar con Fermina Daza."),
            ("La casa de los espíritus", "Isabel Allende", "Plaza & Janés", "Ficción",
             "Saga familiar que mezcla amor, política y magia en un país sudamericano no especificado."),
            ("Rayuela", "Julio Cortázar", "Sudamericana", "Ficción",
             "Horacio Oliveira y La Maga viven un amor bohemio entre París y Buenos Aires en una novela de múltiples lecturas."),
            ("Ficciones", "Jorge Luis Borges", "Sur", "Ficción",
             "Colección de cuentos que exploran laberintos, bibliotecas infinitas y la naturaleza de la realidad."),
            ("El Aleph", "Jorge Luis Borges", "Losada", "Ficción",
             "Un punto mágico que contiene todos los puntos del universo y otros relatos fantásticos."),
            ("Pedro Páramo", "Juan Rulfo", "Fondo de Cultura Económica", "Ficción",
             "Juan Preciado llega a Comala para buscar a su padre y encuentra un pueblo lleno de fantasmas."),
            ("La ciudad y los perros", "Mario Vargas Llosa", "Seix Barral", "Ficción",
             "La violencia y el machismo en un colegio militar limeño, retrato crudo de la juventud."),
            ("El túnel", "Ernesto Sabato", "Sur", "Ficción",
             "Un pintor obsesionado confiesa el asesinato de su amante en un oscuro monólogo psicológico."),
            ("Sapiens", "Yuval Noah Harari", "Debate", "Historia",
             "Un recorrido por la historia de la humanidad, desde los primeros homínidos hasta la era moderna."),
            ("Breve historia del tiempo", "Stephen Hawking", "Bantam", "Ciencia",
             "Explora los misterios del universo, desde el Big Bang hasta los agujeros negros, para todo público."),
            ("El gen egoísta", "Richard Dawkins", "Oxford University Press", "Ciencia",
             "Propone que los genes son las unidades fundamentales de la evolución, revolucionando la biología."),
            ("Una breve historia de casi todo", "Bill Bryson", "Broadway", "Ciencia",
             "Viaje ameno por la ciencia: geología, física, química y biología explicadas con humor."),
            ("El universo elegante", "Brian Greene", "W.W. Norton", "Ciencia",
             "Introducción a la teoría de supercuerdas y la búsqueda de una teoría unificada de la física."),
            ("Los dragones del Edén", "Carl Sagan", "Random House", "Ciencia",
             "Especulaciones sobre la evolución de la inteligencia humana y el papel del cerebro."),
            ("Cosmos", "Carl Sagan", "Random House", "Ciencia",
             "Un viaje personal a través del espacio y el tiempo, desde la antigüedad hasta la exploración espacial."),
            ("El origen de las especies", "Charles Darwin", "John Murray", "Ciencia",
             "La obra fundacional de la evolución por selección natural que cambió la biología para siempre."),
            ("La tabla periódica", "Primo Levi", "Einaudi", "Ciencia",
             "Relatos autobiográficos de un químico judío en la Italia fascista, utilizando elementos como metáfora."),
            ("Historia del tiempo", "Stephen Hawking", "Crítica", "Ciencia",
             "Otra obra de divulgación de Hawking que explica el cosmos de manera aún más accesible."),
            ("El gen", "Siddhartha Mukherjee", "Scribner", "Ciencia",
             "Una historia íntima y completa del gen, desde Mendel hasta la manipulación genética moderna."),
            ("Armas, gérmenes y acero", "Jared Diamond", "W.W. Norton", "Historia",
             "¿Por qué algunas sociedades dominaron a otras? Un análisis de factores geográficos y tecnológicos."),
            ("La riqueza de las naciones", "Adam Smith", "W. Strahan", "Historia",
             "Clásico del liberalismo económico que defiende el libre mercado y la división del trabajo."),
            ("El arte de la guerra", "Sun Tzu", "Shambhala", "Historia",
             "Antiguo tratado militar chino sobre estrategia y táctica, aplicable hoy a los negocios y la vida."),
            ("Los cañones de agosto", "Barbara W. Tuchman", "Macmillan", "Historia",
             "Crónica de los primeros treinta días de la Primera Guerra Mundial que definieron el conflicto."),
            ("La segunda guerra mundial", "Winston Churchill", "Cassell", "Historia",
             "Memorias y análisis del primer ministro británico sobre la contienda más grande de la historia."),
            ("Churchill", "Andrew Roberts", "Viking", "Historia",
             "Biografía exhaustiva del líder británico, desde su juventud hasta su papel en la guerra."),
            ("Napoleón", "Andrew Roberts", "Viking", "Historia",
             "Vida del emperador francés, sus campañas militares y su legado político."),
            ("Steve Jobs", "Walter Isaacson", "Simon & Schuster", "Tecnología",
             "Biografía autorizada del fundador de Apple, basada en más de cuarenta entrevistas."),
            ("Clean Code", "Robert C. Martin", "Prentice Hall", "Tecnología",
             "Principios y buenas prácticas para escribir código limpio, mantenible y eficiente."),
        ]


        for titulo, autor_nombre, editorial_nombre, categoria_nombre, descripcion in libros_data:
            # Categoría
            cat = Category.query.filter_by(nombre=categoria_nombre).first()
            if not cat:
                cat = Category(nombre=categoria_nombre)
                db.session.add(cat)
                db.session.flush()

            # Autor
            aut = Author.query.filter_by(nombre=autor_nombre).first()
            if not aut:
                aut = Author(nombre=autor_nombre)
                db.session.add(aut)
                db.session.flush()

            # Editorial
            edi = Publisher.query.filter_by(nombre=editorial_nombre).first()
            if not edi:
                edi = Publisher(nombre=editorial_nombre)
                db.session.add(edi)
                db.session.flush()

            # Generar datos aleatorios
            precio = round(random.uniform(50, 300), 2)
            stock = random.randint(0, 50)
            isbn = f"978-{random.randint(10,99)}-{random.randint(1000,9999)}-{random.randint(100,999)}-{random.randint(0,9)}"

            # Crear el libro
            libro = Book(
                titulo=titulo,
                isbn=isbn,
                precio=precio,
                stock=stock,
                descripcion=descripcion,
                categoria_id=cat.id,
                autor_id=aut.id,
                editorial_id=edi.id
            )
            db.session.add(libro)

        db.session.commit()
        print("50 libros de prueba con descripciones insertados correctamente.")

    #sucursales y sus zonas de coberturas
    @app.cli.command("seed-sig")
    def seed_sig():
        """Inserta sucursales y zonas de cobertura desde archivos GeoJSON (QGIS)."""
        import json
        import os
        from app.models import Sucursal, ZonaCobertura

        # ------------------------------------------------------------
        # 1. Eliminar datos antiguos
        # ------------------------------------------------------------
        Sucursal.query.delete()
        ZonaCobertura.query.delete()

        # ------------------------------------------------------------
        # 2. Leer el archivo de sucursales (puntos)
        # ------------------------------------------------------------
        ruta_sucursales = os.path.join('static', 'geojson', 'sucursales.geojson')
        with open(ruta_sucursales, 'r', encoding='utf-8') as f:
            sucursales_data = json.load(f)

        for feature in sucursales_data['features']:
            lon, lat = feature['geometry']['coordinates']  # GeoJSON usa [lon, lat]
            props = feature['properties']
            db.session.add(Sucursal(
                nombre=props.get('nombre', 'Sin nombre'),
                direccion=props.get('direccion', ''),
                telefono=props.get('telefono', ''),
                latitud=lat,
                longitud=lon
            ))
        print(f"{len(sucursales_data['features'])} sucursales insertadas desde GeoJSON.")

        # ------------------------------------------------------------
        # 3. Leer el archivo de zonas de cobertura (polígonos)
        # ------------------------------------------------------------
        ruta_coberturas = os.path.join('static', 'geojson', 'coberturas.geojson')
        with open(ruta_coberturas, 'r', encoding='utf-8') as f:
            coberturas_data = json.load(f)

        for feature in coberturas_data['features']:
            props = feature['properties']
            geom_str = json.dumps(feature['geometry'])  # guardar geometría como string JSON
            db.session.add(ZonaCobertura(
                nombre=props.get('nombre', 'Sin nombre'),
                descripcion=props.get('descripcion', ''),
                geojson=geom_str
            ))
        print(f"{len(coberturas_data['features'])} zonas de cobertura insertadas desde GeoJSON.")

        # ------------------------------------------------------------
        # 4. Guardar cambios
        # ------------------------------------------------------------
        db.session.commit()
        print("¡Datos SIG actualizados correctamente desde archivos GeoJSON!")
        
    # -------------------------------------------------------------
    # tarea en segundo plano para avanzar simulaciones de reparto
    # -------------------------------------------------------------
    def avanzar_simulaciones():
        """cada 10 segundos avanza el progreso de los pedidos en estado 'enviado'."""
        with app.app_context():
            from app.models import Order
            pedidos = Order.query.filter_by(estado="enviado", simulacion_activa=True).all()
            for pedido in pedidos:
                if not pedido.sucursal or not pedido.cliente.latitud or not pedido.cliente.longitud:
                    continue

                url = f"https://router.project-osrm.org/route/v1/driving/{pedido.sucursal.longitud},{pedido.sucursal.latitud};{pedido.cliente.longitud},{pedido.cliente.latitud}?overview=full&geometries=geojson"
                try:
                    resp = http_requests.get(url, timeout=5)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data["routes"]:
                            total_puntos = len(data["routes"][0]["geometry"]["coordinates"])
                            # Avanzar más rápido (2 puntos por intervalo)
                            if pedido.progreso_simulacion < total_puntos - 1:
                                pedido.progreso_simulacion += 3
                            else:
                                # Marcar como entregado al llegar al final
                                pedido.estado = "entregado"
                                pedido.fecha_entrega = pedido.fecha_entrega = datetime.now(ZoneInfo("America/La_Paz")).replace(tzinfo=None)
                                pedido.simulacion_activa = False
                except Exception as e:
                    print(f"Error en simulación del pedido {pedido.id}: {e}")

            db.session.commit()

    scheduler.add_job(avanzar_simulaciones, 'interval', seconds=3)

    # -------------------------------------------------------------
    # importar y registrar blueprints
    # -------------------------------------------------------------
    from app.main.routes import main_bp
    from app.auth.routes import auth_bp
    from app.categories.routes import categories_bp
    from app.users.routes import users_bp
    from app.roles.routes import roles_bp
    from app.authors.routes import authors_bp
    from app.publishers.routes import publishers_bp
    from app.books.routes import books_bp
    from app.customers.routes import customers_bp
    from app.cart.routes import cart_bp
    from app.orders.routes import orders_bp
    from app.dashboard.routes import dashboard_bp
    from app.reports.routes import reports_bp
    from app.mapas.routes import mapas_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(categories_bp, url_prefix="/categories")
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(roles_bp, url_prefix="/roles")
    app.register_blueprint(authors_bp, url_prefix="/authors")
    app.register_blueprint(publishers_bp, url_prefix="/publishers")
    app.register_blueprint(books_bp, url_prefix="/books")
    app.register_blueprint(customers_bp, url_prefix="/customers")
    app.register_blueprint(cart_bp, url_prefix="/cart")
    app.register_blueprint(orders_bp, url_prefix="/orders")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(mapas_bp, url_prefix="/mapas")

    # manejo de errores personalizados
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template("errors/500.html"), 500

    return app