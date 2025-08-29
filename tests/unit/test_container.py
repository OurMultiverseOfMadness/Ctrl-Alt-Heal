"""Tests for dependency injection container."""

import pytest

from ctrl_alt_heal.core.container import (
    Container,
    get_container,
    inject,
    inject_optional,
    ServiceProvider,
)


class TestContainer:
    """Test dependency injection container."""

    def test_container_creation(self):
        """Test creating a new container."""
        container = Container()
        assert container is not None

    def test_register_service(self):
        """Test registering a service."""
        container = Container()

        class TestService:
            def __init__(self):
                self.value = "test"

        service = TestService()
        container.register(TestService, service)

        assert container.has_service(TestService)
        resolved_service = container.resolve(TestService)
        assert resolved_service is service
        assert resolved_service.value == "test"

    def test_register_singleton(self):
        """Test registering a singleton service."""
        container = Container()

        class TestService:
            def __init__(self):
                self.value = "test"

        service = TestService()
        container.register_singleton(TestService, service)

        assert container.has_service(TestService)
        resolved_service1 = container.resolve(TestService)
        resolved_service2 = container.resolve(TestService)
        assert resolved_service1 is resolved_service2
        assert resolved_service1 is service

    def test_register_factory(self):
        """Test registering a factory function."""
        container = Container()

        class TestService:
            def __init__(self, value):
                self.value = value

        def create_service():
            return TestService("factory_created")

        container.register_factory(TestService, create_service)

        assert container.has_service(TestService)
        resolved_service = container.resolve(TestService)
        assert isinstance(resolved_service, TestService)
        assert resolved_service.value == "factory_created"

    def test_resolve_nonexistent_service(self):
        """Test resolving a non-existent service."""
        container = Container()

        class TestService:
            pass

        with pytest.raises(KeyError):
            container.resolve(TestService)

    def test_resolve_optional_service(self):
        """Test resolving an optional service."""
        container = Container()

        class TestService:
            pass

        # Service doesn't exist
        result = container.resolve_optional(TestService)
        assert result is None

        # Register service
        service = TestService()
        container.register(TestService, service)

        # Service exists
        result = container.resolve_optional(TestService)
        assert result is service

    def test_has_service(self):
        """Test checking if service exists."""
        container = Container()

        class TestService:
            pass

        # Service doesn't exist
        assert not container.has_service(TestService)

        # Register service
        service = TestService()
        container.register(TestService, service)

        # Service exists
        assert container.has_service(TestService)

    def test_clear_container(self):
        """Test clearing the container."""
        container = Container()

        class TestService:
            pass

        service = TestService()
        container.register(TestService, service)

        assert container.has_service(TestService)

        container.clear()
        assert not container.has_service(TestService)


class TestGlobalContainer:
    """Test global container functionality."""

    def test_get_container(self):
        """Test getting the global container."""
        container = get_container()
        assert isinstance(container, Container)

    def test_global_container_registration(self):
        """Test registering services in global container."""
        container = get_container()
        container.clear()  # Start fresh

        class TestService:
            def __init__(self):
                self.value = "test"

        service = TestService()
        container.register(TestService, service)

        resolved_service = container.resolve(TestService)
        assert resolved_service is service


class TestInjectDecorator:
    """Test injection decorators."""

    def test_inject_decorator(self):
        """Test the inject decorator."""
        container = get_container()
        container.clear()  # Start fresh

        class TestService:
            def __init__(self):
                self.value = "test"

        service = TestService()
        container.register(TestService, service)

        @inject(TestService)
        def test_function(injected_service, param):
            return injected_service.value + param

        result = test_function("_param")
        assert result == "test_param"

    def test_inject_optional_decorator_with_service(self):
        """Test the inject_optional decorator with service present."""
        container = get_container()
        container.clear()  # Start fresh

        class TestService:
            def __init__(self):
                self.value = "test"

        service = TestService()
        container.register(TestService, service)

        @inject_optional(TestService)
        def test_function(injected_service, param):
            return (
                injected_service.value + param
                if injected_service
                else "no_service" + param
            )

        result = test_function("_param")
        assert result == "test_param"

    def test_inject_optional_decorator_without_service(self):
        """Test the inject_optional decorator without service."""
        container = get_container()
        container.clear()  # Start fresh

        class TestService:
            pass

        @inject_optional(TestService)
        def test_function(injected_service, param):
            return (
                "no_service" + param
                if injected_service is None
                else "service_present" + param
            )

        result = test_function("_param")
        assert result == "no_service_param"


class TestServiceProvider:
    """Test service provider context manager."""

    def test_service_provider_context(self):
        """Test service provider as context manager."""
        container = get_container()
        container.clear()  # Start fresh

        class TestService:
            def __init__(self, value):
                self.value = value

        with ServiceProvider(container) as provider:
            service = TestService("temp")
            provider.register(TestService, service)

            # Service should be available
            resolved_service = container.resolve(TestService)
            assert resolved_service is service

        # Service should be cleaned up
        assert not container.has_service(TestService)

    def test_service_provider_chaining(self):
        """Test service provider method chaining."""
        container = get_container()
        container.clear()  # Start fresh

        class TestService1:
            pass

        class TestService2:
            pass

        with ServiceProvider(container) as provider:
            provider.register(TestService1, TestService1()).register(
                TestService2, TestService2()
            )

            assert container.has_service(TestService1)
            assert container.has_service(TestService2)
