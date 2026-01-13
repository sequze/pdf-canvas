from pydantic import BaseModel


class CreateTaskRequest(BaseModel):
    data: str


class StylesResponse(BaseModel):
    styles: list[str]
