import argparse
import json
import os
import sys

from CLI.api_client import ApiClientError, InventoryApiClient


def build_parser():
    parser = argparse.ArgumentParser(
        description="Manage inventory through the Flask REST API."
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("INVENTORY_API_URL", "http://127.0.0.1:5000"),
        help="API base URL (default: %(default)s)",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("list", help="list all inventory items")

    get_command = commands.add_parser("get", help="view one inventory item")
    get_command.add_argument("item_id", type=int)

    add_command = commands.add_parser("add", help="add an inventory item")
    add_command.add_argument("name")
    add_command.add_argument("quantity", type=int)
    add_command.add_argument("price", type=float)
    add_command.add_argument("--barcode")

    update_command = commands.add_parser("update", help="update an inventory item")
    update_command.add_argument("item_id", type=int)
    update_command.add_argument("--name")
    update_command.add_argument("--quantity", type=int)
    update_command.add_argument("--price", type=float)
    update_command.add_argument("--barcode")

    delete_command = commands.add_parser("delete", help="delete an inventory item")
    delete_command.add_argument("item_id", type=int)

    barcode_command = commands.add_parser(
        "barcode", help="look up a product by barcode"
    )
    barcode_command.add_argument("barcode")

    search_command = commands.add_parser(
        "search", help="search Open Food Facts by product name"
    )
    search_command.add_argument("name")

    commands.add_parser("help", help="show help for CLI commands")

    return parser


def main(argv=None, client=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "help":
        parser.print_help()
        return 0

    api = client if client is not None else InventoryApiClient(args.base_url)

    try:
        if args.command == "list":
            result = api.list_inventory()
        elif args.command == "get":
            result = api.get_inventory_item(args.item_id)
        elif args.command == "add":
            item = {
                "name": args.name,
                "quantity": args.quantity,
                "price": args.price,
            }
            if args.barcode is not None:
                item["barcode"] = args.barcode
            result = api.add_inventory_item(item)
        elif args.command == "update":
            changes = {
                key: value
                for key, value in {
                    "name": args.name,
                    "quantity": args.quantity,
                    "price": args.price,
                    "barcode": args.barcode,
                }.items()
                if value is not None
            }
            if not changes:
                parser.error("update requires at least one field option")
            result = api.update_inventory_item(args.item_id, changes)
        elif args.command == "delete":
            api.delete_inventory_item(args.item_id)
            print(f"Deleted inventory item {args.item_id}.")
            return 0
        elif args.command == "barcode":
            result = api.lookup_barcode(args.barcode)
        else:
            result = api.search_products(args.name)
    except ApiClientError as error:
        print(str(error), file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0