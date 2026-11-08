import React, { useState, useEffect } from 'react';
import {
  startInspection,
  openInspectionWS,
  BACKEND_URL,
  InspectionDetail,
  fetchInspection,
  fetchMetalProfiles,
  updateMaterialSelection,
  startAutoInspection,
  stopAutoInspection,
  fetchAutoInspectionStatus,
  MetalProfile,
  AnalysisMode,
} from '../services/api';
import {
  Play,
  RotateCw,
  Zap,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Camera,
  Maximize2,
  Radio,
  Sliders,
  RefreshCw,
  Box,
  Eye,
  Flame,
  Compass,
  Layers,
  Cpu,
  Check,
  Scan,
} from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  ReferenceLine,
} from 'recharts';

export const LiveInspectionPage: React.FC = () => {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<{ step: number; title: string; detail: string } | null>(null);
  const [stepHistory, setStepHistory] = useState<any[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [forceType, setForceType] = useState<string>('nut');
  const [forceDefect, setForceDefect] = useState<boolean>(false);

  // Live telemetry data
  const [cvView0, setCvView0] = useState<any>(null);
  const [cvResult, setCvResult] = useState<any>(null);
  const [laserResult, setLaserResult] = useState<any>(null);
  const [eddyResult, setEddyResult] = useState<any>(null);
  const [finalDecision, setFinalDecision] = useState<any>(null);
  const [rotationActive, setRotationActive] = useState<boolean>(false);

  // 4-Quadrant Multi-Angle CV Views (0°, 90°, 180°, 270°)
  const [quadrantViews, setQuadrantViews] = useState<Record<string, any>>({});
  const [activeQuadrantAngle, setActiveQuadrantAngle] = useState<number | null>(null);

  // Completed inspection details from API
  const [completedDetail, setCompletedDetail] = useState<InspectionDetail | null>(null);

  // Material and Analysis mode
  const [metals, setMetals] = useState<Record<string, MetalProfile>>({});
  const [modes, setModes] = useState<Record<string, AnalysisMode>>({});
  const [selectedMetal, setSelectedMetal] = useState<string>('carbon_steel');
  const [analysisType, setAnalysisType] = useState<string>('standard');
  const [autoMode, setAutoMode] = useState<boolean>(false);

  useEffect(() => {
    fetchMetalProfiles().then((res) => {
      if (res) {
        setMetals(res.metals);
        setModes(res.modes);
        setSelectedMetal(res.selected_metal);
        setAnalysisType(res.analysis_type);
      }
    }).catch(console.error);

    fetchAutoInspectionStatus().then((res) => {
      if (res) setAutoMode(res.auto_mode);
    }).catch(console.error);
  }, []);

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

  const handleLaunch = async () => {
    setIsRunning(true);
    setCvView0(null);
    setCvResult(null);
    setLaserResult(null);
    setEddyResult(null);
    setFinalDecision(null);
    setCompletedDetail(null);
    setStepHistory([]);
    setRotationActive(false);
    setQuadrantViews({});
    setActiveQuadrantAngle(null);

    try {
      const { inspection_id } = await startInspection(
        forceType,
        forceDefect,
        selectedMetal,
        analysisType
      );
      setActiveId(inspection_id);

      const ws = openInspectionWS(
        inspection_id,
        (msg) => {
          if (msg.type === 'step') {
            setCurrentStep(msg.data);
            setStepHistory((prev) => [...prev, msg.data]);
            const stepTitle = msg.data.title || '';
            if (msg.data.step === 5 || stepTitle.toLowerCase().includes('rotate')) {
              setRotationActive(true);
            } else {
              setRotationActive(false);
            }

            if (stepTitle.includes('0°')) setActiveQuadrantAngle(0);
            else if (stepTitle.includes('90°')) setActiveQuadrantAngle(90);
            else if (stepTitle.includes('180°')) setActiveQuadrantAngle(180);
            else if (stepTitle.includes('270°')) setActiveQuadrantAngle(270);
          } else if (msg.type === 'cv_view_0') {
            setCvView0(msg.data);
            setQuadrantViews((prev) => ({ ...prev, '0deg': msg.data }));
          } else if (msg.type === 'cv_view_90') {
            setQuadrantViews((prev) => ({ ...prev, '90deg': msg.data }));
          } else if (msg.type === 'cv_view_180') {
            setQuadrantViews((prev) => ({ ...prev, '180deg': msg.data }));
          } else if (msg.type === 'cv_view_270') {
            setQuadrantViews((prev) => ({ ...prev, '270deg': msg.data }));
          } else if (msg.type === 'cv_complete') {
            setCvResult(msg.data);
            if (msg.data.views) {
              setQuadrantViews((prev) => ({ ...prev, ...msg.data.views }));
            }
            setActiveQuadrantAngle(null);
          } else if (msg.type === 'laser_complete') {
            setLaserResult(msg.data);
          } else if (msg.type === 'eddy_complete') {
            setEddyResult(msg.data);
          } else if (msg.type === 'decision_complete') {
            setFinalDecision(msg.data);
          } else if (msg.type === 'complete') {
            setIsRunning(false);
            setRotationActive(false);
            setActiveQuadrantAngle(null);
            // Fetch final saved record with image paths
            fetchInspection(inspection_id)
              .then((d) => setCompletedDetail(d))
              .catch(console.error);
          } else if (msg.type === 'error') {
            setIsRunning(false);
            setRotationActive(false);
            setActiveQuadrantAngle(null);
          }
        },
        () => {
          setIsRunning(false);
          setActiveQuadrantAngle(null);
        }
      );
    } catch (e) {
      console.error(e);
      setIsRunning(false);
      setActiveQuadrantAngle(null);
    }
  };

  const getQuadrantImage = (angleLabel: string): string | null => {
    // 1. Direct from completed inspection images list
    const fromCompleted = completedDetail?.images?.find((img) => img.label === angleLabel);
    if (fromCompleted?.url) return `${BACKEND_URL}${fromCompleted.url}`;

    // 2. From real-time quadrant payload
    const qData = quadrantViews[angleLabel];
    if (qData?.image_url) return `${BACKEND_URL}${qData.image_url}`;

    // 3. Fallback to active inspection media path if actively inspecting
    if (activeId && qData) {
      return `${BACKEND_URL}/media/${activeId}/view_${angleLabel}.jpg`;
    }

    return null;
  };

  const eddyChartData = eddyResult?.readings?.map((r: any) => ({
    name: `C${r.coil_index} (${r.angle_deg}°)`,
    impedance: r.impedance,
    deviation: r.deviation_pct,
    nominal: r.nominal,
    is_anomaly: r.is_anomaly,
  })) || [];

  const quadrantDefinitions = [
    {
      angle: 0,
      label: '0deg',
      name: '0° Initial Landing',
      subtitle: 'Slope-Guided Baseline',
      desc: 'Initial resting orientation post slope landing. Baseline major & minor axes under 45° perspective.',
    },
    {
      angle: 90,
      label: '90deg',
      name: '90° Transverse Rotation',
      subtitle: 'SG90 Orthogonal Flip',
      desc: 'Rotates longitudinal axis onto uncompressed transverse sensor plane. Eliminates perspective foreshortening.',
    },
    {
      angle: 180,
      label: '180deg',
      name: '180° Inverted Facets',
      subtitle: 'Reverse Directional Scan',
      desc: 'Exposes rear hex flats / circular perimeter. Illuminates reverse edge shadows & burr defects.',
    },
    {
      angle: 270,
      label: '270deg',
      name: '270° Lateral Perimeter',
      subtitle: 'Full 360° Inspection Closure',
      desc: 'Final quadrant sweep. Completes continuous 360° perimeter integration with sub-pixel verification.',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Controller Bar */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-industrial-900 border border-industrial-800 rounded-xl p-4 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-cyan-950/60 border border-cyan-800 text-cyan-400">
            <Radio className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white flex items-center gap-2">
              Live Quality Inspection Station
              {isRunning && (
                <span className="text-xs font-mono font-normal px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 animate-pulse">
                  ACTIVE CYCLE
                </span>
              )}
            </h1>
            <p className="text-xs text-slate-400 font-mono">
              3 Independent Quality Modules | 360° Rotational CV (0°•90°•180°•270°) | Real-time Decision Engine
            </p>
          </div>
        </div>

        {/* Test Controls */}
        <div className="flex items-center flex-wrap gap-3">
          {/* Metal Selector */}
          <div className="flex items-center gap-2 bg-industrial-850 px-3 py-1.5 rounded-lg border border-industrial-800 text-xs font-mono">
            <span className="text-slate-400">Metal:</span>
            <select
              value={selectedMetal}
              onChange={(e) => {
                setSelectedMetal(e.target.value);
                updateMaterialSelection(e.target.value, analysisType).catch(console.error);
              }}
              disabled={isRunning}
              className="bg-industrial-900 text-amber-400 font-bold border border-industrial-700 rounded px-2 py-1 outline-none"
            >
              {Object.entries(metals).map(([key, m]) => (
                <option key={key} value={key} className="bg-industrial-900 text-white">
                  {m.name}
                </option>
              ))}
            </select>
          </div>

          {/* Analysis Mode Selector */}
          <div className="flex items-center gap-2 bg-industrial-850 px-3 py-1.5 rounded-lg border border-industrial-800 text-xs font-mono">
            <span className="text-slate-400">Criteria:</span>
            <select
              value={analysisType}
              onChange={(e) => {
                setAnalysisType(e.target.value);
                updateMaterialSelection(selectedMetal, e.target.value).catch(console.error);
              }}
              disabled={isRunning}
              className="bg-industrial-900 text-cyan-400 font-bold border border-industrial-700 rounded px-2 py-1 outline-none"
            >
              {Object.entries(modes).map(([key, mode]) => (
                <option key={key} value={key} className="bg-industrial-900 text-cyan-300">
                  {mode.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2 bg-industrial-850 px-3 py-1.5 rounded-lg border border-industrial-800 text-xs font-mono">
            <span className="text-slate-400">Target Type:</span>
            <select
              value={forceType}
              onChange={(e) => setForceType(e.target.value)}
              disabled={isRunning}
              className="bg-industrial-900 text-slate-200 border border-industrial-700 rounded px-2 py-1 outline-none"
            >
              <option value="nut">Nut (Hex)</option>
              <option value="washer">Washer (Round)</option>
            </select>
          </div>

          <label className="flex items-center gap-2 bg-industrial-850 px-3 py-2 rounded-lg border border-industrial-800 text-xs font-mono cursor-pointer">
            <input
              type="checkbox"
              checked={forceDefect}
              onChange={(e) => setForceDefect(e.target.checked)}
              disabled={isRunning}
              className="rounded bg-industrial-900 border-industrial-700 text-rose-500 focus:ring-0"
            />
            <span className={forceDefect ? 'text-rose-400 font-bold' : 'text-slate-400'}>
              Inject Defect Sample
            </span>
          </label>

          <button
            onClick={handleToggleAuto}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-xs font-bold uppercase tracking-wider transition-all shadow-md ${
              autoMode
                ? 'bg-emerald-600 hover:bg-emerald-500 text-white animate-pulse shadow-emerald-950 border border-emerald-400'
                : 'bg-industrial-850 hover:bg-industrial-800 text-slate-300 border border-industrial-700'
            }`}
            title="Continuous sensor-driven loop: optical sensors automatically trigger capture, rotation, ECI, and sorting"
          >
            <span className={`w-2 h-2 rounded-full ${autoMode ? 'bg-white' : 'bg-slate-500'}`}></span>
            {autoMode ? 'Auto-Pilot: ON' : 'Auto-Pilot Loop'}
          </button>

          <button
            onClick={handleLaunch}
            disabled={isRunning || autoMode}
            className={`flex items-center gap-2 px-5 py-2 rounded-lg font-mono text-xs font-bold uppercase tracking-wider transition-all shadow-md ${
              (isRunning || autoMode)
                ? 'bg-industrial-800 text-slate-500 cursor-not-allowed border border-industrial-700'
                : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-cyan-950 glow-cyan'
            }`}
          >
            <Play className="w-4 h-4 fill-current" />
            {isRunning ? 'Inspecting...' : 'Single Cycle'}
          </button>
        </div>
      </div>

      {/* 18-Step Sequence Progress Ribbon */}
      <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-4 shadow-sm">
        <div className="flex items-center justify-between text-xs font-mono mb-2">
          <span className="text-slate-400 uppercase tracking-wider">
            Workflow Progress: {currentStep ? `Step ${currentStep.step} / 18` : 'Idle / Ready'}
          </span>
          <span className="text-cyan-400 font-bold">{currentStep?.title || 'Waiting to start'}</span>
        </div>
        <div className="w-full bg-industrial-800 h-2.5 rounded-full overflow-hidden">
          <div
            className="bg-gradient-to-r from-cyan-500 to-emerald-500 h-full transition-all duration-300 rounded-full"
            style={{ width: `${currentStep ? (currentStep.step / 18) * 100 : 0}%` }}
          ></div>
        </div>
        {currentStep && (
          <p className="text-[11px] font-mono text-slate-400 mt-2 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping"></span>
            {currentStep.detail}
          </p>
        )}
      </div>

      {/* ROW 1: PRIMARY LIVE CAMERA STREAM & CENTRAL DECISION ENGINE (12 Cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Smartphone Inspection Camera Live Video Stream (6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-industrial-900 border border-industrial-800 rounded-xl overflow-hidden shadow-sm">
            <div className="flex items-center justify-between px-4 py-3 border-b border-industrial-800 bg-industrial-850">
              <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
                <Camera className="w-4 h-4 text-cyan-400" />
                <span className="font-semibold">Live Smartphone Camera Stream (45° Perspective)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800 animate-pulse">
                  IP WEB STREAM
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-industrial-800 text-slate-300 border border-industrial-700">
                  45° TILT
                </span>
              </div>
            </div>
            <div className="relative aspect-video bg-black flex items-center justify-center overflow-hidden">
              <img
                src={`${BACKEND_URL}/api/stream/video_feed`}
                alt="Live Camera Feed"
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as any).style.display = 'none';
                }}
              />

              {/* Perspective Grid & Center Crosshairs HUD */}
              <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                <div className="w-24 h-24 border border-cyan-500/30 rounded-full flex items-center justify-center">
                  <div className="w-1 h-1 bg-cyan-400 rounded-full"></div>
                </div>
                <div className="absolute top-2 left-2 text-[10px] font-mono bg-black/60 px-2 py-0.5 rounded text-slate-400 border border-industrial-800">
                  Slope Landing Target: (X:320, Y:240)
                </div>
              </div>

              {/* Active Servo Rotation Overlay */}
              {rotationActive && (
                <div className="absolute inset-0 bg-black/60 backdrop-blur-xs flex flex-col items-center justify-center text-cyan-400 z-10">
                  <RotateCw className="w-12 h-12 animate-spin mb-2 text-cyan-400" />
                  <span className="font-mono text-sm font-bold tracking-widest uppercase text-white">
                    SG90 Servo 1: Rotating 90°
                  </span>
                  <span className="font-mono text-xs text-cyan-300 mt-1">
                    Aligning Component to Quadrant Angle...
                  </span>
                </div>
              )}
            </div>
            <div className="p-3 bg-industrial-950/60 border-t border-industrial-800 flex items-center justify-between text-[11px] font-mono text-slate-400">
              <div className="flex items-center gap-1.5">
                <Compass className="w-3.5 h-3.5 text-cyan-400" />
                <span>Perspective Angle: <strong className="text-slate-200">45° Foreshortened</strong></span>
              </div>
              <div>
                <span>Platform Rotation: <strong className="text-amber-400">4 × 90° Multi-Angle Steps</strong></span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Central Decision Engine & High-Level Summary (6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          <div
            className={`border rounded-xl p-5 shadow-lg transition-all h-full flex flex-col justify-between ${
              finalDecision?.quality_status === 'PASS'
                ? 'bg-emerald-950/40 border-emerald-700 glow-emerald'
                : finalDecision?.quality_status === 'FAIL'
                ? 'bg-rose-950/40 border-rose-700 glow-rose'
                : finalDecision?.quality_status === 'REVIEW'
                ? 'bg-amber-950/40 border-amber-700 glow-amber'
                : 'bg-industrial-900 border-industrial-800'
            }`}
          >
            <div>
              <div className="flex items-center justify-between border-b border-industrial-700/60 pb-3 mb-3">
                <span className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Cpu className="w-4 h-4 text-cyan-400" />
                  Central Multi-Modal Quality Decision
                </span>
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-industrial-850 text-slate-200 border border-industrial-700">
                  Target: {forceType.toUpperCase()}
                </span>
              </div>

              <div className="flex items-center gap-4 my-2">
                <div className="text-4xl">
                  {finalDecision?.quality_status === 'PASS' && <CheckCircle2 className="w-12 h-12 text-emerald-400" />}
                  {finalDecision?.quality_status === 'FAIL' && <XCircle className="w-12 h-12 text-rose-400" />}
                  {finalDecision?.quality_status === 'REVIEW' && <AlertTriangle className="w-12 h-12 text-amber-400" />}
                  {!finalDecision && <RefreshCw className="w-10 h-10 text-slate-600 animate-spin" />}
                </div>
                <div>
                  <div
                    className={`text-3xl font-extrabold font-mono tracking-wider ${
                      finalDecision?.quality_status === 'PASS'
                        ? 'text-emerald-400'
                        : finalDecision?.quality_status === 'FAIL'
                        ? 'text-rose-400'
                        : finalDecision?.quality_status === 'REVIEW'
                        ? 'text-amber-400'
                        : 'text-slate-400'
                    }`}
                  >
                    {finalDecision?.quality_status || (isRunning ? 'EVALUATING SENSORS...' : 'IDLE / READY')}
                  </div>
                  <div className="text-xs font-mono text-slate-300 mt-1">
                    Sorting SG90 Servo 2 Action: <span className="font-bold text-white uppercase">{finalDecision?.sorting_command || (isRunning ? 'PENDING' : 'HOLD')}</span>
                  </div>
                </div>
              </div>

              {finalDecision?.final_reason && (
                <div className="mt-3 p-3 rounded-lg bg-black/50 border border-industrial-800 text-xs font-mono text-slate-300 leading-relaxed">
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold mb-1">Decision Verdict Detail</div>
                  {finalDecision.final_reason}
                </div>
              )}
            </div>

            {/* Quick Multi-Module Status Matrix */}
            <div className="grid grid-cols-3 gap-2 pt-3 mt-3 border-t border-industrial-800/80 text-xs font-mono">
              <div className="bg-industrial-850/80 p-2.5 rounded-lg border border-industrial-800">
                <div className="text-[10px] text-slate-500 uppercase">Method 1 (CV 360°)</div>
                <div className={`font-bold mt-0.5 ${cvResult?.status === 'PASS' ? 'text-emerald-400' : cvResult?.status === 'FAIL' ? 'text-rose-400' : 'text-slate-400'}`}>
                  {cvResult?.status || 'AWAITING'}
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5 truncate">
                  {cvResult?.dimensions?.metric_size ? `${cvResult.dimensions.metric_size} ${cvResult.component_type?.toUpperCase()}` : '0°-360° Scan'}
                </div>
              </div>
              <div className="bg-industrial-850/80 p-2.5 rounded-lg border border-industrial-800">
                <div className="text-[10px] text-slate-500 uppercase">Method 2 (Laser)</div>
                <div className={`font-bold mt-0.5 ${laserResult?.status === 'PASS' ? 'text-emerald-400' : laserResult?.status === 'FAIL' ? 'text-rose-400' : 'text-slate-400'}`}>
                  {laserResult?.status || 'AWAITING'}
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  {laserResult ? `Δh ${laserResult.max_height_variation_mm}mm` : 'Triangulation'}
                </div>
              </div>
              <div className="bg-industrial-850/80 p-2.5 rounded-lg border border-industrial-800">
                <div className="text-[10px] text-slate-500 uppercase">Method 3 (ECI)</div>
                <div className={`font-bold mt-0.5 ${eddyResult?.status === 'PASS' ? 'text-emerald-400' : eddyResult?.status === 'FAIL' ? 'text-rose-400' : 'text-slate-400'}`}>
                  {eddyResult?.status || 'AWAITING'}
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  {eddyResult ? `ΔZ ${eddyResult.max_deviation_pct}%` : 'Coil Array'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ROW 2: CENTERPIECE DEDICATED 360° ROTATIONAL CV INSPECTION — ALL 4 QUADRANT IMAGES & INDIVIDUAL CV ANALYSIS */}
      <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-lg space-y-4">
        {/* Section Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-industrial-800 pb-4 gap-2">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyan-950/80 border border-cyan-800 text-cyan-400">
              <Scan className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold font-mono text-white flex items-center gap-2">
                360° Rotational Live Inspection: 4-Quadrant Multi-Angle Analysis
                <span className="text-xs font-normal px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800">
                  0° • 90° • 180° • 270°
                </span>
              </h2>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Servo rotates every 90°. Each frame captured & analyzed independently using OpenCV + trained Random Forest sizing models.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap text-xs font-mono">
            <span className="px-2.5 py-1 rounded bg-industrial-850 text-slate-300 border border-industrial-800">
              Metric Size: <strong className="text-amber-400">{cvResult?.dimensions?.metric_size || 'Calibrating'}</strong>
            </span>
            <span className={`px-2.5 py-1 rounded border ${cvResult?.multi_angle_consistent ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800' : 'bg-industrial-850 text-slate-400 border-industrial-800'}`}>
              Consistency: <strong className="text-white">{cvResult?.multi_angle_consistent ? '✓ 4/4 Quadrants Matched' : 'Awaiting 4 Views'}</strong>
            </span>
          </div>
        </div>

        {/* 4 Quadrants Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quadrantDefinitions.map((quad) => {
            const viewData = quadrantViews[quad.label] || cvResult?.views?.[quad.label];
            const imgSrc = getQuadrantImage(quad.label);
            const isCapturingNow = isRunning && activeQuadrantAngle === quad.angle;
            const hasData = !!viewData;

            return (
              <div
                key={quad.label}
                className={`flex flex-col justify-between bg-industrial-950/80 rounded-xl border transition-all duration-300 overflow-hidden ${
                  isCapturingNow
                    ? 'border-cyan-400 ring-2 ring-cyan-500/20 shadow-lg shadow-cyan-950/50'
                    : hasData
                    ? viewData?.status === 'PASS'
                      ? 'border-emerald-800/80 hover:border-emerald-600'
                      : 'border-rose-800/80 hover:border-rose-600'
                    : 'border-industrial-800'
                }`}
              >
                {/* Quadrant Card Header */}
                <div className="p-3 bg-industrial-900/90 border-b border-industrial-800 flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold font-mono text-cyan-400">
                        {quad.angle}°
                      </span>
                      <span className="text-xs font-semibold font-mono text-white">
                        {quad.name.replace(`${quad.angle}° `, '')}
                      </span>
                    </div>
                    <div className="text-[10px] font-mono text-slate-400">
                      {quad.subtitle}
                    </div>
                  </div>

                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase tracking-wider ${
                      isCapturingNow
                        ? 'bg-cyan-950 text-cyan-300 border border-cyan-700 animate-pulse'
                        : viewData?.status === 'PASS'
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        : viewData?.status === 'FAIL'
                        ? 'bg-rose-950 text-rose-400 border border-rose-800'
                        : 'bg-industrial-800 text-slate-400 border border-industrial-700'
                    }`}
                  >
                    {isCapturingNow ? 'CAPTURING' : viewData?.status || 'AWAITING'}
                  </span>
                </div>

                {/* Quadrant Image Display */}
                <div className="relative aspect-4/3 bg-black flex items-center justify-center overflow-hidden border-b border-industrial-800">
                  {imgSrc ? (
                    <img
                      src={imgSrc}
                      alt={`${quad.name} Capture`}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="flex flex-col items-center justify-center p-4 text-center">
                      <Box className={`w-8 h-8 mb-2 ${isCapturingNow ? 'text-cyan-400 animate-bounce' : 'text-slate-600'}`} />
                      <span className="text-xs font-mono text-slate-400">
                        {isCapturingNow ? `Capturing ${quad.angle}° Frame...` : `Platform Position: ${quad.angle}°`}
                      </span>
                      <span className="text-[10px] font-mono text-slate-600 mt-1">
                        {isCapturingNow ? 'Running OpenCV Analysis' : 'Awaiting servo rotation'}
                      </span>
                    </div>
                  )}

                  {/* Image Overlays */}
                  <div className="absolute top-2 left-2 flex items-center gap-1">
                    <span className="text-[9px] font-mono bg-black/70 text-slate-300 px-1.5 py-0.5 rounded border border-industrial-700">
                      View: {quad.label}
                    </span>
                    <span className="text-[9px] font-mono bg-black/70 text-cyan-300 px-1.5 py-0.5 rounded border border-industrial-700">
                      45° Tilt De-projected
                    </span>
                  </div>

                  {isCapturingNow && (
                    <div className="absolute inset-0 bg-cyan-950/30 border-2 border-cyan-400 pointer-events-none flex items-center justify-center">
                      <span className="text-xs font-mono font-bold bg-black/80 px-2.5 py-1 rounded text-cyan-300 border border-cyan-500 animate-pulse">
                        ANALYSIZER ACTIVE
                      </span>
                    </div>
                  )}
                </div>

                {/* Computer Vision Metrics Breakdown */}
                <div className="p-3 space-y-2.5 text-xs font-mono flex-1 flex flex-col justify-between">
                  {viewData ? (
                    <>
                      {/* Metric & Classification */}
                      <div className="flex items-center justify-between pb-2 border-b border-industrial-800/80">
                        <div>
                          <span className="text-[10px] text-slate-500 block uppercase">CLASSIFICATION</span>
                          <span className="font-bold text-white uppercase flex items-center gap-1.5">
                            {viewData.component_type || '-'}
                            {viewData.metric_size && (
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-950 text-amber-400 border border-amber-800">
                                {viewData.metric_size}
                              </span>
                            )}
                          </span>
                        </div>
                        <div className="text-right">
                          <span className="text-[10px] text-slate-500 block uppercase">CONFIDENCE</span>
                          <span className="font-bold text-cyan-400">
                            {viewData.confidence ? `${Math.round(viewData.confidence * 100)}%` : '-'}
                          </span>
                        </div>
                      </div>

                      {/* Dimension Metrics */}
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div className="bg-industrial-900/90 p-2 rounded border border-industrial-800">
                          <span className="text-slate-500 text-[10px] block">
                            {viewData.component_type === 'nut' ? 'FLATS (s)' : 'OUTER (OD)'}
                          </span>
                          <span className="font-bold text-cyan-300">
                            {viewData.dimensions?.across_flats_mm || viewData.dimensions?.outer_diameter_mm
                              ? `${viewData.dimensions.across_flats_mm || viewData.dimensions.outer_diameter_mm} mm`
                              : '-'}
                          </span>
                        </div>
                        <div className="bg-industrial-900/90 p-2 rounded border border-industrial-800">
                          <span className="text-slate-500 text-[10px] block">INNER HOLE (ID)</span>
                          <span className="font-bold text-cyan-300">
                            {viewData.dimensions?.inner_diameter_mm ? `${viewData.dimensions.inner_diameter_mm} mm` : '-'}
                          </span>
                        </div>
                        <div className="bg-industrial-900/90 p-2 rounded border border-industrial-800">
                          <span className="text-slate-500 text-[10px] block">CIRCULARITY</span>
                          <span className="font-bold text-slate-200">
                            {viewData.circularity ? Number(viewData.circularity).toFixed(3) : '-'}
                          </span>
                        </div>
                        <div className="bg-industrial-900/90 p-2 rounded border border-industrial-800">
                          <span className="text-slate-500 text-[10px] block">CORNERS / VERTICES</span>
                          <span className="font-bold text-slate-200">
                            {viewData.corners !== undefined ? `${viewData.corners} pts` : '-'}
                          </span>
                        </div>
                      </div>

                      {/* Defects Detected At This Angle */}
                      <div className="pt-1">
                        <span className="text-[10px] text-slate-500 block mb-1 uppercase font-semibold">
                          Angle {quad.angle}° Defects & Tolerances:
                        </span>
                        {viewData.defects && viewData.defects.length > 0 ? (
                          <div className="bg-rose-950/40 border border-rose-900/60 p-2 rounded text-[10px] text-rose-300 space-y-1">
                            {viewData.defects.map((d: string, i: number) => (
                              <div key={i} className="leading-tight">• {d}</div>
                            ))}
                          </div>
                        ) : (
                          <div className="bg-emerald-950/40 border border-emerald-900/50 p-1.5 rounded text-[10px] text-emerald-400 flex items-center gap-1.5">
                            <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                            <span>No surface or geometry defects (PASS)</span>
                          </div>
                        )}
                      </div>
                    </>
                  ) : (
                    <div className="py-8 text-center text-slate-500 flex flex-col items-center justify-center">
                      <RefreshCw className={`w-5 h-5 mb-2 ${isCapturingNow ? 'text-cyan-400 animate-spin' : 'text-slate-700'}`} />
                      <span className="text-[11px] font-mono">
                        {isCapturingNow ? `Analyzing ${quad.angle}° frame...` : 'Awaiting Cycle Execution'}
                      </span>
                      <p className="text-[10px] text-slate-600 mt-1 max-w-[180px]">
                        {quad.desc}
                      </p>
                    </div>
                  )}
                </div>

                {/* Card Footer */}
                <div className="px-3 py-1.5 bg-industrial-900/60 border-t border-industrial-800/80 flex items-center justify-between text-[10px] font-mono text-slate-500">
                  <span>SG90 Platform: {quad.angle}°</span>
                  <span>{hasData ? (viewData?.is_within_tolerance ? '±Tol: Compliant' : '±Tol: Exceeded') : 'Pending'}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ROW 3: COMPLEMENTARY SENSORS — METHOD 2 (LASER) & METHOD 3 (EDDY CURRENT) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* METHOD 2: TRIANGULAR LASER PROFILING (REAL) (6 Cols) */}
        <div className="lg:col-span-6 bg-industrial-900 border border-industrial-800 rounded-xl p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-industrial-800 pb-2">
            <span className="text-xs font-mono font-bold text-rose-400 uppercase tracking-wider flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
              Method 2: Triangular Laser Profilometry (REAL)
            </span>
            <span
              className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                laserResult?.status === 'PASS'
                  ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                  : laserResult?.status === 'FAIL'
                  ? 'bg-rose-950 text-rose-400 border border-rose-800'
                  : 'bg-industrial-800 text-slate-400'
              }`}
            >
              {laserResult?.status || 'AWAITING'}
            </span>
          </div>

          {/* Industrial Laser Profile Chart */}
          <div className="h-44 w-full bg-industrial-950 rounded-lg p-2 border border-industrial-800 relative">
            {laserResult?.profile_sample ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={laserResult.profile_sample} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="laserGlow" x1="0" y1="0" x2="0" y2="1">
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
                  {laserResult?.peak_height_mm && (
                    <ReferenceLine
                      y={laserResult.peak_height_mm}
                      stroke="#38bdf8"
                      strokeDasharray="3 3"
                      label={{
                        value: `Peak: ${laserResult.peak_height_mm}mm`,
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
                    strokeWidth={2.2}
                    fill="url(#laserGlow)"
                    dot={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-xs font-mono text-slate-500 gap-2">
                <div className="w-8 h-8 rounded-full border border-rose-900 flex items-center justify-center text-rose-500">
                  📡
                </div>
                <span>Awaiting laser triangulation surface profile...</span>
              </div>
            )}
          </div>

          {/* Profile Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
            <div className="p-2 rounded bg-industrial-850 border border-industrial-800">
              <div className="text-slate-500 text-[10px]">PEAK HEIGHT (h_max)</div>
              <div className="text-white font-bold">
                {laserResult ? `${laserResult.peak_height_mm} mm` : '-'}
              </div>
            </div>
            <div className="p-2 rounded bg-industrial-850 border border-industrial-800">
              <div className="text-slate-500 text-[10px]">HEIGHT VARIATION (Δh)</div>
              <div className="text-cyan-400 font-bold">
                {laserResult ? `${laserResult.max_height_variation_mm} mm` : '-'}
              </div>
            </div>
            <div className="p-2 rounded bg-industrial-850 border border-industrial-800">
              <div className="text-slate-500 text-[10px]">ROUGHNESS (R_z)</div>
              <div className="text-emerald-400 font-bold">
                {laserResult ? `${laserResult.roughness_std_mm ?? 0.04} mm` : '-'}
              </div>
            </div>
            <div className="p-2 rounded bg-industrial-850 border border-industrial-800">
              <div className="text-slate-500 text-[10px]">GEOMETRY STATUS</div>
              <div className="text-slate-200 font-bold truncate">
                {laserResult?.calibration_notice || 'CALIBRATED'}
              </div>
            </div>
          </div>

          {laserResult?.anomalies?.length > 0 && (
            <div className="p-2 rounded bg-rose-950/30 border border-rose-900/50 text-[11px] font-mono text-rose-300">
              {laserResult.anomalies.map((a: string, i: number) => (
                <div key={i}>• {a}</div>
              ))}
            </div>
          )}
        </div>

        {/* METHOD 3: EDDY CURRENT ARRAY INSPECTION (6 Cols) */}
        <div className="lg:col-span-6 bg-industrial-900 border border-industrial-800 rounded-xl p-4 shadow-sm space-y-3 relative">
          <div className="flex items-center justify-between border-b border-industrial-800 pb-2">
            <span className="text-xs font-mono font-bold text-sky-400 uppercase tracking-wider flex items-center gap-1.5">
              Method 3: Eddy Current Array (ECI)
              <span className="bg-sky-950 text-sky-300 border border-sky-800 text-[10px] px-2 py-0.5 rounded font-mono font-medium">
                {metals[selectedMetal]?.name || 'Alloy Calibrated'}
              </span>
            </span>
            <span
              className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                eddyResult?.status === 'PASS'
                  ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                  : eddyResult?.status === 'FAIL'
                  ? 'bg-rose-950 text-rose-400 border border-rose-800'
                  : 'bg-industrial-800 text-slate-400'
              }`}
            >
              {eddyResult?.status || 'AWAITING'}
            </span>
          </div>

          {/* Coil Array Bar Chart */}
          <div className="h-44 w-full bg-industrial-950 rounded-lg p-2 border border-industrial-800">
            {eddyChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={eddyChartData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 9, fontFamily: 'monospace' }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 9, fontFamily: 'monospace' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', fontSize: '11px', fontFamily: 'monospace' }}
                    itemStyle={{ color: '#38bdf8' }}
                  />
                  <ReferenceLine y={12} stroke="#ef4444" strokeDasharray="3 3" />
                  <Bar dataKey="deviation" fill="#0284c7" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-[11px] font-mono text-slate-600">
                Awaiting 8-coil high-frequency array scan...
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
            <div className="p-2 rounded bg-industrial-850 border border-industrial-800">
              <div className="text-slate-500 text-[10px]">BASE IMPEDANCE (Z₀)</div>
              <div className="text-sky-400 font-bold">
                {eddyResult?.nominal_impedance ? `${eddyResult.nominal_impedance} Ω` : '-'}
              </div>
            </div>
            <div className="p-2 rounded bg-industrial-850 border border-industrial-800">
              <div className="text-slate-500 text-[10px]">MAX DEVIATION (ΔZ)</div>
              <div className="text-amber-400 font-bold">
                {eddyResult ? `${eddyResult.max_deviation_pct}%` : '-'}
              </div>
            </div>
            <div className="p-2 rounded bg-industrial-850 border border-industrial-800">
              <div className="text-slate-500 text-[10px]">OPERATING FREQ</div>
              <div className="text-slate-200 font-bold">
                {eddyResult?.operating_freq_khz ? `${eddyResult.operating_freq_khz} kHz` : `${metals[selectedMetal]?.operating_freq_khz || 100} kHz`}
              </div>
            </div>
            <div className="p-2 rounded bg-industrial-850 border border-industrial-800">
              <div className="text-slate-500 text-[10px]">SIGNAL-TO-NOISE</div>
              <div className="text-emerald-400 font-bold">
                {eddyResult?.snr_db ? `${eddyResult.snr_db} dB` : '38.4 dB'}
              </div>
            </div>
          </div>

          {eddyResult?.anomalies?.length > 0 && (
            <div className="p-2 rounded bg-rose-950/30 border border-rose-900/50 text-[11px] font-mono text-rose-300">
              {eddyResult.anomalies.map((a: string, i: number) => (
                <div key={i}>• {a}</div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
