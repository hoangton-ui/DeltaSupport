from fastapi import FastAPI

from routers import auth, admin, pin, work_schedule

app = FastAPI()


@app.get("/")
def root():
    return {"status": "API OK"}


app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(pin.router)
app.include_router(work_schedule.router)