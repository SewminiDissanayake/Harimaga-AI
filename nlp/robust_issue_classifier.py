import re
from nlp.issue_classifier import HybridIssueClassifier


class RobustIssueClassifier:
    """
    HariMaga robust wrapper.

    Safety fix v1.3:
      - supports karadara / kradara spelling variants
      - supports karanawa / kranawa / karanwa / krnawa variants
      - keeps safety intent ahead of the base classifier
      - preserves previous road/electricity/bus/consumer/lost-document fixes
    """

    ROAD_PATTERNS = [
        r"\bpara\b", r"\bpare\b", r"\bparata\b", r"\broad\b",
        r"\bmargaya\b", r"\bmaargaya\b", r"පාර", r"මාර්ග",
    ]
    ROAD_DAMAGE_PATTERNS = [
        r"\bwalak\b", r"\bwala\b", r"\bpothole\b", r"\bkadila\b",
        r"\bbroken\b", r"\bdamaged\b", r"\bmada\b", r"වල", r"කැඩ", r"මඩ",
    ]

    ELECTRICITY_STRONG_PATTERNS = [
        r"\bcurrent\s*(?:eka\s*)?(?:na|ne|naha|nae|nane)\b",
        r"\bkarant\s*(?:eka\s*)?(?:na|ne|naha|nae|nane)\b",
        r"\bcurrent\s*(?:eka\s*)?(?:giya|gihin|kapala|cut)\b",
        r"\bkarant\s*(?:eka\s*)?(?:giya|gihin|kapala|cut)\b",
        r"\bpower\s*(?:eka\s*)?(?:na|ne|naha|nae|nane|cut|out|outage)\b",
        r"\belectricity\s*(?:eka\s*)?(?:na|ne|naha|nae|nane|out|outage)\b",
        r"\b(?:apita|gedara|gewalata|gewal\s*walata)\s+light\s*(?:na|ne|naha|nae|nane)\b",
        r"විදුලිය\s*(?:නෑ|නැහැ)", r"කරන්ට්\s*(?:නෑ|නැහැ)", r"ගෙදර\s*ලයිට්\s*(?:නෑ|නැහැ)",
    ]
    STREET_LIGHT_EXCLUSIONS = [
        r"\bstreet\s*light\b", r"\bstreetlight\b", r"\blamp\s*post\b",
        r"\bpare\s+light\b", r"\bpara\s+light\b", r"වීදි\s*ලාම්පු", r"පාරේ\s*ලයිට්",
    ]

    BUS_CONTEXT_PATTERNS = [r"\bbus\b", r"බස්"]
    BUS_COMPLAINT_PATTERNS = [
        r"\benne\s*(?:na|ne|naha|nae|nane)\b",
        r"\bwada\s*karanne\s*(?:na|ne|naha|nae|nane)\b",
        r"\bduwanne\s*(?:na|ne|naha|nae|nane)\b",
        r"\bnawaththanne\s*(?:na|ne|naha|nae|nane)\b",
        r"\blate\b", r"\bdelay\b",
        r"\bticket\s*(?:dunne|denne)\s*(?:na|ne|naha|nae|nane)\b",
        r"\bbalance\s*(?:dunne|denne)\s*(?:na|ne|naha|nae|nane)\b",
        r"\bfare\s*(?:wadi|wrong|extra)\b", r"\bsalli\s*wadi\b",
        r"\bconductor\b", r"\bdriver\b", r"\breckless\b", r"\bdangerous\b",
        r"\bspeed\b", r"\bovercrowd", r"ටිකට්", r"කොන්දොස්තර", r"රියදුරු",
    ]

    CONSUMER_CONTEXT_PATTERNS = [
        r"\bshop\b", r"\bstore\b", r"\bseller\b", r"\bbusiness\b",
        r"\bproduct\b", r"\bitem\b", r"\bservice\b", r"\bonline\s*order\b",
        r"\bwarranty\b", r"\brefund\b", r"\breplace", r"\breceipt\b",
        r"\bprice\b", r"\bexpired\b", r"\bkade\b", r"\bkaden\b", r"\bbadu\b",
        r"කඩ", r"භාණ්ඩ", r"වොරන්ටි",
    ]
    CONSUMER_PROBLEM_PATTERNS = [
        r"\bwadi\s*ganak\b", r"\bsalli\s*wadi\b", r"\bprice\s*wadi\b",
        r"\bovercharg", r"\bwrong\s*price\b",
        r"\brefund\s*(?:denne|dunne|karanne)\s*(?:na|ne|naha|nae|nane)\b",
        r"\breplace(?:ment)?\s*(?:denne|dunne|karanne)\s*(?:na|ne|naha|nae|nane)\b",
        r"\bwarranty\s*(?:ganne|accept|honour|honor|denne)\s*(?:na|ne|naha|nae|nane)\b",
        r"\bkadila\b", r"\bbroken\b", r"\bdefect", r"\bexpired\b",
        r"\bfake\b", r"\bmislead",
        r"\bonline\s*order.*(?:awe|awa|enne)\s*(?:na|ne|naha|nae|nane)\b",
    ]

    LOST_DOCUMENT_CONTEXT = [
        r"\bnic\b", r"\bid\s*card\b", r"\bidentity\s*card\b",
        r"\bid\s*(?:eka|ek)?\b",
        r"\blicen[cs]e\b", r"\bdriving\s*licen[cs]e\b",
        r"\bpassport\b", r"\bpaasport\b",
        r"\bhadunumpatha\b", r"\bhadunum\s*patha\b",
        r"හැඳුනුම්පත", r"රියදුරු\s*බලපත්", r"පාස්පෝට්",
        # v10
        r"\bbirth\s+certificate\b", r"\buppanna\b", r"උප්පැන්න",
        r"அடையாள\s*அட்டை", r"கடவுச்சீட்டு", r"உரிமம்",
    ]
    LOST_DOCUMENT_SIGNALS = [
        r"\bnathi\s*(?:una|wela|wuna|welaa)\b", r"\bnathi\b",
        r"\bhoyaganna\s*(?:ba|be|bae)\b", r"\blost\b", r"\bmissing\b",
        r"\bstolen\b", r"\bhorakam\b", r"\bhorakan\b",
        r"නැති", r"හොයාගන්න\s*බෑ", r"නැතිවෙලා", r"හොරකම්",
        # v10
        r"\bnathi\s*una\b", r"\bnathiuna\b",
        r"தொலை", r"காணவில்லை", r"திருட",
    ]

    ACTION_KARANAWA = r"(?:karanawa|kranawa|karanwa|krnawa)"
    KARADARA = r"(?:karadara|kradara)"

    WOMEN_CHILD_SAFETY_PATTERNS = [
        # Following / stalking
        rf"\b(?:mawa|mwa|mata|mt)\b.*\bfollow(?:ing)?\b.*\b{ACTION_KARANAWA}\b",
        rf"\bfollow(?:ing)?\b.*\b(?:mawa|mwa|mata|mt)\b.*\b{ACTION_KARANAWA}\b",
        rf"\b(?:kenek|ekkena|ekkenek|manussayek|manussyek|minihek)\b.*\bfollow(?:ing)?\b.*\b{ACTION_KARANAWA}\b",
        r"\bstalk(?:ing|er|ed)?\b",
        r"\bfollow\s+someone\b",

        # Harassment spelling variants
        r"\bhar+as+h?ment\b",
        r"\bharass(?:ment|ed|ing)?\b",
        r"\bharras(?:ment|ed|ing)?\b",
        r"\bharash(?:ment|ed|ing)?\b",
        r"\bsexual\b.*\bhar",
        r"\bsexual\s+abuse\b",

        # General bothering / harassment
        rf"\b(?:mawa|mwa|mata|mt)\b.*\b{KARADARA}\s+{ACTION_KARANAWA}\b",
        rf"\b(?:kenek|ekkena|ekkenek|manussayek|manussyek|minihek)\b.*\b{KARADARA}\s+{ACTION_KARANAWA}\b",
        rf"\b{KARADARA}\s+{ACTION_KARANAWA}\b.*\b(?:mawa|mwa|mata|mt)\b",
        rf"\b(?:manussayek|manussyek|kenek|ekkena)\b\s+{KARADARA}\s+{ACTION_KARANAWA}\b",

        # Physical / sexual threat
        r"\bbalen\s+allanawa\b",
        rf"\btouch\s+{ACTION_KARANAWA}\b",
        # Fix v9: "threat" alone matched "flood threat" and
        # "threatening to cut trees". Now a person must be the target.
        r"\bthreat(?:en|ens|ened|ening)\s+(?:me|us|my|her|him|them|our)\b",
        r"\bthreat(?:en|ens|ened|ening)\s+to\s+(?:kill|hurt|harm|beat|attack|rape)\b",
        r"\b(?:death|rape|kill)\s+threats?\b",
        r"\bassault(?:ed|ing)?\b",
        r"\bdomestic\s+violence\b",
        r"\bgedara\s+gahenawa\b",

        # Child abuse / neglect / exploitation
        r"\bchild\s+abus(?:e|ed|ing)\b",
        r"\bchild\s+neglect(?:ed|ing)?\b",
        r"\bchild\s+exploit(?:ation|ed|ing)?\b",
        r"\bchild\s+labou?r\b",
        rf"\b(?:lamaya|lamayek|lamayata|lamek|podi\s+lamayek)\b.*\b{KARADARA}\b",
        r"\b(?:lamaya|lamayek|lamayata|lamek)\b.*\babus",
        rf"\blamayekta\s+{KARADARA}\b",
        rf"\blamayata\s+{KARADARA}\b",

        # Singlish hitting a person
        r"\b(?:mata|mta|apita|lamayata|lamayinta|daruwata|daruwanta|birindata|ammata)\s+(?:\w+\s+)?gahanawa\b",

        # v10: English
        r"\bfollow(?:s|ing)?\s+(?:me|her|my\s+(?:daughter|son|child|wife|sister))\b",
        r"\bbeat(?:s|ing)?\s+(?:me|her|his|their|my|the)\s*(?:wife|children|kids|child|daughter|son)?\b",
        r"\b(?:hits?|hitting)\s+(?:me|her|my|his)\b",
        r"\bthreatening\s+(?:messages?|calls?|me)\b",
        r"\b(?:inappropriately|molest\w*|grop\w*)\b",
        r"\bchild(?:ren)?\b.*\b(?:work|labou?r)\b|\b(?:work|labou?r)\b.*\bchild(?:ren)?\b",

        # v10: Singlish: a family member / someone hitting or scaring
        r"\b(?:husband|aya|thaththa|appachchi|appa|amma|mahaththaya|kenek)\b.*\bgahanawa\b",
        r"\b(?:baya\s*karanawa|bayakaranawa|bayanawa|threaten\s+karanawa)\b",
        r"\b(?:lamai|lamayi|lamaya|lamayek|podi\s+lamayek)\b.*\bwada(?:ta|\s+karanawa)\b",
        r"\bharassment\s+karanawa\b",

        # Sinhala
        # Fix v9: bare "ගහනවා" matched "වැස්ස ගහනවා" (it's raining).
        # Now hitting must be aimed at a person.
        r"හිරිහැර", r"අපයෝජන", r"පසුපස\s*එනවා",
        r"(?:මට|මාව|අපිට|ළමයාට|ළමයින්ට|දරුවාට|දරුවන්ට|බිරිඳට|අම්මට)\s*(?:\S+\s+)?ගහනවා",
        # v10
        r"(?:සැමියා|ස්වාමිපුරුෂයා|මහත්තයා).*ගහනවා",
        r"තර්ජනය",
        r"(?:ළමයෙක්|ළමයින්|දරුවන්|ළමයි).*වැඩට",

        # v10: Tamil (please have a native speaker review)
        r"பின்தொடர்",      # following / stalking
        r"அடிக்கிற",        # hitting (a person)
        r"துன்புறுத்",      # harassing
        r"வன்முறை",        # violence
        r"சிறுவர்.*வேலை",   # child labour
    ]

    # Fix v9: open burning of plastic / garbage is an environment issue.
    OPEN_BURNING_PATTERNS = [
        r"\bburn(?:s|ing|ed|t)?\s+(?:\w+\s+)?(?:plastic|garbage|rubbish|waste|tyres?|tires?|polythene)\b",
        r"\bopen\s+burning\b",
        r"\b(?:plastic|kunu|polythene)\s+(?:\w+\s+)?(?:pulussanawa|pichchanawa|gini\s+thiyanawa)\b",
        r"(?:ප්ලාස්ටික්|කුණු|පොලිතීන්)\s*(?:\S+\s+)?(?:පුළුස්සනවා|පිච්චනවා)",
    ]

    FLOOD_PATTERNS = [
        r"\bflood\b", r"\bflooded\b",
        r"\bwathura\s+gahala\b", r"\bwathura\s+pirila\b",
        r"\bwathurata\s+yata\s+wela\b",
        r"\bganga\s+pita\s+dala\b", r"\bganga\s+us\s+wela\b",
        r"\bflood\s+warning\b",
        r"ගංවතුර", r"වතුරට\s*යට", r"ගඟ\s*පිටාර",
        # v10
        r"\briver\b.*\b(?:rising|overflow\w*|burst)\b", r"\bwater\s+level\b.*\b(?:high|rising)\b",
        r"\b(?:heavy\s+rain|wessa|wesse|wahina|wahinawa)\b.*\b(?:gewal|gedara)\b.*\bwathura\b",
        r"\b(?:heavy\s+rain|wessa|wesse|wahina|wahinawa)\b.*\bwathura\b.*\b(?:gewal|gedara)\b",
        r"வெள்ள",           # Tamil: flood
    ]

    LANDSLIDE_PATTERNS = [
        r"\blandslide\b", r"\bland\s*slide\b",
        r"\bnaaya\s*y", r"\bnaya\s*y",
        r"\bpas\s+kanda\s+bihinawa\b",
        r"\bpas\s+kanda\s+kadila\b",
        r"\bgal\s+peralenawa\b", r"\bground\s+crack",
        r"\bslope\s+fail", r"\blandslide\s+warning\b",
        r"නායයෑ", r"පස්\s*කන්ද", r"ගල්\s*පෙරළ",
        # v10
        r"\bcracks?\b.*\b(?:hill|slope|mountain|ground)\b",
        r"(?:කන්ද|කන්දේ).*(?:කඩා|නාය|ඉරිතැල)", r"පස්\s*කඩා",
        r"மண்சரிவு",        # Tamil: landslide
    ]

    def __init__(self, *args, **kwargs):
        self.base = HybridIssueClassifier(*args, **kwargs)

    @staticmethod
    def _contains_any(text, patterns):
        return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)

    @staticmethod
    def _low_or_unknown(result):
        return (
            result.get("label") == "unknown_government_issue"
            or float(result.get("confidence", 0.0) or 0.0) < 0.50
        )

    # v10: the ML model now knows the safety category. If it gives safety at
    # least this probability, route to safety even if another label won:
    # missing a safety case costs far more than a false alarm.
    SAFETY_ML_THRESHOLD = 0.30

    def _ml_safety_probability(self, text):
        model = self.base.model
        classes = list(model.classes_)
        if "women_child_safety" not in classes:
            return 0.0
        return float(model.predict_proba([text])[0][classes.index("women_child_safety")])

    def predict(self, text):
        normalized = " ".join(str(text or "").strip().lower().split())

        if self._contains_any(normalized, self.WOMEN_CHILD_SAFETY_PATTERNS):
            return {
                "label": "women_child_safety",
                "confidence": 0.98,
                "method": "high_precision_safety_rule_v6_3",
            }

        if self._contains_any(normalized, self.FLOOD_PATTERNS):
            return {
                "label": "disaster_alert",
                "confidence": 0.98,
                "method": "high_precision_flood_rule_v6",
                "disaster_subtype": "flood_alert",
            }

        if self._contains_any(normalized, self.LANDSLIDE_PATTERNS):
            return {
                "label": "disaster_alert",
                "confidence": 0.98,
                "method": "high_precision_landslide_rule_v6",
                "disaster_subtype": "landslide_alert",
            }

        lost_document = (
            self._contains_any(normalized, self.LOST_DOCUMENT_CONTEXT)
            and self._contains_any(normalized, self.LOST_DOCUMENT_SIGNALS)
        )
        if lost_document:
            return {
                "label": "lost_document",
                "confidence": 0.97,
                "method": "high_precision_lost_document_rule_v5_2",
            }

        if self._contains_any(normalized, self.OPEN_BURNING_PATTERNS):
            return {
                "label": "environment_issue",
                "confidence": 0.95,
                "method": "high_precision_open_burning_rule_v9",
            }

        result = self.base.predict(text)

        safety_p = self._ml_safety_probability(text)
        if result.get("label") != "women_child_safety" and safety_p >= self.SAFETY_ML_THRESHOLD:
            return {
                "label": "women_child_safety",
                "confidence": round(safety_p, 3),
                "method": "ml_safety_bias_v10",
                "other_label": result.get("label"),
            }

        strong_bus = (
            self._contains_any(normalized, self.BUS_CONTEXT_PATTERNS)
            and self._contains_any(normalized, self.BUS_COMPLAINT_PATTERNS)
        )
        if strong_bus and self._low_or_unknown(result):
            return {"label":"bus_complaint","confidence":0.96,"method":"high_precision_bus_rule_v3"}

        strong_consumer = (
            self._contains_any(normalized, self.CONSUMER_CONTEXT_PATTERNS)
            and self._contains_any(normalized, self.CONSUMER_PROBLEM_PATTERNS)
        )
        if strong_consumer and self._low_or_unknown(result):
            return {"label":"consumer_complaint","confidence":0.96,"method":"high_precision_consumer_rule_v4"}

        strong_electricity = self._contains_any(normalized, self.ELECTRICITY_STRONG_PATTERNS)
        street = self._contains_any(normalized, self.STREET_LIGHT_EXCLUSIONS)
        if strong_electricity and not street and self._low_or_unknown(result):
            return {"label":"electricity_issue","confidence":0.96,"method":"high_precision_electricity_rule_v2"}

        strong_road = (
            self._contains_any(normalized, self.ROAD_PATTERNS)
            and self._contains_any(normalized, self.ROAD_DAMAGE_PATTERNS)
        )
        if strong_road and self._low_or_unknown(result):
            return {"label":"road_issue","confidence":0.96,"method":"high_precision_road_rule_v2"}

        return result
