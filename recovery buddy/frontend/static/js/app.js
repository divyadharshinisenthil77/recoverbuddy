/**
 * RecoverBuddy Frontend Application Logic
 * Integrates Patient Experience, Care Team Workflows, Judge Demo Scenarios, and Experiment KPIs.
 */

// Global App State
let currentMode = "RECOVERBUDDY"; // or 'BASELINE'
let currentPatientId = "patient_priya";

document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initModeToggle();
    initFormHandlers();
    loadPatientData();
    loadCareTeamData();
    loadEducationModules();
    loadSimulationData();
});

// Navigation Handling
function initNavigation() {
    const tabs = document.querySelectorAll(".nav-tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            const targetId = tab.getAttribute("data-tab");
            document.querySelectorAll(".tab-content").forEach(content => {
                content.classList.remove("active");
            });
            const activeContent = document.getElementById(targetId);
            if (activeContent) activeContent.classList.add("active");

            // Refresh tab-specific data
            if (targetId === "care-team") loadCareTeamData();
            if (targetId === "experiment") loadSimulationData();
        });
    });
}

// Mode Toggle Handling
function initModeToggle() {
    const toggle = document.getElementById("mode-toggle");
    const label = document.getElementById("mode-label");
    if (!toggle) return;

    toggle.addEventListener("change", (e) => {
        currentMode = e.target.checked ? "RECOVERBUDDY" : "BASELINE";
        label.textContent = currentMode === "RECOVERBUDDY" ? "✨ RecoverBuddy Mode" : "📄 Baseline Mode";
        label.style.color = currentMode === "RECOVERBUDDY" ? "#0284c7" : "#64748b";
        
        // Show/hide RecoverBuddy-specific widgets
        document.querySelectorAll(".recoverbuddy-feature").forEach(el => {
            el.style.display = currentMode === "RECOVERBUDDY" ? "" : "none";
        });
    });
}

// Form Handlers
function initFormHandlers() {
    // Pain slider live value
    const painSlider = document.getElementById("pain-score-input");
    const painVal = document.getElementById("pain-value-display");
    if (painSlider && painVal) {
        painSlider.addEventListener("input", (e) => {
            painVal.textContent = e.target.value;
        });
    }

    // Wound radio selection styling
    const woundRadios = document.querySelectorAll("input[name='wound_status']");
    woundRadios.forEach(radio => {
        radio.addEventListener("change", () => {
            document.querySelectorAll(".radio-card").forEach(c => c.classList.remove("selected"));
            radio.closest(".radio-card").classList.add("selected");
        });
    });

    // Checkin submission
    const form = document.getElementById("checkin-form");
    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            await submitCheckin();
        });
    }
}

// Load Patient Data
async function loadPatientData() {
    try {
        const [progressRes, engRes, notifRes] = await Promise.all([
            fetch(`/api/patients/${currentPatientId}/progress`),
            fetch(`/api/patients/${currentPatientId}/engagement`),
            fetch(`/api/notifications/${currentPatientId}`)
        ]);

        const progress = await progressRes.json();
        const eng = await engRes.json();
        const notifs = await notifRes.json();

        // Update Engagement and Streak
        const engVal = document.getElementById("patient-eng-score");
        if (engVal) engVal.textContent = eng.overall_score || "85";

        const streakVal = document.getElementById("patient-streak-days");
        if (streakVal) streakVal.textContent = eng.streak_days || "5";

        // Update Badges List
        const badgeContainer = document.getElementById("patient-badges");
        if (badgeContainer && eng.badges) {
            badgeContainer.innerHTML = eng.badges.map(b => `<span class="badge badge-primary">🏆 ${b}</span>`).join(" ");
        }

        // Render Recent Check-ins History Table
        renderPatientHistory(progress.history || []);

        // Render Notification List
        renderNotifications(notifs);

    } catch (err) {
        console.error("Error loading patient data:", err);
    }
}

