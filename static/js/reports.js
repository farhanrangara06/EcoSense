/**
 * EcoSense Report Submission JavaScript
 */

document.addEventListener('DOMContentLoaded', async () => {
    // Load areas into dropdown
    const res = await fetch('/api/areas');
    const data = await res.json();
    const sel = document.getElementById('reportArea');
    data.areas.forEach((a, i) => {
        sel.innerHTML += `<option value="${a.id}" ${i === 0 ? 'selected' : ''}>${a.name}, ${a.city}</option>`;
    });

    // Handle form submission
    document.getElementById('reportForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const btn = e.target.querySelector('button[type="submit"]');
        btn.disabled = true;
        btn.textContent = 'Submitting...';

        try {
            const res = await fetch('/api/reports', { method: 'POST', body: formData });
            const result = await res.json();

            if (result.success) {
                document.getElementById('reportForm').style.display = 'none';
                const successEl = document.getElementById('reportSuccess');
                successEl.style.display = 'block';
                successEl.innerHTML = `
                    <h3>✅ Concern Submitted Successfully!</h3>
                    <p>Report ID: <strong>${result.report_id}</strong></p>
                    <p>Status: <span class="status-badge status-pending">Pending</span></p>
                    <p>Your report has been sent to the admin for review.</p>
                    <a href="/my-reports" class="btn btn-primary" style="margin-top:1rem">View My Reports</a>`;
            } else {
                alert(result.error || 'Failed to submit report.');
                btn.disabled = false;
                btn.textContent = 'Submit Concern';
            }
        } catch (err) {
            alert('Error submitting report. Please try again.');
            btn.disabled = false;
            btn.textContent = 'Submit Concern';
        }
    });
});
