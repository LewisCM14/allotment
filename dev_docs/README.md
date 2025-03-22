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

Type Checking
```
mypy .
```

Start the PostgreSQL Server
```
sudo systemctl start postgresql
```

Open the PostgreSQL Shell
```
psql
```

Autogenerate Alembic Migration
```
alembic revision --autogenerate -m "REVISION MSG"
```