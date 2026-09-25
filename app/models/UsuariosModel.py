from app.main import ConnectionDb
from app.utils.Logger import logger

from sqlalchemy import insert, text

LOG = logger()
sql_connection = ConnectionDb.alchemy_db

## Modelos de tablas de catalogos

class UsuariosModel(sql_connection.Model):
    __tablename__ = 'UsuariosModel'

    id_UsuariosModel = sql_connection.Column(sql_connection.Integer, primary_key=True)
    nombre = sql_connection.Column(sql_connection.String(100), nullable=False)

    def __init__(self, id_UsuariosModel, nombre=None) -> None:
        self.id_UsuariosModel = id_UsuariosModel
        self.nombre = nombre

    @staticmethod
    def obtener_usuarios():
        sql = text(f"EXEC sp_ObtenerListadoUsuariosChecadorApp;")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        return result
    
    @staticmethod
    def validar_login(cliente,correo,password_hash):
        sql = text(f"EXEC sp_ValidarClientes_SIC @CodCliente='{cliente}',@Correo='{correo}',@Password='{password_hash}';")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        return result
    
    @staticmethod
    def actualizar_password(correo,password_hash):
        sql = text(f"EXEC sp_ActualizarPasswordCliente_SIC @Correo='{correo}', @NuevaPassword='{password_hash}';")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        return result

    @staticmethod
    def actualizar_permiso_sic(usuario,flag_permiso): ###PENDIENTE MODIFICAR
        sql = text(f"EXEC sp_ActualizarPermisoAPP @UsuarioChecador='{usuario}',@FlagPermiso={flag_permiso};")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        return result
    
    @staticmethod
    def obtener_pass_cliente_login(cliente):
        sql = text(f"EXEC sp_ObtenerPassClienteLogin_SIC @CodCliente='{cliente}';")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        return result
    
    @staticmethod
    def validar_correo_cliente(correo_cliente):
        sql = text(f"EXEC sp_ValidarCorreoCliente_SIC @Correo='{correo_cliente}';")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        return result
    
    @staticmethod
    def registrar_usuario(cod_cliente, nom_cliente,rfc_cte,moneda,correo):
        sql = text(f"EXEC sp_RegistrarCliente_SIC @CodCliente='{cod_cliente}',@NomCliente='{nom_cliente}',"
                f"@RfcCliente='{rfc_cte}',@Moneda='{moneda}',@CorreoCliente='{correo}';")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        return result
    
    def roll_back(self):
        sql_connection.session.rollback(self)

