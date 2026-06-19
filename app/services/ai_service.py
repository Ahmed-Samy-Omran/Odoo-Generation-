import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from app.models.schemas import ModuleConfig

load_dotenv()


class AIService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
        )

    def analyze_requirements(self, user_prompt: str) -> ModuleConfig:
        prompt = f"""You are an expert Odoo module developer. Your task is to analyze user requirements and generate a JSON configuration for an Odoo module. The JSON should strictly adhere to the following Pydantic schema. Do not include any additional text or formatting outside of the JSON object. Ensure all required fields are present and types are correct.

Schema Definition:
{ModuleConfig.model_json_schema()}

User Request: {user_prompt}

Generate the JSON configuration for the Odoo module based on the user's request. Focus on extracting models, fields, their types, labels, and any relations. If the user mentions filters or group_by options for a search view, include them. If tree_view_fields or form_view_fields are not explicitly mentioned, you can infer them from the defined fields. For actions and menus, create sensible defaults based on the models. The module name should be lowercase and use underscores for spaces. Model names should be in the format 'module_name.model_name'.

Example for 'I need a Hospital Management System with patients and doctors':
```json
{{
  "module_name": "hospital_management",
  "module_description": "Module for managing hospital patients and doctors",
  "models": [
    {{
      "name": "hospital_management.patient",
      "description": "Patient Records",
      "rec_name": "name",
      "fields": [
        {{"name": "name", "type": "char", "label": "Patient Name", "required": true}},
        {{"name": "age", "type": "integer", "label": "Age"}},
        {{"name": "doctor_id", "type": "many2one", "label": "Primary Doctor", "relation": "hospital_management.doctor"}}
      ],
      "tree_view_fields": ["name", "age", "doctor_id"],
      "form_view_fields": ["name", "age", "doctor_id"]
    }},
    {{
      "name": "hospital_management.doctor",
      "description": "Doctor Records",
      "rec_name": "name",
      "fields": [
        {{"name": "name", "type": "char", "label": "Doctor Name", "required": true}},
        {{"name": "specialty", "type": "char", "label": "Specialty"}}
      ],
      "tree_view_fields": ["name", "specialty"],
      "form_view_fields": ["name", "specialty"]
    }}
  ],
  "actions": [
    {{
      "name": "Patients",
      "res_model": "hospital_management.patient",
      "view_mode": "tree,form",
      "help_text": "Manage hospital patients"
    }},
    {{
      "name": "Doctors",
      "res_model": "hospital_management.doctor",
      "view_mode": "tree,form",
      "help_text": "Manage hospital doctors"
    }}
  ],
  "menus": [
    {{
      "name": "Hospital Management",
      "sequence": 10
    }},
    {{
      "name": "Patients",
      "parent_xml_id": "hospital_management.menu_hospital_management_menu",
      "action_xml_id": "hospital_management.patients_action",
      "sequence": 10
    }},
    {{
      "name": "Doctors",
      "parent_xml_id": "hospital_management.menu_hospital_management_menu",
      "action_xml_id": "hospital_management.doctors_action",
      "sequence": 20
    }}
  ]
}}
```
"""
        convo = self.model.start_chat(history=[])
        response = convo.send_message(prompt)

        # Parse the JSON response and validate with Pydantic
        try:
            json_response = json.loads(response.text)
            validated_config = ModuleConfig(**json_response)
            return validated_config
        except json.JSONDecodeError as e:
            raise ValueError(f"AI response was not valid JSON: {e}\nResponse: {response.text}")
        except Exception as e:
            raise ValueError(f"AI response did not match schema: {e}\nResponse: {response.text}")

