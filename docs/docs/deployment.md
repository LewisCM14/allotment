## Deployment ADR

Whilst the application is to prioritize vertical scaling over horizontal, in order to retain the ability to efficiently deploy to private severs if desired, the current intended deployment scenario is one that use a cloud based hosting provider that offers managed Postgres and the ability to to run Docker containers. The chosen hosting provider must be able to support the deployment of React and FastAPI applications on top of a PostgreSQL database with the ability to scale to 2.5million users

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

In order to ensure that the applications deployments are scalable and repeatable GitHub actions is to be leveraged in conjunction with Render to create a CI/CD pipeline.

1. **CI Pipelines**

    - The **Frontend** pipeline is to be triggered each time a pull to `main` is made. First ensuring the correct versions of `Node` & `NPM` are available before installing the dependencies in order to check the linting and formatting and ensure the `TypeScript` code compiles. Once these steps are complete the test suite is to be ran and upon a 100% pass rate the CD pipeline is to be triggered.

    - The **Backend** pipeline is to be triggered each time a pull to `main` is made. First it must install `UV` before using the package management tool to install `Python` and the required dependencies. The virtual environment is to then activated so the linting and formatting can be checked followed by verification of the static typing. Once these steps are complete the test suite is to be ran and upon a 100% pass rate the CD pipeline is to be triggered.

        !!! info
            In order to run the test suite the `.env.template` will be utilized to provide environment variables.


1. **CD Pipelines**

    - The **Frontend** pipeline is to orchestrate the process of creating the required container for application deployment's and registering it on GitHub. This process leverages a `Dockerfile` that installs the dependencies, copies the source code for better caching and builds the application. An `NGINX` configuration, that is under version control in the repository, is to then be applied and a health check endpoint as defined in a `health.json` file utilized for monitoring and recovery.

    - The **Backend** pipeline is to orchestrate the process of creating the required container for application deployment and registering it on GitHub. This process leverages a `Dockerfile` that installs `UV` before then using the package management tool to install the applications dependencies. The source code is to then be copied for caching and the APIs health check endpoint utilized for monitoring and recovery. Database migrations are to then be ran prior to container startup. A `docker-entrypoint.sh` script that leverages the `Alembic` migration scripts is to be executed.

    !!! info
        In order to ensure that only relevant source code is copied, making the images smaller, more secure, and faster to build `.dockerignore` files are to be created in the **Frontend** & **Backend** folders.

1. **Register the Containers on GitHub**
    
    - Upon successful orchestration of the CD pipeline a **Frontend** & **Backend** container is to be registered within the repository on GitHub.

1. **Create a PostgreSQL Database on Render**

    - As the current deployment scenario leverages a cloud based hosting platform, in Render, that offers managed PostgreSQL Databases, the applications datastore must be configured within the platform.

1. **Register Environment Variables**

    - Once a PostgreSQL database has been registered the applications environment variables are to then be registered in Renders dashboard. `.env.template` files are to be provided within the **Frontend** & **Backend** folders for reference when instantiating these settings.
    
    !!! info
        When running the application for local development, copies of these files are to be created and the _template_ suffix dropped in order to run the application. To prevent the leaking of secrets to the public these files are to be added to the repositories global `.gitignore` file.


1. Deploy the Backend & Frontend Containers on Render

!!! note
    The developer documentation, detailed in the `docs` folder of the repository, is to be a `MKDocs` application that is automatically deployed via a CD/CD action on GitHub to there static website hosting platform (GitHub Pages). The pipeline is to leverage `UV` to install the required dependencies and build the static website before pushing these files to a `gh-pages` branch that the site is configured to display from within the GitHub dashboard. 