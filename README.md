# AI Business Automation Designer

Design, validate, and run complex business automations across your SaaS stack with an AI crew that drafts flows from plain-English goals, maps data between apps, simulates costs/failures, and deploys safe, versioned pipelines with observability and human-in-the-loop approvals.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm 8+
- Python 3.9+
- Docker and Docker Compose
- PostgreSQL, Redis, NATS, MinIO (via Docker)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ai-business-automation-designer
```

### 2. Start Infrastructure

```bash
# Start all required services (PostgreSQL, Redis, NATS, MinIO)
npm run docker:up
```

### 3. Install Dependencies

```bash
# Install all dependencies for the monorepo
npm run install:all
```

### 4. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Add your API keys for OpenAI, Anthropic, etc.
```

### 5. Start Development

```bash
# Start all services in development mode
npm run dev
```

This will start:
- **Frontend**: Next.js 14 app on http://localhost:3000
- **Gateway**: NestJS API on http://localhost:3001
- **Orchestrator**: FastAPI service on http://localhost:8000
- **Workers**: Celery workers for task processing

## 🏗️ Architecture

### Monorepo Structure

```
ai-business-automation-designer/
├── apps/
│   ├── frontend/          # Next.js 14 (App Router) - Flow Builder UI
│   ├── gateway/           # NestJS - API Gateway & Auth
│   ├── orchestrator/      # FastAPI - CrewAI Design Intelligence
│   └── workers/           # Python - Execution Plane
├── packages/
│   └── sdk/              # Shared TypeScript SDK
├── docker-compose.dev.yml # Local development infrastructure
└── .cursor/              # Project documentation & rules
```

### Technology Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Radix UI
- **API Gateway**: NestJS, TypeORM, Passport, Swagger
- **Orchestrator**: FastAPI, CrewAI, Pydantic, SQLAlchemy
- **Workers**: Celery, Redis, NATS, PostgreSQL
- **Infrastructure**: Docker, PostgreSQL, Redis, NATS, MinIO
- **Observability**: OpenTelemetry, Prometheus, Grafana

## 🎯 Core Features

### 1. Goal-to-Flow Design
- Natural language → BPMN-lite workflow drafts
- AI crew (Process Architect, Integrator, Data Mapper, etc.)
- Multi-step refinement with human feedback

### 2. Visual Flow Builder
- Drag-and-drop workflow editor
- Real-time collaboration
- Version control and branching

### 3. Data Mapping & Validation
- Schema inference for connectors
- Field mapping with transforms
- Type guards and validators (Zod)

### 4. Simulation & Testing
- Dry-run simulator with synthetic data
- Cost and latency forecasting
- Failure injection and testing

### 5. Execution & Reliability
- State machine execution engine
- Retries with exponential backoff
- Dead letter queues and compensation
- Rate-limit aware throttling

## 📚 API Documentation

### Gateway API (NestJS)
- **Base URL**: http://localhost:3001/v1
- **Docs**: http://localhost:3001/api
- **Auth**: JWT Bearer tokens

### Orchestrator API (FastAPI)
- **Base URL**: http://localhost:8000/v1
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/v1/health

## 🔧 Development

### Available Scripts

```bash
# Development
npm run dev                    # Start all services
npm run dev:frontend          # Frontend only
npm run dev:gateway           # Gateway only
npm run dev:orchestrator      # Orchestrator only
npm run dev:workers           # Workers only

# Building
npm run build                 # Build all packages
npm run build:sdk            # Build SDK only
npm run build:frontend       # Build frontend only
npm run build:gateway        # Build gateway only

# Testing
npm run test                 # Run all tests
npm run test:frontend        # Frontend tests
npm run test:gateway         # Gateway tests
npm run test:sdk             # SDK tests

# Linting
npm run lint                 # Lint all packages
npm run lint:frontend        # Frontend linting
npm run lint:gateway         # Gateway linting
npm run lint:sdk             # SDK linting

# Docker
npm run docker:up            # Start infrastructure
npm run docker:down          # Stop infrastructure
npm run docker:logs          # View logs

# Utilities
npm run clean                # Clean all builds
npm run install:all          # Install all dependencies
```

### Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_automation

# Redis
REDIS_URL=redis://localhost:6379

# NATS
NATS_URL=nats://localhost:4222

# AI Services
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Object Storage
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
```

## 🧪 Testing

### Frontend Testing
```bash
cd apps/frontend
npm run test
```

### Gateway Testing
```bash
cd apps/gateway
npm run test
npm run test:e2e
```

### Orchestrator Testing
```bash
cd apps/orchestrator
pytest
```

## 🚀 Deployment

### Production Build
```bash
npm run build
```

### Docker Deployment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

## 📖 Documentation

- [Architecture Overview](.cursor/ARCH.md)
- [Development Plan](.cursor/PLAN.md)
- [Product Brief](.cursor/PRODUCT_BRIEF)
- [Development Rules](.cursor/RULES-INDEX.md)

## 🤝 Contributing

1. Follow the development rules in `.cursor/rules/`
2. Use conventional commits
3. Ensure all tests pass
4. Update documentation as needed

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For questions and support:
- Check the documentation in `.cursor/`
- Review the architecture in `ARCH.md`
- Open an issue for bugs or feature requests
