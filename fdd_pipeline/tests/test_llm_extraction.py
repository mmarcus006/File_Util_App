# fdd_pipeline/llm_extraction/tests/test_extractor.py
import json, pathlib, builtins, types
import pytest
from pydantic import BaseModel
from fdd_pipeline.llm_extraction import extractor
# fdd_pipeline/llm_extraction/tests/test_extractor.py
monkeypatch.setattr(extractor.client, "call_openrouter", _fake_call)

class _Dummy(BaseModel):
    foo: int
    bar: str

@pytest.fixture(autouse=True)
def monkey_openrouter(monkeypatch):
    """Patch call_openrouter to avoid network I/O."""
    def _fake_call(*_, **__):
        return {"foo": 1, "bar": "ok"}
    monkeypatch.setattr(extractor.client, "call_openrouter", _fake_call)

def test_extract_roundtrip(tmp_path):
    fake_pdf = tmp_path / "dummy.pdf"
    fake_pdf.write_bytes(b"%PDF-1.3\n%…")           # minimal stub
    out_json = tmp_path / "out.json"

    obj = extractor.extract(fake_pdf, _Dummy, out_json_path=out_json)
    assert obj.foo == 1 and obj.bar == "ok"
    saved = json.loads(out_json.read_text())
    assert saved == obj.model_dump()
