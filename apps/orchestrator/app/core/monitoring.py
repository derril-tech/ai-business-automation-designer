"""
Monitoring and observability module for the orchestrator.
Provides Prometheus metrics, structured logging, and health checks.
"""

import time
import structlog
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse
from contextlib import contextmanager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
# HTTP request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Workflow execution metrics
workflow_executions_total = Counter(
    'workflow_executions_total',
    'Total number of workflow executions',
    ['status']
)

workflow_execution_duration_seconds = Histogram(
    'workflow_execution_duration_seconds',
    'Workflow execution duration in seconds',
    ['workflow_type']
)

# Step execution metrics
step_executions_total = Counter(
    'step_executions_total',
    'Total number of step executions',
    ['step_type', 'status']
)

step_execution_duration_seconds = Histogram(
    'step_execution_duration_seconds',
    'Step execution duration in seconds',
    ['step_type']
)

# AI agent metrics
ai_agent_calls_total = Counter(
    'ai_agent_calls_total',
    'Total number of AI agent calls',
    ['agent_type', 'status']
)

ai_agent_response_time_seconds = Histogram(
    'ai_agent_response_time_seconds',
    'AI agent response time in seconds',
    ['agent_type']
)

# System metrics
active_workflows = Gauge(
    'active_workflows',
    'Number of currently active workflows'
)

active_simulations = Gauge(
    'active_simulations',
    'Number of currently active simulations'
)

database_connections = Gauge(
    'database_connections',
    'Number of active database connections'
)

redis_connections = Gauge(
    'redis_connections',
    'Number of active Redis connections'
)

class MonitoringMiddleware:
    """FastAPI middleware for monitoring HTTP requests."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        request = Request(scope, receive)
        
        # Extract method and endpoint
        method = request.method
        endpoint = request.url.path
        
        # Process request
        try:
            await self.app(scope, receive, send)
            
            # Record metrics
            duration = time.time() - start_time
            http_requests_total.labels(method=method, endpoint=endpoint, status=200).inc()
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
            
            # Log request
            logger.info(
                "HTTP request completed",
                method=method,
                endpoint=endpoint,
                duration=duration,
                status=200
            )
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            http_requests_total.labels(method=method, endpoint=endpoint, status=500).inc()
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
            
            # Log error
            logger.error(
                "HTTP request failed",
                method=method,
                endpoint=endpoint,
                duration=duration,
                error=str(e),
                status=500
            )
            raise

@contextmanager
def monitor_workflow_execution(workflow_type: str):
    """Context manager for monitoring workflow execution."""
    start_time = time.time()
    active_workflows.inc()
    
    try:
        yield
        # Record successful execution
        duration = time.time() - start_time
        workflow_executions_total.labels(status="success").inc()
        workflow_execution_duration_seconds.labels(workflow_type=workflow_type).observe(duration)
        
        logger.info(
            "Workflow execution completed",
            workflow_type=workflow_type,
            duration=duration,
            status="success"
        )
        
    except Exception as e:
        # Record failed execution
        duration = time.time() - start_time
        workflow_executions_total.labels(status="failed").inc()
        workflow_execution_duration_seconds.labels(workflow_type=workflow_type).observe(duration)
        
        logger.error(
            "Workflow execution failed",
            workflow_type=workflow_type,
            duration=duration,
            error=str(e),
            status="failed"
        )
        raise
    
    finally:
        active_workflows.dec()

@contextmanager
def monitor_step_execution(step_type: str):
    """Context manager for monitoring step execution."""
    start_time = time.time()
    
    try:
        yield
        # Record successful execution
        duration = time.time() - start_time
        step_executions_total.labels(step_type=step_type, status="success").inc()
        step_execution_duration_seconds.labels(step_type=step_type).observe(duration)
        
        logger.debug(
            "Step execution completed",
            step_type=step_type,
            duration=duration,
            status="success"
        )
        
    except Exception as e:
        # Record failed execution
        duration = time.time() - start_time
        step_executions_total.labels(step_type=step_type, status="failed").inc()
        step_execution_duration_seconds.labels(step_type=step_type).observe(duration)
        
        logger.error(
            "Step execution failed",
            step_type=step_type,
            duration=duration,
            error=str(e),
            status="failed"
        )
        raise

@contextmanager
def monitor_ai_agent_call(agent_type: str):
    """Context manager for monitoring AI agent calls."""
    start_time = time.time()
    
    try:
        yield
        # Record successful call
        duration = time.time() - start_time
        ai_agent_calls_total.labels(agent_type=agent_type, status="success").inc()
        ai_agent_response_time_seconds.labels(agent_type=agent_type).observe(duration)
        
        logger.info(
            "AI agent call completed",
            agent_type=agent_type,
            duration=duration,
            status="success"
        )
        
    except Exception as e:
        # Record failed call
        duration = time.time() - start_time
        ai_agent_calls_total.labels(agent_type=agent_type, status="failed").inc()
        ai_agent_response_time_seconds.labels(agent_type=agent_type).observe(duration)
        
        logger.error(
            "AI agent call failed",
            agent_type=agent_type,
            duration=duration,
            error=str(e),
            status="failed"
        )
        raise

def get_metrics():
    """Get Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

def update_system_metrics(db_connection_count: int, redis_connection_count: int):
    """Update system-level metrics."""
    database_connections.set(db_connection_count)
    redis_connections.set(redis_connection_count)

def log_structured_event(event_type: str, **kwargs):
    """Log a structured event."""
    logger.info(f"{event_type} event", event_type=event_type, **kwargs)

def log_error(error: Exception, context: dict = None):
    """Log an error with context."""
    logger.error(
        "Error occurred",
        error=str(error),
        error_type=type(error).__name__,
        context=context or {}
    )
