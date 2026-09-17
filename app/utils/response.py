import json
from datetime import date, datetime
from flask import jsonify

from app.utils.Logger import logger

LOG = logger()

def api_response(status_code, data=None, status_message=None, message=None):
    try:
        body = {
            "status_code": status_code,
            "status_message": status_message,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
        return jsonify({"body": body}), status_code
        
    except Exception as e:
        LOG.error(str(e))
        raise e
    

def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    raise TypeError(f"Tipo {type(obj)} no serializable")
