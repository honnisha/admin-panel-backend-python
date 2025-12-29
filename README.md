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
