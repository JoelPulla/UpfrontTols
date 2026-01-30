import re, io, zipfile
from fastapi import APIRouter, UploadFile, HTTPException, File
from fastapi.responses import StreamingResponse
from PyPDF2 import PdfReader, PdfWriter


app = APIRouter()


@app.get("/pdf")
def get_code_pdfs():
    return {"message": "Pronto veremos mas herramientas"}


PATRON_FACTURA = re.compile(r"F-(\d+)\sAPL-(\d+)", re.IGNORECASE)
PATRON_ANEXO = re.compile(r"ANX-(\d+)\sAPL-(\d+)", re.IGNORECASE)


@app.post("/pdf/merge_pdfs/")
async def merge_pdfs(files: list[UploadFile] = File(...)):

    if len(files) < 2:
        raise HTTPException(400, "Se requieren al menos 2 archivos PDF.")

    documentos = {}
    reporte = {}

    # --------------------------------------
    # PROCESAR ARCHIVOS
    # --------------------------------------
    for f in files:
        nombre = f.filename

        if not nombre.lower().endswith(".pdf"):
            continue

        m1 = PATRON_FACTURA.search(nombre)
        m2 = PATRON_ANEXO.search(nombre)

        if not m1 and not m2:
            continue

        contenido = await f.read()

        if m1:
            num_factura, apl = m1.groups()
            documentos.setdefault(
                apl,
                {
                    "factura": None,
                    "anexo": None,
                    "num_factura": None,
                    "num_anexo": None,
                },
            )
            documentos[apl]["factura"] = contenido
            documentos[apl]["num_factura"] = num_factura

        elif m2:
            num_anexo, apl = m2.groups()
            documentos.setdefault(
                apl,
                {
                    "factura": None,
                    "anexo": None,
                    "num_factura": None,
                    "num_anexo": None,
                },
            )
            documentos[apl]["anexo"] = contenido
            documentos[apl]["num_anexo"] = num_anexo

    # --------------------------------------
    # CREAR ZIP EN MEMORIA
    # --------------------------------------
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:

        for apl, data in documentos.items():

            factura = data["factura"]
            anexo = data["anexo"]
            nf = data["num_factura"]
            na = data["num_anexo"]
            key = f"APL-{apl}"

            if not factura and not anexo:
                reporte[key] = "❌ No se encontraron ni factura ni anexo"
                continue
            if not factura:
                reporte[key] = f"❌ Falta FACTURA para ANX-{na}"
                continue
            if not anexo:
                reporte[key] = f"❌ Falta ANEXO para factura F-{nf}"
                continue

            # Unir PDFs en el mismo bloque por simplicidad
            writer = PdfWriter()

            for pdf_bytes in (factura, anexo):
                reader = PdfReader(io.BytesIO(pdf_bytes))
                for p in reader.pages:
                    writer.add_page(p)

            pdf_output = io.BytesIO()
            writer.write(pdf_output)
            pdf_output.seek(0)

            z.writestr(f"ANX-{na} APL-{apl}.pdf", pdf_output.read())
            reporte[key] = "✔ Unión completada"

    zip_buffer.seek(0)

    # --------------------------------------
    # RETORNAR ZIP COMO DESCARGA
    # --------------------------------------
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=pdfs_unidos.zip"},
    )
