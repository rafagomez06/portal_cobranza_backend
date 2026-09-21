from decimal import Decimal, InvalidOperation


def formato_moneda(valor_decimal):
    # Asegúrate de que el valor tiene dos decimales
    valor_decimal = valor_decimal.quantize(Decimal('0.00'))

    # Formatear el número a string con el símbolo de dólar
    return f"${valor_decimal:,.2f}"