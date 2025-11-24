"""
Graph generation service using matplotlib and seaborn
"""
import logging
import io
import textwrap
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

            # Create figure with better size for PDF and long texts
            plt.figure(figsize=(16, max(10, len(df) * 1.2)))  # More width and dynamic height

            # Create horizontal bar chart (better for long question texts)
            bars = plt.barh(
                y=range(len(df)),
                width=df['count'],
                color=sns.color_palette("husl", len(df))
            )

            # Wrap long question texts into multiple lines for better readability
            wrapped_labels = []
            for question in df['question_text']:
                if len(question) > 40:
                    # Wrap text to 40 characters per line, max 3 lines
                    wrapped = textwrap.wrap(question[:120], width=40)  # Limit total chars to 120
                    if len(wrapped) > 3:
                        wrapped = wrapped[:3]
                        wrapped[-1] += "..."
                    wrapped_labels.append("\n".join(wrapped))
                else:
                    wrapped_labels.append(question)

            # Add wrapped question texts as y-axis labels
            plt.yticks(
                range(len(df)),
                wrapped_labels,
                fontsize=9,
                ha='right'
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

            # Create figure with better size for pie chart and legend
            plt.figure(figsize=(14, 10))

            # Create pie chart without labels (to avoid text overlap with long questions)
            # Only show percentages inside the slices
            wedges, autotexts = plt.pie(
                df['count'],
                labels=[''] * len(df),  # Empty strings for each slice to avoid overlap
                autopct='%1.1f%%',
                startangle=90,
                colors=sns.color_palette("husl", len(df)),
                pctdistance=0.85  # Position percentages closer to center
            )

            # Improve percentage text styling
            for autotext in autotexts:
                autotext.set_fontsize(11)
                autotext.set_fontweight('bold')
                autotext.set_color('white')  # White text on colored background

            # Add legend with truncated question texts
            legend_labels = []
            for question in df['question_text']:
                if len(question) > 25:
                    # Truncate and add ellipsis
                    truncated = question[:22] + "..."
                    legend_labels.append(truncated)
                else:
                    legend_labels.append(question)

            plt.legend(
                wedges,
                legend_labels,
                title="Preguntas",
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1),
                fontsize=9
            )

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

            # Create compact figure for PDF
            plt.figure(figsize=(6, 4))  # More compact: smaller overall

            # Create bar chart with thinner bars
            bars = plt.bar(
                range(len(category_counts)),
                category_counts['count'],
                color=sns.color_palette("husl", len(category_counts)),
                width=0.6  # Thinner bars for more compact look
            )

            # Add category labels with text wrapping for long category names
            category_labels = []
            for category in category_counts['category']:
                if len(str(category)) > 15:
                    # Wrap long category names
                    wrapped = textwrap.wrap(str(category), width=15)
                    category_labels.append("\n".join(wrapped))
                else:
                    category_labels.append(str(category))

            plt.xticks(
                range(len(category_counts)),
                category_labels,
                rotation=45,
                ha='right',
                fontsize=9
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
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            image_bytes = buf.getvalue()

            plt.close()
            logger.info(f"Generated category distribution chart with {len(category_counts)} categories")
            return image_bytes

        except Exception as e:
            logger.error(f"Error generating category chart: {str(e)}")
            return self._generate_empty_chart()

    def generate_modality_distribution_chart(
        self,
        questions_data: List[Dict[str, Any]],
        title: str = "Distribución por Modalidad"
    ) -> bytes:
        """
        Generate a chart showing distribution by modality

        Args:
            questions_data: List of dicts with modality and count
            title: Chart title

        Returns:
            PNG image as bytes
        """
        try:
            if not questions_data:
                logger.warning("No questions data provided for modality chart generation")
                return self._generate_empty_chart()

            # Group by modality
            df = pd.DataFrame(questions_data)
            modality_counts = df.groupby('modality')['count'].sum().reset_index()
            modality_counts = modality_counts.sort_values('count', ascending=False)

            # Create compact figure for PDF
            plt.figure(figsize=(6, 4))  # More compact: smaller overall

            # Create bar chart with thinner bars
            bars = plt.bar(
                range(len(modality_counts)),
                modality_counts['count'],
                color=sns.color_palette("husl", len(modality_counts)),
                width=0.6  # Thinner bars for more compact look
            )

            # Add modality labels with text wrapping for long modality names
            modality_labels = []
            for modality in modality_counts['modality']:
                if len(str(modality)) > 15:
                    # Wrap long modality names
                    wrapped = textwrap.wrap(str(modality), width=15)
                    modality_labels.append("\n".join(wrapped))
                else:
                    modality_labels.append(str(modality))

            plt.xticks(
                range(len(modality_counts)),
                modality_labels,
                rotation=45,
                ha='right',
                fontsize=9
            )

            # Add value labels on bars
            for bar, count in zip(bars, modality_counts['count']):
                plt.text(
                    bar.get_x() + bar.get_width()/2,
                    bar.get_height() + max(modality_counts['count']) * 0.01,
                    f'{int(count)}',
                    ha='center',
                    va='bottom',
                    fontsize=10,
                    fontweight='bold'
                )

            plt.xlabel('Modalidad', fontsize=12, fontweight='bold')
            plt.ylabel('Número Total de Preguntas', fontsize=12, fontweight='bold')
            plt.title(title, fontsize=14, fontweight='bold', pad=20)

            # Adjust layout
            plt.tight_layout()

            # Save to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            image_bytes = buf.getvalue()

            plt.close()
            logger.info(f"Generated modality distribution chart with {len(modality_counts)} modalities")
            return image_bytes

        except Exception as e:
            logger.error(f"Error generating modality chart: {str(e)}")
            return self._generate_empty_chart()

    def generate_submodality_distribution_chart(
        self,
        questions_data: List[Dict[str, Any]],
        title: str = "Distribución por Submodalidad"
    ) -> bytes:
        """
        Generate a chart showing distribution by submodality

        Args:
            questions_data: List of dicts with submodality and count
            title: Chart title

        Returns:
            PNG image as bytes
        """
        try:
            if not questions_data:
                logger.warning("No questions data provided for submodality chart generation")
                return self._generate_empty_chart()

            # Group by submodality
            df = pd.DataFrame(questions_data)
            submodality_counts = df.groupby('submodality')['count'].sum().reset_index()
            submodality_counts = submodality_counts.sort_values('count', ascending=False)

            # Create compact figure for PDF
            plt.figure(figsize=(6, 4))  # More compact: smaller overall

            # Create bar chart with thinner bars
            bars = plt.bar(
                range(len(submodality_counts)),
                submodality_counts['count'],
                color=sns.color_palette("husl", len(submodality_counts)),
                width=0.6  # Thinner bars for more compact look
            )

            # Add submodality labels with text wrapping for long submodality names
            submodality_labels = []
            for submodality in submodality_counts['submodality']:
                if len(str(submodality)) > 15:
                    # Wrap long submodality names
                    wrapped = textwrap.wrap(str(submodality), width=15)
                    submodality_labels.append("\n".join(wrapped))
                else:
                    submodality_labels.append(str(submodality))

            plt.xticks(
                range(len(submodality_counts)),
                submodality_labels,
                rotation=45,
                ha='right',
                fontsize=9
            )

            # Add value labels on bars
            for bar, count in zip(bars, submodality_counts['count']):
                plt.text(
                    bar.get_x() + bar.get_width()/2,
                    bar.get_height() + max(submodality_counts['count']) * 0.01,
                    f'{int(count)}',
                    ha='center',
                    va='bottom',
                    fontsize=10,
                    fontweight='bold'
                )

            plt.xlabel('Submodalidad', fontsize=12, fontweight='bold')
            plt.ylabel('Número Total de Preguntas', fontsize=12, fontweight='bold')
            plt.title(title, fontsize=14, fontweight='bold', pad=20)

            # Adjust layout
            plt.tight_layout()

            # Save to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            image_bytes = buf.getvalue()

            plt.close()
            logger.info(f"Generated submodality distribution chart with {len(submodality_counts)} submodalities")
            return image_bytes

        except Exception as e:
            logger.error(f"Error generating submodality chart: {str(e)}")
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