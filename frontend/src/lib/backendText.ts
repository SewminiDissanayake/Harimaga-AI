/*
  backendText.ts
  --------------
  The backend writes its questions and options in English.
  This file translates them for the interface. If a sentence is not in
  the list, the English text is shown, so nothing ever breaks.

  To add a translation: copy the exact English text from the backend
  as the key, and add the Sinhala and Tamil versions.
  (Tamil: please have a native speaker review before publishing.)
*/
import type { Lang } from './i18n'

type T = { si: string; ta: string }

const QUESTIONS: Record<string, T> = {
  // Core router
  'Which district is the problem located in?': {
    si: 'ප්‍රශ්නය තියෙන්නේ මොන දිස්ත්‍රික්කයේද?',
    ta: 'பிரச்சனை எந்த மாவட்டத்தில் உள்ளது?',
  },
  'Which Divisional Secretariat area is the problem located in?': {
    si: 'ප්‍රශ්නය තියෙන්නේ මොන ප්‍රාදේශීය ලේකම් කොට්ඨාසයේද?',
    ta: 'பிரச்சனை எந்த பிரதேச செயலகப் பிரிவில் உள்ளது?',
  },
  'I could not safely match that District + Divisional Secretariat combination. Please confirm the official DS area name.': {
    si: 'ඒ දිස්ත්‍රික්කය සහ ප්‍රාදේශීය ලේකම් කොට්ඨාසය ගැළපුණේ නෑ. කරුණාකර පහළ ලැයිස්තුවෙන් තෝරන්න.',
    ta: 'அந்த மாவட்டமும் பிரதேச செயலகப் பிரிவும் பொருந்தவில்லை. கீழே உள்ள பட்டியலில் இருந்து தேர்ந்தெடுக்கவும்.',
  },
  'No local-authority mapping was found for this location. Please provide a more specific area or GND.': {
    si: 'මේ ස්ථානයට පළාත් පාලන ආයතනයක් හම්බුණේ නෑ. ග්‍රාම නිලධාරී වසම හෝ ප්‍රදේශය වඩා නිවැරදිව ලියන්න.',
    ta: 'இந்த இடத்திற்கு உள்ளூராட்சி நிறுவனம் கிடைக்கவில்லை. கிராம அலுவலர் பிரிவை அல்லது பகுதியை இன்னும் துல்லியமாக எழுதவும்.',
  },
  'Is this service provided by the National Water Supply and Drainage Board (NWSDB), or another/local water scheme?': {
    si: 'මේ වතුර සපයන්නේ ජාතික ජල සම්පාදන හා ජලාපවහන මණ්ඩලයද (NWSDB), නැත්නම් වෙනත් ප්‍රාදේශීය ජල ව්‍යාපෘතියක්ද?',
    ta: 'இந்த நீரை வழங்குவது தேசிய நீர் வழங்கல் மற்றும் வடிகாலமைப்புச் சபையா (NWSDB), அல்லது வேறு உள்ளூர் நீர் திட்டமா?',
  },
  'Who is your electricity provider?': {
    si: 'ඔබට විදුලිය සපයන්නේ කවුද?',
    ta: 'உங்களுக்கு மின்சாரம் வழங்குவது யார்?',
  },
  'Is the damaged road a national/RDA road or a local council road?': {
    si: 'කැඩිලා තියෙන්නේ ජාතික / RDA පාරක්ද, නැත්නම් ප්‍රාදේශීය සභා පාරක්ද?',
    ta: 'சேதமடைந்த வீதி தேசிய / RDA வீதியா, அல்லது உள்ளூராட்சி வீதியா?',
  },
  'What type of environmental problem is this?': {
    si: 'මේ මොන වගේ පරිසර ප්‍රශ්නයක්ද?',
    ta: 'இது எந்த வகையான சுற்றுச்சூழல் பிரச்சனை?',
  },
  'I need more information before I can safely route this problem.': {
    si: 'මේ ප්‍රශ්නය නිවැරදිව යොමු කරන්න තව විස්තර ඕන.',
    ta: 'இந்தப் பிரச்சனையைச் சரியாக வழிநடத்த இன்னும் தகவல் தேவை.',
  },
  // Bus
  'What type of bus was involved?': {
    si: 'මොන වර්ගයේ බස් එකක්ද?',
    ta: 'எந்த வகை பேருந்து?',
  },
  'In which district did the incident happen?': {
    si: 'සිද්ධිය වුණේ මොන දිස්ත්‍රික්කයේද?',
    ta: 'சம்பவம் எந்த மாவட்டத்தில் நடந்தது?',
  },
  'Which district does this private bus route start from?': {
    si: 'මේ පෞද්ගලික බස් මාර්ගය පටන් ගන්නේ මොන දිස්ත්‍රික්කයෙන්ද?',
    ta: 'இந்த தனியார் பேருந்து வழித்தடம் எந்த மாவட்டத்தில் தொடங்குகிறது?',
  },
  'Which district does this private bus route go to / end in?': {
    si: 'මේ පෞද්ගලික බස් මාර්ගය අවසන් වෙන්නේ මොන දිස්ත්‍රික්කයේද?',
    ta: 'இந்த தனியார் பேருந்து வழித்தடம் எந்த மாவட்டத்தில் முடிகிறது?',
  },
  // Consumer
  'What best describes the consumer problem?': {
    si: 'පාරිභෝගික ප්‍රශ්නය හොඳින්ම විස්තර වෙන්නේ මොකෙන්ද?',
    ta: 'நுகர்வோர் பிரச்சனையை எது சிறப்பாக விவரிக்கிறது?',
  },
  'In which district is the business / seller / service provider located, or where did the transaction happen?': {
    si: 'කඩය / විකුණුම්කරු තියෙන්නේ, නැත්නම් ගනුදෙනුව වුණේ මොන දිස්ත්‍රික්කයේද?',
    ta: 'கடை / விற்பனையாளர் எந்த மாவட்டத்தில் உள்ளது, அல்லது பரிவர்த்தனை எங்கே நடந்தது?',
  },
  // Lost documents
  'Which government document was lost?': {
    si: 'නැති වුණේ මොන රජයේ ලේඛනයද?',
    ta: 'எந்த அரசாங்க ஆவணம் தொலைந்தது?',
  },
  "Type the nearest town or police station name for an official station-contact lookup, or enter 'skip'.": {
    si: 'ළඟම නගරය හෝ පොලිස් ස්ථානයේ නම ලියන්න. ඕන නැත්නම් “skip” ලියන්න.',
    ta: 'அருகிலுள்ள நகரம் அல்லது காவல் நிலையத்தின் பெயரை எழுதவும். தேவையில்லை என்றால் “skip” என எழுதவும்.',
  },
  // Safety
  'What best describes the women / child safety concern?': {
    si: 'කාන්තා / ළමා ආරක්ෂාව පිළිබඳ ප්‍රශ්නය හොඳින්ම විස්තර වෙන්නේ මොකෙන්ද?',
    ta: 'பெண்கள் / குழந்தைகள் பாதுகாப்பு பிரச்சனையை எது சிறப்பாக விவரிக்கிறது?',
  },
  'Is anyone in immediate danger right now?': {
    si: 'කවුරු හරි දැන්ම අනතුරේද?',
    ta: 'யாராவது இப்போது உடனடி ஆபத்தில் இருக்கிறார்களா?',
  },
  'Please answer whether anyone is in immediate danger right now.': {
    si: 'කවුරු හරි දැන්ම අනතුරේද කියලා කරුණාකර කියන්න.',
    ta: 'யாராவது இப்போது ஆபத்தில் இருக்கிறார்களா என்று சொல்லவும்.',
  },
  // Disaster
  'What type of disaster concern is this?': {
    si: 'මේ මොන වගේ ආපදාවක්ද?',
    ta: 'இது எந்த வகையான பேரிடர்?',
  },
  'Which district are you asking about?': {
    si: 'ඔබ අහන්නේ මොන දිස්ත්‍රික්කය ගැනද?',
    ta: 'நீங்கள் எந்த மாவட்டம் பற்றி கேட்கிறீர்கள்?',
  },
  // Answer not understood (app.py v9)
  "Sorry, I didn't understand that answer. Please choose one of the options below.": {
    si: 'සමාවෙන්න, ඒ පිළිතුර තේරුණේ නෑ. කරුණාකර පහළ options වලින් එකක් තෝරන්න.',
    ta: 'மன்னிக்கவும், அந்தப் பதில் புரியவில்லை. கீழே உள்ள தெரிவுகளில் ஒன்றைத் தேர்ந்தெடுக்கவும்.',
  },
  "Sorry, I didn't understand that answer. Please try again.": {
    si: 'සමාවෙන්න, ඒ පිළිතුර තේරුණේ නෑ. කරුණාකර ආයේ උත්සාහ කරන්න.',
    ta: 'மன்னிக்கவும், அந்தப் பதில் புரியவில்லை. மீண்டும் முயற்சிக்கவும்.',
  },
}

