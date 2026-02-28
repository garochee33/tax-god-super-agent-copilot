/* 
  AGORA.JS
  Client Management Interface
*/

export default {
    render() {
        return `
            <div class="agora-container">
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Citizens of the Agora (Clients)</span>
                        <button class="btn btn-primary btn-sm">
                            <svg viewBox="0 0 24 24" style="width: 16px; height: 16px; fill: currentColor; margin-right: 4px;"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
                            Add Citizen
                        </button>
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
                                    <td style="padding: 15px;">
                                        <button class="btn btn-sm btn-outline">View</button>
                                    </td>
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
                                    <td style="padding: 15px;">
                                        <button class="btn btn-sm btn-outline">View</button>
                                    </td>
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
                                    <td style="padding: 15px;">
                                        <button class="btn btn-sm btn-outline">View</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    },

    async init() {
        // Mock data, no logic needed yet
    }
};
