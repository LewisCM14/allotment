## Implementation

The application is to be implemented following the Walking Skeleton approach, allowing for a minimal end-to-end version to be completed early before then expanding upon it, the sequence of development is laid out below.

---

### Preliminary

!!! info
    - A Linux based operation system will be required that has PostgreSQL & pgAdmin installed alongside UV and NPM for package management of Python and JavaScript libraries respectively. 
    - The system will also require Docker in order to run and manage containers
    - A GitHub and Fly.io account will also be required for version control and hosting of the application.
    - A code editor will also be required.

---

### Skeleton

1. **Scaffold Code Repository Structure**
    - The code is to be placed under version control in GitHub with a repository that includes the backend and frontend folders as well as a deployments folder to hold infrastructure as code files plus a documentation folder to house supporting documentation, like this design document.
        
        !!! info
            The design document is to be a MKDocs application hosted via GitHub pages.

1. **Server Side Initial Setup**
    - A Minimal FastAPI application is to be implemented with a heath check endpoint.
        - Pydantic, Ruff and MyPy can be integrated at this point.

1. **Database Integration**
    - SQLAlchemy is to be used to setup and migrate the database schema for the User table to a PostgreSQL database.
        - Pytest can be utilized at this point to allow for the automated integration testing of the server and database layers.

1. **Authentication**
    - The User registration and login endpoints are to be created, allowing for the implementation of the JWT authentication solution using the Authlib and fastapi.security libraries.
        - This is also an ideal time to setup structlog as a logging system.

1. **Client Side Initial Setup**
    - A React application is to be initialized with TypeScript & Vite using React Router to create an initial dashboard, allowing for the introduction of Tailwind CSS and ShadCN UI components.
        - Biome can be integrated at this point

1. **User Registration & Login** + **User Logout Interface**
    - A login form is to be created, requiring the implementation of Axios for API queries along with an authentication context using the ContextAPI and the storing of JWT tokens using React Query. A registration form is to also be created, requiring ZOD and React Hook Form for validation.
        - MSW can be utilized now for API integration testing.
        - Initial setup of Workbox for offline capabilities can also be setup now.
        - A hook for logging out users on the frontend should also be implemented at this point as it offers the ability to manually test the registration flow and authentication state of the UI.

1. **User Password Reset Interface**
    - As the skeleton of the application offers little in terms of user functionality a password reset method should be implemented in order to prepare for the likely event of returning users once the app becomes feature rich.

        !!! info
            Gmail SMTP will be sufficient to handle the email confirmation and password reset flows in the products infancy but as the application scales solutions like SendGrid or Postmark will need to be explored.

1. **Containerization**
    - Both the front & backend are to be containerized using Docker. With a `docker-compose.yml` configured for local development.

1. **CI**
    - GitHub actions are to be setup in order to automate builds.

1. **Deployment**
    - The application is to be deployed to Fly.io

1. **CD**
    - GitHub actions are to be setup in order to automate deployments

---

### Meat

1. **Botanical Group List Interface**
    
    ??? info
        Will require the implementation of the Botanical Group table.

1. **Family Information Interface**

    ??? info
        Will require the implementation of the Family and the Disease & Pest group of tables.

1. **User Allotment Interface**

    ??? info
        Will require the implementation of the User Allotment table.

1. **User Preference Interface**

    ??? info
        Will require the implementation of the Feed and User Feed Day tables.
        
        ???+ tip "Future Improvement"
            This is the first point where offline data synchronization would offer tangible benefit. Cross tab sync for authentication could also be considered here.

1. **Grow Guide**

    ??? info
        Will require the implementation of the: Day, Week, Month, Lifecycle, Planting Conditions and Frequency tables followed by the Variety and Variety Water Day tables.

1. **User Owned Grow Guide Interface**
    
    ??? info
        Will require the implementation of the User Active Varieties table.

1. **Weekly ToDo**

1. **User Profile Interface**

1. **User Notification Interface**
    
    ??? info
        This will require a database migration in order to store a users notification preference.

1. **Public Grow Guides** 

1. **Monthly ToDo**

    ??? info 
        Will require the implementation of the Country Season and Season tables.