## Authentication Requirements

The applications is to contain a minimal amount of personal data. But, whilst minimal, users: emails, postal codes and passwords still require strong protective measures in place and steps to prevent users grow guides from being tampered with must be taken.

As with all other aspects of the application the solution must run on Linux based operating systems and be free for commercial use. Whilst integrating with the modular architecture and able to scale appropriately. It must also be able to run alongside FastAPI & PostgreSQL in a PWA that utilizes a modern front end framework for its user interface.

<u>**Requirements:**</u>

- Please refer to the [High Level Requirements](overview.md).

- Must integrate with PostgreSQL & FastAPI.
- Will need to integrate with a modern front end framework in order to deliver a progressive web app (PWA).
- Must accommodate Representational State Transfer (REST) architectural design principles.
- Must be able to support offline capabilities as allotments can be in areas of poor signal.
- Passwords are not to be stored as plain text.
- Client side request are to be made with **HTTPS** to ensure data is encrypted in transit.

!!! note "Please Note"
    There is currently only a need to authenticate users within the application as all admin owned data is to be managed at the data base layer, meaning an authorization solution is not required. However, the ability to implement a method of authorization in order to support admin activity later on must also be considered.

---

## Authentication ADR

Decision record for the authentication solution the application is to utilize. The chosen solution, as with all other aspects of the application, must run on Linux based operating systems and be free for commercial use. Whilst integrating with the modular architecture and able to scale appropriately. It must also be able to run alongside FastAPI & PostgreSQL in a PWA that utilizes a modern front end framework for its user interface.

!!! success "**Outcome**"

    - **Json Web Tokens (JWT)**

        - Users will authenticate with a email and password. The backend is to then issue a JWT token that the client includes in subsequent requests. This token contains users claims and is verified on each request. This method of stateless authentication is well suited to scalable APIs however it does require the management of JWT on the client side.

        - fastapi.security and Authlib are packages within the FastAPI ecosystem that supports this method of authorization. 
            
            !!! info
                PyJWT is a lightweight alternative to Authlib, however it does not currently handle OAuth2 providers, excluding it from consideration in this use case as an external OAuth2 provider might be desirable in the future. Authlib also provides excellent offline capabilities in line with product requirements.
            
            ???+ tip "Future Improvement"
                Whilst not an immediate requirement, this solution also offers the ability to implement the ability to revoke and blacklist access tokens in the event of a breach. Something that ensures a scalability.

??? abstract "**Alternatives**"

    1. Session-Based Authentication

        - Users will log in and the sever will store and manage session data. A session cookie is then sent to the client and the cookie is validated on each request. This method of authorization is relatively simple when compared to using JWT's, as the browser handles cookies. It is not as scalable long term though.

        - fastapi-users and Starlette Session Middleware are packages within the FastAPI ecosystem that supports this method of authorization.  

    1. OAuth2 & JWTs with External Providers

        - Similar to OAuth2 with JWTs, users authenticate with an external provider (i.e. google, GitHub etc). This provider then issues an access token and the API verifies the token and retrieves user information with each request.

        - Again Authlib can be used to facilitate this process alongside fastapi-login. However, it places an added dependency, that opens the door to requiring the ability to support the various third party providers out there.