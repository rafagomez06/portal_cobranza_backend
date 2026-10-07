import os
import uuid
from PIL import Image
from dotenv import load_dotenv
from app.utils.Logger import logger
from datetime import datetime


LOG = logger()

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}
MAX_IMAGE_SIZE     = (1200, 1200)   # píxeles máximos al redimensionar


class FileTools:
    @staticmethod
    def existe_archivo(ruta: str, nombre: str) -> bool:
        """Verifica si un archivo existe en la ruta dada."""
        return os.path.exists(os.path.join(ruta, nombre))

    @staticmethod
    def elimina_archivo_ruta_nombre(ruta: str, nombre: str) -> bool:
        """
        Elimina un archivo si existe.
        Retorna True si lo eliminó, False si no existía.
        """
        ruta_completa = os.path.join(ruta, nombre)
        if os.path.exists(ruta_completa):
            os.remove(ruta_completa)
            LOG.info(f"Archivo eliminado: {ruta_completa}")
            return True
        LOG.warning(f"Archivo no encontrado para eliminar: {ruta_completa}")
        return False

    @staticmethod
    def elimina_archivo_ruta(ruta: str) -> bool:
        """
        Elimina un archivo si existe.
        Retorna True si lo eliminó, False si no existía.
        """
        if os.path.exists(ruta):
            os.remove(ruta)
            LOG.info(f"Archivo eliminado: {ruta}")
            return True
        LOG.warning(f"Archivo no encontrado para eliminar: {ruta}")
        return False
    
    @staticmethod
    def extension_permitida(nombre_archivo: str) -> bool:
        """Valida que la extensión del archivo esté en la lista permitida."""
        if '.' not in nombre_archivo:
            return False
        ext = nombre_archivo.rsplit('.', 1)[1].lower()
        return ext in ALLOWED_EXTENSIONS

    @staticmethod
    def generar_nombre_unico(nombre_original):
        """
        Genera un nombre único con UUID para evitar colisiones.
        Ejemplo: 'foto.jpg''a3f1c2d4-...-uuid.jpg'
        """
        ext = nombre_original.rsplit('.', 1)[1].lower() if '.' in nombre_original else 'jpg'
        return f"{uuid.uuid4().hex}.{ext}"
    
    @staticmethod
    def generar_nombre_personalizado(nombre_original,cod_cliente,rfc):
        """
        Genera un nombre único con codigo y rfc de cliente para evitar colisiones agregando timestamp y uuid.
        Ejemplo: 'DI456_BAC800208B25_20261003130506_8f5ef079.pdf'
        """
        # Genera tiempo con milisegundos
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        # Obtiene extension de archivo
        extension = nombre_original.rsplit('.', 1)[1].lower() if '.' in nombre_original else 'jpg'
        hexa_limpio = uuid.uuid4().hex
        hexa_corto = hexa_limpio[:8]
        
        # Armado de nombre del archivo
        nombre_archivo_actualizado = f"{cod_cliente}_{rfc}_{timestamp}_{hexa_corto}.{extension}"

        return nombre_archivo_actualizado

    @staticmethod
    def validar_es_imagen(ruta_completa: str) -> bool:
        """
        Usa Pillow para verificar que el archivo es realmente una imagen
        y no un archivo malicioso con extensión cambiada.
        """
        try:
            with Image.open(ruta_completa) as img:
                img.verify()
            return True
        except Exception as e:
            LOG.error(f"Archivo no es imagen válida: {ruta_completa} — {str(e)}")
            return False

    @staticmethod
    def redimensionar_imagen(ruta_completa: str, max_size: tuple = MAX_IMAGE_SIZE) -> bool:
        """
        Redimensiona la imagen si supera el tamaño máximo.
        Mantiene proporción. Útil para optimizar almacenamiento.
        """
        try:
            with Image.open(ruta_completa) as img:
                img.thumbnail(max_size, Image.LANCZOS)
                img.save(ruta_completa, optimize=True, quality=85)
            return True
        except Exception as e:
            LOG.error(f"Error al redimensionar imagen: {str(e)}")
            return False

    @staticmethod
    def guardar_imagen(archivo, carpeta_destino: str) -> str | None:
        if not FileTools.extension_permitida(archivo.filename):
            LOG.warning(f"Extensión no permitida: {archivo.filename}")
            return None

        nombre_unico  = FileTools.generar_nombre_unico(archivo.filename)
        ruta_completa = os.path.join(carpeta_destino, nombre_unico)

        os.makedirs(carpeta_destino, exist_ok=True)
        archivo.save(ruta_completa)

        if not FileTools.validar_es_imagen(ruta_completa):
            os.remove(ruta_completa)
            return None
        FileTools.redimensionar_imagen(ruta_completa)
        LOG.info(f"Imagen guardada: {ruta_completa}")
        return nombre_unico

    @staticmethod
    def guardar_archivo_cobranza(archivo,cod_cliente,rfc):
        #valida extension de archivo
        if not FileTools.extension_permitida(archivo.filename):
            LOG.warning(f"Extensión no permitida: {archivo.filename}")
            return None
        
        # Carpeta Cliente
        cod_cliente_folder = cod_cliente.upper()
        
        # Obtenemos la ruta de variable de entorno
        server_destino = os.getenv("IP_SERVER_FILE")
        carpeta_destino = os.getenv("CARPETA_DESTINO")
        
        # Armado de ruta
        ruta_destino = os.path.join(f"{server_destino}{carpeta_destino}", cod_cliente_folder)

        # Crea la carpeta si no existe
        if ruta_destino and not os.path.exists(ruta_destino):
            os.makedirs(ruta_destino, exist_ok=True)

        nombre_archivo_unico  = FileTools.generar_nombre_personalizado(archivo.filename,cod_cliente,rfc)
        ruta_completa = os.path.join(ruta_destino, nombre_archivo_unico)

        archivo.save(ruta_completa)

        LOG.info(f"Archivo guardado: {ruta_completa}")

        info_archivo = {
            "ruta_completa":ruta_completa,
            "ip_servidor_archivo":server_destino,
            "ruta_comprobante":carpeta_destino,
            "carpeta_padre": cod_cliente_folder,
            "nombre_archivo":nombre_archivo_unico
            }

        return info_archivo
