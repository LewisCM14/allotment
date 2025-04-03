# High Level Requirements

## Requirements

- Every aspect off the application must run on Linux based operating system.
- All technologies, libraries and packages must be free for commercial use.
- The application is to be mobile first.
- The application is to be a Progressive Web App (PWA).
- The applications architecture must ensure that the Client, Server and Database layers are not tightly coupled. So to to allow for the ease of replacing them with other technologies as desired.

    !!! info
        A goal of the project is to deliver upon the ability to use this document as a blueprint to reproduce aspects of the application in new technologies as a personal learning and development exercise.

---

## Key Considerations

### The Development Team

- A personal project for a developer familiar with domain driven design, mainly using Python for server side code and modern JavaScript/TypeScript based frameworks for creating user interfaces built on top of relational databases. With a strong desire to use advanced design patterns.

- Able to working in CI/CD environments with agile delivery.

---

### Deployments

- The ability to vertically scale is to be prioritized over horizontal scaling as the option to efficiently deploy to private servers must always be available. 
    
    !!! info    
        However the current desired deployment scenario is one that uses Docker, hosted in a cloud environment.

- The application will be served by a single database so there is currently no need for eventual consistency.
    
    !!! info
        However the client and server side application are not to be tightly coupled so to allow for independent deployment inline with the modular architectural design.

---

### User Base

- The age of a typical user is to be assumed to be between 35-75, due to this all aspects of the user interface must be intuitive and simple to use.
- There is an estimated 330,000 allotments in the UK, assuming each of these has a unique owner the initial scale that the application should be able to support is 10% or 33,000 users. 
- It should also be assumed that traffic peaks on the weekends, with the application to support many concurrent users, especially during summer months. Due to this the architecture should be able to facilitate 30,000 unique queries at a time initially.
    
    !!! info
        Due to the desired modularity in the applications architecture a solution to further scaling is the option of selecting a new underlying technology. However, if the initial technologies used can scale to roughly 2.5 million users with the ability to facilitate approximately 2.25 million unique queries at once it would be more than sufficient to support the entire market share of European allotments.
