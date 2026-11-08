import { useEffect, useState } from 'react';
import styles from './LiveInspection.module.css';

interface Props {
  inspectionId: string;
  events: unknown[];
  onDone: () => void;
}

type Event = { type: string; data: string };

const STAGE_LABELS: Record<string, string> = {
  'feeding started': 'Stage 1: Feeding Started',
  'feeding completed': 'Stage 1: Feeding Completed',
  'cv started': 'Stage 2: CV Analysis Started',
  'cv completed': 'Stage 2: CV Analysis Complete',
  'laser started': 'Stage 2: Laser Profiling Started',
  'laser completed': 'Stage 2: Laser Profiling Complete',
  'eddy started': 'Stage 2: Eddy Current Started',
  'eddy completed': 'Stage 2: Eddy Current Complete',
  'decision engine': 'Decision Engine Running',
  'sorting started': 'Stage 3: Sorting Started',
  'sorting completed': 'Stage 3: Sorting Complete',
};

export function LiveInspection({ inspectionId, events, onDone }: Props) {
  const [done, setDone] = useState(false);
  const typedEvents = events as Event[];

  useEffect(() => {
    if (typedEvents.some(e => e.type === 'complete')) {
      setDone(true);
    }
  }, [typedEvents]);

  const decision = typedEvents.find(e => e.type === 'decision');
  const errorEvent = typedEvents.find(e => e.type === 'error');

  function outcomeColor(o: string) {
    if (o === 'PASS') return 'var(--pass)';
    if (o === 'FAIL') return 'var(--fail)';
    if (o === 'REVIEW') return 'var(--review)';
    return 'var(--unknown)';
  }

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <h2 className={styles.title}>🔄 Live Inspection</h2>
        <code className={styles.idBadge}>{inspectionId.slice(0, 8)}…</code>
      </div>

      {!done && !errorEvent && (
        <div className={styles.spinnerRow}>
          <div className={styles.spinner} />
          <span>Inspection in progress…</span>
        </div>
      )}

      {decision && (
        <div
          className={styles.resultBox}
          style={{ borderColor: outcomeColor(decision.data), background: `${outcomeColor(decision.data)}11` }}
        >
          <span className={styles.resultLabel}>Decision</span>
          <span className={styles.resultOutcome} style={{ color: outcomeColor(decision.data) }}>
            {decision.data}
          </span>
        </div>
      )}

      {errorEvent && (
        <div className={styles.errorBox}>
          ⚠ Error: {errorEvent.data}
        </div>
      )}

      <div className={styles.eventLog}>
        <h3 className={styles.logTitle}>Event Log</h3>
        <div className={styles.logInner}>
          {typedEvents.map((e, i) => (
            <div key={i} className={`${styles.logEntry} ${styles[`type_${e.type}`] ?? ''}`}>
              <span className={styles.logType}>{e.type}</span>
              <span className={styles.logData}>{STAGE_LABELS[e.data] ?? e.data}</span>
            </div>
          ))}
          {typedEvents.length === 0 && (
            <div className={styles.logEntry}><span className={styles.logData}>Waiting for events…</span></div>
          )}
        </div>
      </div>

      {done && (
        <button className={styles.doneBtn} onClick={onDone}>
          ✓ View Dashboard
        </button>
      )}
    </div>
  );
}

