"""Fixtures and shared setup for Zambretti & Sager tests."""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

# If homeassistant or voluptuous are not installed in the local Python environment,
# provide a dynamic import hook so unit tests can run locally without full HA core.
if "voluptuous" not in sys.modules:
    try:
        import voluptuous  # noqa: F401
    except ImportError:

        class VoluptuousMockModule(types.ModuleType):
            def __init__(self, name: str) -> None:
                super().__init__(name)
                self.Schema = lambda s, *a, **kw: s
                self.Required = lambda k, *a, **kw: k
                self.Optional = lambda k, *a, **kw: k
                self.In = lambda items, *a, **kw: items
                self.Coerce = lambda t, *a, **kw: t
                self.Range = lambda *a, **kw: lambda x: x
                self.All = lambda *a, **kw: lambda x: x
                self.Length = lambda *a, **kw: lambda x: x
                self.ExactSequence = lambda *a, **kw: lambda x: x
                self.MultipleInvalid = Exception
                self.Invalid = Exception

            def __getattr__(self, name: str):
                m = MagicMock()
                setattr(self, name, m)
                return m

        sys.modules["voluptuous"] = VoluptuousMockModule("voluptuous")

if "homeassistant" not in sys.modules:
    try:
        import homeassistant  # noqa: F401
    except ImportError:

        class DynamicMockModule(types.ModuleType):
            def __init__(self, name: str) -> None:
                super().__init__(name)
                self.__path__ = []
                self.__file__ = f"{name}.py"

            def __getattr__(self, name: str):
                m = MagicMock()
                setattr(self, name, m)
                return m

        class HomeAssistantImportHook:
            def find_spec(self, fullname, path, target=None):
                if fullname == "homeassistant" or fullname.startswith("homeassistant."):
                    from importlib.machinery import ModuleSpec

                    return ModuleSpec(fullname, self)
                return None

            def create_module(self, spec):
                mod = DynamicMockModule(spec.name)
                sys.modules[spec.name] = mod
                parts = spec.name.split(".")
                if len(parts) > 1:
                    parent = ".".join(parts[:-1])
                    child = parts[-1]
                    if parent in sys.modules:
                        setattr(sys.modules[parent], child, mod)
                return mod

            def exec_module(self, module):
                pass

        sys.meta_path.insert(0, HomeAssistantImportHook())
        sys.modules["homeassistant"] = DynamicMockModule("homeassistant")

        class MockState:
            def __init__(self, entity_id: str, state: str, attributes: dict | None = None) -> None:
                self.entity_id = entity_id
                self.state = state
                self.attributes = attributes or {}

        class MockEntity:
            _attr_translation_key = None
            _attr_unique_id = None
            _attr_icon = None
            _attr_native_unit_of_measurement = None
            _attr_state_class = None
            _attr_device_class = None
            _attr_entity_category = None
            _attr_force_update = False
            _attr_device_info = None
            _attr_has_entity_name = False

            def __init__(self, coordinator=None) -> None:
                self.coordinator = coordinator

            def __class_getitem__(cls, item):
                return cls

            @property
            def translation_key(self):
                return getattr(self, "_attr_translation_key", None)

            @property
            def unique_id(self):
                return getattr(self, "_attr_unique_id", None)

            @property
            def force_update(self):
                return getattr(self, "_attr_force_update", False)

        class MockCoordinatorEntity(MockEntity):
            pass

        class MockSensorEntity(MockEntity):
            pass

        class MockWeatherEntity(MockEntity):
            pass

        class MockForecast(dict):
            def __init__(self, **kwargs) -> None:
                super().__init__(kwargs)

        import homeassistant.core

        homeassistant.core.State = MockState

        import homeassistant.helpers.update_coordinator

        homeassistant.helpers.update_coordinator.CoordinatorEntity = MockCoordinatorEntity

        import homeassistant.components.sensor

        homeassistant.components.sensor.SensorEntity = MockSensorEntity

        import homeassistant.components.weather

        homeassistant.components.weather.WeatherEntity = MockWeatherEntity
        homeassistant.components.weather.Forecast = MockForecast


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations=None):
    """Enable custom integrations for pytest-homeassistant-custom-component if present."""
    yield
