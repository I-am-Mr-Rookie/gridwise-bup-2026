import asyncio

import pytest

from app import llm

from app.directives import InvalidDirectiveError, validate_directives
from app.schemas import OptimizeRequest
from tests.test_main import valid_request


def test_directive_guardrails_normalize_exact_shape() -> None:
    request = OptimizeRequest.model_validate(valid_request())
    raw = {"interpretations": [{
        "note_index": 0,
        "applies": True,
        "directive_type": "solar_reduction",
        "structured_adjustment": {
            "hours": [12, 13], "factor": 0.25, "minimum_energy_kwh": None, "max_grid_kwh": None
        },
        "explanation": "Panel cleaning reduces usable solar.",
    }]}
    result = validate_directives(raw, request)
    assert result[0]["structured_adjustment"] == {"hours": [12, 13], "factor": 0.25}


def test_directive_guardrails_reject_bad_mapping() -> None:
    request = OptimizeRequest.model_validate(valid_request())
    raw = {"interpretations": [{
        "note_index": 1,
        "applies": False,
        "directive_type": "no_op",
        "structured_adjustment": None,
        "explanation": "Irrelevant.",
    }]}
    with pytest.raises(InvalidDirectiveError):
        validate_directives(raw, request)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"choices": []},
        {"choices": [{"message": {"content": "not json"}}]},
        {"choices": [{"message": {"content": '{"interpretations": []}'}}]},
    ],
)
def test_malformed_provider_output_fails_safely(monkeypatch, payload) -> None:
    class Response:
        def raise_for_status(self) -> None:
            pass

        def json(self):
            return payload

    async def post(*_, **__):
        return Response()

    monkeypatch.setenv("MERGE_API_KEY", "PRIVATE_KEY_SENTINEL")
    monkeypatch.setattr(llm.httpx.AsyncClient, "post", post)
    with pytest.raises(llm.LLMError, match="failed safely") as error:
        asyncio.run(llm.interpret_directives(OptimizeRequest.model_validate(valid_request())))
    assert "PRIVATE_KEY_SENTINEL" not in str(error.value)
