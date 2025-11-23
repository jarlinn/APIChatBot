"""
PDF generation service using ReportLab
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle

logger = logging.getLogger(__name__)


class PDFService:
    """
    Service for generating PDF reports with charts and data using ReportLab
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        # Create custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
        )
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.gray,
            spaceAfter=20,
            alignment=1,
        )
        self.section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=15,
            textColor=colors.blue,
        )
        self.normal_style = self.styles['Normal']

    def generate_frequent_questions_report(
        self,
        questions_data: List[Dict[str, Any]],
        bar_chart_bytes: bytes,
        pie_chart_bytes: bytes,
        category_chart_bytes: Optional[bytes] = None,
        report_period_days: int = 7
    ) -> bytes:
        """
        Generate a complete PDF report for frequent questions

        Args:
            questions_data: List of question data
            bar_chart_bytes: Bar chart image bytes
            pie_chart_bytes: Pie chart image bytes
            category_chart_bytes: Category distribution chart bytes (optional)
            report_period_days: Number of days the report covers

        Returns:
            PDF as bytes
        """
        try:
            # Create PDF buffer
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []

            # Generate report date
            report_date = datetime.now().strftime("%d/%m/%Y %H:%M")
            period_start = (datetime.now() - timedelta(days=report_period_days)).strftime("%d/%m/%Y")
            period_end = datetime.now().strftime("%d/%m/%Y")

            # Title and header
            story.append(Paragraph("🤖 ChatBot UFPS", self.title_style))
            story.append(Paragraph("Sistema de Reportes Automáticos", self.subtitle_style))
            story.append(Spacer(1, 20))

            # Report info
            story.append(Paragraph(f"Reporte de Preguntas Frecuentes", self.section_title_style))
            story.append(Paragraph(f"Período: {period_start} - {period_end} ({report_period_days} días)", self.normal_style))
            story.append(Paragraph(f"Generado el: {report_date}", self.normal_style))
            story.append(Spacer(1, 20))

            # Summary cards
            total_questions = len(questions_data)
            total_occurrences = sum(int(q['count']) for q in questions_data) if questions_data else 0

            summary_data = [
                ["📈 Total de Preguntas Analizadas", str(total_occurrences)],
                ["🎯 Preguntas Únicas", str(total_questions)],
                ["📊 Período de Análisis", f"{report_period_days} días"]
            ]

            summary_table = Table(summary_data, colWidths=[4*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 30))

            # Charts section
            if questions_data:
                # Bar chart
                story.append(Paragraph("📊 Top 5 Preguntas Más Frecuentes", self.section_title_style))
                bar_img = Image(BytesIO(bar_chart_bytes), width=6*inch, height=4*inch)
                story.append(bar_img)
                story.append(Spacer(1, 20))

                # Pie chart
                story.append(Paragraph("🥧 Distribución de Preguntas Frecuentes", self.section_title_style))
                pie_img = Image(BytesIO(pie_chart_bytes), width=6*inch, height=4*inch)
                story.append(pie_img)
                story.append(Spacer(1, 20))

                # Category chart (if available)
                if category_chart_bytes:
                    story.append(Paragraph("📊 Distribución por Categoría", self.section_title_style))
                    cat_img = Image(BytesIO(category_chart_bytes), width=6*inch, height=4*inch)
                    story.append(cat_img)
                    story.append(Spacer(1, 30))

                # Detailed table
                story.append(Paragraph("📋 Detalle de Preguntas Frecuentes", self.section_title_style))

                # Table header
                table_data = [["#", "Pregunta", "Ocurrencias", "Modalidad", "Submodalidad", "Categoría"]]

                # Table rows
                for i, question in enumerate(questions_data, 1):
                    # Truncate long questions for table
                    question_text = question['question_text']
                    if len(question_text) > 50:
                        question_text = question_text[:47] + "..."

                    row = [
                        str(i),
                        question_text,
                        str(int(question['count'])),
                        question.get('modality', 'N/A'),
                        question.get('submodality', 'N/A'),
                        question.get('category', 'N/A')
                    ]
                    table_data.append(row)

                # Create table
                col_widths = [0.5*inch, 2.5*inch, 1*inch, 1*inch, 1*inch, 1*inch]
                questions_table = Table(table_data, colWidths=col_widths)

                # Style the table
                table_style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ])
                questions_table.setStyle(table_style)
                story.append(questions_table)

            # Footer
            story.append(Spacer(1, 30))
            story.append(Paragraph("Reporte generado automáticamente por el sistema ChatBot UFPS", self.normal_style))
            story.append(Paragraph("Para más información, contacte al administrador del sistema", self.normal_style))

            # Build PDF
            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()

            logger.info(f"Generated PDF report with {len(questions_data)} questions using ReportLab")
            return pdf_bytes

        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise



# Global instance
pdf_service = PDFService()