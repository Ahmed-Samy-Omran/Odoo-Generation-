import pytest
from types import SimpleNamespace

from app.models.schemas import ComponentMetadata, ComponentRegistryEntry
from app.services.ai_service import AIService


@pytest.fixture
def mock_component_registry_service():
    return SimpleNamespace(
        list_components=lambda: [
            ComponentRegistryEntry(
                component_id="hospital_management/v1.0",
                metadata=ComponentMetadata(
                    name="Hospital Management",
                    version="1.0.0",
                    description="Odoo module for managing hospital operations, including patient records, appointments, and doctor schedules.",
                    capabilities=["patient_management", "appointment_scheduling", "doctor_management"],
                    author="Coregen",
                    tags=["healthcare", "hospital"],
                ),
            ),
            ComponentRegistryEntry(
                component_id="payment_stripe/v1.2",
                metadata=ComponentMetadata(
                    name="Stripe Payment Gateway",
                    version="1.2.0",
                    description="Integrated Stripe payment gateway for Odoo modules.",
                    capabilities=["refunds", "subscriptions", "webhooks"],
                    author="Coregen",
                    tags=["finance", "payments", "stripe"],
                ),
            ),
        ]
    )


@pytest.fixture
def ai_service_with_mock_registry(mock_component_registry_service):
    service = AIService(redis_url="")
    service.component_registry = mock_component_registry_service
    return service


def test_find_matching_components_hospital(ai_service_with_mock_registry):
    prompt = "Create a hospital management module with appointment scheduling"
    matching_components = ai_service_with_mock_registry._find_matching_components(prompt)

    assert len(matching_components) == 1
    assert matching_components[0].component_id == "hospital_management/v1.0"


def test_find_matching_components_stripe(ai_service_with_mock_registry):
    prompt = "I need a sales system with Stripe payment support"
    matching_components = ai_service_with_mock_registry._find_matching_components(prompt)

    assert len(matching_components) == 1
    assert matching_components[0].component_id == "payment_stripe/v1.2"


def test_find_matching_components_no_match(ai_service_with_mock_registry):
    prompt = "Build a simple blog module"
    matching_components = ai_service_with_mock_registry._find_matching_components(prompt)

    assert len(matching_components) == 0


def test_find_matching_components_multiple_matches(ai_service_with_mock_registry):
    prompt = "Create a hospital management system with payment integration"
    matching_components = ai_service_with_mock_registry._find_matching_components(prompt)

    assert len(matching_components) >= 1
    component_ids = {c.component_id for c in matching_components}
    assert "hospital_management/v1.0" in component_ids
