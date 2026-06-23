# import os
# import json
# import random
# import google.genai.errors
# from google import genai
# from google.genai import types
# from dotenv import load_dotenv
# from app.models.schemas import GeneratorPayload, ModuleConfig
#
# load_dotenv()
#
#
# class AIService:
#     def __init__(self):
#         api_keys_str = os.getenv("GEMINI_API_KEYS")
#         if not api_keys_str:
#             raise ValueError(
#                 "GEMINI_API_KEYS not found in environment variables. Please set it as a comma-separated string.")
#         self.api_keys = [key.strip() for key in api_keys_str.split(',') if key.strip()]
#         if not self.api_keys:
#             raise ValueError("No valid GEMINI_API_KEYS found in environment variables.")
#
#         self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
#
#     def _get_gemini_client(self):
#         # Select an API key randomly or in a round-robin fashion
#         api_key = random.choice(self.api_keys)
#         return genai.Client(api_key=api_key)
#
#     def analyze_requirements(self, user_prompt: str) -> GeneratorPayload:
#         prompt = f"""Act as a senior Odoo developer. Your task is to generate a JSON configuration based on the provided schema. I am using an AI Orchestrator that routes requests through multiple redundant API gateways. Your output must be purely valid JSON, extremely concise, and handle the Odoo syntax constraints provided in the system prompt. Always ensure the output is parseable by json.loads().
#
# ### SYSTEM CAPABILITIES & RULES TO ENFORCE IN JSON:
# 1. MULTI-MODULE: The root of the JSON MUST be an object with a single key, "modules", which is a list of module configurations. If the user request is huge or naturally splits into parts, generate multiple modules within this list and handle dependencies via "depends".
# 2. INHERITANCE (CUSTOMIZATION): If the user wants to modify an existing module (e.g., "add a field to sales"), set "is_customization": true, fill "inherit_model" (e.g., "sale.order"), and for models, use the exact core model name (e.g., "sale.order") and set "is_inherited": true.
# 3. COMPUTE FIELDS: If a field value depends on other fields (e.g., Total = Price * Qty), set its "type" to its raw type, "is_compute": true, and provide the exact single-line or multi-line python code for the compute logic in "compute_code" using standard Odoo 17 @api.depends syntax. Also, list all dependent fields in "depends_fields".
# 4. ADVANCED VIEWS: Generate "views_supported". Always evaluate if the model benefits from "kanban", "calendar", or "dashboard". If yes, set them to true and provide configurations (like color fields, date fields for calendar, etc.).
# 5. PRINT REPORTS (QWEB): If the user requests printable documents, invoices, or summary sheets (e.g., "I want a print button", "printable invoice", "report pdf"), evaluate which models need a print button. Set "enabled": true under "print_reports", and provide the "report_name", "report_label", "report_type" (default to "qweb-pdf"), "model", and a list of fields to include in the printed QWeb PDF layout.
# 6. ADVANCED SECURITY: Define user groups ("security_groups"). Instead of full access, split permissions logically (e.g., Manager: read/write/create/unlink, User: read/write). Define `AccessRuleModel` for each group and model.
# 7. GIT DEPLOYMENT: Read the user\'s deployment preference. If they want to push to github, set "git_deploy_target": "github", otherwise "local_zip".
#
# ### CRITICAL ODOO SYNTAX RULES (FOR ACCURATE CODE GENERATION):
# - NO LITERAL "None" STRINGS: Never set a field\'s "label" or any text parameter to the string "None" or null. Always generate a clear, professional, human-readable English label (e.g., Use "Patient Name" or "Age" or "Doctor").
# - STRICT SELECTION FIELDS: If a field "type" is set to "selection", you MUST explicitly define a list of options inside the configuration (e.g., for gender: [["male", "Male"], ["female", "Female"]]). If the user doesn\'t provide options, infer standard logical ones or fallback to a "char" type.
# - STABLE COMPUTE CODE: Inside "compute_code", ensure the python code block has correct logic, loops through `for rec in self:`, and relies strictly on the fields mentioned in `@api.depends()`.
#
# Schema Definition:
# {GeneratorPayload.model_json_schema()}
#
# User Request: {user_prompt}
#
# Generate the JSON configuration for the Odoo modules based on the user\'s request. Focus on extracting modules, models, fields, their types, labels, and any relations. If the user mentions filters or group_by options for a search view, include them. If tree_view_fields or form_view_fields are not explicitly mentioned, you can infer them from the defined fields. For actions and menus, create sensible defaults based on the models. The module name should be lowercase and use underscores for spaces. Model names should be in the format \'module_name.model_name\'.
# """
#
#         # Retry mechanism for API calls with different keys
#         for _ in range(len(self.api_keys)):
#             try:
#                 client = self._get_gemini_client()
#                 response = client.models.generate_content(
#                     model=self.model_name,
#                     contents=prompt,
#                     config=types.GenerateContentConfig(
#                         temperature=0.7,
#                         top_p=0.95,
#                         top_k=64,
#                         max_output_tokens=8192,
#                         response_mime_type="application/json",
#                     ),
#                 )
#                 break  # If successful, break the retry loop
#             except google.genai.errors.ServerError as e:
#                 print(f"Gemini API Server Error with key: {e.value}. Retrying with another key...")
#                 if _ == len(self.api_keys) - 1:
#                     raise ValueError(f"All Gemini API keys failed: {e.value}\nResponse: {response.text}")
#             except Exception as e:
#                 # Catch other exceptions that are not ServerError and re-raise immediately
#                 raise ValueError(f"An unexpected error occurred during API call: {e}")
#
#         try:
#             json_response = json.loads(response.text)
#             # Check if the AI returned a single module config instead of a GeneratorPayload
#             if isinstance(json_response, dict) and "module_name" in json_response:
#                 validated_config = GeneratorPayload(modules=[ModuleConfig(**json_response)])
#             elif isinstance(json_response, list):
#                 # If the AI returns a list of modules directly, wrap it in GeneratorPayload
#                 validated_config = GeneratorPayload(modules=[ModuleConfig(**m) for m in json_response])
#             else:
#                 validated_config = GeneratorPayload(**json_response)
#             return validated_config
#         except json.JSONDecodeError as e:
#             raise ValueError(f"AI response was not valid JSON: {e}\nResponse: {response.text}")
#         except google.genai.errors.ServerError as e:
#             raise ValueError(f"Gemini API Server Error: {e.value}\nResponse: {response.text}")
#         except Exception as e:
#             raise ValueError(f"AI response did not match schema: {e}\nResponse: {response.text}")
import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
from app.models.schemas import GeneratorPayload, ModuleConfig

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        # Configure providers with correct OpenAI-compatible base URLs and models
        self.providers = [
            {
                "name": "OpenRouter",
                "key": os.getenv("OPENROUTER_KEY", "").strip(),
                "url": "https://openrouter.ai/api/v1",
                "model": "google/gemini-2.0-flash-001"
            },
            {
                "name": "Bynara",
                "key": os.getenv("BYNARA_KEY", "").strip(),
                "url": "https://router.bynara.id/v1",
                "model": "gemini-1.5-flash"
            },
            {
                "name": "Gemini_Direct",
                "key": os.getenv("GEMINI_API_KEY", "").strip(),
                "url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                "model": "gemini-2.0-flash"
            }
        ]

        # Log detected keys
        for p in self.providers:
            status = "FOUND" if p["key"] else "MISSING"
            logger.info(f"Provider {p['name']}: {status}")

    def _get_client(self, provider):
        # Ensure the URL has a trailing slash for OpenAI client compatibility
        base_url = provider["url"]
        if not base_url.endswith('/'):
            base_url += '/'
        return OpenAI(api_key=provider["key"], base_url=base_url)

    def analyze_requirements(self, user_prompt: str) -> GeneratorPayload:
        prompt = self._build_prompt(user_prompt)

        for provider in self.providers:
            if not provider["key"]:
                continue

            try:
                logger.info(f"Attempting to use gateway: {provider['name']}")
                client = self._get_client(provider)

                # Use a standard chat completion call
                response = client.chat.completions.create(
                    model=provider["model"],
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )

                content = response.choices[0].message.content
                if not content:
                    logger.error(f"Gateway {provider['name']} returned empty content.")
                    continue

                return self._parse_response(content)

            except Exception as e:
                logger.error(f"Gateway {provider['name']} failed: {str(e)}")
                # If we get a 429 (Rate Limit) on Gemini, we might want to wait or just move to next
                continue

        raise Exception("Fatal Error: All AI gateways failed. Please check your keys, quotas, and internet connection.")

    def _build_prompt(self, user_prompt: str) -> str:
        """Standardized system prompt with schema."""
        return f"""Act as a senior Odoo developer. Your task is to generate a JSON configuration based on the provided schema. 
Your output must be purely valid JSON.

### SYSTEM CAPABILITIES & RULES:
1. MULTI-MODULE: The root of the JSON MUST be an object with a single key, "modules", which is a list of module configurations.
2. INHERITANCE: If customizing, set "is_customization": true and "inherit_model".
3. COMPUTE FIELDS: Use standard Odoo 17 @api.depends syntax in "compute_code".

### SCHEMA:
{GeneratorPayload.model_json_schema()}

### USER REQUEST:
{user_prompt}

Generate the JSON configuration now. Ensure it is valid JSON and follows the schema strictly.
"""

    def _parse_response(self, response_text: str) -> GeneratorPayload:
        """Validates AI response against the schema."""
        try:
            data = json.loads(response_text)
            # Handle cases where AI might skip the 'modules' wrapper
            if isinstance(data, dict) and "module_name" in data and "modules" not in data:
                return GeneratorPayload(modules=[ModuleConfig(**data)])
            elif isinstance(data, list):
                return GeneratorPayload(modules=[ModuleConfig(**m) for m in data])

            return GeneratorPayload(**data)
        except Exception as e:
            logger.error(f"Failed to parse JSON: {response_text[:200]}...")
            raise ValueError(f"AI response did not match schema: {str(e)}")
