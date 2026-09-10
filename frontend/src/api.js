const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options)
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`)
  return body
}

export const api = {
  health: () => request('/../health'),
  schemes: (params = '') => request(`/schemes${params}`),
  createProfile: (profile) => request('/profiles', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(profile) }),
  checklist: (id) => request(`/profiles/${id}/checklist`),
  profileSchemes: (id) => request(`/profiles/${id}/schemes`),
  intake: (payload) => request('/ai/intake', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
  reviewDocument: (file) => { const data = new FormData(); data.append('file', file); return request('/ai/documents/review', { method: 'POST', body: data }) },
  maitriSubmit: (profileId, fileName, reviewId) => request(`/maitri/submit?profile_id=${profileId}&file_name=${encodeURIComponent(fileName)}&review_id=${reviewId}`, { method: 'POST' }),
}

export const demoProfile = {
  id: 'demo-priya', name: 'Priya Foods', industry_category: 'food_processing', location_district: 'Pune', investment_amount: 6000000, project_stage: 'new_setup', employee_count: 18,
}

export const demoApprovals = [
  { approval_id: 'factory_license', name: 'Factory License', department: 'Directorate of Industrial Safety and Health', required_documents: ['site_plan', 'occupier_identity', 'process_description'], sla_days: 30, dependencies: [], source: 'Illustrative placeholder - verify with the competent authority', applicability_reason: 'Manufacturing activity detected.' },
  { approval_id: 'pollution_consent', name: 'Consent to Establish', department: 'Maharashtra Pollution Control Board', required_documents: ['site_plan', 'process_description', 'water_balance'], sla_days: 45, dependencies: [], source: 'Illustrative placeholder - verify with the competent authority', applicability_reason: 'Industrial activity may create environmental impacts.' },
  { approval_id: 'local_body_noc', name: 'Local Body No-Objection Certificate', department: 'Local Municipal Authority', required_documents: ['lease_or_ownership_proof', 'layout_plan'], sla_days: 21, dependencies: [], source: 'Illustrative placeholder - verify with the competent authority', applicability_reason: 'New setup requires local site clearance.' },
  { approval_id: 'fire_noc', name: 'Fire Safety No-Objection Certificate', department: 'Local Fire Department', required_documents: ['building_plan', 'fire_system_plan'], sla_days: 30, dependencies: ['local_body_noc'], source: 'Illustrative placeholder - verify with the competent authority', applicability_reason: 'Scale crosses the illustrative fire-safety trigger.' },
]
