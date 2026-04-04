import subprocess
from os import environ
from pathlib import Path
from tempfile import TemporaryDirectory

from app.models.schema import Presentation
from app.services.marp_service import MarpService
from app.services.pptx_service import PptxService


class ExportError(Exception):
    pass


class ExportService:
    def __init__(
        self,
        marp_service: MarpService,
        pptx_service: PptxService,
        marp_cli_path: str,
        chrome_path: str | None = None,
        marp_timeout_seconds: float = 60.0,
    ) -> None:
        self.marp_service = marp_service
        self.pptx_service = pptx_service
        self.marp_cli_path = marp_cli_path
        self.chrome_path = chrome_path
        self.marp_timeout_seconds = marp_timeout_seconds

    def export_markdown(self, presentation: Presentation) -> str:
        return self.marp_service.render_markdown(presentation)

    def export_pdf(self, presentation: Presentation) -> bytes:
        markdown = self.export_markdown(presentation)
        with TemporaryDirectory(prefix="slide_app_marp_") as temp_dir:
            temp_path = Path(temp_dir)
            markdown_path = temp_path / "presentation.md"
            pdf_path = temp_path / "presentation.pdf"
            try:
                markdown_path.write_text(markdown, encoding="utf-8")
            except OSError as exc:
                raise ExportError("Failed to write temporary Marp markdown file") from exc

            try:
                command = [
                    self.marp_cli_path,
                    str(markdown_path),
                    "--pdf",
                    "--output",
                    str(pdf_path),
                ]
                env = dict(environ)
                if self.chrome_path:
                    command.extend(["--browser-path", self.chrome_path])
                    env["CHROME_PATH"] = self.chrome_path
                    env["PUPPETEER_EXECUTABLE_PATH"] = self.chrome_path
                completed = subprocess.run(
                    command,
                    check=False,
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=self.marp_timeout_seconds,
                )
            except FileNotFoundError as exc:
                raise ExportError(
                    f"Marp CLI was not found. marp_cli_path={self.marp_cli_path}"
                ) from exc
            except subprocess.TimeoutExpired as exc:
                raise ExportError(
                    f"Marp CLI timed out after {self.marp_timeout_seconds:.0f}s"
                ) from exc
            except OSError as exc:
                raise ExportError(
                    f"Failed to execute Marp CLI. marp_cli_path={self.marp_cli_path}"
                ) from exc

            if completed.returncode != 0:
                stderr = completed.stderr.strip()
                stdout = completed.stdout.strip()
                details = stderr or stdout or "No Marp CLI output"
                raise ExportError(
                    f"Marp CLI failed with exit code {completed.returncode}. details={details}"
                )

            if not pdf_path.exists():
                raise ExportError("Marp CLI completed without creating a PDF file")

            try:
                return pdf_path.read_bytes()
            except OSError as exc:
                raise ExportError("Failed to read generated PDF file") from exc

    def export_pptx(self, presentation: Presentation) -> bytes:
        try:
            return self.pptx_service.render_pptx(presentation)
        except Exception as exc:
            raise ExportError("Failed to generate PPTX file") from exc
