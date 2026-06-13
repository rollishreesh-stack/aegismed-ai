from flask import Flask, request, redirect, url_for, session, flash, render_template_string
import google.generativeai as genai
import os
import json

app = Flask(__name__)
app.secret_key = "cerebrosync_quantum_synapse_core_2026"

# Advanced Neuro-Lab Credentials for Olympiad Showcases
NEURO_USERS = {"neuro_director": "synapse2026"}

# --- CYBER-NEUROLOGY UI TEMPLATES ---
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>CerebroSync AI | Cortical Interface Node</title>
</head>
<body class="bg-slate-950 flex items-center justify-center h-screen text-slate-100 antialiased">
    <div class="bg-slate-900 border border-violet-900/60 p-8 rounded-2xl shadow-2xl w-full max-w-md relative overflow-hidden">
        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-violet-500 via-fuchsia-500 to-cyan-500"></div>
        <div class="text-center mb-6">
            <span class="bg-violet-500/10 text-violet-400 text-[10px] font-mono tracking-widest uppercase px-3 py-1 rounded-full border border-violet-500/20">
                SDG 3 // Assistive Neuro-Prosthetics
            </span>
            <h1 class="text-3xl font-black text-white tracking-tight mt-3">CerebroSync <span class="text-fuchsia-400">AI</span></h1>
            <p class="text-slate-400 text-xs mt-1">Cortical Spike Decoding & Motor Mesh Translation</p>
        </div>
        
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-xl mb-4 text-xs font-mono text-center">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}
        
        <form method="POST" action="/login" class="space-y-4">
            <div>
                <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1">Neuro-Engineer ID</label>
                <input type="text" name="username" required class="w-full p-3 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-fuchsia-500 transition">
            </div>
            <div>
                <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1">Neural Handshake Token</label>
                <input type="password" name="password" required class="w-full p-3 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-fuchsia-500 transition">
            </div>
            <button type="submit" class="w-full bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white font-bold py-3 rounded-xl text-xs uppercase tracking-widest transition shadow-lg shadow-fuchsia-600/10">Sync Neural Uplink</button>
        </form>
        <p class="mt-4 text-[10px] text-center text-slate-500 font-mono">Judges Access -> ID: neuro_director | Token: synapse2026</p>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>CerebroSync Core Dashboard</title>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen antialiased">
    <nav class="bg-slate-900 border-b border-violet-950 px-6 py-4 flex justify-between items-center sticky top-0 z-50">
        <div class="flex items-center space-x-3">
            <span class="w-2.5 h-2.5 bg-fuchsia-400 rounded-full animate-ping"></span>
            <span class="font-black text-lg tracking-wider text-white">CEREBRO<span class="text-fuchsia-400">SYNC</span> AI</span>
        </div>
        <div class="flex items-center space-x-4">
            <div class="text-right hidden sm:block">
                <p class="text-[10px] text-slate-500 font-mono uppercase tracking-widest">BCI Telemetry Node</p>
                <p class="text-xs font-bold text-slate-300 font-mono">{{ session['user'] }}</p>
            </div>
            <a href="/logout" class="bg-slate-800 hover:bg-red-950 border border-slate-700 hover:border-red-900 px-4 py-2 rounded-xl text-xs font-mono uppercase tracking-wider transition">Break Synapse Connection</a>
        </div>
    </nav>

    <main class="max-w-7xl mx-auto p-6 lg:p-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div class="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl h-fit">
            <h2 class="text-base font-bold text-white mb-1">Cortical Array Stream</h2>
            <p class="text-xs text-slate-400 mb-6">Input microvolt array telemetry, spatial matrix metrics, channel frequency maps, or raw sensory-motor tracking data.</p>
            
            <form method="POST" action="/dashboard" class="space-y-4">
                <div>
                    <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1.5">Subject Matrix ID / Implanted Array Hash</label>
                    <input type="text" name="patient_id" placeholder="e.g., Motor-Cortex Array-4 (Patient B-77)" required class="w-full p-3 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-violet-500 transition">
                </div>
                <div>
                    <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1.5">Raw Brainwave Stream & Frequency Logs</label>
                    <textarea name="medical_details" rows="7" placeholder="Paste brainwave stream data here (e.g., High-gamma oscillations detected at 85 Hz across channels 12-18; spike rate bursts up to 140 Hz in primary motor cortex; patient attempting verbalization framework; parietal feedback lag at 12ms)..." required class="w-full p-3 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-violet-500 transition"></textarea>
                </div>
                <button type="submit" class="w-full bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white font-bold py-3 rounded-xl text-xs uppercase tracking-widest shadow-lg shadow-fuchsia-600/10 transition">Run Synaptic Decoding</button>
            </form>
        </div>

        <div class="lg:col-span-2 space-y-6">
            {% if not computational_data %}
            <div class="bg-slate-900/40 border border-violet-900/20 border-dashed rounded-2xl p-16 text-center flex flex-col items-center justify-center min-h-[400px]">
                <div class="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center text-xl text-fuchsia-400 shadow-inner mb-4">🧠</div>
                <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-widest font-mono">Uplink Stream Dormant</h3>
                <p class="text-xs text-slate-500 max-w-xs mt-1 mx-auto">Awaiting real-time cortical data pipelines to reconstruct inner monologues and plot multi-axis robotic limb vectors.</p>
            </div>
            {% else %}
            
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                    <p class="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">Signal Fidelity Alignment ($E_{neuro}$)</p>
                    <p class="text-3xl font-black font-mono text-cyan-400">{{ computational_data.signal_fidelity_index }}%</p>
                    <div class="w-full bg-slate-800 h-1 rounded-full mt-3 overflow-hidden">
                        <div class="bg-cyan-400 h-full" style="width: {{ computational_data.signal_fidelity_index }}%"></div>
                    </div>
                </div>
                <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                    <p class="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">Decoding Confidence Probability</p>
                    <p class="text-3xl font-black font-mono text-fuchsia-400">{{ computational_data.decoding_confidence_percentage }}%</p>
                    <div class="w-full bg-slate-800 h-1 rounded-full mt-3 overflow-hidden">
                        <div class="bg-fuchsia-400 h-full" style="width: {{ computational_data.decoding_confidence_percentage }}%"></div>
                    </div>
                </div>
            </div>

            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 relative overflow-hidden">
                <h3 class="text-xs font-mono uppercase tracking-wider text-fuchsia-400 mb-4 pb-2 border-b border-slate-800">Synthesized Neuro-Prosthetic Interface Vectors</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="bg-slate-950 border border-slate-800 p-4 rounded-xl">
                        <span class="text-[9px] font-mono font-bold uppercase bg-fuchsia-950 text-fuchsia-400 border border-fuchsia-900 px-2 py-0.5 rounded tracking-wide">Decoded Inner Speech Monologue</span>
                        <p class="text-base font-bold text-white mt-3 italic">"{{ computational_data.decoded_linguistic_intent }}"</p>
                    </div>
                    <div class="bg-slate-950 border border-slate-800 p-4 rounded-xl">
                        <span class="text-[9px] font-mono font-bold uppercase bg-cyan-950 text-cyan-400 border border-cyan-900 px-2 py-0.5 rounded tracking-wide">Motor Cortex Mapping (3D Matrix Target)</span>
                        <p class="text-sm font-mono font-black text-slate-200 mt-2">Vector: <span class="text-cyan-400">{{ computational_data.motor_cortex_mapping.spatial_coordinates }}</span></p>
                        <p class="text-xs text-slate-400 mt-2 leading-relaxed">{{ computational_data.motor_cortex_mapping.prosthetic_actuation_path }}</p>
                    </div>
                </div>
            </div>

            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                <h3 class="text-xs font-mono uppercase tracking-wider text-slate-400 mb-4 pb-2 border-b border-slate-800">Neuroplastic Rehabilitation & Optimization Trackers</h3>
                <div class="space-y-3">
                    {% for protocol in computational_data.neuroplastic_rehab_protocol %}
                    <div class="bg-slate-950 border border-slate-800/60 p-4 rounded-xl flex items-start space-x-3">
                        <span class="text-xs text-fuchsia-400 font-mono font-bold bg-slate-900 border border-slate-800 w-6 h-6 flex items-center justify-center rounded-lg flex-shrink-0">⚙</span>
                        <div>
                            <h4 class="text-xs font-bold uppercase tracking-wide text-white">{{ protocol.therapeutic_target }}</h4>
                            <p class="text-xs text-slate-400 mt-0.5">{{ protocol.clinical_action }}</p>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
        </div>
    </main>
