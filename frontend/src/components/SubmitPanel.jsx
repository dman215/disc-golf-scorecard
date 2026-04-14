const styles = {
  submitBtn: {
    background: 'var(--green)',
    color: '#fff',
    border: 'none',
    borderRadius: 8,
    padding: '13px 28px',
    fontSize: 16,
    fontWeight: 700,
    letterSpacing: '0.3px',
    cursor: 'pointer',
  },
  resetBtn: {
    background: 'none',
    border: '1.5px solid var(--border)',
    borderRadius: 8,
    padding: '12px 24px',
    fontSize: 14,
    color: 'var(--mid)',
    fontWeight: 500,
    cursor: 'pointer',
  },
  actions: { display: 'flex', gap: 12, marginTop: 20, alignItems: 'center', flexWrap: 'wrap' },
  overwriteToggle: { display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--muted)', marginLeft: 'auto', cursor: 'pointer' },
  error: {
    background: '#fff3f3',
    border: '1px solid #ffcdd2',
    borderRadius: 10,
    padding: 20,
    color: '#c62828',
    fontSize: 14,
  },
}

export default function SubmitPanel({
  onSubmit,
  onReset,
  overwrite,
  onOverwriteChange,
  error,
}) {
  return (
    <>
      <div style={styles.actions}>
        <button type="button" style={styles.submitBtn} onClick={onSubmit}>
          ✓ Write to Google Sheets
        </button>
        <button type="button" style={styles.resetBtn} onClick={onReset}>
          ← Start over
        </button>
        <label style={styles.overwriteToggle}>
          <input
            type="checkbox"
            checked={overwrite}
            onChange={e => onOverwriteChange(e.target.checked)}
          />
          Overwrite existing rows
        </label>
      </div>

      {error && (
        <div style={{ ...styles.error, marginTop: 16 }}>❌ {error}</div>
      )}
    </>
  )
}
