# High Level Requirements

## Requirements

- Every aspect off the application must run on Linux based operating system.
- All technologies, libraries and packages must be free for commercial use.
- The application is to be mobile first.
- The application is to be a Progressive Web App (PWA).
- The applications architecture must ensure that the Client, Server and Database layers are not tightly coupled. So to to allow for the ease of replacing them with other technologies as desired.

    !!! note "Please Note"
        A goal of the project is to deliver upon the ability to use this document as a blueprint to reproduce aspects of the application in new technologies as a personal learning and development exercise.

---

## Key Considerations

### The Development Team

- A personal project for a developer familiar with domain driven design, mainly using Python for server side code and modern JavaScript/TypeScript based frameworks like React & Vue for creating user interfaces built on top of relational databases. With a strong desire to use advanced design patterns.

- Able to working in CI/CD environments with agile delivery.
- Able to produce their own custom components or make use of component libraries like Mui & Tailwind.

---

### Deployments

- The ability to vertically scale is prioritized over horizontal scaling as the option to efficiently deploy to private and/or dedicated servers must always be available to the application. 
    
    !!! note "Please Note"    
        The current deployment scenario is one that uses containers created with Docker, hosted in a cloud environment by a provider that offers managed database solutions.

- The application is served by a single database so there is currently no need for eventual consistency.
    
    !!! note "Please Note"
        However, the client and server side application are not tightly coupled so to allow for independent deployment inline with the modular architectural design.

---

### User Base

- The age of a typical user is to be assumed to be between 35-75, due to this all aspects of the user interface must be intuitive and simple to use.
- There is an estimated 330,000 allotments in the UK, assuming each of these has a unique owner the initial scale that the application must be able to support is 10% or 33,000 users. 
- It is also to be assumed that traffic peaks on the weekends, with the application required to support many concurrent users, especially during summer months. Due to this the architecture should be able to facilitate several thousand unique queries at a time initially.
    
    !!! note "Please Note"
        Due to the modularity in the applications architecture design, a solution to further scaling is the option of selecting a new underlying technology. However, if the initial technologies used can scale to support roughly 2.5 million active users at once it would be more than sufficient to support the entire market share of European allotments.
