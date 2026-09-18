from app.main import ConnectionDb
from app.utils.Logger import logger

from sqlalchemy import insert, text

LOG = logger()
sql_connection = ConnectionDb.alchemy_db

## Consumos a SQL de Pagos
class PagosModel(sql_connection.Model):
    __tablename__ = 'PagosModel'

    id_PagosModel = sql_connection.Column(sql_connection.Integer, primary_key=True)
    nombre = sql_connection.Column(sql_connection.String(100), nullable=False)

    def __init__(self, id_PagosModel, nombre=None) -> None:
        self.id_PagosModel = id_PagosModel
        self.nombre = nombre

    @staticmethod
    def obtener_facturas(cod_cliente):
        sql = text(f"EXEC sp_ObtenerFacturasCliente_SIC @CodCliente='{cod_cliente}';")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        return result

    
    #############################################################
    @staticmethod
    def validar_login(usuario,password_hash):
        sql = text(f"EXEC sp_ValidarUsuariosChecador @UsuarioChecador='{usuario}',@Password='{password_hash}';")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        return result
    
    @staticmethod
    def actualizar_password(usuario,password_hash):
        sql = text(f"EXEC sp_ActualizarPasswordUsuario @UsuarioChecador='{usuario}',@Password='{password_hash}';")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        return result

    @staticmethod
    def actualizar_permiso_app(usuario,flag_permiso):
        sql = text(f"EXEC sp_ActualizarPermisoAPP @UsuarioChecador='{usuario}',@FlagPermiso={flag_permiso};")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        return result
    
    @staticmethod
    def obtener_usuario_login(usuario):
        sql = text(f"EXEC sp_ObtenerUsuarioLogin @UsuarioChecador='{usuario}';")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        return result
    
    @staticmethod
    def registrar_usuario(id_empleado, id_empresa,usuario_checador,nombre,apellido_paterno,apellido_materno,correo,usuario_creacion):
        sql = text(f"EXEC sp_RegistrarUsuarioChecadorApp @IdEmpleado={id_empleado},@IdEmpresa={id_empresa},"
                f"@UsuarioChecador='{usuario_checador}',@NombreUsuario='{nombre}',@ApellidoPaterno='{apellido_paterno}',"
                f"@ApellidoMaterno='{apellido_materno}',@Correo='{correo}',@UsuarioCreacion='{usuario_creacion}';")
        LOG.info(f"## Consulta: {sql}")

        result = sql_connection.session.execute(sql)
        return result
    
    def roll_back(self):
        sql_connection.session.rollback(self)

