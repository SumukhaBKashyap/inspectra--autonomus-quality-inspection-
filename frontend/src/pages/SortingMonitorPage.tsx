import React, { useState, useEffect } from 'react';
import {
  fetchHardwareStatus,
  fetchStatistics,
  controlServo,
  controlConveyor,
  triggerEmergencyStop,
  resetHardware,
  fetchOperationMode,
  setOperationMode,
  HardwareState,
  DashboardStats,
} from '../services/api';
import {
  RotateCw,
  ArrowRight,
  Split,
  Power,
  AlertOctagon,
  RefreshCw,
  Cpu,
  Layers,
  CheckCircle2,
  Sliders,
  Box,
  Wrench,
  Zap,
  Activity,
  Eye,
} from 'lucide-react';

export const SortingMonitorPage: React.FC = () => {
  const [hw, setHw] = useState<HardwareState | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [opMode, setOpMode] = useState<'manual' | 'automated'>('manual');
  const [loading, setLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [h, s, m] = await Promise.all([
        fetchHardwareStatus(),
        fetchStatistics(),
        fetchOperationMode().catch(() => ({ mode: 'manual' as const, is_auto_running: false })),
      ]);
      setHw(h);
      setStats(s);
      if (m && m.mode) setOpMode(m.mode);
    } catch (e) {
      console.error(e);
    }
  };

  const handleToggleMode = async (targetMode: 'manual' | 'automated') => {
    setLoading(true);
    setActionMessage(`Switching to ${targetMode.toUpperCase()} mode...`);
    try {
      const res = await setOperationMode(targetMode);
      if (res && res.mode) setOpMode(res.mode as any);
      setActionMessage(`Active mode is now: ${targetMode.toUpperCase()}`);
    } catch (e: any) {
      setActionMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
      setTimeout(() => setActionMessage(null), 3500);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 2500);
    return () => clearInterval(interval);
  }, []);

  const handleServo = async (action: string, label: string) => {
    setLoading(true);
    setActionMessage(`Executing ${label}...`);
    try {
      await controlServo(action);
      await loadData();
      setActionMessage(`${label} completed successfully`);
    } catch (e: any) {
      setActionMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
      setTimeout(() => setActionMessage(null), 3000);
    }
  };

  const handleConveyor = async (id: number, action: 'start' | 'stop', label: string) => {
    setLoading(true);
    setActionMessage(`Switching Conveyor ${id} to ${action.toUpperCase()}...`);
    try {
      await controlConveyor(id, action);
      await loadData();
      setActionMessage(`Conveyor ${id} ${action.toUpperCase()} OK`);
    } catch (e: any) {
      setActionMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
      setTimeout(() => setActionMessage(null), 3000);
    }
  };

  const handleEStop = async () => {
    setLoading(true);
    setActionMessage('EMERGENCY STOP TRIGGERED!');
    try {
      await triggerEmergencyStop();
      await loadData();
    } catch (e: any) {
      setActionMessage(`E-Stop error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setLoading(true);
    setActionMessage('Resetting all hardware to home baseline...');
    try {
      await resetHardware();
      await loadData();
      setActionMessage('Hardware reset complete');
    } catch (e: any) {
      setActionMessage(`Reset error: ${e.message}`);
    } finally {
      setLoading(false);
      setTimeout(() => setActionMessage(null), 3000);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Emergency Bar */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-lg">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-white tracking-tight">Mechanical Sorting & Actuator Monitor</h1>
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full font-mono uppercase font-semibold ${
                hw?.simulation_mode
                  ? 'bg-amber-950 text-amber-400 border border-amber-800'
                  : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
              }`}
            >
              {hw?.simulation_mode ? 'Hardware Simulation' : 'Connected to Arduino'}
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Physical Prototype Stage 1 (Feeding) → Stage 2 (Platform SG90) → Stage 3 (Transfer Pusher & Diverter Arm)
          </p>
        </div>

        {/* Global Emergency Stop & Reset */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <button
            onClick={handleReset}
            disabled={loading}
            className="px-4 py-2.5 rounded-lg border border-industrial-700 bg-industrial-850 hover:bg-industrial-800 text-slate-300 text-xs font-mono font-bold flex items-center gap-2 transition-colors"
          >
            <RefreshCw className="w-4 h-4" /> Reset System
          </button>
          <button
            onClick={handleEStop}
            className="flex-1 md:flex-none px-6 py-2.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-mono font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-all shadow-lg shadow-rose-950 glow-rose"
          >
            <AlertOctagon className="w-4 h-4" /> EMERGENCY STOP
          </button>
        </div>
      </div>

      {/* Mode Switcher Banner: Option 1 (Manual Section) vs Option 2 (Fully Automated) */}
      <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-lg">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className={`p-3 rounded-xl border ${
              opMode === 'automated'
                ? 'bg-emerald-950 text-emerald-400 border-emerald-800 glow-emerald'
                : 'bg-amber-950 text-amber-400 border-amber-800'
            }`}>
              {opMode === 'automated' ? <Zap className="w-6 h-6 fill-current animate-pulse" /> : <Wrench className="w-6 h-6" />}
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-base font-bold text-white tracking-tight font-mono uppercase">
                  Operation Mode: {opMode === 'automated' ? 'Option 2: Fully Automated (Sensor & Controller)' : 'Option 1: Manual Section (Buttons & Jog Controls)'}
                </h2>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                  opMode === 'automated'
                    ? 'bg-emerald-950 text-emerald-300 border border-emerald-800 animate-pulse'
                    : 'bg-amber-950 text-amber-300 border border-amber-800'
                }`}>
                  {opMode === 'automated' ? 'AUTO CLOSED-LOOP' : 'MANUAL OVERRIDE'}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-1">
                {opMode === 'automated'
                  ? 'All conveyors, servos, and sorting are engaged automatically by sensors and Arduino controller without manual clicking.'
                  : 'Manual section active: use the buttons below to test individual conveyors, servos, and diverter arm angles.'}
              </p>
            </div>
          </div>

          {/* Mode Switcher Buttons */}
          <div className="flex items-center gap-2 p-1.5 rounded-xl bg-industrial-950 border border-industrial-800 font-mono text-xs w-full lg:w-auto">
            <button
              onClick={() => handleToggleMode('manual')}
              disabled={loading}
              className={`flex-1 lg:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-bold transition-all ${
                opMode === 'manual'
                  ? 'bg-amber-600 text-white shadow-md shadow-amber-950 border border-amber-400'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-industrial-850'
              }`}
            >
              <Wrench className="w-4 h-4" />
              1. MANUAL SECTION
            </button>
            <button
              onClick={() => handleToggleMode('automated')}
              disabled={loading}
              className={`flex-1 lg:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-bold transition-all ${
                opMode === 'automated'
                  ? 'bg-emerald-600 text-white shadow-md shadow-emerald-950 animate-pulse border border-emerald-400'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-industrial-850'
              }`}
            >
              <Zap className="w-4 h-4 fill-current" />
              2. FULLY AUTOMATED
            </button>
          </div>
        </div>

        {/* Real-time Optical Sensor Inputs (Pins 2 & 3) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4 pt-4 border-t border-industrial-800 font-mono text-xs">
          <div className="flex items-center justify-between p-3 rounded-lg bg-industrial-850 border border-industrial-800">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-cyan-400" />
              <div>
                <span className="text-slate-300 font-bold block">Arrival Optical Sensor (Stage 2 Platform)</span>
                <span className="text-slate-500 text-[11px]">Arduino Digital Pin 2 (Active LOW)</span>
              </div>
            </div>
            <span className={`px-2.5 py-1 rounded text-xs font-bold ${
              hw?.actuators?.arrival_sensor
                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800 animate-pulse'
                : 'bg-industrial-900 text-slate-400 border border-industrial-750'
            }`}>
              {hw?.actuators?.arrival_sensor ? '● COMPONENT PRESENT' : '○ BEAM CLEAR'}
            </span>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-industrial-850 border border-industrial-800">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-cyan-400" />
              <div>
                <span className="text-slate-300 font-bold block">Sorting Optical Sensor (Stage 3 Diverter)</span>
                <span className="text-slate-500 text-[11px]">Arduino Digital Pin 3 (Active LOW)</span>
              </div>
            </div>
            <span className={`px-2.5 py-1 rounded text-xs font-bold ${
              hw?.actuators?.sorting_sensor
                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800 animate-pulse'
                : 'bg-industrial-900 text-slate-400 border border-industrial-750'
            }`}>
              {hw?.actuators?.sorting_sensor ? '● AT SORTING ARM' : '○ BEAM CLEAR'}
            </span>
          </div>
        </div>
      </div>

      {actionMessage && (
        <div className="bg-cyan-950/60 border border-cyan-800 text-cyan-300 font-mono text-xs px-4 py-2.5 rounded-lg flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
          {actionMessage}
        </div>
      )}

      {/* Sorting Bins KPI Counters */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Nut Bin */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-4 flex items-center justify-between border-l-4 border-l-cyan-500">
          <div>
            <div className="text-xs font-mono uppercase text-slate-400">Nut Collection Bin</div>
            <div className="text-3xl font-bold font-mono text-cyan-400 mt-1">{stats?.nut_count ?? 0}</div>
            <div className="text-[11px] text-slate-500 font-mono mt-0.5">Diverted at Servo 3 (45°)</div>
          </div>
          <div className="p-3 rounded-lg bg-cyan-950/60 border border-cyan-800 text-cyan-400">
            <Box className="w-6 h-6" />
          </div>
        </div>

        {/* Washer Bin */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-4 flex items-center justify-between border-l-4 border-l-emerald-500">
          <div>
            <div className="text-xs font-mono uppercase text-slate-400">Washer Collection Bin</div>
            <div className="text-3xl font-bold font-mono text-emerald-400 mt-1">{stats?.washer_count ?? 0}</div>
            <div className="text-[11px] text-slate-500 font-mono mt-0.5">Diverted at Servo 3 (135°)</div>
          </div>
          <div className="p-3 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-400">
            <Box className="w-6 h-6" />
          </div>
        </div>

        {/* Manual Rejection / Stop */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-4 flex items-center justify-between border-l-4 border-l-rose-500">
          <div>
            <div className="text-xs font-mono uppercase text-slate-400">Manual Rejections / Stops</div>
            <div className="text-3xl font-bold font-mono text-rose-400 mt-1">
              {(stats?.fail_count ?? 0) + (stats?.review_count ?? 0)}
            </div>
            <div className="text-[11px] text-slate-500 font-mono mt-0.5">Halted for manual handling</div>
          </div>
          <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-400">
            <AlertOctagon className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Mechanical Prototype Layout Diagram */}
      <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between border-b border-industrial-800 pb-3 mb-6">
          <h2 className="text-sm font-semibold font-mono text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Sliders className="w-4 h-4 text-cyan-400" />
            Physical Prototype Stage Diagram
          </h2>
          <span className="text-xs font-mono text-slate-400">3-Stage Conveyor & Servo Flow</span>
        </div>

        {/* Schematic Layout Flow */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Stage 1: Feeding Conveyor */}
          <div className="bg-industrial-950 rounded-xl p-4 border border-industrial-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-mono font-bold text-slate-300 uppercase">Stage 1: Feeding Conveyor</span>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                    hw?.actuators?.conveyor1 ? 'bg-emerald-950 text-emerald-400' : 'bg-industrial-800 text-slate-500'
                  }`}
                >
                  {hw?.actuators?.conveyor1 ? 'MOTOR ON' : 'STOPPED'}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Feeds parts down slope onto stationary inspection platform.
              </p>
            </div>
            <div className="mt-4 flex gap-2">
              <button
                onClick={() => handleConveyor(1, 'start', 'Conveyor 1 Start')}
                className="flex-1 py-1.5 rounded bg-emerald-900/60 hover:bg-emerald-800 text-emerald-300 text-xs font-mono border border-emerald-700"
              >
                Run Feed
              </button>
              <button
                onClick={() => handleConveyor(1, 'stop', 'Conveyor 1 Stop')}
                className="flex-1 py-1.5 rounded bg-industrial-800 hover:bg-industrial-700 text-slate-300 text-xs font-mono border border-industrial-700"
              >
                Halt Feed
              </button>
            </div>
          </div>

          {/* Stage 2: Inspection Platform (Servo 1) */}
          <div className="bg-industrial-950 rounded-xl p-4 border border-cyan-800/60 flex flex-col justify-between glow-cyan">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-mono font-bold text-cyan-400 uppercase">Stage 2: Inspection Platform</span>
                <span className="text-xs font-mono font-bold text-white px-2 py-0.5 rounded bg-cyan-950 border border-cyan-700">
                  Servo 1: {hw?.actuators?.servo1 ?? 0}°
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Stations part for 0° CV capture, rotates 90° with SG90 Servo 1 for second view, runs laser & eddy scan.
              </p>
            </div>
            <div className="mt-4">
              <button
                onClick={() => handleServo('rotate_90', 'Servo 1 90° Rotation')}
                className="w-full py-2 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-mono font-bold flex items-center justify-center gap-1.5 shadow"
              >
                <RotateCw className="w-3.5 h-3.5" /> Test Servo 1 (0° → 90° Sweep)
              </button>
            </div>
          </div>

          {/* Stage 3: Transfer Pusher & Sorting (Servo 2 & Servo 3) */}
          <div className="bg-industrial-950 rounded-xl p-4 border border-industrial-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-mono font-bold text-slate-300 uppercase">Stage 3: Sorting Conveyor</span>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                    hw?.actuators?.conveyor2 ? 'bg-emerald-950 text-emerald-400' : 'bg-industrial-800 text-slate-500'
                  }`}
                >
                  {hw?.actuators?.conveyor2 ? 'MOTOR ON' : 'STOPPED'}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Servo 2 pushes PASS parts onto conveyor. Servo 3 swinging arm diverts NUT (45°) or WASHER (135°).
              </p>
            </div>
            <div className="mt-4 space-y-2">
              <button
                onClick={() => handleServo('transfer', 'Servo 2 Pusher')}
                className="w-full py-1.5 rounded bg-industrial-850 hover:bg-industrial-800 text-slate-200 text-xs font-mono border border-industrial-700 flex items-center justify-center gap-1.5"
              >
                <ArrowRight className="w-3.5 h-3.5" /> Test Servo 2 Pusher
              </button>
              <div className="flex gap-2">
                <button
                  onClick={() => handleServo('divert_nut', 'Servo 3 to Nut Bin')}
                  className="flex-1 py-1.5 rounded bg-cyan-950 hover:bg-cyan-900 text-cyan-300 text-xs font-mono border border-cyan-800"
                >
                  Divert Nut (45°)
                </button>
                <button
                  onClick={() => handleServo('divert_washer', 'Servo 3 to Washer Bin')}
                  className="flex-1 py-1.5 rounded bg-emerald-950 hover:bg-emerald-900 text-emerald-300 text-xs font-mono border border-emerald-800"
                >
                  Divert Washer (135°)
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Manual Actuator Diagnostics Table */}
      <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-sm">
        <h2 className="text-sm font-semibold font-mono text-slate-200 uppercase tracking-wider mb-4">
          Direct Actuator Control Matrix
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 font-mono text-xs">
          {/* Servo 1 Card */}
          <div className="p-3.5 rounded-lg bg-industrial-850 border border-industrial-800 space-y-2">
            <div className="text-slate-400 font-bold">SG90 SERVO 1 (ROTATOR)</div>
            <div className="text-slate-500 text-[11px]">Pin: D9 | Neutral: 0° | Active: 90°</div>
            <div className="text-cyan-400 font-bold">Current: {hw?.actuators?.servo1 ?? 0}°</div>
            <button
              onClick={() => handleServo('rotate_90', 'Servo 1 90°')}
              className="w-full py-1.5 rounded bg-industrial-800 hover:bg-industrial-700 text-slate-300 border border-industrial-700"
            >
              Trigger 90° Cycle
            </button>
          </div>

          {/* Servo 2 Card */}
          <div className="p-3.5 rounded-lg bg-industrial-850 border border-industrial-800 space-y-2">
            <div className="text-slate-400 font-bold">SG90 SERVO 2 (PUSHER)</div>
            <div className="text-slate-500 text-[11px]">Pin: D10 | Rest: 0° | Push: 65°</div>
            <div className="text-cyan-400 font-bold">Current: {hw?.actuators?.servo2 ?? 0}°</div>
            <button
              onClick={() => handleServo('transfer', 'Servo 2 Push')}
              className="w-full py-1.5 rounded bg-industrial-800 hover:bg-industrial-700 text-slate-300 border border-industrial-700"
            >
              Trigger Push Cycle
            </button>
          </div>

          {/* Servo 3 Card */}
          <div className="p-3.5 rounded-lg bg-industrial-850 border border-industrial-800 space-y-2">
            <div className="text-slate-400 font-bold">SG90 SERVO 3 (DIVERTER)</div>
            <div className="text-slate-500 text-[11px]">Pin: D11 | Nut: 45° | Washer: 135°</div>
            <div className="text-cyan-400 font-bold">Current: {hw?.actuators?.servo3 ?? 90}°</div>
            <div className="flex gap-2">
              <button
                onClick={() => handleServo('divert_nut', 'Nut Divert')}
                className="flex-1 py-1.5 rounded bg-industrial-800 hover:bg-industrial-700 text-slate-300 border border-industrial-700 text-[11px]"
              >
                Nut (45°)
              </button>
              <button
                onClick={() => handleServo('divert_washer', 'Washer Divert')}
                className="flex-1 py-1.5 rounded bg-industrial-800 hover:bg-industrial-700 text-slate-300 border border-industrial-700 text-[11px]"
              >
                Wash (135°)
              </button>
            </div>
          </div>

          {/* Conveyor 1 & 2 Controls */}
          <div className="p-3.5 rounded-lg bg-industrial-850 border border-industrial-800 space-y-2">
            <div className="text-slate-400 font-bold">CONVEYORS (STAGE 1 & 3)</div>
            <div className="text-slate-500 text-[11px]">Pins: D5 (Feed) & D6 (Sort)</div>
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => handleConveyor(1, hw?.actuators?.conveyor1 ? 'stop' : 'start', 'Conveyor 1')}
                className="flex-1 py-1.5 rounded bg-industrial-800 hover:bg-industrial-700 text-slate-300 border border-industrial-700 text-[11px]"
              >
                {hw?.actuators?.conveyor1 ? 'Stop Conv 1' : 'Run Conv 1'}
              </button>
              <button
                onClick={() => handleConveyor(2, hw?.actuators?.conveyor2 ? 'stop' : 'start', 'Conveyor 2')}
                className="flex-1 py-1.5 rounded bg-industrial-800 hover:bg-industrial-700 text-slate-300 border border-industrial-700 text-[11px]"
              >
                {hw?.actuators?.conveyor2 ? 'Stop Conv 2' : 'Run Conv 2'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

