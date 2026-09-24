document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('.auth-form');
    if (!form) return;

    const isRegister = Boolean(document.getElementById('name'));
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const endpoint = isRegister ? '/api/register' : '/api/login';
        const payload = {
            email: document.getElementById('email').value.trim(),
            password: document.getElementById('password').value,
        };
        if (isRegister) {
            payload.name = document.getElementById('name').value.trim();
        }

        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            cache: 'no-store',
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) {
            alert(data.error || 'Request failed. Please try again.');
            return;
        }
        window.location.href = data.redirect || '/dashboard';
    });
});
