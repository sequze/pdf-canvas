from pydantic import BaseModel


class Token(BaseModel):
    """Auth token schema"""
    access_token: str
    refresh_token: str
    type: str = "Bearer"

