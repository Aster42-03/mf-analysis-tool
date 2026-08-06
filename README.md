# Mutual Fund Analysis API (v0)

This is a simple dockerized microservice That Pulls data from the web scraper called mftool that has the data of the
Mutual Fund Houses of India, stores them in a local Database for fast access and then links it to its own API endpoints
to extend the functionality to go beyond just being a collection of data and facilitate the training of a small A.I.
model in future to make sense of the said data.

## Tech Stack:

- **Framework:** FastAPI
- **Database**: PostgreSQL Container (via Docker)
- **Package Manager:** 'uv'
- **Testing:** Pytest, TestClient, 'pytest-dotenv' (synchronous for now)

---

## Prerequisites:

Before Running this project, Ensure that these are installed in your system:

- Docker & Docker-Compose (If You do not have it installed click [[here]])

---

## Quick Start (Local Development):

**1. Install Dependencies**

```bash
uv sync
```

*If You Plan to test the application as well run this command.*

```bash
uv sync --group test
```

**2. Create a .env File in your root directory**

```.env
DB_URL=postgresql+asyncpg://username:your_strong_password@hostname:port/mf_data
DB_NAME=mf_data
DB_USER=username
DB_PASSWORD=your_strong_password
DB_HOST=hostname
DB_PORT=port_number
```

**3. Boot Up the service**
If you are using the taskrunner files such as the makefile or just file, the setup is as easy as:

```bash
just start

# or if you are using the make file
make start
```

this would start the containers and the api would be exposed on port http://localhost:8000, Documentation made using
SwaggerUI would be at http://localhost:8000/docs by default unless specified otherwise.

Or if you want to open it in developer mode

```bash
just dev
# or
make dev
```

## Testing

This project uses the standard 'static sandbox' method of testing in that each test is performed in isolation on a test
database so as not to pollute the main database.

To run the test, set up the environment with a `{bash} .env.test` file in the root directory so `pytest-dotenv` can
route traffic to the testing environment.

**1. Setting up the testing environment**

```.env.test
DB_URL=postgresql+asyncpg://username:your_strong_passowrd@hostname:port/test_db
DB_NAME=test_db
DB_USER=test_user
DB_PASSWORD=your_strong_password
DB_HOST=hostname
DB_PORT=port_number
```

**2. Running the Tests**
To test the API, run the command:

```bash
# When using justfile
just test

# When using makefile
make test
```

# Roadmap (v1):

- [ ] Migrate from static sandbox to ephemeral testcontainers.
- [ ] Implement GitHub actions based CI/CD pipeline.
- [ ] Integrate A.I. model processing.



