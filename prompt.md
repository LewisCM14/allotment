I am now at the point in my application where i want to begin implementing the user preference interface (see implementation.md). This is the interface marked as 7 in the wire frames found in client_side.md. its purpose is to allow users to nominate a day to give a specific type of plant food.

1. I would like to begin the implementation by adding the database models as per the design found in database.md. The first model will be the one for the Feed table. the feed table. which is a reference table for the possible plant feeds available when creating grow guides i.e. Bone Meal, Tomato Feed, etc. i will seed the feed groups via alembic like i have in my other migrations (see add_disease_and_pest). the model definition itself should live in `/home/lewis/dev/allotment/backend/app/api/models/grow_guide/guide_options_model.py`.

1. The next model is the user_feed_day model which is for a junction table that uses a composite primary key for storing what day each unique users gives each type of plant food. this will most likely live in `/home/lewis/dev/allotment/backend/app/api/models/user/user_model.py`

1. I will then need to add the api logic to allow users to perform crud operations for setting a specific day they wish to give each type of feed via the UI. The detail specification for how the API should be implemented is found in server_side.md. but in short there will be an endpoint stored in user_preference.py that provides Users the ability to alter the day they give a nominated feed type. This utilizes a read and update route that manipulates entries in the User Feed Day table and the workflow for a create & update is:
    
    ```
    API Layer (Endpoints):

    Receives the request and validates input using Pydantic schemas.
    Delegates the business logic to the Service Layer.
    Service Layer (Unit of Work):

    Starts a Unit of Work to manage the transaction.
    Invokes the Domain Layer (i.e. Factories) to validate and prepare domain objects.
    Coordinates operations across multiple Repositories via the Unit of Work.
    Domain Layer (Factories):

    Applies business rules and validations to ensure only valid objects are passed to the Repository Layer.
    Returns validated domain objects to the Service Layer.
    Repository Layer:

    Encapsulates database access logic.
    Executes SQL queries or ORM operations to persist the validated objects.
    info

    Does not handle transactions or business logic.

    Service Layer (Unit of Work):

    Finalizes the transaction by committing or rolling back changes.
    Returns the result to the API Layer.
    API Layer:

    Constructs the response and sends it back to the client.
    ```

- Unit & integration test are to be created here - `/home/lewis/dev/allotment/backend/tests`

1. The UI can then be created. i follow a three later pattern for my interfaces where i have a container and presenter component that will be stored in here - `/home/lewis/dev/allotment/frontend/src/features/preference/components` that then feed into a page stored here `/home/lewis/dev/allotment/frontend/src/features/preference/pages`, this page component will sit within my standard pageLayout.tsx component. I then integration test the interface at the page level. (see UserAllotmentInfo.test.tsx for example). I am using ShadCN and Tailwind for my UI components, see global.css for my variable configurations. in terms of API integration between the frontend and backend, i have a services folder in the feature folder that will have the logic for accessing the endpoint created in user_preference.py. this logic will leverage the tanstack for caching, hooks are to be stored here - `/home/lewis/dev/allotment/frontend/src/features/preference/hooks` and my api.ts & errorMonitoring.ts files. mocks for testing are stored here `/home/lewis/dev/allotment/frontend/src/mocks`. i also have test for my services, see AllotmentService.test.tsx for example. I also use workbox for service worker capabilities in the frontend, see ServiceWorker.tsx. The user preferences interface is to be a protected route, see App.tsx, AppRoutes.tsx & ProtectedRoute.tsx for how this is configured. further details of my frontend design patters can be found in client_side.md

- The formatting, linting, type-checking/compiling & testing commands can be found in CONTRIBUTING.md
    - for the python based code they must be ran from the backend folder
    - for the typescript based code they must be ran from the frontend folder


We have missed a table out, the day table also needs implementing as detailed in database.md. this should also be stored here - `/home/lewis/dev/allotment/backend/app/api/models/grow_guide/guide_options_model.py`. the days are to be as follows:
- Monday  1
- Tuesday 2
- Wednesday 3
- Thursday 4
- Friday 5
- Saturday 6
- Sunday 7