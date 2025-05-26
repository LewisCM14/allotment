## Deployments Requirements

The application is to priorities the ability to vertically scale over horizontally in order to retain the ability to efficiently deploy to private and/or dedicated severs if desired in the future. However, the initial method of deploying the system to production is to be one that is robust and repeatable, allowing for a seamless CI/CD experience to a cloud based environment that offers managed PostgreSQL. Affording the application the ability to scale in user base and application reach.

<u>**Requirements:**</u>

- Please refer to the [High Level Requirements](overview.md).

- The deployment method must be one that stands the application up in production on a cloud based hosting provider that offers managed PostgreSQL solutions.
- Must integrate into a CI/CD pipeline that produces Docker containers for both the front and backend services designed to run on Linux based operating systems, held in a online registry.
    - The Client, Server and Database layers of the application must be able to be deployed in isolation to support the applications modular architecture.

---

## Deployment ADR

Whilst the application is to prioritize vertical scaling over horizontal, in order to retain the ability to efficiently deploy to private and/or dedicated severs if desired, the current intended deployment scenario is one that use a cloud based hosting provider that offers managed Postgres and the ability to to run Docker containers.

!!! success "Outcome"

    - Render
        - Like Fly.io, Render provides a pathway for Docker based deployments, offering managed PostgreSQL databases, global distribution and good performance, it offers this solution with a free tier though which is ideal in this iteration of the project.

??? abstract "**Alternatives**"

    1. Fly.io
        - Fly.io provides a simple pathway for Docker based deployments, offering built in PostgreSQL, global distribution and good performance at the expense of customizability when compared to a provider like AWS.

    1. Digital Ocean
        - Whilst Digital Ocean provides full control over a cost effective environment it requires a manual setup and maintenance, something that isn't within scope of the project at this iteration. 

    1. AWS
        - Whilst AWS provide highly scalable managed severs the cost can spiral with this scale, making it a poor choice currently.

---

## Deployment Process 

In order to ensure that the applications deployments are scalable and repeatable GitHub actions is leveraged to execute a CI/CD pipeline that pushes separate containers for the front and backend to a registry. Render then access this registry to deploy from via a hook.

1. **CI Pipelines**

    - The **Frontend** pipeline is triggered each time a pull to `main` is made that alters content stored within the `frontend` folder. First ensuring the correct versions of `Node` & `NPM` are available before installing the dependencies in order to check the linting and formatting and ensure the `TypeScript` code compiles. Once these steps are complete the test suite is ran and upon a 100% pass rate the CD pipeline is triggered.

    - The **Backend** pipeline is triggered each time a pull to `main` is made that alters content stored within the `backend` folder. First it installs `UV` before using the package management tool to install `Python` and the required dependencies. The virtual environment is then activated so the linting and formatting can be checked followed by verification of the static typing. Once these steps are complete the test suite is ran and upon a 100% pass rate the CD pipeline is triggered.

        !!! info
            In order to run the backend test suite the `.env.template` is utilized to provide environment variables.


1. **CD Pipelines**

    - The **Frontend** pipeline orchestrates the process of creating the required frontend container for application deployment and registering it on GitHub. This process leverages a `Dockerfile` that installs the dependencies, copies the source code for better caching and builds the application. An `NGINX` configuration, that is under version control in the repository, is then applied via a `docker-entrypoint.sh` script prior to container startup.

    - The **Backend** pipeline orchestrates the process of creating the required backend container for application deployment and registering it on GitHub. This process leverages a `Dockerfile` that installs `UV` before then using the package management tool to install the applications dependencies. The source code is to then copied for caching and the APIs health check endpoint utilized for monitoring and recovery. Database migrations are then ran prior to container startup. A `docker-entrypoint.sh` script that leverages the `Alembic` migrations is executed to facilitate this.

    !!! info
        In order to ensure that only relevant source code is copied, making the images smaller, more secure, and faster to build `.dockerignore` files are stored in the **Frontend** & **Backend** folders.

1. **Register the Containers on GitHub**
    
    - Upon successful orchestration of the CD pipeline a **Frontend** & **Backend** container is registered within the repository on GitHub.

!!! example "Deployment Files"

    ```
    /.github/workflows
        - backend_cd.yml
        - backend_ci.yml
        - docs_cicd.yml
        - frontend_cd.yml
        - frontend_cd.yml
    /backend
        - .dockerignore
        - docker-entrypoint.sh
        - dockerfile
    /frontend
        - .dockerignore
        - docker-entrypoint.sh
        - dockerfile
        - nginx.conf
    ```

!!! note "Please Note"
    All the steps up to this point have not been Render specific and the produced front and backend containers can be taken from the registry, configured thorough the use of environment variables and deployed via almost any method desired.

1. **Deploy the Backend & Frontend Containers on Render**

    - The next step after registering the containers is deploying them to Render. This is step is automated thorough the use of deployment hooks, one for the frontend and one for the backend, in order to access the hooks provided by Render the following steps have been completed:

    1. **Create a Environment on Render**

        - The application sits within an environment created in the Render dashboard that consists of three individual services.

    1. **Create a PostgreSQL Database Service in the Environment**

        - A PostgreSQL database has been configured as a service within the application.

    1. **Create The Front and Backend Services in the Environment**

        - Separate web services have been created within the Render environment. One for the Frontend and one for the Backend. Each of these services has had their environment variables configured through the Render UI based upon the `.env.template` files found within the **Frontend** & **Backend** folders.
        
        !!! info
            When running the application for local development, copies of these files are created and the _template_ suffix dropped in order to run the application. To prevent the leaking of secrets to the public these files have been added to the repositories global `.gitignore` file. More information on setting the project up locally can be found in the `CONTRIBUTING.md` file at the root of the repository.

        !!! info
            As the frontend is a Vite application that is built during the CD pipeline and the resulting container pushed to a registry, environment variables are injected at runtime. This is achieved by a script that generates a `env-config.js` file within the Docker container when it starts, making the variables available to the application.
    
    1. **Register The Hook in GitHub**

        - The provided hook, found in the settings tab of the Render UI for each respective web service, has then been registered in the GitHub repositories **Settings** tab under the **Secrets and Variables: Actions** section. The CD pipelines utilize these keys to trigger automated deployment to the platform.


!!! note "Please Note"
    The developer documentation, detailed in the `docs` folder of the repository, is a `MKDocs` application that is automatically deployed via a CI/CD action on GitHub to there static website hosting platform (GitHub Pages). The pipeline leverages `UV` to install the required dependencies and build the static website before pushing these files to a `gh-pages` branch that the site is configured to display from within the GitHub dashboard.