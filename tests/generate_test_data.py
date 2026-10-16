#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
from datetime import datetime, timedelta
import random

# テストデータ用の各項目リスト
COUNTRIES = ['日本', 'アメリカ', 'イギリス', 'カナダ', 'オーストラリア', 'マレーシア']

SCHOOLS_JP = [
    '東京大学', '東大', '京都大学', '早稲田大学', '慶應義塾大学',
    '明治大学', '同志社大学', '立命館大学', '関西学院大学',
    '大学', '未定', 'テンプル大学'
]

SCHOOLS_US = [
    'ハーバード大学', 'Harvard University', 'Yale', 'BYU', 'BYU大学',
    'UCLA', 'UC Berkeley', 'Community College', 'テンプル大学'
]

SCHOOLS_AU = [
    'メルボルン大学', 'University of Melbourne', 'ニューカッスル大学'
]

SCHOOLS_MY = [
    'モナッシュ大学', 'Monash大学', 'Monash University Malaysia'
]

MAJORS = [
    '経済学', '経営学', 'Business Management', 'Economics',
    '工学', '工', '工学科', 'Engineering',
    'コンピュータサイエンス', 'Computer science',
    'マーケティング', 'Marketing',
    '金融学', 'Finance', '未定', '勉強'
]

MINORS = [
    'データサイエンス', 'データサイエンス', '心理学', 'Psychology',
    '金融学', 'Finance', '未定', ''
]

def generate_test_data(num_rows=100):
    """テストデータを生成"""
    rows = [['回答ID', '回答日時', '回答者ID', '国', '学校名', '専攻', '副専攻']]

    base_date = datetime(2026, 10, 15, 9, 0)

    for i in range(1, num_rows + 1):
        answer_id = i
        timestamp = (base_date + timedelta(minutes=i*5)).strftime('%Y-%m-%d %H:%M')
        user_id = f"USER{i:03d}"

        country = random.choice(COUNTRIES)

        # 国に応じた学校を選択
        if country == '日本':
            school = random.choice(SCHOOLS_JP)
        elif country == 'アメリカ':
            school = random.choice(SCHOOLS_US)
        elif country == 'オーストラリア':
            school = random.choice(SCHOOLS_AU)
        elif country == 'マレーシア':
            school = random.choice(SCHOOLS_MY)
        else:
            school = random.choice(SCHOOLS_JP + SCHOOLS_US)

        # 複数学校の場合がある（約15%）
        if random.random() < 0.15:
            school2 = random.choice(SCHOOLS_JP + SCHOOLS_US)
            school = f"{school} / {school2}"

        major = random.choice(MAJORS)
        minor = random.choice(MINORS)

        rows.append([answer_id, timestamp, user_id, country, school, major, minor])

    return rows

def save_test_csv(rows, filepath):
    """CSV ファイルに保存"""
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"✓ テストデータを生成しました: {filepath} ({len(rows)-1} 行)")

if __name__ == '__main__':
    rows = generate_test_data(100)
    save_test_csv(rows, 'test_100rows.csv')
