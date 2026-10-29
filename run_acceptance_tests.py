#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sys
import os
import importlib

# UTF-8 出力を強制
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from rulebook import load_dictionaries_from_sheets, normalize_school, normalize_major, normalize_country

# Google Sheets から辞書を読み込み
print("=" * 100)
print("📋 受け入れテスト実行開始")
print("=" * 100)
print("\n🔄 Google Sheets から辞書を読み込み中...\n")

spreadsheet_id = '1XB9s0VI5k0t_SOnNCTBTIsBaWzbb1nnCEQl-wldGyPo'
dicts = load_dictionaries_from_sheets(spreadsheet_id)
school_dict = dicts['school']['Other']
major_dict = dicts['major']
country_dict = dicts['country']

print(f"✓ 学校名辞書：{len(school_dict)} 件")
print(f"✓ 専攻辞書：{len(major_dict)} 件")
print(f"✓ 国辞書：{len(country_dict)} 件")

# テストデータを読み込み
test_file = '../lstep-data-updates/acceptance_tests.csv'
df = pd.read_csv(test_file, encoding='utf-8', keep_default_na=False, na_filter=False)

# 項目ごとのテストを分離
school_tests = df[df['項目'] == '学校名'].reset_index(drop=True)
major_tests = df[df['項目'] == '専攻'].reset_index(drop=True)
minor_tests = df[df['項目'] == '副専攻'].reset_index(drop=True)
country_tests = df[df['項目'] == '国'].reset_index(drop=True)

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

# テスト実行結果
total_tests = 0
passed_tests = 0
failed_tests_list = []

print("\n" + "=" * 100)
print("【学校名テスト】")
print("=" * 100)

for idx, row in school_tests.iterrows():
    total_tests += 1
    input_value = row['入力']
    expected_output = row['期待する出力']
    expected_status = ''
    if '期待する status' in df.columns:
        status_val = row.get('期待する status', '')
        if pd.notna(status_val) and status_val != '':
            expected_status = str(status_val).strip()
    country_name = ''
    if '国(学校名のみ)' in df.columns:
        country_val = row.get('国(学校名のみ)', '')
        if pd.notna(country_val):
            country_name = str(country_val).strip()

    country_code = country_mapping.get(country_name, None) if country_name else None

    result = normalize_school(input_value, school_dict, country=country_code)
    actual_output = result['value']
    actual_status = result['status']

    output_match = (actual_output == expected_output)
    status_match = (expected_status == '' or actual_status == expected_status)
    is_pass = output_match and status_match

    if is_pass:
        passed_tests += 1
        print(f"✓ [{idx+2:2d}] {input_value:30s} → {actual_output:45s} ({actual_status})")
    else:
        failed_tests_list.append({
            'line': idx + 2,
            'item': '学校名',
            'input': input_value,
            'expected_output': expected_output,
            'actual_output': actual_output,
            'expected_status': expected_status,
            'actual_status': actual_status,
            'output_match': output_match,
            'status_match': status_match
        })
        details = []
        if not output_match:
            details.append(f"出力不一致（期待: {expected_output}）")
        if not status_match:
            details.append(f"status不一致（期待: {expected_status}）")
        print(f"✗ [{idx+2:2d}] {input_value:30s} → {actual_output:45s} ({actual_status}) — {', '.join(details)}")

print(f"\n学校名テスト：{passed_tests - len([x for x in failed_tests_list if x['item'] != '学校名'])}/{len(school_tests)}")

print("\n" + "=" * 100)
print("【専攻テスト】")
print("=" * 100)

major_passed = 0
for idx, row in major_tests.iterrows():
    total_tests += 1
    input_value = row['入力']
    expected_output = row['期待する出力']
    expected_status = ''
    if '期待する status' in df.columns:
        status_val = row.get('期待する status', '')
        if pd.notna(status_val) and status_val != '':
            expected_status = str(status_val).strip()

    result = normalize_major(input_value, major_dict)
    actual_output = result['value']
    actual_status = result['status']

    # Handle NaN comparison
    if pd.isna(expected_output):
        expected_output = pd.NA
    if pd.isna(actual_output):
        actual_output = pd.NA

    if pd.isna(expected_output) and pd.isna(actual_output):
        output_match = True
    else:
        output_match = (str(actual_output) == str(expected_output))

    status_match = (expected_status == '' or actual_status == expected_status)
    is_pass = output_match and status_match

    if is_pass:
        passed_tests += 1
        major_passed += 1
        output_str = 'NaN' if pd.isna(actual_output) else actual_output
        print(f"✓ [{idx+2:2d}] {input_value:25s} → {output_str:30s} ({actual_status})")
    else:
        failed_tests_list.append({
            'line': idx + 2,
            'item': '専攻',
            'input': input_value,
            'expected_output': expected_output,
            'actual_output': actual_output,
            'expected_status': expected_status,
            'actual_status': actual_status,
            'output_match': output_match,
            'status_match': status_match
        })
        details = []
        if not output_match:
            details.append(f"出力不一致（期待: {expected_output}）")
        if not status_match:
            details.append(f"status不一致（期待: {expected_status}）")
        output_str = 'NaN' if pd.isna(actual_output) else actual_output
        print(f"✗ [{idx+2:2d}] {input_value:25s} → {output_str:30s} ({actual_status}) — {', '.join(details)}")