/** Some questions start with a fixed sentence and continue differently. */
const PREFIXES: [string, T][] = [
  [
    'This DS area overlaps more than one local authority.',
    {
      si: 'මේ ප්‍රදේශයට පළාත් පාලන ආයතන කිහිපයක් අයිතියි. ඔබේ සභාව දන්නවා නම් පහළින් තෝරන්න. නැත්නම් ග්‍රාම නිලධාරී වසම ලියන්න.',
      ta: 'இந்தப் பகுதி பல உள்ளூராட்சி நிறுவனங்களுக்குள் வருகிறது. உங்கள் சபை தெரிந்தால் கீழே தேர்ந்தெடுக்கவும். இல்லையென்றால் கிராம அலுவலர் பிரிவை எழுதவும்.',
    },
  ],
]

const OPTIONS: Record<string, T> = {
  'National / RDA road': { si: 'ජාතික / RDA පාර', ta: 'தேசிய / RDA வீதி' },
  'Local council road': { si: 'ප්‍රාදේශීය සභා පාර', ta: 'உள்ளூராட்சி வீதி' },
  'Not sure': { si: 'විශ්වාස නෑ', ta: 'உறுதியாகத் தெரியாது' },
  'Other / local water scheme': { si: 'වෙනත් / ප්‍රාදේශීය ජල ව්‍යාපෘතිය', ta: 'வேறு / உள்ளூர் நீர் திட்டம்' },
  'Industrial pollution': { si: 'කර්මාන්ත දූෂණය', ta: 'தொழிற்சாலை மாசு' },
  'Hazardous waste': { si: 'අනතුරුදායක අපද්‍රව්‍ය', ta: 'அபாயகரமான கழிவுகள்' },
  'Noise pollution': { si: 'ශබ්ද දූෂණය', ta: 'ஒலி மாசு' },
  'Environmental damage': { si: 'පරිසර හානිය', ta: 'சுற்றுச்சூழல் சேதம்' },
  'Routine garbage collection': { si: 'සාමාන්‍ය කුණු එකතු කිරීම', ta: 'வழக்கமான குப்பை சேகரிப்பு' },
  'Private bus': { si: 'පෞද්ගලික බස්', ta: 'தனியார் பேருந்து' },
  Yes: { si: 'ඔව්', ta: 'ஆம்' },
  No: { si: 'නෑ', ta: 'இல்லை' },
  'Overpricing / price display issue': { si: 'වැඩි මිල / මිල ප්‍රදර්ශනය නොකිරීම', ta: 'அதிக விலை / விலை காட்சிப் பிரச்சனை' },
  'Defective product / warranty issue': { si: 'දෝෂ සහිත භාණ්ඩ / warranty ප්‍රශ්න', ta: 'குறைபாடுள்ள பொருள் / உத்தரவாதப் பிரச்சனை' },
  'Refund / replacement dispute': { si: 'මුදල් ආපසු / භාණ්ඩ මාරු කිරීම', ta: 'பணத்தைத் திருப்புதல் / மாற்றுதல் தகராறு' },
  'Expired / unsafe / mislabelled goods': { si: 'කල් ඉකුත් / අනාරක්ෂිත / වැරදි ලේබල් භාණ්ඩ', ta: 'காலாவதியான / பாதுகாப்பற்ற / தவறான லேபிள் பொருட்கள்' },
  'Misleading advertisement / unfair trade practice': { si: 'නොමඟ යවන දැන්වීම් / අසාධාරණ වෙළඳාම', ta: 'தவறான விளம்பரம் / நியாயமற்ற வர்த்தகம்' },
  'Paid service complaint': { si: 'මුදල් ගෙවූ සේවාවක් ගැන පැමිණිල්ල', ta: 'கட்டண சேவை பற்றிய முறைப்பாடு' },
  'Other consumer issue': { si: 'වෙනත් පාරිභෝගික ප්‍රශ්නයක්', ta: 'வேறு நுகர்வோர் பிரச்சனை' },
  'National Identity Card (NIC)': { si: 'ජාතික හැඳුනුම්පත (NIC)', ta: 'தேசிய அடையாள அட்டை (NIC)' },
  'Driving Licence': { si: 'රියදුරු බලපත්‍රය', ta: 'சாரதி அனுமதிப்பத்திரம்' },
  'Sri Lankan Passport': { si: 'ශ්‍රී ලංකා ගමන් බලපත්‍රය', ta: 'இலங்கை கடவுச்சீட்டு' },
  'Other government-issued document': { si: 'වෙනත් රජයේ ලේඛනයක්', ta: 'வேறு அரசாங்க ஆவணம்' },
  'Public / sexual harassment': { si: 'පොදු / ලිංගික හිරිහැර', ta: 'பொது / பாலியல் துன்புறுத்தல்' },
  'Stalking / being followed': { si: 'ලුහුබැඳීම / පසුපසින් ඒම', ta: 'பின்தொடர்தல்' },
  'Domestic violence': { si: 'ගෘහස්ථ හිංසනය', ta: 'குடும்ப வன்முறை' },
  'Child abuse / neglect / exploitation': { si: 'ළමා අපචාර / නොසලකා හැරීම / සූරාකෑම', ta: 'சிறுவர் துஷ்பிரயோகம் / புறக்கணிப்பு / சுரண்டல்' },
  'Physical assault / threat': { si: 'ශාරීරික පහරදීම / තර්ජනය', ta: 'உடல் தாக்குதல் / அச்சுறுத்தல்' },
  'Online harassment / abuse': { si: 'Online හිරිහැර', ta: 'இணையத் துன்புறுத்தல்' },
  'Other women/child safety concern': { si: 'වෙනත් කාන්තා / ළමා ආරක්ෂක ප්‍රශ්නයක්', ta: 'வேறு பெண்கள் / குழந்தைகள் பாதுகாப்பு பிரச்சனை' },
  'Flood warning / flood risk': { si: 'ගංවතුර අනතුරු ඇඟවීම / අවදානම', ta: 'வெள்ள எச்சரிக்கை / அபாயம்' },
  'Landslide warning / slope-failure risk': { si: 'නායයෑම් අනතුරු ඇඟවීම / අවදානම', ta: 'மண்சரிவு எச்சரிக்கை / அபாயம்' },
}

