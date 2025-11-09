from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from backend.app.db.models import ExternalAPI, ModelRoute, RouteNode
from backend.app.schemas.route import (
    ModelRouteCreate,
    ModelRouteUpdate,
    RouteNodeCreate,
)
from backend.app.services.routing import (
    RouteNotFoundError,
    RouteServiceError,
    RouteValidationError,
    get_routing_service,
)


@pytest.fixture
def provider_openai(db_session: Session) -> ExternalAPI:
    provider = ExternalAPI(
        name="OpenAI",
        base_url="https://api.openai.com/v1",
        api_key_encrypted="encrypted_key_1",
        models=["gpt-4", "gpt-3.5-turbo"],
        is_active=True,
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    return provider


@pytest.fixture
def provider_anthropic(db_session: Session) -> ExternalAPI:
    provider = ExternalAPI(
        name="Anthropic",
        base_url="https://api.anthropic.com",
        api_key_encrypted="encrypted_key_2",
        models=["claude-3-opus", "claude-3-sonnet"],
        is_active=True,
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    return provider


@pytest.fixture
def provider_cohere(db_session: Session) -> ExternalAPI:
    provider = ExternalAPI(
        name="Cohere",
        base_url="https://api.cohere.ai",
        api_key_encrypted="encrypted_key_3",
        models=["command", "command-light"],
        is_active=True,
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    return provider


@pytest.fixture
def provider_inactive(db_session: Session) -> ExternalAPI:
    provider = ExternalAPI(
        name="Inactive Provider",
        base_url="https://api.inactive.com",
        api_key_encrypted="encrypted_key_4",
        models=["model-1"],
        is_active=False,
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    return provider


class TestRouteCRUD:
    def test_create_auto_route(
        self, db_session: Session, provider_openai: ExternalAPI, provider_anthropic: ExternalAPI
    ) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="test-auto-route",
            mode="auto",
            is_active=True,
            nodes=[
                RouteNodeCreate(api_id=provider_openai.id, strategy="round-robin"),
                RouteNodeCreate(api_id=provider_anthropic.id, strategy="round-robin"),
            ],
        )

        route = service.create_route(db_session, payload)

        assert route.id is not None
        assert route.name == "test-auto-route"
        assert route.mode == "auto"
        assert route.is_active is True
        assert len(route.route_nodes) == 2

    def test_create_specific_route(self, db_session: Session, provider_openai: ExternalAPI) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="test-specific-route",
            mode="specific",
            is_active=True,
            nodes=[
                RouteNodeCreate(api_id=provider_openai.id, models=["gpt-4"]),
            ],
        )

        route = service.create_route(db_session, payload)

        assert route.mode == "specific"
        assert len(route.route_nodes) == 1
        assert route.route_nodes[0].models == ["gpt-4"]

    def test_create_multi_route(
        self, db_session: Session, provider_openai: ExternalAPI, provider_anthropic: ExternalAPI
    ) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="test-multi-route",
            mode="multi",
            is_active=True,
            nodes=[
                RouteNodeCreate(
                    api_id=provider_openai.id, priority=0, strategy="round-robin"
                ),
                RouteNodeCreate(
                    api_id=provider_anthropic.id, priority=1, strategy="failover"
                ),
            ],
        )

        route = service.create_route(db_session, payload)

        assert route.mode == "multi"
        assert len(route.route_nodes) == 2
        priorities = sorted([node.priority for node in route.route_nodes])
        assert priorities == [0, 1]

    def test_create_route_with_duplicate_name(
        self, db_session: Session, provider_openai: ExternalAPI
    ) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="duplicate-route",
            mode="auto",
            nodes=[RouteNodeCreate(api_id=provider_openai.id)],
        )

        service.create_route(db_session, payload)

        with pytest.raises(RouteServiceError, match="already exists"):
            service.create_route(db_session, payload)

    def test_create_route_with_invalid_provider(self, db_session: Session) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="invalid-provider-route",
            mode="auto",
            nodes=[RouteNodeCreate(api_id=9999)],
        )

        with pytest.raises(RouteValidationError, match="not found"):
            service.create_route(db_session, payload)

    def test_create_route_with_invalid_model(
        self, db_session: Session, provider_openai: ExternalAPI
    ) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="invalid-model-route",
            mode="specific",
            nodes=[RouteNodeCreate(api_id=provider_openai.id, models=["invalid-model"])],
        )

        with pytest.raises(RouteValidationError, match="not found"):
            service.create_route(db_session, payload)

    def test_get_route(self, db_session: Session, provider_openai: ExternalAPI) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="get-test-route",
            mode="auto",
            nodes=[RouteNodeCreate(api_id=provider_openai.id)],
        )

        created = service.create_route(db_session, payload)
        retrieved = service.get_route(db_session, created.id)

        assert retrieved.id == created.id
        assert retrieved.name == created.name

    def test_get_nonexistent_route(self, db_session: Session) -> None:
        service = get_routing_service()

        with pytest.raises(RouteNotFoundError):
            service.get_route(db_session, 9999)

    def test_list_routes(self, db_session: Session, provider_openai: ExternalAPI) -> None:
        service = get_routing_service()

        payload1 = ModelRouteCreate(
            name="route-1",
            mode="auto",
            nodes=[RouteNodeCreate(api_id=provider_openai.id)],
        )
        payload2 = ModelRouteCreate(
            name="route-2",
            mode="specific",
            nodes=[RouteNodeCreate(api_id=provider_openai.id)],
        )

        service.create_route(db_session, payload1)
        service.create_route(db_session, payload2)

        routes = service.list_routes(db_session)

        assert len(routes) == 2
        assert routes[0].name == "route-1"
        assert routes[1].name == "route-2"

    def test_update_route(self, db_session: Session, provider_openai: ExternalAPI, provider_anthropic: ExternalAPI) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="original-route",
            mode="auto",
            is_active=True,
            nodes=[RouteNodeCreate(api_id=provider_openai.id)],
        )
        route = service.create_route(db_session, payload)

        update_payload = ModelRouteUpdate(
            name="updated-route",
            is_active=False,
            nodes=[RouteNodeCreate(api_id=provider_anthropic.id)],
        )

        updated = service.update_route(db_session, route.id, update_payload)

        assert updated.name == "updated-route"
        assert updated.is_active is False
        assert len(updated.route_nodes) == 1
        assert updated.route_nodes[0].api_id == provider_anthropic.id

    def test_delete_route(self, db_session: Session, provider_openai: ExternalAPI) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="delete-test-route",
            mode="auto",
            nodes=[RouteNodeCreate(api_id=provider_openai.id)],
        )
        route = service.create_route(db_session, payload)

        service.delete_route(db_session, route.id)

        with pytest.raises(RouteNotFoundError):
            service.get_route(db_session, route.id)


