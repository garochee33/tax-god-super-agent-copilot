# Tax God — Build Log

## 2026-06-05 (Kiro Agent — iMac Terminal)

### Commits:
| SHA | Message |
|-----|---------|
| e61217a | chore: consolidate as canonical repo |
| 32af820 | fix: full audit cleanup — imports, bare excepts, TS config |
| 29c4795 | feat: subscription billing (Stripe), free trial, setup script |
| ee9cba6 | feat: admin settings page |
| 3e4ad2c | enhance: settings UX — links, show/hide, help text |
| a2eae49 | feat: settings 10 upgrades — rotation, audit, keychain, profiles |
| cda8cd6 | refactor: 100% local-only sovereign app |
| 1f97a03 | feat: post-registration onboarding wizard |
| 874f339 | feat: activity logs, build tracker, knowledge base |

### Decisions:
- Consolidated `tas-god-super-agent` (archived) into this repo
- 100% local sovereign — no cloud deploy
- Subscription: 7-day trial → $29/mo Stripe
- Auto-generate secrets on setup (SECRET_KEY, ENCRYPTION_KEY)
- .app launcher with first-run detection
- Onboarding wizard guides new users through API key setup

### Systems Added:
- Subscription/billing (Stripe integration)
- Admin settings (UI + 10 advanced features)
- Activity logs (all user actions)
- Build logs (agent contributions)
- Knowledge base (docs, reports, memories)
- Onboarding wizard (4-step guided setup)

---

## Tracking Tables (PostgreSQL):

| Table | Purpose |
|-------|---------|
| users | Accounts + roles (admin/preparer/reviewer/client) |
| subscriptions | Tier + Stripe IDs + trial expiry |
| activity_logs | All user/system actions |
| build_logs | Coding agent contributions |
| knowledge_entries | Persistent KB (docs, reports, notes) |
| settings_audit_log | Every .env key change with hashes |
