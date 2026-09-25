# mailer.py
import smtplib
import ssl
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr

logger = logging.getLogger(__name__)

# Separador de correos (ajústalo si en VB es distinto; normalmente ";")
SEPARADOR_CORREOS = ";"


class MailerError(Exception):
    """Excepción propia para errores de envío de correo."""
    pass


class MailerDAL:
    """
    Capa de acceso a datos para bitácora y configuración SMTP.
    Sustituye a MobileDAL.MobileDAL2 en VB.NET.
    """

    def registrar_bitacora_correos(self, para, asunto, cuerpo, cadena_archivos,
                                   cod_autenticacion, usar_gator, copia_a, bcc,
                                   identificador, pantalla, empresa, ordenes):
        """
        Debe devolver un objeto con atributos .respuesta (bool) y .datos (int id).
        Aquí lo simulo; en tu app real conéctalo a tu BD.
        """
        # TODO: reemplaza con INSERT en tu tabla de bitácora
        class Respuesta:
            def __init__(self, respuesta, datos):
                self.respuesta = respuesta
                self.datos = datos

        # Simulación de éxito
        return Respuesta(True, 1)

    def obtener_correos_autenticacion(self, cod_autenticacion, usar_hostgator):
        """
        Debe devolver un dict con:
        {
            "usarGator": "0"|"1",
            "ServidorSMTP": "...",
            "PuertoSMTP": 587,
            "Correo": "...",
            "Password": "..."
        }
        """

        # Obtenemos Valores de variable de entorno
        CorreoSMTP = os.getenv("COBRANZA_CORREO_SMTP")
        PasswordSMTP = os.getenv("COBRANZA_PASS_SMTP")
        ServerSMTP = os.getenv("COBRANZA_SERVER_SMTP")
        PuertoSMTP = os.getenv("COBRANZA_PUERTO_SMTP")

        return {
            "usarGator": "1" if usar_hostgator else "0",
            "ServidorSMTP": ServerSMTP,
            "PuertoSMTP": PuertoSMTP,
            "Correo": CorreoSMTP,
            "Password": PasswordSMTP,
        }

    def actualizar_bitacora_correos(self, id_bitacora, mensaje, estatus):
        """estatus: 1 = éxito, 0 = error."""
        # TODO: UPDATE bitácora
        logger.info(f"Bitácora {id_bitacora} actualizada: estatus={estatus}, msg={mensaje[:100]}")


def _deduplicar(destinatarios, ya_presentes):
    """Elimina correos ya presentes y repetidos internamente."""
    resultado = []
    for correo in destinatarios:
        correo = correo.strip()
        if not correo:
            continue
        if correo.lower() in [p.strip().lower() for p in ya_presentes]:
            continue
        if correo.lower() in [r.lower() for r in resultado]:
            continue
        resultado.append(correo)
    return resultado


def enviar_correo(
    para,
    asunto,
    cuerpo,
    lista_archivo,
    cod_autenticacion,
    usar_hostgator,
    copia_a,
    bcc,
    identificador,
    pantalla,
    empresa,
    enviar_flag,
    ordenes,
):
    """
    Equivalente a _EnviarCorreo de VB.NET.
    Retorna "" si todo OK, o mensaje de error.
    """

    dal: MailerDAL = None

    if dal is None:
        dal = MailerDAL()

    id_bitacora = -1
    msg_obj = None

    try:
        # 1. Cadena de archivos 
        cadena_archivos = ""
        if lista_archivo:
            cadena_archivos = ",".join(str(x) for x in lista_archivo)

        # 2. Registrar bitácora 
        resp = dal.registrar_bitacora_correos(
            para, asunto, cuerpo, cadena_archivos,
            cod_autenticacion, 1 if usar_hostgator else 0,
            copia_a, bcc, identificador, pantalla, empresa, ordenes
        )

        if not enviar_flag:
            return "Registro de envio de Correo"

        if not resp.respuesta:
            logger.warning("No se pudo registrar en bitácora de envío de correos, "
                           "aun así se intentará enviar")
        else:
            id_bitacora = resp.datos

        # 3. Deduplicar destinatarios
        correos_para = [c for c in para.split(SEPARADOR_CORREOS) if c.strip()]
        correos_cc = [c for c in copia_a.split(SEPARADOR_CORREOS) if c.strip()]
        correos_bcc = [c for c in bcc.split(SEPARADOR_CORREOS) if c.strip()]

        # Para: únicos entre sí
        para_list = _deduplicar(correos_para, [])
        # CC: excluir los que ya están en Para
        cc_list = _deduplicar(correos_cc, para_list)
        # BCC: excluir los que ya están en Para y CC
        bcc_list = _deduplicar(correos_bcc, para_list + cc_list)

        para_final = ",".join(para_list)
        cc_final = ",".join(cc_list)
        bcc_final = ",".join(bcc_list)

        # 4. Obtener configuración SMTP
        cfg = dal.obtener_correos_autenticacion(cod_autenticacion, usar_hostgator)

        # 5. Construir mensaje
        msg_obj = MIMEMultipart()
        msg_obj["Subject"] = asunto
        msg_obj["From"] = cfg["Correo"]
        if para_final:
            msg_obj["To"] = para_final
        if cc_final:
            msg_obj["Cc"] = cc_final
        # BCC no se agrega al header, se pasa al sendmail

        msg_obj.attach(MIMEText(cuerpo, "html", "utf-8"))

        # --- 6. Adjuntos ---
        if lista_archivo:
            for ruta in lista_archivo:
                if not os.path.isfile(ruta):
                    logger.warning(f"Adjunto no encontrado: {ruta}")
                    continue
                with open(ruta, "rb") as f:
                    parte = MIMEBase("application", "octet-stream")
                    parte.set_payload(f.read())
                encoders.encode_base64(parte)
                parte.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{os.path.basename(ruta)}"'
                )
                msg_obj.attach(parte)

        # 7. Configurar conexión SMTP 
        destinatarios_todos = para_list + cc_list + bcc_list

        if str(cfg["usarGator"]) == "1":
            # HostGator: 587 sin SSL (como en VB)
            server = smtplib.SMTP("gator3271.hostgator.com", 587, timeout=30)
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.login(cfg["Correo"], cfg["Password"])
        else:
            contexto = ssl.create_default_context()
            # Forzar TLS 1.2 (equivalente a SecurityProtocolType 3072)
            contexto.minimum_version = ssl.TLSVersion.TLSv1_2
            server = smtplib.SMTP(cfg["ServidorSMTP"], int(cfg["PuertoSMTP"]), timeout=30)
            server.ehlo()
            server.starttls(context=contexto)
            server.ehlo()
            server.login(cfg["Correo"], cfg["Password"])

        #8. Enviar
        server.sendmail(cfg["Correo"], destinatarios_todos, msg_obj.as_string())
        server.quit()

        dal.actualizar_bitacora_correos(id_bitacora, "", 1)
        return ""

    except Exception as ex:
        msg = str(ex)
        logger.exception("Error al enviar correo")
        if dal:
            try:
                dal.actualizar_bitacora_correos(id_bitacora, msg, 0)
            except Exception:
                logger.exception("Error actualizando bitácora")
        return f"Error al enviar correo: {msg}"