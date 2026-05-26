"""
RGE Data Export Compliance Advisor — Streamlit App
====================================================
Run with:  streamlit run rge_compliance_advisor_streamlit.py
"""

import re
import streamlit as st

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="RGE Data Export Compliance Advisor",
    page_icon="📊",
    layout="wide",
)

# ─────────────────────────────────────────────
# CUSTOM CSS  (mirrors the HTML colour scheme)
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── global typography ─────────────────────────── */
html, body, [class*="css"] { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }

/* ── header banner ─────────────────────────────── */
.rge-header {
    background: linear-gradient(135deg, #1a365d, #2c5282);
    color: white;
    padding: 22px 32px;
    border-radius: 10px;
    margin-bottom: 24px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.18);
}
.rge-header h1 { font-size: 1.65rem; font-weight: 700; margin: 0 0 4px 0; }
.rge-header p  { font-size: 0.9rem;  opacity: 0.85; margin: 0; }

/* ── result boxes ───────────────────────────────── */
.box-green  { background:#f0fff4; border:1px solid #c6f6d5; border-radius:10px; padding:18px 22px; margin-top:12px; }
.box-yellow { background:#fffff0; border:1px solid #fefcbf; border-radius:10px; padding:18px 22px; margin-top:12px; }
.box-red    { background:#fff5f5; border:1px solid #fed7d7; border-radius:10px; padding:18px 22px; margin-top:12px; }
.box-blue   { background:#ebf8ff; border:1px solid #bee3f8; border-radius:10px; padding:18px 22px; margin-top:12px; }

/* ── badges ─────────────────────────────────────── */
.badge        { display:inline-block; padding:2px 10px; border-radius:12px; font-size:0.8rem; font-weight:700; margin-right:6px; }
.badge-green  { background:#c6f6d5; color:#22543d; }
.badge-yellow { background:#fefcbf; color:#744210; }
.badge-red    { background:#fed7d7; color:#742a2a; }
.badge-blue   { background:#bee3f8; color:#2a4365; }

/* ── section headings ───────────────────────────── */
.section-title { font-size:0.97rem; font-weight:700; color:#1a365d; margin:14px 0 5px 0; }

/* ── country card (audit tab) ───────────────────── */
.country-card {
    border-left: 4px solid #1a365d;
    padding: 14px 18px;
    background: #f7fafc;
    border-radius: 0 8px 8px 0;
    margin-bottom: 14px;
}
.country-card h4 { color:#1a365d; margin:0 0 8px 0; font-size:1.05rem; }

/* ── update flags ───────────────────────────────── */
.flag-red    { background:#fff5f5; border:1px solid #fc8181; color:#742a2a; padding:7px 12px; border-radius:6px; font-size:0.87rem; margin-bottom:7px; }
.flag-yellow { background:#fef3c7; border:1px solid #f59e0b; color:#92400e; padding:7px 12px; border-radius:6px; font-size:0.87rem; margin-bottom:7px; }
.flag-green  { background:#f0fff4; border:1px solid #68d391; color:#22543d; padding:7px 12px; border-radius:6px; font-size:0.87rem; margin-bottom:7px; }

/* ── penalty box ────────────────────────────────── */
.penalty-box { background:#fff5f5; border-left:4px solid #e53e3e; padding:12px 16px; border-radius:0 8px 8px 0; margin:8px 0; font-size:0.9rem; }

/* ── disclaimer ─────────────────────────────────── */
.disclaimer { background:#edf2f7; padding:12px 16px; border-radius:8px; font-size:0.82rem; color:#718096; margin-top:22px; }

/* ── hide streamlit default footer/menu ─────────── */
#MainMenu {visibility:hidden;} footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# KNOWLEDGE BASE
# ─────────────────────────────────────────────
KB = {
    "indonesia": {
        "name": "Indonesia", "flag": "🇮🇩",
        "legislation": ["PDP Law No. 27/2022","GR 71/2019","MOCD Reg 20/2016","GI Law (Law 4/2011)","Marine Law (Law 32/2014)","MEMR Reg 7/2019"],
        "server_locations": {"Emails":"Local Indonesia (migrating to MS 365 Singapore)","Legal":"Onsite Indonesia","Financial":"Hong Kong","HR":"Ireland (Workday) + Local Indonesia"},
        "data_types": {
            "personal":   {"restricted":True,  "conditions":["Adequacy of Protection: destination has equal or higher PDP protection","Appropriate Safeguards: if no adequacy, binding safeguards must be in place","Consent: if neither adequacy nor safeguards, prior consent from data subject required","MOCD Filing: (a) planned transfer report, (b) advocacy request if needed, (c) implementation report"],"notes":"No official adequacy list issued by the PDP Agency (not yet operational, May 2026). RPP PDP implementing regulation remains unfinalized. Employee consent obtained for Workday processing.","rge_status":"RGE Indonesian entities have obtained employee consent for HR data on Workday (Ireland). Other HR data (ID cards, tax numbers, etc.) stored locally."},
            "hr":         {"restricted":True,  "conditions":["Same conditions as personal data apply","Employee consent required for collection, processing, storage and use","HR data on Workday (Ireland) requires cross-border transfer compliance"],"notes":"RGE Indonesia stores some HR data locally (ID cards, family cards, tax IDs, diplomas, BPJS, bank details, medical records, fingerprints, face recognition) and processes other HR data on Workday in Dublin.","rge_status":"Consent obtained from employees. Local data kept on local server and IKM."},
            "geospatial": {"restricted":True,  "conditions":["GI Law applies to entities with licenses to collect/process geospatial data","The GI Law is silent on use of PROCESSED geospatial data by third parties including export","If RGE entities hold collection/processing licenses, governmental approval may be required"],"notes":"The GI Law primarily regulates licensed collectors/processors. Silent on third-party use of processed data. Plantation geospatial data should be assessed case-by-case.","rge_status":"Focal points indicated GI Laws are primarily relevant to licensed collectors/processors. Silence on third-party use of processed data."},
            "financial":  {"restricted":False, "conditions":["Financial data currently stored in Hong Kong","General PDP Law applies if financial data contains personal data"],"notes":"Banking sector data localisation rules only apply to commercial banks — not applicable to RGE.","rge_status":"Financial data stored in Hong Kong. Banking sector restrictions not applicable."},
            "email":      {"restricted":True,  "conditions":["Emails on local server in Indonesia","Migration planned to Microsoft 365 (Singapore server)","If emails contain personal data, PDP Law cross-border transfer rules apply","Caching on local server may mitigate some concerns"],"notes":"Migration to MS 365 Singapore means personal data in emails will be transferred cross-border. PDP Law compliance required.","rge_status":"Currently local. Migration to MS 365 Singapore planned — PDP Law compliance needed for personal data in emails."},
            "legal":      {"restricted":False, "conditions":["Legal data stored on onsite server in Indonesia","PDP Law applies if legal data contains personal data"],"notes":"Currently stored locally. No cross-border transfer issues unless legal data is moved offshore.","rge_status":"Stored locally in Indonesia."},
            "sensitive":  {"restricted":True,  "conditions":["PDP Law classifies health, biometric, genetic, criminal records, children's data, financial data as 'specific personal data'","Higher protection standards apply","All cross-border transfer conditions for personal data apply with additional scrutiny"],"notes":"Specific personal data receives heightened protection under the PDP Law.","rge_status":"Health check-up results, fingerprints, and face recognition data stored locally."},
            "business":   {"restricted":False, "conditions":["General business data not restricted unless it contains personal data or falls into regulated categories (geospatial, marine, oil & gas)"],"notes":"Non-personal business data can generally be exported freely unless in a regulated category.","rge_status":"No specific restrictions identified."},
            "important":  {"restricted":False, "conditions":["Not a China-specific concept in Indonesian law"],"notes":"This category is specific to Chinese law. Not applicable to Indonesia.","rge_status":"N/A"},
        },
        "penalties": "Administrative fines up to 2% of annual revenue. Criminal sanctions: monetary penalties (up to 10x max for entities), asset seizure, business suspension/closure, licence revocation, liquidation. At least 23 criminal cases prosecuted under PDP Law.",
        "galexy": "Yes — Galexy use is compliant with Indonesian data residency/export laws.",
    },
    "china": {
        "name": "China", "flag": "🇨🇳",
        "legislation": ["Cybersecurity Law (CSL, amended Jan 2026)","Data Security Law (DSL)","Personal Information Protection Law (PIPL)","Provisions on Promoting and Regulating Cross-Border Data Flows","CAC Order No. 11 (Security Assessment)","CAC Order No. 13 (SCCs)","Measures for Certification of Cross-Border PI Transfer (Jan 2026)"],
        "server_locations": {"Emails":"China","Legal":"China","Financial":"Hong Kong","HR":"Ireland (Workday)"},
        "data_types": {
            "personal":   {"restricted":True,  "conditions":["Non-CIIO: PI of <100K individuals (non-sensitive) generally exempt from formal mechanisms but must still comply with PIPL","100K–1M individuals (non-sensitive) OR <10K individuals (sensitive): SCCs or Certification required",">1M individuals (non-sensitive) OR >10K individuals (sensitive): mandatory Security Assessment","CIIOs: always require Security Assessment regardless of volume","All transfers require: consent, PI Protection Impact Assessment, notification to data subjects"],"notes":"RGE Chinese entities are NOT CIIOs. Total HR data exceeds 10,000 individuals but qualifies for the HR management exemption under Art 5(1)(b). CAUTION: Oct 2025 CAC FAQ narrows this exemption — higher-risk PI (ID numbers, passport info, bank accounts) should not be transferred without verifying necessity.","rge_status":"HR exemption applies but must be narrowly applied. Higher-risk employee PI should be carefully assessed before transfer."},
            "hr":         {"restricted":True,  "conditions":["HR management exemption under Art 5(1)(b) of Cross-Border Provisions applies","Must be under lawfully formulated employment rules/policies or collective contracts","Transfer must be NECESSARY for HR management purposes","Scope limited to PI DIRECTLY RELEVANT to HR management","Should minimise impact on employees","Higher-risk PI (ID, passport, bank info) requires additional necessity assessment"],"notes":"The Oct 2025 CAC FAQ emphasises this exemption is narrowly construed. Only transfer what is necessary. Do not bulk-transfer sensitive employee data without justification.","rge_status":"RGE China entities use Workday (Ireland) for HR. Exemption applies but scope must be carefully managed."},
            "financial":  {"restricted":False, "conditions":["Financial data stored in Hong Kong","If financial data contains personal information, PIPL cross-border rules apply","Personal credit data restrictions only apply to credit reporting agencies — not applicable to RGE"],"notes":"Hong Kong is outside mainland China, so transfer of financial data containing PI is a cross-border transfer under PIPL.","rge_status":"Financial data stored in Hong Kong. Credit data restrictions not applicable."},
            "important":  {"restricted":True,  "conditions":["Important data may ONLY be exported via Security Assessment (most stringent pathway)","Definition: data that if compromised may endanger national security, economic operation, social stability, public health/safety","If relevant authority has NOT notified data as 'important', it need not be declared as such","CCGT power plant and LNG terminal data COULD potentially qualify, but no notification received to date"],"notes":"RGE China legal team confirms: no Business Unit has received notification requiring data to be managed as Important Data. Monitor for future policy adjustments or publication of Important Data catalogues.","rge_status":"Currently not involved in processing Important Data based on self-assessment. Monitor for changes."},
            "geospatial": {"restricted":False, "conditions":["Not specifically regulated under China's data export framework for RGE's operations","General PIPL/DSL rules apply if data contains PI or important data"],"notes":"China's geospatial data restrictions primarily affect surveying and mapping activities. General data security rules apply.","rge_status":"No specific restrictions identified for RGE operations."},
            "email":      {"restricted":True,  "conditions":["Emails stored in China","If emails contain personal information, PIPL cross-border rules apply for any transfer outside China","Internal emails should not be exported without compliance assessment"],"notes":"Email servers are in China. Any transfer of email data containing PI outside China must comply with PIPL.","rge_status":"Emails stored locally in China."},
            "legal":      {"restricted":True,  "conditions":["Legal data stored in China","Data stored in China requested by foreign judicial/law enforcement cannot be provided without approval","Specific determinations based on actual circumstances of each case"],"notes":"Article 36 of the DSL prohibits providing data stored in China to foreign judicial or law enforcement without approval from competent Chinese authorities.","rge_status":"Legal data stored locally in China. Cannot be provided to foreign judicial/law enforcement without approval."},
            "sensitive":  {"restricted":True,  "conditions":["Sensitive PI includes: biometric, religious, medical/health, financial, location data, and PI of minors under 14","Separate consent required for processing sensitive PI","Stricter thresholds for cross-border transfer: >10,000 individuals requires Security Assessment","PI Protection Impact Assessment mandatory before processing"],"notes":"Higher scrutiny and lower volume thresholds for cross-border transfer of sensitive PI.","rge_status":"Assess all sensitive PI transfers carefully."},
            "business":   {"restricted":False, "conditions":["General business data not restricted unless classified as 'important data' or contains PI","No notification received classifying RGE business data as important"],"notes":"Non-personal, non-important business data can generally be transferred freely.","rge_status":"No specific restrictions for general business data."},
        },
        "penalties": "DSL Art 46: RMB 100K–1M (serious: RMB 1M–10M + suspension/revocation). PIPL Art 66: up to RMB 50M or 5% of prior year's turnover; director bans. CSL (amended Jan 2026): up to RMB 10M (10x increase); personal fines up to RMB 1M; no 'warning first' requirement; broadened extraterritorial enforcement. Leniency framework available for voluntary remediation.",
        "galexy": "Yes — Galexy use is compliant.",
    },
    "brazil": {
        "name": "Brazil", "flag": "🇧🇷",
        "legislation": ["LGPD (Law 13.709/2018)","Resolução CD/ANPD nº 19/2024","Decreto nº 6.666/2008 (updated by Decreto 12.402/2025)","Portaria Secex nº 65/2020"],
        "server_locations": {"Emails":"Brazil","Legal":"Brazil","Financial":"Brazil","HR":"Ireland (Workday)"},
        "data_types": {
            "personal":   {"restricted":True,  "conditions":["Adequacy decision by ANPD (none issued yet for any country)","Standard Contractual Clauses (ANPD-approved model, Annex II of Resolução 19/2024) — compliance deadline was 23 Aug 2025","Binding Corporate Rules (BCRs) for intra-group transfers","Specific contractual clauses (for exceptional cases)","Data subject consent","Legal/regulatory obligations, contract performance, legal proceedings"],"notes":"ANPD has NOT issued any adequacy decisions yet. Most transfers must rely on SCCs (now mandatory to use ANPD-approved model), BCRs, or consent. Brazilian law mandates onshore retention of original physical documents (civil: 10 years, tax: 5 years).","rge_status":"Brazil will use Netlex (not Galexy). Netlex server location should be confirmed."},
            "hr":         {"restricted":True,  "conditions":["Same conditions as personal data apply","HR data on Workday (Ireland) requires valid transfer mechanism","Employee consent and/or SCCs required","Physical document retention obligations in Brazil apply"],"notes":"HR data processed on Workday in Ireland. Must ensure ANPD-approved SCCs or other valid mechanism is in place.","rge_status":"HR data on Workday (Ireland). Transfer mechanism compliance needs confirmation."},
            "geospatial": {"restricted":True,  "conditions":["Decreto nº 6.666/2008 and Decreto nº 12.402/2025 regulate geospatial datasets","Prior authorisation may be required from: Ministry of Defense, IBGE/INDE (geospatial datasets), ANM (subsoil/mineral resources)","Approvals are case-specific based on nature and sensitivity"],"notes":"No blanket prohibition, but prior authorisation required when data involves geospatial, subsoil, or defense-sensitive information.","rge_status":"For Bracell, relevant if exported content includes engineering drawings, plant layouts, or proprietary process data (reportedly not the case)."},
            "financial":  {"restricted":True,  "conditions":["Financial data stored in Brazil","If containing personal data, LGPD transfer rules apply","Tax/fiscal records must be retained in Brazil for 5 years (CTN)"],"notes":"Financial records have onshore retention obligations under Brazilian tax law.","rge_status":"Financial data stored in Brazil. Retention obligations apply."},
            "email":      {"restricted":True,  "conditions":["Emails stored in Brazil","If emails contain personal data, LGPD cross-border rules apply"],"notes":"Email servers in Brazil. Cross-border transfer of email data with PI requires LGPD compliance.","rge_status":"Emails stored locally in Brazil."},
            "legal":      {"restricted":True,  "conditions":["Legal data stored in Brazil","Original physical documents must be retained onshore (Lei 8.159/1991)","Digital equivalents only valid if ICP-Brasil standards met (Decreto 10.278/2020)"],"notes":"Strong physical document retention requirements in Brazil.","rge_status":"Legal data stored locally in Brazil."},
            "business":   {"restricted":True,  "conditions":["Portaria Secex nº 65/2020 may restrict export of sensitive business information","Applies to technical documentation, industrial designs, proprietary process data","May require Siscomex administrative treatment and export licences for strategic/military tech","For Bracell: applies only if exporting engineering drawings, plant layouts, or proprietary process data"],"notes":"Bracell has confirmed this is currently not the case for their operations.","rge_status":"Not currently applicable to Bracell's operations."},
            "sensitive":  {"restricted":True,  "conditions":["LGPD Art 11 governs processing of sensitive data (health, biometric, genetic, racial/ethnic, religious, political, trade union, sex life)","Additional legal basis required beyond general grounds","All cross-border transfer conditions apply with heightened scrutiny"],"notes":"Sensitive data requires specific legal basis under Art 11 LGPD in addition to transfer mechanisms.","rge_status":"Assess all sensitive data transfers carefully."},
            "important":  {"restricted":False, "conditions":["Not a concept in Brazilian law"],"notes":"This category is specific to Chinese law. Not applicable to Brazil.","rge_status":"N/A"},
        },
        "penalties": "LGPD Art 52: Fines up to 2% of Brazil revenue, capped at BRL 50 million per violation. Daily fines. Public disclosure. Data blocking/deletion. Processing suspension/prohibition.",
        "galexy": "N/A — Brazil will use Netlex. Server location needs confirmation.",
    },
    "hongkong": {
        "name": "Hong Kong", "flag": "🇭🇰",
        "legislation": ["Personal Data (Privacy) Ordinance (PDPO, Cap. 486)","Protection of Critical Infrastructure Ordinance (Cap. 653, effective Jan 2026)"],
        "server_locations": {"Emails":"Hong Kong","Legal":"Hong Kong","Financial":"Hong Kong","HR":"Hong Kong"},
        "data_types": {
            "personal":   {"restricted":False, "conditions":["Section 33 (cross-border transfer restrictions) is NOT YET IN FORCE — no statutory prohibition on overseas transfers","Must comply with 6 Data Protection Principles (DPPs) regardless","DPP1: Collect fairly and lawfully for identified purpose","DPP3: Do not use for new purpose without prescribed consent","DPP4: Take all practicable steps to safeguard data (applies to overseas processors)","PCPD recommends: voluntary compliance with s.33 standards and use of Recommended Model Clauses (RMCs)","GBA Standard Contract available for transfers within Greater Bay Area (extended to all sectors Nov 2024)"],"notes":"Hong Kong currently has NO statutory restriction on cross-border data transfer. PCPD best practice guidance encourages voluntary compliance with s.33 standards. Most organisations use RMCs as a precaution.","rge_status":"All data (emails, legal, financial, HR) stored in Hong Kong. No cross-border transfer issues."},
            "hr":         {"restricted":False, "conditions":["Same as personal data — no statutory cross-border restriction","Must comply with DPPs","Inform data subjects of potential transfers at or before collection"],"notes":"HR data stored locally in Hong Kong. No cross-border transfer.","rge_status":"HR data stored in Hong Kong."},
            "financial":  {"restricted":False, "conditions":["No specific financial data export restrictions beyond DPPs","Banking sector regulations may apply to banks (not RGE)"],"notes":"Financial data stored in Hong Kong.","rge_status":"Financial data stored in Hong Kong."},
            "email":      {"restricted":False, "conditions":["No specific restrictions","DPPs apply if emails contain personal data"],"notes":"Emails stored in Hong Kong.","rge_status":"Emails stored in Hong Kong."},
            "legal":      {"restricted":False, "conditions":["No specific restrictions","DPPs apply if legal data contains personal data"],"notes":"Legal data stored in Hong Kong.","rge_status":"Legal data stored in Hong Kong."},
            "geospatial": {"restricted":False, "conditions":["No specific geospatial data export restrictions in Hong Kong"],"notes":"Not specifically regulated.","rge_status":"No restrictions identified."},
            "sensitive":  {"restricted":False, "conditions":["PDPO does not have a separate category for 'sensitive' personal data","All personal data treated equally under DPPs","Best practice dictates higher safeguards for health, biometric data"],"notes":"Unlike GDPR, PDPO does not distinguish sensitive data as a separate category.","rge_status":"Apply best practice safeguards."},
            "business":   {"restricted":False, "conditions":["No restrictions on business data export"],"notes":"Business data can be freely transferred.","rge_status":"No restrictions."},
            "important":  {"restricted":False, "conditions":["Not a concept in Hong Kong law"],"notes":"N/A","rge_status":"N/A"},
        },
        "penalties": "Enforcement notice breach: max HK$50,000 + 2 years imprisonment + HK$1,000/day (first conviction); HK$100,000 + 2 years + HK$2,000/day (subsequent). S.33 breach (when enacted): HK$10,000. Civil damages under s.66 PDPO.",
        "galexy": "Yes — Galexy use is compliant.",
    },
    "malaysia": {
        "name": "Malaysia", "flag": "🇲🇾",
        "legislation": ["Personal Data Protection Act 2010 (PDPA, amended 2024)","CBPDT Guidelines (29 April 2025)"],
        "server_locations": {"Emails":"Malaysia","Legal":"Malaysia","Financial":"Malaysia","HR":"Ireland (Workday)"},
        "data_types": {
            "personal":   {"restricted":True,  "conditions":["Destination has law 'substantially similar' to PDPA, OR","Destination ensures 'adequate level of protection' (at least equivalent to PDPA)","Transfer Impact Assessment (TIA) required — valid for 3 years","Alternative bases: data subject consent, contract performance, legal proceedings, vital interests","Due diligence mechanisms: BCRs, contractual clauses (ASEAN/EU SCCs), certifications (APEC CBPR, Europrivacy)","Must notify data subjects, use secure transfer methods, maintain transfer records","DPO appointment mandatory (from June 2025)","Data breach notification mandatory (from June 2025)"],"notes":"The CBPDT Guidelines (April 2025) provide comprehensive operational guidance. TIA must assess destination laws, enforcement, data subject rights, regulatory authority, security measures. Records of each transfer must be maintained.","rge_status":"HR managed on Workday (Ireland). Malaysia entities confirm compliance with requirements (consents, controls). No personal data exported to RGE Singapore."},
            "hr":         {"restricted":True,  "conditions":["Same conditions as personal data apply","HR data on Workday (Ireland) — valid transfer mechanism required","TIA for Ireland as destination should be conducted","Employee consent and/or contractual safeguards needed"],"notes":"Malaysia HR confirms compliance with PDPA requirements for Workday (Ireland) processing. No personal data exported to RGE Singapore.","rge_status":"Workday (Ireland) in use. Compliance confirmed."},
            "financial":  {"restricted":True,  "conditions":["Financial data stored in Malaysia","If containing personal data, PDPA cross-border rules apply","Banking/insurance sector entities have additional registration requirements"],"notes":"Financial data stored locally. Banking sector requirements only apply to banks.","rge_status":"Financial data stored in Malaysia."},
            "email":      {"restricted":True,  "conditions":["Emails stored in Malaysia","If emails contain personal data, PDPA cross-border rules apply for any transfer"],"notes":"Emails stored locally.","rge_status":"Emails stored in Malaysia."},
            "legal":      {"restricted":True,  "conditions":["Legal data stored in Malaysia","PDPA applies if containing personal data"],"notes":"Legal data stored locally.","rge_status":"Legal data stored in Malaysia."},
            "sensitive":  {"restricted":True,  "conditions":["Sensitive personal data now includes biometric data (2024 amendment)","Also includes: physical/mental health, political opinions, religious beliefs, criminal offences","Processing requires explicit consent","Cross-border transfer subject to all PDPA conditions plus heightened scrutiny"],"notes":"Definition expanded to include biometric data under 2024 amendments.","rge_status":"Assess sensitive data processing carefully."},
            "geospatial": {"restricted":False, "conditions":["No specific geospatial data export restrictions under PDPA","General PDPA rules apply if data contains personal information"],"notes":"Not specifically regulated under Malaysian data export law.","rge_status":"No specific restrictions."},
            "business":   {"restricted":False, "conditions":["General business data not restricted under PDPA unless containing personal data"],"notes":"Non-personal business data can generally be transferred freely.","rge_status":"No specific restrictions."},
            "important":  {"restricted":False, "conditions":["Not a concept in Malaysian law"],"notes":"N/A","rge_status":"N/A"},
        },
        "penalties": "Updated PDPA (2025): Fines up to RM 1,000,000 + up to 3 years imprisonment. Directors personally liable. Breach notification failure: up to RM 250,000 + 2 years. No DPO appointment: fines + possible imprisonment. PDP Commissioner can issue enforcement notices and compoundable penalties.",
        "galexy": "Yes — Galexy use is compliant.",
    },
    "canada": {
        "name": "Canada", "flag": "🇨🇦",
        "legislation": ["PIPEDA (federal)","Alberta PIPA","British Columbia PIPA"],
        "server_locations": {"Emails":"Canada","Legal":"Canada","Financial":"Canada","HR":"Ireland (Workday)"},
        "data_types": {
            "personal":   {"restricted":True,  "conditions":["Destination must have comparable (not identical) level of data protection","Contractual provisions protecting confidentiality required between sender and recipient","Risk assessment of data export required","Individuals must be notified that their data is being exported to another country","Accountability principle: organisation remains responsible for data transferred to third parties"],"notes":"PEC Canada companies are governed by provincial PIPAs (Alberta and BC), not PIPEDA. Bill C-27 (CPPA) died in early 2025. New federal legislation expected in 2026. Alberta PIPA may be reformed following Feb 2025 committee recommendations.","rge_status":"Personal data IS exported to Singapore (RGE), Malaysia (Averis) & Ireland (Workday). No standard data processor agreement currently in use."},
            "hr":         {"restricted":True,  "conditions":["Same conditions as personal data apply","HR data exported to Ireland (Workday), Singapore (RGE), Malaysia (Averis)","Contractual safeguards and notification to employees required","Risk assessment for each destination needed"],"notes":"Canada HR confirmed personal data exports to Singapore, Malaysia, and Ireland. Awaiting Canada HR reply on whether HR is managed exclusively out of Canada.","rge_status":"HR data exported to multiple jurisdictions. Compliance with provincial PIPA requirements needed."},
            "financial":  {"restricted":True,  "conditions":["Financial data stored in Canada","If containing personal data, privacy law applies to any transfer"],"notes":"Financial data stored locally.","rge_status":"Financial data stored in Canada."},
            "email":      {"restricted":True,  "conditions":["Emails stored in Canada","Privacy law applies if emails contain personal information"],"notes":"Emails stored locally.","rge_status":"Emails stored in Canada."},
            "legal":      {"restricted":True,  "conditions":["Legal data stored in Canada","Privacy law applies if containing personal information"],"notes":"Legal data stored locally.","rge_status":"Legal data stored in Canada."},
            "business":   {"restricted":True,  "conditions":["Sector-specific export controls exist under Canada's Export Control List","Categories include: special materials/equipment, materials processing, electronics, telecom/info security, sensors, navigation, marine, aerospace","PEC Canada confirms: not in the business of producing tools, equipment, technology, or electronic components","Not applicable to RGE Canada's current operations"],"notes":"Export control list categories assessed and found not applicable to PEC Canada's operations.","rge_status":"Sector-specific restrictions not applicable."},
            "sensitive":  {"restricted":True,  "conditions":["Sensitive information (health, financial, etc.) requires express consent","Higher safeguards expected for cross-border transfer","Provincial PIPAs have specific provisions"],"notes":"Handle with additional care under provincial privacy laws.","rge_status":"Assess on case-by-case basis."},
            "geospatial": {"restricted":False, "conditions":["No specific geospatial data export restrictions for RGE's operations"],"notes":"Not specifically regulated for RGE.","rge_status":"No restrictions identified."},
            "important":  {"restricted":False, "conditions":["Not a concept in Canadian law"],"notes":"N/A","rge_status":"N/A"},
        },
        "penalties": "Alberta PIPA: organisations up to CAD 100,000; individuals up to CAD 10,000. BC PIPA: same. PIPEDA: breach reporting failures up to CAD 100,000. Note: Federal reform expected in 2026 — proposed penalties up to CAD 25M or 5% of revenue.",
        "galexy": "Yes — Galexy use is compliant.",
    },
    "spain": {
        "name": "Spain", "flag": "🇪🇸",
        "legislation": ["GDPR (Regulation EU 2016/679)","LOPDGDD (Organic Law 3/2018)","LSSI (Law 34/2002)"],
        "server_locations": {"Emails":"EU (Spain)","Legal":"EU (Spain)","Financial":"EU (Spain)","HR":"EU (Spain)"},
        "data_types": {
            "personal":   {"restricted":True,  "conditions":["Transfers within EEA: freely permitted","Transfers outside EEA require one of:","• EU adequacy decision (Canada PIPEDA scope, Japan, Korea, UK renewed Dec 2025, US Data Privacy Framework, Brazil, others)","• Standard Contractual Clauses (EU SCCs)","• Binding Corporate Rules (BCRs)","• Narrow derogations under Art 49 GDPR (explicit consent, contract performance, public interest, vital interests, legal claims)"],"notes":"Spain's AEPD is one of Europe's most aggressive enforcement bodies (record €35.5M fines in FY2024). Transfers to Singapore require SCCs or BCRs — no EU adequacy decision for Singapore. Ireland is within the EEA — no transfer restrictions.","rge_status":"All data stored within EU (Spain). No cross-border transfer outside EEA currently. Galexy NOT implemented in Spain."},
            "hr":         {"restricted":True,  "conditions":["Same as personal data","LOPDGDD Arts 87-91 contain specific employee data processing rules","Right to digital disconnection (Art 88)","Monitoring of digital communications subject to specific requirements"],"notes":"All HR data stored in EU (Spain). No cross-border transfer issues.","rge_status":"HR data stored in EU (Spain)."},
            "sensitive":  {"restricted":True,  "conditions":["GDPR Art 9 'special categories': health, biometric, genetic, racial/ethnic, political, religious, trade union, sex life/orientation","Requires both: valid Art 9 legal basis AND valid Chapter V transfer mechanism","Higher scrutiny for international transfers — detailed risk assessments required"],"notes":"Strongly restricted. Both processing basis and transfer mechanism must be in place.","rge_status":"Assess carefully if any sensitive data processing is undertaken."},
            "financial":  {"restricted":True,  "conditions":["If containing personal data, GDPR rules apply","Financial sector may have additional requirements"],"notes":"Stored within EU. No transfer issues.","rge_status":"Financial data stored in EU (Spain)."},
            "email":      {"restricted":True,  "conditions":["GDPR applies if emails contain personal data","LSSI applies to electronic communications"],"notes":"Stored within EU.","rge_status":"Emails stored in EU (Spain)."},
            "legal":      {"restricted":True,  "conditions":["GDPR applies if containing personal data","Criminal records data (Art 10 GDPR) is highly restricted — processing only under explicit legal authorisation"],"notes":"Criminal records data processing rare and tightly controlled.","rge_status":"Legal data stored in EU (Spain)."},
            "geospatial": {"restricted":False, "conditions":["No specific geospatial data export restrictions beyond GDPR"],"notes":"Not specifically regulated beyond GDPR.","rge_status":"No specific restrictions."},
            "business":   {"restricted":False, "conditions":["Non-personal business data generally not restricted under GDPR","Sector-specific laws (defence, public administration) may impose additional controls"],"notes":"General business data can be transferred freely if it does not contain personal data.","rge_status":"No specific restrictions."},
            "important":  {"restricted":False, "conditions":["Not a concept in Spanish/EU law"],"notes":"N/A","rge_status":"N/A"},
        },
        "penalties": "GDPR Tier 1: up to €10M or 2% global turnover. GDPR Tier 2: up to €20M or 4% global turnover (for transfer violations). LOPDGDD: Minor up to €40K; Serious €40K–€300K; Very Serious €300K–€20M/4%. AEPD imposed record €35.5M in FY2024.",
        "galexy": "N/A — Galexy will NOT be implemented in Spain per Apical's decision.",
    },
}

AUDIT_FINDINGS = {
    "indonesia": {
        "name":"Indonesia","flag":"🇮🇩",
        "updates":[
            ("red","🔴 KEY UPDATE","The PDP Law implementing regulation (RPP PDP) remains unfinalized as of May 2026. The DPA is still not operational — a draft Presidential Regulation was published end of Feb 2026 and is awaiting presidential approval."),
            ("yellow","🟡 UPDATE","The ministry name has changed from MOCI to <strong>MOCD</strong> (Ministry of Communication and Digital Affairs / Komdigi). Spreadsheet references to 'MOCI' should be updated."),
            ("yellow","🟡 UPDATE","The U.S.–Indonesia Reciprocal Trade Agreement (19 Feb 2026) commits Indonesia to recognising the US as having adequate data protection. However, this requires ratification and does not yet have domestic legal effect."),
            ("green","🟢 CONFIRMED","The Constitutional Court has upheld the PDP Law's cross-border transfer framework (adequacy → safeguards → consent) as constitutionally sound. No official adequacy list has been issued yet."),
            ("green","🟢 CONFIRMED","Criminal enforcement of PDP Law Articles 65(1) and 65(3) is now active — at least 23 criminal cases have been prosecuted."),
        ],
        "spreadsheet_status":"Legislation correctly cited. Transfer mechanism accurately described. Penalties accurately stated.",
        "action_required":"Update ministry name references. Monitor DPA establishment and implementing regulation finalisation.",
    },
    "china": {
        "name":"China","flag":"🇨🇳",
        "updates":[
            ("red","🔴 CRITICAL UPDATE","The Cybersecurity Law (CSL) was substantially amended effective 1 January 2026. Penalties increased up to <strong>10×</strong> (max RMB 10 million). Individual liability extends beyond senior managers. The 'warning first' requirement before fines is eliminated."),
            ("red","🔴 CRITICAL UPDATE","The <strong>Certification route</strong> for cross-border personal data transfer is now fully operational (effective 1 Jan 2026). All three PIPL pathways (Security Assessment, SCCs, Certification) are now complete."),
            ("yellow","🟡 UPDATE","October 2025 CAC FAQ clarifies the HR exemption (Art 5(1)(b)) is <strong>narrowly construed</strong>: companies should NOT transfer higher-risk employee PI (ID numbers, passport info, bank accounts) without verifying necessity."),
            ("green","🟢 CONFIRMED","HR data exemption for cross-border transfer remains valid for RGE China entities, but scope must be limited to data directly relevant to HR management."),
        ],
        "spreadsheet_status":"Legislation and CIIO analysis correct. Important data self-assessment approach correct.",
        "action_required":"Update penalty figures. Review HR data transfers against the narrowed CAC guidance. Consider certification route for ongoing transfers.",
    },
    "brazil": {
        "name":"Brazil","flag":"🇧🇷",
        "updates":[
            ("yellow","🟡 UPDATE","The SCC compliance deadline under Resolution CD/ANPD No. 19/2024 was <strong>23 August 2025</strong>. Companies must now use ANPD-approved Standard Contractual Clauses (Annex II) for cross-border transfers."),
            ("yellow","🟡 UPDATE","ANPD has <strong>not yet issued any adequacy decisions</strong> for any country. All cross-border transfers must rely on other mechanisms (SCCs, BCRs, consent)."),
            ("green","🟢 CONFIRMED","The EU Commission has recognised Brazil as an adequate jurisdiction under the GDPR (per AEPD's updated adequacy list)."),
            ("green","🟢 CONFIRMED","Legislation and penalty framework correctly stated in spreadsheet."),
        ],
        "spreadsheet_status":"Legislation correctly cited. Penalties accurately stated.",
        "action_required":"Confirm Netlex server location and compliance with SCC requirements. Verify Bracell's data transfer contracts include ANPD-approved SCCs.",
    },
    "hongkong": {
        "name":"Hong Kong","flag":"🇭🇰",
        "updates":[
            ("green","🟢 CONFIRMED","Section 33 of the PDPO remains <strong>NOT in force</strong> as of May 2026. There is no indication of imminent implementation."),
            ("yellow","🟡 UPDATE","The GBA Standard Contract (Greater Bay Area) was extended to <strong>all sectors</strong> from November 2024 (previously limited to key industries). Adoption remains voluntary."),
            ("yellow","🟡 UPDATE","The Protection of Critical Infrastructure (Computer Systems) Ordinance (Cap. 653) came into force on <strong>1 January 2026</strong>, establishing cybersecurity obligations for designated Critical Infrastructure Operators across 8 sectors."),
        ],
        "spreadsheet_status":"Accurately reflects current position. Legislation and penalties correct.",
        "action_required":"Minimal. Continue voluntary compliance with PCPD's recommended model contractual clauses (RMCs) as best practice.",
    },
    "malaysia": {
        "name":"Malaysia","flag":"🇲🇾",
        "updates":[
            ("green","🟢 CONFIRMED","PDPA Amendment Act 2024 came into force in stages from January to June 2025. CBPDT Guidelines issued 29 April 2025."),
            ("yellow","🟡 UPDATE","Terminology change — 'data user' is now '<strong>data controller</strong>' throughout the Act. 'Sensitive personal data' expanded to include <strong>biometric data</strong>."),
            ("yellow","🟡 UPDATE","<strong>Data processors</strong> now have direct legal obligations under the Security Principle (Section 9) — this is new."),
            ("yellow","🟡 UPDATE","<strong>DPO appointment</strong> and <strong>mandatory data breach notification</strong> requirements now in force (from June 2025)."),
            ("green","🟢 CONFIRMED","TIA requirement, conditions for transfer, and penalty figures correctly stated in spreadsheet."),
        ],
        "spreadsheet_status":"Substantively accurate and comprehensive. Minor terminology updates needed.",
        "action_required":"Confirm DPO appointment. Ensure data breach notification procedures are in place. Update internal references from 'data user' to 'data controller'.",
    },
    "canada": {
        "name":"Canada","flag":"🇨🇦",
        "updates":[
            ("yellow","🟡 UPDATE","Bill C-27 (CPPA/AIDA) <strong>died</strong> when Parliament was prorogued in early 2025. New federal privacy legislation expected to be introduced in 2026."),
            ("yellow","🟡 UPDATE","Bill C-15 (November 2025) introduces <strong>data mobility/portability</strong> amendments to PIPEDA."),
            ("yellow","🟡 UPDATE","Alberta PIPA — Court of King's Bench (May 2025, Clearview AI case) found portions of PIPA <strong>unconstitutional</strong>. Alberta committee has recommended extensive reforms (Feb 2025 Final Report)."),
            ("green","🟢 CONFIRMED","PIPEDA, Alberta PIPA, and BC PIPA remain the operative legislation. Penalties correctly stated."),
        ],
        "spreadsheet_status":"Legislation and conditions correctly cited. Sector-specific categories analysis correct.",
        "action_required":"Monitor Alberta PIPA reform process. Confirm status of pending Canada HR reply regarding exclusive HR management. Note: Personal data IS exported to Singapore (RGE), Malaysia (Averis) & Ireland (Workday).",
    },
    "spain": {
        "name":"Spain","flag":"🇪🇸",
        "updates":[
            ("yellow","🟡 UPDATE","AEPD imposed a <strong>record €35.5 million</strong> in total fines in fiscal year 2024 (19.4% increase over prior year). Spain is one of the EU's most aggressive enforcement jurisdictions."),
            ("yellow","🟡 UPDATE","UK adequacy decision was <strong>renewed by the EU Commission in December 2025</strong>. EU-US Data Privacy Framework (July 2023) remains in effect."),
            ("green","🟢 CONFIRMED","GDPR and LOPDGDD framework correctly described. Penalty tiers accurately stated."),
            ("green","🟢 CONFIRMED","Galexy will NOT be implemented in Spain per Apical's decision."),
        ],
        "spreadsheet_status":"Comprehensive and accurate.",
        "action_required":"Minimal. Ensure any future data transfers from Spain comply with GDPR Chapter V mechanisms (SCCs, BCRs, or adequacy decisions).",
    },
}

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
COUNTRY_OPTIONS = {
    "indonesia": "🇮🇩 Indonesia",
    "china":     "🇨🇳 China",
    "brazil":    "🇧🇷 Brazil",
    "hongkong":  "🇭🇰 Hong Kong",
    "malaysia":  "🇲🇾 Malaysia",
    "canada":    "🇨🇦 Canada",
    "spain":     "🇪🇸 Spain",
}

DATA_TYPE_OPTIONS = {
    "personal":  "Personal Data (employee/customer)",
    "sensitive": "Sensitive Personal Data (health/biometric)",
    "financial": "Financial Data",
    "hr":        "HR / Employment Data",
    "geospatial":"Geospatial / Plantation Data",
    "legal":     "Legal / Litigation Data",
    "email":     "Email Communications",
    "business":  "Business / Commercial Data",
    "important": "Important / Critical Data (China-specific)",
}

def detect_data_type(question: str) -> str:
    q = question.lower()
    if re.search(r"hr|human resource|employee|payroll|workday|staff", q):      return "hr"
    if re.search(r"email|outlook|microsoft 365|ms 365", q):                    return "email"
    if re.search(r"financial|accounting|finance|revenue|tax", q):              return "financial"
    if re.search(r"geospatial|plantation|geographic|gis|map|terrain", q):      return "geospatial"
    if re.search(r"legal|litigation|contract|court", q):                       return "legal"
    if re.search(r"health|medical|biometric|genetic|sensitive", q):            return "sensitive"
    if re.search(r"important|critical|national security", q):                  return "important"
    if re.search(r"business|commercial|trade|proprietary", q):                 return "business"
    return "personal"

def is_cross_border(question: str, destination: str) -> bool:
    if destination.strip():
        return True
    return bool(re.search(r"transfer|export|send|share|move|upload|cloud|outsid|cross.border|overseas|abroad|foreign", question.lower()))

def destination_advice(country: str, destination: str) -> list:
    notes = []
    dest = destination.lower()
    if country == "spain":
        eea = ["austria","belgium","bulgaria","croatia","cyprus","czech","denmark","estonia","finland","france","germany","greece","hungary","iceland","ireland","italy","latvia","liechtenstein","lithuania","luxembourg","malta","netherlands","norway","poland","portugal","romania","slovakia","slovenia","sweden","spain"]
        adequate = ["canada","japan","korea","south korea","united kingdom","uk","united states","us","usa","brazil","argentina","switzerland","new zealand","israel","uruguay","andorra","guernsey","jersey","isle of man","faroe islands"]
        if any(c in dest for c in eea):
            notes.append(("green", f"<b>PERMITTED</b> — <em>{destination}</em> is within the EEA. No transfer restrictions apply."))
        elif any(c in dest for c in adequate):
            notes.append(("green", f"<b>PERMITTED</b> — <em>{destination}</em> has an EU adequacy decision. Transfer permitted without additional safeguards."))
        else:
            notes.append(("yellow", f"<b>CONDITIONAL</b> — <em>{destination}</em> does not have an EU adequacy decision. You must use SCCs, BCRs, or an Art 49 derogation."))
    if country == "china":
        if "hong kong" in dest or dest.strip() == "hk":
            notes.append(("blue", "Hong Kong is outside mainland China. Transfer to HK is a cross-border transfer under PIPL."))
        if any(c in dest for c in ["singapore","ireland","us","united states"]):
            notes.append(("yellow", f"Transfer to <em>{destination}</em> requires compliance with the applicable PIPL pathway (Security Assessment, SCCs, or Certification depending on volume/sensitivity thresholds)."))
    if country == "indonesia":
        notes.append(("yellow", "No official adequacy list has been issued by the Indonesian DPA (not yet operational). In practice, rely on Appropriate Safeguards or obtain data subject consent, and file required reports with MOCD."))
        if any(c in dest for c in ["us","united states"]):
            notes.append(("blue", "The US-Indonesia Trade Agreement (Feb 2026) commits to recognising US adequacy, but requires ratification and does not yet have domestic legal effect."))
    if country == "malaysia":
        notes.append(("yellow", f"Conduct a Transfer Impact Assessment (TIA) for <em>{destination}</em>. Assess whether the destination has a law substantially similar to the PDPA or ensures adequate protection. TIA valid for 3 years."))
        if "ireland" in dest:
            notes.append(("green", "Ireland has comprehensive data protection law (GDPR) which is likely to be assessed as substantially similar to PDPA."))
        if "singapore" in dest:
            notes.append(("green", "Singapore has the PDPA 2012 which may be assessed as substantially similar. Conduct TIA to confirm."))
    if country == "canada":
        notes.append(("yellow", f"Ensure <em>{destination}</em> has comparable data protection, put contractual safeguards in place, conduct a risk assessment, and notify affected individuals."))
    if country == "brazil":
        notes.append(("yellow", f"No ANPD adequacy decisions have been issued yet. Use ANPD-approved SCCs (Annex II of Resolução 19/2024), BCRs, or obtain data subject consent for transfer to <em>{destination}</em>."))
    return notes

CONSENT_INFO = {
    "indonesia": "Under the PDP Law, if neither Adequacy of Protection nor Appropriate Safeguards are present, <b>prior consent</b> from the data subject is required. RGE Indonesian entities have obtained employee consent for HR data processing on Workday.",
    "china":     "Under PIPL, <b>separate consent</b> is required for cross-border transfer of personal information. For sensitive PI, additional explicit consent is needed. The HR exemption may reduce but does not eliminate consent requirements.",
    "brazil":    "Under LGPD Art 7/33, <b>data subject consent</b> is one mechanism for lawful transfer. This is a contractual/privacy requirement, NOT regulatory authority approval. ANPD-approved SCCs are an alternative.",
    "malaysia":  "Under PDPA Section 129(3)(a), <b>explicit consent</b> from the data subject is one basis for transfer. Written notice detailing recipient class and purpose must be provided. Consent must be recorded and maintained.",
    "canada":    "Under PIPEDA/PIPA, <b>knowledge and consent</b> of the individual are required. Individuals must be notified that data may be transferred to another country.",
    "spain":     "Under GDPR Art 49(1)(a), <b>explicit consent</b> is a narrow derogation for transfers without adequacy/safeguards. Data subject must be informed of risks. Prefer SCCs or BCRs as primary mechanism.",
    "hongkong":  "Under PDPO DPP3, <b>prescribed consent</b> (express, voluntary, not withdrawn) is required to use personal data for a new purpose. Data subjects should be informed of potential transfers at or before collection.",
}

BOX_COLOURS = {"green":"box-green","yellow":"box-yellow","red":"box-red","blue":"box-blue"}
BADGE_COLOURS = {"green":"badge-green","yellow":"badge-yellow","red":"badge-red","blue":"badge-blue"}

def box(colour: str, content: str):
    st.markdown(f'<div class="{BOX_COLOURS.get(colour,"box-green")}">{content}</div>', unsafe_allow_html=True)

def badge(colour: str, text: str) -> str:
    return f'<span class="badge {BADGE_COLOURS.get(colour,"badge-blue")}">{text}</span>'

def section_title(text: str):
    st.markdown(f'<p class="section-title">{text}</p>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="rge-header">
  <h1>📊 RGE Data Export Compliance Advisor</h1>
  <p>Interactive tool for assessing data export permissibility across 7 jurisdictions &bull;
     Based on company data audit dated 27.01.26, cross-checked and updated against current laws as of May 2026</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "❓ Compliance Advisor",
    "🔍 Legal Audit Findings",
    "📋 Country Matrix",
    "⚠️ Penalties",
])

# ══════════════════════════════════════════════
# TAB 1 – COMPLIANCE ADVISOR
# ══════════════════════════════════════════════
with tab1:
    st.subheader("🧭 Ask a Compliance Question")
    st.caption("Describe your proposed action and select the relevant country. The advisor will assess permissibility under applicable data export and privacy laws.")

    col1, col2 = st.columns(2)
    with col1:
        country_key = st.selectbox(
            "Country of Origin",
            options=list(COUNTRY_OPTIONS.keys()),
            format_func=lambda k: COUNTRY_OPTIONS[k],
            index=None,
            placeholder="— Select Country —",
        )
    with col2:
        dt_key = st.selectbox(
            "Type of Data Involved",
            options=list(DATA_TYPE_OPTIONS.keys()),
            format_func=lambda k: DATA_TYPE_OPTIONS[k],
            index=None,
            placeholder="— Select Data Type —",
        )

    destination = st.text_input("Destination Country (if transferring data)", placeholder="e.g. Singapore, Ireland, Hong Kong, USA…")
    question    = st.text_area("Describe Your Proposed Action or Question",
                               placeholder="e.g. 'Can we transfer employee payroll data from Indonesia to Singapore for centralised HR processing?'",
                               height=90)

    # Quick-question buttons
    st.caption("**Quick questions:**")
    qcols = st.columns(6)
    quick_qs = [
        ("HR data to Singapore?",       "Can we transfer employee HR data to Singapore?",                  "hr"),
        ("Emails on foreign cloud?",     "Can we store emails on a cloud server outside the country?",     "email"),
        ("Financials to HK?",            "Can we transfer financial records to Hong Kong?",                 "financial"),
        ("Geospatial on Galexy?",        "Can we upload geospatial/plantation data to Galexy?",             "geospatial"),
        ("Consent requirements?",        "What consents do we need for cross-border data transfer?",        "personal"),
        ("Workday (Ireland) for HR?",    "Can we use Workday (Ireland) for HR data?",                      "hr"),
    ]
    for i, (label, q_text, q_dt) in enumerate(quick_qs):
        if qcols[i].button(label, key=f"qq_{i}", use_container_width=True):
            question    = q_text
            dt_key      = q_dt
            st.session_state["_qq_question"] = q_text
            st.session_state["_qq_dt"]       = q_dt

    # Carry quick-question state across rerun
    if "_qq_question" in st.session_state and not question:
        question = st.session_state["_qq_question"]
    if "_qq_dt" in st.session_state and not dt_key:
        dt_key = st.session_state["_qq_dt"]

    analyse_btn = st.button("🔍 Analyse Permissibility", type="primary")

    if analyse_btn:
        if not country_key:
            st.warning("⚠️ Please select a Country of Origin.")
        else:
            kb   = KB[country_key]
            dt   = dt_key if dt_key else detect_data_type(question)
            dti  = kb["data_types"].get(dt) or kb["data_types"]["personal"]
            xcb  = is_cross_border(question, destination)
            asks_galexy  = bool(re.search(r"galexy", question, re.IGNORECASE))
            asks_consent = bool(re.search(r"consent|permission|approval|authoriz", question, re.IGNORECASE))
            asks_storage = bool(re.search(r"store|storage|server|cloud|host|locat", question, re.IGNORECASE))
            dt_label     = DATA_TYPE_OPTIONS.get(dt, dt)

            severity = "yellow" if dti["restricted"] else "green"

            # ── Header ──────────────────────────────────────────────
            if dti["restricted"]:
                header_html = (f'<h3>{kb["flag"]} {kb["name"]} — {dt_label}</h3>'
                               f'{badge("yellow","RESTRICTED")} This type of data is subject to '
                               f'export/processing restrictions in {kb["name"]}.')
            else:
                header_html = (f'<h3>{kb["flag"]} {kb["name"]} — {dt_label}</h3>'
                               f'{badge("green","GENERALLY PERMITTED")} This type of data is not '
                               f'specifically restricted for export in {kb["name"]}.')
            box(severity, header_html)

            # ── Cross-border conditions ──────────────────────────────
            if xcb and dti["restricted"]:
                section_title("📋 Conditions for Cross-Border Transfer:")
                cond_html = "<ul>" + "".join(f"<li>{c}</li>" for c in dti["conditions"]) + "</ul>"
                box("yellow", cond_html)

                # Destination advice
                if destination:
                    section_title(f"🌍 Destination-Specific Notes ({destination}):")
                    for colour, note in destination_advice(country_key, destination):
                        box(colour, note)

            elif xcb and not dti["restricted"]:
                box("green", f'{badge("green","GENERALLY PERMITTED")} This data type is not specifically '
                    f'restricted for cross-border transfer from {kb["name"]}. However, general data protection '
                    f'principles still apply if any personal data is included.')

            # ── Galexy ──────────────────────────────────────────────
            if asks_galexy:
                section_title("📱 Galexy Compliance:")
                box("blue", kb["galexy"])

            # ── Storage ─────────────────────────────────────────────
            if asks_storage:
                section_title("💾 Current Server Locations:")
                rows = "".join(f"<tr><td><b>{k}</b></td><td>{v}</td></tr>" for k, v in kb["server_locations"].items())
                box("blue", f"<table style='width:100%;font-size:0.9rem'>{rows}</table>")

            # ── RGE Entity Status ────────────────────────────────────
            section_title("🏢 RGE Entity Status:")
            box("blue", dti["rge_status"])

            # ── Additional notes ─────────────────────────────────────
            if dti.get("notes"):
                section_title("📝 Additional Notes:")
                box("blue", dti["notes"])

            # ── Consent ──────────────────────────────────────────────
            if asks_consent and country_key in CONSENT_INFO:
                section_title("✅ Consent Requirements:")
                box("green", CONSENT_INFO[country_key])

            # ── Penalties ─────────────────────────────────────────────
            section_title("⚠️ Penalties for Non-Compliance:")
            box("red", f'<span style="font-size:0.9rem">{kb["penalties"]}</span>')

            # ── Recommended actions ───────────────────────────────────
            section_title("🎯 Recommended Actions:")
            actions = []
            if dti["restricted"] and xcb:
                actions += [
                    "Ensure a valid transfer mechanism is in place before any cross-border transfer.",
                    "Document compliance measures (TIA, consent records, contracts, BCRs).",
                    "Review and update data processing agreements with recipients.",
                ]
                if country_key == "indonesia": actions.append("File required reports with MOCD (planned transfer report + implementation report).")
                if country_key == "china":     actions.append("Verify HR data transfers are limited to directly relevant information (Oct 2025 CAC guidance).")
                if country_key == "brazil":    actions.append("Ensure ANPD-approved SCCs (Annex II of Resolução 19/2024) are incorporated in contracts.")
                if country_key == "malaysia":
                    actions.append("Conduct Transfer Impact Assessment (TIA) for the destination jurisdiction.")
                    actions.append("Appoint DPO and ensure breach notification procedures are in place.")
            actions.append("Consult qualified local legal counsel for specific compliance advice.")
            box("green", "<ul>" + "".join(f"<li>{a}</li>" for a in actions) + "</ul>")

    # Disclaimer
    st.markdown('<div class="disclaimer">⚠️ <b>Disclaimer:</b> This tool provides general guidance based on the RGE data export compliance audit (27.01.26) cross-referenced against publicly available legal information as of May 2026. It does not constitute legal advice. Laws and regulations are subject to change. Always consult qualified legal counsel in the relevant jurisdiction before making compliance decisions.</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 2 – LEGAL AUDIT FINDINGS
# ══════════════════════════════════════════════
with tab2:
    st.subheader("🔍 Legal Audit: Spreadsheet vs. Current Law (May 2026)")
    st.caption("Key discrepancies, updates, and corrections identified when cross-referencing the spreadsheet (dated 27.01.26) against current legislation.")

    for ckey, findings in AUDIT_FINDINGS.items():
        with st.expander(f"{findings['flag']} {findings['name']}", expanded=False):
            for colour, label, text in findings["updates"]:
                flag_class = {"red":"flag-red","yellow":"flag-yellow","green":"flag-green"}.get(colour,"flag-yellow")
                st.markdown(f'<div class="{flag_class}"><b>{label}:</b> {text}</div>', unsafe_allow_html=True)
            st.markdown(f"**Spreadsheet Status:** {findings['spreadsheet_status']}")
            st.markdown(f"**Action Required:** {findings['action_required']}")


# ══════════════════════════════════════════════
# TAB 3 – COUNTRY MATRIX
# ══════════════════════════════════════════════
with tab3:
    st.subheader("📋 Cross-Border Data Transfer Requirements Matrix")

    matrix_rows = [
        ("🇮🇩 Indonesia",  "PDP Law 27/2022, GR 71/2019, MOCD Reg 20/2016",                  "Yes — Personal data + restricted categories",        "Adequacy → Safeguards → Consent + MOCD filing",                       "✅ Yes"),
        ("🇨🇳 China",      "CSL (amended 2026), DSL, PIPL, Cross-Border Provisions",           "Yes — Critical info, important data, PI",             "Security Assessment / SCCs / Certification (all 3 live); HR exemption","✅ Yes"),
        ("🇧🇷 Brazil",     "LGPD (13.709/2018), Resolução 19/2024",                            "Yes — Personal, geospatial, sensitive business",       "Adequacy / SCCs (ANPD model) / BCRs / Consent",                       "N/A — Using Netlex"),
        ("🇭🇰 Hong Kong",  "PDPO (Cap. 486)",                                                  "Limited — S.33 not yet in force",                     "DPPs compliance + voluntary RMCs / GBA Standard Contract",            "✅ Yes"),
        ("🇲🇾 Malaysia",   "PDPA 2010 (amended 2024), CBPDT Guidelines 2025",                  "Yes — Personal data",                                 "Similar law / Adequate protection (TIA) / Consent / Contract / BCRs", "✅ Yes"),
        ("🇨🇦 Canada",     "PIPEDA, Alberta PIPA, BC PIPA",                                    "Yes — Personal data + sector-specific",               "Comparable protection + contracts + risk assessment + notice",         "✅ Yes"),
        ("🇪🇸 Spain",      "GDPR + LOPDGDD (Organic Law 3/2018)",                              "Yes — Personal data (strict GDPR regime)",            "Adequacy / SCCs / BCRs / Art 49 Derogations",                         "N/A — Not implemented"),
    ]
    import pandas as pd
    df = pd.DataFrame(matrix_rows, columns=["Country","Key Legislation","Data Export Restricted?","Transfer Mechanisms Available","Galexy Compliant?"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("📁 Current Data Server Locations")
    server_rows = [
        ("🇮🇩 Indonesia",  "Local (migrating to MS 365 SG)", "Local",         "Hong Kong", "Ireland (Workday) + Local"),
        ("🇨🇳 China",      "China",                          "China",         "Hong Kong", "Ireland (Workday)"),
        ("🇧🇷 Brazil",     "Brazil",                         "Brazil",        "Brazil",    "Ireland (Workday)"),
        ("🇭🇰 Hong Kong",  "Hong Kong",                      "Hong Kong",     "Hong Kong", "Hong Kong"),
        ("🇲🇾 Malaysia",   "Malaysia",                       "Malaysia",      "Malaysia",  "Ireland (Workday)"),
        ("🇨🇦 Canada",     "Canada",                         "Canada",        "Canada",    "Ireland (Workday)"),
        ("🇪🇸 Spain",      "EU (Spain)",                     "EU (Spain)",    "EU (Spain)","EU (Spain)"),
    ]
    df2 = pd.DataFrame(server_rows, columns=["Country","Emails","Legal Data","Financial Info","HR Data"])
    st.dataframe(df2, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════
# TAB 4 – PENALTIES
# ══════════════════════════════════════════════
with tab4:
    st.subheader("⚠️ Penalty Framework by Country (Updated May 2026)")

    for ckey, kb in KB.items():
        st.markdown(f'<div class="penalty-box"><b>{kb["flag"]} {kb["name"]}</b><br>{kb["penalties"]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="disclaimer">⚠️ <b>Disclaimer:</b> This tool provides general guidance only and does not constitute legal advice. Always consult qualified legal counsel before making compliance decisions.</div>', unsafe_allow_html=True)

