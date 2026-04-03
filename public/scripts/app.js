/* ================================================================
   AI Resume Analyzer — Frontend Application Logic
   ================================================================ */

// ==================== CONFIG ====================
const API_BASE = "https://resume-analyzer-api-go7i.onrender.com";

// ==================== DOM REFERENCES ====================
const uploadZone = document.getElementById('uploadZone');
const resumeInput = document.getElementById('resumeInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileRemove = document.getElementById('fileRemove');
const jdTextarea = document.getElementById('jdTextarea');
const charCount = document.getElementById('charCount');
const analyzeBtn = document.getElementById('analyzeBtn');
const btnLoader = document.getElementById('btnLoader');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingTitle = document.getElementById('loadingTitle');
const loadingStep = document.getElementById('loadingStep');
const progressBar = document.getElementById('progressBar');
const resultsSection = document.getElementById('resultsSection');
const rewriteBtn = document.getElementById('rewriteBtn');
const rewriteInput = document.getElementById('rewriteInput');
const rewriteOutput = document.getElementById('rewriteOutput');
const rewriteResult = document.getElementById('rewriteResult');
const rewriteLoader = document.getElementById('rewriteLoader');
const exportBtn = document.getElementById('exportBtn');
const copyRewriteBtn = document.getElementById('copyRewriteBtn');

// State
let selectedFile = null;
let lastResults = null;

// ==================== PARTICLE BACKGROUND ====================
function initParticles() {
    const canvas = document.getElementById('particleCanvas');
    const ctx = canvas.getContext('2d');
    let particles = [];

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    class Particle {
        constructor() {
            this.reset();
        }
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = (Math.random() - 0.5) * 0.3;
            this.vy = (Math.random() - 0.5) * 0.3;
            this.radius = Math.random() * 1.5 + 0.5;
            this.opacity = Math.random() * 0.4 + 0.1;
        }
        update() {
            this.x += this.vx;
            this.y += this.vy;
            if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
            if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(34, 211, 238, ${this.opacity})`;
            ctx.fill();
        }
    }

    const count = Math.min(80, Math.floor(window.innerWidth / 15));
    for (let i = 0; i < count; i++) {
        particles.push(new Particle());
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw connections
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(34, 211, 238, ${0.06 * (1 - dist / 120)})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }

        particles.forEach(p => {
            p.update();
            p.draw();
        });

        requestAnimationFrame(animate);
    }
    animate();
}

// ==================== UPLOAD HANDLING ====================
uploadZone.addEventListener('click', () => resumeInput.click());

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('drag-over');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('drag-over');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
        handleFileSelect(file);
    } else {
        showToast('Please upload a PDF file', 'error');
    }
});

resumeInput.addEventListener('change', (e) => {
    if (e.target.files[0]) {
        handleFileSelect(e.target.files[0]);
    }
});

function handleFileSelect(file) {
    selectedFile = file;
    fileName.textContent = file.name;
    fileInfo.classList.remove('hidden');
    uploadZone.style.display = 'none';
    updateAnalyzeBtn();
}

fileRemove.addEventListener('click', () => {
    selectedFile = null;
    resumeInput.value = '';
    fileInfo.classList.add('hidden');
    uploadZone.style.display = '';
    updateAnalyzeBtn();
});

// ==================== TEXTAREA ====================
jdTextarea.addEventListener('input', () => {
    charCount.textContent = `${jdTextarea.value.length} characters`;
    updateAnalyzeBtn();
});

function updateAnalyzeBtn() {
    analyzeBtn.disabled = !(selectedFile && jdTextarea.value.trim().length > 20);
}

// ==================== ROLE SELECTOR ====================
document.querySelectorAll('.role-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.role-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    });
});

// ==================== LOADING ANIMATION ====================
const loadingSteps = [
    'Extracting text from PDF',
    'Parsing resume structure',
    'Analyzing job description',
    'Computing semantic similarity',
    'Matching keywords',
    'Identifying skill gaps',
    'Generating AI insights',
    'Compiling results'
];

function showLoading() {
    loadingOverlay.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    let stepIndex = 0;
    let progress = 0;

    const stepInterval = setInterval(() => {
        if (stepIndex < loadingSteps.length) {
            loadingStep.textContent = loadingSteps[stepIndex];
            stepIndex++;
            progress = Math.min(90, progress + Math.random() * 15 + 5);
            progressBar.style.width = `${progress}%`;
        }
    }, 600);

    return () => {
        clearInterval(stepInterval);
        progressBar.style.width = '100%';
        setTimeout(() => {
            loadingOverlay.classList.add('hidden');
            document.body.style.overflow = '';
        }, 400);
    };
}

// ==================== ANALYZE API CALL ====================
analyzeBtn.addEventListener('click', async () => {
    if (!selectedFile || !jdTextarea.value.trim()) return;

    const btnText = analyzeBtn.querySelector('.btn-text');
    btnText.classList.add('hidden');
    btnLoader.classList.remove('hidden');
    analyzeBtn.disabled = true;

    const hideLoading = showLoading();

    try {
        const formData = new FormData();
        formData.append('resume', selectedFile);
        formData.append('job_description', jdTextarea.value);

        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        lastResults = data;
        renderResults(data);

    } catch (err) {
        console.error('Analysis failed:', err);
        showToast('Failed to connect to the server. Make sure the backend is running.', 'error');
    } finally {
        hideLoading();
        btnText.classList.remove('hidden');
        btnLoader.classList.add('hidden');
        updateAnalyzeBtn();
    }
});

// ==================== RENDER RESULTS ====================
function renderResults(data) {
    resultsSection.classList.remove('hidden');

    // Smooth scroll to results
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 200);

    // Animate score circle
    animateScore(data.score);

    // Render skills
    renderSkills(data.matched_skills, data.missing_skills);

    // Render explanations
    renderExplanations(data.explanations);

    // Render suggestions
    renderSuggestions(data.suggestions);
}

function animateScore(score) {
    const scoreNumber = document.getElementById('scoreNumber');
    const scoreRing = document.getElementById('scoreRing');
    const semanticBar = document.getElementById('semanticBar');
    const keywordsBar = document.getElementById('keywordsBar');
    const skillsBar = document.getElementById('skillsBar');
    const semanticValue = document.getElementById('semanticValue');
    const keywordsValue = document.getElementById('keywordsValue');
    const skillsValue = document.getElementById('skillsValue');

    const overall = Math.round(score.overall);
    const circumference = 553; // 2 * PI * 88
    const offset = circumference - (circumference * overall / 100);

    // Add SVG gradient definition if not present
    const svg = document.querySelector('.score-svg');
    if (!svg.querySelector('defs')) {
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
        gradient.setAttribute('id', 'scoreGradient');
        gradient.setAttribute('x1', '0%');
        gradient.setAttribute('y1', '0%');
        gradient.setAttribute('x2', '100%');
        gradient.setAttribute('y2', '100%');

        let color1, color2;
        if (overall >= 80) {
            color1 = '#34d399'; color2 = '#22d3ee';
        } else if (overall >= 50) {
            color1 = '#fbbf24'; color2 = '#f59e0b';
        } else {
            color1 = '#f87171'; color2 = '#ef4444';
        }

        const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
        stop1.setAttribute('offset', '0%');
        stop1.setAttribute('stop-color', color1);
        const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
        stop2.setAttribute('offset', '100%');
        stop2.setAttribute('stop-color', color2);

        gradient.appendChild(stop1);
        gradient.appendChild(stop2);
        defs.appendChild(gradient);
        svg.insertBefore(defs, svg.firstChild);
    }

    // Animate score number
    let current = 0;
    const step = Math.ceil(overall / 60);
    const counter = setInterval(() => {
        current += step;
        if (current >= overall) {
            current = overall;
            clearInterval(counter);
        }
        scoreNumber.textContent = current;
    }, 20);

    // Animate ring
    setTimeout(() => {
        scoreRing.style.strokeDashoffset = offset;
    }, 100);

    // Animate breakdown bars
    setTimeout(() => {
        semanticBar.style.width = `${score.semantic}%`;
        semanticValue.textContent = `${Math.round(score.semantic)}%`;
    }, 300);

    setTimeout(() => {
        keywordsBar.style.width = `${score.keywords}%`;
        keywordsValue.textContent = `${Math.round(score.keywords)}%`;
    }, 500);

    setTimeout(() => {
        skillsBar.style.width = `${score.skills}%`;
        skillsValue.textContent = `${Math.round(score.skills)}%`;
    }, 700);
}

function renderSkills(matched, missing) {
    const matchedContainer = document.getElementById('matchedSkills');
    const missingContainer = document.getElementById('missingSkills');
    const matchedCount = document.getElementById('matchedCount');
    const missingCount = document.getElementById('missingCount');

    matchedContainer.innerHTML = '';
    missingContainer.innerHTML = '';
    matchedCount.textContent = matched.length;
    missingCount.textContent = missing.length;

    matched.forEach((skill, i) => {
        const tag = document.createElement('span');
        tag.className = 'skill-tag matched';
        tag.textContent = skill;
        tag.style.animationDelay = `${i * 0.05}s`;
        matchedContainer.appendChild(tag);
    });

    missing.forEach((skill, i) => {
        const tag = document.createElement('span');
        tag.className = 'skill-tag missing';
        tag.textContent = skill;
        tag.style.animationDelay = `${i * 0.05}s`;
        missingContainer.appendChild(tag);
    });

    if (matched.length === 0) {
        matchedContainer.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem;">No matching skills found</p>';
    }
    if (missing.length === 0) {
        missingContainer.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem;">No missing skills detected — great coverage!</p>';
    }
}

function renderExplanations(explanations) {
    const grid = document.getElementById('explanationsGrid');
    grid.innerHTML = '';

    if (!explanations || explanations.length === 0) return;

    const iconMap = {
        positive: '✅',
        warning: '⚠️',
        critical: '🔴'
    };

    explanations.forEach((exp, i) => {
        const card = document.createElement('div');
        card.className = `explanation-card ${exp.type}`;
        card.style.animationDelay = `${i * 0.1}s`;
        card.innerHTML = `
            <div class="explanation-icon">${iconMap[exp.type] || '💡'}</div>
            <div class="explanation-body">
                <h4>${escapeHtml(exp.title)}</h4>
                <p>${escapeHtml(exp.detail)}</p>
            </div>
        `;
        grid.appendChild(card);
    });
}

function renderSuggestions(suggestions) {
    const grid = document.getElementById('suggestionsGrid');
    grid.innerHTML = '';

    if (!suggestions || suggestions.length === 0) return;

    suggestions.forEach((sug, i) => {
        const card = document.createElement('div');
        card.className = 'suggestion-card';
        card.style.animationDelay = `${i * 0.1}s`;
        card.innerHTML = `
            <h4>${escapeHtml(sug.title)}</h4>
            <p>${escapeHtml(sug.detail)}</p>
        `;
        grid.appendChild(card);
    });
}

// ==================== REWRITE FEATURE ====================
rewriteBtn.addEventListener('click', async () => {
    const text = rewriteInput.value.trim();
    if (!text) {
        showToast('Please enter some text to rewrite', 'error');
        return;
    }

    const btnText = rewriteBtn.querySelector('.btn-text');
    btnText.classList.add('hidden');
    rewriteLoader.classList.remove('hidden');

    try {
        const formData = new FormData();
        formData.append('section_text', text);
        // Send JD context so the rewriter can tailor output
        const jdText = jdTextarea ? jdTextarea.value.trim() : '';
        if (jdText) {
            formData.append('jd_text', jdText);
        }

        const response = await fetch(`${API_BASE}/api/rewrite`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        rewriteResult.textContent = data.improved_text;
        rewriteOutput.classList.remove('hidden');

    } catch (err) {
        showToast('Rewrite failed. Please try again.', 'error');
    } finally {
        btnText.classList.remove('hidden');
        rewriteLoader.classList.add('hidden');
    }
});

// Copy rewrite result
copyRewriteBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(rewriteResult.textContent).then(() => {
        copyRewriteBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            Copied!
        `;
        setTimeout(() => {
            copyRewriteBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                Copy
            `;
        }, 2000);
    });
});

// ==================== EXPORT REPORT ====================
exportBtn.addEventListener('click', () => {
    if (!lastResults) return;

    const data = lastResults;
    const report = generateTextReport(data);

    const blob = new Blob([report], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'resume_analysis_report.txt';
    a.click();
    URL.revokeObjectURL(url);

    showToast('Report downloaded!', 'success');
});

function generateTextReport(data) {
    let report = '';
    report += '═══════════════════════════════════════\n';
    report += '       AI RESUME ANALYZER REPORT       \n';
    report += '═══════════════════════════════════════\n\n';

    report += `📊 OVERALL SCORE: ${Math.round(data.score.overall)}%\n`;
    report += `   Semantic Match:  ${Math.round(data.score.semantic)}%\n`;
    report += `   Keyword Match:   ${Math.round(data.score.keywords)}%\n`;
    report += `   Skills Overlap:  ${Math.round(data.score.skills)}%\n\n`;

    report += '───────────────────────────────────────\n';
    report += '🟢 MATCHED SKILLS\n';
    report += '───────────────────────────────────────\n';
    if (data.matched_skills.length > 0) {
        data.matched_skills.forEach(s => report += `  ✓ ${s}\n`);
    } else {
        report += '  None found\n';
    }

    report += '\n───────────────────────────────────────\n';
    report += '🔴 MISSING SKILLS\n';
    report += '───────────────────────────────────────\n';
    if (data.missing_skills.length > 0) {
        data.missing_skills.forEach(s => report += `  ✗ ${s}\n`);
    } else {
        report += '  None — great coverage!\n';
    }

    if (data.explanations && data.explanations.length > 0) {
        report += '\n───────────────────────────────────────\n';
        report += '❓ WHY THIS SCORE\n';
        report += '───────────────────────────────────────\n';
        data.explanations.forEach(exp => {
            const icon = exp.type === 'positive' ? '✅' : exp.type === 'warning' ? '⚠️' : '🔴';
            report += `\n${icon} ${exp.title}\n`;
            report += `   ${exp.detail}\n`;
        });
    }

    if (data.suggestions && data.suggestions.length > 0) {
        report += '\n───────────────────────────────────────\n';
        report += '💡 AI IMPROVEMENT SUGGESTIONS\n';
        report += '───────────────────────────────────────\n';
        data.suggestions.forEach((sug, i) => {
            report += `\n${i + 1}. ${sug.title}\n`;
            report += `   ${sug.detail}\n`;
        });
    }

    report += '\n═══════════════════════════════════════\n';
    report += '  Generated by AI Resume Analyzer\n';
    report += `  Date: ${new Date().toLocaleString()}\n`;
    report += '═══════════════════════════════════════\n';

    return report;
}

// ==================== TOAST NOTIFICATIONS ====================
function showToast(message, type = 'info') {
    // Remove existing toasts
    document.querySelectorAll('.toast').forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 24px;
        left: 50%;
        transform: translateX(-50%) translateY(20px);
        padding: 14px 28px;
        border-radius: 12px;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        font-weight: 500;
        z-index: 10000;
        opacity: 0;
        transition: all 0.3s ease;
        backdrop-filter: blur(20px);
        border: 1px solid ${type === 'error' ? 'rgba(248,113,113,0.3)' : type === 'success' ? 'rgba(52,211,153,0.3)' : 'rgba(34,211,238,0.3)'};
        background: ${type === 'error' ? 'rgba(248,113,113,0.15)' : type === 'success' ? 'rgba(52,211,153,0.15)' : 'rgba(34,211,238,0.15)'};
        color: ${type === 'error' ? '#f87171' : type === 'success' ? '#34d399' : '#22d3ee'};
    `;

    document.body.appendChild(toast);

    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(-50%) translateY(0)';
    });

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(-50%) translateY(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ==================== UTILITIES ====================
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ==================== INIT ====================
document.addEventListener('DOMContentLoaded', () => {
    initParticles();
});
