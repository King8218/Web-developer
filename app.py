from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
import requests
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ---------- CONFIG (अपनी API Keys यहाँ डालें - Optional) ----------
VERIPHONE_API_KEY = ""  # https://veriphone.com से फ्री लें
NUMVERIFY_API_KEY = ""  # https://numverify.com से फ्री लें

# ---------- HTML TEMPLATE ----------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌊 अंकित ओसियन - Phone Lookup</title>
    <meta name="description" content="अंकित ओसियन - Phone number lookup service. Get operator, circle, location & validity">
    <style>
        /* ===== RESET ===== */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #e8f0fe 0%, #d4e0f7 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        /* ===== HEADER ===== */
        .header {
            background: linear-gradient(135deg, #0a1628 0%, #1a3a6b 50%, #0d47a1 100%);
            color: white;
            padding: 30px 40px;
            border-radius: 25px;
            width: 100%;
            max-width: 850px;
            text-align: center;
            box-shadow: 0 15px 40px rgba(13,71,161,0.4);
            margin-bottom: 25px;
            position: relative;
            overflow: hidden;
        }
        .header::before {
            content: '🌊';
            position: absolute;
            font-size: 100px;
            opacity: 0.08;
            right: -20px;
            top: -30px;
            transform: rotate(15deg);
        }
        .header .logo {
            font-size: 42px;
            font-weight: 800;
            letter-spacing: 2px;
        }
        .header .logo span {
            color: #64b5f6;
        }
        .header .logo .wave {
            display: inline-block;
            animation: wave 2s ease-in-out infinite;
        }
        @keyframes wave {
            0%, 100% { transform: rotate(0deg); }
            50% { transform: rotate(10deg); }
        }
        .header .subtitle {
            font-size: 16px;
            opacity: 0.9;
            margin-top: 8px;
            font-weight: 300;
            letter-spacing: 1px;
        }
        .header .tagline {
            display: inline-block;
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(10px);
            padding: 6px 20px;
            border-radius: 30px;
            font-size: 12px;
            margin-top: 12px;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .privacy-badge {
            display: inline-block;
            background: #e8f5e9;
            color: #1b5e20;
            padding: 6px 18px;
            border-radius: 30px;
            font-size: 12px;
            font-weight: 600;
            margin-top: 10px;
        }
        /* ===== SEARCH BOX ===== */
        .search-box {
            background: white;
            padding: 30px;
            border-radius: 20px;
            width: 100%;
            max-width: 850px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.08);
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.3);
        }
        .input-group {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        .input-group input {
            flex: 1;
            padding: 16px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 14px;
            font-size: 16px;
            min-width: 200px;
            transition: 0.3s;
            background: #fafafa;
        }
        .input-group input:focus {
            outline: none;
            border-color: #0d47a1;
            box-shadow: 0 0 0 4px rgba(13,71,161,0.1);
            background: white;
        }
        .input-group button {
            padding: 16px 35px;
            background: linear-gradient(135deg, #0a1628 0%, #0d47a1 100%);
            color: white;
            border: none;
            border-radius: 14px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: 0.3s;
            white-space: nowrap;
        }
        .input-group button:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 30px rgba(13,71,161,0.35);
        }
        .input-group button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .input-hint {
            margin-top: 12px;
            font-size: 12px;
            color: #999;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .input-hint span {
            background: #f5f5f5;
            padding: 4px 12px;
            border-radius: 20px;
            color: #666;
        }
        /* ===== LOADING ===== */
        #loading {
            text-align: center;
            padding: 30px;
            display: none;
        }
        .spinner {
            display: inline-block;
            width: 45px;
            height: 45px;
            border: 4px solid #e0e0e0;
            border-top: 4px solid #0d47a1;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        #loading p {
            margin-top: 12px;
            color: #555;
            font-weight: 500;
        }
        /* ===== RESULT ===== */
        #result {
            display: none;
            width: 100%;
            max-width: 850px;
        }
        .card {
            background: white;
            border-radius: 16px;
            padding: 22px 25px;
            margin-bottom: 16px;
            box-shadow: 0 3px 15px rgba(0,0,0,0.06);
            border-left: 5px solid #0d47a1;
            animation: fadeUp 0.4s ease;
            transition: 0.3s;
        }
        .card:hover {
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        @keyframes fadeUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .card h3 {
            font-size: 16px;
            color: #0a1628;
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .card h3 .badge-count {
            background: #0d47a1;
            color: white;
            font-size: 11px;
            padding: 2px 12px;
            border-radius: 20px;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 9px 0;
            border-bottom: 1px solid #f0f2f5;
            flex-wrap: wrap;
            gap: 5px;
        }
        .info-row:last-child { border-bottom: none; }
        .label {
            color: #888;
            font-weight: 500;
            font-size: 14px;
        }
        .value {
            color: #1a1a2e;
            font-weight: 600;
            font-size: 14px;
            text-align: right;
            word-break: break-word;
            max-width: 70%;
        }
        /* ===== BADGES ===== */
        .badge {
            display: inline-block;
            padding: 3px 14px;
            border-radius: 30px;
            font-size: 12px;
            font-weight: 700;
        }
        .badge-success { background: #e8f5e9; color: #1b5e20; }
        .badge-danger { background: #ffebee; color: #b71c1c; }
        .badge-warning { background: #fff8e1; color: #e65100; }
        .badge-info { background: #e3f2fd; color: #0d47a1; }
        .badge-purple { background: #f3e5f5; color: #4a148c; }
        /* ===== NAME HIGHLIGHT ===== */
        .name-highlight {
            background: linear-gradient(135deg, #e8eaf6, #c5cae9);
            padding: 15px;
            border-radius: 12px;
            text-align: center;
            font-size: 26px;
            font-weight: 700;
            color: #0a1628;
        }
        .name-source {
            text-align: center;
            font-size: 12px;
            color: #888;
            margin-top: 6px;
        }
        /* ===== HISTORY ===== */
        #history-section {
            background: white;
            border-radius: 16px;
            padding: 20px 25px;
            box-shadow: 0 3px 15px rgba(0,0,0,0.06);
            margin-top: 5px;
        }
        #history-section h4 {
            color: #555;
            font-size: 14px;
            margin-bottom: 12px;
        }
        .history-item {
            display: inline-block;
            background: #f0f2f5;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            margin: 4px 6px 4px 0;
            cursor: pointer;
            transition: 0.2s;
            color: #333;
        }
        .history-item:hover {
            background: #0d47a1;
            color: white;
            transform: scale(1.05);
        }
        .clear-btn {
            background: none;
            border: none;
            color: #c62828;
            font-size: 12px;
            cursor: pointer;
            text-decoration: underline;
            margin-top: 10px;
        }
        .clear-btn:hover { color: #b71c1c; }
        /* ===== FOOTER ===== */
        .footer {
            margin-top: 30px;
            text-align: center;
            color: #999;
            font-size: 12px;
            padding: 15px;
            width: 100%;
            max-width: 850px;
        }
        .footer a {
            color: #0d47a1;
            text-decoration: none;
            font-weight: 500;
        }
        .footer a:hover { text-decoration: underline; }
        .footer .heart {
            color: #e53935;
        }
        /* ===== MODAL ===== */
        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(5px);
            z-index: 1000;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .modal.show { display: flex; }
        .modal-content {
            background: white;
            border-radius: 20px;
            padding: 30px;
            max-width: 600px;
            width: 100%;
            max-height: 80vh;
            overflow-y: auto;
            position: relative;
            animation: fadeUp 0.3s ease;
        }
        .modal-content h2 {
            color: #0a1628;
            margin-bottom: 15px;
            font-size: 24px;
        }
        .modal-content h2 .emoji { font-size: 28px; }
        .modal-content p, .modal-content li {
            color: #444;
            font-size: 14px;
            line-height: 1.8;
        }
        .modal-content ul { padding-left: 20px; }
        .modal-content li { margin-bottom: 6px; }
        .modal-close {
            background: linear-gradient(135deg, #0a1628, #0d47a1);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 20px;
            width: 100%;
            transition: 0.3s;
        }
        .modal-close:hover {
            transform: scale(1.02);
            box-shadow: 0 8px 20px rgba(13,71,161,0.3);
        }
        /* ===== RESPONSIVE ===== */
        @media (max-width: 600px) {
            .header { padding: 20px; }
            .header .logo { font-size: 28px; }
            .search-box { padding: 18px; }
            .input-group { flex-direction: column; }
            .input-group button { width: 100%; justify-content: center; }
            .card { padding: 16px 18px; }
            .info-row { flex-direction: column; align-items: flex-start; }
            .value { text-align: left; max-width: 100%; }
            .modal-content { padding: 20px; }
            .input-hint { flex-direction: column; gap: 5px; }
        }
        /* ===== SPAM WARNING ===== */
        .spam-warning {
            background: #ffebee;
            border: 2px solid #ef5350;
            padding: 12px 18px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .spam-warning .icon { font-size: 28px; }
        .spam-warning .text {
            color: #b71c1c;
            font-weight: 600;
            font-size: 14px;
        }
        /* ===== OCEAN THEME ELEMENTS ===== */
        .ocean-dots {
            display: flex;
            gap: 6px;
            justify-content: center;
            margin-top: 10px;
        }
        .ocean-dots span {
            width: 6px;
            height: 6px;
            background: rgba(255,255,255,0.3);
            border-radius: 50%;
            animation: pulse 1.5s ease-in-out infinite;
        }
        .ocean-dots span:nth-child(2) { animation-delay: 0.3s; }
        .ocean-dots span:nth-child(3) { animation-delay: 0.6s; }
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.3; }
            50% { transform: scale(1.5); opacity: 1; }
        }
    </style>
</head>
<body>

    <!-- ===== HEADER ===== -->
    <div class="header">
        <div class="logo">
            🌊 अंकित <span>ओसियन</span>
        </div>
        <div class="subtitle">🔍 Phone Lookup Service — Osiyant जैसा, लेकिन Safe</div>
        <div class="tagline">⚡ भारत का भरोसेमंद नंबर लुकअप</div>
        <div class="privacy-badge">🔒 सिर्फ सार्वजनिक डेटा • कोई निजी जानकारी नहीं</div>
        <div class="ocean-dots">
            <span></span><span></span><span></span>
        </div>
    </div>

    <!-- ===== SEARCH BOX ===== -->
    <div class="search-box">
        <div class="input-group">
            <input type="text" id="phoneInput" placeholder="+91 98765 43210" value="+919876543210">
            <button id="searchBtn">🔍 खोजें</button>
        </div>
        <div class="input-hint">
            <span>📱 उदाहरण: +91 98765 43210</span>
            <span>🇮🇳 सिर्फ भारतीय नंबर</span>
            <span>🔒 100% प्राइवेट</span>
        </div>
    </div>

    <!-- ===== LOADING ===== -->
    <div id="loading">
        <div class="spinner"></div>
        <p>⏳ डेटा लाया जा रहा है...</p>
    </div>

    <!-- ===== RESULT ===== -->
    <div id="result">
        <!-- Name Card -->
        <div class="card" id="nameCard" style="display:none; border-left-color:#ff6f00;">
            <h3>👤 नाम की जानकारी</h3>
            <div id="nameContent"></div>
        </div>

        <!-- Number Details -->
        <div class="card">
            <h3>📱 नंबर की डिटेल</h3>
            <div id="infoContent"></div>
        </div>

        <!-- Network & Location -->
        <div class="card" style="border-left-color:#0d47a1;">
            <h3>📍 नेटवर्क & लोकेशन</h3>
            <div id="locationContent"></div>
        </div>

        <!-- Spam Warning -->
        <div class="card" id="spamCard" style="display:none; border-left-color:#c62828;">
            <h3>⚠️ स्पैम अलर्ट</h3>
            <div id="spamContent"></div>
        </div>

        <!-- History -->
        <div id="history-section">
            <h4>🕐 हाल की खोजें</h4>
            <div id="historyList"><span style="color:#bbb; font-size:13px;">अभी कोई इतिहास नहीं</span></div>
            <button class="clear-btn" onclick="clearHistory()">🗑️ इतिहास साफ़ करें</button>
        </div>
    </div>

    <!-- ===== FOOTER ===== -->
    <div class="footer">
        🔒 <a href="#" onclick="openModal('privacy')">Privacy Policy</a>
        &nbsp;•&nbsp; 📜 <a href="#" onclick="openModal('terms')">Terms of Service</a>
        &nbsp;•&nbsp; Made with <span class="heart">❤️</span> by अंकित
        &nbsp;•&nbsp; ⚡ Hosted on Vercel
    </div>

    <!-- ===== PRIVACY MODAL ===== -->
    <div class="modal" id="privacyModal">
        <div class="modal-content">
            <h2><span class="emoji">🔒</span> Privacy Policy</h2>
            <p><strong>Last Updated:</strong> July 2025</p>
            <p>Welcome to <strong>अंकित ओसियन</strong>. Your privacy is our priority.</p>
            <ul>
                <li><strong>No Data Collection:</strong> We do NOT collect, store, or share any personal information.</li>
                <li><strong>Local Storage Only:</strong> Your search history is saved locally in your browser. We never see it.</li>
                <li><strong>No Cookies:</strong> We don't use tracking cookies.</li>
                <li><strong>Public Data Only:</strong> We only show operator, circle, line type — all publicly available.</li>
                <li><strong>No Personal Info:</strong> No names, addresses, emails, or Aadhaar are displayed.</li>
                <li><strong>HTTPS Secure:</strong> All communication is encrypted.</li>
            </ul>
            <p>📧 Questions? <strong>support@ankit-ocean.com</strong></p>
            <button class="modal-close" onclick="closeModal('privacy')">✅ I Understand</button>
        </div>
    </div>

    <!-- ===== TERMS MODAL ===== -->
    <div class="modal" id="termsModal">
        <div class="modal-content">
            <h2><span class="emoji">📜</span> Terms of Service</h2>
            <p><strong>Last Updated:</strong> July 2025</p>
            <p>By using <strong>अंकित ओसियन</strong>, you agree to:</p>
            <ul>
                <li><strong>Informational Use:</strong> This service is for reference only.</li>
                <li><strong>No Illegal Activity:</strong> No stalking, harassment, or misuse.</li>
                <li><strong>Public Data:</strong> We only display publicly available information.</li>
                <li><strong>No Warranty:</strong> Service provided "as is" — accuracy not guaranteed.</li>
                <li><strong>Fair Usage:</strong> Excessive requests may be rate-limited.</li>
                <li><strong>Indemnification:</strong> You are responsible for how you use this service.</li>
                <li><strong>Changes:</strong> Terms may be updated anytime.</li>
            </ul>
            <p>By continuing, you accept these terms.</p>
            <button class="modal-close" onclick="closeModal('terms')">✅ I Agree</button>
        </div>
    </div>

    <script>
        // ===== MODALS =====
        function openModal(type) {
            document.getElementById(type + 'Modal').classList.add('show');
        }
        function closeModal(type) {
            document.getElementById(type + 'Modal').classList.remove('show');
        }
        window.onclick = function(event) {
            if (event.target.classList.contains('modal')) {
                event.target.classList.remove('show');
            }
        }

        // ===== HISTORY =====
        function loadHistory() {
            try {
                const history = JSON.parse(localStorage.getItem('ankitOceanHistory') || '[]');
                const container = document.getElementById('historyList');
                if (history.length === 0) {
                    container.innerHTML = '<span style="color:#bbb; font-size:13px;">अभी कोई इतिहास नहीं</span>';
                    return;
                }
                container.innerHTML = history.slice(-10).reverse().map(num =>
                    `<span class="history-item" onclick="searchNumber('${num}')">📞 ${num}</span>`
                ).join('');
            } catch(e) { /* ignore */ }
        }

        function saveHistory(number) {
            try {
                let history = JSON.parse(localStorage.getItem('ankitOceanHistory') || '[]');
                history = history.filter(n => n !== number);
                history.push(number);
                if (history.length > 20) history = history.slice(-20);
                localStorage.setItem('ankitOceanHistory', JSON.stringify(history));
                loadHistory();
            } catch(e) { /* ignore */ }
        }

        function clearHistory() {
            localStorage.removeItem('ankitOceanHistory');
            loadHistory();
        }

        function searchNumber(number) {
            document.getElementById('phoneInput').value = number;
            document.getElementById('searchBtn').click();
        }

        // ===== MAIN SEARCH =====
        document.getElementById('searchBtn').addEventListener('click', async function() {
            const phone = document.getElementById('phoneInput').value.trim();
            if (!phone) {
                alert('🙏 कृपया नंबर डालें!');
                return;
            }

            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            document.getElementById('searchBtn').disabled = true;

            try {
                const response = await fetch('/lookup?number=' + encodeURIComponent(phone));
                const data = await response.json();

                if (data.error) {
                    showError(data.error);
                    return;
                }

                displayResult(data);
                saveHistory(data.international || phone);
            } catch (error) {
                showError('❌ सर्वर से कनेक्ट नहीं हो पाया');
            } finally {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('searchBtn').disabled = false;
            }
        });

        // ===== DISPLAY RESULT =====
        function displayResult(data) {
            document.getElementById('result').style.display = 'block';

            // Name Section
            if (data.name) {
                document.getElementById('nameCard').style.display = 'block';
                document.getElementById('nameContent').innerHTML = `
                    <div class="name-highlight">🧑‍💼 ${data.name}</div>
                    <div class="name-source">📡 Source: ${data.name_source || 'API'}</div>
                `;
            } else {
                document.getElementById('nameCard').style.display = 'none';
            }

            // Info Section
            let infoHTML = `
                <div class="info-row">
                    <span class="label">📇 अंतर्राष्ट्रीय</span>
                    <span class="value">${data.international || 'N/A'}</span>
                </div>
                <div class="info-row">
                    <span class="label">🇮🇳 राष्ट्रीय</span>
                    <span class="value">${data.national || 'N/A'}</span>
                </div>
                <div class="info-row">
                    <span class="label">✅ वैध</span>
                    <span class="value">
                        <span class="badge ${data.is_valid ? 'badge-success' : 'badge-danger'}">
                            ${data.is_valid ? '✔️ हाँ' : '❌ नहीं'}
                        </span>
                    </span>
                </div>
                <div class="info-row">
                    <span class="label">📊 संभावित</span>
                    <span class="value">
                        <span class="badge ${data.is_possible ? 'badge-success' : 'badge-danger'}">
                            ${data.is_possible ? '✔️ हाँ' : '❌ नहीं'}
                        </span>
                    </span>
                </div>
                <div class="info-row">
                    <span class="label">📱 लाइन टाइप</span>
                    <span class="value"><span class="badge badge-info">${data.line_type || 'Unknown'}</span></span>
                </div>
            `;
            document.getElementById('infoContent').innerHTML = infoHTML;

            // Location Section
            let locHTML = `
                <div class="info-row">
                    <span class="label">🌍 देश</span>
                    <span class="value">${data.country || 'Unknown'}</span>
                </div>
                <div class="info-row">
                    <span class="label">📍 स्थान</span>
                    <span class="value">${data.location || 'N/A'}</span>
                </div>
                <div class="info-row">
                    <span class="label">📡 ऑपरेटर</span>
                    <span class="value"><strong>${data.operator || 'Unknown'}</strong></span>
                </div>
                <div class="info-row">
                    <span class="label">🕐 टाइमज़ोन</span>
                    <span class="value">${data.timezone ? data.timezone.join(', ') : 'Unknown'}</span>
                </div>
                ${data.circle ? `<div class="info-row"><span class="label">📌 सर्कल</span><span class="value">${data.circle}</span></div>` : ''}
            `;
            document.getElementById('locationContent').innerHTML = locHTML;

            // Spam Check
            if (data.is_spam) {
                document.getElementById('spamCard').style.display = 'block';
                document.getElementById('spamContent').innerHTML = `
                    <div class="spam-warning">
                        <span class="icon">🚨</span>
                        <span class="text">यह नंबर स्पैम के रूप में रिपोर्ट किया गया है!${data.spam_count ? ` (${data.spam_count} लोगों ने रिपोर्ट किया)` : ''}</span>
                    </div>
                `;
            } else {
                document.getElementById('spamCard').style.display = 'none';
            }
        }

        function showError(msg) {
            document.getElementById('result').style.display = 'block';
            document.getElementById('infoContent').innerHTML = `
                <div style="background:#ffebee; padding:15px; border-radius:12px; color:#b71c1c; text-align:center;">
                    ❌ ${msg}
                </div>
            `;
            document.getElementById('locationContent').innerHTML = '';
            document.getElementById('nameCard').style.display = 'none';
            document.getElementById('spamCard').style.display = 'none';
        }

        // Enter key support
        document.getElementById('phoneInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('searchBtn').click();
            }
        });

        // Load history on page load
        loadHistory();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/lookup')
def lookup():
    number = request.args.get('number')
    if not number:
        return jsonify({'error': 'नंबर डालें'}), 400
    
    result = {}
    
    try:
        # ---------- STEP 1: PhoneNumber Library (Free Local) ----------
        parsed = phonenumbers.parse(number, None)
        
        result['international'] = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        result['national'] = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
        result['is_valid'] = phonenumbers.is_valid_number(parsed)
        result['is_possible'] = phonenumbers.is_possible_number(parsed)
        result['country'] = geocoder.description_for_number(parsed, 'en') or 'Unknown'
        result['operator'] = carrier.name_for_number(parsed, 'en') or 'Unknown'
        result['timezone'] = list(timezone.time_zones_for_number(parsed))
        
        # ---------- STEP 2: phone-circle-locator (Free - India Only) ----------
        try:
            from phone_circle_locator import lookup as circle_lookup
            import re
            digits = re.sub(r'\D', '', number)
            if len(digits) >= 10:
                last_10 = digits[-10:]
                circle_data = circle_lookup(last_10)
                if circle_data:
                    result['circle'] = circle_data.get('circle', '')
                    if not result['operator'] or result['operator'] == 'Unknown':
                        result['operator'] = circle_data.get('operator', 'Unknown')
        except:
            pass  # Library not installed, skip
        
        # ---------- STEP 3: Veriphone API (Free 1000/mo) ----------
        if VERIPHONE_API_KEY:
            try:
                vp_url = f"https://api.veriphone.com/v2/verify?phone={number}&key={VERIPHONE_API_KEY}"
                vp_resp = requests.get(vp_url, timeout=5)
                if vp_resp.status_code == 200:
                    vp_data = vp_resp.json()
                    if vp_data.get('phone_valid'):
                        result['line_type'] = vp_data.get('phone_type', 'Unknown').capitalize()
                        if not result['operator'] or result['operator'] == 'Unknown':
                            result['operator'] = vp_data.get('carrier', 'Unknown')
                        result['country'] = vp_data.get('country', result['country'])
            except:
                pass
        
        # ---------- STEP 4: Numverify API (Free 100/mo) ----------
        if NUMVERIFY_API_KEY:
            try:
                nv_url = f"http://apilayer.net/api/validate?access_key={NUMVERIFY_API_KEY}&number={number}"
                nv_resp = requests.get(nv_url, timeout=5)
                if nv_resp.status_code == 200:
                    nv_data = nv_resp.json()
                    if nv_data.get('valid'):
                        result['line_type'] = nv_data.get('line_type', result.get('line_type', 'Unknown')).capitalize()
                        result['location'] = nv_data.get('location', '')
                        if not result['operator'] or result['operator'] == 'Unknown':
                            result['operator'] = nv_data.get('carrier', 'Unknown')
                        result['country'] = nv_data.get('country_name', result['country'])
            except:
                pass
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'❌ गलत नंबर: {str(e)}'}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)