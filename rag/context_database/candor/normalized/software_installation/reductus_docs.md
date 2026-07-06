---
doc_id: reductus_overview
source_id: CANDOR-006
title: Reductus — Neutron Scattering Data Reduction Repository Overview
instrument: multiple / neutron scattering
workflow_stage: data_reduction_software
source_type: software_repository
access_level: public
status: current
owner: reductus organization
last_reviewed: 2026-06-15
source_url_or_path: https://github.com/reductus/reductus
source_last_updated: 2026-05-27
citation_required: true
---

# Reductus — Neutron Scattering Data Reduction Repository Overview

## Purpose

Reductus provides tools for data reduction for neutron and x-ray scattering. The project includes Python reduction libraries and a web-based, visual dataflow interface for neutron scattering instruments.

## Main components

- **reflred** — Python package for loading, modifying, and saving reflectivity data sets.
- **ospecred** — Python package for loading, modifying, and saving off-specular reflectivity data sets.
- **sansred** — Python package for loading, modifying, and saving small-angle neutron scattering (SANS) data sets.
- **web_gui** — Stateless JavaScript frontend with RPC access to reduction libraries.

## Local data loading

To load data from a local store in web reduction, use:

```text
menu -> data -> add source -> local
```

This requires running the server locally with the local datastore enabled in the configuration.

## Installation and use

### Method 1: pip install

Install Reductus with all optional dependencies:

```bash
pip install "reductus[all]"
```

Start the server:

```bash
reductus
```

For the latest development version:

```bash
pip install "git+https://github.com/reductus/reductus.git#egg=reductus[all]"
```

### Method 2: Docker Compose

Clone the repository, change into the repository directory, then run:

```bash
docker-compose build
docker-compose up -d
```

This starts three containers:

- **web_gui** — web server for the interface.
- **reductus** — backend calculation RPC server.
- **Redis** — cache service.

Files in `./web_gui/testdata/` are mapped into the server at `/data` for testing local file handling. To incorporate Python code changes, stop the containers and repeat the build and startup commands.

Stop the containers:

```bash
docker-compose stop
```

Access the client at:

```text
http://localhost:8000/web_gui/web_reduction_filebrowser.html
```

On Windows 7 with `docker-machine`, use the Docker machine IP instead of `localhost`:

```bash
docker-machine ip default
```

The README gives an example URL:

```text
http://192.168.99.100:8000/webreduce/index.html
```

### Method 3: Run from repository for development

Clone the repository, then install in editable mode. Creating a virtual environment first is recommended.

```bash
python -m pip install -e .
python -m pip install -r requirements.txt
web_gui/run.py
```

Run without installing, using the headless flag:

```bash
PYTHONPATH=. python -m web_gui.run -x
```

Browse to the URL printed by the server, likely:

```text
http://localhost:8002/
```

Development notes:

- Restart the server after changes unless the debug mode flag `-d` makes restart unnecessary.
- Use the headless flag `-x` to avoid opening a new browser tab each time.
- The development server is localhost-only unless the external option `--external` is used.
- To debug external JavaScript packages such as `treejs` or `d3-science`, clone the package repository, link it into `web_gui/webreduce/js`, and update `web_gui/webreduce/js/libraries.js` to point to the local version.

### Speeding up browser update times

Browser update times can be slow, especially when accessing the NCNR data source. The README suggests:

1. Copy `configurations/default.py` to `configurations/config.py`.
2. Set `force_IPV4: True`.
3. Optionally set **auto-reload newer files** to false in the web client.
4. To make the auto-reload default false, set `check_mtimes: false` in `web_gui/webreduce/js/menu.js`.

The README notes that the web-client auto-reload setting is not sticky and resets to checked when the client page is reloaded.

### Method 4: Run from repository for production testing

After testing fixes, build the production client to check behavior in the production server.

Install Node.js and build the JavaScript packages. The README says this process is outlined in `.github/workflows/client_build.yml`. If an external JavaScript package changed, update `web_gui/webreduce/js/libraries_production.js` to point to the development version.

```bash
cd web_gui/webreduce
npm install
rm -rf dist
npm run build
cd ../..
```

Start the server:

```bash
cd web_gui
python run.py
```

Visit:

```text
http://localhost:8002/webreduce/dist/index.html
```

## Repository snapshot

- Repository: `reductus/reductus`
- Description: Web-based, visual dataflow data reduction for neutron scattering instruments.
- Default branch: `main`
- Commit snapshot: `4c60a698d4d81013aaec6d6a7fad4298daafc5f1`
- Public repository: yes
- License shown in page sidebar: Unlicense
- Citation file present: `CITATION.cff`

## Top-level repository contents preserved from source

### Directories

- `.github/workflows`
- `doc`
- `docker-compose`
- `explore`
- `extra`
- `provisioning`
- `reductus`
- `reflbin`
- `tests`

### Files

- `.gitattributes`
- `.gitignore`
- `.gitmodules`
- `.travis.yml`
- `CITATION.cff`
- `LICENSE`
- `MANIFEST`
- `MANIFEST.in`
- `README.rst`
- `docker-compose.yml`
- `pyproject.toml`
- `pytest.ini`
- `regression.py`
- `requirements.txt`
- `show_template`

## Source-cleaning notes

Removed GitHub navigation, account/session data, tracking metadata, forms, icons, badges, modal templates, search UI, repository action widgets, duplicated responsive markup, and raw embedded React/JSON payloads. Preserved the README's substantive installation and operation guidance plus repository-level metadata useful for cataloging.
