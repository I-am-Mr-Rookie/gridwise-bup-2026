from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.checker import assert_valid_plan
from app.llm import LLMError, interpret_directives
from app.schemas import OptimizeRequest
from app.solver import InfeasibleScheduleError, solve


app = FastAPI(title="GridWise")


@app.exception_handler(RequestValidationError)
async def invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
    # Do not echo input/context: either may contain non-finite numbers or secrets.
    errors = [{key: error[key] for key in ("loc", "msg", "type")} for error in exc.errors()]
    return JSONResponse(status_code=400, content={"detail": errors})


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/optimize-energy")
async def optimize_energy(request: OptimizeRequest) -> dict:
    try:
        directives = await interpret_directives(request)
        response = await run_in_threadpool(solve, request, directives)
        response["directive_interpretation"] = directives
        assert_valid_plan(request, directives, response)
        return response
    except LLMError as exc:
        raise HTTPException(status_code=500, detail="LLM directive interpretation failed safely.") from exc
    except InfeasibleScheduleError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Optimization failed safely.") from exc
