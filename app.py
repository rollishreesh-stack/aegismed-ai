import os
import math
import json
import sqlite3
import traceback
import requests
from flask import Flask, request, redirect, url_for, session, render_template_string, jsonify
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
# 3. ADVANCED CARDIOPULMONARY ENGINE
# ==========================================
class AdvancedCardiopulmonaryEngine:
    @staticmethod
    def calculate_hemodynamics(inputs):
        """
        Calculates advanced hemodynamics including systemic oxygen delivery (DO2)
        and estimates the impact of Positive End-Expiratory Pressure (PEEP) on the myocardium.
        """
        fio2 = float(inputs.get('fio2', 21.0)) / 100.0
        paco2 = float(inputs.get('peco2', 40.0)) 
        hco3 = float(inputs.get('hco3_input', 24.0))
        hb = float(inputs.get('hemoglobin', 14.0)) 
        cardiac_output = float(inputs.get('cardiac_output', 5.0)) 
        peep = float(inputs.get('peep', 5.0))

        # 1. Alveolar Gas Equation (PAO2)
        p_A_O2 = round(((760 - 47) * fio2) - (paco2 / 0.8), 1)
        
        # 2. Henderson-Hasselbalch (pH)
        try:
            ph = round(6.1 + math.log10(hco3 / (0.0301 * paco2)), 2)
        except ValueError:
            ph = 7.40

        # 3. Arterial Oxygen Content (CaO2) and Delivery (DO2)
        sao2 = 0.98 if p_A_O2 > 80 else 0.88 
        cao2 = round((1.34 * hb * sao2) + (0.0031 * p_A_O2), 2)
        do2 = round(cardiac_output * cao2 * 10, 1)

        # 4. Myocardial Impact Estimate
        myocardial_impact = "Stable"
        if peep > 12:
            myocardial_impact = "Caution: High intrathoracic pressure may reduce venous return, potentially compromising coronary perfusion gradient."
        elif peep > 8 and cardiac_output < 4.0:
            myocardial_impact = "Warning: Elevated PEEP with low Cardiac Output detected. High risk of myocardial ischemia."

        return {
            "calculated_PAO2": p_A_O2,
            "calculated_pH": ph,
            "oxygen_content_CaO2": cao2,
            "oxygen_delivery_DO2": do2,
            "myocardial_impact": myocardial_impact
        }

# ==========================================
# 4. RESTful API INTEGRATION (Render Safe)
# ==========================================
@app.route('/api/gemini_analyze', methods=['POST'])
def gemini_rest_api():
    """Bypasses standard SDKs using direct HTTP requests to Google's API."""
    
    api_key = os.environ.get("GEMINI_API_KEY", "")
    data = request.json
    notes = data.get('notes', '')
    
    if not notes or not api_key:
        return jsonify({"error": "Missing notes or GEMINI_API_KEY not set in Render environment."}), 400
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"""
                You are Lyra, an advanced AI clinical assistant embedded in a ventilator system. 
                Analyze these clinical notes. 
                Notes: {notes}
                
                Respond ONLY with a raw JSON object containing:
                - "suspicion": (string) Primary diagnosis.
                - "evidence": (string) Key findings.
                - "missing": (string) Labs needed.
                - "treatments": (list of strings) 3 action items.
                - "presetMap": (string) One of: healthy, ards, copd, asthma, edema, pe, custom.
                Do not include markdown blocks like ```json.
                """
            }]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() 
        result_data = response.json()
        
        ai_text = result_data['candidates'][0]['content']['parts'][0]['text']
        clean_text = ai_text.replace('```json', '').replace('```', '').strip()
        
        return jsonify(json.loads(clean_text))
        
    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed: {e}")
        return jsonify({
            "error": "Failed to connect to Google API.", 
            "suspicion": "API Connection Timeout", 
            "presetMap": "custom"
        }), 500
    except (KeyError, json.JSONDecodeError) as e:
        print(f"JSON Parse failed: {e}")
        return jsonify({
            "error": "AI returned malformed data.", 
            "suspicion": "Parsing Error", 
            "presetMap": "custom"
        }), 500

@app.route('/api/hemodynamics', methods=['POST'])
def calculate_hemodynamics():
    """Endpoint for processing cardiopulmonary calculations."""
    data = request.json
    results = AdvancedCardiopulmonaryEngine.calculate_hemodynamics(data)
    return jsonify(results)

# ==========================================
# 5. MAIN APPLICATION EXECUTION
# ==========================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
