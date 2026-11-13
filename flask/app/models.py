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
