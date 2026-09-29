import argparse
import asyncio
import logging
import sys
from agent.config import AgentConfig
from agent.client import AgentClient
from agent.connection import AgentConnection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("devops-agent")


def main():
    parser = argparse.ArgumentParser(description="DevOps Platform Lightweight Execution Agent")
    subparsers = parser.add_subparsers(dest="command", help="Agent Command")

    # Command: enroll
    enroll_parser = subparsers.add_parser("enroll", help="Enroll agent with control plane")
    enroll_parser.add_argument("--server", required=True, help="Backend control plane URL")
    enroll_parser.add_argument("--token", required=True, help="One-time enrollment token")
    enroll_parser.add_argument("--config", default="agent_config.json", help="Path to config file")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Run agent execution loop")
    run_parser.add_argument("--config", default="agent_config.json", help="Path to config file")

    # Command: status
    status_parser = subparsers.add_parser("status", help="Check local agent status")
    status_parser.add_argument("--config", default="agent_config.json", help="Path to config file")

    args = parser.parse_args()

    if args.command == "enroll":
        config = AgentConfig(server_url=args.server, config_path=args.config)
        client = AgentClient(config)
        try:
            res = asyncio.run(client.enroll(args.token))
            logger.info("Enrollment BERHASIL!")
            logger.info("Agent ID: %s", res.get("agent_id"))
            logger.info("Server ID: %s", res.get("server_id"))
            logger.info("Workspace ID: %s", res.get("workspace_id"))
            logger.info("Konfigurasi tersimpan di: %s", args.config)
        except Exception as e:
            logger.error("Enrollment GAGAL: %s", e)
            sys.exit(1)

    elif args.command == "run":
        config = AgentConfig.load(args.config)
        if not config.is_enrolled:
            logger.error("Agent belum di-enroll. Jalankan 'devops-agent enroll --server <url> --token <token>' terlebih dahulu.")
            sys.exit(1)

        conn = AgentConnection(config)
        try:
            asyncio.run(conn.start())
        except KeyboardInterrupt:
            logger.info("Agent shutting down gracefully...")
            conn.stop()

    elif args.command == "status":
        config = AgentConfig.load(args.config)
        if config.is_enrolled:
            print(f"Status: ENROLLED")
            print(f"Agent ID: {config.agent_id}")
            print(f"Server ID: {config.server_id}")
            print(f"Workspace ID: {config.workspace_id}")
            print(f"Server URL: {config.server_url}")
        else:
            print("Status: NOT ENROLLED")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
