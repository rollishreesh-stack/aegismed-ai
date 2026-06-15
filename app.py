import os
import math
import json
import sqlite3
import traceback
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "aerolung_absolute_sync_2026")
DB_NAME = "aerolung_database.db"

# ==========================================
# GEMINI API INITIALIZATION
# ==========================================
if os.environ.get("GEMINI_API_KEY"):
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# ==========================================
# ADVANCED LLM-POWERED LUNG PATHOLOGY ANALYZER
# ==========================================
class NLPAnalyzer:
    @staticmethod
    def analyze_report(report_text):
        if not os.environ.get("GEMINI_API_KEY"):
            return {"error": "GEMINI_API_KEY environment variable is not configured."}
        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            prompt = f"""
            You are an elite expert critical care pulmonologist and medical NLP engine.
            Analyze the following unstructured patient clinical report or pathology notes. Identify the underlying lung pathology and determine the realistic respiratory parameters, descriptions, and solutions suitable for a lung simulation engine.
            
            Patient Report:
            "{report_text}"
            
            Provide your response strictly as a JSON object with the following keys and layout. Do NOT include markdown blocks like ```json.
            {{
                "condition": "Specific Diagnosis Name",
                "description": "A highly detailed pathophysiological breakdown of compliance, airway resistance, and exchange impacts.",
                "solutions": [
                    "Action plan item 1",
                    "Action plan item 2",
                    "Action plan item 3",
                    "Action plan item 4"
                ],
                "vt_input": 450,
                "peep": 10,
                "pplat": 25,
                "pip": 32,
                "peak_flow": 60,
                "fio2": 50,
                "rr": 16
            }}
            """
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json", "temperature": 0.2}
            )
            return json.loads(response.text.strip())
        except Exception as e:
            return {"error": f"NLP Engine Failure: {str(e)}"}

# ==========================================
# ADVANCED LIVE CONTEXT-AWARE LYRA ENGINE
# ==========================================
class LyraAssistant:
    @staticmethod
    def chat_response(user_message, active_patient_context, chat_history):
        if not os.environ.get("GEMINI_API_KEY"):
            return "Lyra System Offline: Please configure a GEMINI_API_KEY."
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            formatted_history = []
            for msg in chat_history:
                role = "model" if msg.get("sender") == "lyra" else "user"
                formatted_history.append({"role": role, "parts": [msg.get("text", "")]})
                
            system_instruction = f"""
            You are Lyra, an advanced Respiratory Care AI Assistant with master-level knowledge of mechanical ventilation, ABGs, and pulmonary physiology.
            You are actively monitoring a patient with the following simulated live parameters:
            - Pathology Group: {active_patient_context.get('ai_condition', 'Undifferentiated State')}
            - Pathophysiological Baseline: {active_patient_context.get('ai_description', 'Awaiting sync.')}
            - Measured Arterial pH: {active_patient_context.get('ph', 7.40)}
            - PaCO2: {active_patient_context.get('paco2', 40)} mmHg
            - PaO2: {active_patient_context.get('pao2', 95)} mmHg
            - Acid-Base Diagnosis: {active_patient_context.get('acid_base_status', 'Normal')}
            - Lung Compliance: {active_patient_context.get('compliance', 50)} mL/cmH2O
            - Airway Resistance: {active_patient_context.get('resistance', 5)} cmH2O/L/s
            - Shunt Fraction: {active_patient_context.get('shunt', 5)}%
            
            Guidelines:
            Act as an expert co-pilot. Be conversational yet professional. Address questions directly using the clinical numbers shown above.
            """
            chat = model.start_chat(history=formatted_history)
            response = chat.send_message(f"System Context: {system_instruction}\n\nUser Message: {user_message}")
            return response.text
        except Exception as e:
            return f"Lyra Connection Error: {str(e)}"

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
# 3. HTML, CSS & JAVASCRIPT
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
            "atelectasis_cond": "Atelectasia Lobar Mayor", "atelectasis_desc": "Pérdida aguda de volumen pulmonar debido al lóbulo colapsado, lo que resulta en una disminución de la distensibilidad.",
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

