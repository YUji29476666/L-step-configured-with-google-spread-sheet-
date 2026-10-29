#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import difflib
import sys
sys.path.insert(0, '.')

from rulebook import load_dictionaries_from_sheets, load_dictionaries

class SimilarityMatcher:
    def __init__(self, school_dict=None, use_sheets=False, spreadsheet_id=None, credentials_path=None):
        if use_sheets and spreadsheet_id:
            try:
                dicts = load_dictionaries_from_sheets(spreadsheet_id, credentials_path)
                self.school_dict = dicts['school']['Other']
            except:
                print("[WARN] Google Sheets 読み込み失敗、CSV に切り替えます")
                dicts = load_dictionaries(use_sheets=False)
                self.school_dict = dicts['school']['Other']
        elif school_dict:
            self.school_dict = school_dict
        else:
            dicts = load_dictionaries(use_sheets=False)
            self.school_dict = dicts['school']['Other']

    def find_candidates(self, unmatched_school, country_code='', threshold=0.7, top_k=3):
        """
        unmatched_school に類似した既存学校の候補を返す

        Args:
            unmatched_school: 未一致の学校名（日本語など）
            country_code: 国コード（オプション）
            threshold: 相似度閾値（0-1）
            top_k: 返す候補数

        Returns:
            [
                {'school': '統一名', 'similarity': 0.95},
                {'school': '統一名2', 'similarity': 0.88},
                ...
            ]
        """
        candidates = []

        for (variant, variant_country), unified in self.school_dict.items():
            if variant == unmatched_school:
                continue

            ratio = difflib.SequenceMatcher(None, unmatched_school, variant).ratio()

            if ratio >= threshold:
                candidates.append({
                    'school': unified,
                    'variant': variant,
                    'similarity': round(ratio, 3),
                    'country_code': variant_country
                })

        candidates.sort(key=lambda x: x['similarity'], reverse=True)
        return candidates[:top_k]

    def batch_find_candidates(self, unmatched_list, threshold=0.7, top_k=3):
        """
        複数の unmatched 学校に対して候補を一括検索

        Args:
            unmatched_list: [{'school_name': 'xxx', 'count': 5}, ...]

        Returns:
            [
                {'school_name': 'xxx', 'candidates': [...], 'count': 5},
                ...
            ]
        """
        results = []

        for item in unmatched_list:
            school_name = item.get('school_name', '')
            count = item.get('count', 1)

            candidates = self.find_candidates(school_name, threshold=threshold, top_k=top_k)

            results.append({
                'school_name': school_name,
                'count': count,
                'candidates': candidates
            })

        return results

def main():
    import json
    import argparse

    parser = argparse.ArgumentParser(description='Unmatched schools に対して類似度検索')
    parser.add_argument('--input', required=True, help='入力 JSON（unmatched_schools.json）')
    parser.add_argument('--output', default='output/similarity_candidates.json', help='出力ファイル')
    parser.add_argument('--spreadsheet-id', help='Google Spreadsheet ID（使用する場合）')
    parser.add_argument('--credentials', default='service-account-key.json', help='認証ファイル')
    parser.add_argument('--threshold', type=float, default=0.7, help='相似度閾値（0-1）')
    parser.add_argument('--top-k', type=int, default=3, help='返す候補数')

    args = parser.parse_args()

    print("=" * 60)
    print("類似度検索（difflib）")
    print("=" * 60)

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    unmatched_list = data.get('schools', [])
    print(f"[OK] {len(unmatched_list)} 件の unmatched schools を読み込みました\n")

    if args.spreadsheet_id:
        print("Google Sheets から辞書を読み込み中...")
        matcher = SimilarityMatcher(use_sheets=True, spreadsheet_id=args.spreadsheet_id,
                                    credentials_path=args.credentials)
    else:
        print("CSV から辞書を読み込み中...")
        matcher = SimilarityMatcher(use_sheets=False)

    print(f"辞書サイズ: {len(matcher.school_dict)} 件\n")

    print("類似度検索を実行中...")
    results = matcher.batch_find_candidates(unmatched_list, threshold=args.threshold, top_k=args.top_k)

    output_data = {
        'extracted_at': data.get('extracted_at'),
        'total': len(results),
        'threshold': args.threshold,
        'top_k': args.top_k,
        'results': results
    }

    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] {args.output} に保存しました")

    print(f"\n=== 検索結果（サンプル） ===")
    for result in results[:5]:
        print(f"\n{result['school_name']} ({result['count']} 件)")
        for i, cand in enumerate(result['candidates'], 1):
            print(f"  {i}. {cand['school']} (相似度: {cand['similarity']})")

if __name__ == '__main__':
    main()
