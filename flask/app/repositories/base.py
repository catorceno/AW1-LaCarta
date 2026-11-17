from sqlalchemy.exc import IntegrityError

from ..errors import ConflictoError, NoSeGuardoError


class Repositorio:
    """Lo común a todos los repositorios: la sesión y el commit.

    El servicio decide cuándo llamar a commit(); el repositorio solo traduce
    los errores de SQLAlchemy a errores propios, para que el servicio nunca
    tenga que importar SQLAlchemy.
    """

    def __init__(self, session):
        self.session = session

    def commit(self):
        try:
            self.session.commit()
        except IntegrityError as err:
            self.session.rollback()
            raise ConflictoError(str(err.orig)) from err
        except Exception as err:
            self.session.rollback()
            raise NoSeGuardoError(str(err)) from err
