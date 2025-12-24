# Shortener

A simple URL Shortener service built with FastAPI.  
This project includes automated tests, linting, and Docker workflows, all
integrated with GitHub Actions.

---

## Features

- Shorten URLs and redirect to the original link
- Health check endpoint (useful for Kubernetes readiness and liveness
  probes)
- Automated tests using `pytest`
- Code formatting with `black` and linting with `pylint`
- CI/CD workflows for branch and production Docker builds via GitHub
  Actions
- GitOps-ready Docker image tags for automated deployment updates

---

## Requirements

- Python 3.13
- Docker & Docker Compose (for local development)

---

## Setup

1. Clone the repository:

```bash
git clone https://github.com/soft-titus/shortener.git
cd shortener
```

2. Install dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. Install git pre-commit hooks:

```bash
cp hooks/pre-commit .git/hooks/
```

4. Run the application locally with Docker:

```bash
docker compose build
docker compose up -d
```

The API will be available at `http://localhost:8080`.

---

## Running Tests

Run the test suite with:

```bash
python -m pytest -v
```

Check code formatting and linting:

```bash
python -m black --check .
python -m pylint /*.py
```

---

## GitHub Actions

- `ci.yaml` : Runs linting and tests on all branches and PRs
- `build-and-publish-branch-docker-image.yaml` : Builds Docker images for
  branches
- `build-and-publish-production-docker-image.yaml` : Builds production
  images on `main`

---

### Branch Builds

Branch-specific Docker images are built with timestamped tags.  

Example: `1.0.0-dev-1762431`

---

### Production Builds

Merges to `main` trigger a production Docker image build.  
Versioning follows semantic versioning based on commit messages:

- `BREAKING CHANGE:` : major version bump
- `feat:` : minor version bump
- `fix:` : patch version bump

Example: `1.0.0`
