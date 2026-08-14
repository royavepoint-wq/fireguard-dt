export type SpatialViewMode = "building" | "floor";

export type SpatialTone = "safe" | "warning" | "critical" | "muted";

export type RouteTone = "safe" | "warning" | "blocked";

export type SpatialVector3 = {
  x: number;
  y: number;
  z: number;
};

export type SpatialSize = {
  width: number;
  height: number;
  depth: number;
};

export type SpatialEntityType = "room" | "corridor" | "exit" | "stair" | "resource-node";

type SpatialEntityBase = {
  id: string;
  name: string;
  type: SpatialEntityType;
  floorId: string;
  position: SpatialVector3;
  size: SpatialSize;
  rotation?: number;
};

export type RoomLayout = SpatialEntityBase & {
  type: "room";
  zoneId?: string;
  roomId?: string;
};

export type CorridorLayout = SpatialEntityBase & {
  type: "corridor";
  zoneId?: string;
  corridorId?: string;
};

export type ExitLayout = SpatialEntityBase & {
  type: "exit";
  exitId: string;
};

export type StairLayout = SpatialEntityBase & {
  type: "stair";
  stairId: string;
};

export type ResourceNodeLayout = SpatialEntityBase & {
  type: "resource-node";
  resourceKind: "crew" | "drone";
  resourceId: string;
};

export type SpatialEntity = RoomLayout | CorridorLayout | ExitLayout | StairLayout | ResourceNodeLayout;

export type FloorLayout = {
  id: string;
  name: string;
  level: number;
  elevation: number;
  slabSize: { width: number; depth: number };
};

export type RouteLayout = {
  id: string;
  name: string;
  floorId: string;
  points: SpatialVector3[];
  defaultVisible: boolean;
};

export type BuildingLayout = {
  buildingId: string;
  floors: FloorLayout[];
  entities: SpatialEntity[];
  routes: RouteLayout[];
};

export type SpatialLayerVisibility = {
  occupants: boolean;
  hazards: boolean;
  routes: boolean;
  resources: boolean;
};

export type FloorPresentation = {
  floorId: string;
  elevation: number;
  isFocused: boolean;
  isDimmed: boolean;
};

export type SpatialRoomInfo = {
  roomId: string;
  name: string;
  floorId: string;
  floorName: string;
  zoneId: string | null;
  status: string;
  tone: SpatialTone;
  temperature: string;
  smoke: string;
  co: string;
  fireRisk: string;
  occupancy: string;
  density: string;
  vulnerableCount: string;
  evacuationStatus: string;
  hvacZone: string;
  sprinkler: string;
};

export type RoomVisualState = {
  roomId: string;
  tone: SpatialTone;
  label: string;
  isSelectedHazardRoom: boolean;
  info: SpatialRoomInfo;
};

export type CorridorVisualState = {
  corridorId: string;
  tone: SpatialTone;
};

export type ExitVisualState = {
  exitId: string;
  tone: SpatialTone;
  label: string;
  blocked: boolean;
};

export type HazardVisualState = {
  id: string;
  entityId: string;
  kind: "risk" | "smoke";
  tone: SpatialTone;
  visible: boolean;
};

export type OccupantVisualState = {
  id: string;
  zoneId: string;
  roomId: string;
  floorId: string;
  count: number;
  density: number;
  label: string;
  tone: SpatialTone;
  position: SpatialVector3;
};

export type ResponseVisualState = {
  id: string;
  resourceId: string;
  kind: "crew" | "drone";
  floorId: string;
  label: string;
  status: string;
  tone: SpatialTone;
  position: SpatialVector3;
};

export type RouteVisualState = {
  routeId: string;
  label: string;
  floorId: string;
  tone: RouteTone;
  points: SpatialVector3[];
  visible: boolean;
};

export type SpatialStateSummary = {
  buildingStatus: string;
  floors: number;
  activeHazardZones: number;
  blockedExits: number;
  occupancy: number;
  activeEvacuations: number;
  responseResources: number;
};

export type MappedSpatialState = {
  roomStates: Record<string, RoomVisualState>;
  corridorStates: Record<string, CorridorVisualState>;
  exitStates: Record<string, ExitVisualState>;
  hazards: HazardVisualState[];
  occupants: OccupantVisualState[];
  resources: ResponseVisualState[];
  routes: RouteVisualState[];
  summary: SpatialStateSummary;
};