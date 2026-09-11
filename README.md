# Videoflix Backend

REST backend for a small video streaming platform. Users register with e-mail
and password, activate their account via mail, log in with JWT cookies and
stream uploaded videos as HLS in 480p, 720p and 1080p.

## Stack

- Python 3.12, Django, Django REST Framework, Simple JWT (HttpOnly cookies)
- PostgreSQL, Redis + django-rq (background jobs), ffmpeg (HLS transcoding)
- Docker Compose (services `db`, `redis`, `web`)

## Prerequisites

- Docker Desktop with Docker Compose
- An SMTP account for activation and password reset mails (e.g. a Mailtrap sandbox)

## Setup

1. Copy the environment template and fill in your values:

   ```bash
   cp .env.example .env
   ```

2. Generate a secret key and put it into `.env` as `SECRET_KEY`:

   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. Build and start everything:

   ```bash
   docker compose up --build
   ```

The entrypoint waits for PostgreSQL, runs `collectstatic`, `makemigrations` and
`migrate`, creates the superuser from `.env`, starts an rq worker and then
gunicorn on port 8000.

## URLs

| URL | Purpose |
| --- | --- |
| `http://localhost:8000/api/` | REST API (see below) |
| `http://localhost:8000/admin/` | Django admin (superuser from `.env`) |
| `http://localhost:8000/django-rq/` | rq dashboard: queues, failed jobs |

## Environment variables

All configuration comes from `.env` (see `.env.example`). `DB_HOST=db` and
`REDIS_HOST=redis` are Compose service names and only resolve inside the
Compose network.

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Django signing key; generate a fresh one per environment |
| `DEBUG` | `True` for local development only |
| `ALLOWED_HOSTS` | Comma separated host names Django accepts |
| `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS` | Frontend origins including scheme and port |
| `DJANGO_SUPERUSER_USERNAME`, `_EMAIL`, `_PASSWORD` | Superuser created on first start |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_LOCATION` | Redis for rq and cache |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`, `DEFAULT_FROM_EMAIL` | SMTP for activation and reset mails |
| `FRONTEND_URL` | Base URL of the frontend, used in mail links |
| `BACKEND_URL` | Base URL of this API, used for the activation link |

## API

All endpoints live under `/api/`. Authenticated endpoints expect the JWT
`access_token` cookie set by the login endpoint.

### Auth

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `register/` | no | Create an inactive user, send activation mail |
| GET | `activate/<uidb64>/<token>/` | no | Activate the account from the mail link |
| POST | `login/` | no | Log in with e-mail and password, sets JWT cookies |
| POST | `logout/` | no | Blacklist the refresh token, clear cookies |
| POST | `token/refresh/` | no | Issue a new access cookie from the refresh cookie |
| POST | `password_reset/` | no | Send a password reset mail (always 200) |
| POST | `password_confirm/<uidb64>/<token>/` | no | Set a new password from the reset link |

### Content

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `video/` | yes | List all videos |
| GET | `video/<movie_id>/<resolution>/index.m3u8` | yes | HLS playlist for `480p`, `720p` or `1080p` |
| GET | `video/<movie_id>/<resolution>/<segment>/` | yes | One `.ts` segment referenced by the playlist |

## Background processing

Uploading a video (currently via the admin) fires a `post_save` signal that
enqueues three rq jobs. Each job runs ffmpeg and writes an HLS playlist plus
segments to `media/videos/<id>/<resolution>/`. Progress and failures are visible
in the rq dashboard and in `docker compose logs web`.

Mails are sent through rq jobs as well, so requests do not wait for SMTP.

## Development

```bash
docker compose exec web python manage.py test            # run all tests
docker compose exec web python manage.py test auth_app   # one app
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell
docker compose logs -f web                               # web + rq worker output
```

The local `venv/` only serves the editor and IntelliSense; the application
itself always runs in Docker.

## Project layout

```
core/            settings, root urls, wsgi
auth_app/        registration, activation, login, password reset, mail tasks
content_app/     video model, signals, ffmpeg tasks, streaming endpoints
<app>/api/       serializers, views and urls of the REST API
<app>/tests/     tests
backend.Dockerfile, backend.entrypoint.sh, docker-compose.yml
```
