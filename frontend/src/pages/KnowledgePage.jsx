import { useState, useEffect } from 'react';
import { api } from '../api/client';
import JsonEditorModal from '../components/JsonEditorModal';

const TABS = [
  { key: 'machines',      label: '🏗️ Станки',         cols: ['machine_id','name','machine_type','machine_minute_cost_kzt','coolant_supported'] },
  { key: 'fixtures',      label: '🔩 Оснастка',        cols: ['fixture_id','name','fixture_type','setup_time_min','setup_cost_kzt'] },
  { key: 'setupMethods',  label: '🎯 Наладка',         cols: ['setup_method_id','name','time_min','cost_kzt','setup_error_mm'] },
  { key: 'tools',         label: '🔪 Инструмент',      cols: ['tool_id','name','tool_type','diameter_mm','tool_cost_kzt','tool_life_min'] },
];

const COL_LABELS = {
  machine_id: 'ID станка', name: 'Название', machine_type: 'Тип', machine_minute_cost_kzt: 'Стоим. ст.-мин, KZT',
  coolant_supported: 'Охлаждение', fixture_id: 'ID оснастки', fixture_type: 'Тип', setup_time_min: 'Время наладки, мин',
  setup_cost_kzt: 'Стоим. наладки, KZT', setup_method_id: 'ID метода', time_min: 'Время, мин', cost_kzt: 'Стоим., KZT',
  setup_error_mm: 'Погрешность, мм', tool_id: 'ID инструмента', tool_type: 'Тип', diameter_mm: 'Ø, мм',
  tool_cost_kzt: 'Цена, KZT', tool_life_min: 'Стойкость, мин',
};

function renderCell(val) {
  if (val === true)  return <span className="badge badge-green">Да</span>;
  if (val === false) return <span className="badge badge-gray">Нет</span>;
  if (typeof val === 'number') return <span className="mono">{val}</span>;
  return val ?? '—';
}

