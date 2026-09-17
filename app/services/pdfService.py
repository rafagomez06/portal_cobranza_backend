# app/services/pdfService.py
import os
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from flask import send_file
import pandas as pd

class PDFService:
    
    @staticmethod
    def generar_pdf_checadas(datos, titulo="Reporte de Checadas App",rango_fecha_inicio='1900-01-01',
                            rango_fecha_fin='1900-01-01',id_empresa='0',pagina='1'):
        """
        Genera un PDF con la información de checadas.
        """
        try:
            # Crear buffer para el PDF
            buffer = io.BytesIO()
            
            # Crear el documento
            doc = SimpleDocTemplate(
                buffer,
                pagesize=landscape(letter),
                rightMargin=76,
                leftMargin=76,
                topMargin=36,
                bottomMargin=10,
            )
            
            # Estilos
            styles = getSampleStyleSheet()

            # Estilo para el contenido de las celdas
            celda_estilo = ParagraphStyle(
                'CeldaTabla',
                fontSize=8,
                leading=10,
                alignment=TA_CENTER,
                wordWrap='CJK',
            )

            celda_header_estilo = ParagraphStyle(
                'CeldaHeader',
                parent=celda_estilo,
                textColor=colors.white,
                fontName='Helvetica-Bold',
            )
            # Estilo para título principal
            titulo_estilo = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#030303'),
                alignment=TA_CENTER,
                spaceAfter=30
            )
            
            # Estilo para subtítulos
            subtitulo_estilo = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor("#030303"),
                spaceAfter=12
            )
            
            # Estilo para texto normal
            texto_estilo = styles['Normal']

            texto_estilo_negritas = ParagraphStyle(
                name='TextoNegritas',
                parent=styles['Normal'],
                fontName='Helvetica-Bold'
            )

            # Elementos del PDF
            elementos = []
            
            # Título
            elementos.append(Paragraph(titulo, titulo_estilo))
            elementos.append(Spacer(1, 12))
            
            # Fecha de creacion
            fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            elementos.append(Paragraph(f"Reporte Generado: {fecha_actual}", texto_estilo_negritas))
            elementos.append(Paragraph(f"Total de empleados: {len(datos)}", texto_estilo_negritas))

            # Si trae filtro de empresa colocar nombre de empresa elegida.
            if not id_empresa:
                nombre_empresa_mostrar = "TODAS"
            else:
                nombre_empresa_mostrar = "N/A"
                if datos and len(datos) > 0:
                    primer_registro = datos[0]
                    nombre_empresa_mostrar = primer_registro.get('nombre_empresa')
            elementos.append(Paragraph(f"Empresa: {nombre_empresa_mostrar}", texto_estilo_negritas))


            # Si existe rangos de fechas seleccionado, agg subtitulo a reporte
            if rango_fecha_fin or rango_fecha_fin:
                elementos.append(Paragraph(f"Datos del : {rango_fecha_inicio} al {rango_fecha_fin}", texto_estilo_negritas))
            elementos.append(Spacer(1, 20))


            # Estilo Para cada usuario
            for usuario in datos:
                # Nombre del usuario
                elementos.append(Paragraph(
                    f"N° Empleado: {usuario.get('id_usuario', 'N/A')} - {usuario.get('nombre_completo', 'Sin nombre')} ",
                    subtitulo_estilo
                ))
                elementos.append(Spacer(1, 8))
                
                # Obtener detalles de checadas
                detalle = usuario.get('detalle_checadas', [])
                
                if detalle:
                    # Crear tabla de checadas
                    data_tabla = [[
                        Paragraph('Tipo', celda_header_estilo),
                        Paragraph('Día', celda_header_estilo),
                        Paragraph('Fecha Registro', celda_header_estilo),
                        Paragraph('Fec. Captura Dispositivo', celda_header_estilo),
                        Paragraph('Ubicación', celda_header_estilo),
                    ]]
                    for checada in detalle:
                        data_tabla.append([
                            Paragraph(str(checada.get('tipo_checada_descripcion', '')), celda_estilo),
                            Paragraph(str(checada.get('dia_semana', '')), celda_estilo),
                            Paragraph(str(checada.get('fecha_registro', '')), celda_estilo),
                            Paragraph(str(checada.get('fecha_captura_dispositivo', '')), celda_estilo),
                            Paragraph(str(checada.get('direccion_ubicacion', 'N/A')), celda_estilo),
                        ])

                    tabla = Table(data_tabla, colWidths=[75, 35, 95, 115, 290], repeatRows=1)
                    tabla.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2779b1")),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    
                    elementos.append(tabla)
                    elementos.append(Spacer(1, 8))
                    
                    # Resumen de checadas del día
                    dias = len(set([c.get('fecha_registro', '')[:10] for c in detalle]))
                    elementos.append(Paragraph(
                        f"Total de checadas: {len(detalle)} - Días: {dias}",
                        texto_estilo_negritas
                    ))
                else:
                    elementos.append(Paragraph(
                        "Sin checadas registradas",
                        texto_estilo_negritas
                    ))
                
                elementos.append(Spacer(1, 20))
                elementos.append(Paragraph("*" * 150, texto_estilo_negritas))
                elementos.append(Spacer(1, 20))
            
            # Construir PDF
            doc.build(elementos)
            
            # Obtener el valor del buffer
            pdf_value = buffer.getvalue()
            buffer.close()
            # Retornamos PDF
            return pdf_value
            
        except Exception as e:
            print(f"Error generando PDF: {e}")
            raise e

    @staticmethod
    def generar_pdf_simple(datos, titulo="Reporte de Checadas App"):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            # Configurar fuente
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, titulo)
            
            # Fecha
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 70, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            
            y = height - 100
            
            # Para cada usuario
            for usuario in datos:
                if y < 100:
                    c.showPage()
                    y = height - 50
                
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y, f"Usuario: {usuario.get('nombre_completo', '')}")
                y -= 20
                
                c.setFont("Helvetica", 9)
                detalle = usuario.get('detalle_checadas', [])
                for checada in detalle:
                    if y < 50:
                        c.showPage()
                        y = height - 50
                        c.setFont("Helvetica", 9)
                    
                    texto = f"  - {checada.get('tipo_checada_descripcion', '')} | {checada.get('fecha_registro', '')}"
                    c.drawString(60, y, texto)
                    y -= 15
                
                y -= 10
            
            c.save()
            pdf_value = buffer.getvalue()
            buffer.close()
            return pdf_value
            
        except Exception as e:
            print(f"Error generando PDF simple: {e}")
            raise e