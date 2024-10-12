from fastapi import FastAPI

from routers import (
    auth,
    user,
)


app = FastAPI(
    openapi_prefix="/api"
)


app.include_router(auth.router)
app.include_router(user.router)
