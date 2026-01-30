from fastapi import FastAPI
from routers import code_pdfs


app = FastAPI()

app.include_router(
    code_pdfs.app,
)


@app.get("/")
async def read_root():
    return {"Hello": "Hello World"}