export function translateQuestion(text: string, lang: Lang): string {
  if (lang === 'en' || !text) return text
  const exact = QUESTIONS[text.trim()]
  if (exact) return exact[lang]
  for (const [prefix, t] of PREFIXES) {
    if (text.startsWith(prefix)) return t[lang]
  }
  return text
}

export function translateOption(label: string, lang: Lang): string {
  if (lang === 'en') return label
  return OPTIONS[label]?.[lang] ?? label
}

/*
  Notes shown under "Good to know".
  Some backend notes are written for developers; here they get a plain
  version for citizens. Notes in HIDDEN_NOTES are internal rules and are never shown.
*/
type T3 = { en: string; si: string; ta: string }

const NOTES: Record<string, T3> = {
  'Local-authority jurisdiction resolved from the DCS/GND geography backbone. Complaint-channel contact details are a separate verified layer.': {
    en: 'Your local council was found using official area maps.',
    si: 'ඔබේ ප්‍රාදේශීය සභාව හොයාගත්තේ නිල ප්‍රදේශ සිතියම් වලින්.',
    ta: 'உங்கள் உள்ளூராட்சி சபை அதிகாரப்பூர்வ பகுதி வரைபடங்களைக் கொண்டு கண்டறியப்பட்டது.',
  },
  'Jurisdiction resolved using the GND-level geography record.': {
    en: 'Found using your Grama Niladhari division.',
    si: 'ඔබේ ග්‍රාම නිලධාරී වසම අනුව හොයාගත්තා.',
    ta: 'உங்கள் கிராம அலுவலர் பிரிவின் அடிப்படையில் கண்டறியப்பட்டது.',
  },
  'Local authority selected by the user from the valid authorities for this DS area.': {
    en: 'You chose this council from the councils that serve your area.',
    si: 'ඔබේ ප්‍රදේශයට අයිති සභා අතරින් ඔබ මේ සභාව තෝරා ගත්තා.',
    ta: 'உங்கள் பகுதிக்குரிய சபைகளில் இருந்து இதை நீங்கள் தேர்ந்தெடுத்தீர்கள்.',
  },
  'Complaint concerns an SLTB-operated bus.': {
    en: 'This was an SLTB bus, so SLTB handles the complaint.',
    si: 'මේක SLTB බස් එකක් නිසා පැමිණිල්ල බලාගන්නේ SLTB එක.',
    ta: 'இது SLTB பேருந்து என்பதால் முறைப்பாட்டை SLTB கையாளும்.',
  },
  'Private bus route crosses provincial boundaries.': {
    en: 'The bus route crosses provincial boundaries.',
    si: 'බස් මාර්ගය පළාත් කිහිපයක් හරහා යනවා.',
    ta: 'பேருந்து வழித்தடம் மாகாண எல்லைகளைக் கடக்கிறது.',
  },
  'Private bus route remains within one province.': {
    en: 'The bus route stays within one province.',
    si: 'බස් මාර්ගය එක පළාතක් ඇතුළේ විතරයි.',
    ta: 'பேருந்து வழித்தடம் ஒரே மாகாணத்துக்குள் உள்ளது.',
  },
  'Operator type is unknown. NTC is used as a verified complaint intake route; NTC can forward provincial-bus and SLTB complaints to the appropriate body.': {
    en: 'Since you’re not sure who runs the bus, the National Transport Commission takes the complaint and passes it to the right body.',
    si: 'බස් එක ධාවනය කරන්නේ කවුද කියලා විශ්වාස නැති නිසා, ජාතික ගමනාගමන කොමිෂන් සභාව පැමිණිල්ල භාරගෙන නිවැරදි ආයතනයට යොමු කරනවා.',
    ta: 'பேருந்தை யார் இயக்குகிறார்கள் என்று தெரியாததால், தேசிய போக்குவரத்து ஆணைக்குழு முறைப்பாட்டைப் பெற்று சரியான நிறுவனத்திற்கு அனுப்பும்.',
  },
  'CAA FAQ states that written complaints seeking redress should be supported by relevant documents and forwarded within the time specified by the Act; the FAQ currently states within 3 months.': {
    en: 'Send your written complaint with supporting documents within 3 months (Consumer Affairs Authority FAQ).',
    si: 'ලිඛිත පැමිණිල්ල අදාළ ලේඛන සමඟ මාස 3ක් ඇතුළත යවන්න (පාරිභෝගික කටයුතු අධිකාරියේ FAQ අනුව).',
    ta: 'எழுத்துமூல முறைப்பாட்டை ஆவணங்களுடன் 3 மாதங்களுக்குள் அனுப்புங்கள் (நுகர்வோர் விவகார அதிகாரசபை FAQ).',
  },
  'Only preserve screenshots, photos, vehicle numbers, messages or other evidence when it is safe to do so.': {
    en: 'Only keep screenshots, photos, vehicle numbers or messages if it is safe to do so.',
    si: 'ආරක්ෂිත නම් විතරක් screenshots, photos, වාහන අංක, messages වගේ සාක්ෂි තියාගන්න.',
    ta: 'பாதுகாப்பாக இருந்தால் மட்டுமே screenshots, புகைப்படங்கள், வாகன இலக்கங்கள், செய்திகளை வைத்திருங்கள்.',
  },
}

const HIDDEN_NOTES = new Set(['Do not invent a business remedy, legal outcome, or compensation amount.'])

/** Returns the note for users, or null if it should not be shown. */
export function translateNote(note: string, lang: Lang): string | null {
  const text = note.trim()
  if (HIDDEN_NOTES.has(text)) return null
  return NOTES[text]?.[lang] ?? text
}