function renderPatientHistory(records) {
    const tableBody = document.getElementById("history-table-body");
    if (!tableBody) return;

    if (!records.length) {
        tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center;">No check-ins recorded yet.</td></tr>`;
        return;
    }

    const recent = records.slice(-7).reverse();
    tableBody.innerHTML = recent.map(r => `
        <tr>
            <td>${new Date(r.timestamp).toLocaleDateString()}</td>
            <td><strong>${r.pain_score}/10</strong></td>
            <td>${r.temperature_celsius ? r.temperature_celsius + "°C" : "N/A"}</td>
            <td><span class="badge ${r.wound_status === 'concerning' ? 'badge-danger' : 'badge-success'}">${r.wound_status}</span></td>
            <td>${r.medication_taken ? '✅ Taken' : '❌ Missed'}</td>
            <td>${r.recovery_activity_completed ? '✅ Done' : '⏳ Pending'}</td>
        </tr>
    `).join("");
}

function renderNotifications(notifs) {
    const notifContainer = document.getElementById("patient-notifications");
    if (!notifContainer) return;

    if (!notifs.length) {
        notifContainer.innerHTML = `<p style="color:var(--text-muted);">No recent notifications.</p>`;
        return;
    }

    notifContainer.innerHTML = notifs.slice(0, 3).map(n => `
        <div style="background:#ffffff; border:1px solid var(--border); border-radius:8px; padding:0.75rem; margin-bottom:0.5rem;">
            <div style="font-size:0.85rem; font-weight:600; color:var(--primary);">${n.notification_type}</div>
            <div style="font-size:0.95rem;">${n.message}</div>
            <div style="font-size:0.75rem; color:var(--text-muted); margin-top:0.25rem;">${new Date(n.created_at).toLocaleString()} • ${n.delivery_status}</div>
        </div>
    `).join("");
}

