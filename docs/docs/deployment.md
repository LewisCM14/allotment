## Deployment ADR

Whilst the application is to prioritize vertical scaling over horizontal, in order to retain the ability to efficiently deploy to private severs if desired, the current intended deployment scenario is one that uses cloud infrastructure to run Docker containers. The chosen hosting provider must be able to support the deployment of React and FastAPI applications on top of a PostgreSQL database with the ability to scale to 2.5million users

!!! success "Outcome"

    - Fly.io
        - Fly.io provides a simple pathway for Docker based deployments, offering built in PostgreSQL, global distribution and good performance at the expense of customizability when compared to a provider like AWS.

??? abstract "**Alternatives**"

    1. Digital Ocean
        - Whilst Digital Ocean provides full control over a cost effective environment it requires a manual setup and maintenance, something that isn't within scope of the project at this iteration. 

    1. AWS
        - Whilst AWS provide highly scalable managed severs the cost can spiral with this scale, making it a poor choice currently.

---

## Deployment Process 

1. Containerize the FastAPI backend & React Frontend.

1. Push these containers to a GitHub container registry.

1. Deploy to Fly.io.

!!! info
    This process can be automated using GitHub actions.