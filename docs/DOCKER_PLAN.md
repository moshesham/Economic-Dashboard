# Comprehensive Docker Containerization Plan for Economic Dashboard

## 1. Architecture Overview

To make the application robust and separate the "heavy lifting" (data processing) from the "presentation" (dashboard), we will use a **Multi-Service Architecture** orchestrated by Docker Compose.

### Components:
1.  **Dashboard Service (`dashboard`)**:
    *   Runs the Streamlit application.
    *   **Role**: Read-only consumer of data.
    *   **Focus**: Responsiveness and UI.
    *   **Access**: Connects to the DuckDB database in `READ_ONLY` mode (recommended for DuckDB concurrency).

2.  **Data Engine Service (`worker`)**:
    *   Runs a Python scheduler (e.g., `APScheduler` or a simple loop).
    *   **Role**: Data ingestion, cleaning, feature engineering, and ML training.
    *   **Focus**: Heavy calculations, API calls (SEC, FRED), and database writes.
    *   **Access**: Connects to DuckDB in `READ_WRITE` mode.

3.  **Shared Volume (`duckdb_data`)**:
    *   A Docker Volume that persists the `economic_dashboard.duckdb` file.
    *   Mounted to both containers.

## 2. Data Flow Strategy

1.  **The Worker** runs periodically (e.g., daily at midnight, or continuously for real-time).
    *   It executes `modules/data_loader.py` to fetch new data.
    *   It runs `scripts/cleanup_old_data.py` to enforce retention.
    *   It runs `modules/features/feature_pipeline.py` to pre-calculate features.
    *   It saves everything to the DuckDB file in the shared volume.
2.  **The Dashboard** simply queries the tables.
    *   Since the data is pre-processed, the dashboard loads instantly without waiting for API calls or calculations.

## 3. Implementation Plan

### Step 1: Create a `scheduler.py`
We need a dedicated entry point for the worker container that orchestrates the tasks.
*   **Task**: Create `scripts/scheduler.py`.
*   **Logic**: Use `schedule` or `time.sleep` loop to trigger existing scripts (`data_loader`, `cleanup`, etc.).

### Step 2: Create the `Dockerfile`
A single Dockerfile can support both services (we just change the command).
*   **Base Image**: `python:3.10-slim` (Lightweight, secure).
*   **System Deps**: `build-essential`, `git` (for dependencies).
*   **Python Deps**: Install from `requirements.txt`.
*   **Setup**: Create non-root user for security.

### Step 3: Create `docker-compose.yml`
Defines the services and how they interact.
*   **Services**: `dashboard`, `worker`.
*   **Volumes**: Map `./data/duckdb` to `/app/data/duckdb`.
*   **Environment Variables**: Configure paths and modes.

### Step 4: Update Database Connection Logic
Ensure `modules/database/connection.py` handles the Docker environment correctly.
*   **Check**: Ensure it uses an absolute path or an environment variable for the DB path.
*   **Concurrency**: Add a flag or logic to open the DB in `read_only=True` mode for the Dashboard if needed.

## 4. Addressing Your Questions

*   **"Contain and write the data to"**:
    *   We use a **Docker Volume**. This maps a folder on your host machine (or a managed docker volume) to the container. Even if you delete the container, the data persists.
*   **"Would Streamlit also need to read from the docker?"**:
    *   Streamlit runs **inside** the container. It reads the file from the "local" path inside the container (which is actually the mounted volume). It does not need to "reach out" to Docker; it's already there.
*   **"Push down calculations"**:
    *   The **Worker** container handles this. By running the heavy scripts in a separate container, the Streamlit app remains responsive. If the Worker crashes or uses 100% CPU, the Dashboard is unaffected (OS scheduling permits).

## 5. Next Steps (Execution)

1.  **Create `scripts/scheduler.py`**: A script to run the jobs.
2.  **Create `Dockerfile`**: The image definition.
3.  **Create `docker-compose.yml`**: The orchestration file.
4.  **Update `requirements.txt`**: Add `schedule` or `apscheduler`.
5.  **Test**: Build and run.

