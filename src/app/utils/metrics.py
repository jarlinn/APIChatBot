"""Metric Module"""
from prometheus_client import Counter, Histogram

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'status_code'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP Request Latency', ['method', 'endpoint'])
FREQUENT_QUESTIONS_COUNT = Counter('frequent_questions_total', 'Total Frequent Questions Found', ['question_id', 'question_text', 'modality', 'submodality', 'category', 'similarity_score'])