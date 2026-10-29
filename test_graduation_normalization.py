#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unicodedata

def normalize_graduation_month(month_str):
    """
    卒業月を正規化（「月」を削除、全角→半角）

    Args:
        month_str: 「3月」「３月」「3」など

    Returns:
        正規化された月（"3"など）、不正な場合は空文字列
    """
    if not month_str:
        return ''

    month_str = str(month_str).strip()

    # 「月」を削除
    month_str = month_str.replace('月', '')

    # 全角→半角に統一
    month_str = unicodedata.normalize('NFKC', month_str)

    # 数値に変換
    try:
        month_num = int(month_str)
    except ValueError:
        return ''  # 数値に変換できない

    # 1-12 の範囲チェック
    if 1 <= month_num <= 12:
        return str(month_num)
    else:
        return ''  # 不正な月

def normalize_graduation_year(year_str):
    """
    卒業年を正規化

    Args:
        year_str: 「2025」「2025年」など

    Returns:
        正規化された年（"2025"など）、不正な場合は空文字列
    """
    if not year_str:
        return ''

    year_str = str(year_str).strip()

    # 「年」を削除
    year_str = year_str.replace('年', '')

    # 全角→半角に統一
    year_str = unicodedata.normalize('NFKC', year_str)

    # 数値に変換
    try:
        year_num = int(year_str)
    except ValueError:
        return ''

    # 年の範囲チェック（1900-2100）
    if 1900 <= year_num <= 2100:
        return str(year_num)
    else:
        return ''

# テストケース
test_cases_month = [
    ('3月', '3'),
    ('３月', '3'),
    ('3', '3'),
    ('12月', '12'),
    ('１2月', '12'),  # 全角1、半角2
    ('13月', ''),  # 不正
    ('0月', ''),   # 不正
    ('', ''),
    (None, ''),
    ('abc', ''),   # 数値ではない
]

test_cases_year = [
    ('2025', '2025'),
    ('２０２５', '2025'),  # 全角
    ('2025年', '2025'),
    ('２０２５年', '2025'),
    ('1999', '1999'),
    ('2100', '2100'),
    ('1899', ''),  # 範囲外
    ('2101', ''),  # 範囲外
    ('', ''),
    (None, ''),
]

print("=" * 60)
print("卒業月の正規化テスト")
print("=" * 60)

for input_val, expected in test_cases_month:
    result = normalize_graduation_month(input_val)
    status = "[OK]" if result == expected else "[NG]"
    print(f"{status} Input: {repr(input_val):15s} → Expected: {repr(expected):5s}, Got: {repr(result):5s}")

print("\n" + "=" * 60)
print("卒業年の正規化テスト")
print("=" * 60)

for input_val, expected in test_cases_year:
    result = normalize_graduation_year(input_val)
    status = "[OK]" if result == expected else "[NG]"
    print(f"{status} Input: {repr(input_val):15s} → Expected: {repr(expected):10s}, Got: {repr(result):10s}")

print("\n" + "=" * 60)
print("Raw データでのテスト")
print("=" * 60)

import sys
sys.path.insert(0, 'python')
from normalize_csv import read_from_spreadsheet

spreadsheet_id = '1XB9s0VI5k0t_SOnNCTBTIsBaWzbb1nnCEQl-wldGyPo'
df = read_from_spreadsheet(spreadsheet_id, 'raw', 'service-account-key.json')

# 卒業月の列を取得
month_col = '14. 最終学歴となる大学・大学院の卒業予定月 / 既卒月'
year_col = '13. 最終学歴となる大学・大学院の卒業予定年 / 既卒年'

# 統計
month_values = df[month_col].dropna().unique()
year_values = df[year_col].dropna().unique()

print(f"\n【卒業月の値（{len(month_values)}種類）】")
for month in sorted(month_values):
    normalized = normalize_graduation_month(month)
    count = len(df[df[month_col] == month])
    status = "[OK]" if normalized else "[NG]"
    print(f"{status} {repr(month):15s} → {repr(normalized):5s} ({count}件)")

print(f"\n【卒業年の値（{len(year_values)}種類）】")
for year in sorted(year_values):
    normalized = normalize_graduation_year(year)
    count = len(df[df[year_col] == year])
    status = "[OK]" if normalized else "[NG]"
    print(f"{status} {repr(year):15s} → {repr(normalized):10s} ({count}件)")