</body>
</html>
"""

# --- SYSTEMS RUNTIME OPERATIONS CORE ---

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username in NEURO_USERS and NEURO_USERS[username] == password:
        session['user'] = username
        return redirect(url_for('dashboard'))
    else:
        flash("SYNAPSE LINK MISALIGNMENT: HANDSHAKE REFUSED")
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    computational_data = None
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        metrics = request.form['medical_details']
        
        try:
            # Safely grab system keys inside processing thread to prevent startup blockages
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("System lacks an active GEMINI_API_KEY environmental token.")
                
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
            
            prompt = f"""
            Analyze the following real-time neural interface tracking signals to decode intended actions and linguistic structures (SDG 3 clinical compliance).
            Implant Identification Hash: {patient_id}
            Cortical Frequency Telemetry: {metrics}

            You must respond with exactly this JSON formatting framework:
            {{
                "decoding_confidence_percentage": (integer between 0 and 100 representing signal decoding calculation certitude),
                "signal_fidelity_index": (integer between 0 and 100 representing signal-to-noise ratio performance),
                "decoded_linguistic_intent": "A striking, contextually sound 1-sentence thought or vocalization statement intended by the user, extracted directly from the neural patterns.",
                "motor_cortex_mapping": {{
                    "spatial_coordinates": "3D matrix values like X: +22.4mm, Y: -11.0mm, Z: +8.4mm",
                    "prosthetic_actuation_path": "A complex clinical breakdown of robotic limb joints, prosthetic grip controls, or cursor mechanics triggered by the corresponding primary motor cortex spikes."
                }},
                "neuroplastic_rehab_protocol": [
                    {{
                        "therapeutic_target": "Specific brain region or biofeedback metric loop",
                        "clinical_action": "Targeted optimization technique or real-time simulation adjustment step to reduce cognitive friction or sync delay."
                    }},
                    {{
                        "therapeutic_target": "Somatosensory feedback target path",
                        "clinical_action": "Method for configuring simulated tactile or visual confirmation frequencies back to the user."
                    }}
                ]
            }}
            """
            
            response = model.generate_content(prompt)
            computational_data = json.loads(response.text)
            
        except Exception as e:
            computational_data = {
                "decoding_confidence_percentage": 0,
                "signal_fidelity_index": 0,
                "decoded_linguistic_intent": f"Uplink Diagnostic Failure: {str(e)}",
                "motor_cortex_mapping": {
                    "spatial_coordinates": "X: 0, Y: 0, Z: 0",
                    "prosthetic_actuation_path": "Check Render variable panels."
                },
                "neuroplastic_rehab_protocol": []
            }
            
    return render_template_string(DASHBOARD_HTML, computational_data=computational_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
