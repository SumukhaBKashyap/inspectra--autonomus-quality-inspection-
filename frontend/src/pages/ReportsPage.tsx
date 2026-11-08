import React, { useState, useEffect } from 'react';
import {
  fetchStatistics,
  fetchInspections,
  DashboardStats,
  InspectionSummary,
  BACKEND_URL,
} from '../services/api';
import {
  FileText,
  Download,
  Printer,
  PieChart as PieIcon,
  BarChart3,
  TrendingUp,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts';

export const ReportsPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [inspections, setInspections] = useState<InspectionSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [s, i] = await Promise.all([fetchStatistics(), fetchInspections(0, 100)]);
      setStats(s);
      setInspections(i);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handlePrint = () => {
    window.print();
  };

  const handleExportJSON = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(inspections, null, 2));
    const dlAnchorElem = document.createElement('a');
    dlAnchorElem.setAttribute('href', dataStr);
    dlAnchorElem.setAttribute('download', `inspectra_report_${new Date().toISOString().slice(0, 10)}.json`);
    dlAnchorElem.click();
  };

  const pieData = stats
    ? [
        { name: 'PASS', value: stats.pass_count, color: '#10b981' },
        { name: 'FAIL', value: stats.fail_count, color: '#ef4444' },
        { name: 'REVIEW', value: stats.review_count, color: '#f59e0b' },
      ].filter((d) => d.value > 0)
    : [];

  const typeData = stats
    ? [
        { name: 'Nuts (Hex)', count: stats.nut_count, fill: '#06b6d4' },
        { name: 'Washers (Round)', count: stats.washer_count, fill: '#10b981' },
        { name: 'Unknown', count: stats.unknown_count, fill: '#64748b' },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* Top Controls & Export Bar */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-cyan-950/60 border border-cyan-800 text-cyan-400">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">Quality Inspection Analytics & Reports</h1>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Automated Statistical Process Control (SPC) & Exportable Audit Trails
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <button
            onClick={handlePrint}
            className="px-3.5 py-2 rounded-lg border border-industrial-700 bg-industrial-850 hover:bg-industrial-800 text-slate-300 text-xs font-mono flex items-center gap-2"
          >
            <Printer className="w-3.5 h-3.5" /> Print Report
          </button>
          <a
            href={`${BACKEND_URL}/api/inspections/export/csv`}
            download="inspectra_report.csv"
            className="px-4 py-2 rounded-lg bg-industrial-800 hover:bg-industrial-700 text-cyan-400 border border-industrial-700 text-xs font-mono font-bold flex items-center gap-2"
          >
            <Download className="w-3.5 h-3.5" /> Export CSV
          </a>
          <button
            onClick={handleExportJSON}
            className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-mono font-bold flex items-center gap-2 shadow glow-cyan"
          >
            <Download className="w-3.5 h-3.5" /> Export JSON
          </button>
        </div>
      </div>

      {/* High-level Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 font-mono text-xs">
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-4">
          <div className="text-slate-400 uppercase">Total Inspected Volume</div>
          <div className="text-2xl font-bold text-white mt-1">{stats?.total ?? 0} units</div>
          <div className="text-slate-500 mt-1">100% evaluated across 3 methods</div>
        </div>

        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-4 border-l-4 border-l-emerald-500">
          <div className="text-slate-400 uppercase">First Pass Yield (FPY)</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{stats?.pass_rate_pct ?? 0}%</div>
          <div className="text-slate-500 mt-1">{stats?.pass_count ?? 0} units accepted</div>
        </div>

        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-4 border-l-4 border-l-rose-500">
          <div className="text-slate-400 uppercase">Defect Rejection Rate</div>
          <div className="text-2xl font-bold text-rose-400 mt-1">{stats?.fail_rate_pct ?? 0}%</div>
          <div className="text-slate-500 mt-1">{stats?.fail_count ?? 0} hard rejections</div>
        </div>

        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-4 border-l-4 border-l-amber-500">
          <div className="text-slate-400 uppercase">Manual Review Rate</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">{stats?.review_rate_pct ?? 0}%</div>
          <div className="text-slate-500 mt-1">{stats?.review_count ?? 0} halted for inspection</div>
        </div>
      </div>

      {/* Statistical Distribution Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pass/Fail/Review Distribution */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between border-b border-industrial-800 pb-3 mb-4">
            <h2 className="text-sm font-semibold font-mono text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <PieIcon className="w-4 h-4 text-cyan-400" />
              Inspection Quality Breakdown
            </h2>
          </div>
          <div className="h-64 flex items-center justify-center">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" outerRadius={90} innerRadius={60} paddingAngle={4} dataKey="value">
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
              <div className="text-xs text-slate-500 font-mono">No data available yet</div>
            )}
          </div>
        </div>

        {/* Component Distribution (Nuts vs Washers) */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between border-b border-industrial-800 pb-3 mb-4">
            <h2 className="text-sm font-semibold font-mono text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-cyan-400" />
              Component Classification Split
            </h2>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={typeData} margin={{ top: 20, right: 20, left: -10, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px' }}
                  itemStyle={{ color: '#06b6d4', fontFamily: 'monospace' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {typeData.map((entry, index) => (
                    <Cell key={`cell-type-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Defect Analysis Breakdown */}
      <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-sm">
        <h2 className="text-sm font-semibold font-mono text-slate-200 uppercase tracking-wider mb-4">
          Independent Quality Method Root Cause Analysis
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
          <div className="p-4 rounded-lg bg-industrial-850 border border-industrial-800">
            <div className="text-slate-400 uppercase font-bold">1. Computer Vision (REAL)</div>
            <div className="text-2xl font-bold text-white mt-2">
              {stats?.defects_by_type.cv_surface_defects ?? 0}
            </div>
            <p className="text-slate-500 mt-1 leading-relaxed">
              Surface cracks, scratches, edge burrs, and dimensional tolerance breaches.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-industrial-850 border border-industrial-800">
            <div className="text-slate-400 uppercase font-bold">2. Triangular Laser (REAL)</div>
            <div className="text-2xl font-bold text-white mt-2">
              {stats?.defects_by_type.laser_height_anomalies ?? 0}
            </div>
            <p className="text-slate-500 mt-1 leading-relaxed">
              Peak-to-valley profile roughness, warp, surface steps, and height variations.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-industrial-850 border border-industrial-800">
            <div className="text-sky-400 uppercase font-bold flex items-center justify-between">
              <span>3. Eddy Current Array</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800">
                ECI METHOD
              </span>
            </div>
            <div className="text-2xl font-bold text-white mt-2">
              {stats?.defects_by_type.eddy_anomalies_simulated ?? 0}
            </div>
            <p className="text-slate-500 mt-1 leading-relaxed">
              Subsurface impedance deviation spikes across 8-coil perimeter array.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

