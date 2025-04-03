## Database Requirements

The aim for the database layer of the application is to enforce data consistency and integrity as granular as possible. Whilst offering scalability in terms of ease of integration of new features, as well as scalability in terms of user base growth.

The solution must also allow for modularity in the applications architecture such that new database technologies can be dropped in/out with minimal disruption to the other layers. 

!!! info
    This is important as a goal of the project is to deliver the ability to learn new technologies by using them to replace components of the application following the original design laid out in this document as a blueprint.

<u>**Requirements:**</u>

- Please refer to the [High Level Requirements](overview.md).

---

## Tables

![Database Diagram](erd.svg){ loading=lazy }

!!! info
    _Unless stated otherwise below, all `VARCHAR` fields will require a constraint that ensures no special characters are used aside from hyphens and a single space. As well as all characters are stored in lowercase._

### Disease & Pests

=== "Pest"
    Holds the various types of pests.

    !!! note
        - The notes field will not require the default `VARCHAR` constraint applied.

=== "Disease"
    Holds the various types of diseases.
    
    !!! note
        - The notes field will not require the default `VARCHAR` constraint applied.

=== "Symptom"
    Holds the various types of symptoms different diseases can exhibit.
    
    !!! note
        - The symptom field will not require the default `VARCHAR` constraint applied.

=== "Intervention"
    Holds methods of intervention used to treat or prevent the various disease and pests.
    
    !!! note
        - The notes field will not require the default `VARCHAR` constraint applied.

=== "Pest Treatment"
    A junction table that uses a composite primary key for linking what intervention methods are used to treat each type of pest.

=== "Pest Prevention"
    A junction table that uses a composite primary key for linking what intervention methods are used to prevent each type of pest.

=== "Disease Treatment"
    A junction table that uses a composite primary key for linking what intervention methods are used to treat each type of disease.

=== "Disease Prevention"
    A junction table that uses a composite primary key for linking what intervention methods are used to prevent each type of disease.

=== "Disease Symptom"
    A junction table that uses a composite primary key for linking what symptoms different types of diseases exhibit.

=== "Family Pest"
    A junction table that uses a composite primary key for linking what pests effect each family.

=== "Family Disease"
    A junction table that uses a composite primary key for linking what diseases effect each family.

---

### Family

=== "Botanical Group"
    Holds the name and if applicable, the maximum years before crop rotation is required, for the different botanical groups, i.e. Nightshade, Brassicas etc.

=== "Family"
    Holds the common name for varieties of fruit and vegetables, i.e. Tomatoes, Broccoli etc. Linking to the Botanical Group table via ID.

=== "Antagonist Family"
    A junction table that uses a composite primary key for linking what families **should not** be planted near each other. 

=== "Companion Family"
    A junction table that uses a composite primary key for linking what families **should be** planted near each other. 

---

### User

=== "User"
    Holds the minimum amount of unique user information required to provide the applications functionality.
    
    !!! note
        - The user email & password fields will not require the default `VARCHAR` constraint applied.
        - The User First Name field will need the `VARCHAR` constraint applied with an additional rule, preventing the used of numbers also.
        - When an user is removed from this table a cascading delete upon the: user active varieties, user feed day and user allotment tables will be required for data consistency.
        
    ???+ tip "Future Improvement"
        - Long term the Country Code will be used in conjunction with the User Allotment table to provide live weather information to users.

=== "User Allotment"
    Holds the minimum amount of information, about a specific users allotment, linked to the User table via user ID, required to provide the applications functionality. This table enforces the rule that each user can only have one allotment.

    ???+ tip "Future Improvement"
        - Allotment Postal / Zip code will be required to provide live weather information to users.
        - Information about the users allotments width & length will be required to provide planting recommendations to users.
        - When the functionality for providing planting recommendations is implemented, users with multiple allotments will have to total the measurements to get recommendations across there entire area.

=== "User Active Varieties"
    A junction table that uses a composite primary key for storing what grow guides users are currently following.

    !!! note
        - There is currently no method of preventing users from following multiple guides for same specific variety of plant, it is down to users themselves to monitor this.
        - A trigger will be required at the database layer that when users activate varieties the User Feed Day table is checked to ensure they have a nominated day for the guides applicable feed. If there is no nominated day a default is to be added that can then be updated later on within the Users Preferences page later on. This ensures data consistency at both the database and backend layers.

=== "User Feed Day"
    A junction table that uses a composite primary key for storing what day each unique users gives each type of plant food.

---

### Grow Guide

