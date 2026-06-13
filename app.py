from flask import Flask, request, redirect, url_for, session, flash, render_template_string
import google.generativeai as genai
import os
import json

app = Flask(__name__)
app.secret_key = "aegismed_secure_core_2026"

# Medical Director Login Credentials for Judges
MED_USERS = {"chief_medical_officer": "geneva16"}

# --- CLINICAL INTELLIGENCE DASHBOARD UI ---
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>AegisMed AI | Secure Intake Portal</title>
</head>
<body class="bg-slate-950 flex items-center justify-center h-screen text-slate-100 antialiased">
    <div class="bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-2xl w-full max-w-md">
        <div class="text-center mb-6">
            <span class="bg-emerald-500/10 text-emerald-400 text-[10px] font-mono tracking-widest uppercase px-3 py-1 rounded-full border border-emerald-500/20">
                SDG 3 // SDG 16 Core
            </span>
            <h1 class="text-3xl font-black text-white tracking-tight mt-3">AegisMed <span class="text-emerald-400">AI</span></h1>
            <p class="text-slate-500 text-xs mt-1">Medical Forensic & Neutrality Verification Pipeline</p>
        </div>
        
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-xl mb-4 text-xs font-mono text-center">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}
        
        <form method="POST" action="/login" class="space-y-4">
            <div>
                <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1">Credential ID</label>
                <input type="text" name="username" required class="w-full p-3 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500 transition">
            </div>
            <div>
                <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1">Security Token</label>
                <input type="password" name="password" required class="w-full p-3 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500 transition">
            </div>
            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-xl text-xs uppercase tracking-widest transition shadow-lg shadow-emerald-600/10">Authorize Terminal</button>
        </form>
        <p class="mt-4 text-[10px] text-center text-slate-600 font-mono">Demo Access -> ID: chief_medical_officer | Token: geneva16</p>
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
    <title>AegisMed Analytics Dashboard</title>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen antialiased">
    <nav class="bg-slate-900 border-b border-slate-800 px-6 py-4 flex justify-between items-center sticky top-0 z-50">
        <div class="flex items-center space-x-3">
            <span class="w-2.5 h-2.5 bg-emerald-400 rounded-full animate-ping"></span>
            <span class="font-black text-lg tracking-wider text-white">AEGIS<span class="text-emerald-400">MED</span> AI</span>
        </div>
        <div class="flex items-center space-x-4">
            <div class="text-right hidden sm:block">
                <p class="text-[10px] text-slate-500 font-mono uppercase tracking-widest">Medical Intelligence Node</p>
                <p class="text-xs font-bold text-slate-300 font-mono">{{ session['user'] }}</p>
            </div>
            <a href="/logout" class="bg-slate-800 hover:bg-red-950 border border-slate-700 hover:border-red-900 px-4 py-2 rounded-xl text-xs font-mono uppercase tracking-wider transition">Disconnect</a>
        </div>
    </nav>

    <main class="max-w-7xl mx-auto p-6 lg:p-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div class="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl h-fit">
            <h2 class="text-base font-bold text-white mb-1">Clinical Intake Telemetry</h2>
            <p class="text-xs text-slate-400 mb-6">Input battlefield hospital logs, forensic intakes, or humanitarian aid denial logs.</p>
            
            <form method="POST" action="/dashboard" class="space-y-4">
                <div>
                    <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1.5">Facility / Coordinate Sector</label>
                    <input type="text" name="location" placeholder="e.g., Zone 4 Field Trauma Hospital" required class="w-full p-3 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-emerald-500 transition">
                </div>
                <div>
                    <label class="block text-slate-400 text-xs font-mono uppercase tracking-wider mb-1.5">Raw Forensic Data / Manifest Text</label>
                    <textarea name="report_details" rows="7" placeholder="Paste data here..." required class="w-full p-3 rounded-xl bg-slate-800 border border-slate-700 text-sm text-white focus:outline-none focus:border-emerald-500 transition"></textarea>
                </div>
                <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-xl text-xs uppercase tracking-widest shadow-lg shadow-emerald-600/10 transition">Run Forensic Scan</button>
            </form>
        </div>

        <div class="lg:col-span-2 space-y-6">
            {% if not diagnostic_data %}
            <div class="bg-slate-900/40 border border-slate-800/80 border-dashed rounded-2xl p-16 text-center flex flex-col items-center justify-center min-h-[400px]">
                <div class="w-10 h-10 rounded-full border border-slate-700 flex items-center justify-center text-slate-500 text-xs font-mono mb-3">+</div>
                <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-widest font-mono">System Standby</h3>
                <p class="text-xs text-slate-500 max-w-xs mt-1 mx-auto">Ingest medical field metrics to map forensic compliance indicators and verify neutrality metrics.</p>
            </div>
            {% else %}
            
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                    <p class="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">Medical Neutrality Threat Matrix</p>
                    <p class="text-3xl font-black font-mono text-red-400">{{ diagnostic_data.neutrality_threat_percentage }}%</p>
                    <div class="w-full bg-slate-800 h-1 rounded-full mt-3 overflow-hidden">
                        <div class="bg-red-400 h-full" style="width: {{ diagnostic_data.neutrality_threat_percentage }}%"></div>
                    </div>
                </div>
                <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                    <p class="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">Humanitarian Legal Integrity</p>
                    <p class="text-3xl font-black font-mono text-emerald-400">{{ diagnostic_data.humanitarian_compliance_index }}%</p>
                    <div class="w-full bg-slate-800 h-1 rounded-full mt-3 overflow-hidden">
                        <div class="bg-emerald-400 h-full" style="width: {{ diagnostic_data.humanitarian_compliance_index }}%"></div>
                    </div>
                </div>
            </div>

            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                <h3 class="text-xs font-mono uppercase tracking-wider text-slate-400 mb-4 pb-2 border-b border-slate-800">Automated Legal-Forensic Pipeline Vectors</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="bg-slate-950 border border-slate-800 p-4 rounded-xl">
                        <span class="text-[9px] font-mono font-bold uppercase bg-red-950 text-red-400 border border-red-900 px-2 py-0.5 rounded tracking-wide">Forensic Medical Pathology</span>
                        <p class="text-xs text-slate-300 mt-3 leading-relaxed">"{{ diagnostic_data.forensic_findings }}"</p>
                    </div>
                    <div class="bg-slate-950 border border-slate-800 p-4 rounded-xl">
                        <span class="text-[9px] font-mono font-bold uppercase bg-emerald-950 text-emerald-400 border border-emerald-900 px-2 py-0.5 rounded tracking-wide">Geneva Accord Compliance Guard</span>
                        <p class="text-xs text-slate-300 mt-3 leading-relaxed">"{{ diagnostic_data.legal_infractions }}"</p>
                    </div>
                </div>
            </div>

            <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                <h3 class="text-xs font-mono uppercase tracking-wider text-slate-400 mb-4 pb-2 border-b border-slate-800">SDG 16 Accountability Measures</h3>
                <div class="space-y-3">
                    {% for action in diagnostic_data.accountability_playbook %}
                    <div class="bg-slate-950 border border-slate-800/60 p-4 rounded-xl flex items-start space-x-3">
                        <span class="text-xs text-emerald-400 font-mono font-bold bg-slate-900 border border-slate-800 w-6 h-6 flex items-center justify-center rounded-lg flex-shrink-0">✓</span>
                        <div>
                            <h4 class="text-xs font-bold uppercase tracking-wide text-white">{{ action.target_mechanism }}</h4>
                            <p class="text-xs text-slate-400 mt-0.5">{{ action.operational_protocol }}</p>
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

