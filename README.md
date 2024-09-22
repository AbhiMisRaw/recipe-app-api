## Recipe REST-API

This project is a fully-featured **API** that allows users to **register** and **log in** with secure **Token authentication**. Once authenticated, users can **list**, **add**, **update**, and **delete recipes**. Each recipe can have multiple **tags** and **ingredients**, offering flexible categorization. The API follows **Test-Driven Development (TDD)**, meaning that **test cases** are written before implementing any feature to ensure code quality and maintainability.

---

### Features

- User Authentication:

  - User registration and login APIs with JWT-based authentication for secure access.

- Recipe Management:

  - Users can list, add, update, and delete recipes with detailed information.

- Tag and Ingredient Management:

  - Recipes support multiple tags and ingredients, allowing users to categorize and customize them as needed.

- Test-Driven Development (TDD):
  - All APIs are built following Test-Driven Development principles. Test cases are written before the implementation of each feature to ensure high code quality and maintainability.

---

### Tech Stack

- **Backend**: Django, Django-Rest-Framework
- **Database**: Postgres
- **Tools**: Docker & Docker-Compose , Swagger, Google Chrome

---

### Local Installation

1. create a directory and move to newwly created directory

```shell
mkdir recipe-app
cd recipe-app
```

2. Make an virtual environment and enable the virtual environment

```shell
# for windows
# creating virtual environment
python -m venv venv

# for linux or unix machine
# creating virtual environment
python3 -m venv venv
```

3. Clone the project

```bash
  git clone https://github.com/AbhiMisRaw/recipe-app-api.git
```

4. Activate virtual environment.

```shell
# activating virtual environment
venv\Script\activate

# activating virtual environment
source venv/bin/activate
```

5. Go to the cloned project directory

```bash
  cd recipe-app-api
```

6. Install dependencies

```bash
  pip install -r requirements.txt
```

7. Create `.env` file and create `SECRET_KEY` for project.

```shell
echo DJANGO_SECRET_KEY='<ANY-SECRET-KEY>' > .env
```

8. Run migrations

```bash
  python manage.py makemigrations
  python manage.py migrate
```

9. Start the server

```bash
    # for windows
    python manage.py runserver

    # for linux and unix machine
    python3 manage.py runserver
```

---

### API_Endpoints

Here's a table that outlines the API endpoints from both the root project and the `recipe` and `user` apps in a clear, readable format:

| **Endpoint**   | **HTTP Method** | **Description**                |
| -------------- | --------------- | ------------------------------ |
| `/admin/`      | GET             | Django Admin Panel             |
| `/api/schema/` | GET             | API Schema (OpenAPI)           |
| `/api/docs/`   | GET             | API Documentation (Swagger UI) |

### User API Endpoints (`/api/users/`)

| **Endpoint**         | **HTTP Method** | **Description**                       |
| -------------------- | --------------- | ------------------------------------- |
| `/api/users/create/` | POST            | Create a new user                     |
| `/api/users/token/`  | POST            | Generate a new authentication token   |
| `/api/users/me/`     | GET/PUT         | Get or update authenticated user info |

### Recipe API Endpoints (`/api/recipe/`)

| **Endpoint**                    | **HTTP Method** | **Description**                           |
| ------------------------------- | --------------- | ----------------------------------------- |
| `/api/recipe/recipes/`          | GET             | List all recipes                          |
| `/api/recipe/recipes/`          | POST            | Create a new recipe                       |
| `/api/recipe/recipes/{id}/`     | GET             | Retrieve a specific recipe                |
| `/api/recipe/recipes/{id}/`     | PUT             | Update a specific recipe                  |
| `/api/recipe/recipes/{id}/`     | DELETE          | Delete a specific recipe                  |
| `/api/recipe/tags/`             | GET             | List all tags                             |
| `/api/recipe/tags/`             | POST            | Create a new tag                          |
| `/api/recipe/tags/{id}/`        | GET/PUT/DELETE  | Retrieve, update, or delete a tag         |
| `/api/recipe/ingredients/`      | GET             | List all ingredients                      |
| `/api/recipe/ingredients/`      | POST            | Create a new ingredient                   |
| `/api/recipe/ingredients/{id}/` | GET/PUT/DELETE  | Retrieve, update, or delete an ingredient |

This format breaks down each API endpoint, HTTP method, and its purpose, making it easier to understand and navigate.
