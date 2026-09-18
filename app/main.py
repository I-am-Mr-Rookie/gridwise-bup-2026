from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas import OptimizeRequest


app = FastAPI(title="GridWise")


@app.exception_handler(RequestValidationError)
async def invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": jsonable_encoder(exc.errors())})


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/optimize-energy")
async def optimize_energy(_: OptimizeRequest) -> None:
    raise HTTPException(status_code=500, detail="Optimization is not available until solver integration.")
