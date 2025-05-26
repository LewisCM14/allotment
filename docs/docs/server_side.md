## Server Side Requirements

The aim with the server side layer of the application, much like the database and client layers, is to support the applications overall modular design by not being tightly coupled to its neighbors, whilst still enforcing data consistency and integrity. 

All while delivering a fast and seamless "request - response" experience to many concurrent end users who are performing CRUD operations that require relatively simple business logic but complex queries with multiple joins.

<u>**Requirements**:</u>

- Please refer to the [High Level Requirements](overview.md).

- Must integrate with PostgreSQL.
- Must support typing so to harmonize with the robust relation database schema proposed.
- Must be able to integrate with a user authentication system.
- Must integrate with a user interface that facilities user creation and Create, Read, Update & Delete (CRUD) actions en masse.
    - Will need to integrate with a modern front end framework in order to deliver a progressive web app (PWA).
- Must adhere to the Representational State Transfer (REST) architectural design principles.
- Must be able to accommodate server side caching in order to support offline capabilities as allotments can be in areas of poor signal.
- Must be able to support push notifications and automated email in order to implement a feature rich application.
    - Must be able to support batch processing in order to send these notifications.

<u>**Testing Considerations**:</u>

- Unit tests that confirm the Server Side solution enforces the stipulated data consistency will be required such that the architectural goal of modularity can be realized.
- Integration tests against the PostgreSQL database would also be beneficial.

!!! info
    Testing the happy pathway is to be prioritized and deemed sufficient unless a bug is discovered that steers the application away from intended functionality. In this instance a test confirming the bug is no longer present is to be written first before a resolution is implemented, following Test Driven Development (TDD) principles and allowing for an automated check that the ensures the application does not regress in the future.

---

## Routes

### User Tables

=== "User"
    Ability to create a user account with email and password that can have a first name and country code assigned to it. This information should be editable by the associated user and thus must be readable also.

    !!! info
        Supporting routes like: login & logout, password reset and email confirmation are also provided when interacting with the User table.

=== "User Allotment"
    Ability for users to create an associated allotment. The details required for this allotment include a zip or postal code along with a width and length measurement. These fields must be editable by the associated user and thus must also be readable.

???+ tip "Future Improvement"
    The ability for users to be able to trigger a cascading delete of all their related data is desirable but currently not a strict requirement as this can be done manually. The effected tables are: user, user active varieties, user feed day, variety water day and the user allotment table.

---

### Disease, Pest & Family Tables

Ability to read from the following tables found within the database:

1. Intervention
1. Pest Treatment
1. Pest Prevention
1. Disease Treatment
1. Disease Prevention
1. Pest
1. Disease
1. Symptom
1. Family Pest
1. Family Disease
1. Disease Symptom
1. Family
1. Botanical Group
1. Antagonist Family
1. Companion Family 

???+ tip "Future Improvement"
    There is only a requirement for read routes on these tables as the data stored within them is to be owned by the projects database administrator(s) and can be updated manually at the database layer via SQL if required. The ability to abstract this out into an administrators panel in the UI later on is desirable though as this will allow for more efficient scaling. 

---

### Grow Guide Tables

=== "Grow Guides"
    The Variety table is the main table users interact with and the data within it forms the backbone off the application. It utilizes the applications authentication solution to allow users to perform complete CRUD operations on the data contained within it. Only a authenticated User, who's ID matches the owner column of a pre exiting row, can alter any data within that row. The complexities of this table that the server side service accommodates include:

    1. If either one of the following pairs exists the other must also:
        1. Transplant Week Start & Transplant Week End
        1. Prune Week Start & Prune Week End
    1. The same logic, in that if a single one exists so must the rest, applies to the following group of columns:
        1. Feed ID - Feed Week Start - Feed Frequency
    1. When a entry within this table is deleted a cascading delete upon the user active varieties and variety water day is performed.

=== "Activate Guide" 
    Users have the ability to set the grow guides they own to active and/or inactive. This action utilizes a route that can read, create and delete entries from the User Active Varieties junction table.

=== "Publish Guide" 
    Users have the ability to make guides they own public/private.
        - The ability for users to copy public guides is also provided.

=== "Feed Day's"
    Users have the ability to alter the day they give a nominated feed type. This utilizes a read and update route that manipulates entries in the User Feed Day table.

=== "Supporting Tables"
    Ability to read from the following tables found within the database:

    1. Lifecycle
    1. Week
    1. Month
    1. Day
    1. Planting Conditions
    1. Feed
    1. Frequency
    1. Country Season
    1. Season

    ???+ tip "Future Improvement"
        There is only a requirement for read routes on these tables as the data stored within them is to be owned by the projects database administrator(s) and can be updated manually at the database layer via SQL if required. The ability to abstract this out into an administrators panel in the UI later on is desirable though as this will allow for more efficient scaling. 

---

### ToDo Routes

!!! info
    The main use case for the application is that users can create and follow grow guides and based upon these guides, have the application produce a todo list of activities they must undertake. These todo lists are split into levels.

