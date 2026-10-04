# Inventory API

The API stores items in an in-memory array for this development stage. Data is
reset whenever the Flask process restarts. The item representation is:

```json
{
  "id": 1,
  "name": "Oat milk",
  "quantity": 12,
  "price": 3.5,
  "barcode": "1234567890123"
}
```

`name`, `quantity`, and `price` are required when creating an item. `barcode`
is optional. Quantity must be a non-negative integer and price a non-negative
number. `PATCH` accepts one or more of those fields.

| Route | Inputs | Response and data change | Planned CLI trigger |
| --- | --- | --- | --- |
| `GET /inventory` | None | `200` with an array of all items; no change. | User chooses list/view all. |
| `GET /inventory/<id>` | Positive integer item ID in the path. | `200` with the item, or `404`; no change. | User chooses view one and supplies its ID. |
| `POST /inventory` | JSON item with required `name`, `quantity`, `price`; optional `barcode`. | `201` with the new item and `Location` header; adds an item with a generated ID. Invalid data returns `400`. | User chooses add and enters item details. |
| `PATCH /inventory/<id>` | Item ID and JSON containing at least one supported field. | `200` with the updated item, or `404`; changes only supplied fields. Invalid data returns `400`. | User chooses edit, supplies an ID, then fields to change. |
| `DELETE /inventory/<id>` | Positive integer item ID in the path. | `204` on success, or `404`; removes the item from the array. | User chooses delete and confirms an item ID. |
| `GET /products/barcode/<barcode>` | Numeric product barcode in the path. | `200` with normalized product details, `404` if absent, or `502` if the external service fails; does not change inventory. | User chooses product lookup by barcode before adding inventory. |
| `GET /products/search?name=<name>` | Non-empty product name query. | `200` with matching products and count, or `502` if the external service fails; does not change inventory. | User chooses product lookup by name before adding inventory. |

Run the development server with `python app.py`. Run the API tests with
`python -m pytest -q`.

Product details come from the Open Food Facts v3 barcode API and its
Search-a-licious name-search API. The lookup routes are read-only; use the
returned details to populate a separate `POST /inventory` request. Search
requests are subject to Open Food Facts' tighter search rate limit.

The CLI in `CLI/` invokes these routes over HTTP. See the project README for
command examples; start the Flask server before issuing CLI commands.