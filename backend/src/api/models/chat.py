from pydantic import BaseModel
from typing import Optional

class ChatMessage(BaseModel):
    content: str
    model: Optional[str] = "gpt-3.5-turbo" 