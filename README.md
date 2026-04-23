# TaskForge DevOps

A Python-based project structured for containerized execution and background task processing.

## Tech Stack
- Python
- Docker
- Redis
- Celery

## Project Structure
- `environment/` - application code and runtime configuration
- `solution/` - solution scripts
- `tests/` - test files
- `task.toml` - task configuration

## Features
- Dockerized setup
- Background task processing
- Environment-based configuration
- Included test support

## How to Run
```bash
docker-compose up --build
