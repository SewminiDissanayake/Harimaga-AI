/*
  normalize.ts
  ------------
  Each HariMaga category returns a DIFFERENT JSON shape
  (bus -> "jurisdiction", consumer -> "authority" object,
   lost document -> "document", safety -> "contacts" ...).

  This file converts all of them into ONE shape: RouteView.
  The RouteCard component then only needs to understand RouteView.

  The logic is ported from the old harimaga-ui-v8.js
  (routeAuthority, collectVerifiedChannels, collectRequiredInfo, collectSteps),
  but contacts are now structured objects instead of text lines,
  so each contact gets its own correct button (call / email / open / WhatsApp).
*/

import type { Routing } from './api'

export type ContactKind = 'phone' | 'whatsapp' | 'email' | 'url' | 'text'

export interface Contact {
  label: string
  value: string
  kind: ContactKind
  href?: string
  /** e.g. the local authority or police station this contact belongs to */
  group?: string
}

export interface RouteView {
  issueKey: string
  authority: string
  subtitle?: string
  district?: string
  contacts: Contact[]
  steps: string[]
  required: string[]
  notes: string[]
  emergency: boolean
}

// Small helpers ----------------------------------------------------------

type Obj = Record<string, unknown>
const isObj = (v: unknown): v is Obj => typeof v === 'object' && v !== null && !Array.isArray(v)
const str = (v: unknown): string => (typeof v === 'string' ? v.trim() : '')
const arr = (v: unknown): unknown[] => (Array.isArray(v) ? v : [])

/** Sri Lankan local number -> international format for wa.me links */
function toWhatsAppNumber(raw: string): string {
  let digits = raw.replace(/\D/g, '')
  if (digits.startsWith('0')) digits = '94' + digits.slice(1)
  return digits
}

/** Decide what kind of contact a value is and build its link. */
export function makeContact(label: string, rawValue: string, group?: string): Contact | null {
  const value = rawValue.trim()
  if (!value) return null

  if (/^https?:\/\//i.test(value)) {
    return { label, value, kind: 'url', href: value, group }
  }
  if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
    return { label, value, kind: 'email', href: `mailto:${value}`, group }
  }
  // Phone: at least 3 digits, and mostly digits/spaces/+/-
  const firstNumber = value.split('/')[0].trim()
  if (/\d{3,}/.test(firstNumber) && /^[\d\s+\-()]+$/.test(firstNumber)) {
    if (/whatsapp/i.test(label)) {
      return { label, value, kind: 'whatsapp', href: `https://wa.me/${toWhatsAppNumber(firstNumber)}`, group }
    }
    return { label, value, kind: 'phone', href: `tel:${firstNumber.replace(/[^\d+]/g, '')}`, group }
  }
  return { label, value, kind: 'text', group }
}

/** Read a record that has `channels: [{label, type, value}]` and/or direct fields. */
function contactsFromRecord(record: unknown, group?: string): Contact[] {
  if (!isObj(record)) return []
  const out: (Contact | null)[] = []

  for (const ch of arr(record.channels)) {
    if (!isObj(ch)) continue
    const label = str(ch.label) || str(ch.purpose) || humanizeKey(str(ch.type)) || 'Official channel'
    const value = str(ch.value) || str(ch.phone) || str(ch.email) || str(ch.url)
    out.push(makeContact(label, value, group))
  }

  const direct: [string, unknown][] = [
    ['Hotline', record.hotline],
    ['Phone', record.phone],
    ['Telephone', record.telephone],
    ['Mobile', record.mobile],
    ['WhatsApp', record.whatsapp],
    ['Email', record.email],
    ['Website', record.website],
    ['Online complaint form', record.online_complaint_form],
    ['Consumer complaint unit', record.consumer_complaint_unit],
  ]
  for (const [label, val] of direct) out.push(makeContact(label, str(val), group))

  return out.filter((c): c is Contact => c !== null)
}

// Main pieces --------------------------------------------------------------

function findAuthority(r: Routing): string {
  const j = isObj(r.jurisdiction) ? r.jurisdiction : {}
  const d = isObj(r.document) ? r.document : {}
  const a = r.authority
  return (
    str(r.technical_authority) ||
    str(j.authority_name) ||
    str(d.authority) ||
    (isObj(a) ? str(a.name) : str(a)) ||
    str(r.authority_name) ||
    ''
  )
}

