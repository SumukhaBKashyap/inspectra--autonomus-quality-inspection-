/**
 * Inspectra Client API & WebSocket Service
 */

const isBrowser = typeof window !== 'undefined';
const proto = isBrowser && window.location.protocol === 'https:' ? 'https:' : 'http:';
const wsProto = isBrowser && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const host = isBrowser && window.location.host ? window.location.host : 'localhost:8000';

export const BACKEND_URL = isBrowser && window.location.origin ? window.location.origin : `${proto}//${host}`;
export const WS_URL = `${wsProto}//${host}`;

export interface InspectionSummary {
  id: string;
  created_at: string;
  status: string;
  duration_ms: number;
  outcome: 'PASS' | 'FAIL' | 'REVIEW' | 'UNKNOWN';
  component_type: 'NUT' | 'WASHER' | 'UNKNOWN';
  cv_status: string;
  laser_status: string;
  eddy_status: string;
  reason: string;
  sorting_command: string;
  defects_count: number;
  dimensions?: Record<string, any>;
}

export interface TargetDimensions {
  required_outer_mm: number;
  required_inner_mm: number;
  required_tolerance_mm: number;
  preset: string;
}

export interface DashboardStats {
  total: number;
  pass_count: number;
  fail_count: number;
  review_count: number;
  nut_count: number;
  washer_count: number;
  unknown_count: number;
  pass_rate_pct: number;
  fail_rate_pct: number;
  review_rate_pct: number;
  defects_by_type: {
    cv_surface_defects: number;
    laser_height_anomalies: number;
    eddy_anomalies_simulated: number;
  };
}

export interface InspectionDetail {
  id: string;
  created_at: string;
  status: string;
  duration_ms: number;
  images: Array<{
    id: number;
    label: string;
    filename: string;
    url: string;
    timestamp: string;
  }>;
  cv_result: {
    status: string;
    component_type: string;
    confidence: number;
    circularity: number;
    corners_detected: number;
    dimensions: Record<string, any>;
    tolerances: Record<string, any>;
    defects: string[];
    multi_angle_match: boolean;
  } | null;
  laser_result: {
    status: string;
    max_height_variation_mm: number;
    mean_height_mm: number;
    peak_height_mm: number;
    is_calibrated: boolean;
    profile_data: Array<{ x: number; height: number; ref_baseline: number }>;
    anomalies: string[];
  } | null;
  eddy_result: {
    status: string;
    is_simulated?: boolean;
    nominal_impedance: number;
    max_deviation_pct: number;
    operating_freq_khz?: number;
    nominal_phase_deg?: number;
    lift_off_um?: number;
    snr_db?: number;
    metal_tested?: string;
    analysis_mode?: string;
    simulated_readings: Array<{
      coil_index: number;
      angle_deg: number;
      impedance: number;
      nominal: number;
      deviation_pct: number;
      phase_deg?: number;
      lift_off_um?: number;
      is_anomaly: boolean;
      data_source: string;
    }>;
    anomalies: string[];
  } | null;
  decision: {
    outcome: string;
    component_type: string;
    cv_status: string;
    laser_status: string;
    eddy_status: string;
    reason: string;
    sorting_command: string;
    created_at: string;
  } | null;
}

export interface HardwareState {
  simulation_mode: boolean;
  connected: boolean;
  serial_port: string;
  baud_rate: number;
  last_error: string | null;
  actuators: {
    servo1: number;
    servo2: number;
    servo3: number;
    conveyor1: boolean;
    conveyor2: boolean;
    arrival_sensor: boolean;
    sorting_sensor: boolean;
  };
}

export async function fetchStatistics(): Promise<DashboardStats> {
  const res = await fetch(`${BACKEND_URL}/api/inspections/stats`);
  if (!res.ok) throw new Error('Failed to fetch statistics');
  return res.json();
}

export async function fetchInspections(
  skip = 0,
  limit = 50,
  outcome?: string,
  component_type?: string
): Promise<InspectionSummary[]> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  if (outcome) params.append('outcome', outcome);
  if (component_type) params.append('component_type', component_type);

  const res = await fetch(`${BACKEND_URL}/api/inspections?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch inspections');
  return res.json();
}

export async function fetchInspection(id: string): Promise<InspectionDetail> {
  const res = await fetch(`${BACKEND_URL}/api/inspections/${id}`);
  if (!res.ok) throw new Error('Failed to fetch inspection detail');
  return res.json();
}

export interface MetalProfile {
  name: string;
  category: string;
  relative_permeability: number;
  conductivity_iacs_pct: number;
  base_impedance_ohms: number;
  nominal_phase_deg: number;
  operating_freq_khz: number;
  laser_roughness_tol_mm: number;
  expected_color_tone: string;
  description: string;
}

export interface AnalysisMode {
  name: string;
  description: string;
  cv_defect_tolerance_pct: number;
  dim_tolerance_mult: number;
  laser_profile_strictness: number;
  eddy_tolerance_pct: number;
}

export interface MaterialProfilesResponse {
  metals: Record<string, MetalProfile>;
  modes: Record<string, AnalysisMode>;
  selected_metal: string;
  analysis_type: string;
}

export async function fetchMetalProfiles(): Promise<MaterialProfilesResponse> {
  const res = await fetch(`${BACKEND_URL}/api/settings/metal-profiles`);
  if (!res.ok) throw new Error('Failed to fetch metal profiles');
  return res.json();
}

export async function updateMaterialSelection(
  metalType?: string,
  analysisMode?: string
): Promise<{
  status: string;
  selected_metal: string;
  analysis_type: string;
  active_profile: MetalProfile;
  active_mode_info: AnalysisMode;
}> {
  const res = await fetch(`${BACKEND_URL}/api/settings/material-selection`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ metal_type: metalType, analysis_mode: analysisMode }),
  });
  if (!res.ok) throw new Error('Failed to update material selection');
  return res.json();
}

export async function startInspection(
  forceType?: string,
  forceDefect = false,
  metalType?: string,
  analysisMode?: string
): Promise<{ inspection_id: string }> {
  const res = await fetch(`${BACKEND_URL}/api/inspection/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      force_type: forceType,
      force_defect: forceDefect,
      metal_type: metalType,
      analysis_mode: analysisMode,
    }),
  });
  if (!res.ok) throw new Error('Failed to start inspection');
  return res.json();
}