=== "Variety"
    The predominate table end users interact with. Storing the grow guides. The application works on the concept of users planning their allotment activities on a weekly basis, these weekly activities can then be linked to specific days as well as months & seasons referred to.
    
    !!! note
        - The notes field will not require the default `VARCHAR` constraint applied.
        - The first constraint this table will require, is that any time even a single column is altered the last updated column is set to the current datetime.
        - The next constraint this table will require is that if either one of the following pairs exists the other must also:
            1. Transplant Week Start & Transplant Week End
            1. Prune Week Start & Prune Week End
        - The same logic, in that if a single one exists so must the rest, applies to the following group of columns:
            1. Feed ID - Feed Week Start - Feed Frequency
        - The final constraint this table needs, is one that ensures the combination of Owner ID & Variety Name is unique.
        - When a entry within this table is deleted a cascading delete upon the user active varieties and variety water day will be required.

=== "Lifecycle"
    A reference table for the possible lifecycle's available when creating grow guides i.e. Perennial, Annual etc.

=== "Planting Conditions"
    A reference table for the possible planting conditions available when creating grow guides i.e. Sunny, Sheltered etc.
    
    ???+ tip "Future Improvement"
        - Further table(s) will be required to allow for users to detail what portions of their allotment meet these conditions to provide more accurate planting recommendations.

=== "Feed"
    A reference table for the possible plant feeds available when creating grow guides i.e. Bone Meal, Tomato Feed etc.

=== "Variety Water Day"
    A junction table that uses a composite primary key for linking what day each variety detailed within a unique grow guide should be watered on.
    
    !!! note
        - A trigger will be required at the database layer that ensures the amount of days nominated within this table, for a specific variety per week, is equal to that of the integer value stored in the column titled frequency days per year found in the Frequency table, that is linked within the Variety table via ID. To do this the amount of days in the Variety Water Day table will need to be multiplied by 52.
    
    ???+ tip "Future Improvement"
        - This entire table will be dropped once live weather information is provided to users. In favour of using the Water Frequency columns on the Variety table to recommend to users when to water crops based on the weather in their Postal \ Zip code.

=== "Frequency"
    A table that holds different frequency units available for use when creating grow guides. i.e. a frequency of Weekly that means the activity would be performed 52 days across this year.
    
    ???+ tip "Future Improvement"
        This table will replace the Variety Water Day table as the predominate table for detailing watering activities when live weather monitoring is functional. Allowing for use cases like a certain variety needs watering every three days. The weather can then be monitored and if there has been no rainfall at the users allotment location within the last three days they will be prompted to water that variety.

=== "Day"
    A reference table for the seven days of the week available when creating grow guides. Also provides a clear entry point when collecting specific information for daily tasks to provide to end users.

=== "Week"
    A table that holds the 52 weeks of the year and their corresponding start and end dates in the format of `01/01, 07/01` etc. The month each unique week starts in is also stored to allow for easy collection of month specific activities.
    
    !!! note
        - A check constraint will be required  to ensure the start & end date columns meet this format.
        - There will be one week that has a potential 8 days within it in order to handle leap years.

=== "Month"
    A reference table for the twelve possible months for use when creating grow guides. Also provides a clear entry point for collecting month specific information to provide to end users.
    
    !!! note
        The application predominantly works on the concept of users planning their allotment activities on a weekly basis, these weekly activities can then be distributed across the seven available days. Due to this the Month table links to the Week table via ID.

=== "Season"
    A reference table linked to the Country Seasons table via ID that stores the possible seasons available, i.e. Summer, Spring.

=== "Country Season"
    A table that stores the start and end date for each season per unique country. These dates can then be referenced against the Week and User table for detailing seasonal activity to end users.
    
    !!! note
        - The first check constraint this table will require is one to ensure the start & end date columns meet the following format `01/01, 07/01`, as per the Week table.
        - The next check constraint required is one that ensures for each unique country added, all four corresponding seasons are added at the same time.
            - It is up to database admins to ensure the start & end dates for these seasons are correct due to the large variation between countries, but infrequent requirement of data being added.
 
---

## Database ADR

Decision record for the underlying database technology selected to support the project. When selecting the intended technology it is important to remember the proposed schema is heavily relational and the project has a requirement to run on Linux based systems with the desire to have the option to scale in support of 2.5 million unique users. The technology must also be free for commercial use.

!!! success "**Outcome**"

    - **PostgreSQL**
        - A relational database technology that is ACID compliant with a rich ecosystem. Meeting all the project requirements and offering extensible features like JSONB and support for complex relationships.

??? abstract "**Alternatives**"

    1. MySQL
        - The second runner. Again a relational database technology with a broad ecosystem that suits applications with moderate complexity and offers a slightly lower barrier to entry that PostgreSQL and arguably more suited to type of web application being proposed within the project. However, there are potential barriers for commercial use.

    1. MongoDB
        - A NoSQL database. As the projects data will be structured and not hierarchical, where ideally the schema does not change frequently, this is not suitable solution. The most likely database candidate for learning document based databases when the tertiary goal of having the project provide a template for learning new technologies is realized.

    1. CockroachDB
        - A distributed SQL database that combines scalability of NoSQL with the consistency and relational capabilities of PostgreSQL. A strong candidate if PostgreSQL becomes a blocker to project scalability.