"""
BOOTH→VRC-LIFE Portal パイプライン統合スクリプト

1. BOOTHからVRChat関連アイテムを収集
2. R18/人気度フィルタリング
3. ルールベースAIタグ付け
4. items.json に出力

Usage:
    python scripts/run_pipeline.py              # 通常実行
    python scripts/run_pipeline.py --dry-run    # ドライラン（HTTP通信なし）
"""

import json
import sys
import os
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from booth_scraper import scrape_booth
from filter_items import filter_items
from auto_tagger import tag_all_items

logger = logging.getLogger(__name__)


def run_pipeline(dry_run: bool = False, output_path: str = None) -> None:
    """パイプラインを実行し items.json を生成する。"""

    logger.info("=" * 60)
    logger.info("VRC-LIFE Portal Fashion パイプライン")
    logger.info(f"実行日時: {datetime.now(timezone.utc).isoformat()}")
    logger.info(f"モード: {'ドライラン' if dry_run else '本番'}")
    logger.info("=" * 60)

    # 出力パスの決定
    if output_path is None:
        project_root = Path(__file__).parent.parent
        output_path = project_root / "docs" / "data" / "items.json"
    else:
        output_path = Path(output_path)

    # Step 1: スクレイピング
    logger.info("\n[Step 1/3] BOOTHからアイテム収集...")
    raw_items = scrape_booth(dry_run=dry_run)
    logger.info(f"  → {len(raw_items)} アイテム収集")

    # Step 2: フィルタリング
    logger.info("\n[Step 2/3] フィルタリング...")
    filtered_items = filter_items(raw_items, min_likes=0)
    logger.info(f"  → {len(filtered_items)} アイテム残存")

    # Step 3: タグ付け
    logger.info("\n[Step 3/3] 自動タグ付け...")
    tagged_items = tag_all_items(filtered_items)
    logger.info(f"  → {len(tagged_items)} アイテムにタグ付与")

    # いいね数でソート（降順）
    tagged_items.sort(key=lambda x: x.get("likes", 0), reverse=True)

    # 出力データ構築
    output_data = {
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
        "totalItems": len(tagged_items),
        "items": tagged_items,
    }

    # 空の結果だった場合は出力しない（既存データを保護）
    if not tagged_items:
        logger.error("❌ エラー: 収集されたアイテムが0件のため、items.json の更新をスキップします。")
        # GitHub Actionsでエラーとして扱いたい場合は exit(1) する
        sys.exit(1)

    # JSON出力
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    logger.info(f"\n{'=' * 60}")
    logger.info(f"✅ 完了: {len(tagged_items)} アイテムを {output_path} に出力")
    logger.info(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(description="BOOTH → VRC-LIFE Portal パイプライン")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ドライランモード（HTTP通信なし、サンプルデータ使用）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="出力ファイルパス（デフォルト: data/items.json）",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    run_pipeline(dry_run=args.dry_run, output_path=args.output)


if __name__ == "__main__":
    main()
