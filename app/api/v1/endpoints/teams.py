"""
Tax God API - Team & Preparer Management Endpoints
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select

from app.api.deps import AdminUser, CurrentUser, DBSession, PreparerOrAdmin
from app.models.client import Client
from app.models.team import ClientAssignment, Team, TeamMember
from app.models.user import User, UserRole

router = APIRouter()


class TeamCreate(BaseModel):
    name: str


class MemberInvite(BaseModel):
    email: EmailStr
    role: str = "preparer"


class AssignClient(BaseModel):
    client_id: str
    preparer_id: str


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_team(body: TeamCreate, user: AdminUser, db: DBSession):
    team = Team(name=body.name, owner_id=user.id)
    db.add(team)
    await db.flush()
    member = TeamMember(team_id=team.id, user_id=user.id, role="owner")
    db.add(member)
    await db.commit()
    await db.refresh(team)
    return {"id": team.id, "name": team.name, "owner_id": team.owner_id}


@router.get("")
async def list_teams(user: CurrentUser, db: DBSession):
    result = await db.execute(
        select(Team).join(TeamMember, TeamMember.team_id == Team.id).where(TeamMember.user_id == user.id)
    )
    teams = result.scalars().all()
    return [{"id": t.id, "name": t.name, "owner_id": t.owner_id} for t in teams]


@router.post("/{team_id}/members", status_code=status.HTTP_201_CREATED)
async def invite_member(team_id: str, body: MemberInvite, user: PreparerOrAdmin, db: DBSession):
    team = await db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    result = await db.execute(select(User).where(User.email == body.email))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    member = TeamMember(team_id=team_id, user_id=target.id, role=body.role)
    db.add(member)
    await db.commit()
    return {"team_id": team_id, "user_id": target.id, "role": body.role}


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(team_id: str, user_id: str, user: AdminUser, db: DBSession):
    result = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    await db.delete(member)
    await db.commit()


@router.post("/assign-client", status_code=status.HTTP_201_CREATED)
async def assign_client(body: AssignClient, user: PreparerOrAdmin, db: DBSession):
    assignment = ClientAssignment(
        client_id=body.client_id, preparer_id=body.preparer_id, assigned_by=user.id
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return {"id": assignment.id, "client_id": assignment.client_id, "preparer_id": assignment.preparer_id, "status": assignment.status}


@router.get("/my-assignments")
async def my_assignments(user: CurrentUser, db: DBSession):
    result = await db.execute(
        select(ClientAssignment, Client.name)
        .join(Client, Client.id == ClientAssignment.client_id)
        .where(ClientAssignment.preparer_id == user.id, ClientAssignment.status == "active")
    )
    rows = result.all()
    return [{"id": r[0].id, "client_id": r[0].client_id, "client_name": r[1], "status": r[0].status} for r in rows]


@router.get("/workload")
async def workload(user: AdminUser, db: DBSession):
    result = await db.execute(
        select(User.id, User.full_name, User.email, func.count(ClientAssignment.id).label("client_count"))
        .outerjoin(ClientAssignment, (ClientAssignment.preparer_id == User.id) & (ClientAssignment.status == "active"))
        .where(User.role == UserRole.PREPARER.value)
        .group_by(User.id)
    )
    rows = result.all()
    return [{"user_id": r[0], "full_name": r[1], "email": r[2], "client_count": r[3]} for r in rows]
