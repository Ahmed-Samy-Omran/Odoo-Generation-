"""AI orchestration for Odoo module generation.

This module routes prompts through configured AI providers, normalizes responses,
validates them against the GeneratorPayload schema, and provides a simple
chat-based requirements flow.
"""

import asyncio
import inspect
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import APIError, OpenAI

from app.models.schemas import ChatResponse, ComponentRegistryEntry, GeneratorPayload, ModuleConfig
from app.services.cache_service import RedisCacheService
from app.services.component_registry_service import ComponentRegistryService
from app.services.rag_service import RAGService
from app.services.supabase_service import supabase_service

Provider = Dict[str, Any]

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
    def __init__(self, redis_url: Optional[str] = None):
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

        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self.cache_service = RedisCacheService(redis_url=self.redis_url)
        self.rag_service = RAGService(redis_url=self.redis_url)
        self.component_registry = ComponentRegistryService()
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

    def _get_client(self, provider: Provider) -> OpenAI:
        """Create an OpenAI-compatible client for a configured provider."""
        base_url = provider["url"]
        if not base_url.endswith('/'):
            base_url += '/'
        return OpenAI(api_key=provider["key"], base_url=base_url)

    @staticmethod
    def _response_text(response: Any) -> str:
        """Best-effort extraction of the assistant text from an OpenAI response."""
        try:
            choices = getattr(response, "choices", None) or []
            if not choices:
                return ""
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message") or {}
                return str(message.get("content") or "")
            message = getattr(first, "message", None)
            return str(getattr(message, "content", None) or "")
        except Exception:
            return ""

    def _log_usage(self, provider: Provider, response: Any, status: str = "success", job_id: Optional[str] = None, prompt_text: str = "", user_id: Optional[str] = None) -> None:
        """Persist token usage metrics returned by the OpenAI client.

        When the provider omits `usage` metadata the call is still counted:
        tokens are estimated from the input/output text length (~4 chars per
        token) and the row is flagged as estimated. Wrapped in try-except so
        a logging failure never breaks generation.
        """
        try:
            usage = getattr(response, "usage", None)
            estimated = False

            def _usage_value(attr: str) -> int:
                if isinstance(usage, dict):
                    return int(usage.get(attr, 0) or 0)
                return int(getattr(usage, attr, 0) or 0)

            if usage is not None:
                prompt_tokens = _usage_value("prompt_tokens")
                completion_tokens = _usage_value("completion_tokens")
                total_tokens = _usage_value("total_tokens") or (prompt_tokens + completion_tokens)
                if prompt_tokens <= 0 and completion_tokens <= 0:
                    estimated = True
            else:
                estimated = True

            if estimated:
                content = self._response_text(response)
                prompt_tokens = max(1, int(len(prompt_text or "") / 4))
                completion_tokens = max(1, int(len(content or "") / 4))
                total_tokens = prompt_tokens + completion_tokens
                logger.debug(
                    "Estimating usage for %s (no metadata): prompt=%d completion=%d",
                    provider.get("name"),
                    prompt_tokens,
                    completion_tokens,
                )

            supabase_service.log_api_usage(
                provider_name=provider.get("name", "unknown"),
                model_name=provider.get("model", "unknown"),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                status=status,
                job_id=job_id,
                estimated=estimated,
                user_id=user_id,
            )
        except Exception as exc:
            logger.exception("Failed to log API usage for %s: %s", provider.get("name"), exc)

    def _call_provider(self, provider: Provider, prompt: str, odoo_version: Optional[str] = None, job_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
        """Send the prompt to a single provider and return raw JSON content."""
        version = (odoo_version or "17.0").strip() or "17.0"
        logger.debug("Calling provider %s for Odoo %s", provider.get("name"), version)
        client = self._get_client(provider)
        response = client.chat.completions.create(
            model=provider["model"],
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a senior Odoo developer targeting Odoo {version}. "
                        f"Always follow the official Odoo {version} coding guidelines. Pay special attention to the manifest.py structure, view inheritance, and the OWL framework for versions 16.0 and 17.0. "
                        "For Odoo 17, ensure the use of the latest web client standards. "
                        "Carefully analyze the request, then generate only valid JSON conforming to the module schema. "
                        "Do not include markdown, comments, or any text outside the JSON. "
                        "If GitHub deployment is requested, set git_deploy_target to 'github'; otherwise use 'local_zip'."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=4096,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Gateway returned empty content.")
        self._log_usage(provider, response, status="success", job_id=job_id, prompt_text=prompt, user_id=user_id)
        return content

    def test_provider(self, provider: Provider, user_prompt: str) -> ProviderTestResult:
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

    def configured_models(self) -> List[Dict[str, str]]:
        """Return configured provider/model pairs even if they have never been used.

        `providers` is a flat list built from the env (nara/gemini/openrouter),
        so a model may map to its primary provider only. This is used by the
        dashboard to show every configured model/provider even with zero usage.
        """
        pairs: Dict[str, str] = {}
        for provider in self.providers:
            model = str(provider.get("model") or "unknown").strip() or "unknown"
            if model not in pairs:
                pairs[model] = str(provider.get("name") or "unknown").strip() or "unknown"
        return [
            {"model_name": model, "provider_name": provider}
            for model, provider in pairs.items()
        ]

    async def chat_requirements(self, messages: List[Dict[str, str]], job_id: Optional[str] = None, user_id: Optional[str] = None) -> ChatResponse:
        """Gather module requirements via conversational Q&A before generation."""
        cache_payload = json.dumps(messages, ensure_ascii=False, sort_keys=True)
        cache_key = self.cache_service.build_key("ai_chat", cache_payload)
        cached_response = await self._ensure_awaited(self.cache_service.get_json(cache_key))
        if cached_response is not None:
            return ChatResponse(**cached_response)

        for provider in self.providers:
            if not provider["key"]:
                continue

            try:
                logger.info(f"Chat via gateway: {provider['name']}")
                content = self._call_provider_chat(provider, messages, job_id=job_id, user_id=user_id)
                response = self._parse_chat_response(content)
                await self._ensure_awaited(
                    self.cache_service.set_json(cache_key, response.model_dump(mode="json"), ttl=900)
                )
                return response
            except Exception as e:
                logger.error(f"Chat gateway {provider['name']} failed: {str(e)}")
                continue

        raise Exception("All AI gateways failed for chat. Please check your keys and connection.")

    def _call_provider_chat(self, provider: Provider, messages: List[Dict[str, str]], job_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
        client = self._get_client(provider)
        response = client.chat.completions.create(
            model=provider["model"],
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful and senior Odoo Module Architect. Maintain a warm, professional, and technically precise tone.\n"
                        "Rules:\n"
                        "0. For every new session, begin with a warm professional greeting and a short introduction, then ask only the first question: the module's technical name. Example style: 'Welcome! I'm your Odoo Module Architect. I'm excited to help you build your next module. To get started, what is the technical name you'd like to give this module?'\n"
                        "1. Ask exactly ONE main question at a time. Do not jump into the full discovery flow or list every requirement in one message.\n"
                        "2. Follow a strict incremental flow: Module Name -> Models -> Fields for those models -> relations/actions/menus/security/manifest details -> final summary.\n"
                        "3. After each user answer, acknowledge it briefly with positive feedback and ask only the next logical question.\n"
                        "4. If the answer is vague, ask one short clarifying question before moving forward.\n"
                        "5. Maintain a balance between being a helpful assistant and a senior technical consultant: friendly, confident, and concise.\n"
                        "6. Focus strictly on Odoo models, fields, relations, actions, menus, security, and manifest requirements.\n"
                        "7. Use clean Markdown with ### headers only when needed, bullet points or numbered lists for items, and backticks for all technical names such as model names, field names, module names, XML IDs, and method names.\n"
                        "8. Keep one blank line between sections and keep the structure ready for code generation.\n"
                        "9. When the conversation is in Arabic, keep the reply professional and technical, using correct Odoo terminology and preserving punctuation and numbers in RTL text.\n"
                        "10. Set 'ready_to_generate' to true only after the full sequence is completed.\n"
                        "11. When ready, provide a technical summary in 'requirements_summary' using the same warm-but-precise style.\n"
                        "Return JSON: {'reply': '...', 'ready_to_generate': true/false, 'requirements_summary': '...'}"
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
        prompt_text = "\n".join(
            str(m.get("content", "")) if isinstance(m, dict) else str(getattr(m, "content", ""))
            for m in messages
        )
        self._log_usage(provider, response, status="success", job_id=job_id, prompt_text=prompt_text, user_id=user_id)
        return content

    async def _ensure_awaited(self, value: Any) -> Any:
        if inspect.isawaitable(value):
            return await value
        return value

    def _parse_chat_response(self, response_text: str) -> ChatResponse:
        """Parse a chat gateway response into the chat response schema."""
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

    async def analyze_requirements(self, user_prompt: str, odoo_version: Optional[str] = None, job_id: Optional[str] = None, user_id: Optional[str] = None) -> GeneratorPayload:
        matching_components = self._find_matching_components(user_prompt)
        component_context = self._build_component_context(matching_components)
        if component_context:
            logger.info(
                "AI Orchestrator found matching registry components: %s",
                ", ".join(c.component_id for c in matching_components),
            )
        prompt = await self._build_prompt(user_prompt, odoo_version, component_context)
        cache_key = self.cache_service.build_key("ai_generate", json.dumps({
            "prompt": user_prompt,
            "odoo_version": odoo_version or "17.0",
            "component_context": component_context,
        }, ensure_ascii=False, sort_keys=True))
        cached_payload = self.cache_service.get_json(cache_key)
        if cached_payload is not None:
            return self._ensure_generator_payload(cached_payload)

        for provider in self.providers:
            if not provider["key"]:
                continue

            try:
                logger.info(f"Attempting to use gateway: {provider['name']}")
                content = self._call_provider(provider, prompt, odoo_version, job_id=job_id, user_id=user_id)
                payload = self._parse_response(content)
                self.cache_service.set_json(cache_key, payload.model_dump(mode="json"), ttl=900)
                return self._ensure_generator_payload(payload)

            except Exception as e:
                logger.error(f"Gateway {provider['name']} failed: {str(e)}")
                continue

        raise Exception("Fatal Error: All AI gateways failed. Please check your keys, quotas, and internet connection.")

    async def _build_prompt(self, user_prompt: str, odoo_version: Optional[str] = None, component_context: Optional[str] = None) -> str:
        """Standardized prompt with schema and a concrete example."""
        version = (odoo_version or "17.0").strip() or "17.0"
        rag_results = await self.rag_service.search(user_prompt, top_k=3)
        rag_context = self.rag_service._format_search_results(rag_results)
        component_block = f"{component_context}\n\n" if component_context else ""
        return f"""{component_block}Analyze the user request in two steps.
1. First, build a concise plan for the module, including models, views, menus, security groups and deployment target.
2. Then output only the final JSON payload that matches the GeneratorPayload schema.

Important:
- Do not include markdown, comments, or any explanation outside the JSON.
- If GitHub deployment is requested, set "git_deploy_target": "github".
- Otherwise set "git_deploy_target": "local_zip".
- Always follow the official Odoo {version} coding guidelines. Pay special attention to the manifest.py structure, view inheritance, and the OWL framework for versions 16.0 and 17.0.
- For Odoo 17, ensure the use of the latest web client standards.
- Always return valid JSON parseable by json.loads().
- Prioritize the provided local Odoo reference context when the request concerns standard Odoo behavior, views, models, or XML structure.

Reference Context:
{rag_context}

Rules:
1. Root object MUST contain key "modules" with a list of module configs.
2. Use lowercase module names with underscores.
3. Model technical names should be short and not prefixed with the module name (e.g., use 'patient', 'doctor' instead of 'hospital.patient').
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

    def _find_matching_components(self, user_prompt: str) -> List[ComponentRegistryEntry]:
        """Return registry components whose metadata keywords match the prompt."""
        normalized = user_prompt.lower()
        matches: List[tuple[int, ComponentRegistryEntry]] = []
        for component in self.component_registry.list_components():
            score = 0
            keywords: List[str] = []
            if component.metadata.name:
                keywords.extend(component.metadata.name.lower().split())
            if component.metadata.capabilities:
                keywords.extend(component.metadata.capabilities)
            if component.metadata.tags:
                keywords.extend(component.metadata.tags)

            for keyword in keywords:
                normalized_keyword = keyword.replace("_", " ").lower().strip()
                if not normalized_keyword:
                    continue
                if normalized_keyword in normalized:
                    score += 1
            if score > 0:
                matches.append((score, component))
        matches.sort(key=lambda item: item[0], reverse=True)
        return [component for _, component in matches]

    def _build_component_context(self, components: List[ComponentRegistryEntry]) -> str:
        if not components:
            return ""
        lines = [
            "Smart components available in the knowledge registry:",
        ]
        for component in components:
            metadata = component.metadata
            lines.append(
                f"- {component.component_id}: {metadata.description or 'No description.'} "
                f"(capabilities: {', '.join(metadata.capabilities or [])})"
            )
        lines.append(
            "When a matched component is suitable, prefer reusing its internal business rules and templates instead of generating all code from scratch."
        )
        return "\n".join(lines)

    def _ensure_generator_payload(self, payload: Any) -> GeneratorPayload:
        if isinstance(payload, GeneratorPayload):
            return payload
        if isinstance(payload, dict):
            return GeneratorPayload(**payload)
        if isinstance(payload, list):
            return GeneratorPayload(modules=[ModuleConfig(**m) for m in payload])
        raise ValueError(f"Unable to normalize payload to GeneratorPayload: {type(payload).__name__}")

    def _parse_response(self, response_text: Any) -> GeneratorPayload:
        """Validate AI response content and normalize it to GeneratorPayload."""
        try:
            if isinstance(response_text, (dict, list)):
                data = response_text
            else:
                cleaned = self._extract_json(str(response_text))
                data = json.loads(cleaned)

            # Handle cases where AI might skip the 'modules' wrapper
            if isinstance(data, dict) and "module_name" in data and "modules" not in data:
                return GeneratorPayload(modules=[ModuleConfig(**data)])
            if isinstance(data, list):
                return GeneratorPayload(modules=[ModuleConfig(**m) for m in data])

            return GeneratorPayload(**data)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON from provider response: %s", response_text)
            raise ValueError(f"AI response was not valid JSON: {e}")
        except Exception as e:
            logger.error("Failed to validate provider schema response: %s", response_text)
            raise ValueError(f"AI response did not match schema: {e}")
