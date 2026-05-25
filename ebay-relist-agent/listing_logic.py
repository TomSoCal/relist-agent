AUCTION_TYPES = {"Chinese", "Dutch"}


def partition_listings(items: list[dict]) -> tuple[list[dict], list[dict]]:
    zero_qty = []
    eligible = []
    for item in items:
        if item["listing_type"] in AUCTION_TYPES:
            continue
        if item["quantity"] == 0:
            zero_qty.append(item)
        else:
            eligible.append(item)
    return zero_qty, eligible


def select_oldest(items: list[dict], n: int = 10) -> list[dict]:
    return sorted(items, key=lambda i: i["start_time"])[:n]
