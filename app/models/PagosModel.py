from app.main import ConnectionDb
from app.utils.Logger import logger

from sqlalchemy import text

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

    @staticmethod
    def registrar_pago(cod_empresa,cod_cliente,rfc_cliente,moneda ,importe_monto,importe_disponible,importe_abonado):
        sql = text(f"EXEC sp_RegistrarPagos_SIC @CodEmpresa={cod_empresa},@CodCliente={cod_cliente},"
                f"@RfcCliente='{rfc_cliente}',@Moneda='{moneda}',@ImporteMonto='{importe_monto}',"
                f"@ImporteDisponible='{importe_disponible}',@ImporteAbonado='{importe_abonado}';")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        return result
    
    @staticmethod
    def registrar_comprobante_pago(id_generado,ip_servidor_archivo,ruta_archivo,carpeta_padre,nombre_archivo):
        sql = text(f"EXEC sp_RegistrarComprobantePago_SIC @IdPago={id_generado},@IpServidor='{ip_servidor_archivo}',"
                f"@RutaArchivo='{ruta_archivo}',@CarpetaPadre='{carpeta_padre}',@NombreArchivo='{nombre_archivo}';")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        return result

    @staticmethod
    def registrar_pago_detalle(id_pago, facturas_data):
        # Validacion por si no hay elementos que insertar
        if not facturas_data:
            return None

        # Armado de consulta como texto
        sql_query = """
            DECLARE @TY_PagosDetalle TYSIC_PagosDetalle;
            SET NOCOUNT ON
            -- Insertar los datos en la tabla temporal
            INSERT INTO @TY_PagosDetalle(orden, factura, importe_factura, importe_abonado, importe_abonar, saldo_pendiente)
            VALUES
            """
        # Concatena los valores a la consulta SQL
        consulta_sql = ""

        for item in facturas_data:
            # Escapar adecuadamente los valores
            consulta_sql += f"({item['orden']},'{item['factura']}',{item['importe_factura']},{item['importe_abonado']},{item['importe_abonar']},{item['saldo_pendiente']}),"
        
        # Quitar la ultima coma y espacio
        consulta_sql = consulta_sql[:-1]

        # CORRECCIÓN AQUÍ: @TYPagosDetalle (coincide con el SP)
        sql_query += consulta_sql + """
            EXEC sp_RegistrarPagosDetalle_SIC
                @IdPago = {idPago},
                @TYPagosDetalle = @TY_PagosDetalle;
            """

        # Formateamos la cadena SQL y asignamos las variables
        sql_query = sql_query.format(
            idPago=id_pago,
        )

        # Convertimos la cadena final a un objeto TextClause
        sql_query = text(sql_query)
        result = sql_connection.session.execute(sql_query)

        return result
    ###########################################################
    def roll_back(self):
        sql_connection.session.rollback(self)