print(f"\n専攻テスト：{major_passed}/{len(major_tests)}")

print("\n" + "=" * 100)
print("【副専攻テスト】")
print("=" * 100)

minor_passed = 0
for idx, row in minor_tests.iterrows():
    total_tests += 1
    input_value = row['入力']
    expected_output = row['期待する出力']
    expected_status = ''
    if '期待する status' in df.columns:
        status_val = row.get('期待する status', '')
        if pd.notna(status_val) and status_val != '':
            expected_status = str(status_val).strip()

    result = normalize_major(input_value, major_dict)
    actual_output = result['value']
    actual_status = result['status']

    # Handle NaN comparison
    if pd.isna(expected_output):
        expected_output = pd.NA
    if pd.isna(actual_output):
        actual_output = pd.NA

    if pd.isna(expected_output) and pd.isna(actual_output):
        output_match = True
    else:
        output_match = (str(actual_output) == str(expected_output))

    status_match = (expected_status == '' or actual_status == expected_status)
    is_pass = output_match and status_match

    if is_pass:
        passed_tests += 1
        minor_passed += 1
        output_str = 'NaN' if pd.isna(actual_output) else actual_output
        print(f"✓ [{idx+2:2d}] {input_value:25s} → {output_str:30s} ({actual_status})")
    else:
        failed_tests_list.append({
            'line': idx + 2,
            'item': '副専攻',
            'input': input_value,
            'expected_output': expected_output,
            'actual_output': actual_output,
            'expected_status': expected_status,
            'actual_status': actual_status,
            'output_match': output_match,
            'status_match': status_match
        })
        details = []
        if not output_match:
            details.append(f"出力不一致（期待: {expected_output}）")
        if not status_match:
            details.append(f"status不一致（期待: {expected_status}）")
        output_str = 'NaN' if pd.isna(actual_output) else actual_output
        print(f"✗ [{idx+2:2d}] {input_value:25s} → {output_str:30s} ({actual_status}) — {', '.join(details)}")

print(f"\n副専攻テスト：{minor_passed}/{len(minor_tests)}")

print("\n" + "=" * 100)
print("【国テスト】")
print("=" * 100)

country_passed = 0
for idx, row in country_tests.iterrows():
    total_tests += 1
    input_value = row['入力']
    expected_output = row['期待する出力']
    expected_status = ''
    if '期待する status' in df.columns:
        status_val = row.get('期待する status', '')
        if pd.notna(status_val) and status_val != '':
            expected_status = str(status_val).strip()

    # Pass the input value directly to normalize_country (it handles "その他 + XX" internally)
    result = normalize_country(input_value, country_dict)
    # cleaned 出力は country_name を使う
    actual_output = result.get('country_name', result['value'])
    actual_status = result['status']

    output_match = (actual_output == expected_output)
    status_match = (expected_status == '' or actual_status == expected_status)
    is_pass = output_match and status_match

    if is_pass:
        passed_tests += 1
        country_passed += 1
        print(f"✓ [{idx+2:2d}] {input_value:35s} → {actual_output:25s} ({actual_status})")
    else:
        failed_tests_list.append({
            'line': idx + 2,
            'item': '国',
            'input': input_value,
            'expected_output': expected_output,
            'actual_output': actual_output,
            'expected_status': expected_status,
            'actual_status': actual_status,
            'output_match': output_match,
            'status_match': status_match
        })
        details = []
        if not output_match:
            details.append(f"出力不一致（期待: {expected_output}）")
        if not status_match:
            details.append(f"status不一致（期待: {expected_status}）")
        print(f"✗ [{idx+2:2d}] {input_value:35s} → {actual_output:25s} ({actual_status}) — {', '.join(details)}")

print(f"\n国テスト：{country_passed}/{len(country_tests)}")

# 最終結果
print("\n" + "=" * 100)
print("📊 最終結果")
print("=" * 100)
success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
print(f"\n総合成功率：{passed_tests}/{total_tests} ({success_rate:.1f}%)")

if failed_tests_list:
    print(f"\n❌ 失敗テスト：{len(failed_tests_list)}件")
    print("\n失敗詳細：")
    for fail in failed_tests_list:
        print(f"\n  [{fail['line']}] {fail['item']} — {fail['input']}")
        if not fail['output_match']:
            print(f"      出力不一致：{fail['actual_output']} （期待: {fail['expected_output']}）")
        if not fail['status_match']:
            print(f"      status不一致：{fail['actual_status']} （期待: {fail['expected_status']}）")
else:
    print("\n✅ すべてのテストが成功しました！")

print("\n" + "=" * 100)
