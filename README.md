# Coditude DevOps Assessment

This repository contains a small deployable application used to demonstrate
containerization, orchestration, infrastructure as code, CI/CD, security, and
operational readiness.

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
| `DB_USERNAME` | Database username injected from Secrets Manager |
| `DB_PASSWORD` | Database password injected from Secrets Manager |
| `DB_POOL_MAX_SIZE` | Maximum backend database connections per container |
| `BACKEND_URL` | Internal URL used by the Next.js server |

The committed `.env.example` contains placeholders only. `.env` is ignored by
Git and is intended only for local development. Cloud deployments will use AWS
Secrets Manager or Parameter Store rather than environment files.

## CloudFormation Architecture

[`infrastructure/root.yaml`](infrastructure/root.yaml) is the deployment entry
point. It passes nested-stack outputs directly into dependent templates:

1. `network.yaml` creates the VPC, subnets, and routing.
2. `security.yaml` creates the workload security groups.
3. `database.yaml` creates the encrypted PostgreSQL RDS database.
4. `container-foundation.yaml` creates the shared ECS, ECR, logging,
   service discovery, IAM, and private endpoint resources.
5. `container-application.yaml` creates the ALB, task definitions,
   Fargate services, private backend discovery, and service autoscaling.

The container platform is split because ECR repositories must exist before the
first immutable application images can be pushed. The application stack can be
enabled after those image tags exist.

The root template defaults to network and security only. The following
parameters explicitly enable billable layers:

| Parameter | Default | Effect |
| --- | --- | --- |
| `DeployDatabase` | `false` | Creates RDS and its managed secret |
| `DeployContainerFoundation` | `false` | Creates ECS, ECR, logs and discovery |
| `EnablePrivateEndpoints` | `false` | Creates billable interface endpoints |
| `DeployContainerApplication` | `false` | Creates ALB and Fargate services |

Validate the templates locally:

```bash
make infra-lint
make root-lint
make database-validate
make container-foundation-validate
make container-application-validate
```

Before deploying the root template, package the local nested template paths
into S3 URLs:

```bash
aws cloudformation package \
  --template-file infrastructure/root.yaml \
  --s3-bucket YOUR_ARTIFACT_BUCKET \
  --output-template-file infrastructure/packaged-root.yaml
```

`packaged-root.yaml` is generated deployment output and should not be manually
edited.

The database template uses RDS-managed credentials. RDS generates the master
password and stores it in Secrets Manager; no password is committed to the
repository or passed as a CloudFormation parameter.

For cost-controlled testing, `dev` and `staging` database resources use
`DeletionPolicy: Delete` and do not preserve a final snapshot when their stack
is deleted. The `prod` database resource uses `DeletionPolicy: Snapshot` and
deletion protection to preserve production data.

The container foundation supports a `single` interface endpoint subnet for
lower-cost non-production testing and an `all` strategy for production
resilience. Interface endpoints incur hourly and data-processing charges when
deployed.

The container application supports HTTP for temporary development testing and
HTTPS when an ACM certificate ARN is supplied. Production validation requires
an ACM certificate. The backend receives database credentials through ECS
Secrets Manager injection and constructs its connection string at runtime.
