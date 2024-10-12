from fastapi import FastAPI

from fastapi_pagination import add_pagination

from routers import (
    auth,
    user,
)


app = FastAPI(
    root_path="/api"
)

add_pagination(app)


app.include_router(auth.router)
app.include_router(user.router)
