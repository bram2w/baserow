from langchain_core.pydantic_v1 import BaseModel, Field


class BaserowFormulaModel(BaseModel):
    formula: str = Field(description="The generated Baserow formula")
