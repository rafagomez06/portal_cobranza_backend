class DatabaseError(Exception):
    """Error al ejecutar operaciones en base de datos."""
    pass

class MissingValueError(Exception):
    """Falta un valor requerido en la petición."""
    pass

class UnexpectedError(Exception):
    """Error inesperado no clasificado."""
    pass

class NotFoundError(Exception):
    """El recurso solicitado no existe."""
    pass

class UnauthorizedError(Exception):
    """El usuario no tiene permisos para esta acción."""
    pass

class FileUploadError(Exception):
    """Error al cargar o procesar un archivo."""
    pass
