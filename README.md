# Flask Inventory Management System

## CLI Commands

Start the Flask API in one terminal:

```sh
python app.py
```

In another terminal, run CLI commands from the project root with `python3 -m CLI`:

```sh
python3 -m CLI help
python3 -m CLI --help
python3 -m CLI add --help
python3 -m CLI list
python3 -m CLI get 1
python3 -m CLI add "Oat milk" 12 3.50 --barcode 1234567890123
python3 -m CLI update 1 --quantity 8 --price 3.25
python3 -m CLI delete 1
python3 -m CLI barcode 3017624010701
python3 -m CLI search "Oat milk"
```

The API defaults to `http://127.0.0.1:5000`. Override it with
`--base-url http://host:port` before the command or set `INVENTORY_API_URL`.
Product lookup commands return Open Food Facts details; they do not add the
product to inventory automatically. Use `add` to create the inventory record.

Run tests with `python -m unittest discover -s Testing`.
