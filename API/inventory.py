class InventoryStore:
    def __init__(self):
        self._items = []
        self._next_id = 1

    def list_items(self):
        return [item.copy() for item in self._items]

    def get_item(self, item_id):
        item = next((item for item in self._items if item["id"] == item_id), None)
        return item.copy() if item is not None else None

    def add_item(self, data):
        item = {"id": self._next_id, **data}
        self._items.append(item)
        self._next_id += 1
        return item.copy()

    def update_item(self, item_id, data):
        item = next((item for item in self._items if item["id"] == item_id), None)
        if item is None:
            return None

        item.update(data)
        return item.copy()

    def delete_item(self, item_id):
        item = next((item for item in self._items if item["id"] == item_id), None)
        if item is None:
            return False

        self._items.remove(item)
        return True