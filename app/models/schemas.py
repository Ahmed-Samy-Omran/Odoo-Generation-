from typing import List, Optional
from pydantic import BaseModel

class FieldModel(BaseModel):
    name: str
    type: str
    label: Optional[str] = None
    required: Optional[bool] = False
    relation: Optional[str] = None
    inverse_name: Optional[str] = None
    relation_table: Optional[str] = None

class ModelDefinition(BaseModel):
    name: str
    description: Optional[str] = ""
    rec_name: Optional[str] = None
    fields: List[FieldModel]

class ModuleConfig(BaseModel):
    module_name: str
    module_description: Optional[str] = ""
    models: List[ModelDefinition]