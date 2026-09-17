# Portal Cobranza - Backend API

# Sistema Integral de Cobranza - SIC

API REST desarrollada con **Python + Flask + SQL**.

## Stack

- Python 3.11+
- Flask 3.x
- Flask-SQLAlchemy + Flask-Migrate
- Flask-JWT-Extended (autenticación)
- Flask-Bcrypt (hash de contraseñas)
- Flask-CORS
- Pillow (validación y optimización de imágenes)

## Setup inicial

### 1. Clonar y crear entorno virtual

```bash
python -m venv venv
```

### 1.1.- Ejecutar comando segun el caso

```bash
source venv/bin/activate # Mac/Linux

venv\Scripts\activate  # Windows
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.template .env
# Editar .env con tus credenciales de PostgreSQL
```

### 4. Levantar el servidor

```bash
flask --app run.py run --host=0.0.0.0 --port=5000
# o
python run.py
# o
flask run
```

### 5 . salir de (venv) usar comando:

```bash
 deactivate
```

### Opcionales:

- Generar token random para encriptado de jwt:

```bash
import secrets
print(secrets.token_hex(32)) # Genera una cadena segura de 64 caracteres hex
```

### La API estará disponible en:

`http://localhost:5000`