=== "Weekly & Daily" 
    
    A route that uses the Weeks table, joined to the Variety Table which is then joined to the: User Active Varieties, Feed Table and the Frequency table in order to provide users with a list of weekly tasks.


    The Day table is then joined in order to provide users with a list of daily todos across a specific week.

=== "Monthly & Seasonal"

    A route that uses the Month table, joined to the Variety Table which is then joined to the: User Active Varieties, Feed Table and the Frequency table in order to provide users with a list of monthly tasks.

 
    This level can then be referenced against the Season and Country Season tables in order to provide a list of seasonal tasks.

???+ tip "Future Improvement"
    These todos, whilst surfaced in the application for users to interact with, will also eventually be able to be sent out as notifications via Email or Push Notification.

---

## General Data Integrity Rules

A method for ensuring no special characters, aside from hyphens and a single space are used, as well as all characters are lower case os provided. That is to be applied to most text based columns, aside from those designated to store notes.
    
!!! danger "Please Note"
    Notes columns are not idea in relational databases and it is to be an ongoing effort to look at the content users are storing within these columns in an effort to provide a more efficient solution.

---

## Server Side Architecture

### Design Patterns

#### Repository Pattern

<u>**Purpose**</u>

Encapsulate data access logic via SQL queries or ORM logic and provide abstraction over database queries by hiding implementation details from the service layer.

<u>**Boundary**</u>

Operates at the Database Layer, Interacting only with the database and should not contain business logic or handle transactions.

<u>**Design**</u>

A Repository class is created for each aggregate or related table group.

!!! example "_The systems Repositories include:_"

    === "User"

        **User Repository** 

        - To encapsulate the: User, User Allotment, User Feed Day and User Active Varieties tables.

    === "Family"

        **Family Repository**

        - To encapsulate the: Family, Botanical Group, Family Antagonist & Family Companion tables.

    === "Disease & Pests"
        
        **Pest Repository**

        - To encapsulate the: Pest, Pest Treatment, Pest Prevention and Family Pest tables.
        
        **Disease Repository**

        - To encapsulate the: Disease, Disease Treatment, Disease Prevention, Symptom, Disease Symptom and Family Disease tables.
        
        **Intervention Repository**

        - To encapsulate the Intervention table.

    === "Grow Guide"

        **Variety Repository**

        - To encapsulate the: Variety, Variety Water Day, Planting Conditions, Feed, Lifecycle and Frequency tables.
        
        **Seasonal Repository**

        - To encapsulate the Country Season and Season tables.
        
        **Day Repository**

        - To encapsulate the Day table.

        **Week Repository**

        - To encapsulate the Week table.

        **Month Repository**

        - To encapsulate the Month table.
        
---

#### Unit of Work

<u>**Purpose**</u>

Groups multiple repository operations into a single transaction, ensuring atomicity and consistency when committing or rolling back operations.

<u>**Boundary**</u>

Only interacts with Repositories at the Service Layer.

<u>**Design**</u>

Unit of Work classes are created to manage transactions and ensure multiple database operations occur as a single unit.

!!! example "_The systems classes include:_"
    
    === "User Management"

        **User**
        
        - For handling the creation of users.

        **User Allotment**

        - For creating and managing user allotments.

    === "Grow Guide Management"

        **Grow Guide**

        - For CRUD operations on grow guides.
    
        **Guide Publishing**

        -  For handling public/private status and copying guides.
    
    === "ToDo Management"   

        **User Weekly ToDo**
    
        - For weekly tasks (coordinating Day, Week, Variety, and User repositories).
        
        **User Monthly ToDo**
        
        - For monthly tasks (coordinating Month, Variety, User, and Seasonal repositories).

    === "Family Information"

        **Family Page**
            
        - For family information pages (coordinating Family, Disease, Pest, and Intervention repositories).

---

#### Factory Pattern

<u>**Purpose**</u>

Apply any business rules or validations before persistence, ensuring the persistence of invalid objects by repositories is prevented.

<u>**Boundary**</u>

Prepares objects at the Domain Layer before they are passed to the Repositories or Unit of Work classes.

<u>**Design**</u>

The Factory pattern is used to simplify the creation of complex domain objects with all required fields validated and constraints applied.

!!! example "_The systems Factories include:_"
   
    === "User"
        
        - User Factory
        
        - User Allotment Factory
    
    === "Grow Guide"
        
        - Variety Factory

    !!! note "Please Note"
        Data input for the remaining tables is handled via a database admin currently factories are not required until an admin panel is introduced in to the application.
---

### Workflow

_The server-side architecture is designed to enforce clear boundaries between layers, ensuring modularity, scalability, and maintainability. Each layer has a distinct purpose and interacts with others in a controlled manner._


#### Create & Update

