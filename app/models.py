# app/models.py
# definicion de todos los modelos de la base de datos para la fase emergent es ii

from datetime import datetime
from app.extensions import db
from flask_login import UserMixin

# ------------------------------------------------------------
# modelo: rol de usuario
# ------------------------------------------------------------
class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

    # relacion inversa con usuarios
    usuarios = db.relationship("User", back_populates="rol", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Role {self.nombre}>"


# ------------------------------------------------------------
# modelo: usuario (con herencia de usermixin para flask-login)
# ------------------------------------------------------------
class User(db.Model, UserMixin):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)

    # relacion con la tabla roles
    rol = db.relationship("Role", back_populates="usuarios")

    # relacion con el carrito (un usuario puede tener un carrito activo)
    carrito = db.relationship("Cart", back_populates="usuario", uselist=False, cascade="all, delete-orphan")

    # relación con el perfil de cliente (uno a uno)
    perfil_cliente = db.relationship("Customer", back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    
    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"<User {self.username}>"


# ------------------------------------------------------------
# modelo: categoria de libro
# ------------------------------------------------------------
class Category(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.Text)

    # relacion inversa con libros
    libros = db.relationship("Book", back_populates="categoria", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category {self.nombre}>"


# ------------------------------------------------------------
# modelo: autor
# ------------------------------------------------------------
class Author(db.Model):
    __tablename__ = "autores"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    nacionalidad = db.Column(db.String(100))
    biografia = db.Column(db.Text)

    # relacion inversa con libros
    libros = db.relationship("Book", back_populates="autor", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Author {self.nombre}>"


# ------------------------------------------------------------
# modelo: editorial
# ------------------------------------------------------------
class Publisher(db.Model):
    __tablename__ = "editoriales"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    pais = db.Column(db.String(100))
    telefono = db.Column(db.String(20))

    # relacion inversa con libros
    libros = db.relationship("Book", back_populates="editorial", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Publisher {self.nombre}>"


# ------------------------------------------------------------
# modelo: libro
# ------------------------------------------------------------
class Book(db.Model):
    __tablename__ = "libros"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    descripcion = db.Column(db.Text)
    imagen = db.Column(db.String(200))  # nombre del archivo de portada

    # llaves foraneas
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey("autores.id"), nullable=False)
    editorial_id = db.Column(db.Integer, db.ForeignKey("editoriales.id"), nullable=False)

    # relaciones
    categoria = db.relationship("Category", back_populates="libros")
    autor = db.relationship("Author", back_populates="libros")
    editorial = db.relationship("Publisher", back_populates="libros")

    # relacion inversa con detalles de pedido y carrito
    detalles_pedido = db.relationship("OrderDetail", back_populates="libro", cascade="all, delete-orphan")
    detalles_carrito = db.relationship("CartDetail", back_populates="libro", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Book {self.titulo}>"


# ------------------------------------------------------------
# modelo: cliente
# ------------------------------------------------------------
# modelo: cliente (perfil de compra)
class Customer(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", name="fk_clientes_usuarios"), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False, default="")
    apellido = db.Column(db.String(100), nullable=False, default="")
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint('usuario_id', name='uq_clientes_usuario_id'),
    )
    # relación con el usuario
    usuario = db.relationship("User", back_populates="perfil_cliente")
    # relación inversa con pedidos
    pedidos = db.relationship("Order", back_populates="cliente", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer {self.nombre} {self.apellido}>"

# ------------------------------------------------------------
# modelo: carrito de compras (uno por usuario)
# ------------------------------------------------------------
class Cart(db.Model):
    __tablename__ = "carrito"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), unique=True, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    # relacion con usuario
    usuario = db.relationship("User", back_populates="carrito")
    # relacion con los items del carrito
    items = db.relationship("CartDetail", back_populates="carrito", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Cart usuario:{self.usuario_id}>"


# ------------------------------------------------------------
# modelo: detalle del carrito (libros agregados)
# ------------------------------------------------------------
class CartDetail(db.Model):
    __tablename__ = "carrito_detalle"

    id = db.Column(db.Integer, primary_key=True)
    carrito_id = db.Column(db.Integer, db.ForeignKey("carrito.id"), nullable=False)
    libro_id = db.Column(db.Integer, db.ForeignKey("libros.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    subtotal = db.Column(db.Float, nullable=False)

    # relaciones
    carrito = db.relationship("Cart", back_populates="items")
    libro = db.relationship("Book", back_populates="detalles_carrito")

    def __repr__(self):
        return f"<CartDetail libro:{self.libro_id} cant:{self.cantidad}>"


# ------------------------------------------------------------
# modelo: pedido
# ------------------------------------------------------------
class Order(db.Model):
    __tablename__ = "pedidos"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default="pendiente")  # pendiente, enviado, entregado
    fecha_envio = db.Column(db.DateTime, nullable=True)
    fecha_entrega = db.Column(db.DateTime, nullable=True)
    # relaciones
    cliente = db.relationship("Customer", back_populates="pedidos")
    detalles = db.relationship("OrderDetail", back_populates="pedido", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.id} estado:{self.estado}>"


# ------------------------------------------------------------
# modelo: detalle del pedido
# ------------------------------------------------------------
class OrderDetail(db.Model):
    __tablename__ = "detalle_pedido"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False)
    libro_id = db.Column(db.Integer, db.ForeignKey("libros.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)  # precio unitario al momento de la compra

    # relaciones
    pedido = db.relationship("Order", back_populates="detalles")
    libro = db.relationship("Book", back_populates="detalles_pedido")

    def __repr__(self):
        return f"<OrderDetail pedido:{self.pedido_id} libro:{self.libro_id}>"