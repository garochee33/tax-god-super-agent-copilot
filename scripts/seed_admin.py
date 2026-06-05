"""Seed admin user for Tax God (local SQLite)."""
import asyncio
import os
import sys

sys.path.insert(0, ".")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///db/taxgod.db")

async def main():
    from sqlalchemy import select

    from app.core.database import Base, async_session_factory, engine
    from app.core.security import hash_password
    from app.models.subscription import Subscription, SubscriptionStatus, SubscriptionTier
    from app.models.user import User, UserRole

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        email = "enzo@trinity-consortium.com"
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            print(f"⚠️  User {email} already exists.")
            return

        password = "TaxGod-Tmp-8x7K!"
        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name="Enzo Garoche",
            role=UserRole.ADMIN.value,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        sub = Subscription(
            user_id=user.id,
            tier=SubscriptionTier.PRO.value,
            status=SubscriptionStatus.ACTIVE.value,
        )
        db.add(sub)
        await db.commit()

        print("✅ Admin user created:")
        print(f"   Email:    {email}")
        print(f"   Password: {password}")
        print("   Role:     admin (full access)")
        print("   Sub:      PRO (active)")
        print("\n   ⚠️  Change your password after first login.")

asyncio.run(main())
