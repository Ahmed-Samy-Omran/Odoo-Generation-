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

If the user request is huge or naturally splits into parts, generate multiple modules and handle dependencies via the "depends" field.

Inheritance Logic:
- If the requirement is to extend an existing Odoo model (e.g., res.partner, sale.order), set "is_inherit" to true and "inherit_model" to the name of the model being extended.
- If it's a customization (adding fields to an existing model without creating a new one), set "is_customization" to true. In this case, "name" should be the same as "inherit_model".
- If "is_inherit" is true but "is_customization" is false, it means you are creating a new model that inherits from an existing one (classical inheritance).

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
