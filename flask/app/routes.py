from flask import Blueprint, request, render_template, redirect, url_for, flash
from sqlalchemy import func

from .extensions import db
from .models import Restaurante, Plato

bp = Blueprint("carta", __name__)

@bp.route('/restaurantes', methods=['GET'])
def listar_restaurantes():
    ciudad = request.args.get('ciudad', '').strip()

    consulta = (
        db.session.query(Restaurante, func.count(Plato.id).label('cantidad'))
            .outerjoin(Plato)
            .group_by(Restaurante.id)
    )

    if ciudad:
        consulta = consulta.filter(Restaurante.ciudad.ilike(f'%{ciudad}%'))

    restaurantes = consulta.order_by(Restaurante.nombre).all()

    return render_template('restaurantes/index.html', restaurantes=restaurantes, ciudad=ciudad)

@bp.route('/restaurantes/<int:restaurante_id>', methods=['GET'])
def detalle_restaurante(restaurante_id):
    restaurante = db.get_or_404(Restaurante, restaurante_id)

    platos = (
        Plato.query
        .filter_by(restaurante_id=restaurante_id)
        .order_by(Plato.nombre)
        .all()
    )
    
    return render_template('restaurantes/detalle.html', restaurante=restaurante, platos=platos)

@bp.route('/restaurantes/crear', methods=['GET'])
def formulario_crear_restaurante():
    return render_template('restaurantes/formulario.html')

@bp.route('/restaurantes/crear', methods=['POST'])
def crear_restaurante():
    try:
        restaurante = Restaurante(
        nombre=request.form.get('nombre', '').strip(),
        ciudad=request.form.get('ciudad', '').strip(),
        direccion=request.form.get('direccion', '').strip() or None,
        telefono=request.form.get('telefono', '').strip() or None,
        )

        db.session.add(restaurante)
        db.session.commit()
        flash('Restaurante creado.', 'exito')
    except Exception:
        db.session.rollback()
        flash('No se pudo crear.', 'error')

    return redirect(url_for('carta.listar_restaurantes'))

@bp.route('/restaurantes/<int:restaurante_id>/editar', methods=['GET', 'POST'])
def editar_restaurante(restaurante_id):
    restaurante = db.get_or_404(Restaurante, restaurante_id)

    if request.method == 'GET':
        return render_template('restaurantes/formulario.html', restaurante=restaurante)

    try:
        restaurante.nombre = request.form.get('nombre', '').strip()
        restaurante.ciudad = request.form.get('ciudad', '').strip()
        restaurante.direccion = request.form.get('direccion', '').strip() or None
        restaurante.telefono = request.form.get('telefono', '').strip() or None

        db.session.commit()
        flash('Restaurante actualizado.', 'exito')
    except Exception:
        db.session.rollback()
        flash('No se pudo actualizar.', 'error')

    return redirect(url_for('carta.detalle_restaurante', restaurante_id=restaurante_id))

@bp.route('/restaurantes/<int:restaurante_id>/eliminar', methods=['POST'])
def eliminar_restaurante(restaurante_id):
    restaurante = db.get_or_404(Restaurante, restaurante_id)

    try:
        db.session.delete(restaurante)
        db.session.commit()
        flash('Restaurante eliminado.', 'exito')
    except Exception:
        db.session.rollback()
        flash('No se pudo eliminar.', 'error')

    return redirect(url_for('carta.listar_restaurantes'))

@bp.route('/restaurantes/<int:restaurante_id>/platos', methods=['POST'])
def crear_plato(restaurante_id):
    db.get_or_404(Restaurante, restaurante_id)

    try:
        plato = Plato(
        nombre=request.form.get('nombre', '').strip(),
        precio=request.form.get('precio', ''),
        disponible='disponible' in request.form,
        restaurante_id=restaurante_id,
        )

        db.session.add(plato)
        db.session.commit()
        flash('Plato creado.', 'exito')
    except Exception:
        db.session.rollback()
        flash('No se pudo crear.', 'error')
        
    return redirect(url_for('carta.detalle_restaurante', restaurante_id=restaurante_id))

@bp.app_errorhandler(404)
def no_encontrado(error):
    return render_template('errores/404.html'), 404

@bp.app_errorhandler(500)
def error_interno(error):
    db.session.rollback()
    return render_template('errores/500.html'), 500

@bp.route('/', methods=['GET'])
def inicio():
    return redirect(url_for('carta.listar_restaurantes'))

