/*
  api.ts: every call to the Flask backend lives here.
  The rest of the app never uses fetch() directly, so if an endpoint
  changes we only fix it in one place.
*/

export type Option = string | { value: unknown; label?: string }

export interface Classification {
  label: string
  confidence: number
  method: string
}

/** The backend returns many different shapes, so most fields are optional. */
export interface Routing {
  status: 'needs_clarification' | 'routed' | 'resolved' | string
  issue_key?: string
  needed_field?: string
  question?: string
  options?: Option[]
  allow_skip?: boolean
  hint?: string
  previous_answer_not_understood?: boolean
  message?: string
  // ...plus many category-specific fields (authority, contacts, jurisdiction...)
  [key: string]: unknown
}

export interface RouteResponse {
  ok: boolean
  input: string
  classification: Classification
  answers: Record<string, unknown>
  routing: Routing
  error?: string
}

export async function routeProblem(
  text: string,
  answers: Record<string, unknown>,
  categoryHint?: string,
): Promise<RouteResponse> {
  const res = await fetch('/api/route', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    // category_hint: the category the user tapped (optional)
    body: JSON.stringify({ text, answers, category_hint: categoryHint }),
  })

  const data = await readJson<RouteResponse>(res)
  return data
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch('/api/health')
    const data = await res.json()
    return data.ok === true
  } catch {
    return false
  }
}

// ---------------------------------------------------------------------------
// Evidence + complaint draft
// ---------------------------------------------------------------------------

export interface Evidence {
  id: string
  filename: string // generic name like "Photo evidence"; original name is never stored
  mime_type: string
  size_bytes: number
  uploaded_at: number
  expires_at: number
  privacy_processed: boolean
  preview_url: string
}

export interface Draft {
  subject: string
  body: string
  review_note: string
}

/** Error that also carries a short code, e.g. 'rate_limited' (HTTP 429) */
export class ApiError extends Error {
  code?: string
  constructor(message: string, code?: string) {
    super(message)
    this.code = code
  }
}

async function readJson<T>(res: Response): Promise<T & { ok: boolean; error?: string }> {
  if (res.status === 429) throw new ApiError('Too many requests.', 'rate_limited')
  let data: T & { ok: boolean; error?: string }
  try {
    data = await res.json()
  } catch {
    throw new Error(`Backend returned an unexpected response (${res.status}).`)
  }
  if (!res.ok || !data.ok) throw new Error(data.error || `Backend error (${res.status}).`)
  return data
}

/** A random anonymous ID that links evidence files to this one request. */
export function newRequestId(): string {
  return 'hm_' + crypto.randomUUID().replaceAll('-', '')
}

export async function uploadEvidence(file: File, requestId: string, privacyProcessed: boolean): Promise<Evidence> {
  const form = new FormData()
  form.append('file', file)
  form.append('request_id', requestId)
  form.append('privacy_processed', privacyProcessed ? 'true' : 'false')
  const res = await fetch('/api/evidence', { method: 'POST', body: form })
  const data = await readJson<{ evidence: Evidence }>(res)
  return data.evidence
}

export async function deleteEvidence(id: string, requestId: string): Promise<void> {
  try {
    await fetch(`/api/evidence/${encodeURIComponent(id)}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ request_id: requestId }),
    })
  } catch {
    /* the server deletes it after 24 hours anyway */
  }
}

export async function prepareDraft(params: {
  text: string
  answers: Record<string, unknown>
  evidenceIds: string[]
  requestId: string
  categoryHint?: string
}): Promise<Draft> {
  const res = await fetch('/api/complaint-draft', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: params.text,
      answers: params.answers,
      evidence_ids: params.evidenceIds,
      request_id: params.requestId,
      category_hint: params.categoryHint,
    }),
  })
  const data = await readJson<{ draft: Draft }>(res)
  return data.draft
}

export async function sendFeedback(issueKey: string, helpful: boolean): Promise<void> {
  // Only the category and yes/no are sent. No text, no ID, nothing personal.
  try {
    await fetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ issue_key: issueKey, helpful }),
    })
  } catch {
    /* feedback is optional */
  }
}
