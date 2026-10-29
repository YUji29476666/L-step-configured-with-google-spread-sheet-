#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import os
import pandas as pd
from datetime import datetime

sys.path.insert(0, '.')

from extract_unmatched import read_cleaned_sheet, extract_unmatched, aggregate_unmatched
from similarity_matcher import SimilarityMatcher

def results_to_csv(results, output_csv_path):
    """
    類似度検索結果を CSV に変換
    ユーザーが確認・編集できる形式
    """
    rows = []

    for result in results:
        school_name = result['school_name']
        count = result['count']
        candidates = result['candidates']

        row = {
            '元の学校名': school_name,
            '出現回数': count,
            '候補1': candidates[0]['school'] if len(candidates) > 0 else '',
            '相似度1': candidates[0]['similarity'] if len(candidates) > 0 else '',
            '候補2': candidates[1]['school'] if len(candidates) > 1 else '',
            '相似度2': candidates[1]['similarity'] if len(candidates) > 1 else '',
            '候補3': candidates[2]['school'] if len(candidates) > 2 else '',
            '相似度3': candidates[2]['similarity'] if len(candidates) > 2 else '',
            'ユーザー判定': '',
            '確認済み': ''
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print(f"[OK] {output_csv_path} に保存しました")
    return df

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Unmatched schools 抽出 + 類似度検索 + CSV 出力')
    parser.add_argument('--spreadsheet-id', required=True, help='Google Spreadsheet ID')
    parser.add_argument('--cleaned-sheet', default='cleaned', help='cleaned シート名')
    parser.add_argument('--output-csv', default='output/unmatched_with_candidates.csv', help='出力 CSV')
    parser.add_argument('--output-json', default='output/suggestion_results.json', help='出力 JSON')
    parser.add_argument('--credentials', default='service-account-key.json', help='認証ファイル')
    parser.add_argument('--threshold', type=float, default=0.7, help='相似度閾値')
    parser.add_argument('--top-k', type=int, default=3, help='返す候補数')
    parser.add_argument('--use-sheets-dict', action='store_true', help='Google Sheets から辞書を読み込む')
    parser.add_argument('--min-count', type=int, default=1, help='最小出現回数')

    args = parser.parse_args()

    print("=" * 70)
    print("Unmatched 学校 抽出 + 候補検索")
    print("=" * 70)

    print("\n[Step 1] Unmatched 学校を抽出中...\n")
    df = read_cleaned_sheet(args.spreadsheet_id, args.cleaned_sheet, args.credentials)
    unmatched_dict = extract_unmatched(df)
    unmatched_list = aggregate_unmatched(unmatched_dict, args.min_count)

    print(f"[OK] Unmatched schools: {len(unmatched_list)} 件\n")

    print("[Step 2] 既存辞書を読み込み中...\n")
    if args.use_sheets_dict:
        print("Google Sheets から辞書を読み込み...")
        matcher = SimilarityMatcher(use_sheets=True, spreadsheet_id=args.spreadsheet_id,
                                    credentials_path=args.credentials)
    else:
        print("CSV から辞書を読み込み...")
        matcher = SimilarityMatcher(use_sheets=False)

    print(f"[OK] 辞書サイズ: {len(matcher.school_dict)} 件\n")

    print("[Step 3] 類似度検索を実行中...\n")
    results = matcher.batch_find_candidates(unmatched_list, threshold=args.threshold, top_k=args.top_k)

    print(f"[OK] 検索完了\n")

    print("[Step 4] CSV に変換中...\n")
    df_csv = results_to_csv(results, args.output_csv)

    print(f"[OK] CSV に保存完了\n")

    output_json_data = {
        'extracted_at': datetime.now().isoformat(),
        'stats': {
            'total_unmatched': len(unmatched_list),
            'dictionary_size': len(matcher.school_dict),
            'threshold': args.threshold,
            'top_k': args.top_k
        },
        'results': results
    }

    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, 'w', encoding='utf-8') as f:
        json.dump(output_json_data, f, ensure_ascii=False, indent=2)

    print(f"[OK] {args.output_json} に保存しました\n")

    print("=" * 70)
    print("処理結果サマリー")
    print("=" * 70)
    print(f"Unmatched schools: {len(unmatched_list)} 件")
    print(f"辞書サイズ: {len(matcher.school_dict)} 件")
    print(f"\n出力ファイル:")
    print(f"  [OK] CSV: {args.output_csv}")
    print(f"  [OK] JSON: {args.output_json}")
    print(f"\n次のステップ:")
    print(f"  1. {args.output_csv} を Excel/Sheets で開く")
    print(f"  2. 「ユーザー判定」列を以下のいずれかで記入:")
    print(f"     - 「統合：学校名」（既存校へマージ）")
    print(f"     - 「新規：学校名」（新規追加）")
    print(f"     - 「要確認」（手動判定保留）")
    print(f"  3. 保存後、辞書更新スクリプトで適用")

    print(f"\n" + "=" * 70)

    print(f"\n=== 検索結果（上位10件） ===\n")
    for i, result in enumerate(results[:10], 1):
        print(f"{i}. {result['school_name']} （{result['count']} 件）")
        for j, cand in enumerate(result['candidates'], 1):
            print(f"   {j}. {cand['school']} (相似度: {cand['similarity']})")
        print()

    if len(results) > 10:
        print(f"... ほか {len(results) - 10} 件")

if __name__ == '__main__':
    main()
