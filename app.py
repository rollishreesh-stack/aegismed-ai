import os
import math
import json
import sqlite3
import traceback
from flask import Flask, request, redirect, url_for, session, flash, render_template_string
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
            "Position the patient with the 'good lung down' to optimize perfusion, but occasionally rotate to facilitate drainage of the affected lobe.",
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
# 3. CLINICAL RECORD NLP COGNITIVE PARSER ENGINE
# ==========================================
class ClinicalNLPEngine:
    @staticmethod
    def parse_text_to_matrices(raw_text):
        if not raw_text or str(raw_text).strip() == "":
            return None

        normalized = raw_text.lower()
        matched_preset = "custom"
        scores = {k: 0 for k in DISEASE_PROFILES.keys()}
        
        keywords = {
            "ards": ["ards", "distress syndrome", "alveolar damage", "flooding", "shunting", "protective lung", "p/f ratio"],
            "copd": ["copd", "emphysema", "bronchitis", "hyperinflation", "air trapping", "auto-peep", "retainer"],
            "asthma": ["asthma", "bronchospasm", "status asthmaticus", "wheezing", "albuterol", "magnesium sulfate"],
            "fibrosis": ["fibrosis", "interstitial", "scarring", "stiff lung", "ipf", "restrictive defect"],
            "pe": ["embolism", "pulmonary embolism", "pe", "thrombus", "dead-space", "clot", "rv strain"],
            "pneumonia": ["pneumonia", "consolidation", "lobar", "purulent", "exudate", "infiltrate", "antibiotics"],
            "neuro": ["neuromuscular", "guillain", "myasthenia", "pump failure", "diaphragm", "weakness", "nif"],
            "obesity": ["obesity", "pickwickian", "hypoventilation syndrome", "adiposity", "extrinsic load"],
            "pneumothorax": ["pneumothorax", "tension", "collapsed lung", "pleural space", "needle decompression", "chest tube"],
            "edema": ["edema", "cardiogenic", "furosemide", "chf", "heart failure", "hydrostatic", "ventricular"],
            "cf": ["cystic fibrosis", "cf", "cftr", "mucus plugging", "dornase", "viscous"],
            "kypho": ["kyphoscoliosis", "scoliosis", "deformity", "thoracic spine", "structural restrictive"],
            "bronch": ["bronchiectasis", "dilated bronchi", "purulent sputum", "hemoptysis", "airway collapse"],
            "mild_ards": ["early ards", "mild ards", "leaking capillaries", "prophylactic peep"],
            "atelectasis": ["atelectasis", "lobar collapse", "resorption", "bronchoscopy", "plugging"],
            "flail": ["flail chest", "fractured ribs", "trauma", "paradoxical", "contusion"],
            "p_htn": ["pulmonary hypertension", "cor pulmonale", "nitric oxide", "afterload", "vascular resistance"],
            "co_poison": ["carbon monoxide", "co toxicity", "carboxyhemoglobin", "smoke inhalation", "hyperbaric"]
        }

        for preset, terms in keywords.items():
            for term in terms:
                if term in normalized:
                    scores[preset] += 3

        max_score = 0
        for preset, score in scores.items():
            if score > max_score:
                max_score = score
                matched_preset = preset

        if max_score == 0 and "healthy" in normalized:
            matched_preset = "healthy"

        extracted_inputs = {}
        import re
        
        patterns = {
            'vt_input': [r'vt\s*[:=]?\s*(\d+)', r'tidal\s*volume\s*[:=]?\s*(\d+)'],
            'rr': [r'rr\s*[:=]?\s*(\d+)', r'resp\s*rate\s*[:=]?\s*(\d+)', r'rate\s*[:=]?\s*(\d+)\s*bpm'],
            'peep': [r'peep\s*[:=]?\s*(\d+)'],
            'pplat': [r'pplat\s*[:=]?\s*(\d+)', r'plateau\s*[:=]?\s*(\d+)'],
            'pip': [r'pip\s*[:=]?\s*(\d+)', r'peak\s*pressure\s*[:=]?\s*(\d+)'],
            'fio2': [r'fio2\s*[:=]?\s*(\d+)', r'oxygen\s*[:=]?\s*(\d+)\s*%'],
            'hco3_input': [r'hco3\s*[:=]?\s*(\d+)', r'bicarb\s*[:=]?\s*(\d+)']
        }

        for key, regexes in patterns.items():
            for reg in regexes:
                match = re.search(reg, normalized)
                if match:
                    extracted_inputs[key] = float(match.group(1))
                    break

        return {
            "matched_preset": matched_preset,
            "extracted_inputs": extracted_inputs,
            "confidence_score": max_score
        }


