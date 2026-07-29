import { useState, useEffect } from 'react';

export default function JsonEditorModal({ title, initialData, onSave, onClose, isCde = false }) {
  const [jsonText, setJsonText] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    setJsonText(JSON.stringify(initialData || {}, null, 2));
  }, [initialData]);

  function handleSave() {
    try {
      const parsed = JSON.parse(jsonText);
      onSave(parsed);
    } catch (e) {
      setError('Ошибка парсинга JSON: ' + e.message);
    }
  }

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.6)', zIndex: 9999,
      display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div className="card" style={{ width: 600, maxWidth: '90vw', maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}>
        <h2 style={{ marginBottom: '1rem' }}>{title}</h2>
        
        {error && <div className="alert alert-danger" style={{ color: 'var(--red)', background: 'rgba(239,68,68,0.1)' }}>{error}</div>}
        
        <p style={{ color: 'var(--muted)', fontSize: '0.8rem', marginBottom: '0.5rem' }}>
          Отредактируйте данные сущности в формате JSON:
        </p>
        
        <textarea
          className="input"
          style={{ flex: 1, minHeight: 400, fontFamily: 'monospace', whiteSpace: 'pre', fontSize: '0.9rem' }}
          value={jsonText}
          onChange={(e) => { setJsonText(e.target.value); setError(''); }}
          spellCheck={false}
        />
        
        <div style={{ display: 'flex', gap: '1rem', marginTop: '1.2rem', justifyContent: 'flex-end' }}>
          <button className="btn btn-ghost" onClick={onClose}>Отмена</button>
          <button className="btn btn-primary" onClick={handleSave}>💾 Сохранить</button>
        </div>
      </div>
    </div>
  );
}
