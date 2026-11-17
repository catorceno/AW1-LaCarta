"""Errores del dominio.

Los lanzan los servicios (y el repositorio, al traducir los errores de la
base). Ninguno sabe de HTTP: la capa de presentación decide qué responder.
"""


class ReglaDeNegocioError(Exception):
    """Se rompió una regla del enunciado. La presentación responde 400."""


class NoEncontradoError(Exception):
    """No existe, o no es visible para quien lo pide. La presentación responde 404."""


class NoSeGuardoError(Exception):
    """El commit falló. El repositorio ya hizo rollback."""


class ConflictoError(NoSeGuardoError):
    """El commit violó una restricción de la base (UNIQUE, CHECK o FK)."""
