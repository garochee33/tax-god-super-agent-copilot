/* 
  AGORA.JS
  Client Management Interface — Coming soon; placeholder demo data
*/

export default {
    render() {
        return `
            <div class="agora-container">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Citizens of the Agora (Clients)</span>
                        <span class="badge badge-warning">Coming soon</span>
                    </div>
                    <div class="agora-coming-soon" style="padding: var(--spacing-lg); text-align: center; color: #666; border: 2px dashed var(--color-gold); border-radius: var(--border-radius-md); margin-bottom: var(--spacing-lg);">
                        <div style="font-size: 48px; margin-bottom: 12px;">🏛️</div>
                        <p style="font-weight: 600; margin-bottom: 8px;">Client CRM & management</p>
                        <p style="font-size: 14px;">Full client list, add citizen, and entity management will be wired to the backend in a future release.</p>
                    </div>

                    <div style="overflow-x: auto;">
                        <table class="client-table" style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="background: var(--color-parchment); text-align: left; font-family: var(--font-heading); font-size: 13px; color: #666;">
                                    <th style="padding: 15px;">Name</th>
                                    <th style="padding: 15px;">Entity Type</th>
                                    <th style="padding: 15px;">Status</th>
                                    <th style="padding: 15px;">Last Action</th>
                                    <th style="padding: 15px;">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr style="border-bottom: 1px solid #eee;">
                                    <td style="padding: 15px; font-weight: 600;">
                                        <div style="display: flex; align-items: center; gap: 10px;">
                                            <div class="avatar" style="width: 30px; height: 30px; font-size: 12px;">JD</div>
                                            John Doe
                                        </div>
                                    </td>
                                    <td style="padding: 15px;">Individual (1040)</td>
                                    <td style="padding: 15px;"><span class="badge badge-success">Filed</span></td>
                                    <td style="padding: 15px; color: #666;">2 days ago</td>
                                    <td style="padding: 15px;"><button class="btn btn-sm btn-outline" disabled title="Coming soon">View</button></td>
                                </tr>
                                <tr style="border-bottom: 1px solid #eee;">
                                    <td style="padding: 15px; font-weight: 600;">
                                        <div style="display: flex; align-items: center; gap: 10px;">
                                            <div class="avatar" style="width: 30px; height: 30px; font-size: 12px; background: var(--color-gold); color: white;">AC</div>
                                            Acme Corp
                                        </div>
                                    </td>
                                    <td style="padding: 15px;">C-Corp (1120)</td>
                                    <td style="padding: 15px;"><span class="badge badge-warning">Audit Risk</span></td>
                                    <td style="padding: 15px; color: #666;">5 hours ago</td>
                                    <td style="padding: 15px;"><button class="btn btn-sm btn-outline" disabled title="Coming soon">View</button></td>
                                </tr>
                                <tr style="border-bottom: 1px solid #eee;">
                                    <td style="padding: 15px; font-weight: 600;">
                                        <div style="display: flex; align-items: center; gap: 10px;">
                                            <div class="avatar" style="width: 30px; height: 30px; font-size: 12px;">SJ</div>
                                            Sarah Jones
                                        </div>
                                    </td>
                                    <td style="padding: 15px;">Sole Prop (Sch C)</td>
                                    <td style="padding: 15px;"><span class="badge badge-gold">In Review</span></td>
                                    <td style="padding: 15px; color: #666;">Just now</td>
                                    <td style="padding: 15px;"><button class="btn btn-sm btn-outline" disabled title="Coming soon">View</button></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div style="padding: 15px; font-size: 12px; color: #999;">Demo data. Connect clients API when available.</div>
                </div>
            </div>
        `;
    },

    async init() {
        // Placeholder until clients API is available
    }
};
