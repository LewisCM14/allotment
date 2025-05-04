# Project Setup

---

## Table of Contents
- [Project Setup](#project-setup)
    - [Operating System](#operating-system)
    - [Database](#database)
    - [Python Package Manager](#python-package-manager)
    - [Backend Setup](#backend-setup)
    - [Frontend Setup](#frontend-setup)
- [Contributing](#contributing)
    - [Backend](#backend)
    - [Frontend](#frontend)
    - [Database Migrations](#database-migrations)
    - [Documentation](#documentation)

---

## Operating System

_The project runs on Ubuntu and this setup guide assumes you have already installed this._

- Useful links for WSL
    - <a href="https://learn.microsoft.com/en-us/windows/wsl/install" target="_blank" rel="noopener noreferrer">Install WSL</a>
    - <a href="https://learn.microsoft.com/en-us/windows/wsl/setup/environment" target="_blank" rel="noopener noreferrer">Setup WSL Environment</a>
    - <a href="https://learn.microsoft.com/en-us/windows/wsl/tutorials/wsl-vscode" target="_blank" rel="noopener noreferrer">Using WSL with VS Code</a>
    - <a href="https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack" target="_blank" rel="noopener noreferrer">VS Code Remote Extension Pack</a>

---

## Database

_The project uses Postgres as its database and recommends pgAdmin4 as a management tool._

1. Install Postgres 
    ```
    sudo apt-get install postgresql postgresql-contrib
    ```
    
    > You can confirm this has worked by running the following command - `sudo systemctl start postgresql`

1. Create a User
    ```
    sudo -i -u postgres
    psql
    CREATE USER myuser WITH PASSWORD 'mypassword';
    ALTER USER myuser WITH SUPERUSER;
    CREATE DATABASE mydatabase;
    ```

1. Allow Remote Access
    ```
    sudo nano /etc/postgresql/*/main/pg_hba.conf
    ```
    _Then add the following line to the end of the file_
    ```
    host    all     myuser     0.0.0.0/0     md5
    ```
    _Then edit the Postgres conf_
    ```
    sudo nano /etc/postgresql/*/main/postgresql.conf
    ```
    _Alter the listen addresses to match the line below_
    ```
    listen_addresses = '*'
    ```

    > It is recommended you restart the server now - `sudo systemctl restart postgresql`

- The following commands can also now be ran as a sanity check. 

    Start the PostgreSQL Server
    ```
    sudo systemctl start postgresql
    ```

    Open the PostgreSQL Shell
    ```
    psql
    ```

1. Connect Postgres to pgAdmin
    
    _Download pgAdmin here <a href="https://www.pgadmin.org/download/" target="_blank" rel="noopener noreferrer">https://www.pgadmin.org/download/</a>_
    1. Within the **Default Workspace** page of pgAdmin right click on the **Servers** tab and choose the options to **Register > Server**
    1. Enter a name for the server within the **General** tab
        
        > Most Likely `allotment`
    
    1. Then navigate to the **Connection** tab
        - Set the **Host name/allotment** to `localhost`
        - In the appropriate field set the username to the user created in the step above
        - Enter the password for the user in the appropriate field
            
            > It is recommended to toggle the **Save password** option on here also
        
        - Ensure the **Port** is correct, most likely port `5342`
    
    1. Hitting the **Save** option should then connect you to the Postgres database provided you have it running within a terminal on your local machine.

---

## Python Package Manager

1. Install UV
   
    _Within a terminal run the below command to install UV_
    ```
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

---

> _The following steps assume you have cloned the repository to your local machine._

## Backend Setup

1. Create the Backend virtual environment
    
    _From within the `backend` folder of the project run the command below to create the projects virtual environment_
    ```
    uv sync
    ```
    
    > This command will also install the required version of Python on your machine.
    > As a sanity check you can activate the virtual env by running the following command from inside the `backend` folder `source .venv/bin/activate`

1. Create a copy of the the `.env.template` found in the `backend/app` folder and rename to `.env`
    
    - _Update the environment variables to point at your local Postgres database as well as a GMAIL SMTP solution._

    > You can update the `APP_NAME`, `APP_VERSION` and `LOG_FILE` as desired.

1. Generate the RSA Key Pair for JWT Authentication
    ```
    openssl genpkey -algorithm RSA -out private.pem -pkeyopt rsa_keygen_bits:2048
    openssl rsa -pubout -in private.pem -out public.pem
    ```

    Then format the keys for your `.env` file:
    ```
    echo "JWT_PRIVATE_KEY=$(cat private.pem | tr '\n' '\\n')"
    echo "JWT_PUBLIC_KEY=$(cat public.pem | tr '\n' '\\n')"
    ```
    
    Copy the output from these commands and paste them into your `.env` file, replacing the existing JWT key variables.
    
    > You can now safely delete the temporary key files (`private.pem` and `public.pem`) as they're stored in your environment variables.

1. The API can now be launched be executing the following command from the root of the `backend` folder with the virtual environment activated.
    ```
    fastapi dev
    ```

> The environment variables also configure what instance the service is, i.e. development, UAT, production.
> In production, environment variables are set in the hosting platform.

---

## Frontend Setup

1. Install the Frontend dependencies

    _From within the `frontend` folder of the project run the command to install the projects dependencies_
    ```
    npm i
    ```

    > This step assumes you have the correct versions of `Node` & `NPM` installed on your local machine.

1. Copy the `.env.template` to the root of the `frontend` folder.
    
    - _Rename this file to `.env.local` and reconfigure port 8000 if desired._

        > In production this file is renamed to `.env`.

1. Ensure `CORS` configuration
    
    - _By default the backend is setup to accept the frontend running on port `5173`, this can be configured differently if desired though._

1. The UI can now be launched be executing the following command from the root of the `frontend`.

    ```
    npm run dev
    ```
    > The backed is setup by default to expect the frontend to be running on `localhost:5173`.
___

# Contributing

---

## Backend

_The following commands must be ran and issues resolved prior to raising pull requests_
> The CI workflow uses `ruff check --select I` and `ruff format --check` to detect issues without automatically fixing them.

Linting
```
ruff check --select I --fix
```

Formatting
```
ruff format
```

Type Checking
```
mypy .
```

Tests
```
pytest
```

Run Tests in Parallel
```
pytest --numprocesses=auto
```
--- 

## Frontend

Dev Build

```
npm run dev
```

Preview Production Build
```
npm run preview
```

Linting
```
npm run lint
```

Formatting
```
npm run format
```

Build
```
npm run build
```

Testing
```
npm run test
```

---

## Database Migrations

_Database migrations and managed with Alembic and can be ran from inside the backed virtual env with the following commands._

Autogenerate Alembic Migration
```
alembic revision --autogenerate -m <REVISION MSG>
```

---

## Documentation

_Design documentation must be updated alongside code changes, to preview changes a local MKDocs server can be launched with the following command._
```
mkdocs serve --dev-addr 0.0.0.0:8080
```
> This will require running the following commands from the root of the `docs` folder.
```
uv sync
source .venv/bin/activate
```
**Where appropriate the `CONTRIBUTING.md` must also be updated.**

___