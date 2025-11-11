from __future__ import annotations

import threading
from typing import Any, Optional

from sqlalchemy.orm import Session, joinedload

from ..db.models import ModelRoute, RouteNode, ExternalAPI
from ..schemas.route import ModelRouteCreate, ModelRouteUpdate, RouteNodeCreate


class RouteNotFoundError(LookupError):
    pass


class RouteServiceError(Exception):
    """Base exception for route service errors."""
    pass


class RouteValidationError(RouteServiceError):
    """Validation errors for route configuration."""
    pass


class RoutingService:
    def __init__(self):
        self._state_lock = threading.RLock()
        self._round_robin_indices: dict[int, int] = {}

    def get_state(self, route_id: int) -> dict[str, Any]:
        with self._state_lock:
            return {
                "round_robin_indices": {str(k): v for k, v in self._round_robin_indices.items() if k == route_id}
            }

    def reset_state(self, route_id: int) -> None:
        with self._state_lock:
            if route_id in self._round_robin_indices:
                del self._round_robin_indices[route_id]

    def _validate_providers_exist(self, session: Session, api_ids: list[int]) -> None:
        for api_id in api_ids:
            provider = session.get(ExternalAPI, api_id)
            if provider is None:
                raise RouteValidationError(f"Provider with id {api_id} not found")

    def _validate_models_exist(self, session: Session, api_id: int, models: list[str]) -> None:
        if not models:
            return
        provider = session.get(ExternalAPI, api_id)
        if provider is None:
            raise RouteValidationError(f"Provider with id {api_id} not found")
        provider_models = set(provider.models or [])
        for model in models:
            if model not in provider_models:
                raise RouteValidationError(
                    f"Model '{model}' not found in provider '{provider.name}'. Available models: {', '.join(provider_models)}"
                )

    def create_route(
        self, session: Session, payload: ModelRouteCreate
    ) -> ModelRoute:
        existing = session.query(ModelRoute).filter(ModelRoute.name == payload.name).one_or_none()
        if existing:
            raise RouteServiceError(f"Route with name '{payload.name}' already exists")

        route_data = payload.model_dump(exclude={"nodes"})
        route = ModelRoute(**route_data)
        session.add(route)
        session.flush()

        if payload.nodes:
            api_ids = [node.api_id for node in payload.nodes]
            self._validate_providers_exist(session, api_ids)

            for node_payload in payload.nodes:
                self._validate_models_exist(session, node_payload.api_id, node_payload.models)

                node_data = node_payload.model_dump()
                node = RouteNode(route_id=route.id, **node_data)
                session.add(node)

        session.commit()
        session.refresh(route)
        return route

    def get_route(self, session: Session, route_id: int) -> ModelRoute:
        route = session.query(ModelRoute).options(
            joinedload(ModelRoute.route_nodes).joinedload(RouteNode.api)
        ).get(route_id)
        if route is None:
            raise RouteNotFoundError(f"Route with id {route_id} not found")
        return route

    def list_routes(self, session: Session) -> list[ModelRoute]:
        return session.query(ModelRoute).options(
            joinedload(ModelRoute.route_nodes).joinedload(RouteNode.api)
        ).order_by(ModelRoute.id).all()

    def update_route(
        self, session: Session, route_id: int, payload: ModelRouteUpdate
    ) -> ModelRoute:
        route = self.get_route(session, route_id)

        update_data = payload.model_dump(exclude={"nodes"}, exclude_unset=True)

        if "name" in update_data:
            existing = session.query(ModelRoute).filter(
                ModelRoute.name == update_data["name"],
                ModelRoute.id != route_id
            ).one_or_none()
            if existing:
                raise RouteServiceError(f"Route with name '{update_data['name']}' already exists")
            route.name = update_data["name"]

        if "mode" in update_data:
            route.mode = update_data["mode"]
        if "is_active" in update_data:
            route.is_active = update_data["is_active"]
        if "config" in update_data:
            route.config = update_data["config"]

        if payload.nodes is not None:
            session.query(RouteNode).filter(RouteNode.route_id == route_id).delete()
            session.flush()

            if payload.nodes:
                api_ids = [node.api_id for node in payload.nodes]
                self._validate_providers_exist(session, api_ids)

                for node_payload in payload.nodes:
                    self._validate_models_exist(session, node_payload.api_id, node_payload.models)

                    node_data = node_payload.model_dump()
                    node = RouteNode(route_id=route_id, **node_data)
                    session.add(node)

        session.commit()
        session.refresh(route)
        return route

    def delete_route(self, session: Session, route_id: int) -> None:
        route = self.get_route(session, route_id)
        self.reset_state(route_id)
        session.delete(route)
        session.commit()

    def select_provider_and_model(
        self, session: Session, route_id: int, model_hint: Optional[str] = None
    ) -> tuple[int, str]:
        route = self.get_route(session, route_id)

        if not route.is_active:
            raise RouteServiceError(f"Route '{route.name}' is not active")

        if route.mode == "auto":
            return self._select_auto(session, route, model_hint)
        elif route.mode == "specific":
            return self._select_specific(session, route, model_hint)
        elif route.mode == "multi":
            if not route.route_nodes:
                raise RouteServiceError(f"Route '{route.name}' has no configured nodes")
            return self._select_multi(session, route, model_hint)
        else:
            raise RouteServiceError(f"Unknown route mode: {route.mode}")

    def _select_auto(
        self, session: Session, route: ModelRoute, model_hint: Optional[str] = None
    ) -> tuple[int, str]:
        config = route.config or {}
        selected_models = config.get('selectedModels', [])
        provider_mode = config.get('providerMode', 'all')
        
        if selected_models:
            return self._select_auto_with_config(session, route, selected_models, provider_mode, model_hint)
        
        if not route.route_nodes:
            raise RouteServiceError(f"Route '{route.name}' has no configured nodes and no models in config")
        
        active_nodes = [
            n for n in route.route_nodes
            if session.get(ExternalAPI, n.api_id).is_active and session.get(ExternalAPI, n.api_id).is_healthy
        ]
        if not active_nodes:
            raise RouteServiceError(f"No active providers in route '{route.name}'")

        selected_node = self._apply_round_robin_strategy(route.id, active_nodes)
        return self._pick_model_from_node(session, selected_node, model_hint)

    def _select_specific(
        self, session: Session, route: ModelRoute, model_hint: Optional[str] = None
    ) -> tuple[int, str]:
        config = route.config or {}
        selected_models = config.get('selectedModels', [])
        
        if selected_models:
            return self._select_specific_with_config(session, route, selected_models, model_hint)
        
        if not route.route_nodes:
            raise RouteServiceError(f"Route '{route.name}' has no configured nodes")
        
        if not model_hint:
            raise RouteServiceError(f"Route '{route.name}' in 'specific' mode requires a model hint")

        for node in route.route_nodes:
            provider = session.get(ExternalAPI, node.api_id)
            if not provider or not provider.is_active or not provider.is_healthy:
                continue
            node_models = node.models or provider.models or []
            if model_hint in node_models:
                return node.api_id, model_hint

        raise RouteServiceError(f"Model '{model_hint}' not found in active providers for route '{route.name}'")

    def _select_multi(
        self, session: Session, route: ModelRoute, model_hint: Optional[str] = None
    ) -> tuple[int, str]:
        active_nodes = sorted(
            [
                n for n in route.route_nodes
                if session.get(ExternalAPI, n.api_id).is_active and session.get(ExternalAPI, n.api_id).is_healthy
            ],
            key=lambda n: n.priority
        )

        if not active_nodes:
            raise RouteServiceError(f"No active providers in route '{route.name}'")

        for node in active_nodes:
            if model_hint:
                node_models = node.models or session.get(ExternalAPI, node.api_id).models or []
                if model_hint not in node_models:
                    continue

            strategy = node.strategy or "round-robin"
            if strategy == "round-robin":
                selected_node = self._apply_round_robin_strategy(route.id, [node])
                return self._pick_model_from_node(session, selected_node, model_hint)
            elif strategy == "failover":
                api_id, model = self._pick_model_from_node(session, node, model_hint)
                return api_id, model

        if model_hint:
            raise RouteServiceError(f"Model '{model_hint}' not found in active providers for route '{route.name}'")
        raise RouteServiceError(f"No suitable provider found in route '{route.name}'")

    def _apply_round_robin_strategy(self, route_id: int, nodes: list[RouteNode]) -> RouteNode:
        if not nodes:
            raise RouteServiceError("No nodes available for round-robin selection")

        with self._state_lock:
            current_index = self._round_robin_indices.get(route_id, 0)
            selected = nodes[current_index % len(nodes)]
            self._round_robin_indices[route_id] = (current_index + 1) % len(nodes)

        return selected

    def _pick_model_from_node(
        self, session: Session, node: RouteNode, model_hint: Optional[str] = None
    ) -> tuple[int, str]:
        provider = session.get(ExternalAPI, node.api_id)
        if not provider:
            raise RouteServiceError(f"Provider with id {node.api_id} not found")

        node_models = node.models if node.models else provider.models
        if not node_models:
            raise RouteServiceError(f"No models available for provider '{provider.name}'")

        if model_hint:
            if model_hint in node_models:
                return provider.id, model_hint
            else:
                raise RouteServiceError(f"Model '{model_hint}' not available in provider '{provider.name}'")

        return provider.id, node_models[0]

    def _select_auto_with_config(
        self, session: Session, route: ModelRoute, selected_models: list[str],
        provider_mode: str, model_hint: Optional[str] = None
    ) -> tuple[int, str]:
        if provider_mode == 'all':
            active_providers = [
                p for p in session.query(ExternalAPI).filter(
                    ExternalAPI.is_active == True,
                    ExternalAPI.is_healthy == True
                ).all()
            ]
            if not active_providers:
                raise RouteServiceError(f"No active providers in route '{route.name}'")
            
            selected_provider = self._apply_round_robin_to_providers(route.id, active_providers)
        else:
            provider_id = int(provider_mode.replace('provider_', ''))
            provider = session.get(ExternalAPI, provider_id)
            if not provider or not provider.is_active or not provider.is_healthy:
                raise RouteServiceError(f"Provider {provider_id} is not active or healthy in route '{route.name}'")
            selected_provider = provider
        
        if model_hint:
            if model_hint in selected_models:
                return selected_provider.id, model_hint
            else:
                raise RouteServiceError(f"Model '{model_hint}' not in configured models for route '{route.name}'")
        
        return selected_provider.id, self._pick_model_from_config(selected_models)

    def _select_specific_with_config(
        self, session: Session, route: ModelRoute, selected_models: list[str],
        model_hint: Optional[str] = None
    ) -> tuple[int, str]:
        if not route.route_nodes:
            raise RouteServiceError(f"Route '{route.name}' has no configured nodes")
        
        node = route.route_nodes[0]
        provider = session.get(ExternalAPI, node.api_id)
        if not provider or not provider.is_active or not provider.is_healthy:
            raise RouteServiceError(f"Provider for route '{route.name}' is not active or healthy")
        
        if model_hint:
            if model_hint in selected_models:
                return provider.id, model_hint
            else:
                raise RouteServiceError(f"Model '{model_hint}' not in configured models for route '{route.name}'")
        
        return provider.id, self._pick_model_from_config(selected_models)

    def _pick_model_from_config(self, selected_models: list[str]) -> str:
        if not selected_models:
            raise RouteServiceError("No models configured for selection")
        return selected_models[0]

    def _apply_round_robin_to_providers(
        self, route_id: int, providers: list[ExternalAPI]
    ) -> ExternalAPI:
        if not providers:
            raise RouteServiceError("No providers available for round-robin selection")

        with self._state_lock:
            key = f"provider_{route_id}"
            current_index = self._round_robin_indices.get(key, 0)
            selected = providers[current_index % len(providers)]
            self._round_robin_indices[key] = (current_index + 1) % len(providers)

        return selected


_routing_service = RoutingService()


def get_routing_service() -> RoutingService:
    return _routing_service
