
# Example

``` shell
uv sync --all-groups --all-extras
uv run uvicorn example.main:app --host 0.0.0.0 --port 8082 --reload
```

Docs:
`http://0.0.0.0:8082/docs`
`http://0.0.0.0:8082/redoc`
`http://0.0.0.0:8082/scalar`

Tests:
``` shell
uv run pytest
```

``` shell
from auth_models.db.models import User
from app.database import auth_db

async with auth_db.async_session() as session:
    user = User(
        username='admin',
        password='admin',
        email="admin@admin.com",
        is_admin=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    user
```
