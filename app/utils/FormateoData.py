from decimal import Decimal, InvalidOperation

# Funciones de ayuda

def formato_moneda(valor_decimal):
    # Asegurar que el valor tiene dos decimales
    valor_decimal = valor_decimal.quantize(Decimal('0.00'))

    # Formatear el número a string con el símbolo de dólar
    #return f"${valor_decimal:,.2f}"
    return valor_decimal