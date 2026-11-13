import random
import click
from .extensions import db
from .models import Restaurante, Plato

# docker compose exec flask flask seed
@click.command('seed')
def seed():
    """Carga datos de prueba: 200 restaurantes y 1000 platos."""
    ciudades = ['La Paz', 'Cochabamba', 'Santa Cruz', 'Sucre', 'Oruro', 'Tarija', 'Potosí']
    nombres_platos = ['Silpancho', 'Pique macho', 'Sajta de pollo', 'Fricasé', 'Majadito',
                      'Chicharrón', 'Anticucho', 'Sopa de maní', 'Lechón', 'Charque']
    try:
        for i in range(1, 201):
            r = Restaurante(
                nombre=f'Restaurante {i}',
                ciudad=random.choice(ciudades),
                direccion=f'Calle {i} #{100 + i}',
                telefono=f'7{i:07d}',
            )
            r.platos = [
                Plato(
                    nombre=random.choice(nombres_platos),
                    precio=round(random.uniform(10, 100), 2),
                    disponible=random.random() > 0.2,
                )
                for _ in range(5)
            ]
            db.session.add(r)
        db.session.commit()
        print('Listo: 200 restaurantes y 1000 platos.')
    except Exception:
        db.session.rollback()
        raise
    finally:
        db.session.close()