from endpoints.settings import SERVICE_CONFIGS


def test_vision_fallback_service_has_address_model_and_secret():
    service = next(item for item in SERVICE_CONFIGS if item["id"] == "vision_fallback")
    fields = {field["id"]: field for field in service["fields"]}

    assert fields["base_url"]["default"] == "https://dasuapi.com/v1"
    assert fields["model"]["default"] == "gpt-5.6-terra"
    assert fields["api_key"]["kind"] == "secret"