class TestAutoModeRouting:
    def test_auto_mode_round_robin(
        self,
        db_session: Session,
        provider_openai: ExternalAPI,
        provider_anthropic: ExternalAPI,
    ) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="auto-rr-route",
            mode="auto",
            nodes=[
                RouteNodeCreate(api_id=provider_openai.id, strategy="round-robin"),
                RouteNodeCreate(api_id=provider_anthropic.id, strategy="round-robin"),
            ],
        )
        route = service.create_route(db_session, payload)

        provider_id_1, model_1 = service.select_provider_and_model(db_session, route.id)
        provider_id_2, model_2 = service.select_provider_and_model(db_session, route.id)
        provider_id_3, model_3 = service.select_provider_and_model(db_session, route.id)

        assert provider_id_1 == provider_openai.id or provider_id_1 == provider_anthropic.id
        assert provider_id_2 != provider_id_1
        assert provider_id_3 == provider_id_1

    def test_auto_mode_skips_inactive_providers(
        self,
        db_session: Session,
        provider_openai: ExternalAPI,
        provider_inactive: ExternalAPI,
    ) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="auto-skip-inactive",
            mode="auto",
            nodes=[
                RouteNodeCreate(api_id=provider_openai.id),
                RouteNodeCreate(api_id=provider_inactive.id),
            ],
        )
        route = service.create_route(db_session, payload)

        provider_id, model = service.select_provider_and_model(db_session, route.id)

        assert provider_id == provider_openai.id

    def test_auto_mode_no_active_providers(
        self,
        db_session: Session,
        provider_inactive: ExternalAPI,
    ) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="auto-no-active",
            mode="auto",
            nodes=[RouteNodeCreate(api_id=provider_inactive.id)],
        )
        route = service.create_route(db_session, payload)

        with pytest.raises(RouteServiceError, match="No active providers"):
            service.select_provider_and_model(db_session, route.id)

    def test_auto_mode_picks_first_model(
        self,
        db_session: Session,
        provider_openai: ExternalAPI,
    ) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="auto-first-model",
            mode="auto",
            nodes=[RouteNodeCreate(api_id=provider_openai.id)],
        )
        route = service.create_route(db_session, payload)

        provider_id, model = service.select_provider_and_model(db_session, route.id)

        assert provider_id == provider_openai.id
        assert model == "gpt-4"


