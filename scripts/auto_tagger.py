"""
ルールベース自動タグ付け＆カテゴライズ
商品名と説明文からキーワードマッチングでタグを付与する。
OpenAI APIキー不要。
"""

import re
import logging

logger = logging.getLogger(__name__)

# === タグ定義 ===

# 対象カテゴリ（メンズ/レディース/キッズ）
CATEGORY_RULES = {
    "mens": {
        "keywords": [
            r"メンズ", r"男性", r"男の子", r"ボーイ", r"boy",
            r"男性向け", r"男子", r"紳士",
        ],
        "avatars": [
            r"リーファ", r"ゼン", r"ボーイ系", r"男性アバター",
        ],
    },
    "womens": {
        "keywords": [
            r"レディース", r"女性", r"女の子", r"ガール", r"girl",
            r"女性向け", r"女子", r"Lady",
        ],
        "avatars": [
            r"舞夜", r"まいや", r"桔梗", r"ききょう", r"セレスティア",
            r"マヌカ", r"リメス", r"イメリス", r"薄荷", r"はっか",
            r"ルシナ", r"ヴェール", r"サフィー", r"あまなつ",
            r"京狐", r"萌", r"シフォン", r"チセ",
        ],
    },
    "kids": {
        "keywords": [
            r"キッズ", r"子供", r"こども", r"スモール",
            r"ミニ", r"ちび", r"小さい",
            r"kids", r"small",
        ],
        "avatars": [
            r"マヌカ", r"ルシナ", r"ラスク", r"ぽこ",
            r"しなの", r"ここあ", r"フィー",
        ],
    },
}

# テイスト分類
TASTE_RULES = {
    "cyber": [
        r"サイバー", r"パンク", r"ネオン", r"グロー", r"光る",
        r"LED", r"ホログラム", r"メカ", r"ロボ",
        r"cyber", r"punk", r"neon", r"glow", r"mecha",
        r"SF", r"近未来", r"電脳",
    ],
    "street": [
        r"ストリート", r"パーカー", r"スニーカー", r"デニム",
        r"ヒップホップ", r"グラフィティ", r"スケート",
        r"street", r"hoodie", r"sneaker",
        r"カジュアル(?!.*和)",
    ],
    "wa-modern": [
        r"和風", r"着物", r"和服", r"和モダン", r"和装",
        r"袴", r"浴衣", r"振袖", r"羽織",
        r"japanese", r"kimono", r"wa-",
    ],
    "ryousangata": [
        r"量産型", r"量産", r"りょうさん",
        r"ガーリー", r"リボン", r"フリル",
        r"パール", r"ピンク系",
    ],
    "jirai": [
        r"地雷", r"じらい", r"病み",
        r"黒×ピンク", r"ダーク(?!.*ファンタジー)",
        r"メンヘラ",
    ],
    "fantasy": [
        r"ファンタジー", r"騎士", r"魔法", r"ドラゴン",
        r"エルフ", r"魔女", r"剣", r"鎧",
        r"fantasy", r"knight", r"magic", r"RPG",
        r"中世", r"異世界",
    ],
    "casual": [
        r"カジュアル", r"デイリー", r"普段着",
        r"Tシャツ", r"ジーンズ", r"シンプル",
        r"casual", r"daily",
    ],
    "gothic": [
        r"ゴシック", r"ゴスロリ", r"ロリータ",
        r"ヴィクトリアン", r"ダークエレガント",
        r"gothic", r"lolita", r"goth",
    ],
    "pop": [
        r"ポップ", r"カラフル", r"原宿",
        r"ゆめかわ", r"夢可愛い", r"パステル",
        r"デコラ", r"Kawaii",
        r"pop", r"colorful",
    ],
}