function collectContacts(r: Routing): Contact[] {
  const list: Contact[] = []

  // Emergency / safety contacts first
  for (const c of arr(r.contacts)) {
    if (!isObj(c)) continue
    const label = str(c.label) || 'Official contact'
    for (const v of [c.phone, c.email, c.url]) {
      const contact = makeContact(label, str(v))
      if (contact) list.push(contact)
    }
  }

  // Core router (RDA, NWSDB, CEB, ...): channels sit at the top level
  list.push(...contactsFromRecord(r))

  for (const rec of [r.verified_provider_route, r.verified_authority_route, r.verified_ntc_fallback]) {
    list.push(...contactsFromRecord(rec))
  }

  // Regional SLTB WhatsApp (bus)
  const j = isObj(r.jurisdiction) ? r.jurisdiction : {}
  if (isObj(j.regional_sltb)) {
    const region = str(j.regional_sltb.region)
    const c = makeContact(`SLTB ${region} WhatsApp`, str(j.regional_sltb.whatsapp))
    if (c) list.push(c)
  }

  // Local authorities (roads, garbage)
  for (const row of arr(r.verified_local_authority_routes)) {
    if (!isObj(row)) continue
    const name = isObj(row.authority) ? str(row.authority.name) : 'Local authority'
    if (row.verified_issue_channel) {
      list.push(...contactsFromRecord(row.verified_issue_channel, name))
    } else if (isObj(row.directory_fallback)) {
      const f = row.directory_fallback
      for (const p of [...arr(f.phones), ...arr(f.mobiles)]) {
        const c = makeContact('Office phone (directory)', str(p), name)
        if (c) list.push(c)
      }
      for (const e of arr(f.emails)) {
        const c = makeContact('Office email (directory)', str(e), name)
        if (c) list.push(c)
      }
    }
  }

  // Consumer Affairs Authority
  if (isObj(r.authority)) list.push(...contactsFromRecord(r.authority))
  if (isObj(r.district_office)) {
    const c = makeContact(str(r.district_office.office) || 'District office', str(r.district_office.telephone))
    if (c) list.push(c)
  }

  // Lost documents
  if (isObj(r.document)) {
    for (const c of arr(r.document.contacts)) {
      if (!isObj(c)) continue
      const contact = makeContact(str(c.label), str(c.value))
      if (contact) list.push(contact)
    }
  }
  for (const p of arr(r.police_station_matches).slice(0, 5)) {
    if (!isObj(p)) continue
    const station = str(p.station) || 'Police station'
    for (const [label, v] of [['General', p.general], ['Mobile', p.mobile], ['Email', p.email]] as const) {
      const c = makeContact(label, str(v), station)
      if (c) list.push(c)
    }
  }

  // Disaster
  for (const key of ['dmc_contacts', 'technical_contacts'] as const) {
    for (const c of arr(r[key])) {
      if (!isObj(c)) continue
      for (const v of [c.phone, c.email]) {
        const contact = makeContact(str(c.label), str(v))
        if (contact) list.push(contact)
      }
    }
  }
  for (const s of arr(r.live_sources)) {
    if (!isObj(s)) continue
    const c = makeContact(str(s.label), str(s.url))
    if (c) list.push(c)
  }

  // Remove duplicates (same kind + same value)
  const seen = new Set<string>()
  return list
    .filter((c) => {
      const key = `${c.kind}:${c.value.replace(/\s/g, '')}`
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
    .slice(0, 16)
}

function unique(items: string[]): string[] {
  return [...new Set(items.filter(Boolean))]
}

export function normalizeRoute(r: Routing, fallbackIssue: string): RouteView {
  const j = isObj(r.jurisdiction) ? r.jurisdiction : {}
  const d = isObj(r.document) ? r.document : {}
  const policy = isObj(r.policy) ? r.policy : {}

  const required = unique([
    ...arr(r.required_information).map(str),
    ...arr(d.required_information).map(str),
  ]).slice(0, 14)

  const steps = arr(d.steps).length ? arr(d.steps).map(str) : arr(r.steps).map(str)

  const notes = unique([
    str(r.note),
    str(r.time_note),
    str(r.safety),
    str(policy.evidence_safety),
    str(j.reason),
  ])

  const district =
    str(r.district) || str(j.incident_district) || str(j.origin_district) || undefined

  const contacts = collectContacts(r)

  return {
    issueKey: str(r.issue_key) || fallbackIssue,
    // No authority field (e.g. women & child safety)? Use the first official
    // contact, which the backend already lists in priority order.
    authority:
      findAuthority(r) || contacts[0]?.label || humanizeKey(str(r.issue_key) || fallbackIssue),
    subtitle: str(r.subtype_label) || str(d.label) || undefined,
    district,
    contacts,
    steps: steps.filter(Boolean),
    required,
    notes,
    emergency: r.issue_key === 'women_child_safety' && r.immediate_danger === true,
  }
}

// Labels ---------------------------------------------------------------------

/**
 * "photo_if_available" -> "Photo (if available)"
 * "immediate_danger_yes_or_no" -> "Immediate danger (yes / no)"
 */
export function humanizeKey(key: string): string {
  if (!key) return ''
  let text = key
  let suffix = ''
  const suffixes: [RegExp, string][] = [
    [/_if_available$/, ' (if available)'],
    [/_if_known$/, ' (if known)'],
    [/_if_relevant$/, ' (if relevant)'],
    [/_if_any$/, ' (if any)'],
    [/_if_visible$/, ' (if visible)'],
    [/_if_made$/, ' (if made)'],
    [/_if_safe$/, ' (only if safe)'],
    [/_only_if_safe$/, ' (only if safe)'],
    [/_yes_or_no$/, ' (yes / no)'],
    [/_as_required$/, ' (as required)'],
  ]
  for (const [re, s] of suffixes) {
    if (re.test(text)) {
      text = text.replace(re, '')
      suffix = s
      break
    }
  }
  const acronyms: Record<string, string> = {
    nic: 'NIC', rda: 'RDA', ceb: 'CEB', leco: 'LECO', nwsdb: 'NWSDB',
    ntc: 'NTC', sltb: 'SLTB', ds: 'DS', or: 'or', and: 'and', of: 'of',
  }
  const words = text.split(/[_-]+/).filter(Boolean).map((w) => acronyms[w] ?? w)
  const sentence = words.join(' ')
  return sentence.charAt(0).toUpperCase() + sentence.slice(1) + suffix
}

/** Sinhala labels for the most common "have this ready" items. */
const SI_LABELS: Record<string, string> = {
  location: 'ස්ථානය',
  nearby_landmark: 'ළඟම ඇති සලකුණක් (landmark)',
  description: 'ප්‍රශ්නයේ විස්තරය',
  brief_description: 'කෙටි විස්තරයක්',
  description_of_problem: 'ප්‍රශ්නයේ විස්තරය',
  description_of_what_happened: 'වුණු දේ',
  what_happened: 'වුණු දේ',
  photo_if_available: 'ඡායාරූපයක් (තියෙනවා නම්)',
  photo_or_video_if_available: 'ඡායාරූප හෝ වීඩියෝ (තියෙනවා නම්)',
  photos_or_video_if_available: 'ඡායාරූප හෝ වීඩියෝ (තියෙනවා නම්)',
  coordinates_if_available: 'GPS ස්ථානය (තියෙනවා නම්)',
  road_name: 'පාරේ නම',
  road_type_if_known: 'පාරේ වර්ගය (දන්නවා නම්)',
  account_number_if_available: 'ගිණුම් අංකය (තියෙනවා නම්)',
  date_and_time: 'දිනය සහ වේලාව',
  date_time: 'දිනය සහ වේලාව',
  date: 'දිනය',
  district: 'දිස්ත්‍රික්කය',
  bus_number: 'බස් අංකය',
  bus_number_or_registration: 'බස් අංකය / ලියාපදිංචි අංකය',
  route: 'මාර්ගය',
  route_number_or_route_name: 'මාර්ග අංකය / නම',
  exact_incident_location: 'සිද්ධිය වුණු නිශ්චිත තැන',
  ticket_or_fare_details_if_relevant: 'ටිකට් / ගාස්තු විස්තර (අදාළ නම්)',
  full_name: 'සම්පූර්ණ නම',
  current_address: 'වර්තමාන ලිපිනය',
  business_name_and_address: 'ව්‍යාපාරයේ නම සහ ලිපිනය',
  product_or_service: 'භාණ්ඩය හෝ සේවාව',
  receipt_or_invoice: 'රිසිට්පත / බිල්පත',
  receipt_if_available: 'රිසිට්පත (තියෙනවා නම්)',
  lost_nic_number_if_known: 'නැති වුණු NIC අංකය (දන්නවා නම්)',
  police_complaint_reference_or_copy: 'පොලිස් පැමිණිලි අංකය / පිටපත',
  date_and_approximate_time_lost: 'නැති වුණු දිනය සහ ආසන්න වේලාව',
  place_or_area_lost: 'නැති වුණු ස්ථානය',
  missed_collection_dates: 'කුණු එකතු නොකළ දින',
  safe_contact_method: 'ආරක්ෂිතව සම්බන්ධ කරගත හැකි ක්‍රමය',
  evidence_only_if_safe: 'සාක්ෂි (ආරක්ෂිත නම් පමණක්)',
}

export function labelFor(key: string, lang: 'si' | 'ta' | 'en'): string {
  if (lang === 'si' && SI_LABELS[key]) return SI_LABELS[key]
  return humanizeKey(key)
}
