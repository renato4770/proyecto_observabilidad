import logging
import random
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# ── OpenTelemetry setup ───────────────────────────────────────────────────────
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

OTEL_ENDPOINT = "http://otel-collector:4317"

# Traces
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True))
)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)

# Metrics
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=OTEL_ENDPOINT, insecure=True),
    export_interval_millis=5000,
)
meter_provider = MeterProvider(metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

request_counter = meter.create_counter("api.requests.total", description="Total requests")
error_counter   = meter.create_counter("api.errors.total",   description="Total errors")
order_counter   = meter.create_counter("api.orders.created", description="Orders created")

# Logs — stdlib solamente (sin OTel logs para evitar el bug)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("api")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Demo Observabilidad")

# Middleware manual para trazas por request (reemplaza FastAPIInstrumentor)
@app.middleware("http")
async def tracing_middleware(request: Request, call_next):
    with tracer.start_as_current_span(f"{request.method} {request.url.path}") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.path", request.url.path)
        response = await call_next(request)
        span.set_attribute("http.status_code", response.status_code)
        return response

# ── Modelos ───────────────────────────────────────────────────────────────────
class Order(BaseModel):
    product: str
    qty: int
    user_id: int = 1

USERS = {
    1: {"id": 1, "name": "Ana García",   "email": "ana@demo.com",   "plan": "premium"},
    2: {"id": 2, "name": "Carlos López", "email": "carlos@demo.com","plan": "basic"},
}
orders_db = []

# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    request_counter.add(1, {"endpoint": "/health"})
    logger.info("Health check OK")
    return {"status": "ok", "service": "demo-observabilidad"}


@app.get("/users/{user_id}")
def get_user(user_id: int):
    request_counter.add(1, {"endpoint": "/users"})
    with tracer.start_as_current_span("get-user-from-db") as span:
        span.set_attribute("user.id", user_id)
        time.sleep(random.uniform(0.05, 0.15))
        user = USERS.get(user_id)
        if not user:
            error_counter.add(1, {"endpoint": "/users", "reason": "not_found"})
            logger.warning(f"User {user_id} not found")
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        logger.info(f"User {user_id} retrieved: {user['name']}")
        return user


@app.post("/orders", status_code=201)
def create_order(order: Order):
    request_counter.add(1, {"endpoint": "/orders"})
    with tracer.start_as_current_span("create-order") as span:
        span.set_attribute("order.product", order.product)
        span.set_attribute("order.qty", order.qty)
        time.sleep(random.uniform(0.1, 0.25))
        new_order = {
            "id": len(orders_db) + 1,
            "product": order.product,
            "qty": order.qty,
            "user_id": order.user_id,
            "status": "created",
        }
        orders_db.append(new_order)
        order_counter.add(1, {"product": order.product})
        logger.info(f"Order created: #{new_order['id']} — {order.product} x{order.qty}")
        return new_order


@app.get("/fail")
def force_error():
    request_counter.add(1, {"endpoint": "/fail"})
    error_counter.add(1, {"endpoint": "/fail", "reason": "intentional"})
    with tracer.start_as_current_span("intentional-error") as span:
        span.set_attribute("error", True)
        logger.error("Intentional error triggered for demo")
        raise HTTPException(status_code=500, detail="Error intencional para el demo")