import logging
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models import User, Workspace, WorkspaceMember, WorkspaceRole, Environment, Server

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_seed():
    """Seeds the database with development initial data."""
    db = SessionLocal()
    try:
        # Check if seed user already exists
        existing_user = db.scalar(select(User).where(User.email == "dev@example.com"))
        if existing_user:
            logger.info("Seed data already present. Skipping.")
            return

        logger.info("Seeding development data...")

        # 1. Create Demo User
        user = User(
            email="dev@example.com",
            name="DevOps Developer",
            password_hash="placeholder_hash_not_for_production",
            is_active=True,
        )
        db.add(user)
        db.flush()

        # 2. Create Demo Workspace
        workspace = Workspace(
            name="Demo Workspace",
            description="Company-agnostic demo workspace for testing",
            timezone="UTC",
        )
        db.add(workspace)
        db.flush()

        # 3. Create Workspace Membership
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user.id,
            role=WorkspaceRole.OWNER.value,
        )
        db.add(member)

        # 4. Create Environments
        env_dev = Environment(
            workspace_id=workspace.id,
            name="Development",
            key="development",
            description="Development environment for local tests",
        )
        env_staging = Environment(
            workspace_id=workspace.id,
            name="Staging",
            key="staging",
            description="Staging pre-production environment",
        )
        env_prod = Environment(
            workspace_id=workspace.id,
            name="Production",
            key="production",
            description="Live production environment",
        )
        db.add_all([env_dev, env_staging, env_prod])
        db.flush()

        # 5. Create Servers
        srv_dev = Server(
            workspace_id=workspace.id,
            environment_id=env_dev.id,
            name="Development Server",
            hostname="dev.local",
            ip_address="127.0.0.1",
            ssh_port=22,
            username="devops",
            operating_system="Ubuntu 22.04 LTS",
            description="Local simulated development server",
            is_active=True,
        )
        srv_staging = Server(
            workspace_id=workspace.id,
            environment_id=env_staging.id,
            name="Staging Server",
            hostname="staging.local",
            ip_address="192.168.1.50",
            ssh_port=2222,
            username="devops",
            operating_system="Debian 12",
            description="Pre-release testing server",
            is_active=True,
        )
        srv_prod = Server(
            workspace_id=workspace.id,
            environment_id=env_prod.id,
            name="Production Server",
            hostname="prod.internal",
            ip_address="10.0.0.10",
            ssh_port=22,
            username="admin",
            operating_system="Rocky Linux 9",
            description="High-availability production server",
            is_active=True,
        )
        db.add_all([srv_dev, srv_staging, srv_prod])

        db.commit()
        logger.info("Successfully seeded development data.")

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
