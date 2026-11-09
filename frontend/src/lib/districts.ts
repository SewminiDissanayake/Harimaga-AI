/*
  districts.ts: Sri Lanka's 25 districts in three languages.
  `value` is the spelling the backend geography data uses (ds_divisions.json),
  so it is what we send as the answer.
*/
import type { Lang } from './i18n'

export interface District {
  value: string
  si: string
  ta: string
  province: 'W' | 'C' | 'S' | 'N' | 'E' | 'NW' | 'NC' | 'U' | 'SB'
}

export const DISTRICTS: District[] = [
  { value: 'Colombo', si: 'කොළඹ', ta: 'கொழும்பு', province: 'W' },
  { value: 'Gampaha', si: 'ගම්පහ', ta: 'கம்பஹா', province: 'W' },
  { value: 'Kalutara', si: 'කළුතර', ta: 'களுத்துறை', province: 'W' },
  { value: 'Kandy', si: 'මහනුවර', ta: 'கண்டி', province: 'C' },
  { value: 'Matale', si: 'මාතලේ', ta: 'மாத்தளை', province: 'C' },
  { value: 'Nuwara Eliya', si: 'නුවරඑළිය', ta: 'நுவரெலியா', province: 'C' },
  { value: 'Galle', si: 'ගාල්ල', ta: 'காலி', province: 'S' },
  { value: 'Matara', si: 'මාතර', ta: 'மாத்தறை', province: 'S' },
  { value: 'Hambantota', si: 'හම්බන්තොට', ta: 'அம்பாந்தோட்டை', province: 'S' },
  { value: 'Jaffna', si: 'යාපනය', ta: 'யாழ்ப்பாணம்', province: 'N' },
  { value: 'Kilinochchi', si: 'කිලිනොච්චිය', ta: 'கிளிநொச்சி', province: 'N' },
  { value: 'Mannar', si: 'මන්නාරම', ta: 'மன்னார்', province: 'N' },
  { value: 'Vavuniya', si: 'වවුනියාව', ta: 'வவுனியா', province: 'N' },
  { value: 'Mullaitivu', si: 'මුලතිව්', ta: 'முல்லைத்தீவு', province: 'N' },
  { value: 'Batticaloa', si: 'මඩකලපුව', ta: 'மட்டக்களப்பு', province: 'E' },
  { value: 'Ampara', si: 'අම්පාර', ta: 'அம்பாறை', province: 'E' },
  { value: 'Trincomalee', si: 'ත්‍රිකුණාමලය', ta: 'திருகோணமலை', province: 'E' },
  { value: 'Kurunegala', si: 'කුරුණෑගල', ta: 'குருணாகல்', province: 'NW' },
  { value: 'Puttalam', si: 'පුත්තලම', ta: 'புத்தளம்', province: 'NW' },
  { value: 'Anuradhapura', si: 'අනුරාධපුරය', ta: 'அனுராதபுரம்', province: 'NC' },
  { value: 'Polonnaruwa', si: 'පොළොන්නරුව', ta: 'பொலன்னறுவை', province: 'NC' },
  { value: 'Badulla', si: 'බදුල්ල', ta: 'பதுளை', province: 'U' },
  { value: 'Moneragala', si: 'මොණරාගල', ta: 'மொனராகலை', province: 'U' },
  { value: 'Ratnapura', si: 'රත්නපුර', ta: 'இரத்தினபுரி', province: 'SB' },
  { value: 'Kegalle', si: 'කෑගල්ල', ta: 'கேகாலை', province: 'SB' },
]

/** Backend fields that expect a district name */
export const DISTRICT_FIELDS = new Set([
  'district',
  'incident_district',
  'origin_district',
  'destination_district',
  'business_district',
])

export function districtLabel(d: District, lang: Lang): string {
  if (lang === 'en') return d.value
  return `${d[lang]}`
}
