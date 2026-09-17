from app.main import bcrypt    
# Conversion de password a pass encriptada con Hash
def set_password(password: str):
        resultado = bcrypt.generate_password_hash(password).decode("utf-8")
        return resultado

# Check de la pass hasheada
def check_password(password_hashSQL:str,password:str) -> bool:
    resultado = bcrypt.check_password_hash(password_hashSQL,password)
    return resultado