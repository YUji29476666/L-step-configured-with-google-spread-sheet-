#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import sys

# 出力ファイルを読み込む（UTF-8）
df = pd.read_csv('tests/actual_data_normalized.csv', encoding='utf-8')

print("=" * 70)
print("処理結果の詳細分析")
print("=" * 70)

# ステータス別の集計
print("\n=== ステータス別の集計 ===")
status_counts = df['processing_status'].value_counts()
for status, count in status_counts.items():
    pct = count / len(df) * 100
    print(f"{status}: {count} 件 ({pct:.1f}%)")

print(f"\n合計: {len(df)} 行")

# 「要確認」のサンプルを表示（学校名と状況を確認）
print("\n=== 「要確認」のサンプル（最初の 10 件） ===")
concern_rows = df[df['processing_status'] == '要確認']
if len(concern_rows) > 0:
    for idx, (i, row) in enumerate(concern_rows.head(10).iterrows()):
        # 学校名列を検索
        school_val = None
        for col in df.columns:
            if '10.' in col or col == '学校名':
                school_val = row[col]
                break
        if school_val:
            print(f"  {idx+1}. {school_val}")

# 「未定」のサンプルを表示
print("\n=== 「未定」のサンプル（最初の 10 件） ===")
undefined_rows = df[df['processing_status'] == '未定']
if len(undefined_rows) > 0:
    for idx, (i, row) in enumerate(undefined_rows.head(10).iterrows()):
        # 学校名列を検索
        school_val = None
        for col in df.columns:
            if '10.' in col or col == '学校名':
                school_val = row[col]
                break
        if school_val:
            print(f"  {idx+1}. {school_val}")

# 元データと出力データの列数比較
print(f"\n=== 列数の比較 ===")
orig_df = pd.read_csv('tests/actual_data.csv', encoding='cp932')
print(f"元データの列数: {len(orig_df.columns)}")
print(f"出力データの列数: {len(df.columns)}")
print(f"追加された列: processing_status")
