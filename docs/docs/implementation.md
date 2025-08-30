## Implementation

!!! note "Please Note"
    - This whole section of the documentation is for reference when building the entire application from the ground up and details a logical approach to developing and integrating each of its constituents.

The application is designed to be implemented following the Walking Skeleton approach, allowing for a minimal end-to-end version to be completed early before then expanding upon it, a logical sequence of development is laid out below.

---

### Preliminary

!!! info 
    - A Linux based operation system will be required that has PostgreSQL & pgAdmin installed alongside UV and NPM for package management of Python and JavaScript libraries respectively. 
    - A GitHub and Render account will also be required for version control and hosting of the application.
    - A code editor will also be required.

---

### Skeleton

1. **Scaffold Code Repository Structure**
    - The code is to be placed under version control in GitHub with a repository that includes the backend and frontend folders as well as a `.github/workflows` folder to hold infrastructure as code files plus a docs folder to house supporting documentation.
        
        !!! note "Please Note"
            i.e. this design document, which is a MkDocs application hosted via GitHub pages.

1. **Server Side Initial Setup**
    - A Minimal FastAPI application is to be implemented with a health check endpoint.
        - Pydantic, Ruff and MyPy can be integrated at this point.

1. **Database Integration**
    - SQLAlchemy is to be used to setup and migrate the database schema for the User table to a PostgreSQL database used for development.
        - Pytest can be utilized at this point to allow for the automated integration testing of the server and database layers.

1. **Authentication**
    - The User registration and login endpoints are to be created, allowing for the implementation of the JWT authentication solution using the Authlib and fastapi.security libraries.
        - This is also an ideal time to setup structlog as a logging system.

1. **Client Side Initial Setup**
    - A React application is to be initialized with TypeScript & Vite using React Router to create an initial dashboard, allowing for the introduction of Tailwind CSS and Shadcn UI components.
        - Biome can be integrated at this point

1. **User Registration & Login** + **User Logout Interface**
    - A login form is to be created, requiring the implementation of Axios for API queries along with an authentication context using the ContextAPI and the storing of JWT tokens using React Query. A registration form is to also be created, requiring ZOD and React Hook Form for validation.
        - MSW can be utilized now for API integration testing.
        - Initial setup of Workbox for offline capabilities can also be setup now.
        - A hook for logging out users on the frontend should also be implemented at this point as it offers the ability to manually test the registration flow and authentication state of the UI.

1. **User Password Reset Interface**
    - As the skeleton of the application offers little in terms of user functionality a password reset method is to be implemented in order to prepare for the likely event of returning users once the app becomes feature rich.

        !!! tip "Future Improvement"
            Gmail SMTP is sufficient to handle the email confirmation and password reset flows in the products infancy but as the application scales solutions like SendGrid or Postmark will need to be explored.

1. **User Profile Interface**
    - At this point it is minimal effort to setup the User Profile interface in its entirety.

1. **CI/CD**
    - GitHub actions are to be setup in order to automate builds and release pipelines to production. These pipelines are to ensure Docker containers, that have passed all required validations, are registered on GitHub and then deployed to a hosting provider that offers managed PostgreSQL solutions.

        !!! info
            Further detail on the required validations can be found in the `CONTRIBUTING.md` file at the root of the repository.

        !!! note "Please Note"
            The current hosting provider is Render.

---

### Body

1. **Botanical Group List Interface**
    
    ??? info
        Will require the implementation of the Family tables: Family, Botanical Group, Antagonist & companion.

1. **Family Information Interface**

    ??? info
        Will require the implementation of the Disease & Pest group of tables.

1. **User Allotment Interface**

    ??? info
        Will require the implementation of the User Allotment table.

1. **User Preference Interface**

    ??? info
        Will require the implementation of the Day, Feed and User Feed Day tables.
        
        ???+ tip "Future Improvement"
            This is the first point where offline data synchronization would offer tangible benefit. Cross tab sync for authentication could also be considered here.

1. **Grow Guide**

    ??? info
        Will require the implementation of the: Week, Month, Lifecycle, Planting Conditions and Frequency tables followed by the Variety and Variety Water Day tables.

1. **User Owned Grow Guide Interface**
    
    ??? info
        Will require the implementation of the User Active Varieties table.

1. **Weekly ToDo**

1. **User Notification Interface**

1. **Public Grow Guides** 

1. **Monthly ToDo**

    ??? info 
        Will require the implementation of the Country Season and Season tables.