# 種別分類
TYPE_RULES = {
    "avatar": [
        r"アバター", r"avatar", r"キャラクター", r"3Dモデル",
        r"character", r"ボディ", r"素体",
    ],
    "costume": [
        r"衣装", r"服", r"ドレス", r"ジャケット", r"パンツ",
        r"スカート", r"パーカー", r"コート", r"ワンピース",
        r"セーター", r"シャツ", r"ブラウス", r"水着",
        r"costume", r"outfit", r"clothing", r"wear",
        r"デニム", r"ニット", r"カーディガン",
    ],
    "accessory": [
        r"アクセサリー", r"ヘッドドレス", r"チョーカー", r"イヤリング",
        r"ピアス", r"ネックレス", r"ブレスレット", r"リング",
        r"帽子", r"メガネ", r"サングラス", r"バッグ",
        r"靴", r"ブーツ", r"スニーカー", r"ハイヒール",
        r"accessory", r"hair", r"hat", r"glasses",
        r"リボン", r"翼", r"ウィング", r"角",
    ],
    "texture": [
        r"テクスチャ", r"マテリアル", r"素材", r"改変素材",
        r"texture", r"material", r"shader",
        r"UV", r"PSD",
    ],
    "tool": [
        r"ツール", r"ギミック", r"システム", r"スクリプト",
        r"tool", r"system", r"script", r"sdk", r"prefab",
        r"導入", r"設定", r"OSC", r"ワールド固定",
    ],
    "pose": [
        r"ポーズ", r"アニメーション", r"モーション", r"ダンス",
        r"pose", r"animation", r"motion", r"dance",
        r"afk", r"emote", r"エモート",
    ],
}


def _match_rules(text: str, rules: dict[str, list[str]]) -> list[str]:
    """テキストにキーワードがマッチするタグをリストで返す。"""
    matched = []
    for tag, patterns in rules.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matched.append(tag)
                break
    return matched


def tag_item(item: dict) -> dict:
    """
    1つのアイテムにタグを付与する。

    付与されるタグ:
    - category: mens / womens / kids
    - taste: [cyber, street, wa-modern, ...]
    - type: avatar / costume / accessory / texture
    """
    # 検索対象テキスト
    search_text = f"{item.get('name', '')} {item.get('description', '')}"

    # カテゴリ判定
    category = "womens"  # デフォルト（VRChatは女性アバターが多い）
    for cat, rules in CATEGORY_RULES.items():
        all_patterns = rules["keywords"] + rules["avatars"]
        for pattern in all_patterns:
            if re.search(pattern, search_text, re.IGNORECASE):
                category = cat
                break

    # テイスト判定
    tastes = _match_rules(search_text, TASTE_RULES)
    if not tastes:
        tastes = ["casual"]  # デフォルト

    # 種別判定
    types = _match_rules(search_text, TYPE_RULES)
    item_type = types[0] if types else "costume"  # デフォルト

    # タグ付与
    item["category"] = category
    item["taste"] = tastes
    item["type"] = item_type

    return item


def tag_all_items(items: list[dict]) -> list[dict]:
    """全アイテムにタグを付与する。"""
    tagged = []
    for item in items:
        tagged_item = tag_item(item)
        tagged.append(tagged_item)
        logger.debug(
            f"  {tagged_item['name'][:30]}... → "
            f"cat:{tagged_item['category']} "
            f"taste:{tagged_item['taste']} "
            f"type:{tagged_item['type']}"
        )

    # 統計
    cat_stats = {}
    taste_stats = {}
    type_stats = {}
    for item in tagged:
        cat_stats[item["category"]] = cat_stats.get(item["category"], 0) + 1
        for t in item["taste"]:
            taste_stats[t] = taste_stats.get(t, 0) + 1
        type_stats[item["type"]] = type_stats.get(item["type"], 0) + 1

    logger.info(f"タグ付け完了: {len(tagged)} アイテム")
    logger.info(f"  カテゴリ: {cat_stats}")
    logger.info(f"  テイスト: {taste_stats}")
    logger.info(f"  種別: {type_stats}")

    return tagged


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

    test_items = [
        {"name": "【VRChat向け】サイバーパンクジャケット", "description": "舞夜対応のサイバーパンク風ジャケット"},
        {"name": "和風モダンドレス for 舞夜", "description": "着物風の和モダンドレスです"},
        {"name": "キッズサイズ ふわもこパジャマ", "description": "マヌカ対応のパジャマ"},
        {"name": "量産型リボンヘッドドレス", "description": "ガーリーなリボン付きヘッドアクセサリー"},
        {"name": "VRChatアバターテクスチャ改変素材集", "description": "テクスチャ改変用PSD素材"},
    ]

    for item in tag_all_items(test_items):
        print(f"{item['name']}: cat={item['category']}, taste={item['taste']}, type={item['type']}")
