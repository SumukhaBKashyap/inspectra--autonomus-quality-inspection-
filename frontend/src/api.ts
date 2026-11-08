const BASE = '/api';

export interface InspectionSummary {
  id: string;
  created_at: string | null;
  outcome: string | null;
  reason: string | null;
}

export interface InspectionDetail {
  id: string;
  created_at: string | null;
  cv_result: {
    component_type: string;
    dimensions: Record<string, number>;
    defects: string[];
  } | null;
  laser_result: {
    height_map?: { cols: number; values: (number | null)[] };
    profile_data?: Array<{ x: number; height: number; ref_baseline: number }>;
    anomalies: string[];
  } | null;
  eddy_result: {
    simulated_readings: Array<{
      coil_index: number;
      angle_deg: number;
      impedance: number;
      deviation_pct: number;
    }>;
    anomalies: string[];
  } | null;
  decision: {
    outcome: string;
    reason: string;
    created_at: string | null;
  } | null;
}

export async function fetchInspections(): Promise<InspectionSummary[]> {
  const res = await fetch(`${BASE}/inspections`);
  if (!res.ok) throw new Error('Failed to fetch inspections');
  return res.json();
}

export async function fetchInspection(id: string): Promise<InspectionDetail> {
  const res = await fetch(`${BASE}/inspections/${id}`);
  if (!res.ok) throw new Error('Failed to fetch inspection');
  return res.json();
}

export async function startInspection(): Promise<{ inspection_id: string }> {
  const res = await fetch(`${BASE}/inspection/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error('Failed to start inspection');
  return res.json();
}

export function openInspectionWS(inspectionId: string, onMessage: (data: unknown) => void): WebSocket {
  const host = typeof window !== 'undefined' && window.location.host ? window.location.host : 'localhost:8000';
  const proto = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${proto}//${host}/ws/inspection/${inspectionId}`);
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  return ws;
}

