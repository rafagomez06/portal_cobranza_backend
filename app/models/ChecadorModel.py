from app.main import ConnectionDb
from app.utils.Logger import logger

from sqlalchemy import insert, text

LOG = logger()
sql_connection = ConnectionDb.alchemy_db

## Modelos de tablas de catalogos

class ChecadorModel(sql_connection.Model):
    __tablename__ = 'ChecadorModel'

    id_ChecadorModel = sql_connection.Column(sql_connection.Integer, primary_key=True)
    nombre = sql_connection.Column(sql_connection.String(100), nullable=False)

    def __init__(self, id_ChecadorModel, nombre=None) -> None:
        self.id_ChecadorModel = id_ChecadorModel
        self.nombre = nombre

    @staticmethod
    def registrar_checada(usuario_id,tipo_checada,latitud,longitud,direccionCompleta,fecha_hora_captura,id_local):
        sql = text(f"EXEC sp_RegistrarChecada @UsuarioSistema='{usuario_id}',@IdTipoChecada={tipo_checada},@FechaCapturaDispositivo='{fecha_hora_captura}',"
                f" @Latitud='{latitud}',@Longitud='{longitud}',@DireccionCompleta='{direccionCompleta}', @IdlocalUUID='{id_local}';")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        
        return result
    
    @staticmethod
    def obtener_historial_checadas(usuario_id,rango_fecha_inicio,rango_fecha_fin):
        sql = text(f"EXEC sp_HistorialChecadas @UsuarioSistema='{usuario_id}',@RangoFechaInicio='{rango_fecha_inicio}',@RangoFechaFin='{rango_fecha_fin}';")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        
        return result
    
    @staticmethod
    def obtener_bitacora_checadas_detalle(usuario_id,rango_fecha_inicio,rango_fecha_fin,id_empresa,pagina):
        sql = text(f"EXEC sp_BitacoraChecadasDetalle @UsuarioSistema='{usuario_id}',@RangoFechaInicio='{rango_fecha_inicio}'"
                f",@RangoFechaFin='{rango_fecha_fin}', @IdEmpresa='{id_empresa}',@Pagina={pagina} ;")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        
        return result


    def roll_back(self):
        sql_connection.session.rollback(self)

