from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...schemas.route import (
    ModelRouteCreate,
    ModelRouteRead,
    ModelRouteUpdate,
    RoutingSelectionResponse,
    RoutingStateResponse,
)
from ...services.routing import get_routing_service

router = APIRouter(prefix="/api/model-routes", tags=["model-routes"])


@router.get("", response_model=list[ModelRouteRead])
def list_routes(db: Session = Depends(get_db)) -> list[ModelRouteRead]:
    service = get_routing_service()
    routes = service.list_routes(db)
    
    # Manual serialization for each route
    result = []
    for route in routes:
        nodes_data = []
        for node in route.route_nodes:
            node_dict = {
                "id": node.id,
                "route_id": node.route_id,
                "api_id": node.api_id,
                "models": node.models,
                "strategy": node.strategy,
                "priority": node.priority,
                "node_metadata": node.node_metadata,
                "api_name": node.api_name,
                "created_at": node.created_at,
                "updated_at": node.updated_at,
            }
            nodes_data.append(node_dict)
        
        route_dict = {
            "id": route.id,
            "name": route.name,
            "mode": route.mode,
            "config": route.config,
            "is_active": route.is_active,
            "created_at": route.created_at,
            "updated_at": route.updated_at,
            "nodes": nodes_data,
        }
        
        result.append(ModelRouteRead(**route_dict))
    
    return result


@router.post("", response_model=ModelRouteRead, status_code=201)
def create_route(payload: ModelRouteCreate, db: Session = Depends(get_db)) -> ModelRouteRead:
    service = get_routing_service()
    route = service.create_route(db, payload)
    
    # Manual serialization to work around the Pydantic issue
    nodes_data = []
    for node in route.route_nodes:
        node_dict = {
            "id": node.id,
            "route_id": node.route_id,
            "api_id": node.api_id,
            "models": node.models,
            "strategy": node.strategy,
            "priority": node.priority,
            "node_metadata": node.node_metadata,
            "api_name": node.api_name,
            "created_at": node.created_at,
            "updated_at": node.updated_at,
        }
        nodes_data.append(node_dict)
    
    route_dict = {
        "id": route.id,
        "name": route.name,
        "mode": route.mode,
        "config": route.config,
        "is_active": route.is_active,
        "created_at": route.created_at,
        "updated_at": route.updated_at,
        "nodes": nodes_data,
    }
    
    return ModelRouteRead(**route_dict)


@router.get("/{route_id}", response_model=ModelRouteRead)
def get_route(route_id: int, db: Session = Depends(get_db)) -> ModelRouteRead:
    service = get_routing_service()
    route = service.get_route(db, route_id)
    
    # Manual serialization to work around the Pydantic issue
    nodes_data = []
    for node in route.route_nodes:
        node_dict = {
            "id": node.id,
            "route_id": node.route_id,
            "api_id": node.api_id,
            "models": node.models,
            "strategy": node.strategy,
            "priority": node.priority,
            "node_metadata": node.node_metadata,
            "api_name": node.api_name,
            "created_at": node.created_at,
            "updated_at": node.updated_at,
        }
        nodes_data.append(node_dict)
    
    route_dict = {
        "id": route.id,
        "name": route.name,
        "mode": route.mode,
        "config": route.config,
        "is_active": route.is_active,
        "created_at": route.created_at,
        "updated_at": route.updated_at,
        "nodes": nodes_data,
    }
    
    return ModelRouteRead(**route_dict)


@router.patch("/{route_id}", response_model=ModelRouteRead)
def update_route(
    route_id: int,
    payload: ModelRouteUpdate,
    db: Session = Depends(get_db),
) -> ModelRouteRead:
    service = get_routing_service()
    route = service.update_route(db, route_id, payload)
    
    # Manual serialization to work around the Pydantic issue
    nodes_data = []
    for node in route.route_nodes:
        node_dict = {
            "id": node.id,
            "route_id": node.route_id,
            "api_id": node.api_id,
            "models": node.models,
            "strategy": node.strategy,
            "priority": node.priority,
            "node_metadata": node.node_metadata,
            "api_name": node.api_name,
            "created_at": node.created_at,
            "updated_at": node.updated_at,
        }
        nodes_data.append(node_dict)
    
    route_dict = {
        "id": route.id,
        "name": route.name,
        "mode": route.mode,
        "config": route.config,
        "is_active": route.is_active,
        "created_at": route.created_at,
        "updated_at": route.updated_at,
        "nodes": nodes_data,
    }
    
    return ModelRouteRead(**route_dict)


@router.delete("/{route_id}", status_code=204)
def delete_route(route_id: int, db: Session = Depends(get_db)) -> Response:
    service = get_routing_service()
    service.delete_route(db, route_id)
    return Response(status_code=204)


@router.post("/{route_id}/select", response_model=RoutingSelectionResponse)
def select_provider_and_model(
    route_id: int,
    model: str | None = Query(default=None, description="Optional model hint for selection"),
    db: Session = Depends(get_db),
) -> RoutingSelectionResponse:
    from ...db.models import ExternalAPI

    service = get_routing_service()
    provider_id, selected_model = service.select_provider_and_model(db, route_id, model)
    provider = db.query(ExternalAPI).filter(ExternalAPI.id == provider_id).one()
    return RoutingSelectionResponse(
        provider_id=provider_id,
        provider_name=provider.name,
        model=selected_model,
    )


@router.get("/{route_id}/state", response_model=RoutingStateResponse)
def get_route_state(
    route_id: int,
    db: Session = Depends(get_db),
) -> RoutingStateResponse:
    service = get_routing_service()
    route = service.get_route(db, route_id)
    state = service.get_state(route_id)
    return RoutingStateResponse(
        route_id=route_id,
        route_name=route.name,
        state=state,
    )
