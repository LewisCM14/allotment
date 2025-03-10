## Useful Commands

Launch the Service (In Development Mode)
```
fastapi dev
```

Linting
```
ruff check --select I --fix
```

Formatting
```
ruff format
```

---

## Repository Layout

Backend Entrypoint
```
api/main.py
```

Backend Configuration
```
api/v1/core/
```

Backend SQLALchemy ORM Models
```
api/v1/models/
```

Backend Data Access Layer
```
api/v1/repositories/
```

Backend Pydantic Schemas
```
api/v1/schemas/
```

Backend Business Logic Layer
```
api/v1/services/
```

Backend Endpoints
```
api/v1/<ENDPOINT>
```
___