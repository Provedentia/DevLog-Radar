# Devlog Radar =�

A comprehensive developer productivity tracker that integrates with GitHub to monitor coding activity, contributions, and provide insights into development patterns.

## <� Features

- **GitHub Integration**: Automatically sync commits, contributions, and repository activity
- **Activity Analytics**: Generate detailed reports and summaries of coding activity
- **Background Processing**: Async data synchronization using Celery + Redis
- **RESTful API**: Complete FastAPI backend with automatic documentation
- **Multi-user Support**: Track multiple developers and their contributions
- **Docker Ready**: Fully containerized with Docker Compose
- **Production Ready**: Proper logging, error handling, and configuration management

## <� Architecture

```
   app/
      api/              # FastAPI route handlers
      core/             # Configuration, database, Redis setup
      models/           # SQLAlchemy models
      schemas/          # Pydantic models for request/response
      services/         # GitHub API integration logic
      workers/          # Celery tasks and scheduling
      main.py           # FastAPI entry point
   scripts/              # CLI utilities
   docker-compose.yml    # Multi-service orchestration
   Dockerfile           # Application container
```

## =� Quick Start

### Prerequisites

- Docker and Docker Compose
- GitHub Personal Access Token
- Python 3.11+ (for local development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd devlog-radar

# Copy environment template
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file with your settings:

```env
# Required: Get from https://github.com/settings/tokens
GITHUB_TOKEN=your_github_personal_access_token_here

# Optional: Change for production
SECRET_KEY=your-secret-key-change-in-production
```

### 3. Start Services

```bash
# Start all services (API, database, Redis, workers)
docker-compose up -d

# View logs
docker-compose logs -f api
```

### 4. Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs
```

## =� API Endpoints

### GitHub Sync

- `POST /sync/github` - Queue GitHub data sync
- `GET /sync/github/status/{task_id}` - Check sync status
- `GET /activity/summary/{username}` - Get activity summary

### User Management

- `POST /users/` - Create user
- `GET /users/` - List all users
- `GET /users/{user_id}` - Get user by ID
- `GET /users/username/{username}` - Get user by username
- `PUT /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Delete user

### System

- `GET /` - API information
- `GET /health` - Health check

## =' Manual Sync

Use the CLI script for one-time syncs:

```bash
# Sync GitHub data for a user
python scripts/manual_sync.py your-github-username

# Sync last 7 days only
python scripts/manual_sync.py your-github-username --days 7

# Sync specific platform
python scripts/manual_sync.py your-github-username --platform github
```

## =� Development Setup

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start database and Redis
docker-compose up postgres redis -d

# Run API locally
uvicorn app.main:app --reload

# Run Celery worker
celery -A app.workers.tasks worker --loglevel=info

# Run Celery scheduler
celery -A app.workers.tasks beat --loglevel=info
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=app
```

## = Background Jobs

The system uses Celery for background processing:

- **Daily GitHub Sync**: Runs at 2 AM UTC daily
- **Daily LeetCode Sync**: Runs at 3 AM UTC daily (stub implementation)
- **Manual Triggers**: Via API endpoints or CLI scripts

### Monitoring Celery

```bash
# View active workers
celery -A app.workers.tasks status

# Monitor tasks
celery -A app.workers.tasks monitor

# View scheduled tasks
celery -A app.workers.tasks inspect scheduled
```

## =� Database Schema

### Users Table
- `id`: Primary key
- `github_username`: GitHub username (unique)
- `email`: User email
- `full_name`: Display name
- `avatar_url`: Profile picture URL
- `github_id`: GitHub user ID
- `is_active`: Account status
- `created_at`, `updated_at`: Timestamps

### Contributions Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `repo_name`: Repository full name
- `repo_url`: Repository URL
- `commit_sha`: Unique commit identifier
- `commit_message`: Commit description
- `commit_url`: Commit URL
- `commit_date`: When commit was made
- `additions`, `deletions`, `files_changed`: Code metrics
- `created_at`: When record was created

## < Production Deployment

### Environment Variables

```env
# Production settings
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://redis-host:6379/0
SECRET_KEY=secure-random-key
GITHUB_TOKEN=github-pat-token
```

### Security Considerations

- Use strong, unique `SECRET_KEY`
- Store `GITHUB_TOKEN` securely
- Use environment-specific database credentials
- Enable HTTPS in production
- Configure proper CORS origins
- Use Redis AUTH in production

### Scaling

- Horizontal scaling: Run multiple API containers
- Worker scaling: Add more Celery workers
- Database: Use connection pooling and read replicas
- Caching: Add Redis caching for frequently accessed data

## = Monitoring

### Health Checks

- API: `GET /health`
- Database: Connection pooling metrics
- Redis: Memory usage and connection count
- Celery: Worker status and task queue length

### Logging

Logs are structured and include:
- Request/response logging
- Background task execution
- Error tracking with stack traces
- Performance metrics

## > Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## =� License

This project is licensed under the MIT License - see the LICENSE file for details.

## <� Troubleshooting

### Common Issues

1. **GitHub API Rate Limits**
   - Use authenticated requests (provide `GITHUB_TOKEN`)
   - Implement exponential backoff for retries

2. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check connection string format
   - Ensure database exists

3. **Celery Worker Not Processing**
   - Verify Redis is accessible
   - Check worker logs for errors
   - Restart worker if needed

4. **Docker Issues**
   - Run `docker-compose down && docker-compose up --build`
   - Check logs: `docker-compose logs service-name`
   - Verify ports are not in use

### Getting Help

- Check the [API documentation](http://localhost:8000/docs)
- Review application logs
- Open an issue on GitHub

---

Built with d using FastAPI, PostgreSQL, Redis, and Celery