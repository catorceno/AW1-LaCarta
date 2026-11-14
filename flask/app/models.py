from .extensions import db

# bigint en Postgres (como lo creó Django); INTEGER en SQLite, que solo
# autoincrementa un "INTEGER PRIMARY KEY" (lo usan los tests con create_all)
BigId = db.BigInteger().with_variant(db.Integer, "sqlite")

class Restaurante(db.Model):
    __tablename__ = 'lacarta_restaurante'
    id = db.Column(BigId, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    ciudad = db.Column(db.String(80), nullable=False)
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(30))

    platos = db.relationship(
        'Plato',
        back_populates='restaurante',
        cascade='all, delete-orphan',
        lazy=True
    )

    def __repr__(self):
        return f'<Restaurante id={self.id} nombre={self.nombre}>'

class Plato(db.Model):
    __tablename__ = 'lacarta_plato'
    id = db.Column(BigId, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    precio = db.Column(db.Numeric(10,2), db.CheckConstraint('precio > 0', 'plato_precio_positivo'), nullable=False)
    disponible = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    restaurante_id = db.Column(
        db.BigInteger,
        db.ForeignKey('lacarta_restaurante.id'),
        nullable=False
    )

    restaurante = db.relationship('Restaurante', back_populates='platos')

    def __repr__(self):
        return f'<Plato id={self.id} nombre={self.nombre}>'


ETIQUETAS_ESTADO = {
    'pendiente': 'Pendiente',
    'en_preparacion': 'En preparación',
    'listo': 'Listo',
    'entregado': 'Entregado',
    'cancelado': 'Cancelado',
}
ESTADOS = tuple(ETIQUETAS_ESTADO)
_ESTADOS_SQL = ", ".join(f"'{e}'" for e in ESTADOS)   # 'pendiente', 'en_preparacion', ...


class Pedido(db.Model):
    """Tabla creada por Django (lacarta_pedido). Flask solo la usa.

    Los CHECK repiten los de Django, con los mismos nombres: en producción no
    hacen nada (la tabla ya existe), pero los tests la crean en SQLite con
    create_all() y así tienen las mismas reglas que Postgres.
    """
    __tablename__ = 'lacarta_pedido'
    __table_args__ = (
        db.CheckConstraint(f"estado IN ({_ESTADOS_SQL})", name='pedido_estado_valido'),
        db.CheckConstraint('total >= 0', name='pedido_total_no_negativo'),
    )

    id = db.Column(BigId, primary_key=True)
    cliente = db.Column(db.String(255), nullable=False)   # el "sub" del token de Auth0
    estado = db.Column(db.String(20), nullable=False, default='pendiente', server_default='pendiente')
    # Sin default de Python: SQLAlchemy no envía la columna y Postgres pone now()
    fecha = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0, server_default='0')
    restaurante_id = db.Column(
        db.BigInteger,
        db.ForeignKey('lacarta_restaurante.id'),
        nullable=False
    )

    restaurante = db.relationship('Restaurante')
    items = db.relationship(
        'ItemPedido',
        back_populates='pedido',
        cascade='all, delete-orphan',
        lazy=True
    )

    @property
    def estado_etiqueta(self):
        """'en_preparacion' -> 'En preparación', para mostrarlo en las plantillas."""
        return ETIQUETAS_ESTADO.get(self.estado, self.estado)

    def __repr__(self):
        return f'<Pedido id={self.id} cliente={self.cliente} estado={self.estado}>'


class ItemPedido(db.Model):
    """Tabla creada por Django (lacarta_itempedido)."""
    __tablename__ = 'lacarta_itempedido'
    __table_args__ = (
        db.CheckConstraint('cantidad > 0', name='itempedido_cantidad_positivo'),
        db.CheckConstraint('precio_unitario >= 0', name='itempedido_preciounitario_no_negativo'),
    )

    id = db.Column(BigId, primary_key=True)
    cantidad = db.Column(db.Integer, nullable=False)
    # Sin default: se copia del plato al crear el pedido (precio congelado, R1.3)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    pedido_id = db.Column(
        db.BigInteger,
        db.ForeignKey('lacarta_pedido.id'),
        nullable=False
    )
    plato_id = db.Column(
        db.BigInteger,
        db.ForeignKey('lacarta_plato.id'),
        nullable=False
    )

    pedido = db.relationship('Pedido', back_populates='items')
    plato = db.relationship('Plato')

    def __repr__(self):
        return f'<ItemPedido {self.cantidad} x plato={self.plato_id}>'