# ==========================================
# 4. HTML, CSS & JAVASCRIPT TEMPLATES
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
    body { font-family: 'Outfit', sans-serif; background-color: #020617; color: #f8fafc; overflow-x: hidden; min-height: 100vh; display: flex; }
    .font-mono { font-family: 'JetBrains Mono', monospace; }
    @keyframes holographicBreathe { 0% { transform: translate(-50%, -50%) scale(0.97); opacity: 0.2; } 50% { transform: translate(-50%, -50%) scale(1.03); opacity: 0.6; } 100% { transform: translate(-50%, -50%) scale(0.97); opacity: 0.2; } }
    .living-lung { position: fixed; top: 50%; left: 50%; width: 100vw; max-width: 900px; z-index: 0; pointer-events: none; animation: holographicBreathe 5s ease-in-out infinite; }
    .glass-panel { background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.08); position: relative; z-index: 10; box-shadow: 0 15px 35px rgba(0,0,0,0.5); }
    .glass-input { background: rgba(0, 0, 0, 0.6); border: 1px solid rgba(255, 255, 255, 0.15); color: #fff; }
    .glass-input:focus { outline: none; border-color: #22d3ee; box-shadow: 0 0 10px rgba(34,211,238,0.3); }
    ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
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
    window.onload = updateClock;

    function copyConfiguration() {
        const dd = document.getElementById('preset-dropdown');
        const pathName = dd.options[dd.selectedIndex].text;
        const configText = `--- AEROLUNG SYNC EXPORT ---\nPathology: ${pathName}\n-----------------------------`;
        navigator.clipboard.writeText(configText).then(() => {
            const btn = document.getElementById('copy-btn');
            btn.innerText = "Copied!";
            setTimeout(() => { btn.innerText = "Copy Config"; }, 2000);
        });
    }
</script>
"""

LOGIN_HTML = GLOBAL_CSS_JS + BACKGROUND_SVG + """
<body class="flex items-center justify-center min-h-screen">
    <div class="glass-panel p-10 rounded-3xl w-full max-w-md text-center shadow-2xl border-t border-cyan-500/30">
        <h1 class="text-5xl font-black text-white mb-2">AERO<span class="text-cyan-400">LUNG</span></h1>
        <form action="/login" method="POST" class="space-y-4 text-left mt-8">
            <div><label class="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Architect ID</label><input type="text" name="username" class="w-full glass-input px-4 py-3 rounded-lg text-sm" required></div>
            <div><label class="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Passkey</label><input type="password" name="password" class="w-full glass-input px-4 py-3 rounded-lg text-sm" required></div>
            <button type="submit" class="w-full mt-4 py-3 rounded-lg bg-cyan-600 font-bold text-white uppercase text-xs tracking-wider">Initialize</button>
        </form>
    </div>
</body>
"""

SETTINGS_HTML = GLOBAL_CSS_JS + BACKGROUND_SVG + """
<body class="flex items-center justify-center relative flex-col min-h-screen">
    <nav class="glass-panel w-full bg-slate-950/90 py-4 px-6 flex justify-between absolute top-0 z-50">
        <h1 class="text-2xl font-black tracking-tighter text-white">AERO<span class="text-cyan-400">LUNG</span></h1>
        <a href="/dashboard" class="px-4 py-2 rounded-lg bg-slate-800 text-white text-xs font-bold uppercase">Return to Dashboard</a>
    </nav>
    <div class="glass-panel rounded-3xl p-10 w-full max-w-lg mt-20">
        <h2 class="text-3xl font-black text-white mb-2 uppercase">Settings</h2>
        <form action="/settings" method="POST" class="space-y-5 text-left">
            <div><label class="block text-[10px] font-bold text-cyan-400 uppercase tracking-widest mb-2">New ID</label><input type="text" name="new_username" class="w-full glass-input px-5 py-4 rounded-xl font-mono text-sm"></div>
            <div><label class="block text-[10px] font-bold text-cyan-400 uppercase tracking-widest mb-2">New Passkey</label><input type="password" name="new_password" class="w-full glass-input px-5 py-4 rounded-xl font-mono text-sm"></div>
            <button type="submit" class="w-full py-4 rounded-xl bg-cyan-600 text-white font-bold text-sm uppercase">Commit Changes</button>
        </form>
    </div>
</body>
"""

DASHBOARD_HTML = GLOBAL_CSS_JS + BACKGROUND_SVG + """
<body class="min-h-screen flex bg-slate-950/80">
    <aside class="w-[380px] shrink-0 glass-panel border-r border-white/5 flex flex-col justify-between sticky top-0 h-screen z-40 p-6 overflow-y-auto">
        <div class="space-y-5">
            <div class="flex items-center justify-between">
                <h1 class="text-3xl font-black text-white tracking-tighter">AERO<span class="text-cyan-400">LUNG</span></h1>
                <div class="flex items-center gap-2">
                    <a href="/settings" class="text-[9px] font-bold text-slate-300 uppercase border border-slate-700 bg-black/50 px-2 py-1.5 rounded">Settings</a>
                    <a href="/logout" class="text-[9px] font-bold text-rose-400 uppercase border border-rose-900/50 bg-rose-950/30 px-2 py-1.5 rounded">Logout</a>
                </div>
            </div>

            <div class="bg-black/40 border border-white/5 p-4 rounded-xl text-center">
                <div id="clock-time" class="text-cyan-400 font-mono font-bold text-2xl tracking-widest"></div>
                <div id="clock-day" class="text-slate-300 text-xs font-bold uppercase tracking-widest mt-1"></div>
                <div id="clock-date" class="text-slate-500 text-[10px] font-mono mt-0.5"></div>
            </div>

            <div class="bg-slate-900/90 border border-purple-500/30 p-4 rounded-2xl space-y-3 shadow-xl">
                <div class="flex items-center justify-between">
                    <span class="text-[10px] font-black text-purple-400 uppercase tracking-widest">NLP Clinical Analyzer (Exhaustive)</span>
                    <span class="w-2 h-2 rounded-full bg-purple-400 animate-pulse"></span>
                </div>
                <form action="/nlp_parse" method="POST" class="space-y-2">
                    <textarea name="nlp_text" rows="4" placeholder="Paste unstructured clinical dictation, physician notes... (e.g., 'ARDS patient found, VT=420, PEEP=12...')" class="w-full bg-black/60 border border-white/10 rounded-xl p-2.5 text-xs font-sans text-slate-200 focus:outline-none focus:border-purple-400 leading-normal">{% if last_nlp %}{{ last_nlp }}{% endif %}</textarea>
                    <button type="submit" class="w-full py-2 bg-gradient-to-r from-purple-700 to-indigo-700 hover:from-purple-600 hover:to-indigo-600 rounded-xl text-[11px] font-bold uppercase tracking-wider text-white transition">Execute NLP Parsing Extraction</button>
                </form>
                {% if nlp_meta %}
                <div class="bg-black/40 border border-purple-900/50 rounded-lg p-2 text-[10px] font-mono space-y-1 text-purple-300">
                    <div><strong>Matched Presets:</strong> {{ nlp_meta.matched_preset.upper() }}</div>
                    <div><strong>Score Weight:</strong> {{ nlp_meta.confidence_score }} pts</div>
                    <div><strong>Extracted Variables:</strong> {{ nlp_meta.extracted_inputs | string }}</div>
                </div>
                {% endif %}
            </div>

            <div>
                <label class="text-[10px] font-bold text-cyan-400 uppercase tracking-widest block mb-2">Pathology Matrix</label>
                <form id="calc-form" action="/calculate" method="POST" class="space-y-4">
                    <input type="hidden" id="preset_id" name="preset_id" value="{{ results.preset_id if results else 'healthy' }}">
                    
                    <select id="preset-dropdown" name="dropdown_preset" onchange="document.getElementById('preset_id').value=this.value; if(this.value !== 'custom') { document.getElementById('custom_ai_desc').value=''; document.getElementById('custom_ai_cond').value=''; document.getElementById('custom_ai_plan').value=''; } this.form.submit();" class="w-full glass-input px-4 py-3 rounded-lg text-xs font-semibold">
                        <option value="healthy" {% if results and results.preset_id == 'healthy' %}selected{% endif %}>Healthy Base</option>
                        <option value="ards" {% if results and results.preset_id == 'ards' %}selected{% endif %}>ARDS (Severe)</option>
                        <option value="copd" {% if results and results.preset_id == 'copd' %}selected{% endif %}>COPD / Emphysema</option>
                        <option value="asthma" {% if results and results.preset_id == 'asthma' %}selected{% endif %}>Status Asthmaticus</option>
                        <option value="fibrosis" {% if results and results.preset_id == 'fibrosis' %}selected{% endif %}>Advanced Fibrosis</option>
                        <option value="pe" {% if results and results.preset_id == 'pe' %}selected{% endif %}>Pulmonary Embolism</option>
                        <option value="pneumonia" {% if results and results.preset_id == 'pneumonia' %}selected{% endif %}>Severe Pneumonia</option>
                        <option value="neuro" {% if results and results.preset_id == 'neuro' %}selected{% endif %}>Neuromuscular Failure</option>
                        <option value="obesity" {% if results and results.preset_id == 'obesity' %}selected{% endif %}>Obesity Hypoventilation</option>
                        <option value="pneumothorax" {% if results and results.preset_id == 'pneumothorax' %}selected{% endif %}>Tension Pneumothorax</option>
                        <option value="edema" {% if results and results.preset_id == 'edema' %}selected{% endif %}>Cardiogenic Edema</option>
                        <option value="cf" {% if results and results.preset_id == 'cf' %}selected{% endif %}>Cystic Fibrosis Exac.</option>
                        <option value="kypho" {% if results and results.preset_id == 'kypho' %}selected{% endif %}>Kyphoscoliosis Decomp.</option>
                        <option value="bronch" {% if results and results.preset_id == 'bronch' %}selected{% endif %}>Bronchiectasis Exac.</option>
                        <option value="mild_ards" {% if results and results.preset_id == 'mild_ards' %}selected{% endif %}>Early / Mild ARDS</option>
                        <option value="atelectasis" {% if results and results.preset_id == 'atelectasis' %}selected{% endif %}>Major Atelectasis</option>
                        <option value="flail" {% if results and results.preset_id == 'flail' %}selected{% endif %}>Flail Chest Segment</option>
                        <option value="p_htn" {% if results and results.preset_id == 'p_htn' %}selected{% endif %}>Pulmonary HTN / Cor Pulm.</option>
                        <option value="co_poison" {% if results and results.preset_id == 'co_poison' %}selected{% endif %}>Carbon Monoxide Tox.</option>
                        <option value="ards_mod" {% if results and results.preset_id == 'ards_mod' %}selected{% endif %}>Moderate ARDS</option>
                        <option value="custom" {% if results and results.preset_id == 'custom' %}selected{% endif %}>Manual Override</option>
                    </select>

                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <label class="text-[9px] text-slate-400 uppercase font-bold">Tidal Volume (mL)</label>
                            <input type="number" id="vt_input" name="vt_input" value="{{ inputs.vt_input if inputs else 500 }}" class="w-full glass-input p-2 rounded text-xs font-mono">
                        </div>
                        <div>
                            <label class="text-[9px] text-slate-400 uppercase font-bold">Resp Rate (bpm)</label>
                            <input type="number" id="rr" name="rr" value="{{ inputs.rr if inputs else 14 }}" class="w-full glass-input p-2 rounded text-xs font-mono">
                        </div>
                        <div>
                            <label class="text-[9px] text-slate-400 uppercase font-bold">PEEP (cmH2O)</label>
                            <input type="number" id="peep" name="peep" value="{{ inputs.peep if inputs else 5 }}" class="w-full glass-input p-2 rounded text-xs font-mono">
                        </div>
                        <div>
                            <label class="text-[9px] text-slate-400 uppercase font-bold">Pplat (cmH2O)</label>
                            <input type="number" id="pplat" name="pplat" value="{{ inputs.pplat if inputs else 14 }}" class="w-full glass-input p-2 rounded text-xs font-mono">
                        </div>
                        <div>
                            <label class="text-[9px] text-slate-400 uppercase font-bold">PIP (cmH2O)</label>
                            <input type="number" id="pip" name="pip" value="{{ inputs.pip if inputs else 20 }}" class="w-full glass-input p-2 rounded text-xs font-mono">
                        </div>
                        <div>
                            <label class="text-[9px] text-slate-400 uppercase font-bold">FiO2 (%)</label>
                            <input type="number" id="fio2" name="fio2" value="{{ inputs.fio2 if inputs else 30 }}" class="w-full glass-input p-2 rounded text-xs font-mono">
                        </div>
                        <div>
                            <label class="text-[9px] text-slate-400 uppercase font-bold">Peak Flow (L/m)</label>
                            <input type="number" name="peak_flow" value="{{ inputs.peak_flow if inputs else 60 }}" class="w-full glass-input p-2 rounded text-xs font-mono">
                        </div>
                        <div>
                            <label class="text-[9px] text-slate-400 uppercase font-bold">PeCO2 (mmHg)</label>
                            <input type="number" name="peco2" value="{{ inputs.peco2 if inputs else 28 }}" class="w-full glass-input p-2 rounded text-xs font-mono">
                        </div>
                        <div>
                            <label class="text-[9px] text-slate-400 uppercase font-bold">CaO2 (vol%)</label>
                            <input type="number" name="cao2" value="{{ inputs.cao2 if inputs else 20 }}" class="w-full glass-input p-2 rounded text-xs font-mono">
                        </div>
                        <div>
                            <label class="text-[9px] text-slate-400 uppercase font-bold">CcO2 (vol%)</label>
                            <input type="number" name="cco2" value="{{ inputs.cco2 if inputs else 21 }}" class="w-full glass-input p-2 rounded text-xs font-mono">
                        </div>
                        <div>
                            <label class="text-[9px] text-slate-400 uppercase font-bold">CvO2 (vol%)</label>
                            <input type="number" name="cvo2" value="{{ inputs.cvo2 if inputs else 15 }}" class="w-full glass-input p-2 rounded text-xs font-mono">
                        </div>
                        <div>
                            <label class="text-[9px] text-slate-400 uppercase font-bold">HCO3 (mEq/L)</label>
                            <input type="number" name="hco3_input" value="{{ inputs.hco3_input if inputs else 24 }}" class="w-full glass-input p-2 rounded text-xs font-mono">
                        </div>
                        <div>
                            <label class="text-[9px] text-slate-400 uppercase font-bold">I:E Ratio (1:x)</label>
                            <input type="number" step="0.1" name="ie_ratio" value="{{ inputs.ie_ratio if inputs else 2 }}" class="w-full glass-input p-2 rounded text-xs font-mono">
                        </div>
                        <div>
                            <label class="text-[9px] text-slate-400 uppercase font-bold">VCO2 (mL/min)</label>
                            <input type="number" name="vco2" value="{{ inputs.vco2 if inputs else 200 }}" class="w-full glass-input p-2 rounded text-xs font-mono">
                        </div>
                    </div>

                    <div class="border-t border-white/5 pt-3 mt-2 space-y-2">
                        <label class="text-[9px] font-bold text-purple-400 uppercase tracking-widest block">Lyra Override Overlays</label>
                        <input type="text" id="custom_ai_cond" name="custom_ai_cond" placeholder="Condition Headline Override" value="{{ inputs.custom_ai_cond if inputs else '' }}" class="w-full glass-input p-2 rounded text-[11px]">
                        <textarea id="custom_ai_desc" name="custom_ai_desc" rows="2" placeholder="Full Clinical Analysis Override Body String..." class="w-full glass-input p-2 rounded text-[11px] leading-tight">{{ inputs.custom_ai_desc if inputs else '' }}</textarea>
                        <input type="text" id="custom_ai_plan" name="custom_ai_plan" placeholder='Action Plan JSON array' value="{{ inputs.custom_ai_plan if inputs else '' }}" class="w-full glass-input p-2 rounded text-[11px] font-mono">
                    </div>

                    <button type="submit" class="w-full py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 font-bold uppercase tracking-wider text-xs transition duration-200 shadow-lg shadow-cyan-950/50">Synchronize Data</button>
                </form>
            </div>
        </div>
        
        <div class="text-[10px] text-slate-500 font-mono text-center border-t border-white/5 pt-4">
            System Operating Normal | Core v4.11
        </div>
    </aside>

    <main class="flex-1 p-8 overflow-y-auto relative z-10 space-y-6">
        {% if results %}
        <div class="grid grid-cols-4 gap-4">
            <div class="glass-panel p-4 rounded-2xl border-l-4 border-cyan-500 flex flex-col justify-between">
                <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Compliance</div>
                <div class="text-3xl font-black text-cyan-400 mt-1 font-mono">{{ results.compliance }} <span class="text-xs text-slate-500">mL/cmH2O</span></div>
            </div>
            <div class="glass-panel p-4 rounded-2xl border-l-4 border-amber-500 flex flex-col justify-between">
                <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Resistance</div>
                <div class="text-3xl font-black text-amber-400 mt-1 font-mono">{{ results.resistance }} <span class="text-xs text-slate-500">cmH2O/L/s</span></div>
            </div>
            <div class="glass-panel p-4 rounded-2xl border-l-4 border-emerald-500 flex flex-col justify-between">
                <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Dead Space</div>
                <div class="text-3xl font-black text-emerald-400 mt-1 font-mono">{{ results.vd_vt }}% <span class="text-xs text-slate-500">Vd/Vt</span></div>
            </div>
            <div class="glass-panel p-4 rounded-2xl border-l-4 border-rose-500 flex flex-col justify-between">
                <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Shunt</div>
                <div class="text-3xl font-black text-rose-400 mt-1 font-mono">{{ results.shunt }}% <span class="text-xs text-slate-500">Qs/Qt</span></div>
            </div>
        </div>

        <div class="glass-panel rounded-3xl p-6 border-t border-cyan-500/20 shadow-2xl relative overflow-hidden">
            <div class="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none"></div>
            
            <div class="flex items-start justify-between">
                <div class="space-y-1">
                    <div class="flex items-center gap-2">
                        <span class="px-2.5 py-0.5 rounded bg-cyan-950/50 border border-cyan-500/30 text-cyan-400 text-[10px] font-bold uppercase tracking-wider">Primary Diagnosis</span>
                        <span class="px-2.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-400 text-[10px] font-mono">Engine-Match Confirmed</span>
                    </div>
                    <h2 class="text-2xl font-black text-white mt-2 tracking-tight">{{ results.ai_condition }}</h2>
                </div>
                <div class="flex gap-2">
                    <button id="copy-btn" onclick="copyConfiguration()" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs font-bold uppercase text-slate-300 transition">Copy Config</button>
                    <button onclick="wakeLyra()" class="px-3 py-1.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 rounded-lg text-xs font-bold uppercase text-white shadow-lg transition">Wake Lyra</button>
                </div>
            </div>

            <div class="grid grid-cols-3 gap-6 mt-6">
                <div class="col-span-2 space-y-4">
                    <div class="bg-black/30 border border-white/5 p-4 rounded-xl">
                        <h4 class="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-2">Pathophysiology Analysis</h4>
                        <p class="text-sm text-slate-300 leading-relaxed font-normal">{{ results.ai_description }}</p>
                    </div>
                    
                    <div class="bg-black/30 border border-white/5 p-4 rounded-xl">
                        <h4 class="text-xs font-bold text-amber-400 uppercase tracking-widest mb-2">Architective Action Protocols</h4>
                        <ul class="space-y-2">
                            {% for sol in results.ai_solutions %}
                            <li class="text-xs text-slate-300 flex items-start gap-2">
                                <span class="text-amber-500 font-bold mt-0.5 shrink-0">■</span>
                                <span>{{ sol }}</span>
                            </li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>

                <div class="space-y-4">
                    <div class="bg-black/40 border border-white/5 p-4 rounded-xl">
                        <h4 class="text-xs font-bold text-rose-400 uppercase tracking-widest mb-3">Arterial Blood Gas</h4>
                        <div class="space-y-2 font-mono text-xs">
                            <div class="flex justify-between border-b border-white/5 pb-1"><span class="text-slate-400">pH Index:</span><span class="font-bold text-white">{{ results.ph }}</span></div>
                            <div class="flex justify-between border-b border-white/5 pb-1"><span class="text-slate-400">PaCO2:</span><span class="font-bold text-white">{{ results.paco2 }} mmHg</span></div>
                            <div class="flex justify-between border-b border-white/5 pb-1"><span class="text-slate-400">PaO2 Matrix:</span><span class="font-bold text-white">{{ results.pao2 }} mmHg</span></div>
                            <div class="flex justify-between"><span class="text-slate-400">HCO3 Baseline:</span><span class="font-bold text-white">{{ results.hco3 }} mEq/L</span></div>
                        </div>
                        <div class="mt-3 text-[10px] text-purple-300 leading-tight bg-purple-950/30 border border-purple-900/50 p-2 rounded">
                            {{ results.acid_base_status }}
                        </div>
                    </div>

                    <div class="bg-black/40 border border-white/5 p-4 rounded-xl">
                        <h4 class="text-xs font-bold text-emerald-400 uppercase tracking-widest mb-2">Volumetric Metrics</h4>
                        <div class="space-y-1.5 text-xs">
                            <div class="flex justify-between font-mono"><span class="text-slate-400">Minute Vent:</span><span class="text-white font-bold">{{ results.minute_vent }} L/min</span></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="glass-panel p-6 rounded-3xl">
            <h3 class="text-sm font-bold uppercase text-slate-400 tracking-wider mb-4">Synchronous Waveform Analytics Loop</h3>
            <div class="h-64 w-full">
                <canvas id="waveformChart"></canvas>
            </div>
        </div>

        <div id="lyra-modal" class="fixed inset-0 bg-black/80 backdrop-blur-md z-50 hidden flex items-center justify-center p-4">
            <div class="glass-panel w-full max-w-lg rounded-3xl p-6 border border-cyan-500/30 shadow-2xl space-y-4">
                <div class="flex justify-between items-center border-b border-white/5 pb-3">
                    <div class="flex items-center gap-2">
                        <div class="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping"></div>
                        <h3 class="text-lg font-black tracking-tight text-white">Lyra Cognitive Clinical Agent</h3>
                    </div>
                    <button onclick="sleepLyra()" class="text-xs text-slate-400 hover:text-white uppercase font-bold">Disconnect</button>
                </div>
                <div class="h-48 overflow-y-auto bg-black/40 border border-white/5 rounded-xl p-4 font-mono text-xs space-y-3" id="lyra-terminal">
                    <p class="text-cyan-400">&gt; [LYRA PROTOCOL INITIALIZED]</p>
                    <p class="text-slate-300">&gt; Analyzing parameters: Comp {{ results.compliance }} | Res {{ results.resistance }} | Shunt {{ results.shunt }}%</p>
                    <p class="text-emerald-400">&gt; Primary Hypothesis: {{ results.ai_condition }}</p>
                </div>
                <div class="flex gap-2">
                    <input type="text" id="lyra-input" placeholder="Query Lyra on physiology changes..." class="flex-1 glass-input px-4 py-2 text-xs rounded-xl font-mono" onkeydown="if(event.key==='Enter') queryLyra();">
                    <button onclick="queryLyra()" class="px-4 py-2 bg-cyan-600 rounded-xl font-bold text-xs uppercase text-white">Execute</button>
                </div>
            </div>
        </div>

        <script>
            const wavePackets = JSON.parse({{ results.waveform_data | tojson | safe }});
            
            const ctx = document.getElementById('waveformChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: wavePackets.t,
                    datasets: [
                        { label: 'Pressure (cmH2O)', data: wavePackets.p, borderColor: '#22d3ee', borderWidth: 2, pointRadius: 0, fill: false, yAxisID: 'y' },
                        { label: 'Volume (mL)', data: wavePackets.v, borderColor: '#eab308', borderWidth: 2, pointRadius: 0, fill: false, yAxisID: 'y1' }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { grid: { color: 'rgba(255,255,255,0.03)' }, ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 9 } } },
                        y: { type: 'linear', display: true, position: 'left', grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#22d3ee' } },
                        y1: { type: 'linear', display: true, position: 'right', grid: { drawOnChartArea: false }, ticks: { color: '#eab308' } }
                    },
                    plugins: { legend: { labels: { color: '#f8fafc', font: { family: 'Outfit', size: 11 } } } }
                }
            });

            function wakeLyra() { document.getElementById('lyra-modal').classList.remove('hidden'); }
            function sleepLyra() { document.getElementById('lyra-modal').classList.add('hidden'); }
            
            function queryLyra() {
                const queryInput = document.getElementById('lyra-input');
                const query = queryInput.value.trim();
                if (!query) return;
                
                const term = document.getElementById('lyra-terminal');
                term.innerHTML += `<p class="text-slate-400">&gt; User: ${query}</p>`;
                term.scrollTop = term.scrollHeight;
                
                fetch('/lyra_query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        query: query,
                        compliance: "{{ results.compliance }}",
                        resistance: "{{ results.resistance }}",
                        shunt: "{{ results.shunt }}",
                        paco2: "{{ results.paco2 }}"
                    })
                })
                .then(res => res.json())
                .then(data => {
                    if(data.response) {
                        term.innerHTML += `<p class="text-cyan-300">&gt; Lyra: ${data.response}</p>`;
                    } else if(data.error) {
                        term.innerHTML += `<p class="text-rose-400">&gt; Lyra Error: ${data.error}</p>`;
                    }
                    term.scrollTop = term.scrollHeight;
                })
                .catch(err => {
                    term.innerHTML += `<p class="text-rose-500">&gt; Lyra Intercept Failure.</p>`;
                });
                
                queryInput.value = '';
            }
        </script>

        {% else %}
        <div class="glass-panel p-12 rounded-3xl text-center max-w-xl mx-auto mt-20 border border-white/5 shadow-2xl">
            <div class="w-16 h-16 bg-cyan-950/50 border border-cyan-500/30 rounded-2xl flex items-center justify-center mx-auto mb-4 animate-pulse">
                <span class="text-cyan-400 text-2xl">⚡</span>
            </div>
            <h2 class="text-2xl font-black text-white uppercase tracking-tight">System Standby</h2>
            <p class="text-slate-400 text-sm mt-2 leading-relaxed">Select a pathology matrix, execute manual parameter adjustments via the override engine, paste charting narratives into the NLP parser, or synchronize a data profile to populate continuous analytical waveforms.</p>
        </div>
        {% endif %}
    </main>
