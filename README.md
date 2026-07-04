# Demo de Observabilidad — Arquitectura y Backend Moderno

Proyecto práctico para el curso **Desarrollo de Aplicaciones de Última Generación**.

Implementación de un stack de observabilidad completo sobre una API REST instrumentada con OpenTelemetry. El sistema recolecta y visualiza en tiempo real las tres señales fundamentales de observabilidad: **trazas distribuidas**, **métricas** y **logs**, todo corriendo localmente con Docker Compose.

---

## Integrantes

| Nombre | Rol |
|--------|-----|
| Renato Emilio Arismendi Ruidias
| Oliver Alexander Rios Zeledón
| Melanie Jazmín Bain Cárdenas

---

## Arquitectura

Cliente Web (localhost:8081)
│
▼
API FastAPI (localhost:8000)
│  trazas + métricas + logs
▼
OTel Collector
├── trazas  ──► Jaeger     (localhost:16686)
├── métricas ──► Prometheus (localhost:9090)
└── logs    ──► Loki       (localhost:3100)
│
▼
Grafana (localhost:3000)
Dashboard unificado en tiempo real

---

## Tecnologías utilizadas

- **FastAPI** — API REST en Python
- **OpenTelemetry SDK** — instrumentación de trazas, métricas y logs
- **OTel Collector** — recolector y enrutador de señales
- **Jaeger** — visualización de trazas distribuidas
- **Prometheus** — almacenamiento y consulta de métricas
- **Loki** — almacenamiento de logs estructurados
- **Grafana** — dashboard unificado de observabilidad
- **Docker Compose** — orquestación de todos los servicios

---

## Requisitos previos

- Docker Engine 24+ con Docker Compose v2
- Los siguientes puertos deben estar libres: 8000, 8081, 3000, 3100, 4317, 4318, 8889, 9090, 16686

---

## Instalación y ejecución

### 1. Clonar el repositorio

git clone https://github.com/renato4770/proyecto_observabilidad.git
cd proyecto_observabilidad

### 2. Levantar el stack completo

docker compose up --build

### 3. Verificar que todo esté corriendo

docker compose ps

### 4. Generar tráfico de prueba

for i in {1..10}; do
  curl -s http://localhost:8000/health > /dev/null
  curl -s http://localhost:8000/users/1 > /dev/null
  curl -s http://localhost:8000/users/2 > /dev/null
  curl -s -X POST http://localhost:8000/orders \
    -H "Content-Type: application/json" \
    -d '{"product": "laptop", "qty": 1, "user_id": 1}' > /dev/null
  curl -s http://localhost:8000/fail > /dev/null
done

### 5. Abrir las interfaces

- Cliente web:  http://localhost:8081
- Grafana:      http://localhost:3000
- Jaeger UI:    http://localhost:16686
- Prometheus:   http://localhost:9090
- API Docs:     http://localhost:8000/docs

---

## Endpoints de la API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /health | Health check del servicio |
| GET | /users/{id} | Obtener usuario (id: 1 o 2) |
| POST | /orders | Crear una orden |
| GET | /fail | Fuerza error 500 para el demo |

---

## Detener el stack

docker compose down

docker compose down -v