import React, { useState, useEffect } from 'react';
import {
  fetchSettings,
  updateSettings,
  resetSettings,
} from '../services/api';
import {
  Settings as SettingsIcon,
  Save,
  RotateCcw,
  Camera,
  Cpu,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  Layers,
  ShieldAlert,
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [config, setConfig] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings()
      .then((data) => setConfig(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleChange = (key: string, value: any) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await updateSettings(config);
      setSavedMessage('Settings successfully saved and applied to runtime.');
    } catch (err: any) {
      setSavedMessage(`Error saving settings: ${err.message}`);
    } finally {
      setLoading(false);
      setTimeout(() => setSavedMessage(null), 3500);
    }
  };

  const handleReset = async () => {
    if (window.confirm('Reset all parameters back to factory defaults?')) {
      setLoading(true);
      try {
        const res = await resetSettings();
        setConfig(res.config);
        setSavedMessage('Configuration reset to factory defaults.');
      } catch (err: any) {
        setSavedMessage(`Error: ${err.message}`);
      } finally {
        setLoading(false);
        setTimeout(() => setSavedMessage(null), 3500);
      }
    }
  };

  if (loading && Object.keys(config).length === 0) {
    return <div className="p-8 text-center text-slate-500 font-mono text-xs">Loading configuration parameters...</div>;
  }

  return (
    <form onSubmit={handleSave} className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-cyan-950/60 border border-cyan-800 text-cyan-400">
            <SettingsIcon className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">System & Hardware Configuration</h1>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Inspection tolerances, camera streaming endpoints, serial hardware, and optical calibration
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <button
            type="button"
            onClick={handleReset}
            className="px-4 py-2 rounded-lg border border-industrial-700 bg-industrial-850 hover:bg-industrial-800 text-slate-300 text-xs font-mono flex items-center gap-2"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Reset Defaults
          </button>
          <button
            type="submit"
            className="px-5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-mono font-bold flex items-center gap-2 shadow glow-cyan"
          >
            <Save className="w-3.5 h-3.5" /> Save Changes
          </button>
        </div>
      </div>

      {savedMessage && (
        <div className="bg-emerald-950/60 border border-emerald-800 text-emerald-300 font-mono text-xs px-4 py-2.5 rounded-lg flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          {savedMessage}
        </div>
      )}

      {/* HARDWARE MODE SWITCH (REAL VS SIMULATION) */}
      <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-industrial-850 text-amber-400 border border-industrial-800">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
                Operation Mode: Hardware Simulation
              </h2>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Enable to simulate Arduino servos, conveyors, and optical triggers without physical hardware attached.
              </p>
            </div>
          </div>

          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={Boolean(config.HARDWARE_SIMULATION_MODE)}
              onChange={(e) => handleChange('HARDWARE_SIMULATION_MODE', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-industrial-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-600"></div>
          </label>
        </div>
      </div>

      {/* Grid of Setting Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Section 1: Android Inspection Camera Configuration */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-industrial-800 pb-3">
            <Camera className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-semibold font-mono text-slate-200 uppercase tracking-wider">
              Method 1: Android Camera Settings
            </h2>
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Video Stream Source (URL or USB Camera Index):</label>
              <input
                type="text"
                value={config.CAMERA_SOURCE || ''}
                onChange={(e) => handleChange('CAMERA_SOURCE', e.target.value)}
                placeholder="http://192.168.1.100:8080/video or 0"
                className="w-full bg-industrial-950 border border-industrial-800 rounded-lg p-2.5 text-slate-200 outline-none focus:border-cyan-500"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">
                Use Android IP Webcam app MJPEG stream or USB webcam index (e.g. 0).
              </span>
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Snapshot URL (High Resolution Capture):</label>
              <input
                type="text"
                value={config.CAMERA_SNAPSHOT_URL || ''}
                onChange={(e) => handleChange('CAMERA_SNAPSHOT_URL', e.target.value)}
                placeholder="http://192.168.1.100:8080/shot.jpg"
                className="w-full bg-industrial-950 border border-industrial-800 rounded-lg p-2.5 text-slate-200 outline-none focus:border-cyan-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 block mb-1">Camera Angle (° to Platform):</label>
                <input
                  type="number"
                  step="0.5"
                  value={config.CAMERA_ANGLE_DEG || 50}
                  onChange={(e) => handleChange('CAMERA_ANGLE_DEG', parseFloat(e.target.value))}
                  className="w-full bg-industrial-950 border border-industrial-800 rounded-lg p-2.5 text-slate-200 outline-none"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">CV Pixel Calibration (mm/px):</label>
                <input
                  type="number"
                  step="0.001"
                  value={config.CV_MM_PER_PIXEL || 0.12}
                  onChange={(e) => handleChange('CV_MM_PER_PIXEL', parseFloat(e.target.value))}
                  className="w-full bg-industrial-950 border border-industrial-800 rounded-lg p-2.5 text-slate-200 outline-none"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Arduino & Serial Port Settings */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-industrial-800 pb-3">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-semibold font-mono text-slate-200 uppercase tracking-wider">
              Arduino Serial Hardware
            </h2>
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 block mb-1">Serial Port (COM / tty):</label>
                <input
                  type="text"
                  value={config.SERIAL_PORT || 'COM3'}
                  onChange={(e) => handleChange('SERIAL_PORT', e.target.value)}
                  className="w-full bg-industrial-950 border border-industrial-800 rounded-lg p-2.5 text-slate-200 outline-none"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Baud Rate (bps):</label>
                <input
                  type="number"
                  value={config.BAUD_RATE || 115200}
                  onChange={(e) => handleChange('BAUD_RATE', parseInt(e.target.value))}
                  className="w-full bg-industrial-950 border border-industrial-800 rounded-lg p-2.5 text-slate-200 outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-slate-400 block mb-1">Servo ACK Timeout (s):</label>
                <input
                  type="number"
                  step="0.5"
                  value={config.SERVO_ACK_TIMEOUT || 6.0}
                  onChange={(e) => handleChange('SERVO_ACK_TIMEOUT', parseFloat(e.target.value))}
                  className="w-full bg-industrial-950 border border-industrial-800 rounded-lg p-2.5 text-slate-200 outline-none"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Arrival Timeout (s):</label>
                <input
                  type="number"
                  step="1"
                  value={config.ARRIVAL_TIMEOUT || 20.0}
                  onChange={(e) => handleChange('ARRIVAL_TIMEOUT', parseFloat(e.target.value))}
                  className="w-full bg-industrial-950 border border-industrial-800 rounded-lg p-2.5 text-slate-200 outline-none"
                />
              </div>
            </div>

            <div className="p-2.5 rounded bg-amber-950/30 border border-amber-900/40 text-[11px] text-amber-300">
              ⚠️ Ensure external 5V/2A power supply is used for SG90 servos with shared common GND to Arduino.
            </div>
          </div>
        </div>

        {/* Section 3: Component Reference Tolerances */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-industrial-800 pb-3">
            <Sliders className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-semibold font-mono text-slate-200 uppercase tracking-wider">
              Component Geometry Tolerances (mm)
            </h2>
          </div>

          <div className="space-y-4 font-mono text-xs">
            {/* Nut Tolerances */}
            <div>
              <span className="text-cyan-400 font-bold block mb-2">NUT (HEXAGONAL) STANDARDS:</span>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">Target Across-Flats (mm):</label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.NUT_TARGET_OUTER_MM || 21.0}
                    onChange={(e) => handleChange('NUT_TARGET_OUTER_MM', parseFloat(e.target.value))}
                    className="w-full bg-industrial-950 border border-industrial-800 rounded-lg p-2 text-slate-200 outline-none"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Flats Tolerance (± mm):</label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.NUT_TOLERANCE_OUTER_MM || 1.2}
                    onChange={(e) => handleChange('NUT_TOLERANCE_OUTER_MM', parseFloat(e.target.value))}
                    className="w-full bg-industrial-950 border border-industrial-800 rounded-lg p-2 text-slate-200 outline-none"
                  />
                </div>
              </div>
            </div>

            {/* Washer Tolerances */}
            <div>
              <span className="text-emerald-400 font-bold block mb-2">WASHER (CIRCULAR) STANDARDS:</span>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">Target Outer Dia (mm):</label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.WASHER_TARGET_OUTER_MM || 24.0}
                    onChange={(e) => handleChange('WASHER_TARGET_OUTER_MM', parseFloat(e.target.value))}
                    className="w-full bg-industrial-950 border border-industrial-800 rounded-lg p-2 text-slate-200 outline-none"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Outer Tolerance (± mm):</label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.WASHER_TOLERANCE_OUTER_MM || 1.5}
                    onChange={(e) => handleChange('WASHER_TOLERANCE_OUTER_MM', parseFloat(e.target.value))}
                    className="w-full bg-industrial-950 border border-industrial-800 rounded-lg p-2 text-slate-200 outline-none"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Section 4: Laser & Eddy Current Thresholds */}
        <div className="bg-industrial-900 border border-industrial-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-industrial-800 pb-3">
            <Layers className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-semibold font-mono text-slate-200 uppercase tracking-wider">
              Laser & Eddy Inspection Limits
            </h2>
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Laser Triangulation Angle (°):</label>
              <input
                type="number"
                step="0.5"
                value={config.LASER_ANGLE_DEG || 35.0}
                onChange={(e) => handleChange('LASER_ANGLE_DEG', parseFloat(e.target.value))}
                className="w-full bg-industrial-950 border border-industrial-800 rounded-lg p-2.5 text-slate-200 outline-none"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Laser Max Surface Variation Tolerance (mm):</label>
              <input
                type="number"
                step="0.05"
                value={config.LASER_MAX_HEIGHT_VARIATION_MM || 0.65}
                onChange={(e) => handleChange('LASER_MAX_HEIGHT_VARIATION_MM', parseFloat(e.target.value))}
                className="w-full bg-industrial-950 border border-industrial-800 rounded-lg p-2.5 text-slate-200 outline-none"
              />
            </div>

            <div>
              <label className="text-sky-400 block mb-1">
                Eddy Current Anomaly Threshold (fraction):
              </label>
              <input
                type="number"
                step="0.01"
                value={config.EDDY_ANOMALY_THRESHOLD || 0.12}
                onChange={(e) => handleChange('EDDY_ANOMALY_THRESHOLD', parseFloat(e.target.value))}
                className="w-full bg-industrial-950 border border-industrial-800 rounded-lg p-2.5 text-slate-200 outline-none"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">
                Readings deviating &gt; 12% trigger subsurface defect flags.
              </span>
            </div>
          </div>
        </div>
      </div>
    </form>
  );
};

