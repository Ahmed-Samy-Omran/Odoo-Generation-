import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from app.models.schemas import GeneratorPayload

load_dotenv()


class AIService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def analyze_requirements(self, user_prompt: str) -> GeneratorPayload:
        prompt = f"""You are an expert Odoo module developer. Your task is to analyze user requirements and generate a JSON configuration for one or more Odoo modules. The JSON should strictly adhere to the following Pydantic schema. Do not include any additional text or formatting outside of the JSON object. Ensure all required fields are present and types are correct.

### SYSTEM CAPABILITIES & RULES TO ENFORCE IN JSON:
1. MULTI-MODULE: The root of the JSON is a list of modules. If the user request is huge or naturally splits into parts, generate multiple modules and handle dependencies via "depends".
2. INHERITANCE (CUSTOMIZATION): If the user wants to modify an existing module (e.g., "add a field to sales"), set "is_customization": true, fill "inherit_model" (e.g., "sale.order"), and for models, use the exact core model name (e.g., "sale.order") and set "is_inherited": true.
3. COMPUTE FIELDS: If a field value depends on other fields (e.g., Total = Price * Qty), set its "type" to its raw type, "is_compute": true, and provide the exact single-line or multi-line python code for the compute logic in "compute_code" using standard Odoo 17 @api.depends syntax. Also, list all dependent fields in "depends_fields".
4. ADVANCED VIEWS: Generate "views_supported". Always evaluate if the model benefits from "kanban", "calendar", or "dashboard". If yes, set them to true and provide configurations (like color fields, date fields for calendar, etc.).
5. PRINT REPORTS (QWEB): If the user requests printable documents, invoices, or summary sheets (e.g., "I want a print button", "printable invoice", "report pdf"), evaluate which models need a print button. Set "enabled": true under "print_reports", and provide the "report_name", "report_label", "report_type" (default to "qweb-pdf"), "model", and a list of fields to include in the printed QWeb PDF layout.
6. ADVANCED SECURITY: Define user groups ("security_groups"). Instead of full access, split permissions logically (e.g., Manager: read/write/create/unlink, User: read/write). Define `AccessRuleModel` for each group and model.
7. GIT DEPLOYMENT: Read the user's deployment preference. If they want to push to github, set "git_deploy_target": "github", otherwise "local_zip".

### CRITICAL ODOO SYNTAX RULES (FOR ACCURATE CODE GENERATION):
- NO LITERAL "None" STRINGS: Never set a field's "label" or any text parameter to the string "None" or null. Always generate a clear, professional, human-readable English label (e.g., Use "Patient Name" or "Age" or "Doctor").
- STRICT SELECTION FIELDS: If a field "type" is set to "selection", you MUST explicitly define a list of options inside the configuration (e.g., for gender: [["male", "Male"], ["female", "Female"]]). If the user doesn't provide options, infer standard logical ones or fallback to a "char" type.
- STABLE COMPUTE CODE: Inside "compute_code", ensure the python code block has correct logic, loops through `for rec in self:`, and relies strictly on the fields mentioned in `@api.depends()`.

Schema Definition:
{GeneratorPayload.model_json_schema()}

User Request: {user_prompt}

Generate the JSON configuration for the Odoo modules based on the user's request. Focus on extracting modules, models, fields, their types, labels, and any relations. If the user mentions filters or group_by options for a search view, include them. If tree_view_fields or form_view_fields are not explicitly mentioned, you can infer them from the defined fields. For actions and menus, create sensible defaults based on the models. The module name should be lowercase and use underscores for spaces. Model names should be in the format 'module_name.model_name'.

Example for 'I need to add a nickname to res.partner':
```json
{{
  "modules": [
    {{
      "module_name": "partner_nickname",
      "module_description": "Adds nickname to partners",
      "depends": ["base"],
      "models": [
        {{
          "name": "res.partner",
          "description": "Partner with nickname",
          "is_inherit": true,
          "inherit_model": "res.partner",
          "is_customization": true,
          "fields": [
            {{"name": "x_nickname", "type": "char", "label": "Nickname"}}
          ]
        }}
      ]
    }}
  ]
}}
```
"""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=64,
                max_output_tokens=8192,
                response_mime_type="application/json",
            ),
        )

        try:
            json_response = json.loads(response.text)
            validated_config = GeneratorPayload(**json_response)
            return validated_config
        except json.JSONDecodeError as e:
            raise ValueError(f"AI response was not valid JSON: {e}\nResponse: {response.text}")
        except Exception as e:
            raise ValueError(f"AI response did not match schema: {e}\nResponse: {response.text}")
