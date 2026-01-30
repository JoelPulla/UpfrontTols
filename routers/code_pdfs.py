from fastapi import APIRouter

app = APIRouter()


@app.get("/pdf")
def get_code_pdfs():
    return {"message": "Pronto veremos mas herramientas"}


app.get("/pdf/mergepdfs")


async def merge_pdfs():
    return {"message": "Aqui se podran unir PDFs"}
