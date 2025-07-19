⚠️ **DISCLAIMER**: This project is a proof of concept and not ready for production use. It's provided as a starting point for those looking to build similar integration platforms.

# Network Intelligence - Production

A Flask-based network intelligence and security monitoring application for production environment.

## Features

- Real-time network monitoring and analysis
- Security event detection and alerting
- RESTful API for data ingestion and retrieval
- Web dashboard for visualization
- Redis caching for performance
- PostgreSQL for data persistence

## Environment

This is the **production environment** for the Network Intelligence application.

## Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export FLASK_APP=app.py
export FLASK_ENV=production
export SECRET_KEY=your-secret-key
export DATABASE_URL=your-postgresql-url
export REDIS_URL=your-redis-url
```

3. Run the application:
```bash
flask run
```

### Heroku Deployment

The app is configured for Heroku deployment with:
- `Procfile` for process management
- `runtime.txt` for Python version specification
- `requirements.txt` for dependencies

## API Endpoints

- `GET /` - Dashboard
- `GET /api/health` - Health check
- `GET /api/events` - List security events
- `POST /api/events` - Create new event
- `GET /api/analytics` - Network analytics

## Environment Variables

- `SECRET_KEY` - Flask secret key
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `FLASK_ENV` - Environment (production)

## Pipeline

This app is part of the network-intelligence pipeline:
- Development: `network-intelligence-dev`
- Staging: `network-intelligence-stage`
- **Production: `network-intelligence-prod`** ← You are here

## Deployment

This production environment receives promotions from the staging environment and serves as the live production system.

## Security

This is a production environment. Ensure all security best practices are followed:
- Use strong, unique secrets
- Enable SSL/TLS
- Monitor logs and metrics
- Regular security updates
- Backup strategies 