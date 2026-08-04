import json

from types import SimpleNamespace

from app.models.schemas import ComponentMetadata, ComponentRegistryEntry
from app.services.ai_service import AIService


def test_find_matching_components_returns_hospital_management_for_hospital_prompt():
    component = ComponentRegistryEntry(
        component_id="hospital_management/v1.0",
        metadata=ComponentMetadata(
            name="Hospital Management",
            version="1.0.0",
            description="Smart component for hospital patient, appointment, and billing workflows.",
            capabilities=[
                "patient_management",
                "appointment_scheduling",
                "medical_records",
                "billing",
                "notifications",
            ],
            author="Coregen",
            tags=["healthcare", "hospital", "workflow"],
        ),
    )
    service = AIService(redis_url="")
    service.component_registry = SimpleNamespace(list_components=lambda: [component])

    results = service._find_matching_components("Create a hospital management module with appointment scheduling")

    assert len(results) == 1
    assert results[0].component_id == "hospital_management/v1.0"


def test_find_matching_components_excludes_hospital_management_for_stripe_prompt():
    component = ComponentRegistryEntry(
        component_id="hospital_management/v1.0",
        metadata=ComponentMetadata(
            name="Hospital Management",
            version="1.0.0",
            description="Smart component for hospital patient, appointment, and billing workflows.",
            capabilities=[
                "patient_management",
                "appointment_scheduling",
                "medical_records",
                "billing",
                "notifications",
            ],
            author="Coregen",
            tags=["healthcare", "hospital", "workflow"],
        ),
    )
    service = AIService(redis_url="")
    service.component_registry = SimpleNamespace(list_components=lambda: [component])

    results = service._find_matching_components("system sales with Stripe payment support")

    assert results == []
