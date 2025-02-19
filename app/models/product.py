from pydantic import BaseModel
from typing import List, Optional, Dict

class Size(BaseModel):
    value: str
    price: float

class Color(BaseModel):
    name: str
    mockupFront: Optional[str]
    mockupBack: Optional[str]

class ProductCreate(BaseModel):
    title: str
    ai_prompt: str
    sizes: List[Size]
    colors: List[Color]
    description: Optional[str] = "" 