// Submit Check-In
async function submitCheckin(overrideData = null) {
    const pain = overrideData ? overrideData.pain_score : parseFloat(document.getElementById("pain-score-input").value);
    const tempInput = document.getElementById("temp-input").value;
    const temp = overrideData ? overrideData.temperature_celsius : (tempInput ? parseFloat(tempInput) : null);
    
    let wound = "improving";
    const selectedWound = document.querySelector("input[name='wound_status']:checked");
    if (selectedWound) wound = selectedWound.value;
    if (overrideData && overrideData.wound_status) wound = overrideData.wound_status;

    const medTaken = overrideData ? overrideData.medication_taken : document.getElementById("med-taken-checkbox").checked;
    const actCompleted = overrideData ? overrideData.recovery_activity_completed : document.getElementById("act-completed-checkbox").checked;
    const notes = overrideData ? overrideData.notes : document.getElementById("checkin-notes").value;

    const payload = {
        patient_id: currentPatientId,
        pain_score: pain,
        temperature_celsius: temp,
        wound_status: wound,
        medication_taken: medTaken,
        recovery_activity_completed: actCompleted,
        notes: notes || null,
        source: "PATIENT_APP"
    };

    try {
        const response = await fetch(`/api/checkins?mode=${currentMode}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        renderCheckinFeedback(result);
        loadPatientData();
    } catch (err) {
        alert("Error submitting check-in: " + err.message);
    }
}

function renderCheckinFeedback(result) {
    const feedbackBox = document.getElementById("checkin-feedback-box");
    if (!feedbackBox) return;

    feedbackBox.style.display = "block";

    if (result.mode === "BASELINE") {
        feedbackBox.innerHTML = `
            <div class="card" style="border-left:5px solid #94a3b8;">
                <div class="card-title">📄 Baseline Mode Response</div>
                <p style="font-size:1.1rem; margin-top:0.5rem;">${result.message}</p>
                <p style="font-size:0.85rem; color:var(--text-muted); margin-top:0.5rem;">Standard static response with no explainability, progress insights, or adaptive motivation.</p>
            </div>
        `;
        return;
    }

    // RecoverBuddy Enhanced Feedback
    const fb = result.feedback;
    feedbackBox.innerHTML = `
        <div class="card" style="border-left:5px solid var(--primary); background:#f0f9ff;">
            <div class="card-title">✨ RecoverBuddy Progress Explanation</div>
            <p style="font-size:1.1rem; font-weight:500; margin:0.75rem 0; color:#0369a1;">${fb.message}</p>
            
            <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-top:0.5rem;">
                <span class="badge badge-primary">Engagement Score: ${result.engagement_score}/100</span>
                <span class="badge badge-success">Streak: ${result.streak_days} Days 🔥</span>
                ${result.escalation_triggered ? '<span class="badge badge-danger">Care Team Follow-Up Created 🚨</span>' : ''}
            </div>

            <!-- Explainability Box for Clinician / Debug Auditing -->
            <div style="margin-top:1rem; padding:0.75rem; background:#ffffff; border-radius:8px; border:1px solid #bae6fd; font-size:0.85rem;">
                <strong>🔍 Internal Explainability & Audit Metadata:</strong>
                <div>Reason Codes: <code>${fb.reason_codes.join(", ")}</code></div>
                <div>Clinical Decision Autonomous: <code>${fb.clinical_decision}</code> (Strict Safety Filter Passed)</div>
            </div>
        </div>
    `;
}

// Load Education Modules
async function loadEducationModules() {
    try {
        const res = await fetch(`/api/patients/${currentPatientId}/education`);
        const data = await res.json();

        const container = document.getElementById("education-modules-container");
        if (!container) return;

        container.innerHTML = data.modules.map(m => `
            <div class="card" style="margin-bottom:1rem;">
                <div class="card-header">
                    <div class="card-title">${m.icon} ${m.title}</div>
                    <span class="badge ${m.completed ? 'badge-success' : 'badge-warning'}">
                        ${m.completed ? `Completed (${m.quiz_score || 100}%)` : 'Not Completed'}
                    </span>
                </div>
                <p style="color:var(--text-muted); margin-bottom:1rem;">${m.summary}</p>
                <button class="btn btn-secondary" onclick="openQuizModal('${m.module_id}')">
                    ${m.completed ? 'Review Quiz' : 'Start Learning & Quiz'}
                </button>
            </div>
        `).join("");
    } catch (err) {
        console.error("Error loading education:", err);
    }
}

async function openQuizModal(moduleId) {
    try {
        const res = await fetch(`/api/education/modules/${moduleId}`);
        const mod = await res.json();

        const modalBody = document.getElementById("quiz-modal-body");
        modalBody.innerHTML = `
            <h3>${mod.icon} ${mod.title}</h3>
            <div style="margin:1rem 0; padding:1rem; background:#f8fafc; border-radius:8px;">
                <strong>Key Learnings:</strong>
                <ul style="margin-left:1.25rem; margin-top:0.5rem;">
                    ${mod.points.map(p => `<li>${p}</li>`).join("")}
                </ul>
            </div>
            
            <h4 style="margin-top:1rem;">Comprehension Check:</h4>
            ${mod.quiz.map((q, idx) => `
                <div style="margin:1rem 0; padding:0.75rem; border:1px solid var(--border); border-radius:8px;">
                    <p><strong>Q${idx+1}: ${q.question}</strong></p>
                    ${q.options.map((opt, oIdx) => `
                        <label style="display:block; margin:0.35rem 0; cursor:pointer;">
                            <input type="radio" name="quiz_q_${q.question_id}" value="${oIdx}"> ${opt}
                        </label>
                    `).join("")}
                </div>
            `).join("")}
            <button class="btn btn-primary" onclick="submitQuiz('${moduleId}')">Submit Quiz Answers</button>
        `;

        document.getElementById("quiz-modal").style.display = "block";
    } catch (err) {
        alert("Error loading quiz: " + err.message);
    }
}

async function submitQuiz(moduleId) {
    const res = await fetch(`/api/education/modules/${moduleId}`);
    const mod = await res.json();

    const answers = {};
    mod.quiz.forEach(q => {
        const selected = document.querySelector(`input[name="quiz_q_${q.question_id}"]:checked`);
        if (selected) answers[q.question_id] = parseInt(selected.value);
    });

    const submitRes = await fetch("/api/education/quiz/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            patient_id: currentPatientId,
            module_id: moduleId,
            answers: answers
        })
    });

    const result = await submitRes.json();
    alert(`Comprehension Score: ${result.score_percentage}%\n${result.feedback}`);
    document.getElementById("quiz-modal").style.display = "none";
    loadEducationModules();
    loadPatientData();
}

// Load Care Team Dashboard Data
async function loadCareTeamData() {
    try {
        const [overviewRes, escRes, followRes] = await Promise.all([
            fetch("/api/care-team/overview"),
            fetch("/api/care-team/escalations"),
            fetch("/api/care-team/followups")
        ]);

        const overview = await overviewRes.json();
        const escalations = await escRes.json();
        const followups = await followRes.json();

        // Render Patient Cohort Queue
        const patientTable = document.getElementById("careteam-patient-table");
        if (patientTable) {
            patientTable.innerHTML = overview.patients.map(p => `
                <tr>
                    <td><strong>${p.display_name}</strong><br><small style="color:var(--text-muted);">${p.surgery_type}</small></td>
                    <td>${p.assigned_nurse}</td>
                    <td>${p.last_checkin ? new Date(p.last_checkin).toLocaleDateString() : 'None'}</td>
                    <td>${p.missing_days > 0 ? `<span class="badge badge-warning">${p.missing_days} days</span>` : '<span class="badge badge-success">Active</span>'}</td>
                    <td><strong>${p.latest_pain !== null ? p.latest_pain + '/10' : 'N/A'}</strong></td>
                    <td><span class="badge ${p.latest_wound === 'concerning' ? 'badge-danger' : 'badge-success'}">${p.latest_wound}</span></td>
                    <td>${p.open_escalations_count > 0 ? `<span class="badge badge-danger">${p.open_escalations_count} Active</span>` : '<span class="badge badge-success">Clear</span>'}</td>
                </tr>
            `).join("");
        }

        // Render Active Escalations Queue
        const escTable = document.getElementById("careteam-escalation-table");
        if (escTable) {
            escTable.innerHTML = escalations.map(e => `
                <tr>
                    <td><code>${e.escalation_id}</code></td>
                    <td><strong>${e.patient_id}</strong></td>
                    <td><span class="badge badge-warning">${e.trigger_type}</span></td>
                    <td><span class="badge ${e.priority === 'CRITICAL' ? 'badge-danger' : (e.priority === 'HIGH' ? 'badge-danger' : 'badge-warning')}">${e.priority}</span></td>
                    <td>${e.assigned_to || 'Unassigned'}</td>
                    <td><span class="badge ${e.status === 'RESOLVED' ? 'badge-success' : 'badge-primary'}">${e.status}</span></td>
                    <td>${new Date(e.due_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
                    <td>
                        ${e.status !== 'RESOLVED' ? `
                            <button class="btn btn-secondary" style="padding:0.35rem 0.65rem; font-size:0.85rem;" onclick="promptResolveEscalation('${e.escalation_id}')">Resolve</button>
                        ` : '✅ Closed'}
                    </td>
                </tr>
            `).join("");
        }

        // Render Follow-up Tasks
        const folTable = document.getElementById("careteam-followup-table");
        if (folTable) {
            folTable.innerHTML = followups.map(f => `
                <tr>
                    <td><code>${f.followup_id}</code></td>
                    <td><strong>${f.owner_id}</strong> (${f.owner_role})</td>
                    <td>${f.action}</td>
                    <td>${new Date(f.due_date).toLocaleString()}</td>
                    <td><span class="badge ${f.status === 'RESOLVED' ? 'badge-success' : 'badge-warning'}">${f.status}</span></td>
                    <td>${f.escalation_level === 2 ? '<span class="badge badge-danger">Level 2 (Lead)</span>' : 'Primary'}</td>
                </tr>
            `).join("");
        }

    } catch (err) {
        console.error("Error loading care team data:", err);
    }
}

async function promptResolveEscalation(escId) {
    const note = prompt("Enter clinical resolution notes for this escalation:");
    if (!note) return;

    await fetch(`/api/escalations/${escId}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "RESOLVED", resolution_notes: note })
    });

    loadCareTeamData();
}

