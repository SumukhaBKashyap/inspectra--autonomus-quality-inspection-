import { InspectionSummary } from '../api';
import styles from './Dashboard.module.css';

interface Props {
  inspections: InspectionSummary[];
  onSelect: (id: string) => void;
  onRefresh: () => void;
}

function outcomeColor(outcome: string | null) {
  if (outcome === 'PASS') return 'var(--pass)';
  if (outcome === 'FAIL') return 'var(--fail)';
  if (outcome === 'REVIEW') return 'var(--review)';
  return 'var(--unknown)';
}

function outcomeIcon(outcome: string | null) {
  if (outcome === 'PASS') return '✓';
  if (outcome === 'FAIL') return '✗';
  if (outcome === 'REVIEW') return '⚑';
  return '?';
}

export function Dashboard({ inspections, onSelect, onRefresh }: Props) {
  const counts = {
    total: inspections.length,
    pass: inspections.filter(i => i.outcome === 'PASS').length,
    fail: inspections.filter(i => i.outcome === 'FAIL').length,
    review: inspections.filter(i => i.outcome === 'REVIEW').length,
  };

  return (
    <div className={styles.root}>
      <div className={styles.statsRow}>
        <StatCard label="Total Inspections" value={counts.total} color="var(--accent)" />
        <StatCard label="Pass" value={counts.pass} color="var(--pass)" />
        <StatCard label="Fail" value={counts.fail} color="var(--fail)" />
        <StatCard label="Review" value={counts.review} color="var(--review)" />
      </div>

      <div className={styles.tableCard}>
        <div className={styles.tableHeader}>
          <h2 className={styles.tableTitle}>Inspection History</h2>
          <button className={styles.refreshBtn} onClick={onRefresh}>⟳ Refresh</button>
        </div>
        {inspections.length === 0 ? (
          <div className={styles.empty}>
            <p>No inspections yet. Click <strong>▶ Start Inspection</strong> to begin.</p>
          </div>
        ) : (
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Time</th>
                  <th>Outcome</th>
                  <th>Reason</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {inspections.map(insp => (
                  <tr key={insp.id} className={styles.row}>
                    <td className={styles.idCell}>{insp.id.slice(0, 8)}…</td>
                    <td>{insp.created_at ? new Date(insp.created_at).toLocaleString() : '—'}</td>
                    <td>
                      <span
                        className={styles.badge}
                        style={{ background: `${outcomeColor(insp.outcome)}22`, color: outcomeColor(insp.outcome) }}
                      >
                        {outcomeIcon(insp.outcome)} {insp.outcome ?? 'Pending'}
                      </span>
                    </td>
                    <td className={styles.reasonCell}>{insp.reason ?? '—'}</td>
                    <td>
                      <button className={styles.viewBtn} onClick={() => onSelect(insp.id)}>
                        View →
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
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className={styles.statCard} style={{ borderColor: color }}>
      <div className={styles.statValue} style={{ color }}>{value}</div>
      <div className={styles.statLabel}>{label}</div>
    </div>
  );
}

