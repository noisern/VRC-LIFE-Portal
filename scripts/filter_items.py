"""
フィルタリングロジック
収集データからR18除外・人気度フィルタ・重複排除を行う。
"""

import logging

logger = logging.getLogger(__name__)


def filter_items(items: list[dict], min_likes: int = 100) -> list[dict]:
    """
    アイテムリストにフィルタリングを適用する。

    フィルタ条件:
    1. R18指定を完全除外
    2. いいね数が min_likes 以上のもののみ
    3. IDベースの重複排除

    Args:
        items: 生データのアイテムリスト
        min_likes: 最小いいね数（デフォルト: 100）

    Returns:
        フィルタ済みアイテムリスト
    """
    original_count = len(items)
    filtered = []
    seen_ids = set()

    r18_removed = 0
    low_likes_removed = 0
    duplicates_removed = 0

    for item in items:
        # R18除外
        if item.get("isR18", False):
            r18_removed += 1
            continue

        # 人気度フィルタ
        if item.get("likes", 0) < min_likes:
            low_likes_removed += 1
            continue

        # 重複排除
        item_id = item.get("id", "")
        if item_id in seen_ids:
            duplicates_removed += 1
            continue
        seen_ids.add(item_id)

        # isR18フラグはフロントに不要なので削除
        clean_item = {k: v for k, v in item.items() if k != "isR18"}
        filtered.append(clean_item)

    logger.info(f"フィルタリング結果:")
    logger.info(f"  入力: {original_count} アイテム")
    logger.info(f"  R18除外: {r18_removed}")
    logger.info(f"  いいね数不足除外 (<{min_likes}): {low_likes_removed}")
    logger.info(f"  重複除外: {duplicates_removed}")
    logger.info(f"  出力: {len(filtered)} アイテム")

    return filtered


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # テスト
    test_items = [
        {"id": "1", "name": "Item A", "likes": 200, "isR18": False},
        {"id": "2", "name": "Item B", "likes": 50, "isR18": False},   # likes不足
        {"id": "3", "name": "Item C", "likes": 300, "isR18": True},   # R18
        {"id": "1", "name": "Item A dup", "likes": 200, "isR18": False},  # 重複
    ]

    result = filter_items(test_items)
    print(f"結果: {len(result)} アイテム")
    for item in result:
        print(f"  - {item['name']}")