# --- SYSTEM BACKEND ENGINEERING ---

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_HTML)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username in MED_USERS and MED_USERS[username] == password:
        session['user'] = username
        return redirect(url_for('dashboard'))
    else:
        flash("ACCESS CODE DENIED: AUTHENTICATION FAILURE")
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    diagnostic_data = None
    if request.method == 'POST':
        location = request.form['location']
        report = request.form['report_details']
        
        try:
            # Configure API key safely right when the form runs
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("Missing GEMINI_API_KEY environment variable on Render.")
                
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
            
            prompt = f"""
            Analyze the following humanitarian medical report for structural human rights violations under Geneva Conventions and SDG 16/SDG 3 guidelines.
            Sector Location: {location}
            Report Payload: {report}

            You must respond with exactly this JSON formatting structure:
            {{
                "neutrality_threat_percentage": (integer between 0 and 100),
                "humanitarian_compliance_index": (integer between 0 and 100),
                "forensic_findings": "Detailed multi-sentence analysis explaining physical medical or structural system patterns showing human rights violations",
                "legal_infractions": "Detailed analysis showing exactly which international justice treaties or health laws were breached",
                "accountability_playbook": [
                    {{
                        "target_mechanism": "String target body name",
                        "operational_protocol": "Concrete step required to preserve forensic evidence or submit reports safely"
                    }}
                ]
            }}
            """
            
            response = model.generate_content(prompt)
            diagnostic_data = json.loads(response.text)
            
        except Exception as e:
            diagnostic_data = {
                "neutrality_threat_percentage": 0,
                "humanitarian_compliance_index": 0,
                "forensic_findings": f"Configuration Note: {str(e)}",
                "legal_infractions": "Please check your Render Environment settings.",
                "accountability_playbook": []
            }
            
    return render_template_string(DASHBOARD_HTML, diagnostic_data=diagnostic_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
