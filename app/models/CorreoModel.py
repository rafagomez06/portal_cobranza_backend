from app.main import ConnectionDb
from app.utils.Logger import logger

from sqlalchemy import insert, text

LOG = logger()
sql_connection = ConnectionDb.alchemy_db

## Consumos a SQL de Pagos
class CorreoModel(sql_connection.Model):
    __tablename__ = 'CorreoModel'

    id_CorreoModel = sql_connection.Column(sql_connection.Integer, primary_key=True)
    nombre = sql_connection.Column(sql_connection.String(100), nullable=False)

    def __init__(self, id_CorreoModel, nombre=None) -> None:
        self.id_CorreoModel = id_CorreoModel
        self.nombre = nombre

    #############################################################
    @staticmethod
    def registrar_bitacora_correo(id_empleado, id_empresa,usuario_checador,nombre,apellido_paterno,apellido_materno,correo,usuario_creacion):
        sql = text(f"EXEC sp_RegistrarUsuarioChecadorApp @IdEmpleado={id_empleado},@IdEmpresa={id_empresa},"
                f"@UsuarioChecador='{usuario_checador}',@NombreUsuario='{nombre}',@ApellidoPaterno='{apellido_paterno}',"
                f"@ApellidoMaterno='{apellido_materno}',@Correo='{correo}',@UsuarioCreacion='{usuario_creacion}';")
        LOG.info(f"## Consulta: {sql}")

        result = sql_connection.session.execute(sql)
        return result
    
    def roll_back(self):
        sql_connection.session.rollback(self)

