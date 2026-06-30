from typing import List, Optional, Dict, Any, Literal
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
    is_compute: Optional[bool] = False
    compute_code: Optional[str] = None
    depends_fields: Optional[List[str]] = None # Fields for @api.depends

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

# New models for Advanced Views
class KanbanViewModel(BaseModel):
    default_group_by: Optional[str] = None
    color_field: Optional[str] = None

class CalendarViewModel(BaseModel):
    date_start: str
    date_stop: Optional[str] = None
    date_delay: Optional[str] = None
    all_day: Optional[str] = None
    color: Optional[str] = None

class DashboardViewModel(BaseModel):
    # Dashboards are usually more custom, so this might be simpler initially
    pass

# New model for Print Reports
class PrintReportModel(BaseModel):
    report_name: str
    report_label: str
    report_type: Literal["qweb-pdf", "qweb-html"] = "qweb-pdf"
    model: str # The model this report is for
    fields: Optional[List[str]] = None # Fields to include in the report layout

# New models for Advanced Security
class AccessRuleModel(BaseModel):
    model_name: str
    perm_read: Optional[bool] = True
    perm_write: Optional[bool] = True
    perm_create: Optional[bool] = True
    perm_unlink: Optional[bool] = True

class SecurityGroupModel(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = "Access/" # e.g., 'Access/Sales' or 'Access/Human Resources'
    implied_ids: Optional[List[str]] = None # List of other group XML IDs this group implies
    rules: Optional[List[AccessRuleModel]] = None

class ModelDefinition(BaseModel):
    name: str
    description: Optional[str] = ""
    rec_name: Optional[str] = None
    fields: List[FieldModel]
    is_inherit: Optional[bool] = False
    inherit_model: Optional[str] = None # The model to inherit from
    is_customization: Optional[bool] = False # If True, it's a customization of an existing model
    search_view: Optional[SearchViewModel] = None
    tree_view_fields: Optional[List[str]] = None # Fields to display in tree view
    form_view_fields: Optional[List[str]] = None # Fields to display in form view
    # New fields for advanced views
    kanban_view: Optional[KanbanViewModel] = None
    calendar_view: Optional[CalendarViewModel] = None
    dashboard_view: Optional[DashboardViewModel] = None
    # New field for print reports
    print_reports: Optional[List[PrintReportModel]] = None

class ModuleConfig(BaseModel):
    module_name: str
    module_description: Optional[str] = ""
    depends: Optional[List[str]] = ["base"]
    models: List[ModelDefinition]
    actions: Optional[List[ActionModel]] = None
    menus: Optional[List[MenuModel]] = None
    # New field for advanced security
    security_groups: Optional[List[SecurityGroupModel]] = None
    # New field for Git Deployment
    git_deploy_target: Optional[Literal["github", "local_zip"]] = "local_zip"

class GeneratorPayload(BaseModel):
    modules: List[ModuleConfig]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    reply: str
    ready_to_generate: bool = False
    requirements_summary: str = ""
