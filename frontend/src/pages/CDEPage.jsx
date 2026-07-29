import { useState, useEffect } from 'react';
import { api } from '../api/client';
import JsonEditorModal from '../components/JsonEditorModal';

const CDE_TYPES = ['plane', 'hole_group', 'pocket', 'thread', 'chamfer', 'bore'];

export default function CDEPage() {
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState('');
  const [projectDet, setProjectDet] = useState(null);
  const [cdeList, setCdeList] = useState([]);
  const [expanded, setExpanded] = useState(null);
  
  const [editingCde, setEditingCde] = useState(null);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    api.projects.list().then(setProjects).catch(() => {});
  }, []);

  async function loadCDE(pid) {
    setProjectId(pid);
    setExpanded(null);
    setMsg('');
    if (!pid) {
      setCdeList([]);
      setProjectDet(null);
      return;
    }
    try {
      const d = await api.projects.get(pid);
      setProjectDet(d);
      setCdeList(d.product?.cde_list || []);
    } catch (e) { 
      setCdeList([]); 
      setProjectDet(null);
      setMsg('❌ Ошибка загрузки проекта: ' + e.message);
    }
  }

  function handleAdd() {
    setEditingCde({
      cde_id: `CDE_NEW_${Date.now().toString().slice(-4)}`,
      type: 'plane',
      name: 'Новый элемент',
      geometry: {},
      requirements: {},
      allowed_methods: []
    });
  }

  function handleEdit(cde) {
    setEditingCde(cde);
  }

  async function handleDelete(cdeId) {
    if (!window.confirm(`Вы уверены, что хотите удалить ${cdeId}?`)) return;
    const newList = cdeList.filter(c => c.cde_id !== cdeId);
    await saveCdeList(newList, `Элемент ${cdeId} удалён.`);
  }

  async function handleSaveCde(parsedCde) {
    let newList = [...cdeList];
    const idx = newList.findIndex(c => c.cde_id === parsedCde.cde_id);
    if (idx >= 0) {
      newList[idx] = parsedCde;
    } else {
      newList.push(parsedCde);
    }
    await saveCdeList(newList, '✅ Элемент успешно сохранён.');
    setEditingCde(null);
  }

  async function saveCdeList(newList, successMsg) {
    if (!projectDet) return;
    setMsg('');
    try {
      const payload = {
        project: {
          project_id:      projectDet.project_id,
          name:            projectDet.name,
          currency:        projectDet.currency,
          production_type: projectDet.production_type,
          batch_size:      projectDet.batch_size,
          material: {
            name:        projectDet.material_name,
            group:       projectDet.material_group,
            hardness_hb: projectDet.hardness_hb,
          },
        },
        product:          { ...(projectDet.product || {}), cde_list: newList },
        strategy:         projectDet.strategy,
        resources:        projectDet.resources,
        process_templates: projectDet.process_templates,
        costs:            projectDet.costs,
        quality_models:   projectDet.quality_models,
      };
      
      await api.projects.save(payload);
      setCdeList(newList);
      setMsg(successMsg);
    } catch (e) {
      setMsg('❌ Ошибка сохранения: ' + e.message);
    }
  }

  const typeColors = {
    plane: 'badge-blue', hole_group: 'badge-green', pocket: 'badge-amber',
    thread: 'badge-gray', chamfer: 'badge-gray', bore: 'badge-blue',
  };

  return (
    <div>
      <div className="page-header">
        <h1>📐 Элементы конструкции (CDE)</h1>
        <p>Конструкторские элементы изделия: плоскости, отверстия, карманы, резьбы</p>
      </div>

      <div className="card">
        <div className="card-title">Выбор проекта</div>
        <select className="select" style={{ maxWidth: 340, marginBottom: '1rem' }} value={projectId}
          onChange={e => loadCDE(e.target.value)}>
          <option value="">— выберите проект —</option>
          {projects.map(p => (
            <option key={p.project_id} value={p.project_id}>{p.name} ({p.project_id})</option>
          ))}
        </select>
        {msg && <div className={`alert ${msg.startsWith('✅') ? 'alert-success' : 'alert-warn'}`} style={{ marginTop: '0.5rem' }}>{msg}</div>}
      </div>

      {projectId && (
        <div className="card">
          <div className="flex justify-between items-center" style={{ marginBottom: '1rem' }}>
            <div className="card-title" style={{ margin: 0 }}>Элементы ({cdeList.length})</div>
            <button className="btn btn-amber" onClick={handleAdd}>➕ Добавить CDE</button>
          </div>

          {cdeList.map((cde, i) => (
            <div key={cde.cde_id} style={{
              border: '1px solid var(--border)',
              borderRadius: 10,
              marginBottom: 8,
              overflow: 'hidden',
            }}>
              {/* Header */}
              <div
                className="flex items-center justify-between"
                style={{
                  padding: '0.7rem 1rem',
                  cursor: 'pointer',
                  background: expanded === i ? 'var(--surface)' : 'transparent',
                  userSelect: 'none',
                }}
                onClick={() => setExpanded(expanded === i ? null : i)}
              >
                <div className="flex items-center gap-2">
                  <span style={{ color: 'var(--muted)', fontSize: '1.2rem', paddingRight: '0.4rem', pointerEvents: 'none' }}>
                    {expanded === i ? '▲' : '▼'}
                  </span>
                  <span className={`badge ${typeColors[cde.type] || 'badge-gray'}`}>{cde.type}</span>
                  <strong style={{ fontSize: '0.925rem' }}>{cde.name}</strong>
                  <span style={{ color: 'var(--muted)', fontSize: '0.78rem' }}>#{cde.cde_id}</span>
                </div>
                
                <div className="flex gap-1" onClick={e => e.stopPropagation()}>
                  <button className="btn btn-ghost" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }} onClick={() => handleEdit(cde)}>✏️</button>
                  <button className="btn btn-danger" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }} onClick={() => handleDelete(cde.cde_id)}>🗑️</button>
                </div>
              </div>

              {/* Expanded detail */}
              {expanded === i && (
                <div style={{ padding: '0.8rem 1.2rem', background: 'var(--navy-card)', borderTop: '1px solid var(--border)' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.2rem' }}>
                    <div>
                      <div className="card-title">Геометрия</div>
                      {Object.entries(cde.geometry || {}).map(([k, v]) => (
                        <div key={k} className="flex justify-between" style={{ marginBottom: 4, fontSize: '0.85rem' }}>
                          <span className="text-muted">{k}</span>
                          <span className="mono">{typeof v === 'object' ? JSON.stringify(v) : v}</span>
                        </div>
                      ))}
                    </div>
                    <div>
                      <div className="card-title">Требования</div>
                      {Object.entries(cde.requirements || {}).map(([k, v]) => (
                        <div key={k} className="flex justify-between" style={{ marginBottom: 4, fontSize: '0.85rem' }}>
                          <span className="text-muted">{k}</span>
                          <span className="mono">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div style={{ marginTop: '0.8rem' }}>
                    <div className="card-title">Допустимые методы обработки</div>
                    <div className="flex gap-1" style={{ flexWrap: 'wrap' }}>
                      {(cde.allowed_methods || []).map(m => (
                        <span key={m} className="badge badge-blue">{m}</span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {projectId && cdeList.length === 0 && (
        <div className="alert alert-info">Нет данных CDE для этого проекта. Добавьте элементы вручную.</div>
      )}

      {/* Editor Modal */}
      {editingCde && (
        <JsonEditorModal
          title={`Редактирование: CDE`}
          initialData={editingCde}
          onSave={handleSaveCde}
          onClose={() => setEditingCde(null)}
          isCde={true}
        />
      )}
    </div>
  );
}