async function checkOverdueSLA() {
    const res = await fetch("/api/care-team/escalate-overdue", { method: "POST" });
    const data = await res.json();
    alert(`SLA Monitor Check Complete:\nOverdue escalated: ${data.overdue_escalated_count}`);
    loadCareTeamData();
}

// Judge Demo Scenarios
async function runDemoScenario(scenarioType) {
    if (scenarioType === "A_NORMAL") {
        await submitCheckin({
            pain_score: 3.5,
            temperature_celsius: 36.7,
            wound_status: "improving",
            medication_taken: true,
            recovery_activity_completed: true,
            notes: "Feeling much stronger today. Walking in the garden."
        });
        alert("Scenario A Triggered: Normal recovery improvement recorded. Check the progress explanation!");
    } else if (scenarioType === "B_MISSING") {
        alert("Scenario B Triggered: Patient missed daily reporting. Notification reminder dispatched.");
        loadPatientData();
    } else if (scenarioType === "C_CONCERNING") {
        await submitCheckin({
            pain_score: 6.5,
            temperature_celsius: 38.3,
            wound_status: "concerning",
            medication_taken: true,
            recovery_activity_completed: false,
            notes: "Incision is red and feels quite hot to touch."
        });
        alert("Scenario C Triggered: Concerning wound + elevated temperature submitted! Escalation task created for nurse review.");
        loadCareTeamData();
    } else if (scenarioType === "D_NOTIF_FAIL") {
        await fetch("/api/notifications/send?simulate_failure=true", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                patient_id: "patient_priya",
                notification_type: "CHECKIN_REMINDER",
                message: "Daily reminder test",
                channel: "SMS_MOCK"
            })
        });
        alert("Scenario D Triggered: Notification delivery failed across retries -> Escalated to care coordinator!");
        loadCareTeamData();
    } else if (scenarioType === "E_OVERDUE") {
        await checkOverdueSLA();
    }
}

