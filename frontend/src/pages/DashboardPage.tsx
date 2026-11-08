import React, { useEffect, useState } from 'react';
import {
  fetchStatistics,
  fetchInspections,
  fetchHardwareStatus,
  fetchMetalProfiles,
  updateMaterialSelection,
  startAutoInspection,
  stopAutoInspection,
  fetchAutoInspectionStatus,
  DashboardStats,
  InspectionSummary,
  HardwareState,
  MetalProfile,
  AnalysisMode,
  InspectionDetail,
  fetchInspection,
  fetchTargetDimensions,
  updateTargetDimensions,
  TargetDimensions,
} from '../services/api';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  AreaChart,
  Area,
  CartesianGrid,
  ReferenceLine,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Layers,
  Cpu,
  ArrowRight,
  Activity,
  HardDrive,
  RefreshCw,
  Play,
  Flame,
  Settings2,
  ShieldCheck,
  Ruler,
  Sliders,
} from 'lucide-react';

interface Props {
  onNavigate: (view: any, id?: string) => void;
  onStartInspection: () => void;
}

export const DashboardPage: React.FC<Props> = ({ onNavigate, onStartInspection }) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recent, setRecent] = useState<InspectionSummary[]>([]);
  const [hw, setHw] = useState<HardwareState | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Material and Analysis criteria
  const [metals, setMetals] = useState<Record<string, MetalProfile>>({});
  const [modes, setModes] = useState<Record<string, AnalysisMode>>({});
  const [selectedMetal, setSelectedMetal] = useState<string>('carbon_steel');
  const [analysisType, setAnalysisType] = useState<string>('standard');
  const [isUpdatingMaterial, setIsUpdatingMaterial] = useState(false);
  const [autoMode, setAutoMode] = useState<boolean>(false);
  const [latestDetail, setLatestDetail] = useState<InspectionDetail | null>(null);

  // Calibrated Required Dimensions for Pass/Fail Decision
  const [reqOuter, setReqOuter] = useState<number>(10.0);
  const [reqInner, setReqInner] = useState<number>(5.0);
  const [reqTol, setReqTol] = useState<number>(0.45);
  const [preset, setPreset] = useState<string>('M5');
  const [isSavingTarget, setIsSavingTarget] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState('');

  const PRESETS: Record<string, { label: string; outer: number; inner: number; tol: number; desc: string }> = {
    'M3': { label: 'M3 Fastener', outer: 7.0, inner: 3.2, tol: 0.35, desc: 'OD 7.0mm / ID 3.2mm (Nut s=5.5mm)' },
    'M4': { label: 'M4 Fastener', outer: 9.0, inner: 4.3, tol: 0.35, desc: 'OD 9.0mm / ID 4.3mm (Nut s=7.0mm)' },
    'M5': { label: 'M5 Fastener', outer: 10.0, inner: 5.0, tol: 0.40, desc: 'OD 10.0mm / ID 5.0mm (Nut s=8.0mm)' },
    'M6': { label: 'M6 Fastener', outer: 12.0, inner: 6.0, tol: 0.45, desc: 'OD 12.0mm / ID 6.0mm (Nut s=10.0mm)' },
    'M8': { label: 'M8 Fastener', outer: 16.0, inner: 8.0, tol: 0.50, desc: 'OD 16.0mm / ID 8.0mm (Nut s=13.0mm)' },
  };

  const handleSaveDimensions = async (customOuter?: number, customInner?: number, customTol?: number, customPreset?: string) => {
    setIsSavingTarget(true);
    setSaveSuccessMsg('');
    try {
      const o = customOuter !== undefined ? customOuter : reqOuter;
      const i = customInner !== undefined ? customInner : reqInner;
      const t = customTol !== undefined ? customTol : reqTol;
      const p = customPreset || preset;
      const res = await updateTargetDimensions({
        required_outer_mm: Number(o),
        required_inner_mm: Number(i),
        required_tolerance_mm: Number(t),
        preset: p,
      });
      if (res) {
        setReqOuter(res.required_outer_mm);
        setReqInner(res.required_inner_mm);
        setReqTol(res.required_tolerance_mm);
        setPreset(res.preset);
        setSaveSuccessMsg('Calibrated! Required dimensions active.');
        setTimeout(() => setSaveSuccessMsg(''), 3000);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsSavingTarget(false);
    }
  };

  const applyPreset = (key: string) => {
    const p = PRESETS[key];
    if (p) {
      setReqOuter(p.outer);
      setReqInner(p.inner);
      setReqTol(p.tol);
      setPreset(key);
      handleSaveDimensions(p.outer, p.inner, p.tol, key);
    }
  };

  const loadData = async () => {
    try {
      const [s, r, h, m, autoRes] = await Promise.all([
        fetchStatistics(),
        fetchInspections(0, 7),
        fetchHardwareStatus(),
        fetchMetalProfiles(),
        fetchAutoInspectionStatus().catch(() => ({ auto_mode: false, is_inspecting: false })),
      ]);
      setStats(s);
      setRecent(r);
      setHw(h);
      if (r && r.length > 0) {
        fetchInspection(r[0].id).then(setLatestDetail).catch(() => {});
      }
      if (autoRes) setAutoMode(autoRes.auto_mode);
      fetchTargetDimensions().then((td) => {
        if (td) {
          setReqOuter(td.required_outer_mm);
          setReqInner(td.required_inner_mm);
          setReqTol(td.required_tolerance_mm);
          setPreset(td.preset || 'M5');
        }
      }).catch(() => {});
      if (m) {
        setMetals(m.metals);
        setModes(m.modes);
        setSelectedMetal(m.selected_metal);
        setAnalysisType(m.analysis_type);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAuto = async () => {
    try {
      if (autoMode) {
        await stopAutoInspection();
        setAutoMode(false);
      } else {
        await startAutoInspection(selectedMetal, analysisType);
        setAutoMode(true);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleMetalChange = async (metalKey: string) => {
    setSelectedMetal(metalKey);
    setIsUpdatingMaterial(true);
    try {
      await updateMaterialSelection(metalKey, analysisType);
    } catch (e) {
      console.error(e);
    } finally {
      setIsUpdatingMaterial(false);
    }
  };

  const handleModeChange = async (modeKey: string) => {
    setAnalysisType(modeKey);
    setIsUpdatingMaterial(true);
    try {
      await updateMaterialSelection(selectedMetal, modeKey);
    } catch (e) {
      console.error(e);
    } finally {
      setIsUpdatingMaterial(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 4000);
    return () => clearInterval(interval);
  }, []);

  const pieData = stats
    ? [
        { name: 'PASS', value: stats.pass_count, color: '#10b981' },
        { name: 'FAIL', value: stats.fail_count, color: '#ef4444' },
        { name: 'REVIEW', value: stats.review_count, color: '#f59e0b' },
      ].filter((d) => d.value > 0)
    : [];

  const defectBarData = stats
    ? [
        { name: 'CV Defects', count: stats.defects_by_type.cv_surface_defects },
        { name: 'Laser Height', count: stats.defects_by_type.laser_height_anomalies },
        { name: 'Eddy Current', count: stats.defects_by_type.eddy_anomalies_simulated },
      ]
    : [];

  const activeProfile = metals[selectedMetal];
  const activeMode = modes[analysisType];

  return (
    <div className="space-y-6">
      {/* Top Banner: Status & Quick Launch */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-lg">
        <div className="flex items-center gap-4">
          <div className="relative flex items-center justify-center w-12 h-12 rounded-lg bg-cyan-950/60 border border-cyan-800 text-cyan-400">
            <Activity className="w-6 h-6" />
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"></span>
            </span>
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold tracking-tight text-white">System Status</h1>
              <span
                className={`text-xs px-2.5 py-0.5 rounded-full font-mono uppercase tracking-wider font-semibold ${
                  hw?.simulation_mode
                    ? 'bg-amber-950 text-amber-400 border border-amber-800'
                    : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                }`}
              >
                {hw?.simulation_mode ? 'Hardware Simulation Mode' : 'Connected to Hardware'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Port: <span className="text-slate-200">{hw?.serial_port || 'Auto'}</span> | 3 SG90 Servos | 2 Conveyor Stages | 3 Quality Methods
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 w-full lg:w-auto">
          <button
            onClick={loadData}
            className="p-2.5 rounded-lg border border-industrial-700 bg-industrial-850 hover:bg-industrial-800 text-slate-300 transition-colors"
            title="Refresh Metrics"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <button
            onClick={handleToggleAuto}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-mono text-xs font-bold uppercase tracking-wider transition-all shadow-md ${
              autoMode
                ? 'bg-emerald-600 hover:bg-emerald-500 text-white animate-pulse shadow-emerald-950 border border-emerald-400'
                : 'bg-industrial-850 hover:bg-industrial-800 text-slate-300 border border-industrial-700'
            }`}
            title="When active, Arduino arrival sensor automatically triggers inspection and sorting in a continuous loop"
          >
            <span className={`w-2 h-2 rounded-full ${autoMode ? 'bg-white' : 'bg-slate-500'}`}></span>
            {autoMode ? 'Auto-Pilot: ACTIVE' : 'Start Auto-Pilot'}
          </button>

          <button
            onClick={onStartInspection}
            className="flex-1 lg:flex-none flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-sm transition-all shadow-lg shadow-cyan-950 glow-cyan"
          >
            <Play className="w-4 h-4 fill-current" />
            Single Test Cycle
          </button>
        </div>
      </div>

      {/* Material Selector & Inspection Criteria Panel */}
      <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-lg">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 border-b border-industrial-800 pb-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-industrial-800 border border-industrial-700 text-amber-400">
              <Flame className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                  Active Conveyor Material & Inspection Criteria
                </h2>
                {isUpdatingMaterial && (
                  <span className="text-[10px] font-mono text-cyan-400 flex items-center gap-1 animate-pulse">
                    <RefreshCw className="w-3 h-3 animate-spin" /> Calibrating...
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Select alloy on conveyor to automatically adjust eddy current coil frequency, laser roughness envelope & CV tolerances
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
            {/* Metal Selector */}
            <div className="flex items-center gap-2 bg-industrial-850 border border-industrial-750 px-3 py-1.5 rounded-lg">
              <span className="text-xs font-mono text-slate-400 font-semibold">ALLOY:</span>
              <select
                value={selectedMetal}
                onChange={(e) => handleMetalChange(e.target.value)}
                className="bg-transparent text-white font-mono text-xs font-bold focus:outline-none cursor-pointer"
              >
                {Object.entries(metals).map(([key, m]) => (
                  <option key={key} value={key} className="bg-industrial-900 text-white">
                    {m.name} ({m.category})
                  </option>
                ))}
              </select>
            </div>

            {/* Analysis Mode Selector */}
            <div className="flex items-center gap-2 bg-industrial-850 border border-industrial-750 px-3 py-1.5 rounded-lg">
              <span className="text-xs font-mono text-slate-400 font-semibold">MODE:</span>
              <select
                value={analysisType}
                onChange={(e) => handleModeChange(e.target.value)}
                className="bg-transparent text-cyan-400 font-mono text-xs font-bold focus:outline-none cursor-pointer"
              >
                {Object.entries(modes).map(([key, mode]) => (
                  <option key={key} value={key} className="bg-industrial-900 text-cyan-300">
                    {mode.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Live Criteria Spec Strip */}
        {activeProfile && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 font-mono text-xs">
            <div className="p-2.5 rounded-lg bg-industrial-850/80 border border-industrial-800">
              <span className="text-[10px] text-slate-500 uppercase block">Material Category</span>
              <span className="text-slate-200 font-bold">{activeProfile.category}</span>
            </div>
            <div className="p-2.5 rounded-lg bg-industrial-850/80 border border-industrial-800">
              <span className="text-[10px] text-slate-500 uppercase block">Permeability (μr)</span>
              <span className="text-cyan-400 font-bold">{activeProfile.relative_permeability}</span>
            </div>
            <div className="p-2.5 rounded-lg bg-industrial-850/80 border border-industrial-800">
              <span className="text-[10px] text-slate-500 uppercase block">Conductivity (% IACS)</span>
              <span className="text-cyan-400 font-bold">{activeProfile.conductivity_iacs_pct}%</span>
            </div>
            <div className="p-2.5 rounded-lg bg-industrial-850/80 border border-industrial-800">
              <span className="text-[10px] text-slate-500 uppercase block">Base Impedance (Z₀)</span>
              <span className="text-amber-400 font-bold">{activeProfile.base_impedance_ohms} Ω</span>
            </div>
            <div className="p-2.5 rounded-lg bg-industrial-850/80 border border-industrial-800">
              <span className="text-[10px] text-slate-500 uppercase block">ECI Operating Freq</span>
              <span className="text-indigo-400 font-bold">{activeProfile.operating_freq_khz} kHz</span>
            </div>
            <div className="p-2.5 rounded-lg bg-industrial-850/80 border border-industrial-800">
              <span className="text-[10px] text-slate-500 uppercase block">Laser Tol. Envelope</span>
              <span className="text-emerald-400 font-bold">±{activeProfile.laser_roughness_tol_mm} mm</span>
            </div>
          </div>
        )}
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Total Inspected */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs uppercase font-mono tracking-wider">Total</span>
            <Layers className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold font-mono text-white">{stats?.total ?? 0}</div>
            <div className="text-xs text-slate-400 mt-0.5">Inspected units</div>
          </div>
        </div>

        {/* PASS */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-4 flex flex-col justify-between border-l-4 border-l-emerald-500">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs uppercase font-mono tracking-wider">Pass</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold font-mono text-emerald-400">{stats?.pass_count ?? 0}</div>
            <div className="text-xs text-emerald-500/80 mt-0.5">{stats?.pass_rate_pct ?? 0}% yield</div>
          </div>
        </div>

        {/* FAIL */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-4 flex flex-col justify-between border-l-4 border-l-rose-500">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs uppercase font-mono tracking-wider">Fail</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold font-mono text-rose-400">{stats?.fail_count ?? 0}</div>
            <div className="text-xs text-rose-500/80 mt-0.5">{stats?.fail_rate_pct ?? 0}% rejected</div>
          </div>
        </div>

        {/* REVIEW */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-4 flex flex-col justify-between border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs uppercase font-mono tracking-wider">Review</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold font-mono text-amber-400">{stats?.review_count ?? 0}</div>
            <div className="text-xs text-amber-500/80 mt-0.5">Manual halt</div>
          </div>
        </div>

        {/* Nuts Count */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs uppercase font-mono tracking-wider">Nuts</span>
            <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-industrial-800 text-slate-300">HEX</span>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold font-mono text-white">{stats?.nut_count ?? 0}</div>
            <div className="text-xs text-slate-400 mt-0.5">Sorted to Nut Bin</div>
          </div>
        </div>

        {/* Washers Count */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs uppercase font-mono tracking-wider">Washers</span>
            <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-industrial-800 text-slate-300">RND</span>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold font-mono text-white">{stats?.washer_count ?? 0}</div>
            <div className="text-xs text-slate-400 mt-0.5">Sorted to Washer Bin</div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quality Distribution Pie */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-sm flex flex-col">
          <div className="flex items-center justify-between border-b border-industrial-800 pb-3 mb-4">
            <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Quality Distribution
            </h2>
            <span className="text-xs text-slate-500 font-mono">3 Modules</span>
          </div>
          <div className="h-56 flex items-center justify-center">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px' }}
                    itemStyle={{ color: '#fff', fontFamily: 'monospace' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-xs text-slate-500 font-mono">No inspection data recorded yet</div>
            )}
          </div>
          <div className="flex justify-around text-xs font-mono text-slate-400 pt-2 border-t border-industrial-800">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
              PASS ({stats?.pass_count ?? 0})
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
              FAIL ({stats?.fail_count ?? 0})
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
              REVIEW ({stats?.review_count ?? 0})
            </div>
          </div>
        </div>

        {/* Defect Pareto Breakdown */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-sm flex flex-col">
          <div className="flex items-center justify-between border-b border-industrial-800 pb-3 mb-4">
            <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Defects by Module
            </h2>
            <span className="text-xs text-cyan-400 font-mono">3 SENSING METHODS</span>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={defectBarData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px' }}
                  itemStyle={{ color: '#38bdf8', fontFamily: 'monospace' }}
                />
                <Bar dataKey="count" fill="#0284c7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="text-[11px] text-slate-500 font-mono text-center pt-2 border-t border-industrial-800">
            Identified via Multi-Angle CV, Laser Triangulation & Eddy Current Array
          </p>
        </div>

        {/* Live Hardware Actuator States */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-industrial-800 pb-3 mb-4">
              <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
                Actuator Health
              </h2>
              <span className="text-xs text-slate-500 font-mono">SG90 x3</span>
            </div>
            <div className="space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-industrial-850 border border-industrial-800">
                <span className="text-slate-400">Servo 1 (90° Rotator):</span>
                <span className="text-cyan-400 font-bold">{hw?.actuators?.servo1 ?? 0}°</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-industrial-850 border border-industrial-800">
                <span className="text-slate-400">Servo 2 (Pusher):</span>
                <span className="text-cyan-400 font-bold">{hw?.actuators?.servo2 ?? 0}°</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-industrial-850 border border-industrial-800">
                <span className="text-slate-400">Servo 3 (Diverter Arm):</span>
                <span className="text-cyan-400 font-bold">{hw?.actuators?.servo3 ?? 90}°</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-industrial-850 border border-industrial-800">
                <span className="text-slate-400">Conveyor 1 (Feeding):</span>
                <span className={hw?.actuators?.conveyor1 ? 'text-emerald-400' : 'text-slate-500'}>
                  {hw?.actuators?.conveyor1 ? 'RUNNING' : 'STOPPED'}
                </span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-industrial-850 border border-industrial-800">
                <span className="text-slate-400">Conveyor 2 (Sorting):</span>
                <span className={hw?.actuators?.conveyor2 ? 'text-emerald-400' : 'text-slate-500'}>
                  {hw?.actuators?.conveyor2 ? 'RUNNING' : 'STOPPED'}
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={() => onNavigate('sorting')}
            className="w-full mt-4 py-2 px-3 rounded-lg border border-industrial-700 bg-industrial-850 hover:bg-industrial-800 text-slate-300 text-xs font-mono flex items-center justify-center gap-2 transition-colors"
          >
            Open Sorting Monitor <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Featured Laser Inspection Graph Scope */}
      <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-lg space-y-3 font-mono">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-industrial-800 pb-3">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping"></span>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Method 2: Triangular Laser Surface Profilometry Scope (Real)
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800 font-bold">
              SURFACE HEIGHT (h mm)
            </span>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <span className="text-slate-400">
              Latest Component: <span className="text-cyan-400 font-bold">{latestDetail?.decision?.component_type || recent[0]?.component_type || 'Awaiting Cycle'}</span>
            </span>
            <button
              onClick={() => onNavigate('live')}
              className="text-xs text-rose-400 hover:text-rose-300 font-bold flex items-center gap-1"
            >
              Live Profiler <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Industrial Laser Graph */}
        <div className="h-48 w-full bg-industrial-950 rounded-xl p-2.5 border border-industrial-800 relative">
          {latestDetail?.laser_result?.profile_data && latestDetail.laser_result.profile_data.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={latestDetail.laser_result.profile_data} margin={{ top: 10, right: 15, left: -15, bottom: 0 }}>
                <defs>
                  <linearGradient id="dashLaserGlow" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="2 2" stroke="#1e293b" />
                <XAxis
                  dataKey="x"
                  stroke="#64748b"
                  tick={{ fontSize: 9, fontFamily: 'monospace' }}
                  tickFormatter={(val) => `${val}px`}
                />
                <YAxis
                  stroke="#64748b"
                  tick={{ fontSize: 9, fontFamily: 'monospace' }}
                  unit="mm"
                  domain={[0, (dataMax: number) => Math.max(4.0, Math.ceil(dataMax + 0.5))]}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: '#374151',
                    borderRadius: '6px',
                    fontSize: '11px',
                    fontFamily: 'monospace'
                  }}
                  formatter={(val: any) => [`${val} mm`, 'Surface Height']}
                  labelFormatter={(label) => `Position X: ${label} px`}
                />
                <ReferenceLine y={0} stroke="#475569" strokeDasharray="2 2" />
                {latestDetail.laser_result.peak_height_mm && (
                  <ReferenceLine
                    y={latestDetail.laser_result.peak_height_mm}
                    stroke="#38bdf8"
                    strokeDasharray="3 3"
                    label={{
                      value: `Peak ${latestDetail.laser_result.peak_height_mm}mm`,
                      fill: '#38bdf8',
                      fontSize: 9,
                      position: 'top'
                    }}
                  />
                )}
                <Area
                  type="monotone"
                  dataKey="height"
                  stroke="#ef4444"
                  strokeWidth={2.4}
                  fill="url(#dashLaserGlow)"
                  dot={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-xs font-mono text-slate-500 gap-2">
              <span className="text-xl">📡</span>
              <span>Awaiting component laser triangulation scan... Click "Launch Inspection Sequence" above</span>
            </div>
          )}
        </div>

        {/* Telemetry Bar below Graph */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs pt-1">
          <div className="p-2.5 rounded-lg bg-industrial-850 border border-industrial-800">
            <span className="text-[10px] text-slate-500 uppercase block">Peak Surface Height (h_max)</span>
            <span className="text-white font-bold">{latestDetail?.laser_result ? `${latestDetail.laser_result.peak_height_mm} mm` : '0.00 mm'}</span>
          </div>
          <div className="p-2.5 rounded-lg bg-industrial-850 border border-industrial-800">
            <span className="text-[10px] text-slate-500 uppercase block">Peak-To-Valley Variation (Δh)</span>
            <span className="text-cyan-400 font-bold">{latestDetail?.laser_result ? `${latestDetail.laser_result.max_height_variation_mm} mm` : '0.00 mm'}</span>
          </div>
          <div className="p-2.5 rounded-lg bg-industrial-850 border border-industrial-800">
            <span className="text-[10px] text-slate-500 uppercase block">Surface Roughness (R_z)</span>
            <span className="text-emerald-400 font-bold">{latestDetail?.laser_result ? `${(latestDetail.laser_result as any).roughness_std_mm ?? 0.04} mm` : '0.00 mm'}</span>
          </div>
          <div className="p-2.5 rounded-lg bg-industrial-850 border border-industrial-800">
            <span className="text-[10px] text-slate-500 uppercase block">Laser Envelope Limit</span>
            <span className="text-amber-400 font-bold">±{activeProfile?.laser_roughness_tol_mm ?? 0.65} mm</span>
          </div>
        </div>
      </div>

      {/* Target Dimensions & Pass/Fail Calibration Control Panel */}
      <div className="bg-industrial-900 border border-cyan-800/60 rounded-xl p-5 shadow-sm space-y-4 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-32 bg-cyan-500/5 rounded-full blur-2xl pointer-events-none"></div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-industrial-800 pb-3">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-cyan-950/80 border border-cyan-800 text-cyan-400">
              <Ruler className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-slate-100 uppercase tracking-wider font-mono flex items-center gap-2">
                Required Dimensions & AI Calibration
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800">
                  PASS / FAIL DETERMINATION
                </span>
              </h2>
              <p className="text-xs font-mono text-slate-400">
                AI vision engine calibrates measured dimensions against these target values to dictate quality status.
              </p>
            </div>
          </div>

          {/* Quick Preset Buttons for Demonstration */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[11px] font-mono text-slate-500 mr-1 flex items-center gap-1">
              <Sliders className="w-3.5 h-3.5" /> Presets:
            </span>
            {Object.keys(PRESETS).map((key) => (
              <button
                key={key}
                onClick={() => applyPreset(key)}
                className={`px-2.5 py-1 text-xs font-mono font-bold rounded border transition-all ${
                  preset === key
                    ? 'bg-cyan-500 text-slate-950 border-cyan-400 shadow-sm'
                    : 'bg-industrial-850 hover:bg-industrial-800 text-slate-300 border-industrial-700'
                }`}
                title={PRESETS[key].desc}
              >
                {key}
              </button>
            ))}
          </div>
        </div>

        {/* Inputs Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs font-mono">
          {/* Required Outer Diameter / Flats */}
          <div className="p-3 rounded-lg bg-industrial-850 border border-industrial-800 space-y-1.5">
            <label className="text-[11px] text-amber-400 uppercase font-bold block flex items-center justify-between">
              <span>Required Outer Dia / Flats</span>
              <span className="text-[10px] text-slate-500 font-normal">OD / s (mm)</span>
            </label>
            <div className="flex items-center gap-1.5 bg-industrial-900 border border-industrial-700 rounded px-2.5 py-1.5">
              <input
                type="number"
                step="0.1"
                min="1.0"
                max="60.0"
                value={reqOuter}
                onChange={(e) => {
                  setReqOuter(parseFloat(e.target.value) || 0);
                  setPreset('CUSTOM');
                }}
                className="bg-transparent text-white font-bold text-sm w-full outline-none"
              />
              <span className="text-slate-500 text-xs font-mono">mm</span>
            </div>
            <span className="text-[10px] text-slate-500 block">Washer OD or Hex Nut Flats width</span>
          </div>

          {/* Required Inner Hole Diameter */}
          <div className="p-3 rounded-lg bg-industrial-850 border border-industrial-800 space-y-1.5">
            <label className="text-[11px] text-cyan-400 uppercase font-bold block flex items-center justify-between">
              <span>Required Inner Hole Dia</span>
              <span className="text-[10px] text-slate-500 font-normal">ID (mm)</span>
            </label>
            <div className="flex items-center gap-1.5 bg-industrial-900 border border-industrial-700 rounded px-2.5 py-1.5">
              <input
                type="number"
                step="0.1"
                min="0.5"
                max="40.0"
                value={reqInner}
                onChange={(e) => {
                  setReqInner(parseFloat(e.target.value) || 0);
                  setPreset('CUSTOM');
                }}
                className="bg-transparent text-white font-bold text-sm w-full outline-none"
              />
              <span className="text-slate-500 text-xs font-mono">mm</span>
            </div>
            <span className="text-[10px] text-slate-500 block">Center bore or internal thread diameter</span>
          </div>

          {/* Allowed Tolerance (±mm) */}
          <div className="p-3 rounded-lg bg-industrial-850 border border-industrial-800 space-y-1.5">
            <label className="text-[11px] text-slate-300 uppercase font-bold block flex items-center justify-between">
              <span>Tolerance Envelope</span>
              <span className="text-[10px] text-slate-500 font-normal">± Limit</span>
            </label>
            <div className="flex items-center gap-1.5 bg-industrial-900 border border-industrial-700 rounded px-2.5 py-1.5">
              <span className="text-slate-400 font-mono">±</span>
              <input
                type="number"
                step="0.05"
                min="0.05"
                max="5.0"
                value={reqTol}
                onChange={(e) => {
                  setReqTol(parseFloat(e.target.value) || 0);
                  setPreset('CUSTOM');
                }}
                className="bg-transparent text-white font-bold text-sm w-full outline-none"
              />
              <span className="text-slate-500 text-xs font-mono">mm</span>
            </div>
            <span className="text-[10px] text-slate-500 block">Exceeding this variance flags FAIL</span>
          </div>

          {/* Save / Calibrate Button */}
          <div className="p-3 rounded-lg bg-industrial-850 border border-industrial-800 flex flex-col justify-between space-y-2">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-slate-400">ACTIVE CRITERIA:</span>
              <span className="px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 font-bold border border-cyan-800 text-[10px]">
                {preset}
              </span>
            </div>
            <button
              onClick={() => handleSaveDimensions()}
              disabled={isSavingTarget}
              className="w-full py-2 px-3 rounded bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 text-slate-950 font-bold font-mono text-xs transition-colors shadow flex items-center justify-center gap-1.5"
            >
              <ShieldCheck className="w-4 h-4" />
              {isSavingTarget ? 'Calibrating...' : 'Apply & Calibrate Model'}
            </button>
            {saveSuccessMsg && (
              <span className="text-[10px] text-emerald-400 font-mono text-center block animate-fade-in">
                ✓ {saveSuccessMsg}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Recent Inspection Activity Feed */}
      <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between border-b border-industrial-800 pb-3 mb-4">
          <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
            Recent Inspection Activity
          </h2>
          <button
            onClick={() => onNavigate('history')}
            className="text-xs text-cyan-400 hover:text-cyan-300 font-mono flex items-center gap-1"
          >
            View Full History <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {recent.length === 0 ? (
          <div className="py-8 text-center text-slate-500 font-mono text-xs">
            No inspections executed yet. Click "Launch Inspection Sequence" above to start.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-industrial-800 text-slate-400">
                  <th className="py-2.5 px-3">Inspection ID</th>
                  <th className="py-2.5 px-3">Time</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Outcome</th>
                  <th className="py-2.5 px-3 min-w-[210px]">Target vs Measured (OD / ID)</th>
                  <th className="py-2.5 px-3">CV Status</th>
                  <th className="py-2.5 px-3">Laser</th>
                  <th className="py-2.5 px-3">Eddy</th>
                  <th className="py-2.5 px-3">Action</th>
                  <th className="py-2.5 px-3 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-industrial-800/60">
                {recent.map((item) => (
                  <tr key={item.id} className="hover:bg-industrial-850/50 transition-colors">
                    <td className="py-3 px-3 text-cyan-400 font-bold">
                      {item.id.slice(0, 8)}...
                    </td>
                    <td className="py-3 px-3 text-slate-400">
                      {item.created_at ? new Date(item.created_at).toLocaleTimeString() : '-'}
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded bg-industrial-800 text-slate-200 border border-industrial-700">
                        {item.component_type}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`px-2.5 py-0.5 rounded-full font-bold ${
                          item.outcome === 'PASS'
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : item.outcome === 'FAIL'
                            ? 'bg-rose-950 text-rose-400 border border-rose-800'
                            : 'bg-amber-950 text-amber-400 border border-amber-800'
                        }`}
                      >
                        {item.outcome}
                      </span>
                    </td>
                    {/* DEMONSTRATION COLUMN: Target vs Measured Dimensions */}
                    <td className="py-3 px-3">
                      {item.dimensions?.measured_outer_mm || item.dimensions?.outer_diameter_mm ? (
                        <div className="flex flex-col gap-0.5">
                          <div className="text-[10px] text-slate-400">
                            <span className="text-amber-400 font-bold">REQ: </span>
                            {item.dimensions?.required_outer_mm ?? reqOuter} / {item.dimensions?.required_inner_mm ?? reqInner} mm
                            <span className="text-slate-500 text-[9px] ml-1">(±{item.dimensions?.required_tolerance_mm ?? reqTol}mm)</span>
                          </div>
                          <div className="text-[11px] font-bold text-white flex items-center gap-1.5">
                            <span className="text-cyan-400 font-normal">MEAS:</span>
                            <span>{item.dimensions?.measured_outer_mm ?? item.dimensions?.outer_diameter_mm ?? item.dimensions?.across_flats_mm ?? '-'} / {item.dimensions?.measured_inner_mm ?? item.dimensions?.inner_diameter_mm ?? '-'} mm</span>
                          </div>
                          {(item.dimensions?.deviation_outer_mm !== undefined || item.dimensions?.deviation_inner_mm !== undefined) && (
                            <div className="text-[10px] text-slate-400 flex items-center gap-1.5">
                              <span>ΔOD: <strong className={item.dimensions?.outer_status === 'FAIL' ? 'text-rose-400' : 'text-emerald-400'}>
                                {item.dimensions?.deviation_outer_mm > 0 ? `+${item.dimensions?.deviation_outer_mm}` : (item.dimensions?.deviation_outer_mm ?? 0)}mm
                              </strong></span>
                              <span>•</span>
                              <span>ΔID: <strong className={item.dimensions?.inner_status === 'FAIL' ? 'text-rose-400' : 'text-emerald-400'}>
                                {item.dimensions?.deviation_inner_mm > 0 ? `+${item.dimensions?.deviation_inner_mm}` : (item.dimensions?.deviation_inner_mm ?? 0)}mm
                              </strong></span>
                            </div>
                          )}
                        </div>
                      ) : (
                        <span className="text-slate-500 text-[11px] italic">No dimension data</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-slate-300">{item.cv_status}</td>
                    <td className="py-3 px-3 text-slate-300">{item.laser_status}</td>
                    <td className="py-3 px-3 text-slate-300">{item.eddy_status}</td>
                    <td className="py-3 px-3 text-slate-400 text-[11px]">{item.sorting_command}</td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => onNavigate('detail', item.id)}
                        className="text-cyan-400 hover:text-cyan-300 underline font-medium"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