class TestSpecificModeRouting:
    def test_specific_mode_with_model_hint(
        self,
        db_session: Session,
        provider_openai: ExternalAPI,
        provider_anthropic: ExternalAPI,
    ) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="specific-with-hint",
            mode="specific",
            nodes=[
                RouteNodeCreate(api_id=provider_openai.id),
                RouteNodeCreate(api_id=provider_anthropic.id),
            ],
        )
        route = service.create_route(db_session, payload)

        provider_id, model = service.select_provider_and_model(db_session, route.id, "gpt-4")

        assert provider_id == provider_openai.id
        assert model == "gpt-4"

    def test_specific_mode_without_model_hint(self, db_session: Session, provider_openai: ExternalAPI) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="specific-no-hint",
            mode="specific",
            nodes=[RouteNodeCreate(api_id=provider_openai.id)],
        )
        route = service.create_route(db_session, payload)

        with pytest.raises(RouteServiceError, match="requires a model hint"):
            service.select_provider_and_model(db_session, route.id)

    def test_specific_mode_model_not_found(
        self,
        db_session: Session,
        provider_openai: ExternalAPI,
    ) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="specific-model-not-found",
            mode="specific",
            nodes=[RouteNodeCreate(api_id=provider_openai.id)],
        )
        route = service.create_route(db_session, payload)

        with pytest.raises(RouteServiceError, match="not found"):
            service.select_provider_and_model(db_session, route.id, "nonexistent-model")


class TestMultiModeRouting:
    def test_multi_mode_prioritizes_nodes(
        self,
        db_session: Session,
        provider_openai: ExternalAPI,
        provider_anthropic: ExternalAPI,
    ) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="multi-priority",
            mode="multi",
            nodes=[
                RouteNodeCreate(api_id=provider_openai.id, priority=1),
                RouteNodeCreate(api_id=provider_anthropic.id, priority=0),
            ],
        )
        route = service.create_route(db_session, payload)

        provider_id, model = service.select_provider_and_model(db_session, route.id)

        assert provider_id == provider_anthropic.id

    def test_multi_mode_respects_model_hint(
        self,
        db_session: Session,
        provider_openai: ExternalAPI,
        provider_anthropic: ExternalAPI,
    ) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="multi-model-hint",
            mode="multi",
            nodes=[
                RouteNodeCreate(api_id=provider_openai.id, priority=0, models=["gpt-4"]),
                RouteNodeCreate(api_id=provider_anthropic.id, priority=1, models=["claude-3-opus"]),
            ],
        )
        route = service.create_route(db_session, payload)

        provider_id, model = service.select_provider_and_model(db_session, route.id, "claude-3-opus")

        assert provider_id == provider_anthropic.id
        assert model == "claude-3-opus"

    def test_multi_mode_skips_incompatible_nodes(
        self,
        db_session: Session,
        provider_openai: ExternalAPI,
        provider_anthropic: ExternalAPI,
    ) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="multi-skip-incompatible",
            mode="multi",
            nodes=[
                RouteNodeCreate(api_id=provider_openai.id, priority=0, models=["gpt-4"]),
                RouteNodeCreate(api_id=provider_anthropic.id, priority=1, models=["claude-3-opus"]),
            ],
        )
        route = service.create_route(db_session, payload)

        with pytest.raises(RouteServiceError, match="not found"):
            service.select_provider_and_model(db_session, route.id, "nonexistent-model")


