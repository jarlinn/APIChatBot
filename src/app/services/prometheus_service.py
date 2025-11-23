"""
Prometheus service for querying metrics
"""
import logging
from typing import List, Dict, Any, Optional
from prometheus_api_client import PrometheusConnect
from prometheus_api_client.utils import parse_datetime

from src.app.config import settings

logger = logging.getLogger(__name__)


class PrometheusService:
    """
    Service for querying Prometheus metrics
    """

    def __init__(self):
        self.prometheus_url = settings.prometheus_url
        logger.info(f"Initializing Prometheus service with URL: {self.prometheus_url}")
        self.prom = PrometheusConnect(url=self.prometheus_url, disable_ssl=True)

    async def get_frequent_questions_report(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get top 5 frequent questions using the exact query from Grafana

        Args:
            days: Number of days to look back (not used in this implementation)

        Returns:
            List of dicts with question_id, question_text, and count
        """
        try:
            # Use the exact query that works in Grafana
            query = 'topk(5, sum(frequent_questions_total) by (question_id, question_text))'
            logger.info(f"Executing query: {query}")

            # Execute the query
            result = self.prom.custom_query(query=query)
            logger.info(f"Query returned {len(result)} results")
            logger.info(f"Raw result: {result}")

            questions_data = []
            for item in result:
                logger.debug(f"Processing result item: {item}")
                logger.debug(f"Item keys: {item.keys()}")

                # Check the structure of the response
                if 'metric' in item and 'value' in item:
                    metric = item['metric']
                    # The value format is [timestamp, value_string]
                    value = float(item['value'][1])

                    questions_data.append({
                        'question_id': metric.get('question_id', 'N/A'),
                        'question_text': metric.get('question_text', 'N/A'),
                        'count': value
                    })
                else:
                    logger.error(f"Unexpected item structure: {item}")

            logger.info(f"Retrieved {len(questions_data)} frequent questions from Prometheus")
            return questions_data

        except Exception as e:
            logger.error(f"Error querying Prometheus for frequent questions: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return []

    async def get_frequent_questions_detailed(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get detailed frequent questions data including modality, submodality, category

        Args:
            days: Number of days to look back

        Returns:
            List of dicts with detailed question information
        """
        try:
            # Use the same approach as the working query but get all data with labels
            query = 'sum(frequent_questions_total) by (question_id, question_text, modality, submodality, category)'
            logger.info(f"Executing detailed query: {query}")

            # Execute the query
            result = self.prom.custom_query(query=query)
            logger.info(f"Detailed query returned {len(result)} results")

            questions_data = []
            for item in result:
                logger.debug(f"Processing detailed result item: {item}")
                logger.debug(f"Item keys: {item.keys()}")

                if 'metric' in item and 'value' in item:
                    metric = item['metric']
                    value = float(item['value'][1])  # value is [timestamp, value]

                    questions_data.append({
                        'question_id': metric.get('question_id', 'N/A'),
                        'question_text': metric.get('question_text', 'N/A'),
                        'modality': metric.get('modality', 'N/A'),
                        'submodality': metric.get('submodality', 'N/A'),
                        'category': metric.get('category', 'N/A'),
                        'count': value
                    })
                else:
                    logger.error(f"Unexpected detailed item structure: {item}")

            # Sort by count descending
            sorted_questions = sorted(
                questions_data,
                key=lambda x: x['count'],
                reverse=True
            )

            logger.info(f"Retrieved {len(sorted_questions)} detailed frequent questions from Prometheus")
            return sorted_questions

        except Exception as e:
            logger.error(f"Error querying Prometheus for detailed frequent questions: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return []


# Global instance
prometheus_service = PrometheusService()