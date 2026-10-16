#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, 'python')

from rulebook import load_dictionaries

dicts = load_dictionaries()

print("=== 国の辞書 ===")
for key, val in sorted(dicts['country'].items()):
    print(f"  {key} -> {val}")

print("\n=== 学校名の辞書（Other）の最初の20項目 ===")
school_dict = dicts['school']['Other']
for i, (key, val) in enumerate(sorted(school_dict.items())[:20]):
    print(f"  {key} -> {val}")

print(f"\n合計: {len(school_dict)} 個の学校\n")

# テスト: いくつかの学校が含まれているか確認
test_schools = ['早稲田大学', 'ハーバード大学', 'UCLA', 'BYU', 'メルボルン大学',
                'モナッシュ大学', '東京大学', '東大', '慶應義塾大学']

print("=== テスト: 特定の学校が辞書に含まれているか ===")
for school in test_schools:
    if school in school_dict:
        print(f"  [OK] {school} -> {school_dict[school]}")
    else:
        print(f"  [NG] {school} は見つかりません")

print("\n=== 専攻の辞書（最初の10項目） ===")
major_dict = dicts['major']
for i, (key, vals) in enumerate(sorted(major_dict.items())[:10]):
    print(f"  {key}: {vals[:3]}...")  # 最初の3つだけ表示
