import os
import uuid
from PIL import Image

from app.utils.Logger import logger

LOG = logger()

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
MAX_IMAGE_SIZE     = (1200, 1200)   # píxeles máximos al redimensionar


class FileTools:
    @staticmethod
    def existe_archivo(ruta: str, nombre: str) -> bool:
        """Verifica si un archivo existe en la ruta dada."""
        return os.path.exists(os.path.join(ruta, nombre))

    @staticmethod
    def elimina_archivo(ruta: str, nombre: str) -> bool:
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
    def extension_permitida(nombre_archivo: str) -> bool:
        """Valida que la extensión del archivo esté en la lista permitida."""
        if '.' not in nombre_archivo:
            return False
        ext = nombre_archivo.rsplit('.', 1)[1].lower()
        return ext in ALLOWED_EXTENSIONS

    @staticmethod
    def generar_nombre_unico(nombre_original: str) -> str:
        """
        Genera un nombre único con UUID para evitar colisiones.
        Ejemplo: 'foto.jpg' → 'a3f1c2d4-...-uuid.jpg'
        """
        ext = nombre_original.rsplit('.', 1)[1].lower() if '.' in nombre_original else 'jpg'
        return f"{uuid.uuid4().hex}.{ext}"

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
