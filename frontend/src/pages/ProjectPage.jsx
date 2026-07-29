import { useState, useEffect } from 'react';
import { api } from '../api/client';

const DEFAULT_PROJECT = {
  project_id: 'machopt_mvp_0001',
  name: 'Корпус - MVP',
  currency: 'KZT',
  production_type: 'serial',
  batch_size: 200,
  material: { name: 'Steel 45', group: 'steel', hardness_hb: 200 },
};

export default function ProjectPage() {
  const [projects, setProjects]   = useState([]);
  const [selected, setSelected]   = useState(null);
  const [detail, setDetail]       = useState(null);
  const [loading, setLoading]     = useState(false);
  const [msg, setMsg]             = useState('');
  const [form, setForm]           = useState({ ...DEFAULT_PROJECT });

  useEffect(() => { loadProjects(); }, []);

  async function loadProjects() {
    try {
      const list = await api.projects.list();
      setProjects(list);
      if (list.length > 0 && !selected) {
        selectProject(list[0].project_id);
      }
    } catch (e) {
      setMsg('⚠️ Нет соединения с backend. Убедитесь, что сервер запущен на порту 8000.');
    }
  }

  async function selectProject(id) {
    setSelected(id);
    try {
      const d = await api.projects.get(id);
      setDetail(d);
      const p = d;
      setForm({
        project_id:      p.project_id || DEFAULT_PROJECT.project_id,
        name:            p.name || DEFAULT_PROJECT.name,
        currency:        p.currency || DEFAULT_PROJECT.currency,
        production_type: p.production_type || DEFAULT_PROJECT.production_type,
        batch_size:      p.batch_size || DEFAULT_PROJECT.batch_size,
        material_name:   p.material_name || DEFAULT_PROJECT.material.name,
        material_group:  p.material_group || DEFAULT_PROJECT.material.group,
        hardness_hb:     p.hardness_hb || DEFAULT_PROJECT.material.hardness_hb,
      });
    } catch (e) { /* ignore */ }
  }

  async function saveProject() {
    setLoading(true);
    setMsg('');
    try {
      const payload = {
        project: {
          project_id:      form.project_id,
          name:            form.name,
          currency:        form.currency,
          production_type: form.production_type,
          batch_size:      Number(form.batch_size),
          material: {
            name:        form.material_name,
            group:       form.material_group,
            hardness_hb: Number(form.hardness_hb),
          },
        },
        // Keep existing sub-documents from detail
        product:          detail?.product,
        strategy:         detail?.strategy,
        resources:        detail?.resources,
        process_templates: detail?.process_templates,
        costs:            detail?.costs,
        quality_models:   detail?.quality_models,
      };
      console.log("Saving payload", payload);
      await api.projects.save(payload);
      setMsg('✅ Проект сохранён');
      await loadProjects();
    } catch (e) {
      console.error("Save error:", e);
      setMsg('❌ Ошибка сохранения: ' + e.message); 
    } finally {
      setLoading(false);
    }
  }

  function set(key) { return (e) => setForm(f => ({ ...f, [key]: e.target.value })); }

  const strategy = detail?.strategy || {};
  const solver   = strategy.solver || {};
  const constr   = strategy.constraints || {};
  const objs     = strategy.objectives || [];

  return (
    <div>
      <div className="page-header">
        <h1>🏭 Проект</h1>
        <p>Описание изделия, стратегия оптимизации и параметры расчёта</p>
      </div>

      {msg && <div className={`alert ${msg.startsWith('✅') ? 'alert-success' : 'alert-warn'}`}>{msg}</div>}

      <div style={{ display: 'flex', gap: '1.2rem', alignItems: 'flex-start' }}>
        {/* Project list */}
        <div style={{ width: 200, flexShrink: 0 }}>
          <div className="card-title">Проекты</div>
          {projects.map(p => (
            <div
              key={p.project_id}
              onClick={() => selectProject(p.project_id)}
              style={{
                padding: '0.6rem 0.9rem',
                borderRadius: 8,
                cursor: 'pointer',
                background: selected === p.project_id ? 'var(--blue-glow)' : 'var(--navy-card)',
                border: `1px solid ${selected === p.project_id ? 'var(--border-hi)' : 'var(--border)'}`,
                color: selected === p.project_id ? 'var(--blue-hi)' : 'var(--text)',
                marginBottom: 6,
                fontSize: '0.875rem',
                fontWeight: 500,
              }}
            >
              {p.name}
              <div style={{ fontSize: '0.72rem', color: 'var(--muted)', marginTop: 2 }}>{p.project_id}</div>
            </div>
          ))}
        </div>

        {/* Edit form */}
        <div style={{ flex: 1 }}>
          <div className="card">
            <div className="card-title">Общие сведения</div>
            <div className="form-row">
              <div className="form-field">
                <label>ID проекта</label>
                <input className="input" value={form.project_id} onChange={set('project_id')} />
              </div>
              <div className="form-field">
                <label>Название</label>
                <input className="input" value={form.name} onChange={set('name')} />
              </div>
              <div className="form-field">
                <label>Тип производства</label>
                <select className="select" value={form.production_type} onChange={set('production_type')}>
                  <option value="single">Единичное</option>
                  <option value="serial">Серийное</option>
                  <option value="mass">Массовое</option>
                </select>
              </div>
              <div className="form-field">
                <label>Объём партии</label>
                <input className="input" type="number" value={form.batch_size} onChange={set('batch_size')} />
              </div>
              <div className="form-field">
                <label>Валюта</label>
                <input className="input" value={form.currency} onChange={set('currency')} />
              </div>
            </div>

            <div className="card-title" style={{ marginTop: '1.2rem' }}>Материал</div>
            <div className="form-row">
              <div className="form-field">
                <label>Материал</label>
                <input className="input" value={form.material_name} onChange={set('material_name')} />
              </div>
              <div className="form-field">
                <label>Группа</label>
                <select className="select" value={form.material_group} onChange={set('material_group')}>
                  <option value="steel">Сталь</option>
                  <option value="cast_iron">Чугун</option>
                  <option value="aluminum">Алюминий</option>
                  <option value="titanium">Титан</option>
                </select>
              </div>
              <div className="form-field">
                <label>Твёрдость, HB</label>
                <input className="input" type="number" value={form.hardness_hb} onChange={set('hardness_hb')} />
              </div>
            </div>

            <button className="btn btn-primary" onClick={saveProject} disabled={loading} style={{ marginTop: '0.8rem' }}>
              {loading ? <><span className="spinner" />&nbsp;Сохранение…</> : '💾 Сохранить проект'}
            </button>
          </div>

          {detail && (
            <div className="card">
              <div className="card-title">Стратегия оптимизации (из конфигурации)</div>
              <div className="form-row">
                <div className="form-field">
                  <label>Метод</label>
                  <input className="input" readOnly value={solver.method || '—'} />
                </div>
                <div className="form-field">
                  <label>Популяция</label>
                  <input className="input" readOnly value={solver.population_size || '—'} />
                </div>
                <div className="form-field">
                  <label>Поколений</label>
                  <input className="input" readOnly value={solver.generations || '—'} />
                </div>
                <div className="form-field">
                  <label>Seed</label>
                  <input className="input" readOnly value={solver.seed ?? '—'} />
                </div>
                <div className="form-field">
                  <label>Макс. операций</label>
                  <input className="input" readOnly value={constr.max_operations || '—'} />
                </div>
              </div>

              <div className="card-title" style={{ marginTop: '1rem' }}>Критерии оптимизации</div>
              <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
                {objs.map(o => (
                  <span key={o.id} className="badge badge-blue">{o.id} ({o.type})</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
