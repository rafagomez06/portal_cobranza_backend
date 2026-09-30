from decimal import Decimal, InvalidOperation

# Funciones de ayuda

def formato_moneda(valor_decimal):
    # Asegurar que el valor tiene dos decimales
    valor_decimal = valor_decimal.quantize(Decimal('0.00'))

    # Formatear el número a string con el símbolo de dólar
    #return f"${valor_decimal:,.2f}"
    return valor_decimal

## Aplica strip a strings; regresa el valor tal cual si no es string o es None.
def _trim(valor):
    if valor is None:
        return None
    if isinstance(valor, str):
        return valor.strip()
    return valor