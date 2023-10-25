from unittest.mock import Mock

from baserow.core.services.registries import ServiceType


def test_service_type_get_schema_name():
    mock_service = Mock(id=123)
    service_type_cls = ServiceType
    service_type_cls.model_class = Mock()
    assert service_type_cls().get_schema_name(mock_service) == "Service123Schema"


def test_service_type_generate_schema():
    mock_service = Mock(id=123)
    service_type_cls = ServiceType
    service_type_cls.model_class = Mock()
    assert service_type_cls().generate_schema(mock_service) is None
