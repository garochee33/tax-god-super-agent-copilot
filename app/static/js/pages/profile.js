import { api } from '../app.js';

export default {
    render() {
        return `
            <div class="page-description">Manage your account information, update your display name, email, and change your password.</div>
            <div class="grid grid-2">
                <div class="card">
                    <div class="card-header"><span class="card-title">Profile Information</span></div>
                    <div id="profile-info" style="margin-bottom: var(--spacing-lg);">
                        <div class="spinner"></div>
                    </div>
                    <form id="profile-form">
                        <div style="margin-bottom: var(--spacing-md);">
                            <label style="font-size: 12px; font-weight: 600; display: block; margin-bottom: 4px;">Full Name</label>
                            <input type="text" id="profile-name" class="form-control" placeholder="Your name">
                        </div>
                        <div style="margin-bottom: var(--spacing-md);">
                            <label style="font-size: 12px; font-weight: 600; display: block; margin-bottom: 4px;">Email</label>
                            <input type="email" id="profile-email" class="form-control" placeholder="Your email">
                        </div>
                        <button type="submit" class="btn btn-primary">Save Changes</button>
                        <span id="profile-msg" style="margin-left: 12px; font-size: 13px;"></span>
                    </form>
                </div>

                <div class="card">
                    <div class="card-header"><span class="card-title">Change Password</span></div>
                    <form id="password-form">
                        <div style="margin-bottom: var(--spacing-md);">
                            <label style="font-size: 12px; font-weight: 600; display: block; margin-bottom: 4px;">Current Password</label>
                            <input type="password" id="pw-current" class="form-control" placeholder="Current password">
                        </div>
                        <div style="margin-bottom: var(--spacing-md);">
                            <label style="font-size: 12px; font-weight: 600; display: block; margin-bottom: 4px;">New Password</label>
                            <input type="password" id="pw-new" class="form-control" placeholder="New password">
                        </div>
                        <div style="margin-bottom: var(--spacing-md);">
                            <label style="font-size: 12px; font-weight: 600; display: block; margin-bottom: 4px;">Confirm New Password</label>
                            <input type="password" id="pw-confirm" class="form-control" placeholder="Confirm new password">
                        </div>
                        <button type="submit" class="btn btn-primary">Update Password</button>
                        <span id="pw-msg" style="margin-left: 12px; font-size: 13px;"></span>
                    </form>
                </div>
            </div>
        `;
    },

    async init() {
        await this.loadProfile();

        document.getElementById('profile-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const msg = document.getElementById('profile-msg');
            try {
                await api.request('PATCH', '/api/v1/profile', {
                    full_name: document.getElementById('profile-name').value,
                    email: document.getElementById('profile-email').value
                });
                msg.style.color = 'green';
                msg.textContent = 'Saved!';
            } catch (err) {
                msg.style.color = 'red';
                msg.textContent = err.message;
            }
        });

        document.getElementById('password-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const msg = document.getElementById('pw-msg');
            const newPw = document.getElementById('pw-new').value;
            if (newPw !== document.getElementById('pw-confirm').value) {
                msg.style.color = 'red';
                msg.textContent = 'Passwords do not match.';
                return;
            }
            try {
                await api.post('/api/v1/profile/password', {
                    current_password: document.getElementById('pw-current').value,
                    new_password: newPw
                });
                msg.style.color = 'green';
                msg.textContent = 'Password updated!';
                document.getElementById('password-form').reset();
            } catch (err) {
                msg.style.color = 'red';
                msg.textContent = err.message;
            }
        });
    },

    async loadProfile() {
        try {
            const profile = await api.get('/api/v1/profile');
            document.getElementById('profile-info').innerHTML = `
                <div style="display: grid; grid-template-columns: auto 1fr; gap: 8px 16px; font-size: 14px; margin-bottom: var(--spacing-lg);">
                    <strong>Name:</strong><span>${profile.full_name || '—'}</span>
                    <strong>Email:</strong><span>${profile.email || '—'}</span>
                    <strong>Role:</strong><span>${profile.role || 'user'}</span>
                    <strong>Member since:</strong><span>${profile.created_at ? new Date(profile.created_at).toLocaleDateString() : '—'}</span>
                </div>
            `;
            document.getElementById('profile-name').value = profile.full_name || '';
            document.getElementById('profile-email').value = profile.email || '';
        } catch (err) {
            document.getElementById('profile-info').innerHTML = `<p style="color: red;">${err.message}</p>`;
        }
    }
};
