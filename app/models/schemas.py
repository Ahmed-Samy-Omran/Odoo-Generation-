from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class FieldModel(BaseModel):
    name: str
    type: str
    label: Optional[str] = None
    required: Optional[bool] = False
    relation: Optional[str] = None
    inverse_name: Optional[str] = None
    relation_table: Optional[str] = None
    selection_options: Optional[List[List[str]]] = None # For selection fields

class FilterModel(BaseModel):
    name: str
    string: str
    domain: Optional[str] = None # Odoo domain as a string

class GroupByModel(BaseModel):
    name: str
    string: str

class SearchViewModel(BaseModel):
    name: str
    fields: Optional[List[str]] = None # List of field names to include in search
    filters: Optional[List[FilterModel]] = None
    group_by: Optional[List[GroupByModel]] = None

class ActionModel(BaseModel):
    name: str
    res_model: str
    view_mode: str = "tree,form"
    domain: Optional[str] = None
    help_text: Optional[str] = None

class MenuModel(BaseModel):
    name: str
    sequence: Optional[int] = 10
    action_xml_id: Optional[str] = None # XML ID of the action to link
    parent_xml_id: Optional[str] = None # XML ID of the parent menu

class ModelDefinition(BaseModel):
    name: str
    description: Optional[str] = ""
    rec_name: Optional[str] = None
    fields: List[FieldModel]
    search_view: Optional[SearchViewModel] = None
    tree_view_fields: Optional[List[str]] = None # Fields to display in tree view
    form_view_fields: Optional[List[str]] = None # Fields to display in form view

class ModuleConfig(BaseModel):
    module_name: str
    module_description: Optional[str] = ""
    depends: Optional[List[str]] = ["base"]
    models: List[ModelDefinition]
    actions: Optional[List[ActionModel]] = None
    menus: Optional[List[MenuModel]] = None

class GeneratorPayload(BaseModel):
    modules: List[ModuleConfig]
