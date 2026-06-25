# TraceGreens — Technical Architecture & Deployment Walkthrough

Welcome to the **TraceGreens** architectural study guide. This document provides a comprehensive breakdown of the application design, codebase mechanics, deployment workflows, security models, and compliance considerations.

---

## 1. Project Overview

**TraceGreens** is a data-driven web application built for chef-grade microgreens batch management and customer-facing traceability. 
* **Customer Facing Portal**: Public users can scan QR codes on microgreens packaging to instantly view the crop’s origin, seeding date, lighting, watering history, harvest metrics, and batch photos.
* **Admin Dashboard**: Secure control panel for farm operators to manage seed inventory, log batch lifecycle events, process customer orders, and manage sales.

---

## 2. Technical Stack & Directory Layout

The application is built using a modern, lightweight Python web stack:

* **Framework**: **FastAPI** — High-performance, asynchronous web framework.
* **Database**: **PostgreSQL** — Relational database with **SQLAlchemy** for Object-Relational Mapping (ORM).
* **UI/Frontend**: **Vanilla HTML/CSS** served via **Jinja2 Templates** (server-side rendering), avoiding heavy JS framework overhead.
* **Production Build**: **Docker** & **Nixpacks** containerization.

### Directory Structure

```text
TraceGreens/
├── app/
│   ├── main.py              # Application initialization and routing entrypoint
│   ├── database.py          # Database connection, engine, and session management
│   ├── config.py            # Pydantic Settings for environment variables
│   ├── models/              # SQLAlchemy Database Models (Batch, BatchEvent, Customer, Order)
│   ├── routers/             # Endpoint Controllers (Admin dashboard, Public trace routes, API endpoints)
│   ├── services/            # Business Logic (Metrics computations)
│   ├── static/              # Favicons, icons, and Apple touch assets
│   └── templates/           # Jinja2 HTML layouts and views
├── Dockerfile               # Docker container specification
├── docker-compose.yml       # Local development services orchestration
├── nixpacks.toml            # Cloud deployment configuration (Railway/Nixpacks)
├── requirements.txt         # Python package dependencies list
└── generate_favicons.py     # Pillow-based brand asset generation utility
```

---

## 3. How the Code Works

### Entrypoint & Lifecycle Management (`app/main.py`)
FastAPI uses a `lifespan` handler to manage application startup and shutdown tasks. In `main.py`, the database tables are created automatically if they don't exist:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup if not present
    Base.metadata.create_all(bind=engine)
    yield
```

Routers are registered modularly to separate public-facing routes from administrative screens:
* `app.include_router(admin.router)`: Manages dashboard views, inventory forms, and order states.
* `app.include_router(trace.router)`: Exposes homepage, redirect rules, and public batch details.

### Database Session lifecycle (`app/database.py`)
SQLAlchemy manages sessions using a generator function `get_db`. This function is injected into route parameters via FastAPI's `Depends` system, ensuring that connection sessions are cleanly opened on request and closed once the request finishes:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Route Handling & Templating (`app/routers/trace.py`)
FastAPI matches incoming paths and returns rendered Jinja2 templates. Here is the lifecycle of a request to `https://tracegreens.com/?batch_id=TG-RAD-20260209-A`:
1. The `homepage` function captures `batch_id` as a query parameter.
2. It fetches data from the database using SQLAlchemy, pre-loading events (`joinedload(Batch.events)`) to prevent N+1 query performance hits.
3. The server passes the database objects to `templates.TemplateResponse("home.html", context)`.
4. Jinja2 interpolates the data into the HTML and serves pure HTML to the user's browser.

---

## 4. Security Architecture

Maintaining integrity and confidentiality is critical, especially when handling business metrics, inventory, and customer details.

### Admin Authentication & Session Security
Admin screens in `app/routers/admin.py` are secured using simple cookie-based authentication:
* Login verification checks a plain-text comparison with the password stored in `settings.ADMIN_PASSWORD` (retrieved from secure environment variables).
* Upon successful authentication, a cookie `admin_session=authenticated` is set.
* **Security Middleware (Decorator Pattern)**: Every admin endpoint checks for this cookie. If missing or invalid, it redirects the request to `/admin/login`.

> [!WARNING]
> While a cookie check is lightweight, in production, session validation should use cryptographically signed tokens (like JWT) or database-backed session IDs to prevent cookie spoofing.

### Database Safety (SQL Injection Prevention)
SQL injection is blocked natively by using **SQLAlchemy ORM**. Database queries are translated into parameterized SQL commands (prepared statements) by the driver, ensuring that user input (like a queried `batch_id`) is treated strictly as data and never as executable code:

```python
# Fully secure from SQL injection:
db.query(Batch).filter(Batch.batch_id == batch_id.strip().upper()).first()
```

### XSS & CSRF Prevention
* **Cross-Site Scripting (XSS)**: Jinja2 auto-escapes all variables passed into templates by default. Any HTML characters (like `<script>`) injected into a form or database field will be converted to safe HTML entities (like `&lt;script&gt;`) upon rendering.
* **Cross-Site Request Forgery (CSRF)**: For form submittals, especially within the admin panel, adding unique session tokens is recommended for enterprise scale to ensure that requests originate from authenticated forms.

---

## 5. Deployment Mechanics

The project supports containerized builds for seamless hosting on platforms like **Railway**, **Render**, or a custom **VPS**.

### Docker Deployment (`Dockerfile` & `docker-compose.yml`)
The `Dockerfile` is built on a minimal footprint (`python:3.12-slim`):
1. Sets up the working directory `/app`.
2. Installs requirements with `--no-cache-dir` to minimize image size.
3. Copies source files and starts the ASGI server `uvicorn`.

For local development, `docker-compose.yml` mounts the host directory into the container. The `--reload` flag instructs Uvicorn to monitor modifications and reload instantly without rebuilding the container:
```yaml
volumes:
  - .:/app
ports:
  - "8000:8000"
```

### Cloud Providers (Railway, Render, Nixpacks)
* **Railway**: Uses the `nixpacks.toml` configuration to recognize the FastAPI layout and automatically compile and run the backend.
* **Procfile**: Tells platforms like Heroku/Render exactly which command to use to run the web server:
  `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## 6. Compliance & Legal Considerations

Operating a public crop traceability web application involves food safety and digital data compliance standards.

### Food Traceability & Safety Compliance
Providing public crop data (soil logs, seed types, water cycles) supports food safety and compliance:
* **FSMA Section 204 (FDA Food Traceability Rule)**: Under modern food regulation, keeping detailed digital records of crop harvesting, shipping, and receiving is highly recommended. TraceGreens maps directly to these compliance rules by recording the dates, locations, and personnel for key events in each tray.
* **Allergen Disclaimer**: Microgreens (especially mustard, sunflower, or pea shoots) can cause allergic reactions in some individuals. It is legally recommended to have a clear disclaimer in the footer or Order page warning customers of allergens.

### Data Privacy & Legal Disclaimers (GDPR & CCPA)
Because you process customer orders and store names, addresses, phone numbers, and purchase history:
1. **Privacy Policy**: You must host a clear Privacy Policy page outlining how customer personal data is stored, protected, and used.
2. **Cookies Policy**: If using session cookies or third-party analytics (like Google Analytics), display a cookie consent banner.
3. **Terms of Service**: Protect your farm business from liability by adding terms stating that crop metrics represent batch averages and do not constitute biological warranties.
