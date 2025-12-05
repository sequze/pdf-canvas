from pathlib import Path
import openai

from src.config import settings


class PromptHelper:

    @staticmethod
    def read_file(filename: str, encoding: str = "utf-8") -> str:
        path = Path(filename)
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: `{path}`")
        return path.read_text(encoding=encoding)

    @classmethod
    def get_main_prompt(cls):
        return cls.read_file(settings.llm_prompt.prompt_path)


class LLMHelper:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        folder: str,
        model: str,
        instruction: str,
        temperature: float,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.folder = folder
        self.model = model
        self.instruction = instruction
        self.temperature = temperature
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            project=folder,
        )

    async def make_request(self, prompt: str):
        return await self.client.responses.create(
            model=self.model,
            temperature=self.temperature,
            instructions=self.instruction,
            input=prompt,
        )
