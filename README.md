# BOE Data Extraction Project

## Short Description

This project implements an automated system to scrape and store data from Spain's *Boletín Oficial del Estado* (BOE). It uses Python together with the Prefect workflow orchestration library to manage the information gathering processes.

## Main Features

The system provides:

1. **Article Metadata Collection by Date**
   * Downloads the daily XML index for a given date.
   * Extracts all published article identifiers (e.g. `BOE-A-YYYY-NNNNN`).
   * For each article, gathers key metadata including direct URLs to the XML and PDF versions.
   * Stores this metadata in a structured JSONL file (`data/boe_metadata.jsonl`).

2. **Article Text Extraction**
   * Allows downloading the full content of a specific BOE URL (generally the XML version of an article).
   * Extracts and saves the plain text content to a file in `data/raw/`.

3. **Workflow Orchestration with Prefect**
   * Uses Prefect flows and tasks to manage extraction and storage.
   * Includes a Prefect deployment configuration (`prefect.yaml`).

## Technologies Used

* **Python 3.x**
* **Prefect** for workflow orchestration
* **Requests** for HTTP requests to BOE services
* **Beautiful Soup 4** for HTML/XML parsing (mainly XML)
* **Standard Python libraries**: `re`, `json`, `pathlib`

## Project Structure

```
.
├── data/
│   ├── raw/                # Extracted article text
│   │   └── boe_13297.txt   # Example text file
│   └── boe_metadata.jsonl  # Article metadata in JSONL format
├── flows/
│   ├── __init__.py
│   ├── scrape_and_store.py       # Prefect flow to download and store content from a URL
│   └── scrape_boe_day_metadata.py # Prefect flow to get a day's metadata
├── main.py                 # Entry point for local flow runs
├── prefect.yaml            # Project and deployment configuration
├── tasks/
│   ├── __init__.py
│   ├── boe.py              # Tasks that interact with the BOE
│   ├── scraping.py         # Generic scraping tasks
│   └── storage.py          # Data storage tasks
└── README.md               # This file
```

## Installation

1. **Clone the repository (if applicable)**
   ```bash
   git clone <repository-url>
   cd <directory-name>
   ```

2. **Create and activate a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/macOS
   # venv\Scripts\activate   # On Windows
   ```

3. **Install dependencies**
   The project includes a `requirements.txt` file with all required packages, including development ones such as `pytest`:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

* **Prefect:** The `prefect.yaml` file defines the Prefect project configuration and deployments.
  * The `work_pool` and `work_queue_name` may need to be adjusted to match your Prefect agent environment.
  * The `pull` section currently contains an absolute directory path that should be changed for portability if using `set_working_directory` in deployments.
* **Flow Parameters:**
  * The `scrape_boe_day_metadata` flow in `main.py` has the date `2025-06-28` hardcoded for testing. For parameterized runs this date should be passed as an argument.
  * The `scrape_and_store` flow receives `url` and `filename` as parameters that can be specified when running or deploying the flow.
  * The metadata file name (`data/boe_metadata.jsonl`) is currently hardcoded in the task `tasks.storage.append_metadata`. It could be turned into a configurable parameter for more flexibility.

## Basic Usage

There are two main ways to run the flows:

1. **Via `main.py` (for local development and testing)**
   The file `main.py` is configured to run one of the flows. By default it runs `scrape_boe_day_metadata`:
   ```bash
   python main.py
   ```
   You can modify `main.py` to run other flows or change parameters.

   **Note about `PREFECT_API_URL`:**
   If you run `python main.py` and get an error like `ValueError: No Prefect API URL provided...`, Prefect is trying to connect to a backend server but no configuration is found. For local runs that interact with the Prefect engine you may need:

   * **Start a local Prefect server (optional if you want to use the UI and other backend features)**
     In a separate terminal run:
     ```bash
     prefect server start
     ```
     This usually starts a server at `http://127.0.0.1:4200`.

   * **Set the API URL**
     Once the server is running (or if you connect to another Prefect instance) set the environment variable in the terminal where you will run `main.py`:
     ```bash
     export PREFECT_API_URL="http://127.0.0.1:4200/api"
     # For Windows (cmd.exe): set PREFECT_API_URL="http://127.0.0.1:4200/api"
     # For Windows (PowerShell): $env:PREFECT_API_URL="http://127.0.0.1:4200/api"
     ```
     Alternatively you can set this in your Prefect profile:
     ```bash
     prefect profile set-api-url http://127.0.0.1:4200/api
     ```
     If you prefer to run the flows in `main.py` without a backend (completely ephemeral and local, losing features such as the UI or persistent run history), make sure your Prefect configuration or how the flows are invoked does not explicitly require a server. For simple tests you can sometimes call the flow function directly with `.fn()` which skips the need for a backend, but this is mainly for unit tests of flow logic rather than a full Prefect run.

2. **Via Prefect Deployments**
   The `prefect.yaml` file defines a deployment named `scrape-boe` for the `scrape_and_store` flow.
   * **Build the deployment (if first time or after changes)**
     ```bash
     prefect deployment build flows/scrape_and_store.py:scrape_and_store -n scrape-boe -q default
     ```
     (Adjust parameters according to `prefect.yaml` or your needs.)
   * **Apply the deployment**
     ```bash
     prefect deployment apply scrape_and_store-deployment.yaml
     ```
     (The YAML file name may vary depending on the output of the build command.)
   * **Run the flow from a Prefect agent**
     Make sure you have a Prefect agent running and listening to the specified work queue (e.g. `default`):
     ```bash
     prefect agent start -q default
     ```
     You can then trigger the flow from the Prefect UI or the CLI.

## Tests

This project uses `pytest` for unit and integration tests and `pytest-cov` to measure code coverage.

To run the tests:

1. **Ensure development dependencies are installed**
   If you followed the "Installation" section you should already have `pytest` and `pytest-cov` from `requirements.txt`. If not, install them:
   ```bash
   pip install pytest pytest-cov
   # or reinstall everything
   # pip install -r requirements.txt
   ```

2. **Run Pytest**
   From the repository root execute:
   ```bash
   pytest
   ```
   This will automatically discover and run all tests in the `tests/` directory. It also generates a coverage report in the terminal and a `coverage.xml` file.

## Possible Improvements / Next Steps

Based on the initial analysis of the project, the following areas could be improved:

* **Robustness and Error Handling** – implement retries, more specific exceptions and data validation.
* **Advanced Configuration** – externalize any hardcoded configuration.
* **Logging** – integrate a detailed logging system.
* **Automated Tests** – develop unit and integration tests.
* **Dependency Management** – create and maintain a `requirements.txt` or `pyproject.toml`.
* **Scalability** – explore concurrent/parallel execution of tasks for large data volumes.
* **Advanced Content Parsing** – create parsers for the internal structure of BOE articles if deeper analysis is required.
* **Documentation** – keep this README up to date and add comments in the code where needed.