export async function startAutoInspection(
  metalType?: string,
  analysisMode?: string
): Promise<{ status: string; auto_mode: boolean }> {
  const res = await fetch(`${BACKEND_URL}/api/inspection/auto/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ metal_type: metalType, analysis_mode: analysisMode }),
  });
  if (!res.ok) throw new Error('Failed to start autonomous mode');
  return res.json();
}

export async function stopAutoInspection(): Promise<{ status: string; auto_mode: boolean }> {
  const res = await fetch(`${BACKEND_URL}/api/inspection/auto/stop`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to stop autonomous mode');
  return res.json();
}

export async function fetchAutoInspectionStatus(): Promise<{ auto_mode: boolean; is_inspecting: boolean }> {
  const res = await fetch(`${BACKEND_URL}/api/inspection/auto/status`);
  if (!res.ok) throw new Error('Failed to fetch auto inspection status');
  return res.json();
}

export async function fetchOperationMode(): Promise<{ mode: 'manual' | 'automated'; is_auto_running: boolean }> {
  const res = await fetch(`${BACKEND_URL}/api/hardware/mode`);
  if (!res.ok) throw new Error('Failed to fetch operation mode');
  return res.json();
}

export async function setOperationMode(mode: 'manual' | 'automated'): Promise<{ status: string; mode: string; is_auto_running: boolean }> {
  const res = await fetch(`${BACKEND_URL}/api/hardware/mode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode }),
  });
  if (!res.ok) throw new Error('Failed to set operation mode');
  return res.json();
}

export async function clearAllInspections(): Promise<void> {
  const res = await fetch(`${BACKEND_URL}/api/inspections`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to clear inspections');
}

export async function fetchHardwareStatus(): Promise<HardwareState> {
  const res = await fetch(`${BACKEND_URL}/api/hardware/status`);
  if (!res.ok) throw new Error('Failed to fetch hardware status');
  return res.json();
}

export async function controlServo(action: string): Promise<any> {
  const res = await fetch(`${BACKEND_URL}/api/hardware/servo/control`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action }),
  });
  return res.json();
}

export async function controlConveyor(conveyorId: number, action: 'start' | 'stop'): Promise<any> {
  const res = await fetch(`${BACKEND_URL}/api/hardware/conveyor/control`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conveyor_id: conveyorId, action }),
  });
  return res.json();
}

export async function triggerEmergencyStop(): Promise<any> {
  const res = await fetch(`${BACKEND_URL}/api/hardware/emergency_stop`, { method: 'POST' });
  return res.json();
}

export async function resetHardware(): Promise<any> {
  const res = await fetch(`${BACKEND_URL}/api/hardware/reset`, { method: 'POST' });
  return res.json();
}

export async function fetchSettings(): Promise<Record<string, any>> {
  const res = await fetch(`${BACKEND_URL}/api/settings`);
  if (!res.ok) throw new Error('Failed to fetch settings');
  return res.json();
}

export async function updateSettings(updates: Record<string, any>): Promise<any> {
  const res = await fetch(`${BACKEND_URL}/api/settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  return res.json();
}

export async function resetSettings(): Promise<any> {
  const res = await fetch(`${BACKEND_URL}/api/settings/reset`, { method: 'POST' });
  return res.json();
}

export async function fetchTargetDimensions(): Promise<TargetDimensions | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/settings/target-dimensions`);
    if (!res.ok) return null;
    return await res.json();
  } catch (e) {
    console.error(e);
    return null;
  }
}

export async function updateTargetDimensions(data: {
  required_outer_mm: number;
  required_inner_mm: number;
  required_tolerance_mm?: number;
  preset?: string;
}): Promise<TargetDimensions | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/settings/target-dimensions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (e) {
    console.error(e);
    return null;
  }
}

export function openInspectionWS(
  inspectionId: string,
  onMessage: (event: any) => void,
  onClose?: () => void,
  onError?: (err: any) => void
): WebSocket {
  const ws = new WebSocket(`${WS_URL}/ws/inspection/${inspectionId}`);
  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      onMessage(data);
    } catch (err) {
      console.error('WS parse error', err);
    }
  };
  if (onClose) ws.onclose = onClose;
  if (onError) ws.onerror = onError;
  return ws;
}