export default function KnowledgePage() {
  const [tab, setTab] = useState('machines');
  const [data, setData] = useState({});
  const [msg, setMsg]   = useState('');
  
  // Modal state
  const [editingItem, setEditingItem] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    loadTab(tab);
  }, [tab]);

  async function loadTab(t) {
    setMsg('');
    try {
      const rows = await api[t].list();
      setData(d => ({ ...d, [t]: rows }));
    } catch (e) {
      setMsg('⚠️ ' + e.message);
    }
  }

  const rows = data[tab] || [];
  const tabDef = TABS.find(t => t.key === tab);

  function getEmptyTemplate(tabKey) {
    if (tabKey === 'machines') return { machine_id: 'NEW_MACHINE', machine_type: 'milling', name: 'Новый станок', capabilities: [], workspace_mm: { x: 500, y: 500, z: 500 }, accuracy: { positioning_mm: 0.01, repeatability_mm: 0.005 }, machine_minute_cost_kzt: 100, coolant_supported: true };
    if (tabKey === 'fixtures') return { fixture_id: 'NEW_FIXTURE', fixture_type: 'vise', name: 'Новая оснастка', compatible_machines: [], setup_time_min: 5.0, setup_cost_kzt: 1000, basing_options: [] };
    if (tabKey === 'setupMethods') return { setup_method_id: 'NEW_METHOD', name: 'Новый метод привязки', time_min: 5.0, cost_kzt: 500, setup_error_mm: 0.05 };
    if (tabKey === 'tools') return { tool_id: 'NEW_TOOL', tool_type: 'end_mill', name: 'Новая фреза', diameter_mm: 10.0, flutes: 4, coating: 'TiAlN', tool_cost_kzt: 15000, tool_life_min: 120, compatible_material_groups: ['steel'], cutting_data: { V_m_min: {min: 50, max: 150}, f_mm_rev: {min: 0.05, max: 0.2}, ap_mm: {min: 0.5, max: 2.0} } };
    return {};
  }

  function handleAdd() {
    setEditingItem(getEmptyTemplate(tab));
  }

  function handleEdit(row) {
    setEditingItem(row);
  }

  async function handleDelete(idProp, id) {
    if (!window.confirm(`Вы уверены, что хотите удалить ${id}?`)) return;
    setIsDeleting(true);
    setMsg('');
    try {
      await api[tab].delete(id);
      loadTab(tab);
      setMsg(`✅ Запись ${id} удалена.`);
    } catch (e) {
      setMsg('❌ Ошибка удаления: ' + e.message);
    }
    setIsDeleting(false);
  }

  async function handleSaveJson(parsedJson) {
    setMsg('');
    try {
      await api[tab].save(parsedJson);
      setEditingItem(null);
      loadTab(tab);
      setMsg('✅ Данные успешно сохранены.');
    } catch (e) {
      setMsg('❌ Ошибка сохранения: ' + e.message);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>🗄️ База знаний</h1>
        <p>Парк оборудования, оснастка, методы наладки, режущий инструмент</p>
      </div>

      {msg && <div className="alert alert-warn">{msg}</div>}

      {/* Tab bar */}
      <div className="flex justify-between items-center" style={{ marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div className="flex gap-1" style={{ flexWrap: 'wrap' }}>
          {TABS.map(t => (
            <button
              key={t.key}
              onClick={() => { setTab(t.key); setMsg(''); }}
              className={`btn ${tab === t.key ? 'btn-primary' : 'btn-ghost'}`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <button className="btn btn-amber" onClick={handleAdd}>
          ➕ Добавить {tabDef.label.replace(/[^а-яА-Я\s]/g, '').trim()}
        </button>
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {tabDef.cols.map(c => (
                  <th key={c}>{COL_LABELS[c] || c}</th>
                ))}
                <th style={{ width: 120 }}>Действия</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr><td colSpan={tabDef.cols.length + 1} style={{ textAlign: 'center', color: 'var(--muted)', padding: '2rem' }}>
                  Нет данных
                </td></tr>
              ) : rows.map((row, i) => {
                const idProp = tabDef.cols[0]; // Convention: first col is always the ID
                const itemId = row[idProp];
                return (
                  <tr key={i}>
                    {tabDef.cols.map(c => (
                      <td key={c}>{renderCell(row[c])}</td>
                    ))}
                    <td>
                      <div className="flex gap-1">
                        <button className="btn btn-ghost" style={{ padding: '0.2rem 0.6rem', fontSize: '0.75rem' }} onClick={() => handleEdit(row)}>✏️</button>
                        <button className="btn btn-danger" style={{ padding: '0.2rem 0.6rem', fontSize: '0.75rem' }} onClick={() => handleDelete(idProp, itemId)} disabled={isDeleting}>🗑️</button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Expanded tool cutting data */}
      {tab === 'tools' && rows.length > 0 && (
        <div className="card" style={{ marginTop: '1rem' }}>
          <div className="card-title">Данные резания по инструменту</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px,1fr))', gap: '0.8rem' }}>
            {rows.map(t => (
              <div key={t.tool_id} style={{ background: 'var(--surface)', borderRadius: 8, padding: '0.8rem' }}>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>{t.name}</div>
                {t.cutting_data && Object.entries(t.cutting_data).map(([param, range]) => (
                  <div key={param} className="flex justify-between" style={{ fontSize: '0.8rem', marginBottom: 2 }}>
                    <span className="text-muted">{param}</span>
                    <span className="mono">{range.min}–{range.max}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Editor Modal */}
      {editingItem && (
        <JsonEditorModal
          title={`Редактирование: ${tabDef.label.replace(/[^а-яА-Я\s]/g, '').trim()}`}
          initialData={editingItem}
          onSave={handleSaveJson}
          onClose={() => setEditingItem(null)}
        />
      )}
    </div>
  );
}
