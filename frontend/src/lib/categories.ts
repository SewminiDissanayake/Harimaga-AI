/*
  categories.ts: the 12 HariMaga service categories.
  `key` must match the backend issue keys (see VALID_CATEGORY_HINTS in app.py).
  When the user taps a category, `key` is sent to /api/route as `category_hint`.
*/
import {
  Bus, CloudRainWind, Construction, Droplet, IdCard, Landmark,
  Leaf, Plane, ShieldCheck, ShoppingBag, Trash2, Zap, type LucideIcon,
} from 'lucide-react'
import type { Lang } from './i18n'

export interface Category {
  key: string
  icon: LucideIcon
  si: string
  en: string
  ta: string
  subSi: string
  subEn: string
  subTa: string
  example: string
  /** Tailwind classes for the icon tile: background gradient + icon colour */
  tone: string
  /** Optional illustration shown in the side panel */
  art?: string
}

export const CATEGORIES: Category[] = [
  { key: 'road_issue', icon: Construction, si: 'පාරවල්', en: 'Roads', ta: 'வீதிகள்', subTa: 'குழிகள், சேதமடைந்த வீதிகள்', subSi: 'වළවල්, කැඩුණු පාරවල්', subEn: 'Potholes, damaged roads',
    example: 'para kadila loku walak thiyenawa', tone: 'from-amber-100 to-amber-200 text-amber-800', art: '/art/civic-road-v8-2.svg' },
  { key: 'water_issue', icon: Droplet, si: 'වතුර', en: 'Water', ta: 'நீர்', subTa: 'நீர் இல்லை, கசிவுகள்', subSi: 'වතුර නැති, කාන්දු', subEn: 'No supply, leaks',
    example: 'apita wathura na dawas 3k', tone: 'from-sky-100 to-sky-200 text-sky-800', art: '/art/civic-water-v8-2.svg' },
  { key: 'electricity_issue', icon: Zap, si: 'විදුලිය', en: 'Electricity', ta: 'மின்சாரம்', subTa: 'CEB / LECO', subSi: 'CEB / LECO', subEn: 'CEB / LECO',
    example: 'current eka na paya 5k', tone: 'from-yellow-100 to-yellow-200 text-yellow-800' },
  { key: 'garbage_collection', icon: Trash2, si: 'කුණු', en: 'Garbage', ta: 'குப்பை', subTa: 'சேகரிக்கப்படாத குப்பை', subSi: 'කුණු එකතු නොකිරීම', subEn: 'Missed collection',
    example: 'garbage collect karanne na sathi dekak', tone: 'from-lime-100 to-lime-200 text-lime-800' },
  { key: 'bus_complaint', icon: Bus, si: 'බස්', en: 'Bus', ta: 'பேருந்து', subTa: 'SLTB, தனியார்', subSi: 'SLTB, පෞද්ගලික', subEn: 'SLTB, private',
    example: 'bus eke conductor balance dunne na', tone: 'from-red-100 to-red-200 text-red-800' },
  { key: 'consumer_complaint', icon: ShoppingBag, si: 'පාරිභෝගික', en: 'Consumer', ta: 'நுகர்வோர்', subTa: 'கடைகள், பணம் திருப்புதல்', subSi: 'කඩ, refund, warranty', subEn: 'Shops, refunds, warranty',
    example: 'shop eken refund denne na', tone: 'from-violet-100 to-violet-200 text-violet-800' },
  { key: 'environment_issue', icon: Leaf, si: 'පරිසරය', en: 'Environment', ta: 'சுற்றுச்சூழல்', subTa: 'புகை, மாசு', subSi: 'දුම, දූෂණය', subEn: 'Smoke, pollution',
    example: 'neighbour is burning plastic every night', tone: 'from-emerald-100 to-emerald-200 text-emerald-800' },
  { key: 'lost_document', icon: IdCard, si: 'ලේඛන', en: 'Documents', ta: 'ஆவணங்கள்', subTa: 'NIC, அனுமதிப்பத்திரம், கடவுச்சீட்டு', subSi: 'NIC, licence, passport', subEn: 'NIC, licence, passport',
    example: 'I lost my NIC', tone: 'from-orange-100 to-orange-200 text-orange-800' },
  { key: 'immigration_issue', icon: Plane, si: 'ගමන් බලපත්‍ර', en: 'Immigration', ta: 'குடிவரவு', subTa: 'கடவுச்சீட்டு, விசா', subSi: 'Passport, visa', subEn: 'Passport, visa',
    example: 'passport eka thama awe na', tone: 'from-cyan-100 to-cyan-200 text-cyan-800' },
  { key: 'women_child_safety', icon: ShieldCheck, si: 'ආරක්ෂාව', en: 'Safety', ta: 'பாதுகாப்பு', subTa: 'பெண்கள் மற்றும் குழந்தைகள்', subSi: 'කාන්තා සහ ළමා', subEn: 'Women & children',
    example: 'mata kenek follow karanawa', tone: 'from-rose-100 to-rose-200 text-rose-800', art: '/art/civic-safety-v8-2.svg' },
  { key: 'disaster_alert', icon: CloudRainWind, si: 'ආපදා', en: 'Disaster', ta: 'பேரிடர்', subTa: 'வெள்ளம், மண்சரிவு', subSi: 'ගංවතුර, නායයෑම්', subEn: 'Floods, landslides',
    example: 'flood warning in Ratnapura', tone: 'from-blue-100 to-blue-200 text-blue-800', art: '/art/civic-disaster-v8-2.svg' },
  { key: 'unknown_government_issue', icon: Landmark, si: 'වෙනත්', en: 'Other', ta: 'மற்றவை', subTa: 'எங்கே செல்வது என்று தெரியவில்லை', subSi: 'කොහෙට යන්නද දන්නේ නෑ', subEn: 'Not sure where to go',
    example: 'which government office should I contact?', tone: 'from-slate-100 to-slate-200 text-slate-700' },
]

/** Short description in the chosen language */
export const categorySub = (c: Category, lang: Lang) =>
  lang === 'si' ? c.subSi : lang === 'ta' ? c.subTa : c.subEn

export const categoryByKey = (key?: string) => CATEGORIES.find((c) => c.key === key)
