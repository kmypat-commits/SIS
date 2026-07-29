import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';

const OBJ_LABELS = {
  time_total_min:   'Трудоёмкость, мин',
  cost_total_min:   'Затраты, KZT',
  setup_error_min:  'Погрешность наладки, мм',
  quality_risk_min: 'Риск качества',
};
const OBJ_KEYS = Object.keys(OBJ_LABELS);

// ── SVG Pareto Scatter ────────────────────────────────────────────────────────
function ParetoChart({ pareto, selected, axisX, axisY }) {
  if (!pareto || pareto.length === 0) return null;
  const W = 480, H = 260, PAD = { l: 55, r: 20, t: 16, b: 50 };
  const plotW = W - PAD.l - PAD.r;
  const plotH = H - PAD.t - PAD.b;

  const xs = pareto.map(s => s.objectives[axisX]);
  const ys = pareto.map(s => s.objectives[axisY]);
  const xmin = Math.min(...xs), xmax = Math.max(...xs);
  const ymin = Math.min(...ys), ymax = Math.max(...ys);
  const xr = xmax - xmin || 1, yr = ymax - ymin || 1;

  function toSvg(sx, sy) {
    return {
      x: PAD.l + ((sx - xmin) / xr) * plotW,
      y: PAD.t + (1 - (sy - ymin) / yr) * plotH,
    };
  }

  // Draw Pareto line
  const sorted = [...pareto].sort((a, b) => a.objectives[axisX] - b.objectives[axisX]);
  const linePoints = sorted.map(s => {
    const { x, y } = toSvg(s.objectives[axisX], s.objectives[axisY]);
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', maxWidth: W, display: 'block' }}>
      {/* Grid lines */}
      {[0,0.25,0.5,0.75,1].map(t => {
        const y = PAD.t + (1 - t) * plotH;
        const val = ymin + t * yr;
        return (
          <g key={t}>
            <line x1={PAD.l} x2={W - PAD.r} y1={y} y2={y} stroke="var(--border)" strokeWidth="0.5" />
            <text x={PAD.l - 5} y={y + 4} fill="var(--muted)" fontSize="9" textAnchor="end">
              {val.toFixed(1)}
            </text>
          </g>
        );
      })}
      {[0,0.25,0.5,0.75,1].map(t => {
        const x = PAD.l + t * plotW;
        const val = xmin + t * xr;
        return (
          <g key={t}>
            <line x1={x} x2={x} y1={PAD.t} y2={PAD.t + plotH} stroke="var(--border)" strokeWidth="0.5" />
            <text x={x} y={PAD.t + plotH + 14} fill="var(--muted)" fontSize="9" textAnchor="middle">
              {val.toFixed(1)}
            </text>
          </g>
        );
      })}

      {/* Pareto front line */}
      <polyline points={linePoints} fill="none" stroke="var(--border-hi)" strokeWidth="1" strokeDasharray="4 3" />

      {/* Points */}
      {pareto.map(s => {
        const { x, y } = toSvg(s.objectives[axisX], s.objectives[axisY]);
        const isSel = selected && s.solution_id === selected.solution_id;
        return (
          <g key={s.solution_id}>
            <circle cx={x} cy={y} r={isSel ? 8 : 5}
              fill={isSel ? 'var(--amber)' : 'var(--blue-hi)'}
              stroke={isSel ? '#fff' : 'var(--navy)'}
              strokeWidth={isSel ? 2 : 1}
              opacity={isSel ? 1 : 0.8}
            >
              <title>{`t=${s.objectives.time_total_min.toFixed(1)} мин | c=${s.objectives.cost_total_min.toFixed(0)} KZT | err=${s.objectives.setup_error_min.toFixed(3)} | risk=${s.objectives.quality_risk_min.toFixed(3)}`}</title>
            </circle>
          </g>
        );
      })}

      {/* Axis labels */}
      <text x={W / 2} y={H - 4} fill="var(--muted-hi)" fontSize="10" textAnchor="middle">{OBJ_LABELS[axisX]}</text>
      <text x={12} y={H / 2} fill="var(--muted-hi)" fontSize="10" textAnchor="middle"
        transform={`rotate(-90,12,${H/2})`}>{OBJ_LABELS[axisY]}</text>
    </svg>
  );
}

// ── Main Optimize Page ────────────────────────────────────────────────────────
export default function OptimizePage() {
  const [projects, setProjects]     = useState([]);
  const [projectId, setProjectId]   = useState('');
  const [running, setRunning]       = useState(false);
  const [progress, setProgress]     = useState(0);
  const [pareto, setPareto]         = useState([]);
  const [selected, setSelected]     = useState(null);
  const [msg, setMsg]               = useState('');
  const [axisX, setAxisX]           = useState('time_total_min');
  const [axisY, setAxisY]           = useState('cost_total_min');
  const [strategy, setStrategy]     = useState('min_criterion');
  const [stratObj, setStratObj]     = useState('time_total_min');
  const [weights, setWeights]       = useState({ time_total_min: 0.4, cost_total_min: 0.3, setup_error_min: 0.15, quality_risk_min: 0.15 });
  const timerRef = useRef(null);

  useEffect(() => {
    api.projects.list().then(list => {
      setProjects(list);
      if (list.length) setProjectId(list[0].project_id);
    }).catch(() => {});
    return () => clearInterval(timerRef.current);
  }, []);

  async function runOptimize() {
    if (!projectId) { setMsg('⚠️ Выберите проект'); return; }
    setRunning(true);
    setProgress(0);
    setPareto([]);
    setSelected(null);
    setMsg('');

    // Animate progress (fake, since backend returns synchronously)
    timerRef.current = setInterval(() => {
      setProgress(p => (p < 90 ? p + Math.random() * 8 : p));
    }, 300);

    try {
      const res = await api.optimize.run(projectId);
      clearInterval(timerRef.current);
      setProgress(100);
      setPareto(res.pareto || []);
      setMsg(`✅ Найдено ${res.pareto_count} Парето-оптимальных решений`);
    } catch (e) {
      clearInterval(timerRef.current);
      setMsg('❌ ' + e.message);
    }
    setTimeout(() => setRunning(false), 400);
  }

  async function selectSolution(sol) {
    setSelected(sol);
    // Persist selection
    await api.optimize.select(projectId, {
      strategy: 'min_criterion',
      objective_id: 'time_total_min',
    }).catch(() => {});
  }

  async function applyStrategy() {
    if (!pareto.length) return;
    const payload = { strategy };
    if (strategy === 'min_criterion') payload.objective_id = stratObj;
    if (strategy === 'weighted_sum')  payload.weights = weights;
    try {
      const sol = await api.optimize.select(projectId, payload);
      const found = pareto.find(s => s.solution_id === sol.solution_id);
      if (found) setSelected(found);
    } catch (e) { setMsg('❌ ' + e.message); }
  }

  async function exportResult() {
    try {
      const data = await api.optimize.export(projectId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href = url; a.download = `solution_${projectId}.json`; a.click();
    } catch (e) { setMsg('❌ ' + e.message); }
  }

  function openReport() {
    window.open(api.report.url(projectId), '_blank');
  }

  return (
    <div>
      <div className="page-header">
        <h1>🚀 Оптимизация</h1>
        <p>Многокритериальная оптимизация (Парето) технологического процесса</p>
      </div>

      {msg && <div className={`alert ${msg.startsWith('✅') ? 'alert-success' : msg.startsWith('⚠') ? 'alert-warn' : 'alert-warn'}`}>{msg}</div>}

      {/* Controls */}
      <div className="card">
        <div className="flex items-center gap-2" style={{ flexWrap: 'wrap' }}>
          <div className="form-field" style={{ minWidth: 280 }}>
            <label>Проект</label>
            <select className="select" value={projectId} onChange={e => setProjectId(e.target.value)}>
              {projects.map(p => <option key={p.project_id} value={p.project_id}>{p.name}</option>)}
            </select>
          </div>
          <div style={{ alignSelf: 'flex-end' }}>
            <button className="btn btn-primary" onClick={runOptimize} disabled={running}>
              {running ? <><span className="spinner" /> Расчёт…</> : '▶ Рассчитать'}
            </button>
          </div>
        </div>

        {/* Progress */}
        {running && (
          <div style={{ marginTop: '1rem' }}>
            <div className="text-muted text-small" style={{ marginBottom: 4 }}>
              Генерация вариантов и построение Парето-фронта…
            </div>
            <div className="progress-wrap">
              <div className="progress-bar" style={{ width: `${progress}%` }} />
            </div>
          </div>
        )}
      </div>

      {pareto.length > 0 && (
        <>
          {/* Objectives summary */}
          <div className="metrics-grid">
            {(['time_total_min','cost_total_min','setup_error_min','quality_risk_min']).map(k => {
              const vals = pareto.map(s => s.objectives[k]);
              const mn = Math.min(...vals), mx = Math.max(...vals);
              return (
                <div className="metric-card" key={k}>
                  <div className="metric-label">{OBJ_LABELS[k]}</div>
                  <div className="metric-value">{mn.toFixed(2)}<span className="metric-unit">–{mx.toFixed(2)}</span></div>
                  <div className="text-muted text-small" style={{ marginTop: 2 }}>мин–макс по фронту</div>
                </div>
              );
            })}
          </div>

          {/* Chart + strategy */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '1.2rem', marginBottom: '1.2rem' }}>
            {/* Scatter */}
            <div className="card">
              <div className="flex justify-between items-center" style={{ marginBottom: '0.8rem' }}>
                <div className="card-title" style={{ margin: 0 }}>Парето-фронт ({pareto.length} точек)</div>
                <div className="flex gap-1">
                  <select className="select" style={{ width: 160 }} value={axisX} onChange={e => setAxisX(e.target.value)}>
                    {OBJ_KEYS.map(k => <option key={k} value={k}>{OBJ_LABELS[k]}</option>)}
                  </select>
                  <select className="select" style={{ width: 160 }} value={axisY} onChange={e => setAxisY(e.target.value)}>
                    {OBJ_KEYS.filter(k => k !== axisX).map(k => <option key={k} value={k}>{OBJ_LABELS[k]}</option>)}
                  </select>
                </div>
              </div>
              <ParetoChart pareto={pareto} selected={selected} axisX={axisX} axisY={axisY} />
              <div className="text-muted text-small" style={{ marginTop: 6, textAlign: 'center' }}>
                🟡 — выбранное решение &nbsp;|&nbsp; 🔵 — Парето-фронт
              </div>
            </div>

            {/* Strategy selector */}
            <div className="card">
              <div className="card-title">Стратегия выбора</div>
              <div className="form-field" style={{ marginBottom: '0.8rem' }}>
                <label>Метод</label>
                <select className="select" value={strategy} onChange={e => setStrategy(e.target.value)}>
                  <option value="min_criterion">Минимум критерия</option>
                  <option value="weighted_sum">Взвешенная свёртка</option>
                  <option value="constraint_then_first">Ограничение + 1-е</option>
                </select>
              </div>

              {strategy === 'min_criterion' && (
                <div className="form-field" style={{ marginBottom: '0.8rem' }}>
                  <label>Критерий</label>
                  <select className="select" value={stratObj} onChange={e => setStratObj(e.target.value)}>
                    {OBJ_KEYS.map(k => <option key={k} value={k}>{OBJ_LABELS[k]}</option>)}
                  </select>
                </div>
              )}

              {strategy === 'weighted_sum' && (
                <div style={{ marginBottom: '0.8rem' }}>
                  {OBJ_KEYS.map(k => (
                    <div key={k} className="form-field" style={{ marginBottom: 6 }}>
                      <label>{OBJ_LABELS[k]}: {weights[k].toFixed(2)}</label>
                      <input type="range" min="0" max="1" step="0.05" value={weights[k]}
                        onChange={e => setWeights(w => ({ ...w, [k]: +e.target.value }))}
                        style={{ width: '100%', accentColor: 'var(--blue-hi)' }} />
                    </div>
                  ))}
                </div>
              )}

              <button className="btn btn-amber w-full" onClick={applyStrategy}>
                Применить стратегию
              </button>

              {selected && (
                <div className="alert alert-success" style={{ marginTop: '0.8rem', fontSize: '0.8rem' }}>
                  Выбрано: {selected.solution_id.substring(0, 8)}…<br />
                  t={selected.objectives.time_total_min.toFixed(2)} мин &nbsp;|&nbsp;
                  c={selected.objectives.cost_total_min.toFixed(0)} KZT
                </div>
              )}

              <div className="flex flex-col gap-1" style={{ marginTop: '0.8rem' }}>
                <button className="btn btn-ghost w-full" onClick={exportResult} disabled={!selected}>
                  📥 Экспорт JSON
                </button>
                <button className="btn btn-ghost w-full" onClick={openReport} disabled={!pareto.length}>
                  📄 Отчёт HTML
                </button>
              </div>
            </div>
          </div>

          {/* Pareto table */}
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '1rem 1.4rem', borderBottom: '1px solid var(--border)' }}>
              <div className="card-title" style={{ margin: 0 }}>Все решения Парето-фронта</div>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Трудоёмкость, мин</th>
                    <th>Затраты, KZT</th>
                    <th>Погр. наладки, мм</th>
                    <th>Риск качества</th>
                    <th>Операций</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {pareto.map((sol, i) => (
                    <tr key={sol.solution_id}
                      className={selected?.solution_id === sol.solution_id ? 'selected-row' : ''}
                      onClick={() => selectSolution(sol)}
                      style={{ cursor: 'pointer' }}
                    >
                      <td><span className="badge badge-gray">{i+1}</span></td>
                      <td><span className="mono">{sol.objectives.time_total_min.toFixed(2)}</span></td>
                      <td><span className="mono">{sol.objectives.cost_total_min.toFixed(0)}</span></td>
                      <td><span className="mono">{sol.objectives.setup_error_min.toFixed(4)}</span></td>
                      <td><span className="mono">{sol.objectives.quality_risk_min.toFixed(4)}</span></td>
                      <td>{sol.operations?.length || '—'}</td>
                      <td>
                        {selected?.solution_id === sol.solution_id
                          ? <span className="badge badge-amber">✓ Выбрано</span>
                          : <button className="btn btn-ghost" style={{ padding: '0.25rem 0.6rem', fontSize: '0.78rem' }}
                              onClick={e => { e.stopPropagation(); selectSolution(sol); }}>
                              Выбрать
                            </button>
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Selected solution detail */}
          {selected && (
            <div className="card" style={{ marginTop: '1.2rem' }}>
              <div className="card-title">Маршрут выбранного решения</div>
              {selected.operations?.map((op, i) => (
                <div key={op.operation_id} style={{
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                  marginBottom: 8,
                  overflow: 'hidden',
                }}>
                  <div style={{ padding: '0.65rem 1rem', background: 'var(--surface)', display: 'flex', gap: '0.8rem', flexWrap: 'wrap', alignItems: 'center' }}>
                    <span className="badge badge-blue">{i + 1}</span>
                    <strong>{op.name}</strong>
                    <span className="badge badge-gray">{op.machine_id}</span>
                    <span className="text-muted text-small">Оснастка: {op.fixture_id}</span>
                    <span className="text-muted text-small">Наладка: {op.setup_method_id}</span>
                    <span className="text-muted text-small">t_нал={op.setup_time_min.toFixed(1)} мин</span>
                    <span className="text-muted text-small">err={op.setup_error_mm.toFixed(3)} мм</span>
                  </div>
                  {op.transitions?.map(tr => (
                    <div key={tr.transition_id} style={{ padding: '0.55rem 1.2rem 0.55rem 2.5rem', borderTop: '1px solid var(--border)', display: 'flex', gap: '1.2rem', flexWrap: 'wrap', alignItems: 'center' }}>
                      <span className="text-muted">↳</span>
                      <span className="badge badge-gray">{tr.method}</span>
                      <span className="text-small">{tr.tool_id}</span>
                      <span className="mono text-small">V={tr.V}</span>
                      <span className="mono text-small">f={tr.f}</span>
                      <span className="mono text-small">ap={tr.ap}</span>
                      <span className="mono text-small">t={tr.basic_time_min.toFixed(2)} мин</span>
                      <span className="mono text-small">Ra={tr.achieved_ra_um} мкм</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
