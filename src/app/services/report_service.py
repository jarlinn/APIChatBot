"""
Report generation service that orchestrates data fetching, graph creation, and PDF generation
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from src.app.services.prometheus_service import prometheus_service
from src.app.services.graph_service import graph_service
from src.app.services.pdf_service import pdf_service

logger = logging.getLogger(__name__)


class ReportService:
    """
    Service for generating complete reports with data, charts, and PDF
    """

    async def generate_frequent_questions_report(
        self,
        days: int = 7,
        include_category_chart: bool = True,
        include_modality_chart: bool = True,
        include_submodality_chart: bool = True
    ) -> bytes:
        """
        Generate a complete frequent questions report

        Args:
            days: Number of days to look back for data
            include_category_chart: Whether to include category distribution chart
            include_modality_chart: Whether to include modality distribution chart
            include_submodality_chart: Whether to include submodality distribution chart

        Returns:
            PDF report as bytes
        """
        try:
            logger.info(f"Starting report generation for last {days} days")

            # 1. Fetch data from Prometheus
            questions_data = await prometheus_service.get_frequent_questions_detailed(days=days)

            if not questions_data:
                logger.warning("No questions data found, generating empty report")
                questions_data = []

            # 2. Generate charts
            bar_chart_bytes = graph_service.generate_frequent_questions_bar_chart(
                questions_data=questions_data,
                title=f"Top {len(questions_data)} Preguntas Más Frecuentes"
            )

            pie_chart_bytes = graph_service.generate_frequent_questions_pie_chart(
                questions_data=questions_data,
                title=f"Distribución de Preguntas Frecuentes (Últimos {days} días)"
            )

            category_chart_bytes = None
            if include_category_chart and questions_data:
                category_chart_bytes = graph_service.generate_category_distribution_chart(
                    questions_data=questions_data,
                    title=f"Distribución por Categoría (Últimos {days} días)"
                )

            modality_chart_bytes = None
            if include_modality_chart and questions_data:
                modality_chart_bytes = graph_service.generate_modality_distribution_chart(
                    questions_data=questions_data,
                    title=f"Distribución por Modalidad (Últimos {days} días)"
                )

            submodality_chart_bytes = None
            if include_submodality_chart and questions_data:
                submodality_chart_bytes = graph_service.generate_submodality_distribution_chart(
                    questions_data=questions_data,
                    title=f"Distribución por Submodalidad (Últimos {days} días)"
                )

            # 3. Generate PDF
            pdf_bytes = pdf_service.generate_frequent_questions_report(
                questions_data=questions_data,
                bar_chart_bytes=bar_chart_bytes,
                pie_chart_bytes=pie_chart_bytes,
                category_chart_bytes=category_chart_bytes,
                modality_chart_bytes=modality_chart_bytes,
                submodality_chart_bytes=submodality_chart_bytes,
                report_period_days=days
            )

            logger.info(f"Successfully generated report with {len(questions_data)} questions, PDF size: {len(pdf_bytes)} bytes")
            return pdf_bytes

        except Exception as e:
            logger.error(f"Error generating frequent questions report: {str(e)}")
            raise

    async def get_report_metadata(self, days: int = 7) -> Dict[str, Any]:
        """
        Get metadata about the report without generating the full PDF

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with report metadata
        """
        try:
            questions_data = await prometheus_service.get_frequent_questions_detailed(days=days)

            total_questions = len(questions_data)
            total_occurrences = sum(int(q['count']) for q in questions_data) if questions_data else 0

            # Get unique categories
            categories = list(set(q.get('category', 'N/A') for q in questions_data)) if questions_data else []

            metadata = {
                "report_type": "frequent_questions",
                "period_days": days,
                "generated_at": datetime.now().isoformat(),
                "total_questions": total_questions,
                "total_occurrences": total_occurrences,
                "categories_count": len(categories),
                "categories": categories,
                "data_available": total_questions > 0
            }

            logger.info(f"Retrieved report metadata: {total_questions} questions, {total_occurrences} total occurrences")
            return metadata

        except Exception as e:
            logger.error(f"Error getting report metadata: {str(e)}")
            return {
                "report_type": "frequent_questions",
                "period_days": days,
                "generated_at": datetime.now().isoformat(),
                "error": str(e),
                "data_available": False
            }


# Global instance
report_service = ReportService()