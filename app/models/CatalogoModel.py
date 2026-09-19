from app.main import ConnectionDb
from app.utils.Logger import logger

from sqlalchemy import insert, text

LOG = logger()
sql_connection = ConnectionDb.alchemy_db

## Modelos de tablas de catalogos

class CatalogoModel(sql_connection.Model):
    __tablename__ = 'CatalogoModel'

    id_CatalogoModel = sql_connection.Column(sql_connection.Integer, primary_key=True)
    nombre = sql_connection.Column(sql_connection.String(100), nullable=False)

    def __init__(self, id_CatalogoModel, nombre=None) -> None:
        self.id_CatalogoModel = id_CatalogoModel
        self.nombre = nombre

    @staticmethod
    def obtener_tipos_facturas():
        sql = text(f"EXEC sp_ObtenerCatalogoTiposFacturas_SIC;")
        LOG.info(f"## Consulta: {sql}")
        result = sql_connection.session.execute(sql)
        return result

    def roll_back(self):
        sql_connection.session.rollback(self)

