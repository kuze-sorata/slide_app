import subprocess

import pytest
from fastapi import HTTPException

from app.models.schema import Presentation
from app.routes.export import export_marp_markdown, export_pdf, export_pptx
from app.services.export_service import ExportError, ExportService
from app.services.marp_service import MarpService
from app.services.pptx_service import PptxService


def sample_presentation() -> Presentation:
    return Presentation.model_validate(
        {
            "deck_title": "営業進捗の共有",
            "slides": [
                {
                    "id": "slide-1",
                    "type": "title",
                    "title": "営業進捗の共有",
                    "bullets": ["部長向け共有"],
                    "layout": "layout1",
                },
                {
                    "id": "slide-2",
                    "type": "content",
                    "title": "重点案件の停滞が課題",
                    "bullets": ["受注見込みが後ろ倒し"],
                    "layout": "layout2",
                },
                {
                    "id": "slide-3",
                    "type": "summary",
                    "title": "優先案件の再整理が必要",
                    "bullets": ["案件優先度を見直す"],
                    "layout": "layout4",
                },
            ],
        }
    )


def test_export_service_raises_when_marp_cli_is_missing() -> None:
    service = ExportService(
        marp_service=MarpService(),
        pptx_service=PptxService(),
        marp_cli_path="missing-marp",
    )

    with pytest.raises(ExportError):
        service.export_pdf(sample_presentation())


def test_export_service_returns_pdf_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    service = ExportService(
        marp_service=MarpService(),
        pptx_service=PptxService(),
        marp_cli_path="marp",
        chrome_path="/tmp/fake-chrome",
    )

    def fake_run(
        args: list[str],
        check: bool,
        capture_output: bool,
        text: bool,
        env: dict[str, str],
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        output_index = args.index("--output") + 1
        output_path = args[output_index]
        assert "--browser-path" in args
        assert env["CHROME_PATH"] == "/tmp/fake-chrome"
        assert env["PUPPETEER_EXECUTABLE_PATH"] == "/tmp/fake-chrome"
        assert timeout == 60.0
        with open(output_path, "wb") as fh:
            fh.write(b"%PDF-1.4 fake")
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    pdf_bytes = service.export_pdf(sample_presentation())

    assert pdf_bytes.startswith(b"%PDF-1.4")


def test_export_service_raises_when_marp_cli_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    service = ExportService(
        marp_service=MarpService(),
        pptx_service=PptxService(),
        marp_cli_path="marp",
    )

    def fake_run(
        args: list[str],
        check: bool,
        capture_output: bool,
        text: bool,
        env: dict[str, str],
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args,
            returncode=1,
            stdout="",
            stderr="render failed",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(ExportError, match="render failed"):
        service.export_pdf(sample_presentation())


@pytest.mark.asyncio
async def test_export_marp_endpoint_returns_markdown() -> None:
    service = ExportService(
        marp_service=MarpService(),
        pptx_service=PptxService(),
        marp_cli_path="marp",
    )
    response = await export_marp_markdown(sample_presentation(), service)

    assert response.status_code == 200
    assert response.media_type == "text/markdown"
    assert "# 営業進捗の共有" in response.body.decode("utf-8")


@pytest.mark.asyncio
async def test_export_pdf_endpoint_returns_pdf() -> None:
    class StubExportService:
        def export_markdown(self, presentation: Presentation) -> str:
            return ""

        def export_pdf(self, presentation: Presentation) -> bytes:
            return b"%PDF-1.4 fake"

        def export_pptx(self, presentation: Presentation) -> bytes:
            return b"PK fake"

    response = await export_pdf(sample_presentation(), StubExportService())

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.body.startswith(b"%PDF-1.4")


@pytest.mark.asyncio
async def test_export_pdf_endpoint_returns_500_on_export_error() -> None:
    class FailingExportService:
        def export_markdown(self, presentation: Presentation) -> str:
            raise ExportError("unused")

        def export_pdf(self, presentation: Presentation) -> bytes:
            raise ExportError("Marp CLI failed")

        def export_pptx(self, presentation: Presentation) -> bytes:
            raise ExportError("unused")

    with pytest.raises(HTTPException) as exc_info:
        await export_pdf(sample_presentation(), FailingExportService())

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Marp CLI failed"


def test_export_service_returns_pptx_bytes() -> None:
    service = ExportService(
        marp_service=MarpService(),
        pptx_service=PptxService(),
        marp_cli_path="marp",
    )

    pptx_bytes = service.export_pptx(sample_presentation())

    assert pptx_bytes.startswith(b"PK")


@pytest.mark.asyncio
async def test_export_pptx_endpoint_returns_pptx() -> None:
    class StubExportService:
        def export_markdown(self, presentation: Presentation) -> str:
            return ""

        def export_pdf(self, presentation: Presentation) -> bytes:
            return b"%PDF-1.4 fake"

        def export_pptx(self, presentation: Presentation) -> bytes:
            return b"PK fake"

    response = await export_pptx(sample_presentation(), StubExportService())

    assert response.status_code == 200
    assert response.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    assert response.body.startswith(b"PK")
