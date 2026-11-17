"""Presentación de la carta: lee el formulario, llama al servicio y elige la plantilla.

Aquí también están los manejadores de error de toda la app: traducen los
errores del dominio (errors.py) a respuestas HTTP.
"""
from decimal import Decimal, InvalidOperation

from flask import Blueprint, request, render_template, redirect, url_for, flash

from .extensions import db
from .auth import requires_auth
from .errors import NoEncontradoError, NoSeGuardoError, ReglaDeNegocioError
from .repositories import RestauranteRepository
from .services.restaurante_service import PlatoDetails, RestauranteDetails, RestauranteService

bp = Blueprint("carta", __name__)


def servicio():
    return RestauranteService(RestauranteRepository(db.session))


def leer_restaurante(form):
    return RestauranteDetails(
        nombre=form.get('nombre', '').strip(),
        ciudad=form.get('ciudad', '').strip(),
        direccion=form.get('direccion', '').strip() or None,
        telefono=form.get('telefono', '').strip() or None,
    )


@bp.route('/restaurantes', methods=['GET'])
def listar_restaurantes():
    ciudad = request.args.get('ciudad', '').strip()
    restaurantes = servicio().listar(ciudad)
    return render_template('restaurantes/index.html', restaurantes=restaurantes, ciudad=ciudad)

@bp.route('/restaurantes/<int:restaurante_id>', methods=['GET'])
def detalle_restaurante(restaurante_id):
    restaurante, platos = servicio().carta(restaurante_id)
    return render_template('restaurantes/detalle.html', restaurante=restaurante, platos=platos)

@bp.route('/restaurantes/crear', methods=['GET'])
@requires_auth("write:carta")
def formulario_crear_restaurante(payload):
    return render_template('restaurantes/formulario.html')

@bp.route('/restaurantes/crear', methods=['POST'])
@requires_auth("write:carta")
def crear_restaurante(payload):
    try:
        servicio().crear(leer_restaurante(request.form))
        flash('Restaurante creado.', 'exito')
    except NoSeGuardoError:
        flash('No se pudo crear.', 'error')

    return redirect(url_for('carta.listar_restaurantes'))

@bp.route('/restaurantes/<int:restaurante_id>/editar', methods=['GET', 'POST'])
@requires_auth("write:carta")
def editar_restaurante(payload, restaurante_id):
    if request.method == 'GET':
        return render_template('restaurantes/formulario.html', restaurante=servicio().obtener(restaurante_id))

    try:
        servicio().actualizar(restaurante_id, leer_restaurante(request.form))
        flash('Restaurante actualizado.', 'exito')
    except NoSeGuardoError:
        flash('No se pudo actualizar.', 'error')

    return redirect(url_for('carta.detalle_restaurante', restaurante_id=restaurante_id))

@bp.route('/restaurantes/<int:restaurante_id>/eliminar', methods=['POST'])
@requires_auth("delete:carta")
def eliminar_restaurante(payload, restaurante_id):
    try:
        servicio().eliminar(restaurante_id)
        flash('Restaurante eliminado.', 'exito')
    except NoSeGuardoError:
        flash('No se pudo eliminar.', 'error')

    return redirect(url_for('carta.listar_restaurantes'))

@bp.route('/restaurantes/<int:restaurante_id>/platos', methods=['POST'])
@requires_auth("write:carta")
def crear_plato(payload, restaurante_id):
    try:
        plato = PlatoDetails(
            nombre=request.form.get('nombre', '').strip(),
            precio=Decimal(request.form.get('precio', '')),
            disponible='disponible' in request.form,
        )
        servicio().agregar_plato(restaurante_id, plato)
        flash('Plato creado.', 'exito')
    except (InvalidOperation, NoSeGuardoError):
        flash('No se pudo crear.', 'error')

    return redirect(url_for('carta.detalle_restaurante', restaurante_id=restaurante_id))

@bp.app_errorhandler(ReglaDeNegocioError)
def regla_rota(error):
    return render_template('errores/400.html', mensaje=str(error)), 400

@bp.app_errorhandler(NoEncontradoError)
def recurso_no_encontrado(error):
    return render_template('errores/404.html'), 404

@bp.app_errorhandler(400)
def solicitud_invalida(error):
    return render_template('errores/400.html', mensaje=error.description), 400

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
