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

1. Containerize the FastAPI backend & React Frontend.

1. Push these containers to a GitHub container registry.

1. Create a PostgreSQL database on Render

1. Deploy the Backend & Frontend.

!!! info
    This process can be automated using GitHub actions.