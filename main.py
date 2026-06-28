#!/usr/bin/env python3
import argparse
import sys
from modules.cloner import clone_page
from modules.harvester import start_listener
from modules.mailer import send_campaign
from modules.tracker import view_logs, export_logs
from modules.utils import banner, menu, color


def interactive_mode():
    banner()
    while True:
        menu()
        choice = input(color("\n[>] Select option: ", "cyan")).strip()

        if choice == "1":
            url = input(color("[>] Target URL to clone: ", "cyan")).strip()
            name = input(color("[>] Campaign name: ", "cyan")).strip()
            clone_page(url, name)

        elif choice == "2":
            name = input(color("[>] Campaign name: ", "cyan")).strip()
            port = input(color("[>] Port (default 8080): ", "cyan")).strip() or "8080"
            start_listener(name, int(port))

        elif choice == "3":
            name = input(color("[>] Campaign name: ", "cyan")).strip()
            targets = input(color("[>] Targets file path: ", "cyan")).strip()
            template = input(color("[>] Email template name: ", "cyan")).strip()
            send_campaign(name, targets, template)

        elif choice == "4":
            name = input(color("[>] Campaign name (leave blank for all): ", "cyan")).strip()
            view_logs(name or None)

        elif choice == "5":
            name = input(color("[>] Campaign name: ", "cyan")).strip()
            export_logs(name)

        elif choice == "0":
            print(color("\n[!] Exiting. Stay ethical.\n", "yellow"))
            sys.exit(0)

        else:
            print(color("[-] Invalid option.", "red"))


def argparse_mode():
    parser = argparse.ArgumentParser(
        description="Phishing Simulation Framework - Authorized use only"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Clone
    clone_p = subparsers.add_parser("clone", help="Clone a target login page")
    clone_p.add_argument("--url", required=True, help="URL to clone")
    clone_p.add_argument("--campaign", required=True, help="Campaign name")

    # Listen
    listen_p = subparsers.add_parser("listen", help="Start harvester listener")
    listen_p.add_argument("--campaign", required=True, help="Campaign name")
    listen_p.add_argument("--port", type=int, default=8080, help="Port to listen on")

    # Send
    send_p = subparsers.add_parser("send", help="Send phishing emails")
    send_p.add_argument("--campaign", required=True, help="Campaign name")
    send_p.add_argument("--targets", required=True, help="Path to targets file")
    send_p.add_argument("--template", required=True, help="Email template name")

    # Logs
    logs_p = subparsers.add_parser("logs", help="View captured credentials and events")
    logs_p.add_argument("--campaign", help="Campaign name (optional)")

    # Export
    export_p = subparsers.add_parser("export", help="Export logs to CSV")
    export_p.add_argument("--campaign", required=True, help="Campaign name")

    args = parser.parse_args()

    if args.command == "clone":
        clone_page(args.url, args.campaign)
    elif args.command == "listen":
        start_listener(args.campaign, args.port)
    elif args.command == "send":
        send_campaign(args.campaign, args.targets, args.template)
    elif args.command == "logs":
        view_logs(args.campaign)
    elif args.command == "export":
        export_logs(args.campaign)
    else:
        parser.print_help()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        argparse_mode()
    else:
        interactive_mode()
