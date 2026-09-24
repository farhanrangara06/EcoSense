/**
 * EcoSense Report Submission JavaScript
 */

function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

function photoSrc(photo) {
    if (!photo) return '';
    if (photo.startsWith('data:')) return photo;
    return `/static/${photo}`;
}

document.addEventListener('DOMContentLoaded', async () => {
    const res = await fetch('/api/areas');
    const data = await res.json();
    const sel = document.getElementById('reportArea');
    data.areas.forEach((a, i) => {
        sel.innerHTML += `<option value="${a.id}" ${i === 0 ? 'selected' : ''}>${a.name}, ${a.city}</option>`;
    });

    document.getElementById('reportForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const btn = e.target.querySelector('button[type="submit"]');
        btn.disabled = true;
        btn.textContent = 'Submitting...';

        try {
            const payload = {
                area_id: formData.get('area_id'),
                issue_type: formData.get('issue_type'),
                description: formData.get('description'),
            };
            const photoFile = formData.get('photo');
            if (photoFile && photoFile.size > 0) {
                payload.photo_data = await fileToBase64(photoFile);
                payload.photo_type = photoFile.type || 'image/jpeg';
            }

            const res = await fetch('/api/reports', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                cache: 'no-store',
                body: JSON.stringify(payload),
            });
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
