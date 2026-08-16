import os
import math
import json
import sqlite3
import traceback
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, Response
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aerolung_absolute_sync_2026")
DB_NAME = "aerolung_database.db"

# ==========================================
# 1. DATABASE INITIALIZATION
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)''')
    
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        hashed_pw = generate_password_hash('admin2026')
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  ('admin', hashed_pw, 'System Architect'))
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 1A. NEXT-GENERATION PLATFORM SERVICES
# ==========================================
def init_advanced_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS simulation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT,
        created_at TEXT NOT NULL,
        preset_id TEXT,
        condition TEXT,
        vt REAL, rr REAL, pip REAL, pplat REAL, peep REAL, fio2 REAL,
        compliance REAL, resistance REAL, vd_vt REAL, shunt REAL,
        ph REAL, paco2 REAL, pao2 REAL, hco3 REAL, minute_vent REAL,
        acid_base_status TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT,
        event TEXT NOT NULL, details TEXT, created_at TEXT NOT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS clinical_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        created_at TEXT NOT NULL, title TEXT, note_text TEXT, result_json TEXT
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_history_user_time ON simulation_history(user_id, created_at DESC)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_audit_user_time ON audit_log(user_id, created_at DESC)")
    c.execute("""CREATE TABLE IF NOT EXISTS case_journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT NOT NULL, note TEXT NOT NULL, tag TEXT DEFAULT 'learning', created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_journal_user_time ON case_journal(user_id, created_at DESC)")
    conn.commit()
    conn.close()

init_advanced_db()

# ==========================================
# 1B. NEXUS MISSION SCENARIOS
# ==========================================
NEXUS3_SCENARIOS = [
    {
        "id": "silent_hypoxemia",
        "title": "Silent Hypoxemia",
        "subtitle": "Oxygenation challenge • interpret telemetry before acting",
        "difficulty": "Advanced",
        "accent": "cyan",
        "preset": "pneumonia"
    },
    {
        "id": "obstructive_crisis",
        "title": "Obstructive Crisis",
        "subtitle": "High resistance • recognize the waveform pattern",
        "difficulty": "Expert",
        "accent": "purple",
        "preset": "asthma"
    },
    {
        "id": "stiff_lung",
        "title": "Stiff Lung Protocol",
        "subtitle": "Low compliance • pressure protection challenge",
        "difficulty": "Expert",
        "accent": "amber",
        "preset": "ards"
    },
    {
        "id": "dead_space",
        "title": "Dead-Space Signal",
        "subtitle": "Perfusion mismatch • detect the pattern",
        "difficulty": "Advanced",
        "accent": "rose",
        "preset": "pe"
    },
    {
        "id": "restrictive",
        "title": "Restrictive Mechanics",
        "subtitle": "Reduced compliance • distinguish pressure from volume",
        "difficulty": "Intermediate",
        "accent": "emerald",
        "preset": "fibrosis"
    }
]

def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def _login_required():
    return 'user_id' in session

def _audit(event, details=''):
    if not _login_required():
        return
    conn = sqlite3.connect(DB_NAME)
    conn.execute("INSERT INTO audit_log (user_id, username, event, details, created_at) VALUES (?, ?, ?, ?, ?)",
                 (session.get('user_id'), session.get('username'), event, details, _now_iso()))
    conn.commit()
    conn.close()

def _save_simulation(result, inputs):
    if not _login_required():
        return
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""INSERT INTO simulation_history
        (user_id, username, created_at, preset_id, condition, vt, rr, pip, pplat, peep, fio2,
         compliance, resistance, vd_vt, shunt, ph, paco2, pao2, hco3, minute_vent, acid_base_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session.get('user_id'), session.get('username'), _now_iso(), result.get('preset_id'),
         result.get('ai_condition'), inputs.get('vt_input'), inputs.get('rr'), inputs.get('pip'),
         inputs.get('pplat'), inputs.get('peep'), inputs.get('fio2'), result.get('compliance'),
         result.get('resistance'), result.get('vd_vt'), result.get('shunt'), result.get('ph'),
         result.get('paco2'), result.get('pao2'), result.get('hco3'), result.get('minute_vent'),
         result.get('acid_base_status')))
    conn.commit()
    conn.close()

# ==========================================
# 2. STRICT PATHOLOGY DATABASE & MATH ENGINE
# ==========================================

DISEASE_PROFILES = {
    "healthy": {
        "condition": "Stable Pulmonary Homeostasis",
        "description": "The patient demonstrates stable pulmonary homeostasis with intact ventilatory mechanics, optimal airway caliber, and unimpeded alveolar-capillary gas exchange. Thoracic cage compliance and lung parenchymal elasticity are within normal physiological bounds. There is no evidence of intrapulmonary shunting, airflow obstruction, or diffusion defects. The work of breathing is minimal, and the neuromuscular pump is fully functional, maintaining an ideal acid-base equilibrium.",
        "solutions": [
            "Maintain current baseline respiratory support and ambient room air settings.",
            "Continuously monitor spontaneous breathing trials (SBT) if mechanical ventilation is active.",
            "Assess readiness for immediate extubation or weaning protocols based on clinical criteria.",
            "Perform routine pulmonary hygiene and check vital sign trends every 4 hours."
        ]
    },
    "ards": {
        "condition": "Severe Acute Respiratory Distress Syndrome",
        "description": "The clinical picture is highly indicative of severe acute respiratory distress syndrome (ARDS), characterized by diffuse alveolar damage, profound inflammatory exudate accumulation, and surfactant inactivation. This results in critically low static lung compliance and massive intrapulmonary right-to-left shunting. Refractory hypoxemia is driven by alveolar flooding and atelectasis, rendering large lung zones completely unventilated yet perfused, vastly increasing the alveolar-arterial oxygen gradient.",
        "solutions": [
            "Implement ultra-protective lung ventilation targeting a tidal volume of 4-6 mL/kg of Predicted Body Weight (PBW).",
            "Maintain plateau pressures strictly below 30 cmH2O and driving pressure below 15 cmH2O to prevent barotrauma.",
            "Titrate high positive end-expiratory pressure (PEEP) utilizing the ARDSNet high-PEEP table to recruit collapsed alveoli.",
            "Initiate early prone positioning for 16-24 hours per day to optimize ventilation-perfusion (V/Q) matching.",
            "Consider continuous neuromuscular blockade (paralysis) to eliminate patient-ventilator dyssynchrony.",
            "Institute a strict, conservative fluid management strategy to minimize secondary pulmonary hydrostatic edema."
        ]
    },
    "copd": {
        "condition": "End-Stage COPD / Emphysema",
        "description": "The presentation reflects severe airflow obstruction and parenchymal destruction consistent with an acute exacerbation of end-stage chronic obstructive pulmonary disease (COPD) and emphysema. Loss of elastic recoil and terminal airway collapse during expiration cause critical dynamic hyperinflation and air trapping. This manifests as highly elevated airway resistance and the generation of intrinsic positive end-expiratory pressure (Auto-PEEP), which severely increases the mechanical work required to trigger a breath and leads to chronic respiratory acidosis with metabolic compensation.",
        "solutions": [
            "Administer continuous or frequent scheduled nebulized short-acting beta-agonists (Albuterol) and anticholinergics (Ipratropium).",
            "Initiate systemic intravenous corticosteroids (e.g., Methylprednisolone 40-60mg) to reduce bronchial mucosal inflammation.",
            "Apply external PEEP cautiously, titrating to approximately 70-80% of measured Auto-PEEP to reduce the work of triggering.",
            "Prolong the expiratory time by reducing the respiratory rate and increasing the peak inspiratory flow rate.",
            "Target a permissive hypercapnia strategy, accepting an elevated PaCO2 as long as arterial pH remains above 7.20.",
            "Maintain a strict oxygenation target (SpO2 88-92%) to safeguard the patient's hypoxic respiratory drive."
        ]
    },
    "asthma": {
        "condition": "Status Asthmaticus",
        "description": "This presentation represents status asthmaticus—an acute, life-threatening bronchospastic crisis refractory to initial conventional therapy. Severe smooth muscle constriction, bronchial wall edema, and tenacious mucus plugging create extreme airway resistance. Expiratory airflow is critically choked, precipitating rapid dynamic hyperinflation and severe air trapping. The mechanical burden threatens respiratory muscle fatigue, progressing from an initial respiratory alkalosis to a catastrophic, uncompensated respiratory and metabolic acidosis.",
        "solutions": [
            "Initiate continuous nebulized Albuterol combined with scheduled hourly Ipratropium bromide.",
            "Administer immediate systemic high-dose corticosteroids intravenously (e.g., Methylprednisolone 60-125mg).",
            "Provide intravenous Magnesium Sulfate (2g infused over 20 minutes) to induce rapid bronchial smooth muscle relaxation.",
            "Optimize ventilator settings to allow a prolonged expiratory phase (low respiratory rate, high inspiratory flow, I:E ratio 1:4 or greater).",
            "Monitor closely for auto-PEEP, barotrauma, and hemodynamic collapse due to increased intrathoracic pressure.",
            "Prepare for continuous intravenous bronchodilator infusions or inhaled volatile anesthetics if the condition remains refractory."
        ]
    },
    "fibrosis": {
        "condition": "Advanced Pulmonary Fibrosis",
        "description": "The clinical markers indicate advanced idiopathic pulmonary fibrosis, a chronic fibrosing interstitial pneumonia causing architectural distortion and dense parenchymal scarring. Lung tissue is profoundly stiff and non-compliant, severely restricting lung volumes. The alveolar-capillary membrane is significantly thickened, drastically impairing diffusion capacity and causing exertional hypoxemia. Gas exchange is limited by restrictive mechanics, where even small tidal volumes generate high plateau pressures.",
        "solutions": [
            "Utilize low tidal volume ventilation strategies carefully adjusted for a severe restrictive defect.",
            "Maintain plateau pressures strictly below 30 cmH2O to prevent barotrauma to fragile, scarred parenchymal tissues.",
            "Titrate PEEP with extreme caution, as high pressures may cause alveolar overdistension without recruiting fibrotic tissue.",
            "Provide high-flow supplemental oxygen therapy to compensate for severe alveolar-capillary diffusion barriers.",
            "Evaluate the patient for an acute exacerbation of interstitial lung disease (AE-ILD) and consider pulse-dose methylprednisolone.",
            "Maintain an optimized fluid balance to avoid any superimposed hydrostatic pulmonary edema."
        ]
    },
    "pe": {
        "condition": "Massive Pulmonary Embolism",
        "description": "The presentation represents a catastrophic, massive pulmonary embolism causing acute mechanical obstruction of the pulmonary arterial bed. This creates an extreme alveolar dead-space (Vd/Vt) anomaly where substantial portions of the lung are well-ventilated but completely unperfused. The sudden increase in pulmonary vascular resistance triggers acute right ventricular (RV) afterload strain, leading to RV dilation, systemic hypotension, severe ventilation-perfusion mismatch, and critical tissue hypoxia.",
        "solutions": [
            "Initiate immediate systemic anticoagulation with an intravenous Unfractionated Heparin bolus followed by a continuous infusion.",
            "Evaluate candidacy for systemic thrombolytic therapy (e.g., alteplase) or catheter-directed embolectomy if hemodynamically unstable.",
            "Provide cautious vasopressor support (Norepinephrine or Epinephrine) to maintain systemic blood pressure and RV perfusion.",
            "Avoid aggressive fluid resuscitation, as volume overloading the failing right ventricle can worsen septal shift and decrease cardiac output.",
            "Deliver 100% supplemental high-flow oxygen to promote pulmonary vasodilation and minimize hypoxic vasoconstriction.",
            "Avoid positive pressure ventilation if possible; if required, keep airway pressures extremely low to protect RV afterload."
        ]
    },
    "pneumonia": {
        "condition": "Severe Lobar Pneumonia",
        "description": "The patient exhibits severe lobar pneumonia, characterized by acute inflammatory consolidation of the alveolar spaces with purulent exudate, red blood cells, and fibrin. This localized alveolar filling prevents ventilation of the affected segments while perfusion persists, creating a severe localized right-to-left intrapulmonary shunt. The resulting ventilation-perfusion mismatch causes marked hypoxemia and increases the work of breathing, coupled with systemic signs of infection and tissue inflammation.",
        "solutions": [
            "Initiate empiric broad-spectrum intravenous antibiotic therapy within 1 hour of presentation.",
            "Implement aggressive pulmonary hygiene, including frequent suctioning, chest physiotherapy, and therapeutic mobilization.",
            "Utilize moderate PEEP (8-12 cmH2O) to recruit atelectatic alveoli adjacent to the consolidation zone.",
            "Position the patient 'good lung down' to optimize gravity-dependent blood flow to better-ventilated lung regions.",
            "Provide targeted fluid resuscitation guided by hemodynamic monitoring to address sepsis without worsening alveolar flooding.",
            "Monitor serial inflammatory markers, lactic acid, and chest radiographs to evaluate treatment efficacy."
        ]
    },
    "neuro": {
        "condition": "Neuromuscular Pump Failure",
        "description": "The data demonstrates acute neuromuscular pump failure, where the intrinsic mechanics of the lung parenchyma and airways are normal, but the mechanical apparatus of ventilation is failing. Impaired neural drive or diaphragmatic weakness leads to a critical drop in minute ventilation. This failure to clear metabolic carbon dioxide results in progressive hypercapnic respiratory failure, respiratory acidosis, and secondary micro-atelectasis due to a chronic lack of deep sigh breaths.",
        "solutions": [
            "Provide immediate full mechanical ventilatory support (Volume Control or Pressure Support) to assume the work of breathing.",
            "Perform serial measurements of Negative Inspiratory Force (NIF), Vital Capacity (VC), and Maximal Inspiratory Pressure (MIP).",
            "Investigate and treat the underlying etiology (e.g., Guillain-Barré flare, Myasthenia Gravis crisis, ALS progression, or toxin exposure).",
            "Initiate aggressive pulmonary toilet and assisted cough techniques to clear secretions and prevent secondary hypostatic pneumonia.",
            "Maintain strict aspiration precautions and evaluate swallowing function before any oral intake.",
            "Avoid respiratory depressant medications (e.g., sedatives, narcotics) unless the airway is fully secured."
        ]
    },
    "obesity": {
        "condition": "Obesity Hypoventilation Syndrome",
        "description": "The physiological parameters match Obesity Hypoventilation Syndrome (Pickwickian syndrome). Extreme adiposity on the chest wall and abdomen acts as a severe restrictive load, drastically reducing chest wall compliance. This extrinsic load increases intra-abdominal pressure, elevates the diaphragm, and causes widespread basal micro-atelectasis. The increased respiratory workload leads to chronic nocturnal hypoventilation, blunted central respiratory drive, diurnal hypercapnia, and secondary polycythemia.",
        "solutions": [
            "Utilize high baseline PEEP (12-16 cmH2O) to counteract extrinsic chest wall weight and recruit collapsed basal alveoli.",
            "Position the patient in a reverse Trendelenburg or semi-fowler's position to relieve diaphragmatic pressure from abdominal mass.",
            "Calculate all ventilator tidal volumes strictly based on Ideal Body Weight (IBW) rather than actual body weight.",
            "Transition to Non-Invasive Positive Pressure Ventilation (BiPAP) with high expiratory pressures during periods of stability.",
            "Monitor for signs of pulmonary hypertension and right ventricular failure (cor pulmonale) secondary to chronic hypoxia.",
            "Implement a controlled, long-term multidisciplinary weight management and nutritional support plan."
        ]
    },
    "pneumothorax": {
        "condition": "Tension Pneumothorax",
        "description": "This is a catastrophic, acute clinical emergency representing a tension pneumothorax. A one-way valve leak in the visceral or parietal pleura allows air to enter the pleural space during inspiration but prevents its escape during expiration. The progressive accumulation of trapped air creates positive intrapleural pressure, completely collapsing the ipsilateral lung, shifting the mediastinum, compressing the vena cava, and causing immediate hemodynamic shock and severe hypoxemia.",
        "solutions": [
            "PERFORM IMMEDIATE needle decompression using a large-bore angiocatheter in the 2nd intercostal space at the midclavicular line.",
            "Prepare immediately for the insertion of a formal tube thoracostomy (chest tube) connected to a water-seal suction system.",
            "Disconnect the patient briefly from positive pressure ventilation if hemodynamic collapse is imminent to reduce intrathoracic pressure.",
            "Administer 100% supplemental oxygen to accelerate the reabsorption of intrapleural nitrogen.",
            "Obtain a stat post-procedure portable chest X-ray to confirm lung re-expansion and correct tube placement.",
            "Monitor chest tube drainage output and check the system for persistent air leaks or fluid blockages."
        ]
    },
    "edema": {
        "condition": "Cardiogenic Pulmonary Edema",
        "description": "The presentation is classic for acute cardiogenic pulmonary edema, driven by a rapid rise in left ventricular end-diastolic pressure (LVEDP) and secondary pulmonary venous hypertension. This elevates capillary hydrostatic pressure above plasma oncotic pressure, forcing fluid across the alveolar-capillary barrier into the interstitium and alveoli. The result is rapid alveolar flooding, lost compliance, severe V/Q mismatch, and an exhausting workload of breathing.",
        "solutions": [
            "Apply immediate Non-Invasive Positive Pressure Ventilation (CPAP or BiPAP) to increase alveolar pressure and drive fluid back into the vasculature.",
            "Administer rapid-acting intravenous loop diuretics (e.g., Furosemide) to reduce circulating intravascular volume.",
            "Initiate intravenous Nitroglycerin titration to decrease preload and afterload, reducing the workload on the failing left ventricle.",
            "Provide supplemental oxygen to maintain adequate tissue oxygenation while active diuresis takes effect.",
            "Obtain an urgent 12-lead ECG, troponins, and an echocardiogram to evaluate for acute myocardial infarction or structural dysfunction.",
            "Monitor urine output, serum electrolytes, and renal function closely during aggressive fluid clearance."
        ]
    },
    "cf": {
        "condition": "Cystic Fibrosis Exacerbation",
        "description": "This exacerbation is characterized by severe airflow obstruction driven by thick, desiccated, and purulent mucous secretions plugging the bronchial tree. The underlying defect in the CFTR protein leads to dehydrated airway surfaces, impairing mucociliary clearance and facilitating chronic polymicrobial endobronchial infections. The combined effect of mucus plugging, airway inflammation, and progressive bronchiectasis causes extremely high airway resistance and patchy, profound gas exchange defects.",
        "solutions": [
            "Deliver aggressive inhaled mucolytics (e.g., Dornase alfa or hypertonic saline) to decrease sputum viscosity.",
            "Intensify chest physiotherapy and high-frequency chest wall oscillation to mobilize tenacious distal airway secretions.",
            "Administer targeted, dual-coverage intravenous antibiotics guided by recent prior sputum culture sensitivities.",
            "Optimize nutritional support and pancreatic enzyme replacement to maintain metabolic demands during the acute infectious exacerbation.",
            "Monitor closely for the development of hemoptysis or pneumothorax, both common complications of advanced cystic fibrosis.",
            "Provide systemic corticosteroids if there is evidence of an allergic bronchopulmonary aspergillosis (ABPA) flare."
        ]
    },
    "kypho": {
        "condition": "Severe Kyphoscoliosis Decompensation",
        "description": "This represents acute-on-chronic respiratory failure secondary to severe structural kyphoscoliosis. The gross anatomical deformity of the thoracic spine and rib cage significantly restricts chest wall compliance and limits maximum lung expansion. Over time, the inefficient mechanics of breathing lead to chronic alveolar hypoventilation, micro-atelectasis, and ultimately chronic hypercapnia, which is now acutely decompensated.",
        "solutions": [
            "Utilize Non-Invasive Positive Pressure Ventilation (BiPAP) as the primary modality to unload the fatigued respiratory musculature.",
            "Titrate external PEEP to overcome the substantial restrictive forces imposed by the deformed thoracic cage.",
            "Aggressively treat any underlying trigger for the decompensation, such as a mild respiratory tract infection or fluid overload.",
            "Monitor arterial blood gases carefully, recognizing that this patient likely has a baseline compensated chronic respiratory acidosis.",
            "Implement assisted cough techniques (e.g., mechanical insufflation-exsufflation) as the deformed chest limits natural cough efficacy.",
            "Avoid excessive sedation which can further blunt the patient's already compromised respiratory drive."
        ]
    },
    "bronch": {
        "condition": "Acute Bronchiectasis Exacerbation",
        "description": "The presentation aligns with an acute exacerbation of severe bronchiectasis. Chronic transmural infection and inflammation have led to the permanent pathological dilation, flaccidity, and scarring of the medium-sized bronchi. These deformed airways pool massive volumes of purulent secretions and collapse easily during expiration, causing immense airway resistance, severe dynamic hyperinflation, and recurrent localized infections.",
        "solutions": [
            "Implement rigorous and frequent pulmonary toilet to clear pooled purulent sputum from the dilated airways.",
            "Initiate broad-spectrum or culture-directed intravenous antibiotics tailored to typical colonizing organisms like H. influenzae or Pseudomonas.",
            "Maintain low ventilator respiratory rates with prolonged expiratory times to mitigate the high risk of dynamic hyperinflation and Auto-PEEP.",
            "Utilize oscillatory positive expiratory pressure (OPEP) therapy to enhance secretion mobilization.",
            "Monitor for massive hemoptysis resulting from hypertrophied, fragile bronchial arteries lining the dilated airways.",
            "Ensure adequate systemic hydration to prevent further desiccation of airway secretions."
        ]
    },
    "mild_ards": {
        "condition": "Early / Mild ARDS",
        "description": "The clinical profile suggests the early, exudative phase of mild Acute Respiratory Distress Syndrome (ARDS). Alveolar macrophages have initiated a localized inflammatory cascade, leading to early capillary endothelial leak and interstitial edema. While compliance is only beginning to decrease, the resulting hypoxemia and stretch-receptor activation drive intense tachypnea, creating an acute respiratory alkalosis before progressing to full alveolar flooding.",
        "solutions": [
            "Maintain strict vigilance for rapid clinical deterioration toward moderate or severe ARDS phenotypes.",
            "Initiate early lung-protective ventilation (6-8 mL/kg PBW) to minimize ventilator-induced lung injury (VILI).",
            "Apply moderate prophylactic PEEP (8-10 cmH2O) to prevent early basilar alveolar decruitment and atelectrauma.",
            "Implement a conservative fluid management strategy immediately to limit hydrostatic progression of the capillary leak.",
            "Aggressively identify and treat the underlying trigger (e.g., pneumonia, sepsis, aspiration, or pancreatitis).",
            "Track the PaO2/FiO2 ratio and compliance mechanics every 4-6 hours."
        ]
    },
    "atelectasis": {
        "condition": "Major Lobar Atelectasis",
        "description": "The data confirms a major lobar atelectasis, representing the acute collapse and volume loss of an entire lung lobe. This is commonly driven by a proximal mucus plug, tumor, or foreign body obstructing the bronchus, leading to complete resorption of distal alveolar gas. The loss of aerated volume causes an acute drop in overall lung compliance and creates a distinct intrapulmonary right-to-left shunt, manifesting as refractory hypoxemia.",
        "solutions": [
            "Perform immediate therapeutic bronchoscopy to visually identify and extract the obstructing endobronchial mucus plug or lesion.",
            "Initiate aggressive chest physiotherapy, postural drainage, and targeted suctioning.",
            "Apply alveolar recruitment maneuvers using transient high-PEEP applications if hemodynamically tolerated.",
            "Encourage deep breathing exercises, incentive spirometry, and early mobilization in non-intubated patients.",
            "Position the patient with the 'good lung down' to optimize gravity-dependent blood flow to better-ventilated lung regions.",
            "Ensure adequate humidification of inspired gases to prevent further drying and impaction of secretions."
        ]
    },
    "flail": {
        "condition": "Flail Chest / Blunt Thoracic Trauma",
        "description": "The physiological derangement points to a flail chest segment secondary to massive blunt thoracic trauma. Multiple contiguous ribs fractured in two or more places have decoupled a segment of the chest wall from the bony thorax. This segment moves paradoxically—inward during inspiration and outward during expiration. The underlying pulmonary contusion and severe mechanical pain drastically limit tidal volumes, causing hypoventilation, shunting, and rapid clinical deterioration.",
        "solutions": [
            "Provide immediate positive pressure ventilation (Non-invasive or Invasive) to act as a 'pneumatic splint', stabilizing the flail segment.",
            "Administer optimal, aggressive multi-modal analgesia, strongly considering a thoracic epidural or regional nerve blocks.",
            "Treat the inevitably co-existing underlying pulmonary contusion with careful, volume-restricted fluid management.",
            "Ensure rigorous clearance of airway blood and secretions, as pain severely limits the patient's natural cough mechanism.",
            "Consult thoracic surgery for potential surgical rib fixation (osteosynthesis) if failure to wean from the ventilator occurs.",
            "Continuously monitor for the delayed development of tension pneumothorax or hemothorax."
        ]
    },
    "p_htn": {
        "condition": "Pulmonary Hypertension / Cor Pulmonale",
        "description": "This condition is marked by severe pulmonary arterial hypertension, which may be idiopathic or secondary to chronic lung disease. A massive increase in pulmonary vascular resistance imposes critical afterload on the right ventricle, eventually culminating in right-sided heart failure (Cor Pulmonale). The vascular remodeling creates extensive dead-space ventilation, severely reducing cardiac output and causing profound systemic tissue hypoxia despite potentially normal alveolar ventilation.",
        "solutions": [
            "Administer inhaled pulmonary vasodilators (e.g., Inhaled Nitric Oxide or Epoprostenol) to selectively dilate ventilated pulmonary beds.",
            "Strictly avoid any degree of hypoxia or hypercapnia, as both are potent triggers for further reactive pulmonary vasoconstriction.",
            "Optimize right ventricular preload; avoid both severe volume depletion and aggressive volume overload which could bow the intraventricular septum.",
            "Utilize inotropic support (e.g., Dobutamine or Milrinone) to assist right ventricular contractility if cardiac output falls.",
            "Minimize high PEEP and plateau pressures, as excessive intrathoracic pressure directly compresses pulmonary capillaries and worsens RV afterload.",
            "Treat underlying triggers, correct acid-base disturbances, and ensure the patient is heavily sedated to minimize oxygen consumption if mechanically ventilated."
        ]
    },
    "co_poison": {
        "condition": "Carbon Monoxide Toxicity",
        "description": "The metrics reflect critical carbon monoxide (CO) poisoning. CO binds to hemoglobin with an affinity >200 times that of oxygen, forming carboxyhemoglobin. This physically displaces oxygen and aggressively shifts the oxyhemoglobin dissociation curve to the left, preventing oxygen offloading at the tissue level. The result is catastrophic cellular hypoxia, lactic acidosis, and neurological damage, paradoxically coexisting with a falsely reassuring 'normal' standard pulse oximetry (SpO2) reading.",
        "solutions": [
            "Immediately apply 100% supplemental FiO2 via a non-rebreather mask or endotracheal tube to drastically reduce the half-life of carboxyhemoglobin.",
            "Obtain an arterial blood gas with co-oximetry to accurately measure the true functional oxygen saturation and carboxyhemoglobin fraction.",
            "Arrange for emergent transfer to a facility with a hyperbaric oxygen (HBO) chamber, especially if the patient shows neurological deficits or cardiac ischemia.",
            "Monitor serum lactate and cardiac enzymes, as profound tissue hypoxia readily precipitates myocardial injury.",
            "Ignore standard pulse oximetry (SpO2) readings, as standard two-wavelength devices cannot distinguish between oxyhemoglobin and carboxyhemoglobin.",
            "Provide supportive care for secondary complications such as seizures, arrhythmias, or anoxic brain injury."
        ]
    },
    "ards_mod": {
        "condition": "Moderate ARDS",
        "description": "The profile is consistent with moderate Acute Respiratory Distress Syndrome (ARDS). A robust inflammatory response has resulted in significant protein-rich fluid leak into the alveoli, causing widespread micro-atelectasis. The PaO2/FiO2 ratio has fallen between 100 and 200. Lung compliance is substantially reduced, and gas exchange is severely compromised by a rising right-to-left intrapulmonary shunt, demanding aggressive ventilator management to prevent hypoxemic failure.",
        "solutions": [
            "Strictly enforce ARDSNet low-tidal volume ventilation (4-6 mL/kg PBW) to mitigate sheer stress and volutrauma.",
            "Maintain plateau pressures below 30 cmH2O, accepting permissive hypercapnia if necessary to protect the fragile lung parenchyma.",
            "Utilize a higher PEEP strategy to maintain open alveoli throughout the entire respiratory cycle, reducing cyclical atelectrauma.",
            "Implement prone positioning early if the PaO2/FiO2 ratio consistently drops toward 150 despite optimized PEEP.",
            "Consider a short course of neuromuscular blockade if the patient exhibits severe patient-ventilator dyssynchrony.",
            "Employ a conservative fluid strategy to achieve a negative fluid balance and reduce the hydrostatic component of the alveolar edema."
        ]
    }
}

class RespiratoryEngine:
    @staticmethod
    def safe_float(val, default):
        try:
            if val is None or str(val).strip() == '': return float(default)
            return float(val)
        except ValueError:
            return float(default)

    @classmethod
    def calculate_simulation(cls, inputs, preset_id="", custom_desc="", custom_cond="", custom_plan_str=""):
        vt = max(10.0, inputs['vt_input'])
        peep = max(0.0, inputs['peep'])
        pplat = max(peep + 1.0, inputs['pplat'])
        pip = max(pplat + 1.0, inputs['pip'])
        flow_lmin = max(5.0, inputs['peak_flow'])
        peco2 = max(0.1, inputs['peco2'])
        cao2 = max(0.1, inputs['cao2'])
        cco2 = max(cao2 + 0.1, inputs['cco2'])
        cvo2 = min(cao2 - 0.1, inputs['cvo2'])
        hco3_input = max(0.1, inputs['hco3_input'])
        rr = max(1.0, inputs['rr'])
        ie = max(0.1, inputs['ie_ratio'])
        vco2 = max(10.0, inputs['vco2'])
        fio2_val = inputs['fio2']

        driving_pressure = pplat - peep
        compliance = vt / driving_pressure
        flow_lsec = flow_lmin / 60.0
        resistance = (pip - pplat) / flow_lsec
        min_vent_est = (vt * rr) / 1000.0
        
        vd_base = 0.35
        if compliance < 45: vd_base += (45.0 - compliance) * 0.012
        if resistance > 12: vd_base += (resistance - 12.0) * 0.008
        vd_vt_ratio = max(0.15, min(0.75, vd_base))
        
        alv_vent = max(0.5, min_vent_est * (1.0 - vd_vt_ratio))
        paco2 = round((0.863 * vco2) / alv_vent, 1)

        shunt_denominator = max(0.1, cco2 - cvo2)
        shunt_ratio = (cco2 - cao2) / shunt_denominator
        shunt_pct = round(max(0.01, min(0.95, shunt_ratio)) * 100, 1)
        
        try: ph = round(6.1 + math.log10(hco3_input / (0.0301 * paco2)), 2)
        except Exception: ph = 7.40

        try:
            custom_plan = json.loads(custom_plan_str) if custom_plan_str else []
        except Exception:
            custom_plan = []

        if preset_id == "custom" and (custom_desc or custom_cond):
            ai_result = {
                'condition': custom_cond if custom_cond else "Undifferentiated Pathophysiology",
                'description': custom_desc if custom_desc else "Custom physiological parameters detected requiring clinical correlation.",
                'solutions': custom_plan if custom_plan else ["Monitor vital signs strictly.", "Adjust ventilatory support based on ABG.", "Investigate underlying etiology."]
            }
        elif preset_id in DISEASE_PROFILES:
            ai_result = DISEASE_PROFILES[preset_id].copy()
            if custom_desc: ai_result['description'] = custom_desc
        else:
            ai_result = cls._fallback_ai_diagnostics(compliance, resistance, shunt_pct, vd_vt_ratio).copy()
            if custom_desc: ai_result['description'] = custom_desc

        acid_base_status = cls._analyze_acid_base(ph, paco2, hco3_input, preset_id if preset_id in DISEASE_PROFILES else "custom")
        p_A_O2 = round(((760 - 47) * (fio2_val / 100.0)) - (paco2 / 0.8), 1)
        pao2 = round(max(30, p_A_O2 - (shunt_pct * 1.2)), 1)
        t_cycle = 60.0 / rr
        tau = max(0.001, (resistance / 1000.0) * compliance)
        waveform_data = cls._generate_waveforms(t_cycle, ie, pip, peep, vt, tau)

        return {
            'compliance': round(compliance, 1), 'resistance': round(resistance, 1),
            'vd_vt': round(vd_vt_ratio * 100, 1), 'shunt': shunt_pct,
            'preset_id': preset_id if preset_id in DISEASE_PROFILES else "custom",
            'ai_condition': ai_result['condition'], 'ai_description': ai_result['description'], 
            'ai_solutions': ai_result['solutions'],
            'paco2': paco2, 'pao2': pao2, 'ph': ph, 'hco3': hco3_input, 
            'acid_base_status': acid_base_status, 'minute_vent': round(min_vent_est, 2),
            'waveform_data': json.dumps(waveform_data)
        }

    @staticmethod
    def _fallback_ai_diagnostics(compliance, resistance, shunt_pct, vd_vt_ratio):
        if compliance < 30 and shunt_pct > 25: return DISEASE_PROFILES['ards']
        elif resistance > 20: return DISEASE_PROFILES['asthma']
        elif vd_vt_ratio > 0.50: return DISEASE_PROFILES['pe']
        elif compliance > 50 and resistance > 12: return DISEASE_PROFILES['copd']
        elif compliance < 35 and shunt_pct < 15: return DISEASE_PROFILES['fibrosis']
        else: return DISEASE_PROFILES['healthy']

    @staticmethod
    def _analyze_acid_base(ph, paco2, hco3, preset_id):
        status = "Normal Acid-Base Equilibrium"
        if ph < 7.35:
            if paco2 > 45: status = "Partially Compensated Resp. Acidosis" if hco3 > 26 else "Acute Respiratory Acidosis"
            elif hco3 < 22: status = "Partially Compensated Met. Acidosis" if paco2 < 35 else "Acute Metabolic Acidosis"
            else: status = "Mixed Acidosis"
        elif ph > 7.45:
            if paco2 < 35: status = "Partially Compensated Resp. Alkalosis" if hco3 < 22 else "Acute Respiratory Alkalosis"
            elif hco3 > 26: status = "Partially Compensated Met. Alkalosis" if paco2 > 45 else "Acute Metabolic Alkalosis"
            else: status = "Mixed Alkalosis"
        else:
            if paco2 > 45 and hco3 > 26: status = "Fully Compensated Resp. Acidosis"
            elif paco2 < 35 and hco3 < 22: status = "Fully Compensated Resp. Alkalosis"

        pathology_contexts = {
            "healthy": "Homeostatic Baseline", "ards": "Severe Intrapulmonary Shunting", "copd": "Chronic CO2 Retainer Profile",
            "asthma": "Acute Bronchospastic Crisis", "fibrosis": "Restrictive Gas Exchange Impairment", "pe": "Acute Dead-Space Anomaly",
            "pneumonia": "Lobar Consolidation Defect", "neuro": "Neuromuscular Hypoventilation", "obesity": "Chest Wall Adiposity / Hypoventilation",
            "pneumothorax": "Acute Pleural Space Impairment", "edema": "Alveolar Flooding / Transudation", "cf": "Obstructive & Suppurative Defect",
            "kypho": "Structural Restrictive Hypoventilation", "bronch": "Chronic Dilated Airway Resistance", "mild_ards": "Early Phase Hyperventilation",
            "atelectasis": "Acute Alveolar Collapse", "flail": "Paradoxical Wall Motion / Contusion", "p_htn": "Pulmonary Vascular Resistance Impairment",
            "co_poison": "Cellular Hypoxia (PaO2 Dissociation)", "ards_mod": "Moderate Alveolar-Capillary Shunting", "custom": "Dynamic Patient Pathology"
        }
        context = pathology_contexts.get(preset_id, pathology_contexts.get("custom"))
        return f"{status} | {context}"

    @staticmethod
    def _generate_waveforms(t_cycle, ie, pip, peep, vt, tau):
        t_i = t_cycle * (1 / (1 + ie))
        t_pts, p_pts, v_pts, f_pts = [], [], [], []
        res = 40
        for i in range(res + 1):
            t = (i / res) * t_cycle
            t_pts.append(round(t, 3))
            if t <= t_i:
                p_pts.append(round(pip, 1))
                v_pts.append(round(vt * (1 - math.exp(-t / tau)), 1))
                f_pts.append(round(((vt / tau) * math.exp(-t / tau)), 1) * 0.06)
            else:
                t_exp = t - t_i
                p_pts.append(round(peep, 1))
                v_pts.append(round(vt * math.exp(-t_exp / tau), 1))
                f_pts.append(round(-((vt / tau) * math.exp(-t_exp / tau)), 1) * 0.06)
        return {'t': t_pts, 'p': p_pts, 'v': v_pts, 'f': f_pts}

# ==========================================
# 3. ADVANCED NEXT-LEVEL HTML, CSS & JAVASCRIPT
# ==========================================

BACKGROUND_SVG = """
<svg class="living-lung" viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <radialGradient id="cyanGrad" cx="50%" cy="50%" r="60%">
            <stop offset="0%" stop-color="#22d3ee" stop-opacity="0.6"/>
            <stop offset="50%" stop-color="#0891b2" stop-opacity="0.8"/>
            <stop offset="100%" stop-color="#164e63" stop-opacity="1"/>
        </radialGradient>
        <filter id="glow"><feGaussianBlur stdDeviation="6" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
    </defs>
    <g filter="url(#glow)">
        <path d="M245 40 h10 v80 h-10 z" fill="#06b6d4"/>
        <path d="M250 120 L190 160 L195 170 L250 135 L305 170 L310 160 Z" fill="#06b6d4"/>
        <path d="M230 135 C 130 90, 50 210, 70 330 C 90 390, 190 390, 230 330 C 250 270, 240 180, 230 135 Z" fill="url(#cyanGrad)"/>
        <path d="M270 135 C 370 90, 450 210, 430 330 C 410 390, 310 390, 270 330 C 250 270, 260 180, 270 135 Z" fill="url(#cyanGrad)"/>
    </g>
</svg>
"""

GLOBAL_CSS_JS = """
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
    body { font-family: 'Outfit', sans-serif; background-color: #020617; color: #f8fafc; overflow-x: hidden; min-height: 100vh; display: flex; flex-direction: column; }
    .font-mono { font-family: 'JetBrains Mono', monospace; }
    @keyframes holographicBreathe { 0% { transform: translate(-50%, -50%) scale(0.97); opacity: 0.15; } 50% { transform: translate(-50%, -50%) scale(1.04); opacity: 0.45; } 100% { transform: translate(-50%, -50%) scale(0.97); opacity: 0.15; } }
    .living-lung { position: fixed; top: 50%; left: 50%; width: 100vw; max-width: 900px; z-index: 0; pointer-events: none; animation: holographicBreathe 6s ease-in-out infinite; }
    .glass-panel { background: rgba(15, 23, 42, 0.78); backdrop-filter: blur(25px); border: 1px solid rgba(255, 255, 255, 0.12); position: relative; z-index: 10; box-shadow: 0 20px 40px rgba(0,0,0,0.6); }
    .glass-input { background: rgba(0, 0, 0, 0.7); border: 1px solid rgba(255, 255, 255, 0.15); color: #fff; transition: all 0.3s ease; }
    .glass-input:focus { outline: none; border-color: #22d3ee; box-shadow: 0 0 15px rgba(34,211,238,0.4); }
    ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
    .glow-cyan { box-shadow: 0 0 20px rgba(34, 211, 238, 0.25); }
    .workspace-tab { transition: all 0.2s ease-in-out; }
    .workspace-tab.active { background: rgba(34, 211, 238, 0.15); border-color: #22d3ee; color: #22d3ee; }
    @keyframes pulseAlert { 0% { opacity: 1; border-color: rgba(244,63,94,0.8); } 50% { opacity: 0.4; border-color: rgba(244,63,94,0.2); } 100% { opacity: 1; border-color: rgba(244,63,94,0.8); } }
    .siri-orb { width:96px;height:96px;border-radius:999px;position:relative;background:radial-gradient(circle at 35% 30%,#f8fbff 0%,#b9eaff 16%,#6d5dfc 42%,#7c3aed 67%,#090b1a 100%);box-shadow:0 0 0 1px rgba(255,255,255,.16),0 0 45px rgba(99,102,241,.55),inset 0 0 30px rgba(255,255,255,.18);transition:transform .35s,box-shadow .35s;overflow:hidden}
    .siri-orb:before,.siri-orb:after{content:"";position:absolute;inset:14px;border-radius:50%;border:1px solid rgba(255,255,255,.18);animation:siriSpin 7s linear infinite}
    .siri-orb:after{inset:24px;border-color:rgba(103,232,249,.35);animation-duration:4s;animation-direction:reverse}
    .siri-orb.listening{transform:scale(1.08);box-shadow:0 0 0 1px rgba(255,255,255,.18),0 0 70px rgba(56,189,248,.7),0 0 120px rgba(124,58,237,.38)}
    @keyframes siriSpin{to{transform:rotate(360deg)}}
    .siri-overlay{background:radial-gradient(circle at 50% 35%,rgba(79,70,229,.18),transparent 42%),rgba(2,6,23,.78);backdrop-filter:blur(24px)}
    .metric-orbit{animation: orbitPulse 3.2s ease-in-out infinite}
    @keyframes orbitPulse{0%,100%{transform:translateY(0);opacity:.9}50%{transform:translateY(-3px);opacity:1}}
    .nx3-cinema body{background:#000b12}
</style>
<script>
    function updateClock() {
        const d = new Date();
        const lang = localStorage.getItem('selectedLang') || 'en-US';
        const timeStr = d.toLocaleTimeString(lang, { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const dayStr = d.toLocaleDateString(lang, { weekday: 'long' });
        const dateStr = d.toLocaleDateString(lang, { year: 'numeric', month: 'long', day: 'numeric' });
        
        const clockTimeEl = document.getElementById('clock-time');
        if(clockTimeEl) {
            clockTimeEl.innerText = timeStr;
            document.getElementById('clock-day').innerText = dayStr;
            document.getElementById('clock-date').innerText = dateStr;
        }
    }
    setInterval(updateClock, 1000);
    window.onload = function() {
        updateClock();
        checkVentilatorAlarms();
    };

    function switchWorkspaceTab(tabId) {
        document.querySelectorAll('.workspace-section').forEach(el => el.classList.add('hidden'));
        document.querySelectorAll('.workspace-tab').forEach(el => el.classList.remove('active'));
        document.getElementById('section-' + tabId).classList.remove('hidden');
        document.getElementById('tab-' + tabId).classList.add('active');
    }

    function checkVentilatorAlarms() {
        const pplatEl = document.getElementById('val-pplat');
        const pao2El = document.getElementById('val-pao2');
        const alarmContainer = document.getElementById('alarm-banner');
        
        if(!pplatEl || !alarmContainer) return;
        
        let pplatVal = parseFloat(pplatEl.innerText) || 15;
        let pao2Val = parseFloat(pao2El?.innerText) || 90;
        
        let alarms = [];
        if (pplatVal > 30) alarms.push("HIGH PRESSURE ALARM: Plateau pressure exceeds 30 cmH2O (Barotrauma risk).");
        if (pao2Val < 60) alarms.push("HYPOXEMIA ALARM: PaO2 is critically depressed (<60 mmHg).");
        
        if (alarms.length > 0) {
            alarmContainer.innerHTML = alarms.map(a => `<div class="bg-rose-950/80 border border-rose-500/50 text-rose-300 px-4 py-2 rounded-xl text-xs font-mono uppercase font-bold flex items-center justify-between mb-2"><span>⚠️ ${a}</span><span class="animate-ping h-2 w-2 rounded-full bg-rose-500"></span></div>`).join('');
            alarmContainer.classList.remove('hidden');
        } else {
            alarmContainer.classList.add('hidden');
            alarmContainer.innerHTML = '';
        }
    }

    const TRANSLATIONS = {
        en: {
            brand: "AERO<span class='text-cyan-400'>LUNG</span>",
            settings: "Settings", logout: "Logout", db_title: "Pathology Matrix",
            select_preset: "-- Select Pathology --", override: "Manual Override",
            btn_scan: "Synchronize Data", standby_title: "System Standby", standby_desc: "Select pathology, scan patient record, or activate Lyra.",
            primary_diag: "Primary Diagnosis", physio: "Physiology", action_plan: "Action Plan",
            abg: "Arterial Blood Gas", mech_exp: "Mechanics Explained",
            comp: "Compliance", res: "Resistance", dead: "Dead Space", shunt: "Shunt",
            graphs: "Waveform Analytics", lyra_btn: "Wake Lyra", lyra_status: "Lyra Sleeping", copy_btn: "Copy Config",
            tab_dashboard: "Live Workspace", tab_analytics: "Advanced Telemetry", tab_protocols: "Clinical Protocols",
            
            "healthy_cond": "Stable Pulmonary Homeostasis", "healthy_desc": "Ventilatory mechanics, airway resistance, and gas exchange are within normal limits.",
            "ards_cond": "Severe Acute Respiratory Distress Syndrome", "ards_desc": "Profound hypoxemia secondary to intrapulmonary shunting and stiff non-compliant lungs.",
            "copd_cond": "End-Stage COPD / Emphysema", "copd_desc": "High static compliance with elevated airway resistance and loss of elastic recoil.",
            "asthma_cond": "Status Asthmaticus", "asthma_desc": "Critically elevated airway resistance indicating severe bronchospasm and mucus plugging.",
            "fibrosis_cond": "Advanced Pulmonary Fibrosis", "fibrosis_desc": "Restricted lung volumes due to dense parenchymal scarring. Compliance is critically low.",
            "pe_cond": "Massive Pulmonary Embolism", "pe_desc": "Severe dead-space (Vd/Vt) anomaly. Alveoli are ventilated, but blood flow is obstructed.",
            "pneumonia_cond": "Severe Lobar Pneumonia", "pneumonia_desc": "Localized alveolar filling causing significant right-to-left intrapulmonary shunting.",
            "neuro_cond": "Neuromuscular Pump Failure", "neuro_desc": "Lung mechanics are normal, but minute ventilation is grossly inadequate leading to hypercapnia.",
            "obesity_cond": "Obesity Hypoventilation Syndrome", "obesity_desc": "Decreased compliance due to adiposity on the chest wall, leading to CO2 retention.",
            "pneumothorax_cond": "Tension Pneumothorax", "pneumothorax_desc": "Catastrophic loss of compliance combined with acute hypercapnia and mediastinal shift.",
            "edema_cond": "Cardiogenic Pulmonary Edema", "edema_desc": "Reduced compliance and elevated shunt indicative of fluid transudation from LV failure.",
            "cf_cond": "Cystic Fibrosis Exacerbation", "cf_desc": "Mixed obstructive/shunting defect. Purulent secretions causing high resistance.",
            "kypho_cond": "Severe Kyphoscoliosis Decompensation", "kypho_desc": "Structural chest wall deformity restricting lung expansion, leading to hypercapnia.",
            "bronch_cond": "Acute Bronchiectasis Exacerbation", "bronch_desc": "Chronically dilated, scarred airways filled with sputum causing massive resistance.",
            "mild_ards_cond": "Early / Mild ARDS", "mild_ards_desc": "Decreasing compliance and tachypnea causing respiratory alkalosis early in disease process.",
            "atelectasis_cond": "Major Lobar Atelectasis", "atelectasis_desc": "Acute loss of lung volume due to collapsed lobe, resulting in decreased compliance.",
            "flail_cond": "Flail Chest / Blunt Thoracic Trauma", "flail_desc": "Paradoxical chest wall movement due to rib fractures, leading to impaired compliance.",
            "p_htn_cond": "Pulmonary Hypertension / Cor Pulmonale", "p_htn_desc": "Right-sided heart failure causing poor perfusion. High dead space and stiff vasculature.",
            "co_poison_cond": "Carbon Monoxide Toxicity", "co_poison_desc": "Critical cellular hypoxia despite standard SpO2 indicating excellent oxygenation.",
            "ards_mod_cond": "Moderate ARDS", "ards_mod_desc": "Significant intrapulmonary shunting. PaO2/FiO2 ratio below 200."
        },
        es: {
            brand: "AERO<span class='text-cyan-400'>LUNG</span>",
            settings: "Ajustes", logout: "Salir", db_title: "Matriz de Patología",
            select_preset: "-- Seleccionar Patología --", override: "Anulación Manual",
            btn_scan: "Sincronizar Datos", standby_title: "Sistema en Espera", standby_desc: "Seleccione patología, escanee registro o active Lyra.",
            primary_diag: "Diagnóstico Principal", physio: "Fisiología", action_plan: "Plan de Acción",
            abg: "Gases Arteriales", mech_exp: "Mecánica Explicada",
            comp: "Distensibilidad", res: "Resistencia", dead: "Espacio Muerto", shunt: "Cortocircuito",
            graphs: "Análisis de Ondas", lyra_btn: "Despertar Lyra", lyra_status: "Lyra Durmiendo", copy_btn: "Copiar Config",
            tab_dashboard: "Espacio de Trabajo", tab_analytics: "Telemetría Avanzada", tab_protocols: "Protocolos Clínicos",
            
            "healthy_cond": "Homeostasis Pulmonar Estable", "healthy_desc": "La mecánica ventilatoria, la resistencia de las vías respiratorias y el intercambio de gases están dentro de los límites normales.",
            "ards_cond": "Síndrome de Dificultad Respiratoria Aguda Severa", "ards_desc": "Hipoxemia profunda secundaria a un cortocircuito intrapulmonar y pulmones rígidos no distensibles.",
            "copd_cond": "EPOC en Etapa Terminal / Enfisema", "copd_desc": "Distensibilidad estática alta con resistencia elevada de las vías respiratorias y pérdida de retroceso elástico.",
            "asthma_cond": "Estado Asmático", "asthma_desc": "Resistencia de las vías respiratorias críticamente elevada que indica broncoespasmo severo y tapones de moco.",
            "fibrosis_cond": "Fibrosis Pulmonar Avanzada", "fibrosis_desc": "Volúmenes pulmonares restringidos debido a cicatrices parenchymatosas densas. La distensibilidad es críticamente baja.",
            "pe_cond": "Embolia Pulmonar Masiva", "pe_desc": "Anomalía severa del espacio muerto (Vd/Vt). Los alvéolos están ventilados, pero el flujo sanguíneo está obstruido.",
            "pneumonia_cond": "Neumonía Lobar Severa", "pneumonia_desc": "Llenado alveolar localizado que causa un cortocircuito intrapulmonar significativo de derecha a izquierda.",
            "neuro_cond": "Fallo de la Bomba Neuromuscular", "neuro_desc": "La mecánica pulmonar es normal, pero la ventilación minuto es sumamente inadeada, lo que lleva a la hipercapnia.",
            "obesity_cond": "Síndrome de Hipoventilación por Obesidad", "obesity_desc": "Disminución de la distensibilidad debido a la adiposidad en la pared torácica, lo que lleva a la retención de CO2.",
            "pneumothorax_cond": "Neumotórax a Tensión", "pneumothorax_desc": "Pérdida catastrófica de distensibilidad combinada con hipercapnia aguda y desplazamiento mediastínico.",
            "edema_cond": "Edema Pulmonar Cardiogénico", "edema_desc": "Reducción de la distensibilidad y cortocircuito elevado indicativo de trasudación de líquidos por insuficiencia del VI.",
            "cf_cond": "Exacerbación de Fibrosis Quística", "cf_desc": "Defecto mixto obstructivo / de cortocircuito. Secreciones purulentas que causan alta resistencia.",
            "kypho_cond": "Descompensación Severa de Cifoescoliosis", "kypho_desc": "Deformidad estructural de la pared torácica que restringe la expansión pulmonar, lo que lleva a la hipercapnia.",
            "bronch_cond": "Exacerbación de Bronquiectasia Aguda", "bronch_desc": "Vías respiratorias crónicamente dilatadas y cicatrizadas llenas de esputo que causan una resistencia masiva.",
            "mild_ards_cond": "SDRA Temprano / Leve", "mild_ards_desc": "Disminución de la distensibilidad y taquipnea que causan alcalosis respiratoria en las primeras etapas de la enfermedad.",
            "atelectasis_cond": "Atelectasis Lobar Mayor", "atelectasis_desc": "Pérdida aguda de volumen pulmonar debido al lóbulo colapsado, lo que resulta en una disminución de la distensibilidad.",
            "flail_cond": "Tórax Inestable / Trauma Torácico Cerrado", "flail_desc": "Movimiento paradójico de la pared torácica debido a fracturas de costillas, lo que lleva a una distensibilidad alterada.",
            "p_htn_cond": "Hipertensión Pulmonaire / Cor Pulmonale", "p_htn_desc": "Insuficiencia cardíaca derecha que causa mala perfusión. Espacio muerto alto y vasculatura rígida.",
            "co_poison_cond": "Toxicidad por Monóxido de Carbono", "co_poison_desc": "Hipoxia celular crítica a pesar de que el SpO2 estándar indica una oxigenación excelente.",
            "ards_mod_cond": "SDRA Moderado", "ards_mod_desc": "Cortocircuito intrapulmonar significativo. Relación PaO2/FiO2 por debajo de 200."
        },
        fr: {
            brand: "AERO<span class='text-cyan-400'>LUNG</span>",
            settings: "Paramètres", logout: "Quitter", db_title: "Matrice Pathologique",
            select_preset: "-- Choisir Pathologie --", override: "Contrôle Manuel",
            btn_scan: "Synchroniser", standby_title: "En Veille", standby_desc: "Sélectionnez, analysez un dossier, ou activez Lyra.",
            primary_diag: "Diagnostic Principal", physio: "Physiologie", action_plan: "Plan d'Action",
            abg: "Gaz du Sang", mech_exp: "Mécanique Expliquée",
            comp: "Compliance", res: "Résistance", dead: "Espace Mort", shunt: "Shunt",
            graphs: "Analyse des Ondes", lyra_btn: "Réveiller Lyra", lyra_status: "Lyra Dort", copy_btn: "Copier Config",
            tab_dashboard: "Espace de Travail", tab_analytics: "Télémétrie Avancée", tab_protocols: "Protocoles Cliniques",
            
            "healthy_cond": "Homéostasie Pulmonaire Stable", "healthy_desc": "La mécanique ventilatoire, la résistance et les échanges gazeux sont normaux.",
            "ards_cond": "Syndrome de Détresse Respiratoire Aiguë Sévère", "ards_desc": "Hypoxémie profonde secondaire à un shunt intrapulmonaire et des poumons rigides.",
            "copd_cond": "BPCO au Stade Terminal / Emphysème", "copd_desc": "Compliance statique élevée avec résistance des voies aériennes élevée et perte de recul élastique.",
            "asthma_cond": "État de Mal Asthmatique", "asthma_desc": "Résistance extrêmement élevée indiquant un bronchospasme sévère et des bouchons muqueux.",
            "fibrosis_cond": "Fibrose Pulmonaire Avancée", "fibrosis_desc": "Volumes pulmonaires restreints dus à de denses cicatrices parenchymateuses. La compliance est très faible.",
            "pe_cond": "Embolie Pulmonaire Massive", "pe_desc": "Anomalie sévère de l'espace mort (Vd/Vt). Les alvéoles sont ventilées, mais le flux sanguin est obstrué.",
            "pneumonia_cond": "Pneumonie Lobaire Sévère", "pneumonia_desc": "Remplissage alvéolaire localisé provoquant un important shunt intrapulmonaire droite-gauche.",
            "neuro_cond": "Défaillance de la Pompe Neuromusculaire", "neuro_desc": "Mécanique pulmonaire normale, mais ventilation minute inadéquate entraînant une hypercapnie.",
            "obesity_cond": "Syndrome d'Hypoventilation de l'Obésité", "obesity_desc": "Diminution de la compliance due à l'adiposité de la paroi thoracique, entraînant une rétention de CO2.",
            "pneumothorax_cond": "Pneumothorax sous Tension", "pneumothorax_desc": "Perte catastrophique de compliance combinée à une hypercapnie aiguë et un déplacement médiastinal.",
            "edema_cond": "Œdème Pulmonaire Cardiogénique", "edema_desc": "Compliance réduite et shunt élevé indiquant une transsudation de liquide due à une insuffisance ventriculaire gauche.",
            "cf_cond": "Exacerbation de la Mucoviscidose", "cf_desc": "Défaut mixte obstructif/shunt. Sécrétions purulentes provoquant une forte résistance.",
            "kypho_cond": "Décompensation Sévère de Cyphoscoliose", "kypho_desc": "Déformation structurelle de la paroi thoracique limitant l'expansion pulmonaire.",
            "bronch_cond": "Exacerbation Aiguë de Bronchectasie", "bronch_desc": "Voies respiratoires chroniquement dilatées et cicatrisées remplies d'expectorations.",
            "mild_ards_cond": "SDRA Précoce / Léger", "mild_ards_desc": "Diminution de la compliance et tachypnée provoquant une alcalose respiratoire au début de la maladie.",
            "atelectasis_cond": "Atélectasie Lobaire Majeure", "atelectasis_desc": "Perte aiguë de volume pulmonaire due à l'effondrement du lobe, entraînant une diminution de la compliance.",
            "flail_cond": "Volet Costal / Traumatisme Thoracique Fermé", "flail_desc": "Mouvement paradoxal de la paroi thoracique dû à des fractures des côtes, entraînant une altération de la compliance.",
            "p_htn_cond": "Hypertension Pulmonaire / Cœur Pulmonaire", "p_htn_desc": "Insuffisance cardiaque droite entraînant une mauvaise perfusion. Espace mort élevé et vaisseaux rigides.",
            "co_poison_cond": "Intoxication au Monoxyde de Carbone", "co_poison_desc": "Hypoxie cellulaire critique malgré une SpO2 standard indiquant une excellente oxygénation.",
            "ards_mod_cond": "SDRA Modéré", "ards_mod_desc": "Shunt intrapulmonaire important. Rapport PaO2/FiO2 inférieur à 200."
        }
    };

    function changeLanguage(lang) {
        localStorage.setItem('selectedLang', lang);
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (TRANSLATIONS[lang] && TRANSLATIONS[lang][key]) el.innerHTML = TRANSLATIONS[lang][key];
        });
        
        const presetId = document.getElementById('current_preset_id')?.value;
        if(presetId && presetId !== 'custom') {
            const condEl = document.getElementById('ai-cond');
            const descEl = document.getElementById('ai-desc');
            const customVal = document.getElementById('custom_ai_desc')?.value;
            
            if (condEl && TRANSLATIONS[lang][presetId + '_cond']) condEl.innerText = TRANSLATIONS[lang][presetId + '_cond'];
            
            if (descEl) {
                if (customVal && customVal.trim() !== '') {
                    descEl.innerText = customVal;
                } else if (TRANSLATIONS[lang][presetId + '_desc']) {
                    descEl.innerText = TRANSLATIONS[lang][presetId + '_desc'];
                }
            }
        }

        const dd = document.getElementById('preset-dropdown');
        if(dd) dd.options[0].text = TRANSLATIONS[lang]['select_preset'];
    }

    function copyConfiguration() {
        const dd = document.getElementById('preset-dropdown');
        const pathName = dd.options[dd.selectedIndex].text;
        const configText = `--- AEROLUNG SYNC EXPORT ---\nPathology: ${pathName}\nVt: ${document.getElementById('vt_input').value} mL\nRate: ${document.getElementById('rr').value} bpm\nPIP: ${document.getElementById('pip').value} cmH2O\nPplat: ${document.getElementById('pplat').value} cmH2O\nPEEP: ${document.getElementById('peep').value} cmH2O\nFiO2: ${document.getElementById('fio2').value} %\n-----------------------------`;
        navigator.clipboard.writeText(configText).then(() => {
            const btn = document.getElementById('copy-btn');
            const originalText = btn.innerText;
            btn.innerText = "Copied!";
            btn.classList.add('bg-emerald-600');
            setTimeout(() => { btn.innerText = originalText; btn.classList.remove('bg-emerald-600'); }, 2000);
        });
    }

    function processClinicalNotes() {
        const text = document.getElementById('patient_record_input').value.toLowerCase();
        if(!text.trim()) return;
        
        document.getElementById('notes-modal').classList.add('hidden');
        
        let suspicion = 'Undifferentiated Respiratory Distress';
        let evidence = "The patient presents with respiratory compromise of mixed or atypical etiology. No single classic pattern dominated the narrative. Clinical presentation warrants broad diagnostic workup.";
        let missing = "Comprehensive metabolic panel, ABG, and advanced imaging (CT Chest).";
        let treatments = ["Ensure airway patency and adequate oxygenation.", "Obtain stat ABG and portable chest X-ray.", "Initiate continuous hemodynamic and SpO2 monitoring.", "Prepare for potential escalation of support."];
        let presetMap = 'custom';

        let vitals = [];
        const hrMatch = text.match(/(?:hr|heart rate|pulse|tachycardia).*?(\d{2,3})/);
        if (hrMatch) vitals.push(`Heart Rate: ${hrMatch[1]} bpm`);
        const rrMatch = text.match(/(?:rr|respiratory rate|breaths).*?(\d{2,3})/);
        if (rrMatch) vitals.push(`Respiratory Rate: ${rrMatch[1]} bpm`);
        const spo2Match = text.match(/(?:spo2|saturation|sat).*?(\d{2,3})/);
        if (spo2Match) vitals.push(`SpO2: ${spo2Match[1]}%`);
        let vitalsStr = vitals.length > 0 ? `\n\nEXTRACTED VITALS: ${vitals.join(' | ')}. These parameters indicate physiological stress correlating with the suspected pathology.` : "";

        const pathologyProfiles = [
            {
                name: 'End-Stage COPD / Emphysema',
                keywords: ['smok', 'barrel', 'productive cough', 'hyperinflation', 'expiratory phase', 'coalesced bullae', 'gold guidelines', 'fev1'],
                evidence: "Chronic productive cough and heavy smoking history strongly suggest COPD with underlying emphysematous changes, chronic air trapping, and hyperinflation.",
                missing: "Formal Spirometry showing FEV1/FVC < 0.70 to confirm severe obstruction, and a current baseline ABG to check for chronic hypercapnia.",
                treatments: ["Administer continuous nebulized bronchodilators (Albuterol/Ipratropium).", "Initiate systemic IV corticosteroids.", "Target SpO2 of 88-92% to prevent blunting of hypoxic drive.", "Utilize NiPPV/BiPAP to reduce work of breathing."],
                presetMap: 'copd'
            },
            {
                name: 'Status Asthmaticus',
                keywords: ['wheez', 'asthma', 'albuterol', 'bronchospasm', 'fluticasone', 'montelukast', 'atopic', 'eosinophilic'],
                evidence: "Auscultation of loud, bilateral expiratory wheezing along with episodic shortness of breath suggests severe reactive airway disease and critical bronchospasm.",
                missing: "Peak expiratory flow rate (PEFR) and response to continuous nebulization.",
                treatments: ["Administer continuous nebulized Albuterol and Ipratropium.", "Immediate IV Corticosteroids (e.g., Solu-Medrol).", "Consider IV Magnesium Sulfate for severe refractory bronchospasm."],
                presetMap: 'asthma'
            },
            {
                name: 'Cardiogenic Pulmonary Edema',
                keywords: ['orthopnea', 'frothy', 'jvd', 'jugular vein', 'bnp', 'furosemide', 'chf', 'cardiomegaly', 'pcwp'],
                evidence: "Findings of bibasilar crackles, orthopnea, and hypoxemia strongly point to left ventricular failure causing massive fluid transudation into the alveoli.",
                missing: "Echocardiogram to assess left ventricular ejection fraction and a stat NT-proBNP level.",
                treatments: ["Administer IV loop diuretics (e.g., Furosemide) immediately.", "Apply CPAP or BiPAP to decrease work of breathing and displace alveolar fluid.", "Administer vasodilators (e.g., Nitroglycerin) to reduce cardiac preload."],
                presetMap: 'edema'
            },
            {
                name: 'Pneumothorax / Tension Pneumothorax',
                keywords: ['pneumothorax', 'collapsed lung', 'hyperresonance', 'absent breath', 'tracheal deviation', 'visceral pleura', 'deep sulcus sign'],
                evidence: "Asymmetric or completely absent breath sounds combined with hyperresonance to percussion indicates a critical air leak into the pleural space.",
                missing: "Immediate upright chest X-ray or point-of-care thoracic ultrasound (POCUS looking for absence of lung sliding).",
                treatments: ["Perform urgent needle decompression if tension physiology (hemodynamic collapse, tracheal deviation) is present.", "Prepare for formal tube thoracostomy insertion.", "Administer high-flow 100% oxygen to facilitate pleural gas reabsorption."]
            },
            {
                name: 'Acute Respiratory Distress Syndrome (ARDS)',
                keywords: ['ards', 'refractory hypoxemia', 'pao2/fio2', 'p/f ratio', 'non-cardiogenic', 'bilateral infiltrates', 'diffuse alveolar damage', 'berlin criteria'],
                evidence: "Severe hypoxemia highly refractory to standard high-flow oxygen delivery paired with bilateral pulmonary infiltrates strongly points to a diffuse alveolar capillary leak condition.",
                missing: "Calculation of the precise PaO2/FiO2 ratio and an echocardiogram to definitively rule out a primary hydrostatic cardiogenic origin.",
                treatments: ["Initiate low-tidal-volume lung-protective ventilation settings (4-6 mL/kg predicted body weight).", "Titrate high positive end-expiratory pressure (PEEP) tables to preserve recruitment.", "Enforce early prolonged prone positioning cycles (16+ hours per day) for severe cases."]
            }
        ];

        let leadingProfile = null;
        let highestScore = 0;

        pathologyProfiles.forEach(profile => {
            let currentScore = 0;
            profile.keywords.forEach(keyword => {
                if (text.includes(keyword)) { currentScore++; }
            });
            if (currentScore > highestScore) {
                highestScore = currentScore;
                leadingProfile = profile;
            }
        });

        if (leadingProfile && highestScore >= 2) {
            suspicion = leadingProfile.name;
            evidence = leadingProfile.evidence + vitalsStr;
            missing = leadingProfile.missing;
            treatments = leadingProfile.treatments;
            if (leadingProfile.presetMap) presetMap = leadingProfile.presetMap;
        } else {
            suspicion = 'Atypical Pulmonary Insufficiency';
            evidence = "The patient shows objective signs of respiratory stress, but the clinical clues do not isolate a classic preset or specific disease footprint. Requires open diagnostic mapping." + vitalsStr;
            missing = "High-Resolution CT Chest, Arterial Blood Gas profiling, and urgent specialist consultation.";
            treatments = ["Deliver supplemental oxygen to safeguard vital organs.", "Initiate continuous monitoring of cardiac rhythm and SpO2.", "Coordinate a formal pulmonology evaluation."];
        }

        const formattedOutput = `PRIMARY SUSPICION: ${suspicion.toUpperCase()}\n\nCLINICAL EVIDENCE: ${evidence}\n\nMISSING DATA: ${missing}`;
        
        document.getElementById('custom_ai_desc').value = formattedOutput;
        const condElem = document.getElementById('custom_ai_cond');
        if(condElem) condElem.value = suspicion;
        const planElem = document.getElementById('custom_ai_plan');
        if(planElem) planElem.value = JSON.stringify(treatments);
        
        const langCode = localStorage.getItem('selectedLang') || 'en';
        let msg = "Record analyzed. Generating profile for " + suspicion.toUpperCase();
        document.getElementById('lyra-status').innerText = msg;
        lyraSpeak(msg, langCode);
        
        if (presetMap !== 'custom') {
            setTimeout(() => { loadPreset(presetMap); }, 2500);
        } else {
            document.getElementById('preset_id').value = 'custom';
            document.getElementById('preset-dropdown').value = 'custom';
            setTimeout(() => { document.getElementById('calc-form').submit(); }, 2500);
        }
    }

    let recognition;
    let lyraActive = false;
    const LYRA = {active:false, voiceOut:true, mode:'SIRI', history:[], contexts:[], confidence:1, lastReply:'Ready when you are.'};
    const LYRA_COMMANDS = {healthy:'healthy',normal:'healthy',ards:'ards',copd:'copd',epoc:'copd',bpco:'copd',asthma:'asthma',fibrosis:'fibrosis',embolism:'pe',embolus:'pe','pulmonary embolism':'pe',pe:'pe',pneumonia:'pneumonia',neumonia:'pneumonia',edema:'edema',oedema:'edema',pneumothorax:'pneumothorax',bronchiectasis:'bronch','cystic fibrosis':'cf',obesity:'obesity',kyphoscoliosis:'kypho',atelectasis:'atelectasis','flail chest':'flail','pulmonary hypertension':'p_htn','carbon monoxide':'co_poison','moderate ards':'ards_mod','mild ards':'mild_ards'};
    function lyraSetStatus(msg,tone='normal'){
      const e=document.getElementById('lyra-status'); if(e)e.innerText=msg;
      const st=document.getElementById('lyra-state'); if(st){st.innerText=tone==='alert'?'ALERT':tone==='busy'?'BUSY':'READY';st.className='px-2 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest '+(tone==='alert'?'bg-rose-400/10 border border-rose-400/20 text-rose-300':tone==='busy'?'bg-amber-400/10 border border-amber-400/20 text-amber-300':'bg-emerald-400/10 border border-emerald-400/20 text-emerald-300');}
    }
    function lyraSpeak(text,lang){if(!LYRA.voiceOut||!('speechSynthesis'in window))return;window.speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);u.lang=lang==='es'?'es-ES':lang==='fr'?'fr-FR':'en-US';u.pitch=.94;u.rate=.98;window.speechSynthesis.speak(u)}
    function lyraLog(command,result,kind='info'){
      LYRA.history.unshift({time:new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'}),command,result,kind});LYRA.history=LYRA.history.slice(0,40);renderLyraHub();
    }
    function lyraToggleVoice(){LYRA.voiceOut=!LYRA.voiceOut;if(!LYRA.voiceOut&&'speechSynthesis'in window)window.speechSynthesis.cancel();const a=document.getElementById('lyra-voice-btn');if(a)a.innerText=LYRA.voiceOut?'Voice On':'Voice Off';renderLyraHub()}
    function openLyraHub(){document.getElementById('lyra-hub')?.classList.remove('hidden');renderLyraHub()}
    function closeLyraHub(){document.getElementById('lyra-hub')?.classList.add('hidden')}
    function renderLyraHub(){
      const h=document.getElementById('lyra-hub-history');if(h)h.innerHTML=LYRA.history.length?LYRA.history.slice(0,14).map(x=>`<div class="lyra-history-item"><div class="flex justify-between gap-2"><span class="text-violet-200 font-bold">${x.command}</span><span class="text-[9px] text-slate-500">${x.time}</span></div><div class="text-[10px] text-slate-400 mt-1">${x.result}</div></div>`).join(''):'<div class="text-xs text-slate-500">No commands yet.</div>';
      const c=document.getElementById('lyra-context');if(c)c.innerHTML=(LYRA.contexts.length?LYRA.contexts:['No active context']).map(x=>`<span class="px-2 py-1 rounded-lg bg-white/5 border border-white/10 text-[9px] text-slate-300">${x}</span>`).join('');
      const m=document.getElementById('lyra-mode');if(m)m.innerText=LYRA.mode;const cf=document.getElementById('lyra-confidence');if(cf)cf.innerText=Math.round(LYRA.confidence*100)+'%';const n=document.getElementById('lyra-command-count');if(n)n.innerText=LYRA.history.length;const hn=document.getElementById('lyra-hub-history-count');if(hn)hn.innerText=LYRA.history.length+' events';const hv=document.getElementById('lyra-hub-voice-state');if(hv)hv.innerText=LYRA.voiceOut?'ON':'OFF';
    }
    function lyraHelp(){const msg='Commands: load pathology; set PEEP, FiO2, RR, Pplat, VT or flow; show risk, telemetry or protocols; compare two presets; analyze a note; cinema; save note; stop.';lyraSetStatus(msg);lyraLog('help',msg);lyraSpeak(msg,localStorage.getItem('selectedLang')||'en')}
    function lyraMatchPathology(text){const keys=Object.keys(LYRA_COMMANDS).sort((a,b)=>b.length-a.length);const k=keys.find(k=>text.includes(k));return k?LYRA_COMMANDS[k]:null}
    function lyraMetric(text){const patterns=[['peep','peep'],['fio2','fio2'],['fi o2','fio2'],['pplat','pplat'],['plateau pressure','pplat'],['pip','pip'],['rr','rr'],['rate','rr'],['respiratory rate','rr'],['vt','vt_input'],['tidal volume','vt_input'],['flow','peak_flow'],['i:e','ie_ratio']];for(const [label,id] of patterns){const m=text.match(new RegExp(label.replace(':','')+'\\s*(?:to|=)?\\s*(\\d+(?:\\.\\d+)?)'));if(m)return{id,value:parseFloat(m[1]),label}}return null}
    function lyraCompare(text){const clean=text.replace(/^compare\s+/,'').replace(/\s+versus\s+/,'|').replace(/\s+vs\s+/,'|').replace(/\s+with\s+/,'|');const parts=clean.split('|').map(x=>x.trim()).filter(Boolean);if(parts.length<2){lyraSetStatus('Use: compare COPD vs ARDS','alert');return}const find=q=>Object.keys(PRESETS).find(k=>q.includes(k))||lyraMatchPathology(q);const a=find(parts[0]),b=find(parts[1]);if(!a||!b){lyraSetStatus('I could not identify both comparison presets.','alert');return}const A=PRESETS[a],B=PRESETS[b],rows=[['VT',A.vt,B.vt],['RR',A.rr,B.rr],['PIP',A.pip,B.pip],['Pplat',A.pplat,B.pplat],['PEEP',A.peep,B.peep],['FiO2',A.fio2,B.fio2],['I:E',A.ie,B.ie]];document.getElementById('lyra-compare-card')?.classList.remove('hidden');document.getElementById('lyra-compare-a').innerText=a.toUpperCase();document.getElementById('lyra-compare-b').innerText=b.toUpperCase();document.getElementById('lyra-compare-output').innerHTML=rows.map(r=>`<div class="grid grid-cols-3 gap-2 py-2 border-b border-white/5 text-[10px]"><span class="text-slate-400">${r[0]}</span><span class="text-cyan-300 font-mono">${r[1]}</span><span class="text-violet-300 font-mono">${r[2]}</span></div>`).join('');const msg=`Comparison ready: ${a} versus ${b}.`;lyraSetStatus(msg);lyraLog(`compare ${a} ${b}`,msg);lyraSpeak(msg,localStorage.getItem('selectedLang')||'en')}
    function lyraApplyMetric(id,value,label){const el=document.getElementById(id);if(!el){lyraSetStatus('That parameter is not available.','alert');return}el.value=value;el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));document.getElementById('preset_id').value='custom';lyraSetStatus(`${label.toUpperCase()} set to ${value}. Recomputing telemetry.`,'busy');lyraLog(`set ${label} ${value}`,`Applied ${label}=${value}`);document.getElementById('calc-form')?.requestSubmit()}
    function processLyraCommand(text,lang){
      const raw=(text||'').trim(),t=raw.toLowerCase();if(!t)return;LYRA.confidence=1;openLyraHub();if(t==='new case'||t.includes('surprise me')||t.includes('give me a case')){nexus3RandomCase();LYRA.lastReply='I picked a new learning case for you.';lyraSetStatus(LYRA.lastReply);lyraSpeak(LYRA.lastReply,lang);lyraLog(raw,LYRA.lastReply);return;}
      if(t==='help'||t.includes('what can you do')||t.includes('commands'))return lyraHelp();
      if(t.includes('voice off')){LYRA.voiceOut=false;lyraSetStatus('Voice output muted.');lyraLog(raw,'Voice output muted.');return}
      if(t.includes('voice on')){LYRA.voiceOut=true;lyraSetStatus('Voice output enabled.');lyraLog(raw,'Voice output enabled.');return}
      if(t.includes('analyze')||t.includes('clinical note')||t.includes('record')){document.getElementById('notes-modal')?.classList.remove('hidden');lyraSetStatus('Clinical Record Synchronizer opened.','busy');lyraLog(raw,'Record analyzer opened.');return}
      if(t.includes('telemetry')||t.includes('waveform')||t.includes('analytics')){switchWorkspaceTab('analytics');lyraSetStatus('Advanced telemetry opened.');lyraLog(raw,'Telemetry workspace opened.');return}
      if(t.includes('protocol')){switchWorkspaceTab('protocols');lyraSetStatus('Protocol workspace opened.');lyraLog(raw,'Protocols opened.');return}
      if(t.includes('dashboard')||t.includes('workspace')){switchWorkspaceTab('dashboard');lyraSetStatus('Live workspace opened.');lyraLog(raw,'Workspace opened.');return}
      if(t.includes('cinema')){nexus3ToggleCinema();lyraLog(raw,'Cinema mode toggled.');return}
      if(t.includes('risk')||t.includes('safety')){nexus3ClinicalLens();openLyraHub();lyraSetStatus('Decision Lens refreshed.');lyraLog(raw,'Risk lens refreshed.');return}
      if(t.startsWith('compare'))return lyraCompare(t);
      const metric=lyraMetric(t);if(metric)return lyraApplyMetric(metric.id,metric.value,metric.label);
      if(t.includes('stop')||t.includes('sleep')){if(lyraActive)toggleLyra();else lyraSetStatus('Lyra is already in standby.');return}
      if(t.includes('save note')){openLyraHub();document.getElementById('lyra-note-text')?.focus();lyraSetStatus('Journal ready. Add a learning note.');lyraLog(raw,'Journal ready.');return}
      const matched=lyraMatchPathology(t);if(matched){['custom_ai_desc','custom_ai_cond','custom_ai_plan'].forEach(id=>{const e=document.getElementById(id);if(e)e.value=''});loadPreset(matched);LYRA.contexts=[matched.toUpperCase(),'SIMULATOR','EDUCATIONAL'];lyraSetStatus('Loaded '+matched.toUpperCase()+' • telemetry synchronized.');lyraLog(raw,'Loaded '+matched.toUpperCase());lyraSpeak('Loading '+matched.replace('_',' '),lang);setTimeout(nexus3ClinicalLens,150);return}
      LYRA.confidence=.35;lyraSetStatus('I didn’t catch that. Try pathology, risk, telemetry, compare, or new case.','alert');lyraSpeak(LYRA.lastReply,lang);lyraLog(raw,'Unrecognized command.','alert')
    }
    function submitLyraText(){const e=document.getElementById('lyra-console');if(e){processLyraCommand(e.value,localStorage.getItem('selectedLang')||'en');e.value='';e.focus()}}
    function lyraRunQuick(command){const e=document.getElementById('lyra-console');if(e)e.value=command;processLyraCommand(command,localStorage.getItem('selectedLang')||'en')}
    function toggleLyra(){
      const SpeechRec=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SpeechRec){lyraSetStatus('Voice input is unavailable here. Typed Lyra commands remain active.','alert');document.getElementById('lyra-console')?.focus();return}
      const btn=document.getElementById('lyra-btn'),langCode=localStorage.getItem('selectedLang')||'en';
      if(!lyraActive){recognition=new SpeechRec();recognition.continuous=true;recognition.interimResults=true;recognition.maxAlternatives=3;recognition.lang=langCode==='es'?'es-ES':langCode==='fr'?'fr-FR':'en-US';recognition.onresult=e=>{const r=e.results[e.results.length-1],t=r[0].transcript.trim();lyraSetStatus((r.isFinal?'Heard: ':'Listening: ')+t,'busy');if(r.isFinal)processLyraCommand(t,langCode)};recognition.onerror=e=>lyraSetStatus('Voice error: '+(e.error||'unknown')+'. Typed mode is available.','alert');recognition.onend=()=>{if(lyraActive){try{recognition.start()}catch(err){}}};try{recognition.start();lyraActive=true;btn.innerText='Stop';lyraSetStatus('Listening • command mode active','busy');lyraSpeak('Lyra online. Command mode active.',langCode)}catch(e){lyraSetStatus('Could not start voice recognition. Use typed commands.','alert')}}else{lyraActive=false;try{recognition.stop()}catch(e){}btn.innerText='Wake';lyraSetStatus('Standby • ready for command')}openLyraHub()}
    const PRESETS = {
        healthy:      {vt: 500, rr: 14, pip: 20, pplat: 14, peep: 5,  flow: 60, fio2: 30, ie: 2.0, cao2: 19.8, cvo2: 14.8, cco2: 20.4, peco2: 28, vco2: 200, hco3: 24},
        ards:         {vt: 350, rr: 28, pip: 38, pplat: 32, peep: 14, flow: 50, fio2: 80, ie: 1.5, cao2: 15.2, cvo2: 11.2, cco2: 20.1, peco2: 18, vco2: 240, hco3: 20},
        copd:         {vt: 520, rr: 10, pip: 32, pplat: 16, peep: 5,  flow: 45, fio2: 35, ie: 4.0, cao2: 18.5, cvo2: 14.2, cco2: 20.2, peco2: 24, vco2: 190, hco3: 31},
        asthma:       {vt: 450, rr: 12, pip: 45, pplat: 17, peep: 5,  flow: 40, fio2: 40, ie: 5.0, cao2: 19.2, cvo2: 14.1, cco2: 20.3, peco2: 25, vco2: 210, hco3: 24},
        fibrosis:     {vt: 350, rr: 26, pip: 35, pplat: 33, peep: 8,  flow: 55, fio2: 45, ie: 1.5, cao2: 17.5, cvo2: 13.0, cco2: 20.1, peco2: 22, vco2: 220, hco3: 24},
        pe:           {vt: 500, rr: 28, pip: 22, pplat: 15, peep: 5,  flow: 60, fio2: 50, ie: 2.0, cao2: 16.0, cvo2: 11.0, cco2: 20.0, peco2: 12, vco2: 200, hco3: 24},
        pneumonia:    {vt: 400, rr: 22, pip: 28, pplat: 22, peep: 10, flow: 50, fio2: 60, ie: 2.0, cao2: 16.5, cvo2: 12.0, cco2: 20.2, peco2: 20, vco2: 230, hco3: 22},
        neuro:        {vt: 250, rr: 10, pip: 15, pplat: 10, peep: 5,  flow: 40, fio2: 21, ie: 2.0, cao2: 18.0, cvo2: 13.5, cco2: 20.4, peco2: 35, vco2: 180, hco3: 26},
        obesity:      {vt: 400, rr: 18, pip: 30, pplat: 26, peep: 12, flow: 50, fio2: 30, ie: 2.0, cao2: 18.5, cvo2: 14.0, cco2: 20.0, peco2: 35, vco2: 250, hco3: 32},
        pneumothorax: {vt: 300, rr: 30, pip: 45, pplat: 40, peep: 5,  flow: 60, fio2: 90, ie: 1.0, cao2: 14.0, cvo2: 10.0, cco2: 20.0, peco2: 15, vco2: 220, hco3: 20},
        edema:        {vt: 400, rr: 24, pip: 30, pplat: 25, peep: 12, flow: 50, fio2: 50, ie: 2.0, cao2: 16.5, cvo2: 12.0, cco2: 20.0, peco2: 20, vco2: 210, hco3: 24},
        cf:           {vt: 450, rr: 20, pip: 35, pplat: 20, peep: 8,  flow: 50, fio2: 45, ie: 3.0, cao2: 17.0, cvo2: 12.5, cco2: 20.2, peco2: 22, vco2: 220, hco3: 28},
        kypho:        {vt: 250, rr: 24, pip: 35, pplat: 32, peep: 5,  flow: 40, fio2: 30, ie: 2.0, cao2: 18.0, cvo2: 13.5, cco2: 20.4, peco2: 32, vco2: 190, hco3: 29},
        bronch:       {vt: 480, rr: 16, pip: 28, pplat: 18, peep: 5,  flow: 45, fio2: 35, ie: 2.5, cao2: 18.0, cvo2: 13.0, cco2: 20.0, peco2: 24, vco2: 200, hco3: 26},
        mild_ards:    {vt: 400, rr: 20, pip: 28, pplat: 24, peep: 10, flow: 55, fio2: 50, ie: 2.0, cao2: 17.5, cvo2: 13.0, cco2: 20.2, peco2: 22, vco2: 210, hco3: 24},
        atelectasis:  {vt: 380, rr: 20, pip: 26, pplat: 22, peep: 5,  flow: 50, fio2: 40, ie: 2.0, cao2: 18.2, cvo2: 13.8, cco2: 20.3, peco2: 26, vco2: 200, hco3: 24},
        flail:        {vt: 400, rr: 26, pip: 28, pplat: 20, peep: 8,  flow: 50, fio2: 40, ie: 2.0, cao2: 17.8, cvo2: 13.0, cco2: 20.0, peco2: 24, vco2: 210, hco3: 23},
        p_htn:        {vt: 450, rr: 22, pip: 25, pplat: 18, peep: 5,  flow: 55, fio2: 50, ie: 2.0, cao2: 15.0, cvo2: 10.0, cco2: 19.5, peco2: 18, vco2: 180, hco3: 22},
        co_poison:    {vt: 500, rr: 16, pip: 20, pplat: 14, peep: 5,  flow: 60, fio2: 100,ie: 2.0, cao2: 12.0, cvo2: 8.0,  cco2: 20.0, peco2: 30, vco2: 200, hco3: 20},
        ards_mod:     {vt: 380, rr: 24, pip: 32, pplat: 28, peep: 12, flow: 55, fio2: 60, ie: 1.5, cao2: 16.5, cvo2: 12.0, cco2: 20.1, peco2: 20, vco2: 230, hco3: 22}
    };

    function loadPreset(type) {
        if (!type || type === "custom") return;
        const data = PRESETS[type];
        document.getElementById('preset_id').value = type;
        document.getElementById('preset-dropdown').value = type;
        
        const c_desc = document.getElementById('custom_ai_desc'); if(c_desc) c_desc.value = '';
        const c_cond = document.getElementById('custom_ai_cond'); if(c_cond) c_cond.value = '';
        const c_plan = document.getElementById('custom_ai_plan'); if(c_plan) c_plan.value = '';
        
        document.getElementById('vt_input').value = data.vt;
        document.getElementById('rr').value = data.rr;
        document.getElementById('pip').value = data.pip;
        document.getElementById('pplat').value = data.pplat;
        document.getElementById('peep').value = data.peep;
        document.getElementById('peak_flow').value = data.flow;
        document.getElementById('fio2').value = data.fio2;
        document.getElementById('ie_ratio').value = data.ie;
        document.getElementById('cao2').value = data.cao2;
        document.getElementById('cvo2').value = data.cvo2;
        document.getElementById('cco2').value = data.cco2;
        document.getElementById('peco2').value = data.peco2;
        document.getElementById('vco2').value = data.vco2;
        document.getElementById('hco3_input').value = data.hco3;
        
        document.getElementById('calc-form').submit();
    }
</script>
"""

LOGIN_HTML = GLOBAL_CSS_JS + BACKGROUND_SVG + """
<body class="flex items-center justify-center min-h-screen">
    <div class="glass-panel p-10 rounded-3xl w-full max-w-md text-center shadow-2xl border-t border-cyan-500/30">
        <h1 class="text-5xl font-black text-white mb-2" data-i18n="brand">AERO<span class="text-cyan-400">LUNG</span></h1>
        <p class="text-slate-400 text-xs mb-8 tracking-wider uppercase">Advanced Pulmonary Simulation Suite</p>
        <form action="/login" method="POST" class="space-y-4 text-left mt-4">
            <div><label class="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Architect ID</label><input type="text" name="username" class="w-full glass-input px-4 py-3 rounded-xl text-sm" required></div>
            <div><label class="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Passkey</label><input type="password" name="password" class="w-full glass-input px-4 py-3 rounded-xl text-sm" required></div>
            <button type="submit" class="w-full mt-6 py-3.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 transition-colors font-bold text-white uppercase text-xs tracking-widest shadow-lg glow-cyan">Initialize Access</button>
        </form>
    </div>
</body>
"""

SETTINGS_HTML = GLOBAL_CSS_JS + BACKGROUND_SVG + """
<body class="flex items-center justify-center relative flex-col min-h-screen">
    <nav class="glass-panel w-full bg-slate-950/90 py-4 px-8 flex justify-between absolute top-0 z-50 border-b border-white/10">
        <h1 class="text-2xl font-black tracking-tighter text-white" data-i18n="brand">AERO<span class="text-cyan-400">LUNG</span></h1>
        <a href="/dashboard" class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 transition-colors text-white text-xs font-bold uppercase tracking-wider" data-i18n="return_dash">Return to Dashboard</a>
    </nav>
    <div class="glass-panel rounded-3xl p-10 w-full max-w-lg mt-20">
        <h2 class="text-3xl font-black text-white mb-2 uppercase" data-i18n="settings">Settings</h2>
        <p class="text-slate-400 text-xs mb-6 uppercase tracking-wider">Configure System Security Parameters</p>
        <form action="/settings" method="POST" class="space-y-5 text-left">
            <div><label class="block text-[10px] font-bold text-cyan-400 uppercase tracking-widest mb-2">New Architect ID</label><input type="text" name="new_username" class="w-full glass-input px-5 py-4 rounded-xl font-mono text-sm"></div>
            <div><label class="block text-[10px] font-bold text-cyan-400 uppercase tracking-widest mb-2">New Passkey</label><input type="password" name="new_password" class="w-full glass-input px-5 py-4 rounded-xl font-mono text-sm"></div>
            <button type="submit" class="w-full py-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 transition-colors font-bold text-white uppercase text-xs tracking-widest mt-4 shadow-lg glow-cyan">Save Configuration</button>
        </form>
    </div>
</body>
"""

DASHBOARD_HTML = GLOBAL_CSS_JS + BACKGROUND_SVG + """
<body class="min-h-screen flex flex-col">
    <!-- TOP NAVIGATION BAR -->
    <header class="glass-panel w-full bg-slate-950/90 py-3.5 px-8 flex flex-wrap justify-between items-center border-b border-white/10 z-50">
        <div class="flex items-center space-x-6">
            <h1 class="text-2xl font-black tracking-tighter text-white" data-i18n="brand">AERO<span class="text-cyan-400">LUNG</span></h1>
            <div class="hidden md:flex space-x-2 border-l border-white/10 pl-6">
                <button onclick="switchWorkspaceTab('dashboard')" id="tab-dashboard" class="workspace-tab active px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider text-slate-300 border border-transparent" data-i18n="tab_dashboard">Live Workspace</button>
                <button onclick="switchWorkspaceTab('analytics')" id="tab-analytics" class="workspace-tab px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider text-slate-300 border border-transparent" data-i18n="tab_analytics">Advanced Telemetry</button>
                <button onclick="switchWorkspaceTab('protocols')" id="tab-protocols" class="workspace-tab px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider text-slate-300 border border-transparent" data-i18n="tab_protocols">Clinical Protocols</button>
            </div>
        </div>
        
        <div class="flex items-center space-x-6">
            <div class="hidden lg:block text-right font-mono text-xs">
                <div id="clock-time" class="text-cyan-400 font-bold text-sm">00:00:00</div>
                <div class="text-slate-400 text-[10px]"><span id="clock-day">Day</span>, <span id="clock-date">Date</span></div>
            </div>
            <div class="flex space-x-2 bg-black/40 p-1.5 rounded-xl border border-white/10">
                <button onclick="changeLanguage('en')" class="px-2.5 py-1 rounded-lg text-xs font-bold text-slate-300 hover:text-white hover:bg-white/10 transition">EN</button>
                <button onclick="changeLanguage('es')" class="px-2.5 py-1 rounded-lg text-xs font-bold text-slate-300 hover:text-white hover:bg-white/10 transition">ES</button>
                <button onclick="changeLanguage('fr')" class="px-2.5 py-1 rounded-lg text-xs font-bold text-slate-300 hover:text-white hover:bg-white/10 transition">FR</button>
            </div>
            <div class="flex items-center space-x-2 border-l border-white/10 pl-4">
                <a href="/settings" class="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 transition text-slate-300 hover:text-white text-xs font-bold" title="Settings">⚙️</a>
                <a href="/logout" class="px-4 py-2.5 rounded-xl bg-rose-600/20 hover:bg-rose-600/40 border border-rose-500/30 text-rose-300 transition text-xs font-bold uppercase tracking-wider" data-i18n="logout">Logout</a>
            </div>
        </div>
    </header>

    <!-- MAIN CONTENT AREA -->
    <main class="flex-1 p-6 md:p-8 max-w-[1600px] w-full mx-auto space-y-6">
        
        <!-- VENTILATOR ALARM BANNER -->
        <div id="alarm-banner" class="hidden"></div>

        <!-- WORKSPACE TAB 1: LIVE WORKSPACE -->
        <div id="section-dashboard" class="workspace-section space-y-6">
            
            <!-- CONTROLS & NLP SCANNER HEADER -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Pathology Preset Selector -->
                <div class="glass-panel p-6 rounded-3xl flex flex-col justify-between">
                    <div>
                        <h2 class="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-3" data-i18n="db_title">Pathology Matrix</h2>
                        <select id="preset-dropdown" onchange="loadPreset(this.value)" class="w-full glass-input px-4 py-3 rounded-xl text-sm font-semibold">
                            <option value="custom" data-i18n="select_preset">-- Select Pathology --</option>
                            {% for key in DISEASE_PROFILES.keys() %}
                            <option value="{{ key }}" {% if result.preset_id == key %}selected{% endif %}>{{ DISEASE_PROFILES[key].condition }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <button onclick="document.getElementById('notes-modal').classList.remove('hidden')" class="w-full mt-4 py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 transition font-bold text-white text-xs uppercase tracking-wider shadow-lg glow-cyan" data-i18n="btn_scan">Synchronize Data</button>
                </div>
                <!-- Minimal Lyra / Siri-like Assistant -->
                <div class="glass-panel p-5 rounded-3xl flex items-center justify-between gap-4">
                    <div class="flex items-center gap-4 min-w-0">
                        <button onclick="openLyraHub()" class="siri-orb !w-14 !h-14 shrink-0" aria-label="Open Lyra"></button>
                        <div class="min-w-0"><div class="text-xs font-black text-white">Lyra</div><p id="lyra-status" class="text-[11px] text-slate-400 truncate">Ready when you are</p></div>
                    </div>
                    <button id="lyra-btn" onclick="toggleLyra()" class="px-4 py-2.5 rounded-2xl bg-violet-500/10 border border-violet-400/20 text-violet-200 text-[10px] font-black uppercase tracking-widest">Ask</button>
                </div>

                <!-- Export & Config Copy -->
                <div class="glass-panel p-6 rounded-3xl flex flex-col justify-between">
                    <div>
                        <h2 class="text-xs font-bold text-emerald-400 uppercase tracking-widest mb-1">Configuration Telemetry</h2>
                        <p class="text-xs text-slate-300 font-mono">Active Model Sync ID: <span class="text-white font-bold uppercase">{{ result.preset_id }}</span></p>
                    </div>
                    <button id="copy-btn" onclick="copyConfiguration()" class="w-full py-3 rounded-xl bg-slate-800 hover:bg-slate-700 border border-white/10 transition font-bold text-white text-xs uppercase tracking-wider" data-i18n="copy_btn">Copy Config</button>
                </div>
            </div>

            <!-- SIMULATION FORM & DIAGNOSTIC CORE -->
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <!-- Ventilator Parameters Input Form -->
                <div class="lg:col-span-4 glass-panel p-6 rounded-3xl">
                    <h3 class="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4" data-i18n="override">Manual Override</h3>
                    <form id="calc-form" action="/dashboard" method="POST" class="space-y-3.5">
                        <input type="hidden" id="preset_id" name="preset_id" value="{{ result.preset_id }}">
                        <input type="hidden" id="custom_ai_desc" name="custom_desc" value="">
                        <input type="hidden" id="custom_ai_cond" name="custom_cond" value="">
                        <input type="hidden" id="custom_ai_plan" name="custom_plan_str" value="">
                        
                        <div class="grid grid-cols-2 gap-3">
                            <div><label class="block text-[10px] font-bold text-slate-400 mb-1 uppercase">Tidal Vol (mL)</label><input type="number" step="10" id="vt_input" name="vt_input" value="{{ request.form.get('vt_input', 500) }}" class="w-full glass-input p-2.5 rounded-xl font-mono text-xs"></div>
                            <div><label class="block text-[10px] font-bold text-slate-400 mb-1 uppercase">Resp Rate (/m)</label><input type="number" step="1" id="rr" name="rr" value="{{ request.form.get('rr', 14) }}" class="w-full glass-input p-2.5 rounded-xl font-mono text-xs"></div>
                        </div>
                        <div class="grid grid-cols-3 gap-2">
                            <div><label class="block text-[10px] font-bold text-slate-400 mb-1 uppercase">PIP</label><input type="number" step="1" id="pip" name="pip" value="{{ request.form.get('pip', 20) }}" class="w-full glass-input p-2.5 rounded-xl font-mono text-xs"></div>
                            <div><label class="block text-[10px] font-bold text-slate-400 mb-1 uppercase">Pplat</label><input type="number" step="1" id="pplat" name="pplat" value="{{ request.form.get('pplat', 14) }}" class="w-full glass-input p-2.5 rounded-xl font-mono text-xs"></div>
                            <div><label class="block text-[10px] font-bold text-slate-400 mb-1 uppercase">PEEP</label><input type="number" step="1" id="peep" name="peep" value="{{ request.form.get('peep', 5) }}" class="w-full glass-input p-2.5 rounded-xl font-mono text-xs"></div>
                        </div>
                        <div class="grid grid-cols-3 gap-2">
                            <div><label class="block text-[10px] font-bold text-slate-400 mb-1 uppercase">Flow (L/m)</label><input type="number" step="5" id="peak_flow" name="peak_flow" value="{{ request.form.get('peak_flow', 60) }}" class="w-full glass-input p-2.5 rounded-xl font-mono text-xs"></div>
                            <div><label class="block text-[10px] font-bold text-slate-400 mb-1 uppercase">FiO2 (%)</label><input type="number" step="1" id="fio2" name="fio2" value="{{ request.form.get('fio2', 30) }}" class="w-full glass-input p-2.5 rounded-xl font-mono text-xs"></div>
                            <div><label class="block text-[10px] font-bold text-slate-400 mb-1 uppercase">I:E Ratio</label><input type="number" step="0.1" id="ie_ratio" name="ie_ratio" value="{{ request.form.get('ie_ratio', 2.0) }}" class="w-full glass-input p-2.5 rounded-xl font-mono text-xs"></div>
                        </div>
                        <div class="grid grid-cols-3 gap-2">
                            <div><label class="block text-[10px] font-bold text-slate-400 mb-1 uppercase">CaO2</label><input type="number" step="0.1" id="cao2" name="cao2" value="{{ request.form.get('cao2', 19.8) }}" class="w-full glass-input p-2.5 rounded-xl font-mono text-xs"></div>
                            <div><label class="block text-[10px] font-bold text-slate-400 mb-1 uppercase">CvO2</label><input type="number" step="0.1" id="cvo2" name="cvo2" value="{{ request.form.get('cvo2', 14.8) }}" class="w-full glass-input p-2.5 rounded-xl font-mono text-xs"></div>
                            <div><label class="block text-[10px] font-bold text-slate-400 mb-1 uppercase">CcO2</label><input type="number" step="0.1" id="cco2" name="cco2" value="{{ request.form.get('cco2', 20.4) }}" class="w-full glass-input p-2.5 rounded-xl font-mono text-xs"></div>
                        </div>
                        <div class="grid grid-cols-3 gap-2">
                            <div><label class="block text-[10px] font-bold text-slate-400 mb-1 uppercase">PetCO2</label><input type="number" step="1" id="peco2" name="peco2" value="{{ request.form.get('peco2', 28) }}" class="w-full glass-input p-2.5 rounded-xl font-mono text-xs"></div>
                            <div><label class="block text-[10px] font-bold text-slate-400 mb-1 uppercase">VCO2</label><input type="number" step="10" id="vco2" name="vco2" value="{{ request.form.get('vco2', 200) }}" class="w-full glass-input p-2.5 rounded-xl font-mono text-xs"></div>
                            <div><label class="block text-[10px] font-bold text-slate-400 mb-1 uppercase">HCO3</label><input type="number" step="0.5" id="hco3_input" name="hco3_input" value="{{ request.form.get('hco3_input', 24) }}" class="w-full glass-input p-2.5 rounded-xl font-mono text-xs"></div>
                        </div>
                        <button type="submit" class="w-full py-3.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 transition font-bold text-white uppercase text-xs tracking-widest mt-2 shadow-lg glow-cyan">Compute Telemetry</button>
                    </form>
                </div>

                <!-- Diagnostic Breakdown & Metrics -->
                <div class="lg:col-span-8 space-y-6">
                    <!-- AI Diagnosis Banner -->
                    <div class="glass-panel p-6 rounded-3xl border-l-4 border-cyan-400">
                        <span class="text-[10px] font-bold text-cyan-400 uppercase tracking-widest" data-i18n="primary_diag">Primary Diagnosis</span>
                        <h2 id="ai-cond" class="text-2xl font-black text-white mt-1 mb-2">{{ result.ai_condition }}</h2>
                        <p id="ai-desc" class="text-sm text-slate-300 leading-relaxed">{{ result.ai_description }}</p>
                    </div>

                    <!-- Metrics Grid -->
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="glass-panel p-5 rounded-2xl text-center">
                            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest" data-i18n="comp">Compliance</span>
                            <div class="text-2xl font-black text-cyan-400 font-mono mt-1">{{ result.compliance }} <span class="text-xs text-slate-400">mL/cm</span></div>
                        </div>
                        <div class="glass-panel p-5 rounded-2xl text-center">
                            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest" data-i18n="res">Resistance</span>
                            <div class="text-2xl font-black text-cyan-400 font-mono mt-1">{{ result.resistance }} <span class="text-xs text-slate-400">cm/L/s</span></div>
                        </div>
                        <div class="glass-panel p-5 rounded-2xl text-center">
                            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest" data-i18n="dead">Dead Space</span>
                            <div class="text-2xl font-black text-cyan-400 font-mono mt-1">{{ result.vd_vt }} <span class="text-xs text-slate-400">%</span></div>
                        </div>
                        <div class="glass-panel p-5 rounded-2xl text-center">
                            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest" data-i18n="shunt">Shunt</span>
                            <div class="text-2xl font-black text-cyan-400 font-mono mt-1">{{ result.shunt }} <span class="text-xs text-slate-400">%</span></div>
                        </div>
                    </div>

                    <!-- Hidden Data Elements for Real-Time Alarm Monitor -->
                    <div class="hidden">
                        <span id="val-pplat">{{ result.compliance and (request.form.get('vt_input', 500)|float / result.compliance) + request.form.get('peep', 5)|float or 15 }}</span>
                        <span id="val-pao2">{{ result.pao2 }}</span>
                    </div>

                    <!-- Action Plan -->
                    <div class="glass-panel p-6 rounded-3xl">
                        <h3 class="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-3" data-i18n="action_plan">Action Plan</h3>
                        <ul class="space-y-2">
                            {% for sol in result.ai_solutions %}
                            <li class="flex items-start text-xs text-slate-300 leading-relaxed bg-black/30 p-3 rounded-xl border border-white/5">
                                <span class="text-cyan-400 font-bold mr-2">›</span> {{ sol }}
                            </li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <!-- WORKSPACE TAB 2: ADVANCED TELEMETRY & WAVEFORMS -->
        <div id="section-analytics" class="workspace-section space-y-6 hidden">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="glass-panel p-6 rounded-3xl text-center">
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest" data-i18n="abg">Arterial Blood Gas</span>
                    <div class="mt-3 font-mono text-sm space-y-1">
                        <div>pH: <span class="text-cyan-400 font-bold">{{ result.ph }}</span></div>
                        <div>PaCO2: <span class="text-cyan-400 font-bold">{{ result.paco2 }} mmHg</span></div>
                        <div>PaO2: <span class="text-cyan-400 font-bold">{{ result.pao2 }} mmHg</span></div>
                        <div>HCO3: <span class="text-cyan-400 font-bold">{{ result.hco3 }} mEq/L</span></div>
                    </div>
                </div>
                <div class="glass-panel p-6 rounded-3xl text-center md:col-span-2 flex flex-col justify-center">
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest" data-i18n="mech_exp">Mechanics Explained</span>
                    <div class="mt-2 text-sm text-slate-300 font-mono">{{ result.acid_base_status }}</div>
                </div>
            </div>

            <!-- Waveform Telemetry Chart -->
            <div class="glass-panel p-6 rounded-3xl">
                <h3 class="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-4" data-i18n="graphs">Waveform Analytics</h3>
                <div class="relative h-[350px] w-full">
                    <canvas id="waveformChart"></canvas>
                </div>
            </div>
        </div>

        <!-- WORKSPACE TAB 3: CLINICAL PROTOCOLS -->
        <div id="section-protocols" class="workspace-section space-y-6 hidden">
            <div class="glass-panel p-8 rounded-3xl space-y-4">
                <h2 class="text-xl font-black text-white uppercase" data-i18n="tab_protocols">Clinical Protocols & Safety Directives</h2>
                <p class="text-xs text-slate-300 leading-relaxed">All synchronized presets adhere strictly to institutional mechanical ventilation guidelines, ARDSNet low tidal volume scaling, and physiologic acid-base balancing equations. Verify ventilator alarms and inspect patient circuit integrity continuously.</p>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
                    <div class="p-4 rounded-2xl bg-black/40 border border-white/10">
                        <h4 class="text-xs font-bold text-cyan-400 uppercase mb-1">Barotrauma Prevention</h4>
                        <p class="text-[11px] text-slate-400">Keep plateau pressures (Pplat) below 30 cmH2O and driving pressure below 15 cmH2O during volume control modes.</p>
                    </div>
                    <div class="p-4 rounded-2xl bg-black/40 border border-white/10">
                        <h4 class="text-xs font-bold text-cyan-400 uppercase mb-1">Permissive Hypercapnia</h4>
                        <p class="text-[11px] text-slate-400">Accept gradual rises in PaCO2 as long as arterial pH remains strictly above 7.20 to prevent volutrauma.</p>
                    </div>
                </div>
            </div>
        </div>

    </main>


<section id="nexus3-hero" class="relative overflow-hidden rounded-[2rem] border border-white/10 bg-gradient-to-br from-slate-900/95 via-slate-900/75 to-cyan-950/40 p-6 md:p-8 shadow-[0_25px_80px_rgba(0,0,0,.45)]">
  <canvas id="nexus3-particles" class="absolute inset-0 w-full h-full opacity-50 pointer-events-none"></canvas>
  <div class="relative z-10 grid grid-cols-1 xl:grid-cols-[1.5fr_.8fr] gap-6 items-center">
    <div>
      <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-400/10 border border-cyan-400/20 text-cyan-300 text-[10px] font-bold uppercase tracking-[.28em]"><span class="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span> NEXUS // ADAPTIVE CLINICAL SIM LAB</div>
      <h2 class="mt-4 text-4xl md:text-6xl font-black tracking-tight leading-none">Make physiology<br><span class="text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 via-sky-400 to-violet-400">visible.</span></h2>
      <p class="mt-4 max-w-2xl text-slate-300 text-sm md:text-base leading-7">A cinematic teaching environment for respiratory mechanics, gas exchange, ventilator telemetry and pattern recognition.</p>
      <div class="mt-6 flex flex-wrap gap-3">
        <button onclick="nexus3Scroll('nexus3-mission')" class="px-5 py-3 rounded-2xl bg-cyan-500 text-slate-950 font-black text-xs uppercase tracking-widest hover:bg-cyan-300 transition">Enter Mission Control</button>
        <button onclick="nexus3ToggleCinema()" id="nx3-cinema-btn" class="px-5 py-3 rounded-2xl bg-white/5 border border-white/10 text-white font-bold text-xs uppercase tracking-widest hover:bg-white/10 transition">Cinema Mode</button>
        <button onclick="nexus3Toast('Educational mode active — verify all outputs clinically.')" class="px-5 py-3 rounded-2xl bg-amber-400/10 border border-amber-300/20 text-amber-200 font-bold text-xs uppercase tracking-widest">Educational Mode</button>
      </div>
    </div>
    <div class="grid grid-cols-2 gap-3">
      <div class="rounded-3xl bg-black/30 border border-white/10 p-5"><div class="text-[10px] uppercase tracking-widest text-slate-500">System Mood</div><div id="nx3-mood" class="mt-2 text-2xl font-black text-cyan-300">CALM</div><div class="mt-1 text-[11px] text-slate-400">Adaptive visual state</div></div>
      <div class="rounded-3xl bg-black/30 border border-white/10 p-5"><div class="text-[10px] uppercase tracking-widest text-slate-500">Cases</div><div id="nx3-case-count" class="mt-2 text-2xl font-black text-white">0</div><div class="mt-1 text-[11px] text-slate-400">In your learning ledger</div></div>
      <div class="rounded-3xl bg-black/30 border border-white/10 p-5"><div class="text-[10px] uppercase tracking-widest text-slate-500">Focus</div><div id="nx3-focus" class="mt-2 text-2xl font-black text-violet-300">100%</div><div class="mt-1 text-[11px] text-slate-400">Interface clarity</div></div>
      <div class="rounded-3xl bg-black/30 border border-white/10 p-5"><div class="text-[10px] uppercase tracking-widest text-slate-500">Session</div><div id="nx3-session" class="mt-2 text-2xl font-black text-emerald-300">00:00</div><div class="mt-1 text-[11px] text-slate-400">Current workspace</div></div>
    </div>
  </div>
</section>
<section id="nexus3-mission" class="mt-6 grid grid-cols-1 xl:grid-cols-[1.05fr_.95fr] gap-6">
  <div class="glass-panel rounded-[2rem] p-6 border-white/10">
    <div class="flex items-center justify-between gap-4 mb-5">
      <div><div class="text-[10px] text-cyan-400 font-bold uppercase tracking-[.25em]">Mission Control</div><h3 class="text-2xl font-black text-white mt-1">Choose your case</h3></div>
      <div id="nx3-score" class="px-4 py-2 rounded-2xl bg-violet-500/10 border border-violet-400/20 text-violet-300 font-black text-sm">XP 0</div>
    </div>
    <div id="nx3-scenarios" class="grid grid-cols-1 md:grid-cols-2 gap-3"></div>
  </div>
  <div class="glass-panel rounded-[2rem] p-6 border-white/10 relative overflow-hidden">
    <div class="absolute -top-16 -right-16 w-40 h-40 bg-violet-500/10 blur-3xl rounded-full"></div>
    <div class="relative">
      <div class="flex items-center justify-between gap-3">
        <div><div class="text-[10px] text-violet-300 font-bold uppercase tracking-[.25em]">Decision Lens</div><h3 id="nx3-lens-title" class="text-2xl font-black text-white mt-1">Live physiology</h3></div>
        <div id="nx3-lens-risk" class="px-3 py-1.5 rounded-xl bg-emerald-400/10 border border-emerald-400/20 text-emerald-300 text-[10px] font-black uppercase tracking-widest">LOW RISK</div>
      </div>
      <p id="nx3-lens-sub" class="text-sm text-slate-400 mt-2">The lens now reads directly from the active simulator values.</p>
      <div class="mt-5 grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="rounded-2xl bg-black/25 border border-white/5 p-4"><div class="text-[10px] text-slate-500 uppercase">Pplat</div><div id="nx3-lens-pplat" class="text-xl font-black text-cyan-300 mt-1">—</div><div class="text-[9px] text-slate-500">cmH₂O</div></div>
        <div class="rounded-2xl bg-black/25 border border-white/5 p-4"><div class="text-[10px] text-slate-500 uppercase">Drive ΔP</div><div id="nx3-lens-drive" class="text-xl font-black text-cyan-300 mt-1">—</div><div class="text-[9px] text-slate-500">cmH₂O</div></div>
        <div class="rounded-2xl bg-black/25 border border-white/5 p-4"><div class="text-[10px] text-slate-500 uppercase">P/F</div><div id="nx3-lens-pf" class="text-xl font-black text-emerald-300 mt-1">—</div><div class="text-[9px] text-slate-500">oxygenation</div></div>
        <div class="rounded-2xl bg-black/25 border border-white/5 p-4"><div class="text-[10px] text-slate-500 uppercase">pH</div><div id="nx3-lens-ph" class="text-xl font-black text-violet-300 mt-1">—</div><div class="text-[9px] text-slate-500">acid-base</div></div>
      </div>
      <div class="mt-4 rounded-2xl bg-white/[.03] border border-white/10 p-4">
        <div class="flex items-center justify-between gap-3"><span class="text-[10px] uppercase tracking-widest text-slate-500">Interpretation</span><span id="nx3-lens-pulse" class="text-[10px] text-cyan-300 font-mono">SYNCED</span></div>
        <div id="nx3-lens-interpretation" class="text-sm text-slate-300 leading-6 mt-2">Select a scenario or change a ventilator parameter to generate a live interpretation.</div>
      </div>
      <div class="mt-4 flex flex-wrap gap-2"><button onclick="nexus3RandomCase()" class="px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white text-[10px] font-black uppercase tracking-widest">Surprise Me</button><button onclick="nexus3Quick('dashboard')" class="px-4 py-2.5 rounded-xl bg-cyan-500/10 border border-cyan-400/20 text-cyan-200 text-[10px] font-black uppercase tracking-widest">Open Simulator</button></div>
    </div>
  </div>
</section>
<section class="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
  <div class="glass-panel rounded-[2rem] p-6"><div class="text-[10px] text-cyan-400 font-bold uppercase tracking-[.25em]">Adaptive Insights</div><h3 class="text-xl font-black mt-1">What matters now?</h3><div id="nx3-insights" class="mt-4 space-y-3"></div></div>
  <div class="glass-panel rounded-[2rem] p-6"><div class="text-[10px] text-emerald-400 font-bold uppercase tracking-[.25em]">Live Pulse</div><h3 class="text-xl font-black mt-1">Telemetry heartbeat</h3><div class="mt-5 h-40"><canvas id="nx3-spark"></canvas></div></div>
  <div class="glass-panel rounded-[2rem] p-6"><div class="text-[10px] text-violet-300 font-bold uppercase tracking-[.25em]">Command Palette</div><h3 class="text-xl font-black mt-1">Fast actions</h3><div class="mt-4 grid grid-cols-2 gap-3"><button onclick="nexus3Quick('dashboard')" class="nx3-action">Workspace</button><button onclick="nexus3Quick('analytics')" class="nx3-action">Telemetry</button><button onclick="nexus3Quick('protocols')" class="nx3-action">Protocols</button><button onclick="nexus3Quick('top')" class="nx3-action">Top</button></div><div class="mt-4 text-[10px] text-slate-500">Tip: use <span class="font-mono text-slate-300">⌘/Ctrl + K</span> for search.</div></div>
</section>
<div id="nx3-toast" class="fixed right-5 bottom-5 z-[100] translate-y-24 opacity-0 transition-all duration-300 px-5 py-4 rounded-2xl bg-slate-900/95 border border-cyan-400/20 shadow-2xl max-w-sm text-xs text-slate-200"></div>
<style>
.nx3-action{padding:.8rem;border-radius:1rem;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;color:#cbd5e1;transition:.2s}.nx3-action:hover{background:rgba(34,211,238,.08);border-color:rgba(34,211,238,.25);color:#fff;transform:translateY(-2px)}
.nx3-cinema .glass-panel{box-shadow:0 0 0 1px rgba(34,211,238,.05),0 30px 100px rgba(0,0,0,.55)}
</style>
<script>
const NEXUS3_SCENARIOS={{ scenarios|tojson }}; let nx3Started=Date.now(),nx3XP=0,nx3Spark=null;
function nexus3Toast(t){const el=document.getElementById('nx3-toast');if(!el)return;el.innerText=t;el.classList.remove('translate-y-24','opacity-0');clearTimeout(window.__nx3toast);window.__nx3toast=setTimeout(()=>el.classList.add('translate-y-24','opacity-0'),2800)}
function nexus3Scroll(id){document.getElementById(id)?.scrollIntoView({behavior:'smooth',block:'start'})}
function nexus3Quick(tab){if(tab==='top')window.scrollTo({top:0,behavior:'smooth'});else if(typeof switchWorkspaceTab==='function')switchWorkspaceTab(tab)}
function nexus3ToggleCinema(){document.documentElement.classList.toggle('nx3-cinema');const b=document.getElementById('nx3-cinema-btn');if(b)b.innerText=document.documentElement.classList.contains('nx3-cinema')?'Exit Cinema':'Cinema Mode';nexus3Toast(document.documentElement.classList.contains('nx3-cinema')?'Cinema mode engaged':'Cinema mode closed')}
function nexus3ReadField(id,fallback=0){const e=document.getElementById(id);const n=parseFloat(e?.value);return Number.isFinite(n)?n:fallback}
function nexus3ClinicalLens(){
  const pplat=nexus3ReadField('pplat',15), peep=nexus3ReadField('peep',5), fio2=nexus3ReadField('fio2',30), pao2=parseFloat(document.getElementById('val-pao2')?.innerText||90), ph=parseFloat((document.querySelector('#section-analytics')?.innerText.match(/pH:\s*([0-9.]+)/)||[])[1]||7.4);
  const drive=pplat-peep, pf=fio2>0?pao2/(fio2/100):0; let risk=0, flags=[];
  if(pplat>30){risk+=35;flags.push('plateau pressure is above the 30 cmH₂O safety threshold');}
  if(drive>15){risk+=25;flags.push('driving pressure is above 15 cmH₂O');}
  if(pf<200){risk+=20;flags.push('oxygenation is reduced by the P/F ratio');}
  if(pao2<60){risk+=20;flags.push('PaO₂ is below 60 mmHg');}
  risk=Math.min(100,risk); const riskLabel=risk>=60?'HIGH RISK':risk>=30?'WATCH':'LOW RISK';
  const riskEl=document.getElementById('nx3-lens-risk'); if(riskEl){riskEl.innerText=riskLabel;riskEl.className='px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest '+(risk>=60?'bg-rose-400/10 border border-rose-400/20 text-rose-300':risk>=30?'bg-amber-400/10 border border-amber-400/20 text-amber-300':'bg-emerald-400/10 border border-emerald-400/20 text-emerald-300');}
  const set=(id,v)=>{const e=document.getElementById(id);if(e)e.innerText=v}; set('nx3-lens-pplat',pplat.toFixed(1)); set('nx3-lens-drive',drive.toFixed(1)); set('nx3-lens-pf',pf.toFixed(0)); set('nx3-lens-ph',ph.toFixed(2));
  set('nx3-lens-pulse',new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'}));
  set('nx3-lens-interpretation',flags.length?('Priority signals: '+flags.join('; ')+'.'):'No configured threshold alert detected. Compare the complete patient context, waveform pattern, and serial trends.');
}
function nexus3LoadScenario(s){const p=document.getElementById('preset_id');if(p)p.value=s.preset;const d=document.getElementById('preset-dropdown');if(d){d.value=s.preset;if(typeof loadPreset==='function')loadPreset(s.preset)}document.getElementById('nx3-lens-title').innerText=s.title;document.getElementById('nx3-lens-sub').innerText=s.subtitle+' • '+s.difficulty;nx3XP+=25;document.getElementById('nx3-score').innerText='XP '+nx3XP;setTimeout(nexus3ClinicalLens,100);nexus3Toast(s.title+' loaded into the simulator')}
function nexus3RenderScenarios(){const w=document.getElementById('nx3-scenarios');if(!w)return;w.innerHTML=NEXUS3_SCENARIOS.map(s=>`<button onclick='nexus3LoadScenario(${JSON.stringify(s)})' class="text-left rounded-3xl p-5 bg-white/[.03] border border-white/10 hover:border-cyan-400/30 hover:bg-cyan-400/[.04] transition group"><div class="flex items-center justify-between"><span class="text-[10px] uppercase tracking-[.2em] text-slate-500">${s.difficulty}</span><span class="w-2.5 h-2.5 rounded-full bg-${s.accent}-400"></span></div><div class="text-lg font-black text-white mt-3">${s.title}</div><div class="text-xs text-slate-400 mt-1">${s.subtitle}</div><div class="mt-4 text-[10px] uppercase tracking-widest text-cyan-300">Launch case →</div></button>`).join('')}
function nexus3RandomCase(){nexus3LoadScenario(NEXUS3_SCENARIOS[Math.floor(Math.random()*NEXUS3_SCENARIOS.length)]);nexus3Scroll('nexus3-mission')}
function nexus3Insights(){const vals=[['Model continuity','Compare the newest telemetry with your prior runs.','cyan'],['Guardrail','Review pressure and oxygenation thresholds before applying outputs clinically.','amber'],['Learning loop','Use pattern relationships rather than memorizing isolated numbers.','violet']];document.getElementById('nx3-insights').innerHTML=vals.map(v=>`<div class="p-3 rounded-2xl bg-black/20 border border-white/5"><div class="text-[10px] text-${v[2]}-300 font-bold uppercase tracking-widest">${v[0]}</div><div class="text-xs text-slate-400 mt-1 leading-5">${v[1]}</div></div>`).join('')}
function nexus3Particles(){const c=document.getElementById('nexus3-particles');if(!c)return;const x=c.getContext('2d');function size(){c.width=c.clientWidth*devicePixelRatio;c.height=c.clientHeight*devicePixelRatio;x.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0)}size();addEventListener('resize',size);const pts=Array.from({length:55},()=>({x:Math.random()*c.clientWidth,y:Math.random()*c.clientHeight,r:Math.random()*1.8+.3,vx:(Math.random()-.5)*.15,vy:(Math.random()-.5)*.15}));function loop(){x.clearRect(0,0,c.clientWidth,c.clientHeight);for(const p of pts){p.x+=p.vx;p.y+=p.vy;if(p.x<0)p.x=c.clientWidth;if(p.x>c.clientWidth)p.x=0;if(p.y<0)p.y=c.clientHeight;if(p.y>c.clientHeight)p.y=0;x.beginPath();x.arc(p.x,p.y,p.r,0,Math.PI*2);x.fillStyle='rgba(103,232,249,.45)';x.fill()}requestAnimationFrame(loop)}loop()}
function nexus3Sparkline(){const c=document.getElementById('nx3-spark');if(!c||typeof Chart==='undefined')return;const data=Array.from({length:24},(_,i)=>70+Math.sin(i/2.2)*12+Math.random()*8);nx3Spark=new Chart(c,{type:'line',data:{labels:data.map((_,i)=>i+1),datasets:[{data,borderColor:'#a78bfa',backgroundColor:'rgba(167,139,250,.08)',fill:true,borderWidth:2,tension:.4,pointRadius:0}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{display:false},y:{display:false}}}})}
setInterval(()=>{const sec=Math.floor((Date.now()-nx3Started)/1000),mm=String(Math.floor(sec/60)).padStart(2,'0'),ss=String(sec%60).padStart(2,'0'),e=document.getElementById('nx3-session');if(e)e.innerText=`${mm}:${ss}`},1000);
setInterval(()=>{const mood=document.getElementById('nx3-mood');if(mood)mood.innerText=['CALM','FOCUSED','ANALYTIC','ALERT'][Math.floor(Date.now()/5000)%4]},5000);
document.addEventListener('DOMContentLoaded',()=>{nexus3RenderScenarios();nexus3Insights();nexus3Particles();nexus3Sparkline();nexus3ClinicalLens();document.querySelectorAll('#calc-form input').forEach(e=>e.addEventListener('input',nexus3ClinicalLens));fetch('/api/nexus/history').then(r=>r.json()).then(d=>{document.getElementById('nx3-case-count').innerText=d.stats?.total||0}).catch(()=>{})})
</script>

    <div id="lyra-hub" class="fixed inset-0 z-[120] hidden siri-overlay items-center justify-center p-5">
      <div class="w-full max-w-2xl text-center">
        <button onclick="closeLyraHub()" class="absolute top-6 right-6 w-10 h-10 rounded-full bg-white/5 border border-white/10 text-slate-300">✕</button>
        <div class="text-[10px] uppercase tracking-[.35em] text-violet-300 font-black">LYRA</div>
        <div id="lyra-siri-orb" class="siri-orb mx-auto mt-8"></div>
        <div id="lyra-mode" class="mt-7 text-2xl md:text-4xl font-black text-white">Ready when you are</div>
        <div id="lyra-confidence" class="hidden">100%</div>
        <p id="lyra-siri-reply" class="mt-3 text-sm md:text-base text-slate-400 max-w-xl mx-auto min-h-[48px]">Ask for a pathology, telemetry, risk, a comparison, or a learning case.</p>
        <div class="mt-8 flex justify-center gap-3">
          <button id="lyra-voice-btn" onclick="toggleLyra()" class="px-6 py-3 rounded-full bg-white text-slate-950 text-xs font-black uppercase tracking-widest shadow-2xl">Tap to Talk</button>
          <button onclick="lyraToggleVoice()" class="px-5 py-3 rounded-full bg-white/5 border border-white/10 text-slate-200 text-xs font-bold">Voice</button>
        </div>
        <div class="mt-6 max-w-xl mx-auto flex gap-2">
          <input id="lyra-console" onkeydown="if(event.key==='Enter')submitLyraText()" placeholder="Or type to Lyra…" class="flex-1 glass-input px-4 py-3 rounded-full text-xs text-center">
          <button onclick="submitLyraText()" class="px-5 rounded-full bg-violet-600 text-white text-xs font-black">Send</button>
        </div>
        <div class="mt-5 flex flex-wrap justify-center gap-2">
          <button onclick="lyraRunQuick('load ARDS')" class="lyra-chip">ARDS</button>
          <button onclick="lyraRunQuick('show risk')" class="lyra-chip">Risk</button>
          <button onclick="lyraRunQuick('show telemetry')" class="lyra-chip">Telemetry</button>
          <button onclick="lyraRunQuick('compare COPD vs ARDS')" class="lyra-chip">Compare</button>
          <button onclick="lyraRunQuick('new case')" class="lyra-chip">Case</button>
        </div>
      </div>
    </div>
    <section id="operator-deck" class="hidden"></section>
<style>.lyra-chip,.deck-btn{padding:.55rem .7rem;border-radius:.75rem;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.08);font-size:9px;font-weight:900;letter-spacing:.12em;text-transform:uppercase;color:#cbd5e1;transition:.18s}.lyra-chip:hover,.deck-btn:hover{transform:translateY(-1px);border-color:rgba(139,92,246,.35);background:rgba(139,92,246,.08);color:white}.lyra-history-item{padding:.7rem .8rem;border-radius:.9rem;background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.055);font-size:10px}</style><script>function lyraHubRun(){const e=document.getElementById('lyra-hub-input');if(!e)return;const v=e.value.trim();if(!v)return;processLyraCommand(v,localStorage.getItem('selectedLang')||'en');e.value='';renderLyraHub()}async function lyraSaveNote(){const title=document.getElementById('lyra-note-title')?.value||'Lyra learning note',note=document.getElementById('lyra-note-text')?.value||'';if(!note.trim()){lyraSetStatus('Enter a note before saving.','alert');return}try{const r=await fetch('/api/nexus/journal',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,note,tag:'lyra'})});if(!r.ok)throw new Error();lyraSetStatus('Journal note saved.');lyraLog('save note','Journal note saved.');document.getElementById('lyra-note-text').value='';renderLyraHub()}catch(e){lyraSetStatus('Could not save the journal note.','alert')}}document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.shiftKey&&e.key.toLowerCase()==='l'){e.preventDefault();openLyraHub()}});</script>

    <button id="advanced-tools-fab" onclick="openAdvancedTools()" class="fixed right-5 bottom-5 z-[95] w-12 h-12 rounded-full bg-slate-900/90 border border-white/10 text-slate-300 shadow-2xl hover:text-white" title="Advanced tools">⌘</button>
    <div id="advanced-tools" class="fixed inset-0 z-[110] hidden bg-black/70 backdrop-blur-md p-5 items-end justify-center">
      <div class="w-full max-w-lg rounded-[2rem] glass-panel p-5 border-white/10">
        <div class="flex items-center justify-between"><div><div class="text-[10px] uppercase tracking-[.3em] text-cyan-300 font-black">Advanced tools</div><div class="text-lg font-black text-white">AEROLUNG Studio</div></div><button onclick="closeAdvancedTools()" class="w-9 h-9 rounded-full bg-white/5 text-slate-300">✕</button></div>
        <div class="grid grid-cols-2 gap-2 mt-5">
          <button class="deck-btn" onclick="closeAdvancedTools();switchWorkspaceTab('analytics')">Telemetry</button>
          <button class="deck-btn" onclick="closeAdvancedTools();switchWorkspaceTab('protocols')">Protocols</button>
          <button class="deck-btn" onclick="closeAdvancedTools();nexus3RandomCase()">Case Lab</button>
          <button class="deck-btn" onclick="closeAdvancedTools();lyraRunQuick('compare COPD vs ARDS')">Compare</button>
          <button class="deck-btn" onclick="closeAdvancedTools();document.getElementById('notes-modal')?.classList.remove('hidden')">Record Analyzer</button>
          <button class="deck-btn" onclick="closeAdvancedTools();window.location.href='/api/nexus/export?format=csv'">Export Ledger</button>
        </div>
      </div>
    </div>
    <style>
      #nexus3-hero,#nexus3-mission,#operator-deck,#advanced-command-center{display:none!important}
      #advanced-tools{display:flex}
      #lyra-hub{display:flex!important}
      #lyra-hub.hidden{display:none!important}
    </style>
    <script>
      function openAdvancedTools(){document.getElementById('advanced-tools')?.classList.remove('hidden')}
      function closeAdvancedTools(){document.getElementById('advanced-tools')?.classList.add('hidden')}
      function openLyraHub(){const h=document.getElementById('lyra-hub');if(h){h.classList.remove('hidden');h.classList.add('flex')}renderLyraHub();setTimeout(()=>document.getElementById('lyra-console')?.focus(),120)}
      function closeLyraHub(){const h=document.getElementById('lyra-hub');if(h){h.classList.add('hidden');h.classList.remove('flex')}if(lyraActive)toggleLyra()}
      function renderLyraHub(){const reply=document.getElementById('lyra-siri-reply');if(reply)reply.innerText=LYRA.lastReply||'Ask me anything about the simulator, telemetry, pathology presets, or learning cases.';const mode=document.getElementById('lyra-mode');if(mode)mode.innerText=lyraActive?'Listening…':'Ready when you are';const orb=document.getElementById('lyra-siri-orb');if(orb)orb.classList.toggle('listening',!!lyraActive)}
      function lyraSetStatus(msg,tone='normal'){const e=document.getElementById('lyra-status');if(e)e.innerText=msg;LYRA.lastReply=msg;const orb=document.getElementById('lyra-siri-orb');if(orb)orb.classList.toggle('listening',tone==='busy'||lyraActive);renderLyraHub()}
      function lyraSpeak(text,lang){if(LYRA.voiceOut&&'speechSynthesis'in window){window.speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);u.lang=lang==='es'?'es-ES':lang==='fr'?'fr-FR':'en-US';u.pitch=.96;u.rate=.96;window.speechSynthesis.speak(u)}}
      document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeLyraHub();closeAdvancedTools()}if((e.ctrlKey||e.metaKey)&&e.shiftKey&&e.key.toLowerCase()==='l'){e.preventDefault();openLyraHub();toggleLyra()}});
    </script>
    <!-- NLP CLINICAL RECORD ANALYZER MODAL -->
    <div id="notes-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md hidden p-4">
        <div class="glass-panel p-8 rounded-3xl max-w-lg w-full space-y-4 border border-white/10">
            <h3 class="text-lg font-black text-white uppercase">Clinical Record Synchronizer</h3>
            <p class="text-xs text-slate-300">Paste physician notes, patient presentation narratives, or EHR triage data below to automatically map pathology and calculate parameters:</p>
            <textarea id="patient_record_input" rows="6" class="w-full glass-input p-4 rounded-xl text-xs font-mono" placeholder="Enter clinical text here..."></textarea>
            <div class="flex space-x-3 pt-2">
                <button onclick="processClinicalNotes()" class="flex-1 py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 transition font-bold text-white text-xs uppercase tracking-wider glow-cyan">Process Record</button>
                <button onclick="document.getElementById('notes-modal').classList.add('hidden')" class="px-5 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 transition font-bold text-slate-300 text-xs uppercase">Cancel</button>
            </div>
        </div>
    </div>

    <!-- CHART.JS TELEMETRY RENDERING -->
    <script>
        const rawWaveform = {{ result.waveform_data | safe }};
        const ctx = document.getElementById('waveformChart').getContext('2d');
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: rawWaveform.t,
                datasets: [
                    { label: 'Pressure (cmH2O)', data: rawWaveform.p, borderColor: '#22d3ee', backgroundColor: 'rgba(34,211,238,0.05)', borderWidth: 2, tension: 0.3, fill: true, yAxisID: 'y' },
                    { label: 'Volume (mL)', data: rawWaveform.v, borderColor: '#34d399', borderWidth: 2, tension: 0.3, yAxisID: 'y1' }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { family: 'JetBrains Mono', size: 10 } } },
                    y: { type: 'linear', display: true, position: 'left', grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#22d3ee', font: { family: 'JetBrains Mono', size: 10 } } },
                    y1: { type: 'linear', display: true, position: 'right', grid: { drawOnChartArea: false }, ticks: { color: '#34d399', font: { family: 'JetBrains Mono', size: 10 } } }
                },
                plugins: { legend: { labels: { color: '#f8fafc', font: { family: 'Outfit', size: 11 } } } }
            }
        });
    </script>
</body>
"""

# ==========================================
# 4. FLASK ROUTING CONTROLLER
# ==========================================

@app.route("/", methods=["GET"])
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template_string(LOGIN_HTML)

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    
    if row and check_password_hash(row[1], password):
        session["user_id"] = row[0]
        session["username"] = username
        return redirect(url_for("dashboard"))
    
    flash("Invalid credentials")
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user_id" not in session:
        return redirect(url_for("index"))
        
    if request.method == "POST":
        new_username = request.form.get("new_username")
        new_password = request.form.get("new_password")
        
        if new_username or new_password:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            if new_username:
                try:
                    c.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, session["user_id"]))
                    session["username"] = new_username
                except Exception:
                    pass
            if new_password:
                hashed = generate_password_hash(new_password)
                c.execute("UPDATE users SET password = ? WHERE id = ?", (hashed, session["user_id"]))
            conn.commit()
            conn.close()
        return redirect(url_for("dashboard"))
        
    return render_template_string(SETTINGS_HTML)

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("index"))
        
    preset_id = request.form.get("preset_id", "healthy")
    custom_desc = request.form.get("custom_desc", "")
    custom_cond = request.form.get("custom_cond", "")
    custom_plan_str = request.form.get("custom_plan_str", "")
    
    inputs = {
        'vt_input': RespiratoryEngine.safe_float(request.form.get('vt_input'), 500),
        'rr': RespiratoryEngine.safe_float(request.form.get('rr'), 14),
        'pip': RespiratoryEngine.safe_float(request.form.get('pip'), 20),
        'pplat': RespiratoryEngine.safe_float(request.form.get('pplat'), 14),
        'peep': RespiratoryEngine.safe_float(request.form.get('peep'), 5),
        'peak_flow': RespiratoryEngine.safe_float(request.form.get('peak_flow'), 60),
        'fio2': RespiratoryEngine.safe_float(request.form.get('fio2'), 30),
        'ie_ratio': RespiratoryEngine.safe_float(request.form.get('ie_ratio'), 2.0),
        'cao2': RespiratoryEngine.safe_float(request.form.get('cao2'), 19.8),
        'cvo2': RespiratoryEngine.safe_float(request.form.get('cvo2'), 14.8),
        'cco2': RespiratoryEngine.safe_float(request.form.get('cco2'), 20.4),
        'peco2': RespiratoryEngine.safe_float(request.form.get('peco2'), 28),
        'vco2': RespiratoryEngine.safe_float(request.form.get('vco2'), 200),
        'hco3_input': RespiratoryEngine.safe_float(request.form.get('hco3_input'), 24)
    }
    
    result = RespiratoryEngine.calculate_simulation(inputs, preset_id, custom_desc, custom_cond, custom_plan_str)
    if request.method == 'POST':
        _save_simulation(result, inputs)
        _audit('SIMULATION_RUN', json.dumps({'preset_id': preset_id, 'condition': result.get('ai_condition')}))
    return render_template_string(DASHBOARD_HTML, result=result, DISEASE_PROFILES=DISEASE_PROFILES, scenarios=NEXUS3_SCENARIOS)


# ==========================================
# 5. NEXT-GENERATION COMMAND CENTER
# ==========================================
ADVANCED_COMMAND_CENTER = r"""
<section id="advanced-command-center" class="space-y-6 mt-8">
  <div class="glass-panel rounded-3xl p-6 border border-cyan-400/20 overflow-hidden relative">
    <div class="absolute -right-20 -top-20 w-56 h-56 rounded-full bg-cyan-500/10 blur-3xl"></div>
    <div class="relative flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
      <div>
        <div class="flex items-center gap-3"><span class="px-2 py-1 rounded-md bg-cyan-400/10 border border-cyan-400/20 text-cyan-300 text-[9px] font-bold uppercase tracking-widest">NEXUS v2</span><span id="nexus-status" class="text-[10px] text-emerald-400 font-mono">● ONLINE</span></div>
        <h2 class="text-2xl font-black mt-2">Advanced Command Center</h2>
        <p class="text-xs text-slate-400 mt-1 max-w-2xl">Longitudinal simulation history, safety scoring, live trend analytics, and export tools layered on top of the original AEROLUNG engine.</p>
      </div>
      <div class="flex flex-wrap gap-2"><button onclick="refreshNexus()" class="px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold uppercase tracking-wider">↻ Refresh</button><button onclick="exportNexus('json')" class="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-white/10 text-xs font-bold uppercase tracking-wider">Export JSON</button><button onclick="exportNexus('csv')" class="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-white/10 text-xs font-bold uppercase tracking-wider">Export CSV</button></div>
    </div>
  </div>
  <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
    <div class="glass-panel p-5 rounded-2xl"><span class="text-[9px] uppercase tracking-widest text-slate-500">Simulations</span><div id="nx-total" class="text-2xl font-black font-mono mt-1">—</div></div>
    <div class="glass-panel p-5 rounded-2xl"><span class="text-[9px] uppercase tracking-widest text-slate-500">Avg Compliance</span><div id="nx-compliance" class="text-2xl font-black font-mono mt-1 text-cyan-400">—</div></div>
    <div class="glass-panel p-5 rounded-2xl"><span class="text-[9px] uppercase tracking-widest text-slate-500">Avg P/F</span><div id="nx-pf" class="text-2xl font-black font-mono mt-1 text-amber-300">—</div></div>
    <div class="glass-panel p-5 rounded-2xl"><span class="text-[9px] uppercase tracking-widest text-slate-500">Safety Score</span><div id="nx-safety" class="text-2xl font-black font-mono mt-1 text-emerald-400">—</div></div>
    <div class="glass-panel p-5 rounded-2xl"><span class="text-[9px] uppercase tracking-widest text-slate-500">Current Risk</span><div id="nx-risk" class="text-2xl font-black font-mono mt-1 text-rose-300">—</div></div>
  </div>
  <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
    <div class="xl:col-span-2 glass-panel p-6 rounded-3xl"><div class="flex justify-between items-center mb-4"><div><h3 class="text-xs font-bold text-cyan-400 uppercase tracking-widest">Longitudinal Telemetry</h3><p class="text-[10px] text-slate-500 mt-1">Last 20 synchronized runs</p></div><select id="nx-chart-mode" onchange="refreshNexus()" class="glass-input rounded-lg px-3 py-2 text-[10px]"><option value="compliance">Compliance</option><option value="pao2">PaO2</option><option value="paco2">PaCO2</option><option value="shunt">Shunt</option><option value="vd_vt">Dead Space</option></select></div><div class="h-[320px]"><canvas id="nexusTrendChart"></canvas></div></div>
    <div class="glass-panel p-6 rounded-3xl"><h3 class="text-xs font-bold text-purple-400 uppercase tracking-widest mb-4">Current Safety Matrix</h3><div class="space-y-3 text-xs"><div class="flex justify-between p-3 rounded-xl bg-black/30 border border-white/5"><span>Pplat</span><b id="nx-pplat">—</b></div><div class="flex justify-between p-3 rounded-xl bg-black/30 border border-white/5"><span>Driving Pressure</span><b id="nx-driving">—</b></div><div class="flex justify-between p-3 rounded-xl bg-black/30 border border-white/5"><span>FiO₂</span><b id="nx-fio2">—</b></div><div class="flex justify-between p-3 rounded-xl bg-black/30 border border-white/5"><span>PaO₂/FiO₂</span><b id="nx-current-pf">—</b></div><div class="flex justify-between p-3 rounded-xl bg-black/30 border border-white/5"><span>pH</span><b id="nx-ph">—</b></div></div><div id="nx-alerts" class="mt-4 space-y-2"></div><p class="text-[9px] text-slate-500 mt-4 leading-relaxed">Decision-support visualization only. It does not replace bedside assessment, local protocols, or specialist judgment.</p></div>
  </div>
  <div class="glass-panel rounded-3xl p-6"><div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4"><div><h3 class="text-xs font-bold text-emerald-400 uppercase tracking-widest">Simulation Ledger</h3><p class="text-[10px] text-slate-500 mt-1">Persistent audit trail for your account</p></div><input id="nx-search" oninput="filterNexusHistory()" placeholder="Search pathology or status…" class="glass-input rounded-xl px-4 py-2 text-xs w-full md:w-72"></div><div class="overflow-x-auto"><table class="w-full text-left text-[10px] font-mono"><thead><tr class="text-slate-500 uppercase border-b border-white/10"><th class="py-3">Time</th><th>Pathology</th><th>Compliance</th><th>PaO₂</th><th>PaCO₂</th><th>P/F</th><th>Shunt</th><th>pH</th></tr></thead><tbody id="nx-history-body"><tr><td colspan="8" class="py-8 text-center text-slate-500">Loading ledger…</td></tr></tbody></table></div></div>
</section>
<script>
let nexusHistory=[]; let nexusChart=null;
async function nexusFetch(url){const r=await fetch(url,{headers:{'X-Requested-With':'XMLHttpRequest'}});if(!r.ok)throw new Error('Request failed');return r.json();}
function nexusNum(v,d=0){const n=parseFloat(v);return Number.isFinite(n)?n:d;}
function currentNexusRisk(){const pao2=nexusNum(document.getElementById('val-pao2')?.innerText,90),fio2=nexusNum(document.getElementById('fio2')?.value,30),peep=nexusNum(document.getElementById('peep')?.value,5),pplat=nexusNum(document.getElementById('pplat')?.value,15),rr=nexusNum(document.getElementById('rr')?.value,14),pf=fio2>0?pao2/(fio2/100):0;let risk=0,alerts=[];if(pplat>30){risk+=35;alerts.push('Pplat > 30 cmH₂O');}if(pplat-peep>15){risk+=25;alerts.push('Driving pressure > 15 cmH₂O');}if(pf<100){risk+=30;alerts.push('Very low P/F ratio');}else if(pf<200){risk+=15;alerts.push('Reduced P/F ratio');}if(pao2<60){risk+=20;alerts.push('PaO₂ < 60 mmHg');}if(rr>30){risk+=10;alerts.push('High respiratory rate');}risk=Math.min(100,risk);document.getElementById('nx-risk').innerText=risk+'%';document.getElementById('nx-safety').innerText=(100-risk)+'%';document.getElementById('nx-pplat').innerText=pplat.toFixed(1)+' cmH₂O';document.getElementById('nx-driving').innerText=(pplat-peep).toFixed(1)+' cmH₂O';document.getElementById('nx-fio2').innerText=fio2.toFixed(0)+'%';document.getElementById('nx-current-pf').innerText=pf.toFixed(0);document.getElementById('nx-ph').innerText=document.querySelector('#section-analytics')?.innerText.match(/pH:\s*([0-9.]+)/)?.[1]||'—';document.getElementById('nx-alerts').innerHTML=alerts.length?alerts.map(x=>`<div class="px-3 py-2 rounded-lg bg-rose-950/40 border border-rose-500/20 text-rose-300">⚠ ${x}</div>`).join(''):'<div class="px-3 py-2 rounded-lg bg-emerald-950/40 border border-emerald-500/20 text-emerald-300">✓ No threshold alert detected</div>';}
function renderNexusHistory(){const q=(document.getElementById('nx-search')?.value||'').toLowerCase(),body=document.getElementById('nx-history-body'),rows=nexusHistory.filter(x=>(x.condition+' '+x.acid_base_status).toLowerCase().includes(q));body.innerHTML=rows.length?rows.map(x=>`<tr class="border-b border-white/5 hover:bg-white/[0.03]"><td class="py-3 text-slate-500">${new Date(x.created_at).toLocaleString()}</td><td class="text-white">${x.condition||x.preset_id}</td><td>${nexusNum(x.compliance).toFixed(1)}</td><td>${nexusNum(x.pao2).toFixed(1)}</td><td>${nexusNum(x.paco2).toFixed(1)}</td><td>${x.fio2?(nexusNum(x.pao2)/(nexusNum(x.fio2)/100)).toFixed(0):'—'}</td><td>${nexusNum(x.shunt).toFixed(1)}%</td><td>${nexusNum(x.ph).toFixed(2)}</td></tr>`).join(''):'<tr><td colspan="8" class="py-8 text-center text-slate-500">No matching records.</td></tr>';}
function drawNexusChart(){const mode=document.getElementById('nx-chart-mode').value,labels=nexusHistory.slice().reverse().map(x=>new Date(x.created_at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})),data=nexusHistory.slice().reverse().map(x=>nexusNum(x[mode])),ctx=document.getElementById('nexusTrendChart');if(!ctx)return;if(nexusChart)nexusChart.destroy();nexusChart=new Chart(ctx,{type:'line',data:{labels,datasets:[{label:mode.toUpperCase(),data,borderColor:'#22d3ee',backgroundColor:'rgba(34,211,238,.08)',borderWidth:2,tension:.35,fill:true}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#f8fafc'}}},scales:{x:{ticks:{color:'#64748b'},grid:{color:'rgba(255,255,255,.04)'}},y:{ticks:{color:'#94a3b8'},grid:{color:'rgba(255,255,255,.04)'}}}}});}
async function refreshNexus(){try{const d=await nexusFetch('/api/nexus/history');nexusHistory=d.history||[];const s=d.stats||{};document.getElementById('nx-total').innerText=s.total||0;document.getElementById('nx-compliance').innerText=s.avg_compliance!=null?Number(s.avg_compliance).toFixed(1):'—';document.getElementById('nx-pf').innerText=s.avg_pf!=null?Number(s.avg_pf).toFixed(0):'—';renderNexusHistory();drawNexusChart();currentNexusRisk();document.getElementById('nexus-status').innerText='● SYNCED';}catch(e){document.getElementById('nexus-status').innerText='● OFFLINE';console.error(e);}}
function filterNexusHistory(){renderNexusHistory();} function exportNexus(fmt){window.location.href='/api/nexus/export?format='+encodeURIComponent(fmt);}
document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();document.getElementById('nx-search')?.focus();}if(e.key==='Escape')document.getElementById('notes-modal')?.classList.add('hidden');});
setTimeout(()=>{refreshNexus();currentNexusRisk();},300);setInterval(currentNexusRisk,5000);
setInterval(()=>{try{nexus3ClinicalLens();}catch(e){}},1000);
</script>
"""
DASHBOARD_HTML = DASHBOARD_HTML.replace('    </main>\n\n    <!-- NLP CLINICAL RECORD ANALYZER MODAL -->', ADVANCED_COMMAND_CENTER + '\n    </main>\n\n    <!-- NLP CLINICAL RECORD ANALYZER MODAL -->')

@app.route('/api/nexus/history')
def nexus_history():
    if not _login_required(): return {'error':'authentication_required'}, 401
    conn=sqlite3.connect(DB_NAME); conn.row_factory=sqlite3.Row
    rows=conn.execute("SELECT * FROM simulation_history WHERE user_id=? ORDER BY id DESC LIMIT 100",(session['user_id'],)).fetchall(); conn.close()
    history=[dict(r) for r in rows]; recent=history[:20]
    comps=[r['compliance'] for r in recent if r['compliance'] is not None]
    pfs=[r['pao2']/(r['fio2']/100.0) for r in recent if r['fio2'] and r['fio2']>0 and r['pao2'] is not None]
    return {'history':history[:20],'stats':{'total':len(history),'avg_compliance':sum(comps)/len(comps) if comps else None,'avg_pf':sum(pfs)/len(pfs) if pfs else None}}

@app.route('/api/nexus/export')
def nexus_export():
    if not _login_required(): return {'error':'authentication_required'}, 401
    import io,csv
    fmt=request.args.get('format','json').lower(); conn=sqlite3.connect(DB_NAME); conn.row_factory=sqlite3.Row
    rows=[dict(r) for r in conn.execute("SELECT * FROM simulation_history WHERE user_id=? ORDER BY id DESC",(session['user_id'],)).fetchall()]; conn.close(); _audit('EXPORT_HISTORY',fmt)
    if fmt=='csv':
        out=io.StringIO(); fields=list(rows[0].keys()) if rows else ['message']; w=csv.DictWriter(out,fieldnames=fields); w.writeheader(); w.writerows(rows if rows else [{'message':'No simulation history'}])
        from flask import Response
        return Response(out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=aerolung_simulation_history.csv'})
    from flask import Response
    return Response(json.dumps(rows,indent=2),mimetype='application/json',headers={'Content-Disposition':'attachment; filename=aerolung_simulation_history.json'})

@app.route('/api/nexus/clear',methods=['POST'])
def nexus_clear():
    if not _login_required(): return {'error':'authentication_required'}, 401
    conn=sqlite3.connect(DB_NAME); conn.execute("DELETE FROM simulation_history WHERE user_id=?",(session['user_id'],)); conn.commit(); conn.close(); _audit('CLEAR_HISTORY'); return {'ok':True}



# NEXUS v3 journal API
@app.route('/api/nexus/journal', methods=['GET','POST','DELETE'])
def nexus3_journal():
    if 'user_id' not in session: return {'error':'authentication_required'}, 401
    uid=session['user_id']; conn=sqlite3.connect(DB_NAME); conn.row_factory=sqlite3.Row
    try:
        if request.method=='POST':
            data=request.get_json(silent=True) or {}
            title=(data.get('title') or 'Untitled Case').strip()[:120]
            note=(data.get('note') or '').strip()[:5000]
            tag=(data.get('tag') or 'learning').strip()[:50]
            conn.execute('INSERT INTO case_journal(user_id,title,note,tag) VALUES(?,?,?,?)',(uid,title,note,tag)); conn.commit(); return {'ok':True}
        if request.method=='DELETE':
            conn.execute('DELETE FROM case_journal WHERE user_id=?',(uid,)); conn.commit(); return {'ok':True}
        rows=[dict(r) for r in conn.execute('SELECT * FROM case_journal WHERE user_id=? ORDER BY id DESC LIMIT 50',(uid,)).fetchall()]
        return {'journal':rows}
    finally: conn.close()

@app.route('/api/nexus/mission-pack')
def nexus3_mission_pack():
    if 'user_id' not in session: return {'error':'authentication_required'}, 401
    return {'missions':NEXUS3_SCENARIOS,'education_only':True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
