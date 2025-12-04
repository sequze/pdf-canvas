import markdown
from playwright.async_api import async_playwright
import aiofiles

from src.config import settings


class PdfConverter:
    def __init__(self):
        pass

    @staticmethod
    async def _read_file(file_path: str):
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                return await f.read()
        except FileNotFoundError:
            raise

    @classmethod
    async def _get_style(cls, style: str):
        # Get style file path from settings
        style_file_path = settings.md.css_files.get(style, None)

        # Return style if provided
        if style_file_path:
            return await cls._read_file(style_file_path)
        return ""

    def _build_html(self, html_body: str, style_body: str):
        return f"""<!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>Markdown to HTML</title>
            <style>
            {style_body}
            </style>
        </head>
        <body>
        {html_body}
        </body>
        </html>
        """

    async def convert_to_html(self, md_text: str, style_type: str) -> str:
        html_body = markdown.markdown(
            md_text, extensions=["fenced_code", "tables", "toc", "codehilite"]
        )
        style = await self._get_style(style_type)
        html = self._build_html(html_body, style)
        return html

    async def convert_html_to_pdf(self, html: str, output_path: str) -> None:
        """
        Convert HTML string to PDF file using Playwright and save.
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()

                # Set HTML content
                await page.set_content(html)

                # Generate PDF with specified options
                await page.pdf(
                    path=output_path,
                    format="A4",
                    print_background=True,
                    margin={
                        "top": "20mm",
                        "right": "20mm",
                        "bottom": "20mm",
                        "left": "20mm",
                    },
                )

                await browser.close()
        except Exception as e:
            print(f"Error converting HTML to PDF: {e}")
            raise

    async def convert_file_to_pdf(
        self, text: str, output_path: str, style_type: str = "default"
    ) -> None:
        """
        Convert Markdown to PDF.
        """
        try:
            html_text = await self.convert_to_html(text, style_type)
            await self.convert_html_to_pdf(html_text, output_path)
        except FileNotFoundError:
            print("File not found")
            raise
        except Exception as e:
            print(f"Error converting file to PDF: {e}")
            raise
