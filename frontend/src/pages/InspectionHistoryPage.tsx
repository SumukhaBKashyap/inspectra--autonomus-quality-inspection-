import React, { useState, useEffect } from 'react';
import {
  fetchInspections,
  fetchInspection,
  clearAllInspections,
  InspectionSummary,
  InspectionDetail,
  BACKEND_URL,
} from '../services/api';
import {
  Search,
  Filter,
  Trash2,
  RefreshCw,
  Eye,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  X,
  Layers,
  Box,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';


export const InspectionHistoryPage: React.FC = () => {
  const [inspections, setInspections] = useState<InspectionSummary[]>([]);
  const [filterOutcome, setFilterOutcome] = useState<string>('');
  const [filterType, setFilterType] = useState<string>('');
  const [searchId, setSearchId] = useState<string>('');
  const [loading, setLoading] = useState(false);

  // Selected Detail Modal
  const [selectedDetail, setSelectedDetail] = useState<InspectionDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchInspections(0, 100, filterOutcome || undefined, filterType || undefined);
      setInspections(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterOutcome, filterType]);

  const handleOpenDetail = async (id: string) => {
    setDetailLoading(true);
    try {
      const detail = await fetchInspection(id);
      setSelectedDetail(detail);
    } catch (e) {
      console.error(e);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleClearHistory = async () => {
    if (window.confirm('Are you sure you want to permanently clear all inspection history?')) {
      await clearAllInspections();
      loadData();
    }
  };

  const filtered = inspections.filter((item) => {
    if (searchId && !item.id.toLowerCase().includes(searchId.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Top Filter and Search Bar */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 bg-industrial-900 border border-industrial-800 rounded-xl p-4 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-cyan-950/60 border border-cyan-800 text-cyan-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">Inspection History Records</h1>
            <p className="text-xs text-slate-400 font-mono">
              Saved telemetry, CV multi-angle imagery, laser height maps, and eddy current array data
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center flex-wrap gap-3 w-full lg:w-auto">
          {/* Search by ID */}
          <div className="flex items-center gap-2 bg-industrial-850 px-3 py-1.5 rounded-lg border border-industrial-800 text-xs font-mono">
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search UUID..."
              value={searchId}
              onChange={(e) => setSearchId(e.target.value)}
              className="bg-transparent text-slate-200 outline-none w-28 md:w-36"
            />
          </div>

          {/* Outcome Filter */}
          <select
            value={filterOutcome}
            onChange={(e) => setFilterOutcome(e.target.value)}
            className="bg-industrial-850 text-slate-200 border border-industrial-800 rounded-lg px-3 py-1.5 text-xs font-mono outline-none"
          >
            <option value="">All Outcomes</option>
            <option value="PASS">PASS</option>
            <option value="FAIL">FAIL</option>
            <option value="REVIEW">REVIEW</option>
          </select>

          {/* Type Filter */}
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-industrial-850 text-slate-200 border border-industrial-800 rounded-lg px-3 py-1.5 text-xs font-mono outline-none"
          >
            <option value="">All Types</option>
            <option value="NUT">NUT</option>
            <option value="WASHER">WASHER</option>
          </select>

          <button
            onClick={loadData}
            className="p-2 rounded-lg border border-industrial-700 bg-industrial-850 hover:bg-industrial-800 text-slate-300"
            title="Refresh"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={handleClearHistory}
            className="px-3 py-1.5 rounded-lg border border-rose-900 bg-rose-950/40 hover:bg-rose-900/60 text-rose-400 text-xs font-mono flex items-center gap-1.5 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" /> Clear All
          </button>
        </div>
      </div>

      {/* History Table */}
      <div className="bg-industrial-900 border border-industrial-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-industrial-800 bg-industrial-850 text-slate-400">
                <th className="py-3 px-4">Inspection ID</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Outcome</th>
                <th className="py-3 px-4 min-w-[210px]">Target vs Measured (OD / ID)</th>
                <th className="py-3 px-4">CV Status</th>
                <th className="py-3 px-4">Laser Triangulation</th>
                <th className="py-3 px-4">Eddy Array</th>
                <th className="py-3 px-4">Sorting Command</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-industrial-800/60">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-8 text-center text-slate-500 font-mono">
                    {loading ? 'Loading historical inspections...' : 'No inspections match the selected filters.'}
                  </td>
                </tr>
              ) : (
                filtered.map((item) => (
                  <tr key={item.id} className="hover:bg-industrial-850/50 transition-colors">
                    <td className="py-3 px-4 text-cyan-400 font-bold">{item.id.slice(0, 8)}...</td>
                    <td className="py-3 px-4 text-slate-400">
                      {item.created_at ? new Date(item.created_at).toLocaleString() : '-'}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded bg-industrial-800 text-slate-200 border border-industrial-700">
                        {item.component_type}
                      </span>
                    </td>
                    <td className="py-3 px-4">
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
                    <td className="py-3 px-4">
                      {item.dimensions?.measured_outer_mm || item.dimensions?.outer_diameter_mm ? (
                        <div className="flex flex-col gap-0.5">
                          <div className="text-[10px] text-slate-400">
                            <span className="text-amber-400 font-bold">REQ: </span>
                            {item.dimensions?.required_outer_mm ?? 10.0} / {item.dimensions?.required_inner_mm ?? 5.0} mm
                            <span className="text-slate-500 text-[9px] ml-1">(±{item.dimensions?.required_tolerance_mm ?? 0.45}mm)</span>
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
                    <td className="py-3 px-4 text-slate-300">{item.cv_status}</td>
                    <td className="py-3 px-4 text-slate-300">{item.laser_status}</td>
                    <td className="py-3 px-4 text-slate-300">{item.eddy_status}</td>
                    <td className="py-3 px-4 text-slate-400 text-[11px]">{item.sorting_command}</td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleOpenDetail(item.id)}
                        className="px-2.5 py-1 rounded bg-industrial-800 hover:bg-industrial-700 text-cyan-400 border border-industrial-700 font-medium inline-flex items-center gap-1"
                      >
                        <Eye className="w-3 h-3" /> Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Inspection Detail Modal */}
      {selectedDetail && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-industrial-900 border border-industrial-700 rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto shadow-2xl p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-industrial-800 pb-3">
              <div>
                <h2 className="text-base font-bold font-mono text-white flex items-center gap-2">
                  Inspection Telemetry: <span className="text-cyan-400">{selectedDetail.id}</span>
                </h2>
                <div className="text-xs font-mono text-slate-400 mt-1">
                  Recorded: {new Date(selectedDetail.created_at).toLocaleString()} | Duration:{' '}
                  {selectedDetail.duration_ms.toFixed(0)} ms
                </div>
              </div>
              <button
                onClick={() => setSelectedDetail(null)}
                className="p-1.5 rounded-lg bg-industrial-800 hover:bg-industrial-700 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Decision Summary Banner */}
            <div
              className={`p-4 rounded-xl border flex items-center justify-between ${
                selectedDetail.decision?.outcome === 'PASS'
                  ? 'bg-emerald-950/40 border-emerald-700'
                  : selectedDetail.decision?.outcome === 'FAIL'
                  ? 'bg-rose-950/40 border-rose-700'
                  : 'bg-amber-950/40 border-amber-700'
              }`}
            >
              <div>
                <div className="text-xs font-mono text-slate-400 uppercase">FINAL DECISION</div>
                <div className="text-xl font-bold font-mono text-white">
                  {selectedDetail.decision?.outcome} — {selectedDetail.decision?.component_type}
                </div>
                <div className="text-xs font-mono text-slate-300 mt-1">
                  Reason: {selectedDetail.decision?.reason || 'All parameters nominal'}
                </div>
              </div>
              <div className="text-right font-mono text-xs">
                <span className="px-3 py-1 rounded bg-black/50 text-slate-200 border border-industrial-700">
                  {selectedDetail.decision?.sorting_command}
                </span>
              </div>
            </div>

            {/* Captured Multi-Angle Images */}
            <div>
              <h3 className="text-xs font-bold font-mono text-slate-300 uppercase tracking-wider mb-3">
                Saved Inspection Images (0° & 90°)
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {selectedDetail.images.map((img) => (
                  <div key={img.id} className="space-y-1">
                    <div className="text-xs font-mono text-cyan-400">{img.label} View</div>
                    <div className="aspect-square bg-black rounded-lg border border-industrial-800 overflow-hidden">
                      <img
                        src={`${BACKEND_URL}${img.url}`}
                        alt={img.label}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Method Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
              {/* CV Result */}
              <div className="p-3.5 rounded-lg bg-industrial-850 border border-industrial-800 space-y-2">
                <div className="font-bold text-slate-300 border-b border-industrial-800 pb-1.5">
                  CV INSPECTION (REAL)
                </div>
                <div>Status: <span className="font-bold text-white">{selectedDetail.cv_result?.status}</span></div>
                <div>Outer Dia: <span className="text-cyan-400">{selectedDetail.cv_result?.dimensions?.outer_diameter_mm} mm</span></div>
                <div>Inner Hole: <span className="text-cyan-400">{selectedDetail.cv_result?.dimensions?.inner_diameter_mm} mm</span></div>
                <div>Defects: <span className="text-rose-400">{selectedDetail.cv_result?.defects?.length || 0}</span></div>
              </div>

              {/* Laser Result */}
              <div className="p-3.5 rounded-lg bg-industrial-850 border border-industrial-800 space-y-2">
                <div className="font-bold text-rose-400 border-b border-industrial-800 pb-1.5 flex items-center justify-between">
                  <span>TRIANGULAR LASER (REAL)</span>
                  <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                </div>
                <div>Status: <span className="font-bold text-white">{selectedDetail.laser_result?.status}</span></div>
                <div>Height Var (Δh): <span className="text-cyan-400">{selectedDetail.laser_result?.max_height_variation_mm} mm</span></div>
                <div>Peak Height: <span className="text-cyan-400">{selectedDetail.laser_result?.peak_height_mm} mm</span></div>
                <div>Anomalies: <span className="text-rose-400">{selectedDetail.laser_result?.anomalies?.length || 0}</span></div>
              </div>

              {/* Eddy Current Result */}
              <div className="p-3.5 rounded-lg bg-industrial-850 border border-industrial-800 space-y-2">
                <div className="font-bold text-sky-400 border-b border-industrial-800 pb-1.5">
                  EDDY CURRENT ARRAY
                </div>
                <div>Status: <span className="font-bold text-white">{selectedDetail.eddy_result?.status}</span></div>
                <div>Max Deviation: <span className="text-amber-400">{selectedDetail.eddy_result?.max_deviation_pct}%</span></div>
                <div>Coils Measured: <span className="text-slate-300">8 Array Coils</span></div>
                <div>Anomalies: <span className="text-rose-400">{selectedDetail.eddy_result?.anomalies?.length || 0}</span></div>
              </div>
            </div>

            {/* Historical Laser Surface Profilometry Graph */}
            {selectedDetail.laser_result?.profile_data && selectedDetail.laser_result.profile_data.length > 0 && (
              <div className="p-4 rounded-xl bg-industrial-900 border border-industrial-800 space-y-2 font-mono">
                <div className="flex items-center justify-between border-b border-industrial-800 pb-2">
                  <span className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
                    Scanned Laser Height Profile Graph (Triangulation Geometry)
                  </span>
                  <span className="text-[11px] text-slate-400">
                    60 Sensor Points • Δh: {selectedDetail.laser_result.max_height_variation_mm} mm
                  </span>
                </div>
                <div className="h-40 w-full bg-industrial-950 rounded-lg p-2 border border-industrial-800">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={selectedDetail.laser_result.profile_data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="historyLaserGlow" x1="0" y1="0" x2="0" y2="1">
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
                      <RechartsTooltip
                        contentStyle={{
                          backgroundColor: '#111827',
                          borderColor: '#374151',
                          borderRadius: '6px',
                          fontSize: '11px',
                          fontFamily: 'monospace'
                        }}
                        formatter={(val: any) => [`${val} mm`, 'Height']}
                        labelFormatter={(label) => `Position X: ${label} px`}
                      />
                      <ReferenceLine y={0} stroke="#475569" strokeDasharray="2 2" />
                      {selectedDetail.laser_result.peak_height_mm && (
                        <ReferenceLine
                          y={selectedDetail.laser_result.peak_height_mm}
                          stroke="#38bdf8"
                          strokeDasharray="3 3"
                          label={{
                            value: `Peak: ${selectedDetail.laser_result.peak_height_mm}mm`,
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
                        fill="url(#historyLaserGlow)"
                        dot={false}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
