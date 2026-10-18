#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sys
import os

# UTF-8 出力を強制
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from rulebook import load_dictionaries_from_sheets, normalize_school

# Google Sheets から辞書を読み込み
print("Google Sheets から辞書を読み込み中...")
spreadsheet_id = '1XB9s0VI5k0t_SOnNCTBTIsBaWzbb1nnCEQl-wldGyPo'
dicts = load_dictionaries_from_sheets(spreadsheet_id)
school_dict = dicts['school']['Other']
print(f"✓ {len(school_dict)} 件の学校名対応を読み込みました\n")

# テストデータを読み込み
test_file = '../lstep-data-updates/acceptance_tests.csv'
df = pd.read_csv(test_file, encoding='utf-8')

# 学校名のテストケースを抽出
school_tests = df[df['項目'] == '学校名'].reset_index(drop=True)
print(f"学校名テストケース：{len(school_tests)} 件\n")

# 国名→country_code 変換テーブル
country_mapping = {
    '日本': 'JP',
    'アメリカ': 'US',
    'カナダ': 'CA',
    'オーストラリア': 'AU',
    'マレーシア': 'MY',
    'シンガポール': 'SG',
    'タイ': 'TH',
    'インド': 'IN',
    '中国': 'CN',
    '韓国': 'KR',
    'イギリス': 'GB',
    'フランス': 'FR',
    'ドイツ': 'DE',
    'オランダ': 'NL',
    'スイス': 'CH',
    'ニュージーランド': 'NZ',
    '南アフリカ': 'ZA',
    '台湾': 'TW',
    'スウェーデン': 'SE',
    'ノルウェー': 'NO',
    'フィリピン': 'PH',
}

# テスト実行
matches = 0
mismatches = []

for idx, row in school_tests.iterrows():
    input_value = row['入力']
    expected = row['期待する出力']
    country_name = row.get('国(学校名のみ)', None) if '国(学校名のみ)' in row.index else None

    # 国名を country_code に変換
    country_code = country_mapping.get(country_name, None) if country_name else None

    # normalize_school を実行（国別対応）
    result = normalize_school(input_value, school_dict, country=country_code)
    actual = result['value']

    # 一致判定
    is_match = (actual == expected)

    if is_match:
        matches += 1
        status = "✓"
        country_str = f" ({country_code})" if country_code else ""
        print(f"{status} [{idx+1:2d}] {input_value:30s} → {actual:40s}{country_str}")
    else:
        mismatches.append((idx+1, input_value, actual, expected, country_code))
        status = "✗"
        country_str = f" ({country_code})" if country_code else ""
        print(f"{status} [{idx+1:2d}] {input_value:30s} → {actual:40s} (期待: {expected}){country_str}")

# 結果表示
print(f"\n{'='*100}")
print(f"一致数：{matches}/{len(school_tests)} ({100*matches/len(school_tests):.1f}%)")
print(f"不一致数：{len(mismatches)}/{len(school_tests)} ({100*len(mismatches)/len(school_tests):.1f}%)")
print(f"{'='*100}")

if mismatches:
    print("\n❌ 不一致の詳細：")
    for mismatch_data in mismatches:
        idx = mismatch_data[0]
        input_val = mismatch_data[1]
        actual = mismatch_data[2]
        expected = mismatch_data[3]
        country = mismatch_data[4] if len(mismatch_data) > 4 else None
        country_str = f" ({country})" if country else ""
        print(f"  [{idx:2d}] {input_val:30s} → {actual:40s} (期待: {expected}){country_str}")
