"""
Graph generation service using matplotlib and seaborn
"""
import logging
import io
from typing import Any, List, Dict
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

logger = logging.getLogger(__name__)


class GraphService:
    """
    Service for generating graphs from metrics data
    """

    def __init__(self):
        # Set matplotlib backend to non-interactive for server environments
        plt.switch_backend('Agg')

        # Set seaborn style
        sns.set_style("whitegrid")
        sns.set_palette("husl")

    def generate_frequent_questions_bar_chart(
        self,
        questions_data: List[Dict[str, Any]],
        title: str = "Top 5 Preguntas Frecuentes"
    ) -> bytes:
        """
        Generate a bar chart for frequent questions

        Args:
            questions_data: List of dicts with question_text and count
            title: Chart title

        Returns:
            PNG image as bytes
        """
        try:
            if not questions_data:
                logger.warning("No questions data provided for graph generation")
                return self._generate_empty_chart()

            # Prepare data
            df = pd.DataFrame(questions_data)

            # Create figure with better size for PDF
            plt.figure(figsize=(12, 8))

            # Create horizontal bar chart (better for long question texts)
            bars = plt.barh(
                y=range(len(df)),
                width=df['count'],
                color=sns.color_palette("husl", len(df))
            )

            # Add question texts as y-axis labels
            plt.yticks(
                range(len(df)),
                [q[:50] + "..." if len(q) > 50 else q for q in df['question_text']],
                fontsize=10
            )

            # Add value labels on bars
            for i, (bar, count) in enumerate(zip(bars, df['count'])):
                plt.text(
                    bar.get_width() + max(df['count']) * 0.01,
                    bar.get_y() + bar.get_height()/2,
                    f'{int(count)}',
                    ha='left',
                    va='center',
                    fontsize=10,
                    fontweight='bold'
                )

            plt.xlabel('Número de Ocurrencias', fontsize=12, fontweight='bold')
            plt.ylabel('Pregunta', fontsize=12, fontweight='bold')
            plt.title(title, fontsize=14, fontweight='bold', pad=20)

            # Adjust layout
            plt.tight_layout()

            # Save to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            image_bytes = buf.getvalue()

            plt.close()
            logger.info(f"Generated bar chart with {len(questions_data)} questions")
            return image_bytes

        except Exception as e:
            logger.error(f"Error generating bar chart: {str(e)}")
            return self._generate_empty_chart()

    def generate_frequent_questions_pie_chart(
        self,
        questions_data: List[Dict[str, Any]],
        title: str = "Distribución de Preguntas Frecuentes"
    ) -> bytes:
        """
        Generate a pie chart for frequent questions distribution

        Args:
            questions_data: List of dicts with question_text and count
            title: Chart title

        Returns:
            PNG image as bytes
        """
        try:
            if not questions_data:
                logger.warning("No questions data provided for pie chart generation")
                return self._generate_empty_chart()

            # Prepare data
            df = pd.DataFrame(questions_data)

            # Create figure
            plt.figure(figsize=(10, 8))

            # Create pie chart
            wedges, texts, autotexts = plt.pie(
                df['count'],
                labels=[q[:30] + "..." if len(q) > 30 else q for q in df['question_text']],
                autopct='%1.1f%%',
                startangle=90,
                colors=sns.color_palette("husl", len(df))
            )

            # Improve text styling
            for text in texts:
                text.set_fontsize(9)
            for autotext in autotexts:
                autotext.set_fontsize(9)
                autotext.set_fontweight('bold')

            plt.title(title, fontsize=14, fontweight='bold', pad=20)
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle

            # Adjust layout
            plt.tight_layout()

            # Save to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            image_bytes = buf.getvalue()

            plt.close()
            logger.info(f"Generated pie chart with {len(questions_data)} questions")
            return image_bytes

        except Exception as e:
            logger.error(f"Error generating pie chart: {str(e)}")
            return self._generate_empty_chart()

    def generate_category_distribution_chart(
        self,
        questions_data: List[Dict[str, Any]],
        title: str = "Distribución por Categoría"
    ) -> bytes:
        """
        Generate a chart showing distribution by category

        Args:
            questions_data: List of dicts with category and count
            title: Chart title

        Returns:
            PNG image as bytes
        """
        try:
            if not questions_data:
                logger.warning("No questions data provided for category chart generation")
                return self._generate_empty_chart()

            # Group by category
            df = pd.DataFrame(questions_data)
            category_counts = df.groupby('category')['count'].sum().reset_index()
            category_counts = category_counts.sort_values('count', ascending=False)

            # Create figure
            plt.figure(figsize=(12, 6))

            # Create bar chart
            bars = plt.bar(
                range(len(category_counts)),
                category_counts['count'],
                color=sns.color_palette("husl", len(category_counts))
            )

            # Add category labels
            plt.xticks(
                range(len(category_counts)),
                category_counts['category'],
                rotation=45,
                ha='right',
                fontsize=10
            )

            # Add value labels on bars
            for bar, count in zip(bars, category_counts['count']):
                plt.text(
                    bar.get_x() + bar.get_width()/2,
                    bar.get_height() + max(category_counts['count']) * 0.01,
                    f'{int(count)}',
                    ha='center',
                    va='bottom',
                    fontsize=10,
                    fontweight='bold'
                )

            plt.xlabel('Categoría', fontsize=12, fontweight='bold')
            plt.ylabel('Número Total de Preguntas', fontsize=12, fontweight='bold')
            plt.title(title, fontsize=14, fontweight='bold', pad=20)

            # Adjust layout
            plt.tight_layout()

            # Save to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            image_bytes = buf.getvalue()

            plt.close()
            logger.info(f"Generated category distribution chart with {len(category_counts)} categories")
            return image_bytes

        except Exception as e:
            logger.error(f"Error generating category chart: {str(e)}")
            return self._generate_empty_chart()

    def _generate_empty_chart(self) -> bytes:
        """
        Generate an empty chart placeholder

        Returns:
            PNG image as bytes
        """
        try:
            plt.figure(figsize=(8, 6))
            plt.text(0.5, 0.5, 'No hay datos disponibles',
                    horizontalalignment='center',
                    verticalalignment='center',
                    fontsize=14,
                    transform=plt.gca().transAxes)
            plt.title('Gráfico No Disponible', fontsize=16, fontweight='bold')
            plt.axis('off')

            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            image_bytes = buf.getvalue()

            plt.close()
            return image_bytes

        except Exception as e:
            logger.error(f"Error generating empty chart: {str(e)}")
            # Return minimal valid PNG bytes if everything fails
            return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'


# Global instance
graph_service = GraphService()