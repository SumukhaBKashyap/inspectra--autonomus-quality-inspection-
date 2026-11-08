import { InspectionDetail as Detail } from '../api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';
import styles from './InspectionDetail.module.css';

interface Props {
  detail: Detail;
  onBack: () => void;
}

function outcomeColor(o: string) {
  if (o === 'PASS') return 'var(--pass)';
  if (o === 'FAIL') return 'var(--fail)';
  if (o === 'REVIEW') return 'var(--review)';
  return 'var(--unknown)';
}

export function InspectionDetail({ detail, onBack }: Props) {
  const outcome = detail.decision?.outcome ?? 'UNKNOWN';
  const color = outcomeColor(outcome);

  const laserData = detail.laser_result?.profile_data?.length
    ? detail.laser_result.profile_data.map((p: any, i: number) => ({ col: p.x ?? i, height: p.height }))
    : ((detail.laser_result as any)?.height_map?.values
      ?.map((v: any, i: number) => ({ col: i, height: v ?? 0 }))
      .filter((_: any, i: number) => i % 4 === 0) ?? []);

  const eddyData = detail.eddy_result?.simulated_readings?.map(r => ({
    name: `C${r.coil_index}`,
    deviation: r.deviation_pct,
    impedance: r.impedance,
  })) ?? [];

  return (
    <div className={styles.root}>
      <div className={styles.topBar}>
        <button className={styles.backBtn} onClick={onBack}>← Back</button>
        <div className={styles.idLabel}>Inspection <code>{detail.id}</code></div>
        <span className={styles.outcome} style={{ background: `${color}22`, color }}>
          {outcome}
        </span>
      </div>

      {detail.decision?.reason && (
        <div className={styles.reasonBox}>
          <strong>Decision Reason:</strong> {detail.decision.reason}
        </div>
      )}

      <div className={styles.grid}>
        {/* CV Result */}
        <div className={styles.card}>
          <h3 className={styles.cardTitle}>🔬 Computer Vision</h3>
          {detail.cv_result ? (
            <>
              <div className={styles.kv}>
                <span>Component Type</span>
                <strong>{detail.cv_result.component_type}</strong>
              </div>
              {Object.entries(detail.cv_result.dimensions ?? {}).map(([k, v]) => {
                if (typeof v === 'object' && v !== null) return null;
                return (
                  <div className={styles.kv} key={k}>
                    <span>{k.replace(/_/g, ' ')}</span>
                    <strong>{typeof v === 'number' ? `${v} mm` : String(v)}</strong>
                  </div>
                );
              })}
              <div className={styles.defects}>
                {detail.cv_result.defects?.length === 0 ? (
                  <span className={styles.ok}>✓ No defects detected</span>
                ) : (
                  detail.cv_result.defects?.map((d, i) => (
                    <span key={i} className={styles.defectBadge}>{d}</span>
                  ))
                )}
              </div>
            </>
          ) : <p className={styles.muted}>No CV data</p>}
        </div>

        {/* Laser Result */}
        <div className={styles.card}>
          <h3 className={styles.cardTitle}>📡 Laser Profile</h3>
          {detail.laser_result ? (
            <>
              {detail.laser_result.anomalies?.length === 0 ? (
                <span className={styles.ok}>✓ No anomalies</span>
              ) : (
                <div className={styles.defects}>
                  {detail.laser_result.anomalies?.map((a, i) => (
                    <span key={i} className={styles.defectBadge}>{a}</span>
                  ))}
                </div>
              )}
              {laserData.length > 0 && (
                <div className={styles.chartWrap}>
                  <ResponsiveContainer width="100%" height={160}>
                    <LineChart data={laserData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis dataKey="col" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} />
                      <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} />
                      <Tooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)' }} />
                      <Line type="monotone" dataKey="height" stroke="var(--accent)" dot={false} strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
          ) : <p className={styles.muted}>No laser data</p>}
        </div>

        {/* Eddy Result */}
        <div className={styles.card}>
          <h3 className={styles.cardTitle}>⚡ Eddy Current Array</h3>
          {detail.eddy_result ? (
            <>
              {detail.eddy_result.anomalies?.length === 0 ? (
                <span className={styles.ok}>✓ No anomalies</span>
              ) : (
                <div className={styles.defects}>
                  {detail.eddy_result.anomalies?.map((a, i) => (
                    <span key={i} className={styles.defectBadge}>{a}</span>
                  ))}
                </div>
              )}
              {eddyData.length > 0 && (
                <div className={styles.chartWrap}>
                  <ResponsiveContainer width="100%" height={200}>
                    <RadarChart data={eddyData}>
                      <PolarGrid stroke="var(--border)" />
                      <PolarAngleAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} />
                      <PolarRadiusAxis tick={{ fill: 'var(--text-muted)', fontSize: 9 }} />
                      <Radar name="Deviation %" dataKey="deviation" stroke="var(--accent)" fill="var(--accent)" fillOpacity={0.3} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
          ) : <p className={styles.muted}>No eddy data</p>}
        </div>
      </div>
    </div>
  );
}