</body>
"""

# ==========================================
# 5. CONTROLLER LAYER / ROUTING
# ==========================================

@app.route('/')
def root():
    if "user" in session:
        return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    
    if row and check_password_hash(row[0], password):
        session['user'] = username
        return redirect(url_for('dashboard'))
    
    return redirect(url_for('root'))

@app.route('/dashboard')
def dashboard():
    if "user" not in session:
        return redirect(url_for('root'))
    return render_template_string(DASHBOARD_HTML, results=None, inputs=None, last_nlp="", nlp_meta=None)

@app.route('/nlp_parse', methods=['POST'])
def nlp_parse():
    if "user" not in session:
        return redirect(url_for('root'))
        
    raw_text = request.form.get('nlp_text', '')
    nlp_res = ClinicalNLPEngine.parse_text_to_matrices(raw_text)
    
    if not nlp_res:
        return redirect(url_for('dashboard'))
        
    preset_id = nlp_res['matched_preset']
    extracted = nlp_res['extracted_inputs']
    
    inputs = {
        'vt_input': extracted.get('vt_input', 500),
        'rr': extracted.get('rr', 14),
        'peep': extracted.get('peep', 5),
        'pplat': extracted.get('pplat', 14),
        'pip': extracted.get('pip', 20),
        'fio2': extracted.get('fio2', 30),
        'peak_flow': 60, 'peco2': 28, 'cao2': 20, 'cco2': 21, 'cvo2': 15,
        'hco3_input': extracted.get('hco3_input', 24),
        'ie_ratio': 2, 'vco2': 200,
        'custom_ai_cond': '', 'custom_ai_desc': '', 'custom_ai_plan': ''
    }
    
    results = RespiratoryEngine.calculate_simulation(inputs, preset_id=preset_id)
    return render_template_string(DASHBOARD_HTML, results=results, inputs=inputs, last_nlp=raw_text, nlp_meta=nlp_res)

@app.route('/calculate', methods=['POST'])
def calculate():
    if "user" not in session:
        return redirect(url_for('root'))
        
    inputs = {
        'vt_input': RespiratoryEngine.safe_float(request.form.get('vt_input'), 500),
        'rr': RespiratoryEngine.safe_float(request.form.get('rr'), 14),
        'peep': RespiratoryEngine.safe_float(request.form.get('peep'), 5),
        'pplat': RespiratoryEngine.safe_float(request.form.get('pplat'), 14),
        'pip': RespiratoryEngine.safe_float(request.form.get('pip'), 20),
        'fio2': RespiratoryEngine.safe_float(request.form.get('fio2'), 30),
        'peak_flow': RespiratoryEngine.safe_float(request.form.get('peak_flow'), 60),
        'peco2': RespiratoryEngine.safe_float(request.form.get('peco2'), 28),
        'cao2': RespiratoryEngine.safe_float(request.form.get('cao2'), 20),
        'cco2': RespiratoryEngine.safe_float(request.form.get('cco2'), 21),
        'cvo2': RespiratoryEngine.safe_float(request.form.get('cvo2'), 15),
        'hco3_input': RespiratoryEngine.safe_float(request.form.get('hco3_input'), 24),
        'ie_ratio': RespiratoryEngine.safe_float(request.form.get('ie_ratio'), 2),
        'vco2': RespiratoryEngine.safe_float(request.form.get('vco2'), 200),
        'custom_ai_cond': request.form.get('custom_ai_cond', ''),
        'custom_ai_desc': request.form.get('custom_ai_desc', ''),
        'custom_ai_plan': request.form.get('custom_ai_plan', '')
    }
    
    preset_id = request.form.get('preset_id', 'custom')
    results = RespiratoryEngine.calculate_simulation(
        inputs, 
        preset_id=preset_id,
        custom_desc=inputs['custom_ai_desc'],
        custom_cond=inputs['custom_ai_cond'],
        custom_plan_str=inputs['custom_ai_plan']
    )
    
    return render_template_string(DASHBOARD_HTML, results=results, inputs=inputs, last_nlp="", nlp_meta=None)

@app.route('/lyra_query', methods=['POST'])
def lyra_query():
    if "user" not in session:
        return json.dumps({"error": "Unauthorized session"}), 401
        
    data = request.get_json() or {}
    user_query = data.get("query", "").lower()
    
    try:
        comp = float(data.get("compliance", 50.0))
        res = float(data.get("resistance", 4.0))
        shunt = float(data.get("shunt", 5.0))
        paco2 = float(data.get("paco2", 40.0))
    except Exception:
        comp, res, shunt, paco2 = 50.0, 4.0, 5.0, 40.0
        
    if "compliance" in user_query or "stiff" in user_query:
        if comp < 30:
            reply = f"Critical lung stiffness detected. Compliance is severely dropped at {comp} mL/cmH2O. This mirrors high elastic recoil common in ARDS variants. Keep tidal volumes protective."
        else:
            reply = f"Compliance evaluates at {comp} mL/cmH2O. Intrinsic mechanical tissue elasticity is currently holding its threshold bounds."
    elif "resistance" in user_query or "airway" in user_query:
        if res > 15:
            reply = f"Airway resistance is critically elevated at {res} cmH2O/L/s. This implies high bronchospastic forces or airway obstruction. Investigate for auto-PEEP vectors immediately."
        else:
            reply = f"Airway resistance is tracking smoothly at {res} cmH2O/L/s. No severe bronchial choke alerts match this profile."
    elif "shunt" in user_query or "oxygen" in user_query:
        if shunt > 20:
            reply = f"Shunt fraction is calculated at a high risk level of {shunt}%. This confirms substantial unventilated perfusion zones. Recruitment strategies should be prioritized."
        else:
            reply = f"Intrapulmonary shunt calculations look stable at {shunt}%. Fluid barriers are tracking within optimal baselines."
    else:
        reply = f"Telemetry verified. Current metrics show Compliance: {comp} and Resistance: {res}. Data lines up with the current active rendering configuration loop."

    return json.dumps({"response": reply})

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if "user" not in session:
        return redirect(url_for('root'))
    if request.method == 'POST':
        new_user = request.form.get('new_username')
        new_pass = request.form.get('new_password')
        if new_user and new_pass:
            hashed = generate_password_hash(new_pass)
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("UPDATE users SET username=?, password=? WHERE username=?", (new_user, hashed, session['user']))
            conn.commit()
            conn.close()
            session['user'] = new_user
        return redirect(url_for('dashboard'))
    return render_template_string(SETTINGS_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('root'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