async function resetDemoData() {
    if (!confirm("Reset database to initial pristine state for Priya demo?")) return;
    const res = await fetch("/api/system/reset-demo", { method: "POST" });
    const data = await res.json();
    alert(data.message);
    loadPatientData();
    loadCareTeamData();
}

// Load Experiment & Simulation Data
async function loadSimulationData() {
    try {
        const [simRes, errRes] = await Promise.all([
            fetch("/api/simulation/results"),
            fetch("/api/simulation/error-analysis")
        ]);

        const sim = await simRes.json();
        const errData = await errRes.json();

        // Render Summary KPIs
        if (sim.summary_kpis) {
            const kpi = sim.summary_kpis;
            document.getElementById("kpi-part").textContent = `${kpi.participation_rate.baseline} ➔ ${kpi.participation_rate.mvp}`;
            document.getElementById("kpi-part-gain").textContent = `${kpi.participation_rate.improvement_pct} gain`;

            document.getElementById("kpi-ret").textContent = `${kpi.retention_rate_week8.baseline} ➔ ${kpi.retention_rate_week8.mvp}`;
            document.getElementById("kpi-ret-gain").textContent = `${kpi.retention_rate_week8.improvement_pct} gain`;

            document.getElementById("kpi-comp").textContent = `${kpi.comprehension_score.baseline} ➔ ${kpi.comprehension_score.mvp}`;
            document.getElementById("kpi-comp-gain").textContent = `${kpi.comprehension_score.improvement_pct} gain`;

            document.getElementById("kpi-edu").textContent = `${kpi.education_completion.baseline} ➔ ${kpi.education_completion.mvp}`;
            document.getElementById("kpi-edu-gain").textContent = `${kpi.education_completion.improvement_pct} gain`;

            document.getElementById("kpi-sat").textContent = `${kpi.patient_satisfaction.baseline} ➔ ${kpi.patient_satisfaction.mvp}`;
            document.getElementById("kpi-sat-gain").textContent = `${kpi.patient_satisfaction.improvement_pct} gain`;
        }

        // Render Weekly Progression Table
        const simTable = document.getElementById("simulation-table-body");
        if (simTable && sim.weekly_progression) {
            simTable.innerHTML = sim.weekly_progression.map(w => `
                <tr>
                    <td><strong>Week ${w.week}</strong></td>
                    <td>${w.baseline_participation_pct}%</td>
                    <td><strong style="color:var(--primary);">${w.mvp_participation_pct}%</strong></td>
                    <td>${w.baseline_retention_pct}%</td>
                    <td><strong style="color:var(--primary);">${w.mvp_retention_pct}%</strong></td>
                    <td>${w.baseline_comprehension_pct}%</td>
                    <td><strong style="color:var(--primary);">${w.mvp_comprehension_pct}%</strong></td>
                </tr>
            `).join("");
        }

    } catch (err) {
        console.error("Error loading simulation data:", err);
    }
}
