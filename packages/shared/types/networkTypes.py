from typing import Optional, TypedDict
from packages.shared.types.jsonTypes import Content


class InternalResponse(TypedDict):
  success: bool;
  message: str;
  content: Optional[Content]

def makeResponse(success: bool, message: str, content: Optional[Content]) -> InternalResponse:
  return {
    "success": success,
    "message": message,
    "content": content
  }