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

    async def get_frequent_questions_detailed(self, days: int = 15) -> List[Dict[str, Any]]:
        """
        Get detailed frequent questions data including modality, submodality, category
        using range queries to get all historical data

        Args:
            days: Number of days to look back

        Returns:
            List of dicts with detailed question information
        """
        try:
            # Use range query to get all historical data over the specified period
            query = 'frequent_questions_total'  # Query simple como en el frontend
            logger.info(f"Executing range query: {query} for last {days} days")

            # Get data for the last N days
            end_time = parse_datetime("now")
            start_time = parse_datetime(f"{days}d")

            # Query range to get historical data
            result = self.prom.get_metric_range_data(
                metric_name='frequent_questions_total',
                label_config={},  # Get all labels
                start_time=start_time,
                end_time=end_time,
            )

            logger.info(f"Range query returned {len(result)} time series")

            # Aggregate data by metric labels
            aggregated_data = {}
            for metric_data in result:
                metric = metric_data['metric']
                question_id = metric.get('question_id')
                question_text = metric.get('question_text')

                if not question_id or not question_text:
                    continue

                key = f"{question_id}:{question_text}"

                if key not in aggregated_data:
                    aggregated_data[key] = {
                        'question_id': question_id,
                        'question_text': question_text,
                        'modality': metric.get('modality', 'N/A'),
                        'submodality': metric.get('submodality', 'N/A'),
                        'category': metric.get('category', 'N/A'),
                        'count': 0
                    }

                # Sum the last value from each time series for the same question
                if metric_data['values']:
                    try:
                        # Get the last (most recent) value
                        last_value = metric_data['values'][-1]
                        aggregated_data[key]['count'] += float(last_value[1])
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing last value from time series: {e}")
                        continue

            # Convert to list and sort by count descending
            questions_data = list(aggregated_data.values())
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