## Operating System

The project runs on Ubuntu and this setup guide assumes you have already installed this.

??? info "Useful Links for WSL"
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
    
    !!! info
        You can confirm this has worked by running the below command
        ```
        sudo systemctl start postgresql
        ```

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

    !!! info
        It is recommended you restart the server now - `sudo systemctl restart postgresql`

1. Connect Postgres to pgAdmin
    
    ??? info "Download pgAdmin"
        <a href="https://www.pgadmin.org/download/" target="_blank" rel="noopener noreferrer">https://www.pgadmin.org/download/</a>

    1. Within the **Default Workspace** page of pgAdmin right click on the **Servers** tab and choose the options to **Register > Server**
    1. Enter a name for the server within the **General** tab
        
        !!! info
            Most Likely `allotment`
    
    1. Then navigate to the **Connection** tab
        - Set the **Host name/allotment** to `localhost`
        - In the appropriate field set the username to the user created in the step above
        - Enter the password for the user in the appropriate field
            
            !!! info
                It is recommended to toggle the **Save password** option on here also
        
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

## Backend Setup

1. Create the Backend virtual environment
    
    _From within the `backend` folder of the project run the command below to create the projects virtual environment_
    ```
    uv sync
    ```

    !!! info
        This command will also install the required version of Python on your machine.

1. Copy the `settings.template.yml` to `backend/app` folder and rename to `settings.yml`
    
    - _The settings will then want configuring to point at your local Postgres database_

    !!! info 
        You can update the `name`, `version` and path for the `log_file` as desired.

1. Generate the RSA Key Pair (For RS256)
    ```
    openssl genpkey -algorithm RSA -out app/keys/private.pem -pkeyopt rsa_keygen_bits:2048
    openssl rsa -pubout -in app/keys/private.pem -out app/keys/public.pem
    ```

    !!! info
        You may need to set permissions with the following commands:
        ```
        chmod 600 app/keys/private.pem
        chmod 644 app/keys/public.pem
        ```

---

## Frontend Setup

1. Install the Frontend dependencies

    _From within the `frontend` folder of the project run the command to install the projects dependencies_
    ```
    npm i
    ```

    !!! info "Please Note"
    This step assumes you have `Node` & `NPM` installed on your local machine.

1. Copy the `.env.template` to the root of the `frontend` folder.
    
    - _Rename this file to `.env.local` and reconfigure port 8000 if desired._

    !!! info 
        In production this file is renamed to `.env`.

1. Ensure `CORS` configuration
    
    - _By default the backend is setup to accept the frontend running on port `5173`, ths can be configured differently if desired though._