class TestRouteState:
    def test_get_route_state(
        self,
        db_session: Session,
        provider_openai: ExternalAPI,
        provider_anthropic: ExternalAPI,
    ) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="state-test",
            mode="auto",
            nodes=[
                RouteNodeCreate(api_id=provider_openai.id),
                RouteNodeCreate(api_id=provider_anthropic.id),
            ],
        )
        route = service.create_route(db_session, payload)

        service.select_provider_and_model(db_session, route.id)
        state = service.get_state(route.id)

        assert "round_robin_indices" in state
        assert str(route.id) in state["round_robin_indices"] or len(state["round_robin_indices"]) > 0

    def test_reset_route_state(
        self,
        db_session: Session,
        provider_openai: ExternalAPI,
        provider_anthropic: ExternalAPI,
    ) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="state-reset-test",
            mode="auto",
            nodes=[
                RouteNodeCreate(api_id=provider_openai.id),
                RouteNodeCreate(api_id=provider_anthropic.id),
            ],
        )
        route = service.create_route(db_session, payload)

        service.select_provider_and_model(db_session, route.id)
        service.reset_state(route.id)
        state = service.get_state(route.id)

        assert len(state.get("round_robin_indices", {})) == 0


class TestBackupAndRestore:
    def test_backup_includes_routes(
        self,
        db_session: Session,
        provider_openai: ExternalAPI,
    ) -> None:
        from backend.app.services.backup import write_backup
        import json

        payload = ModelRouteCreate(
            name="backup-test-route",
            mode="auto",
            nodes=[RouteNodeCreate(api_id=provider_openai.id)],
        )
        service = get_routing_service()
        service.create_route(db_session, payload)

        backup_path = write_backup(db_session)
        backup_data = json.loads(backup_path.read_text())

        assert "routes" in backup_data
        assert len(backup_data["routes"]) > 0
        assert backup_data["routes"][0]["name"] == "backup-test-route"

    def test_restore_includes_routes(
        self,
        db_session: Session,
        provider_openai: ExternalAPI,
        settings,
    ) -> None:
        from backend.app.services.backup import restore_from_backup, write_backup

        payload = ModelRouteCreate(
            name="restore-test-route",
            mode="specific",
            nodes=[RouteNodeCreate(api_id=provider_openai.id, models=["gpt-4"])],
        )
        service = get_routing_service()
        service.create_route(db_session, payload)

        write_backup(db_session)

        db_session.query(ModelRoute).delete()
        db_session.commit()

        result = restore_from_backup(db_session)

        assert result.get("routes", 0) > 0
        restored_routes = db_session.query(ModelRoute).all()
        assert len(restored_routes) > 0
        assert restored_routes[0].name == "restore-test-route"


class TestInactiveRoute:
    def test_inactive_route_raises_error(
        self,
        db_session: Session,
        provider_openai: ExternalAPI,
    ) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="inactive-route",
            mode="auto",
            is_active=False,
            nodes=[RouteNodeCreate(api_id=provider_openai.id)],
        )
        route = service.create_route(db_session, payload)

        with pytest.raises(RouteServiceError, match="not active"):
            service.select_provider_and_model(db_session, route.id)


class TestModelNodeOverrides:
    def test_node_with_model_override(
        self,
        db_session: Session,
        provider_openai: ExternalAPI,
    ) -> None:
        service = get_routing_service()

        payload = ModelRouteCreate(
            name="model-override-route",
            mode="auto",
            nodes=[
                RouteNodeCreate(api_id=provider_openai.id, models=["gpt-3.5-turbo"]),
            ],
        )
        route = service.create_route(db_session, payload)

        provider_id, model = service.select_provider_and_model(db_session, route.id)

        assert model == "gpt-3.5-turbo"