// ==========================================
// 1. NLP REPORT ANALYZER API CALL
// ==========================================
    async function analyzeReport() {
        const reportInput = document.getElementById('report_text_area'); 
        if (!reportInput || !reportInput.value.trim()) {
            alert("Please paste a clinical report first.");
            return;
        }

        const btn = document.getElementById('analyze_btn');
        const originalText = btn ? btn.innerText : "Analyze";
        if(btn) btn.innerText = "Analyzing Pathology...";

        try {
            const response = await fetch('/api/analyze-report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ report_text: reportInput.value })
            });

            const data = await response.json();
            
            if (data.error) {
                alert("Analysis Error: " + data.error);
            } else {
                document.querySelector('[name="vt_input"]').value = data.vt_input;
                document.querySelector('[name="peep"]').value = data.peep;
                document.querySelector('[name="pplat"]').value = data.pplat;
                document.querySelector('[name="pip"]').value = data.pip;
                document.querySelector('[name="peak_flow"]').value = data.peak_flow;
                document.querySelector('[name="fio2"]').value = data.fio2;
                document.querySelector('[name="rr"]').value = data.rr;

                document.querySelector('[name="custom_ai_cond"]').value = data.condition;
                document.querySelector('[name="custom_ai_desc"]').value = data.description;
                document.querySelector('[name="custom_ai_plan"]').value = JSON.stringify(data.solutions);
                
                document.querySelector('[name="preset_id"]').value = "custom";

                alert(`Analysis Complete: ${data.condition}\nClick 'Synchronize Data' to apply parameters.`);
            }
        } catch (err) {
            alert("API Connection Failed. Check console.");
            console.error(err);
        } finally {
            if(btn) btn.innerText = originalText;
        }
    }

    // ==========================================
    // 2. LYRA CHAT ASSISTANT API CALL
    // ==========================================
    let lyraChatHistory = [];

    async function sendToLyra() {
        const inputEl = document.getElementById('lyra_chat_input'); 
        if (!inputEl) return;
        const message = inputEl.value.trim();
        if (!message) return;

        appendMessageToUI("User", message);
        lyraChatHistory.push({ sender: "user", text: message });
        inputEl.value = '';

        try {
            const response = await fetch('/api/lyra-chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message, 
                    history: lyraChatHistory 
                })
            });

            const data = await response.json();
            const reply = data.reply || data.error;
            
            appendMessageToUI("Lyra", reply);
            lyraChatHistory.push({ sender: "lyra", text: reply });

        } catch (err) {
            appendMessageToUI("System", "Error connecting to Lyra's core.");
            console.error(err);
        }
    }

    function appendMessageToUI(sender, text) {
        const chatBox = document.getElementById('lyra_chat_window'); 
        if (chatBox) {
            const msgDiv = document.createElement('div');
            msgDiv.innerHTML = `<strong>${sender}:</strong> ${text}`;
            msgDiv.style.marginBottom = "10px";
            msgDiv.style.color = sender === "Lyra" ? "#22d3ee" : "#fff";
            chatBox.appendChild(msgDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        } else {
            console.log(`${sender}: ${text}`);
        }
    }
</script>
"""

LOGIN_HTML = GLOBAL_CSS_JS + BACKGROUND_SVG + """
<body class="flex items-center justify-center min-h-screen">
    <div class="glass-panel p-10 rounded-3xl w-full max-w-md text-center shadow-2xl border-t border-cyan-500/30">
        <h1 class="text-5xl font-black text-white mb-2" data-i18n="brand">AERO<span class="text-cyan-400">LUNG</span></h1>
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
        <h1 class="text-2xl font-black tracking-tighter text-white" data-i18n="brand">AERO<span class="text-cyan-400">LUNG</span></h1>
        <a href="/dashboard" class="px-4 py-2 rounded-lg bg-slate-800 text-white text-xs font-bold uppercase" data-i18n="return_dash">Return to Dashboard</a>
    </nav>
    <div class="glass-panel rounded-3xl p-10 w-full max-w-lg mt-20">
        <h2 class="text-3xl font-black text-white mb-2 uppercase" data-i18n="settings">Settings</h2>
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
    
    <aside class="w-[360px] shrink-0 glass-panel border-r border-white/5 flex flex-col justify-between sticky top-0 h-screen z-40 p-6 overflow-y-auto">
        <div class="space-y-5">
            <div>
                <h1 class="text-3xl font-black text-white tracking-tighter" data-i18n="brand">AERO<span class="text-cyan-400">LUNG</span></h1>
                <div class="flex items-center gap-3 mt-4">
                    <select id="lang-selector" onchange="changeLanguage(this.value)" class="bg-black/50 border border-slate-700 text-slate-300 text-[10px] font-bold uppercase rounded-lg px-2 py-1.5 cursor-pointer">
                        <option value="en">EN</option><option value="es">ES</option><option value="fr">FR</option>
                    </select>
                    <a href="/settings" class="text-[9px] font-bold text-slate-300 uppercase border border-slate-700 bg-black/50 px-2 py-1.5 rounded" data-i18n="settings">Settings</a>
                    <a href="/logout" class="text-[9px] font-bold text-rose-400 uppercase border border-rose-900/50 bg-rose-950/30 px-2 py-1.5 rounded" data-i18n="logout">Logout</a>
                </div>
            </div>

            <div class="bg-black/40 border border-white/5 p-4 rounded-xl text-center">
                <div id="clock-time" class="text-cyan-400 font-mono font-bold text-2xl"></div>
                <div id="clock-day" class="text-slate-300 text-xs font-bold uppercase tracking-widest mt-1"></div>
                <div id="clock-date" class="text-slate-500 text-[10px] font-mono mt-0.5"></div>
            </div>

            <div class="bg-purple-950/20 border border-purple-500/30 p-4 rounded-xl text-center shadow-[0_0_15px_rgba(147,51,234,0.1)]">
                <button id="lyra-btn" onclick="toggleLyra()" class="w-full py-3 rounded-lg bg-purple-600 font-bold text-white text-xs uppercase tracking-wider transition-all shadow-[0_0_15px_rgba(147,51,234,0.3)]" data-i18n="lyra_btn">Wake Lyra</button>
                <div id="lyra-status" class="text-[9px] text-purple-300 font-mono mt-3" data-i18n="lyra_status">Lyra Sleeping</div>
                
                <button type="button" onclick="document.getElementById('notes-modal').classList.remove('hidden')" class="w-full py-2 mt-3 rounded border border-emerald-600/50 bg-emerald-900/30 text-emerald-400 font-bold text-[10px] uppercase tracking-wider transition-all hover:bg-emerald-900/50 shadow-[0_0_10px_rgba(16,185,129,0.1)]">Analyze Patient Record</button>
            </div>

            <div>
                <label class="text-[10px] font-bold text-cyan-400 uppercase tracking-widest block mb-2" data-i18n="db_title">Pathology Matrix</label>
                <select id="preset-dropdown" onchange="document.getElementById('custom_ai_desc').value=''; if(this.value) loadPreset(this.value);" class="w-full glass-input px-3 py-2 rounded-lg text-xs font-semibold">
                    <option value="" disabled {% if not current_preset %}selected{% endif %} data-i18n="select_preset">-- Select Pathology --</option>
                    <option value="healthy" {% if current_preset == 'healthy' %}selected{% endif %}>Healthy Baseline</option>
                    <option value="mild_ards" {% if current_preset == 'mild_ards' %}selected{% endif %}>Mild ARDS</option>
                    <option value="ards_mod" {% if current_preset == 'ards_mod' %}selected{% endif %}>Moderate ARDS</option>
                    <option value="ards" {% if current_preset == 'ards' %}selected{% endif %}>Severe ARDS</option>
                    <option value="copd" {% if current_preset == 'copd' %}selected{% endif %}>End-Stage COPD</option>
                    <option value="asthma" {% if current_preset == 'asthma' %}selected{% endif %}>Status Asthmaticus</option>
                    <option value="fibrosis" {% if current_preset == 'fibrosis' %}selected{% endif %}>Pulmonary Fibrosis</option>
                    <option value="pe" {% if current_preset == 'pe' %}selected{% endif %}>Massive Pulm Embolism</option>
                    <option value="pneumonia" {% if current_preset == 'pneumonia' %}selected{% endif %}>Severe Pneumonia</option>
                    <option value="neuro" {% if current_preset == 'neuro' %}selected{% endif %}>Neuromuscular Failure</option>
                    <option value="obesity" {% if current_preset == 'obesity' %}selected{% endif %}>Obesity Hypoventilation</option>
                    <option value="pneumothorax" {% if current_preset == 'pneumothorax' %}selected{% endif %}>Tension Pneumothorax</option>
                    <option value="edema" {% if current_preset == 'edema' %}selected{% endif %}>Cardiogenic Edema</option>
                    <option value="cf" {% if current_preset == 'cf' %}selected{% endif %}>Cystic Fibrosis</option>
                    <option value="kypho" {% if current_preset == 'kypho' %}selected{% endif %}>Kyphoscoliosis</option>
                    <option value="bronch" {% if current_preset == 'bronch' %}selected{% endif %}>Bronchiectasis</option>
                    <option value="atelectasis" {% if current_preset == 'atelectasis' %}selected{% endif %}>Lobar Atelectasis</option>
                    <option value="flail" {% if current_preset == 'flail' %}selected{% endif %}>Flail Chest Trauma</option>
                    <option value="p_htn" {% if current_preset == 'p_htn' %}selected{% endif %}>Pulmonary HTN</option>
                    <option value="co_poison" {% if current_preset == 'co_poison' %}selected{% endif %}>Carbon Monoxide Poisoning</option>
                    <option value="custom" {% if current_preset == 'custom' %}selected{% endif %} hidden>Custom Override</option>
                </select>
            </div>

            <form id="calc-form" method="POST" action="/dashboard" class="border-t border-white/10 pt-4">
                <input type="hidden" name="preset_id" id="preset_id" value="{{ current_preset }}">
                <input type="hidden" name="custom_ai_desc" id="custom_ai_desc" value="{{ inputs.custom_ai_desc|default('') }}">
                <input type="hidden" name="custom_ai_cond" id="custom_ai_cond" value="{{ inputs.custom_ai_cond|default('') }}">
                <input type="hidden" name="custom_ai_plan" id="custom_ai_plan" value="{{ inputs.custom_ai_plan|default('') }}">
                
                <div class="flex justify-between items-center mb-4">
                    <label class="text-[10px] font-bold text-cyan-400 uppercase tracking-widest block" data-i18n="override">Manual Override</label>
                    <button type="button" id="copy-btn" onclick="copyConfiguration()" class="bg-slate-800 text-cyan-300 text-[8px] uppercase font-bold px-2 py-1 rounded transition-colors" data-i18n="copy_btn">Copy Config</button>
                </div>
                
                <div class="grid grid-cols-2 gap-3 mb-4">
                    <div><label class="text-[9px] text-slate-400 uppercase font-bold block mb-1">Vt (mL)</label><input type="number" name="vt_input" id="vt_input" value="{{ inputs.vt_input|default(500) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono" oninput="document.getElementById('preset-dropdown').value='custom'; document.getElementById('preset_id').value='custom';"></div>
                    <div><label class="text-[9px] text-slate-400 uppercase font-bold block mb-1">Rate (bpm)</label><input type="number" name="rr" id="rr" value="{{ inputs.rr|default(14) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono"></div>
                    
                    <div><label class="text-[9px] text-slate-400 uppercase font-bold block mb-1">PIP</label><input type="number" name="pip" id="pip" value="{{ inputs.pip|default(20) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-rose-300"></div>
                    <div><label class="text-[9px] text-slate-400 uppercase font-bold block mb-1">Pplat</label><input type="number" name="pplat" id="pplat" value="{{ inputs.pplat|default(14) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-rose-300"></div>
                    
                    <div><label class="text-[9px] text-slate-400 uppercase font-bold block mb-1">PEEP</label><input type="number" name="peep" id="peep" value="{{ inputs.peep|default(5) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-cyan-300"></div>
                    <div><label class="text-[9px] text-slate-400 uppercase font-bold block mb-1">Flow (L/m)</label><input type="number" name="peak_flow" id="peak_flow" value="{{ inputs.peak_flow|default(60) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono"></div>
                    
                    <div><label class="text-[9px] text-slate-400 uppercase font-bold block mb-1">FiO2 (%)</label><input type="number" name="fio2" id="fio2" value="{{ inputs.fio2|default(30) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono"></div>
                    <div><label class="text-[9px] text-slate-400 uppercase font-bold block mb-1">I:E Ratio</label><input type="number" step="0.1" name="ie_ratio" id="ie_ratio" value="{{ inputs.ie_ratio|default(2.0) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono"></div>
                    
                    <div><label class="text-[9px] text-slate-400 uppercase font-bold block mb-1">CaO2</label><input type="number" step="0.1" name="cao2" id="cao2" value="{{ inputs.cao2|default(19.8) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-emerald-300"></div>
                    <div><label class="text-[9px] text-slate-400 uppercase font-bold block mb-1">CvO2</label><input type="number" step="0.1" name="cvo2" id="cvo2" value="{{ inputs.cvo2|default(14.8) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-emerald-300"></div>
                    
                    <div><label class="text-[9px] text-slate-400 uppercase font-bold block mb-1">CcO2</label><input type="number" step="0.1" name="cco2" id="cco2" value="{{ inputs.cco2|default(20.4) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-emerald-300"></div>
                    <div><label class="text-[9px] text-slate-400 uppercase font-bold block mb-1">PECO2</label><input type="number" name="peco2" id="peco2" value="{{ inputs.peco2|default(28) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-amber-300"></div>
                    
                    <div><label class="text-[9px] text-slate-400 uppercase font-bold block mb-1">VCO2</label><input type="number" name="vco2" id="vco2" value="{{ inputs.vco2|default(200) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-amber-300"></div>
                    <div><label class="text-[9px] text-slate-400 uppercase font-bold block mb-1">HCO3</label><input type="number" name="hco3_input" id="hco3_input" value="{{ inputs.hco3_input|default(24) }}" class="w-full glass-input px-2 py-1.5 rounded text-xs font-mono text-purple-300"></div>
                </div>

                <button type="submit" class="w-full py-3 mt-2 rounded bg-cyan-600 text-white font-bold text-xs uppercase shadow-[0_0_15px_rgba(34,211,238,0.2)]" data-i18n="btn_scan">Synchronize Data</button>
            </form>
        </div>
        
        <div class="border-t border-slate-800/80 pt-4 text-center mt-4">
            <p class="text-[10px] text-slate-500 font-mono tracking-wide">&copy; 2026 Shreesh Santoshkumar Rolli. All Rights Reserved.</p>
        </div>
    </aside>

    <main class="flex-1 p-6 overflow-y-auto w-full relative z-10">
        {% if not sim_data %}
        <div class="glass-panel rounded-3xl h-[600px] flex flex-col items-center justify-center text-center p-8 border-dashed border-white/10 shadow-2xl">
            <h2 class="text-3xl font-black text-white uppercase tracking-tight mb-2" data-i18n="standby_title">System Standby</h2>
            <p class="text-sm text-slate-400 font-mono" data-i18n="standby_desc">Select pathology, scan patient record, or activate Lyra.</p>
        </div>
        {% else %}
        
        <input type="hidden" id="current_preset_id" value="{{ sim_data.preset_id }}">
        
        <div class="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
            <div class="glass-panel p-8 rounded-2xl border-l-4 border-l-cyan-400 bg-gradient-to-br from-slate-900/90 to-black">
                <h3 class="text-[10px] font-bold uppercase tracking-widest text-cyan-400 mb-1" data-i18n="primary_diag">Primary Diagnosis</h3>
                <div id="ai-cond" class="text-3xl font-black text-white uppercase mb-4">{{ sim_data.ai_condition }}</div>
                
                <h4 class="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-1" data-i18n="physio">Physiology</h4>
                <p id="ai-desc" class="text-sm text-slate-300 bg-black/40 p-4 rounded-lg border border-white/5 mb-4 whitespace-pre-wrap">{{ sim_data.ai_description }}</p>
                
                <h4 class="text-[9px] font-bold text-emerald-500 uppercase tracking-widest mb-1" data-i18n="action_plan">Action Plan</h4>
                <ul class="space-y-2">
                    {% for sol in sim_data.ai_solutions %}
                    <li class="flex items-start gap-2 bg-emerald-950/20 p-2.5 rounded-lg border border-emerald-900/30 text-xs text-slate-200">
                        <span class="text-emerald-500 font-bold mt-0.5">⯈</span> <span>{{ sol }}</span>
                    </li>
                    {% endfor %}
                </ul>
            </div>

            <div class="glass-panel p-8 rounded-2xl border-t-4 border-t-purple-500 flex flex-col justify-center">
                <h3 class="text-[10px] font-bold uppercase tracking-widest text-purple-400 mb-6 text-center" data-i18n="abg">Arterial Blood Gas</h3>
                <div class="grid grid-cols-3 gap-2 bg-black/40 p-6 rounded-2xl border border-white/5 text-center mb-6">
                    <div><div class="text-[10px] text-slate-500 font-bold uppercase mb-2">pH</div><div class="text-3xl font-black font-mono text-emerald-400">{{ sim_data.ph }}</div></div>
                    <div class="border-l border-white/10"><div class="text-[10px] text-slate-500 font-bold uppercase mb-2">PaCO2</div><div class="text-3xl font-black font-mono text-amber-400">{{ sim_data.paco2 }}</div></div>
                    <div class="border-l border-white/10"><div class="text-[10px] text-slate-500 font-bold uppercase mb-2">HCO3</div><div class="text-3xl font-black font-mono text-purple-400">{{ sim_data.hco3 }}</div></div>
                </div>
                <div id="abg-status" data-raw="{{ sim_data.acid_base_status }}" class="text-[11px] font-bold text-white uppercase tracking-wider bg-purple-950/50 block text-center py-3 px-2 rounded-lg border border-purple-800 leading-relaxed">{{ sim_data.acid_base_status }}</div>
            </div>
        </div>

        <div class="glass-panel p-6 rounded-2xl mb-6">
            <h3 class="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-4 border-b border-white/10 pb-2" data-i18n="mech_exp">Mechanics Explained</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5"><span class="text-[10px] text-cyan-400 font-bold uppercase block mb-2" data-i18n="comp">Compliance</span><div class="text-3xl font-black text-white font-mono">{{ sim_data.compliance }}</div></div>
                <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5"><span class="text-[10px] text-rose-400 font-bold uppercase block mb-2" data-i18n="res">Resistance</span><div class="text-3xl font-black text-white font-mono">{{ sim_data.resistance }}</div></div>
                <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5"><span class="text-[10px] text-amber-400 font-bold uppercase block mb-2" data-i18n="dead">Dead Space</span><div class="text-3xl font-black text-white font-mono">{{ sim_data.vd_vt }}%</div></div>
                <div class="bg-black/40 p-5 rounded-xl text-center border border-white/5"><span class="text-[10px] text-emerald-400 font-bold uppercase block mb-2" data-i18n="shunt">Shunt</span><div class="text-3xl font-black text-white font-mono">{{ sim_data.shunt }}%</div></div>
            </div>
        </div>

        <div class="glass-panel p-6 rounded-2xl h-[400px] flex flex-col relative">
            <div class="flex justify-between items-center mb-4 border-b border-white/10 pb-2">
                <h3 class="text-[10px] font-bold uppercase tracking-widest text-slate-400" data-i18n="graphs">Waveform Analytics</h3>
                
                <div class="text-[10px] text-slate-300 flex gap-4 font-mono bg-black/50 px-3 py-1.5 rounded-lg border border-white/5">
                    <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded bg-[#22d3ee]"></span><span class="font-bold">Paw</span></div>
                    <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded bg-[#10b981]"></span><span class="font-bold">Vol</span></div>
                    <div class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded bg-[#f43f5e]"></span><span class="font-bold">Flow</span></div>
                </div>
            </div>
            <div class="flex-1 w-full relative"><canvas id="matrixChart"></canvas></div>
        </div>

        <script>
            const waveData = {{ sim_data.waveform_data | safe }};
            Chart.defaults.color = '#64748b';
            Chart.defaults.font.family = "'JetBrains Mono', monospace";
            
            new Chart(document.getElementById('matrixChart'), {
                type: 'line',
                data: {
                    labels: waveData.t,
                    datasets: [
                        { label: 'Pressure (cmH2O)', data: waveData.p, borderColor: '#22d3ee', borderWidth: 2, pointRadius: 0, fill: false },
                        { label: 'Volume (mL)', data: waveData.v, borderColor: '#10b981', borderWidth: 2, pointRadius: 0, fill: false },
                        { label: 'Flow (L/m)', data: waveData.f, borderColor: '#f43f5e', borderWidth: 2, pointRadius: 0, fill: false }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { 
                        x: { grid: { color: 'rgba(255,255,255,0.05)' } }, 
                        y: { grid: { color: 'rgba(255,255,255,0.05)' } } 
                    }
                }
            });
        </script>
        {% endif %}
    </main>

    <div id="notes-modal" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
        <div class="glass-panel p-8 rounded-2xl w-[500px] border border-emerald-500/30 shadow-2xl relative flex flex-col">
            <button onclick="document.getElementById('notes-modal').classList.add('hidden')" class="absolute top-4 right-4 text-slate-400 hover:text-white transition text-lg">✕</button>
            <h2 class="text-xl font-black text-white uppercase tracking-widest mb-2 text-emerald-400">Clinical Notes Analyzer</h2>
            <p class="text-[10px] text-slate-400 font-mono mb-4 leading-relaxed">Paste unstructured patient record data below. The AI will scan the text, extract physiological markers, and identify the most probable lung pathology.</p>
            <textarea id="patient_record_input" class="w-full glass-input px-4 py-3 rounded-lg text-xs h-32 mb-4 font-mono text-slate-300" placeholder="E.g., A 65-year-old male presents with worsening shortness of breath, chronic productive cough, and 40 pack-year smoking history..."></textarea>
            <button onclick="processClinicalNotes()" class="w-full py-3 rounded-lg bg-emerald-600 font-bold text-white uppercase text-xs tracking-wider transition hover:bg-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.3)]">Scan & Analyze Record</button>
        </div>
    </div>
</body>
"""

# ==========================================
# 4. FLASK SERVER ROUTES
# ==========================================
@app.route('/')
def home():
    if 'user' in session: 
        return redirect(url_for('dashboard'))
    return render_template_string(HOME_HTML)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    
    if user and check_password_hash(user[2], password):
        session['user'] = user[1]
        return redirect(url_for('dashboard'))
    
    flash('Invalid credentials')
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('last_sim_data', None)
    return redirect(url_for('home'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user' not in session: return redirect(url_for('home'))
    if request.method == 'POST':
        np = request.form.get('new_password')
        curr = session['user']
        if np:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("UPDATE users SET password=? WHERE username=?", (generate_password_hash(np), curr))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))
    return render_template_string(SETTINGS_HTML)

# ==========================================
# ASYNCHRONOUS API ROUTES FOR AI INTEGRATION
# ==========================================
@app.route('/api/analyze-report', methods=['POST'])
def api_analyze_report():
    data = request.get_json() or {}
    report_text = data.get("report_text", "")
    if not report_text.strip():
        return jsonify({"error": "Report text field cannot be blank."}), 400
    return jsonify(NLPAnalyzer.analyze_report(report_text))

@app.route('/api/lyra-chat', methods=['POST'])
def api_lyra_chat():
    data = request.get_json() or {}
    user_message = data.get("message", "")
    chat_history = data.get("history", [])
    active_context = session.get("last_sim_data", {})
    reply = LyraAssistant.chat_response(user_message, active_context, chat_history)
    return jsonify({"reply": reply})

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session: return redirect(url_for('home'))
    sim_data = None
    inputs = {}
    preset = request.form.get('preset_id', '')
    custom_desc = request.form.get('custom_ai_desc', '')
    custom_cond = request.form.get('custom_ai_cond', '')
    custom_plan = request.form.get('custom_ai_plan', '')
    
    if request.method == 'POST':
        inputs = {k: request.form.get(k) for k in request.form if k not in ['preset_id', 'custom_ai_desc', 'custom_ai_cond', 'custom_ai_plan']}
        clean_inputs = {k: RespiratoryEngine.safe_float(v, 0) for k, v in inputs.items()}
        try:
            sim_data = RespiratoryEngine.calculate_simulation(clean_inputs, preset, custom_desc, custom_cond, custom_plan)
            
            # SAVES COMPUTE STATE SO LYRA CAN RETRIEVE THE CLINICAL CONTEXT REAL-TIME
            session['last_sim_data'] = sim_data
            
        except Exception:
            flash(f"Error calculating metrics: {traceback.format_exc()}")
            
        inputs['custom_ai_desc'] = custom_desc
        inputs['custom_ai_cond'] = custom_cond
        inputs['custom_ai_plan'] = custom_plan

    return render_template_string(INDEX_HTML, sim_data=sim_data, inputs=inputs, preset=preset)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