!!! example "Example"

    1. API Layer (Endpoints):
        - Receives the request and validates input using Pydantic schemas.
        - Delegates the business logic to the **Service Layer**.

    1. Service Layer (Unit of Work):
        - Starts a **Unit of Work** to manage the transaction.
        - Invokes the **Domain Layer** (i.e. Factories) to validate and prepare domain objects.
        - Coordinates operations across multiple **Repositories** via the **Unit of Work**.

    1. Domain Layer (Factories):
        - Applies business rules and validations to ensure only valid objects are passed to the **Repository Layer**.
        - Returns validated domain objects to the **Service Layer**.

    1. Repository Layer:
        - Encapsulates database access logic.
        - Executes SQL queries or ORM operations to persist the validated objects.
        
        !!! danger "info"
            Does not handle transactions or business logic.

    1. Service Layer (Unit of Work):
        - Finalizes the transaction by committing or rolling back changes.
        - Returns the result to the **API Layer**.

    1. API Layer:
        - Constructs the response and sends it back to the client.

---

### Read & Delete

!!! example "Example Workflow"

    1. API Layer (FastAPI Endpoints):
        - Receives the request and validates input using Pydantic schemas.
        - Delegates the business logic to the **Service Layer**.

    1. Service Layer (Unit of Work):
        - Starts a **Unit of Work** to manage the operation.
        - Invokes the **Repository Layer** to fetch or delete data.

    1. Repository Layer:
        - Executes SQL queries or ORM operations to retrieve or delete data.
        - Returns the result to the **Service Layer**.

    1. Service Layer (Unit of Work):
        - Finalizes the operation by committing or rolling back changes (if applicable).
        - Returns the result to the **API Layer**.

    1. API Layer:
        - Constructs the response and sends it back to the client.

---

### Folder Structure

!!! example "Pattern-Based Folder Structure"

    Due to the server-side being a FastAPI application that has a well defined architecture that makes use of specified design patterns the following folder structure is implemented, allowing related logic to be kept together.

    ``` title="FastAPI & Python Application"
    /app
        /api
            /core
                - auth.py
                - config.py
                - database.py
                - limiter.py
                - logging.py
            /factories
                - Contains the "Factories" that apply business rules and/or validation before persistence
            /middleware
                - error_codes.py
                - error_handler.py
                - exception_handler.py
                - logging_middleware.py
            /models
                - Contains the Database Models.
            /repositories
                - Encapsulate data access logic via SQL/ORM logic abstracting it into "Repositories".
            /schemas
                - Contains Schemas for request & response serialization.
            /services
                - Contains the "Units Of Work" for grouping multiple repository operations into a single transaction.
                - Contains any general purpose utilities i.e. the email service.
            /v1
                - Contains the API Endpoints.
        - main.py
        - .env
    /migrations
        - Database migrations version controlled with `Alembic`
    /tests
        - Integration & Unit test suites ran with `Pytest`
    - pyproject.toml
    - uv.lock
    ```
---

## Server Side ADR

Decision record for the server side technologies selected to support the project. When selecting the intended technologies it is important to remember the project requires a modular, scalable and maintainable architecture to support a progressive web app. The server side must run on Linux based operating systems using technologies that are free for commercial use and can integrate with a PostgreSQL database via a RESTful API with support for user authentication. The technologies must also handle many concurrent users that require a high-read workload, caching is also required to support this as well as background tasks.

!!! success "**Outcome**"

    - **Python & FastAPI**

        - Python is well suited for Domain-Drive-Design (DDD) and can be written to provide strong typing support. The team are also familiar with the language already.

        - FastAPI is a high-performance web framework, that automatically generates API documentation and can handle many concurrent users and provides strong typing support via Pydantic. SQLAlchemy, Authlib and Redis can be used to handle PostgreSQL and 2 & multiple methods of user authentication as well as caching support. Celery can also be used to support background tasks. However it does not provide an out the box admin panel, this is not a strict requirement currently though.

??? abstract "**Alternatives**"

    1. TypeScript & NextJS

        - TypeScript is an extremely type safe language that the team do have experience with already and its use would allow them to use the same programming language on the Client & Server sides. However the ecosystem is less mature for PostgreSQL integration than when compared to the Python ecosystem

        - NextJS is a highly modular and scalable framework that offers TypeORM for support in writing database queries that would adhere to the Repository Pattern. As well as integrating with Redis for caching and BullMQ for background tasks. Passport.js could also be used to provide authentication/authorization support.

    1. Python & Django

        - Python is well suited for Domain-Drive-Design (DDD) and can be written to provide strong typing support. The team are also familiar with the language already.

        - Django is a mature, synchronous by default framework, that is extremely secure and comes with its own ORM that is relatively simple to use when compared to SQLAlchemy as well as an out the box admin panel. However it is more suited to monolithic applications and will be less performant when compared to FastAPI in supporting many concurrent users.

    1. Go & Fiber / Gin

        - Go is an extremely fast concurrent language that is compiled. Offering low memory usage ideally suited for microservices ran on cloud infrastructure. However Go does not allow for exceptions and all error handling is done manually.

        - Fiber is a lightweight framework and Gin is a popular and flexible framework. Both will integrate with Redis for caching support and PGX driver for PostgreSQL integration. However the support for ORM's and OAuth2 compliant authentication is low maturity when compared to the other options.