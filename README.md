# Coditude Application

This repository contains the Coditude assessment application. It is owned by
the application team and contains the Next.js frontend, FastAPI backend, local
PostgreSQL environment, tests, Dockerfiles, and application delivery workflows.

AWS infrastructure is maintained separately in the
[`coditude-infrastructure`](https://github.com/ali509/coditude-infrastructure)
repository.

## Local Architecture

```text
Browser -> Next.js frontend -> FastAPI backend -> PostgreSQL
             edge network       edge + data       data network
```

- Only the frontend and backend development ports are published to the host.
- PostgreSQL is isolated on an internal Docker network.
- The backend uses a bounded PostgreSQL connection pool.
- `/health` checks whether the backend process is alive.
- `/ready` checks whether the backend can query PostgreSQL.
- Service startup is controlled by health checks rather than fixed delays.

## Prerequisites

- Docker Desktop with Docker Compose
- Python 3.12 for local backend development
- Node.js 22 for local frontend development

## Start The Complete Stack

Create the local environment file once:

```bash
cp .env.example .env
```

Replace the example password in `.env`, then start the services:

```bash
docker compose config --quiet
docker compose up --build --detach
docker compose ps
```

Open `http://127.0.0.1:3000`. The page should report `postgresql` as its data
source.

## Verification

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/api/v1/message
curl http://127.0.0.1:3000/api/health
```

Inspect logs and service health:

```bash
docker compose ps
docker compose logs backend
docker compose logs frontend
docker compose logs database
```

Stop the application without deleting database data:

```bash
docker compose down
```

Delete the local database volume as well:

```bash
docker compose down --volumes
```

## Local Application Tests

```bash
cd apps/backend
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest -v
deactivate

cd ../frontend
npm run lint
npm run build
```

## Configuration

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | Environment name returned by the backend |
| `DATABASE_URL` | PostgreSQL connection string injected into the backend |
| `DB_HOST` | RDS endpoint used when `DATABASE_URL` is not supplied |
| `DB_PORT` | PostgreSQL port, defaulting to `5432` |
| `DB_NAME` | PostgreSQL database name |
| `DB_SECRET_ARN` | RDS-managed secret read by the EC2 backend at startup |
| `DB_USERNAME` | Database username used for local development |
| `DB_PASSWORD` | Database password used for local development |
| `DB_POOL_MAX_SIZE` | Maximum backend database connections per container |
| `BACKEND_URL` | Internal URL used by the Next.js server |

The committed `.env.example` contains placeholders only. `.env` is ignored by
Git and is intended only for local development. Cloud deployments will use AWS
Secrets Manager or Parameter Store rather than environment files.

## Continuous Integration

The credential-free GitHub Actions workflow at
`.github/workflows/validate.yml` runs on pushes to `main`, pull requests, and
manual dispatches. It performs:

- Python dependency installation and backend tests
- Next.js dependency installation, linting, and production build
- Docker Compose validation
- Independent frontend and backend container builds

The validation workflow has read-only repository permissions and does not
authenticate to AWS or deploy an application.

## Infrastructure Contract

The application repository does not provision AWS resources. Deployment
workflows consume environment-specific values created by the infrastructure
repository:

| Value | Purpose |
| --- | --- |
| `AWS_REGION` | Region containing the target platform |
| `AWS_ROLE_ARN` | GitHub OIDC deployment role |
| `ECS_CLUSTER_NAME` | ECS cluster receiving the release |
| `FRONTEND_SERVICE_NAME` | Frontend ECS service |
| `BACKEND_SERVICE_NAME` | Backend ECS service |
| `FRONTEND_ECR_REPOSITORY` | Frontend ECR repository URI |
| `BACKEND_ECR_REPOSITORY` | Backend ECR repository URI |

These values belong in GitHub Environments named `dev`, `staging`, and `prod`.
They must not be hard-coded in application source or stored as long-lived AWS
access keys.

Application deployment will use an immutable commit SHA as the image tag. The
same tested image is promoted through environments; staging and production
deployments require environment approval. Infrastructure changes are reviewed
and deployed independently from the infrastructure repository.

## EC2 CodeDeploy Bundles

The non-containerized deployment path produces separate CodeDeploy revisions
for the frontend and backend:

```text
deploy/ec2/
  frontend/
    appspec.yml
    scripts/
    systemd/
  backend/
    appspec.yml
    scripts/
    systemd/
```

Build both revision archives locally:

```bash
make codedeploy-bundles
```

The generated files are ignored by Git:

```text
build/codedeploy/coditude-frontend.zip
build/codedeploy/coditude-backend.zip
```

Each deployment follows this lifecycle:

1. `deploy.sh` stops the old service and prepares the application directory.
2. CodeDeploy copies the new application files.
3. The same `deploy.sh` installs dependencies and starts the service.
4. `validate.sh` checks the health endpoint and fails the deployment if needed.

The frontend requires `/etc/coditude-frontend.env` containing `BACKEND_URL`.
The backend requires `/etc/coditude-backend.env` containing its environment and
database settings. These files are infrastructure/runtime responsibilities and
are never included in a deployment ZIP.
