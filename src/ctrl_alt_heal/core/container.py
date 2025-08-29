"""Dependency injection container for Ctrl-Alt-Heal application."""

from __future__ import annotations

from typing import Any, Dict, Type, TypeVar, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Container:
    """Simple dependency injection container."""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}

    def register(self, service_type: Type[T], implementation: T) -> None:
        """
        Register a service implementation.

        Args:
            service_type: Type of the service
            implementation: Service implementation
        """
        service_name = service_type.__name__
        self._services[service_name] = implementation
        logger.debug(f"Registered service: {service_name}")

    def register_singleton(self, service_type: Type[T], implementation: T) -> None:
        """
        Register a singleton service implementation.

        Args:
            service_type: Type of the service
            implementation: Service implementation
        """
        service_name = service_type.__name__
        self._singletons[service_name] = implementation
        logger.debug(f"Registered singleton: {service_name}")

    def register_factory(self, service_type: Type[T], factory: callable) -> None:
        """
        Register a factory function for creating service instances.

        Args:
            service_type: Type of the service
            factory: Factory function to create service instances
        """
        service_name = service_type.__name__
        self._factories[service_name] = factory
        logger.debug(f"Registered factory: {service_name}")

    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service instance.

        Args:
            service_type: Type of the service to resolve

        Returns:
            Service instance

        Raises:
            KeyError: If service is not registered
        """
        service_name = service_type.__name__

        # Check singletons first
        if service_name in self._singletons:
            return self._singletons[service_name]

        # Check regular services
        if service_name in self._services:
            return self._services[service_name]

        # Check factories
        if service_name in self._factories:
            instance = self._factories[service_name]()
            # Cache as singleton if it's a factory
            self._singletons[service_name] = instance
            return instance

        raise KeyError(f"Service not registered: {service_name}")

    def resolve_optional(self, service_type: Type[T]) -> Optional[T]:
        """
        Resolve a service instance, returning None if not found.

        Args:
            service_type: Type of the service to resolve

        Returns:
            Service instance or None
        """
        try:
            return self.resolve(service_type)
        except KeyError:
            return None

    def has_service(self, service_type: Type[T]) -> bool:
        """
        Check if a service is registered.

        Args:
            service_type: Type of the service

        Returns:
            True if service is registered
        """
        service_name = service_type.__name__
        return (
            service_name in self._services
            or service_name in self._singletons
            or service_name in self._factories
        )

    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()
        logger.debug("Container cleared")


# Global container instance
_container = Container()


def get_container() -> Container:
    """Get the global container instance."""
    return _container


def inject(service_type: Type[T]) -> T:
    """
    Decorator to inject dependencies into functions.

    Args:
        service_type: Type of the service to inject

    Returns:
        Decorated function with injected dependency
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Inject the service as the first argument
            service = _container.resolve(service_type)
            return func(service, *args, **kwargs)

        return wrapper

    return decorator


def inject_optional(service_type: Type[T]) -> Optional[T]:
    """
    Decorator to inject optional dependencies into functions.

    Args:
        service_type: Type of the service to inject

    Returns:
        Decorated function with injected optional dependency
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Inject the service as the first argument (None if not found)
            service = _container.resolve_optional(service_type)
            return func(service, *args, **kwargs)

        return wrapper

    return decorator


class ServiceProvider:
    """Context manager for service registration."""

    def __init__(self, container: Optional[Container] = None):
        self.container = container or _container
        self._temp_services: Dict[str, Any] = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up temporary services
        for service_name in self._temp_services:
            if service_name in self.container._services:
                del self.container._services[service_name]

    def register(self, service_type: Type[T], implementation: T) -> ServiceProvider:
        """Register a temporary service."""
        service_name = service_type.__name__
        self._temp_services[service_name] = implementation
        self.container.register(service_type, implementation)
        return self
