export interface ModelRoute {
  id: number;
  name: string;
  mode: 'auto' | 'specific' | 'multi';
  config: Record<string, any>;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
  nodes: RouteNode[];
}

export interface RouteNode {
  id: number;
  routeId: number;
  apiId: number;
  apiName: string;
  models: string[];
  strategy: 'round-robin' | 'failover';
  priority: number;
  nodeMetadata: Record<string, any>;
}

export interface ModelRouteCreate {
  name: string;
  mode: 'auto' | 'specific' | 'multi';
  config?: Record<string, any>;
  isActive?: boolean;
}

export interface ModelRouteUpdate {
  name?: string;
  mode?: 'auto' | 'specific' | 'multi';
  config?: Record<string, any>;
  isActive?: boolean;
}

export interface RouteNodeCreate {
  apiId: number;
  models: string[];
  strategy: 'round-robin' | 'failover';
  priority: number;
  nodeMetadata?: Record<string, any>;
}

export interface RouteNodeUpdate {
  apiId?: number;
  models?: string[];
  strategy?: 'round-robin' | 'failover';
  priority?: number;
  nodeMetadata?: Record<string, any>;
}

export interface RoutingSelectionResponse {
  providerId: number;
  providerName: string;
  model: string;
}

export interface RoutingStateResponse {
  routeId: number;
  routeName: string;
  state: Record<string, any>;
}

export interface ModelRouteFormValues {
  name: string;
  mode: 'auto' | 'specific' | 'multi';
  config?: Record<string, any>;
  isActive: boolean;
}

export interface RouteNodeFormValues {
  apiId: number;
  models: string[];
  strategy: 'round-robin' | 'failover';
  priority: number;
  nodeMetadata?: Record<string, any>;
}