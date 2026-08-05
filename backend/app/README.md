# Backend architecture

The backend is a modular monolith with one-way dependencies:

```text
api -> application -> domain <- infrastructure
             ^                    |
             +---- container -----+
```

- `api` owns HTTP routing and Pydantic transport schemas.
- `application` owns use-case orchestration.
- `domain` owns framework-independent ports and errors.
- `infrastructure` adapts LlamaIndex and file-based persistence.
- `container.py` is the only composition root allowed to wire concrete adapters.

The domain and application packages must not import FastAPI, LlamaIndex, database drivers, or concrete storage implementations.
