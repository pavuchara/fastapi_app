from fastapi import FastAPI

from fastapi_pagination import add_pagination

from routers import (
    auth,
    core,
    user,
    recipe,
)


app = FastAPI(
    root_path="/api"
)

add_pagination(app)


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(core.router)
app.include_router(recipe.router)
