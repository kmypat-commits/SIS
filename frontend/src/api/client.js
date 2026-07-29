// API client – wrappers around all backend endpoints
const BASE = 'http://localhost:8000';

async function req(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(BASE + path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

// ── Projects ─────────────────────────────────────────────
export const api = {
  projects: {
    list:   ()   => req('GET',  '/api/projects/'),
    get:    (id) => req('GET',  `/api/projects/${id}`),
    save:   (data) => req('POST', '/api/projects/', data),
    delete: (id) => req('DELETE', `/api/projects/${id}`),
  },

  // ── Knowledge base ──────────────────────────────────────
  machines: {
    list:   ()     => req('GET',    '/api/knowledge/machines'),
    save:   (data) => req('POST',   '/api/knowledge/machines', data),
    delete: (id)   => req('DELETE', `/api/knowledge/machines/${id}`),
  },
  fixtures: {
    list:   ()     => req('GET',    '/api/knowledge/fixtures'),
    save:   (data) => req('POST',   '/api/knowledge/fixtures', data),
    delete: (id)   => req('DELETE', `/api/knowledge/fixtures/${id}`),
  },
  setupMethods: {
    list:   ()     => req('GET',    '/api/knowledge/setup-methods'),
    save:   (data) => req('POST',   '/api/knowledge/setup-methods', data),
    delete: (id)   => req('DELETE', `/api/knowledge/setup-methods/${id}`),
  },
  tools: {
    list:   ()     => req('GET',    '/api/knowledge/tools'),
    save:   (data) => req('POST',   '/api/knowledge/tools', data),
    delete: (id)   => req('DELETE', `/api/knowledge/tools/${id}`),
  },

  // ── Optimization ────────────────────────────────────────
  optimize: {
    run:     (projectId)           => req('POST', `/api/optimize/run/${projectId}`),
    results: (projectId)           => req('GET',  `/api/optimize/results/${projectId}`),
    select:  (projectId, payload)  => req('POST', `/api/optimize/select/${projectId}`, payload),
    export:  (projectId)           => req('GET',  `/api/optimize/export/${projectId}`),
  },

  report: {
    url: (projectId) => `${BASE}/api/report/${projectId}`,
  },
};
