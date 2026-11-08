import React, { useState, useEffect } from 'react';
import { DashboardPage } from './pages/DashboardPage';
import { LiveInspectionPage } from './pages/LiveInspectionPage';
import { SortingMonitorPage } from './pages/SortingMonitorPage';
import { InspectionHistoryPage } from './pages/InspectionHistoryPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';
import { fetchOperationMode, setOperationMode } from './services/api';
import {
  LayoutDashboard,
  Radio,
  SlidersHorizontal,
  History,
  FileBarChart,
  Settings,
  Hexagon,
  Power,
  Layers,
  Wrench,
  Zap,
} from 'lucide-react';

export type NavTab = 'dashboard' | 'live' | 'sorting' | 'history' | 'reports' | 'settings';

export default function App() {
  const [currentTab, setCurrentTab] = useState<NavTab>('dashboard');
  const [opMode, setOpMode] = useState<'manual' | 'automated'>('automated');
  const [isSwitching, setIsSwitching] = useState(false);

  useEffect(() => {
    fetchOperationMode().then((res) => {
      if (res && res.mode) setOpMode(res.mode);
    }).catch(console.error);

    const interval = setInterval(() => {
      fetchOperationMode().then((res) => {
        if (res && res.mode) setOpMode(res.mode);
      }).catch(() => {});
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleSwitchMode = async (targetMode: 'manual' | 'automated') => {
    if (opMode === targetMode) return;
    setIsSwitching(true);
    setOpMode(targetMode);
    try {
      const res = await setOperationMode(targetMode);
      if (res && res.mode) setOpMode(res.mode as any);
      // Auto-navigate to relevant tab if switching
      if (targetMode === 'manual' && currentTab === 'dashboard') {
        setCurrentTab('sorting');
      } else if (targetMode === 'automated' && currentTab === 'sorting') {
        setCurrentTab('live');
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsSwitching(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f17] text-slate-100 flex flex-col font-sans">
      {/* Primary Top Header Navigation */}
      <header className="border-b border-industrial-800 bg-industrial-900/90 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setCurrentTab('dashboard')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-md shadow-cyan-950 glow-cyan">
              <Hexagon className="w-6 h-6 stroke-[2.2]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-black tracking-wider text-white font-mono uppercase">
                  INSPECTRA
                </span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-400 border border-cyan-800 font-mono font-bold">
                  PRO
                </span>
              </div>
              <span className="text-[10px] text-slate-400 font-mono block -mt-0.5">
                Automated Quality Inspection & Sorting
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex items-center gap-1 font-mono text-xs font-semibold">
            <button
              onClick={() => setCurrentTab('dashboard')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg transition-all ${
                currentTab === 'dashboard'
                  ? 'bg-industrial-800 text-cyan-400 border border-industrial-700 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-industrial-850'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" /> Dashboard
            </button>

            <button
              onClick={() => setCurrentTab('live')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg transition-all ${
                currentTab === 'live'
                  ? 'bg-industrial-800 text-cyan-400 border border-industrial-700 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-industrial-850'
              }`}
            >
              <Radio className="w-4 h-4" /> Live Inspection
            </button>

            <button
              onClick={() => setCurrentTab('sorting')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg transition-all ${
                currentTab === 'sorting'
                  ? 'bg-industrial-800 text-cyan-400 border border-industrial-700 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-industrial-850'
              }`}
            >
              <SlidersHorizontal className="w-4 h-4" /> Manual Controls & Sorting
            </button>

            <button
              onClick={() => setCurrentTab('history')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg transition-all ${
                currentTab === 'history'
                  ? 'bg-industrial-800 text-cyan-400 border border-industrial-700 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-industrial-850'
              }`}
            >
              <History className="w-4 h-4" /> History
            </button>

            <button
              onClick={() => setCurrentTab('reports')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg transition-all ${
                currentTab === 'reports'
                  ? 'bg-industrial-800 text-cyan-400 border border-industrial-700 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-industrial-850'
              }`}
            >
              <FileBarChart className="w-4 h-4" /> Reports
            </button>

            <button
              onClick={() => setCurrentTab('settings')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg transition-all ${
                currentTab === 'settings'
                  ? 'bg-industrial-800 text-cyan-400 border border-industrial-700 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-industrial-850'
              }`}
            >
              <Settings className="w-4 h-4" /> Settings
            </button>
          </nav>

          {/* Master Operation Mode Switcher */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 p-1 rounded-xl bg-industrial-950 border border-industrial-800 font-mono text-xs">
              <button
                onClick={() => handleSwitchMode('manual')}
                disabled={isSwitching}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold transition-all ${
                  opMode === 'manual'
                    ? 'bg-amber-600 text-white shadow-md shadow-amber-950 border border-amber-400'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-industrial-850'
                }`}
                title="Manual section: engage individual conveyors, test servos and divert manually"
              >
                <Wrench className="w-3.5 h-3.5" />
                MANUAL
              </button>

              <button
                onClick={() => handleSwitchMode('automated')}
                disabled={isSwitching}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold transition-all ${
                  opMode === 'automated'
                    ? 'bg-emerald-600 text-white shadow-md shadow-emerald-950 animate-pulse border border-emerald-400'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-industrial-850'
                }`}
                title="Fully automated mode: optical sensors on Arduino trigger all conveyor feeds, 90° rotation, inspection and sorting automatically"
              >
                <Zap className="w-3.5 h-3.5 fill-current" />
                FULLY AUTOMATED
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Nav Bar */}
      <div className="md:hidden flex overflow-x-auto border-b border-industrial-800 bg-industrial-950 px-2 py-2 gap-1 text-xs font-mono">
        {(['dashboard', 'live', 'sorting', 'history', 'reports', 'settings'] as NavTab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setCurrentTab(tab)}
            className={`px-3 py-1.5 rounded whitespace-nowrap capitalize ${
              currentTab === tab ? 'bg-industrial-800 text-cyan-400 font-bold' : 'text-slate-400'
            }`}
          >
            {tab === 'sorting' ? 'Manual & Sorting' : tab}
          </button>
        ))}
      </div>

      {/* Main Page Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentTab === 'dashboard' && (
          <DashboardPage
            onNavigate={(view) => setCurrentTab(view as NavTab)}
            onStartInspection={() => setCurrentTab('live')}
          />
        )}
        {currentTab === 'live' && <LiveInspectionPage />}
        {currentTab === 'sorting' && <SortingMonitorPage />}
        {currentTab === 'history' && <InspectionHistoryPage />}
        {currentTab === 'reports' && <ReportsPage />}
        {currentTab === 'settings' && <SettingsPage />}
      </main>

      {/* Industrial Footer */}
      <footer className="border-t border-industrial-800/80 bg-industrial-950 text-slate-500 font-mono text-xs py-4 px-4 sm:px-6 lg:px-8 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            INSPECTRA Automated Inspection Prototype — Mechanical, Vision, Laser & Eddy-Current Integration
          </div>
          <div className="flex items-center gap-4 text-[11px]">
            <span>Method 1: CV (REAL)</span>
            <span>•</span>
            <span>Method 2: Laser Triangulation (REAL)</span>
            <span>•</span>
            <span className="text-sky-400 font-bold">Method 3: Eddy Current Array</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
