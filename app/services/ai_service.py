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
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from openai import OpenAI, APIError
from dotenv import load_dotenv
from app.models.schemas import GeneratorPayload, ModuleConfig, ChatResponse

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ProviderTestResult:
    name: str
    model: str
    url: str
    key_status: str
    success: bool
    module_name: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    http_status: Optional[int] = None
    response_preview: Optional[str] = None


class AIService:
    def __init__(self):
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        openrouter_model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
        bynara_url = os.getenv("BYNARA_URL", "https://router.bynara.id/v1")
        bynara_key = os.getenv("BYNARA_KEY", "").strip()
        bynara_models = [
            model.strip()
            for model in os.getenv(
                "BYNARA_MODELS",
                "claude-sonnet-4.5,mistral-large,claude-haiku-4.5",
            ).split(",")
            if model.strip()
        ] or [os.getenv("BYNARA_MODEL", "claude-sonnet-4.5")]

        nara_providers = [
            {
                "name": f"NaraRouter/{model}",
                "key": bynara_key,
                "url": bynara_url,
                "model": model,
            }
            for model in bynara_models
        ]

        provider_groups = {
            "nara": nara_providers,
            "gemini": [
                {
                    "name": "Gemini_Direct",
                    "key": os.getenv("GEMINI_API_KEY", "").strip(),
                    "url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                    "model": gemini_model,
                }
            ],
            "openrouter": [
                {
                    "name": "OpenRouter",
                    "key": os.getenv("OPENROUTER_KEY", "").strip(),
                    "url": "https://openrouter.ai/api/v1",
                    "model": openrouter_model,
                }
            ],
        }

        # Nara models first (best -> lighter), then Gemini backup, then OpenRouter
        default_order = ("nara", "gemini", "openrouter")
        configured_order = os.getenv("AI_PROVIDER_ORDER", ",".join(default_order))
        order = [name.strip().lower() for name in configured_order.split(",") if name.strip()]

        self.providers = []
        for name in order:
            group = provider_groups.get(name)
            if group:
                self.providers.extend(group)
            else:
                logger.warning(f"Unknown provider in AI_PROVIDER_ORDER: {name}")

        for fallback_name in default_order:
            if fallback_name not in order:
                self.providers.extend(provider_groups.get(fallback_name, []))

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

    def _call_provider(self, provider: Dict[str, Any], prompt: str) -> str:
        client = self._get_client(provider)
        response = client.chat.completions.create(
            model=provider["model"],
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior Odoo developer. Return one complete JSON object only. "
                        "No markdown, no comments, no placeholders like '...', and no truncated output."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=8192,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Gateway returned empty content.")
        return content

    def test_provider(self, provider: Dict[str, Any], user_prompt: str) -> ProviderTestResult:
        """Test a single gateway and return a detailed result."""
        result = ProviderTestResult(
            name=provider["name"],
            model=provider["model"],
            url=provider["url"],
            key_status="FOUND" if provider["key"] else "MISSING",
            success=False,
        )

        if not provider["key"]:
            result.error_type = "MISSING_KEY"
            result.error_message = "API key missing in .env"
            return result

        prompt = self._build_prompt(user_prompt)
        try:
            content = self._call_provider(provider, prompt)
            try:
                payload = self._parse_response(content)
            except ValueError as e:
                result.error_type = "PARSE_ERROR"
                result.error_message = str(e)
                result.response_preview = content[:300]
                return result

            result.success = True
            result.module_name = payload.modules[0].module_name if payload.modules else None
            return result
        except APIError as e:
            result.error_type = "API_ERROR"
            result.http_status = getattr(e, "status_code", None)
            result.error_message = str(e.body) if getattr(e, "body", None) else str(e)
            return result
        except ValueError as e:
            result.error_type = "VALIDATION_ERROR"
            result.error_message = str(e)
            return result
        except Exception as e:
            result.error_type = type(e).__name__
            result.error_message = str(e)
            return result

    def test_all_providers(self, user_prompt: str) -> List[ProviderTestResult]:
        """Test every configured gateway independently."""
        return [self.test_provider(provider, user_prompt) for provider in self.providers]

    def chat_requirements(self, messages: List[Dict[str, str]]) -> ChatResponse:
        """Gather module requirements via conversational Q&A before generation."""
        for provider in self.providers:
            if not provider["key"]:
                continue

            try:
                logger.info(f"Chat via gateway: {provider['name']}")
                content = self._call_provider_chat(provider, messages)
                return self._parse_chat_response(content)
            except Exception as e:
                logger.error(f"Chat gateway {provider['name']} failed: {str(e)}")
                continue

        raise Exception("All AI gateways failed for chat. Please check your keys and connection.")

    def _call_provider_chat(self, provider: Dict[str, Any], messages: List[Dict[str, str]]) -> str:
        client = self._get_client(provider)
        response = client.chat.completions.create(
            model=provider["model"],
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an Odoo module requirements consultant. Gather enough detail before code generation.\n\n"
                        "Rules:\n"
                        "- Reply in the same language the user uses (Arabic or English).\n"
                        "- Ask 1-3 focused clarifying questions when requirements are incomplete.\n"
                        "- For casual replies (ok, thanks, ايك, تمام, yes), acknowledge briefly — do NOT treat them as module specs.\n"
                        "- Set ready_to_generate to true ONLY when you clearly have: module purpose, main models/entities, "
                        "key fields, and any special features (reports, workflows, security).\n"
                        "- When ready_to_generate is true, fill requirements_summary with a complete English spec "
                        "for the code generator, covering everything discussed.\n"
                        "- Never say you are generating code; the user clicks Generate separately.\n\n"
                        "Return JSON only:\n"
                        '{"reply": "message to user", "ready_to_generate": false, "requirements_summary": ""}'
                    ),
                },
                *messages,
            ],
            response_format={"type": "json_object"},
            max_tokens=2048,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Gateway returned empty chat content.")
        return content

    def _parse_chat_response(self, response_text: str) -> ChatResponse:
        cleaned = self._extract_json(response_text)
        try:
            data = json.loads(cleaned)
            return ChatResponse(
                reply=str(data.get("reply", "")).strip() or "How can I help with your Odoo module?",
                ready_to_generate=bool(data.get("ready_to_generate", False)),
                requirements_summary=str(data.get("requirements_summary", "")).strip(),
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Chat response was not valid JSON: {e}")

    def analyze_requirements(self, user_prompt: str) -> GeneratorPayload:
        prompt = self._build_prompt(user_prompt)

        for provider in self.providers:
            if not provider["key"]:
                continue

            try:
                logger.info(f"Attempting to use gateway: {provider['name']}")
                content = self._call_provider(provider, prompt)
                return self._parse_response(content)

            except Exception as e:
                logger.error(f"Gateway {provider['name']} failed: {str(e)}")
                continue

        raise Exception("Fatal Error: All AI gateways failed. Please check your keys, quotas, and internet connection.")

    def _build_prompt(self, user_prompt: str) -> str:
        """Standardized prompt with schema and a concrete example."""
        return f"""Generate a complete Odoo module JSON configuration.

Rules:
1. Root object MUST contain key "modules" with a list of module configs.
2. Use lowercase module names with underscores.
3. Model technical names must be module_name.model_name.
4. Return fully expanded JSON only. Never use "..." or omit sections.

Example output shape:
{{
  "modules": [
    {{
      "module_name": "library",
      "module_description": "Library management",
      "models": [
        {{
          "name": "library.book",
          "description": "Book",
          "rec_name": "name",
          "fields": [
            {{"name": "name", "type": "char", "label": "Title", "required": true}},
            {{"name": "isbn", "type": "char", "label": "ISBN"}}
          ],
          "tree_view_fields": ["name", "isbn"],
          "form_view_fields": ["name", "isbn"]
        }}
      ],
      "actions": [
        {{
          "name": "Books",
          "res_model": "library.book",
          "view_mode": "tree,form",
          "help_text": "Manage books"
        }}
      ],
      "menus": [
        {{"name": "Library", "sequence": 10}},
        {{
          "name": "Books",
          "parent_xml_id": "library.menu_library",
          "action_xml_id": "library.books_action",
          "sequence": 10
        }}
      ]
    }}
  ]
}}

Schema reference:
{GeneratorPayload.model_json_schema()}

User request:
{user_prompt}
"""

    @staticmethod
    def _extract_json(response_text: str) -> str:
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]
        return text

    def _parse_response(self, response_text: str) -> GeneratorPayload:
        """Validates AI response against the schema."""
        cleaned = self._extract_json(response_text)
        try:
            data = json.loads(cleaned)
            # Handle cases where AI might skip the 'modules' wrapper
            if isinstance(data, dict) and "module_name" in data and "modules" not in data:
                return GeneratorPayload(modules=[ModuleConfig(**data)])
            elif isinstance(data, list):
                return GeneratorPayload(modules=[ModuleConfig(**m) for m in data])

            return GeneratorPayload(**data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {cleaned[:300]}...")
            raise ValueError(f"AI response was not valid JSON: {e}")
        except Exception as e:
            logger.error(f"Failed to validate schema: {cleaned[:300]}...")
            raise ValueError(f"AI response did not match schema: {e}")
