#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google Sheets の対応表から辞書を読み込み、rulebook.py を更新するスクリプト
"""

import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import json

SHEETS_ID = '1ztsbQbyUrnNZitpyx4iQYTxmK8ZHN3WRWxq7kvCsZw4'
CREDENTIALS_PATH = 'service-account-key.json'

# シート名と対応する gid
SHEETS_INFO = {
    '学校名': 359105897,
    '専攻': 359105897,  # 同じシート内の別のセクションかもしれません
    '副専攻': 2104780629,
}

def get_sheets_service():
    """Google Sheets API サービスを取得"""
    credentials = Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    return build('sheets', 'v4', credentials=credentials)

def fetch_sheet_data(sheet_name, gid):
    """Google Sheets からデータを取得"""
    service = get_sheets_service()

    # シート名から範囲を取得
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEETS_ID,
        range=f"'{sheet_name}'!A:Z"
    ).execute()

    values = result.get('values', [])
    if not values:
        print(f"✗ シート「{sheet_name}」にデータがありません")
        return None

    # DataFrame に変換
    headers = values[0]
    data = values[1:]
    df = pd.DataFrame(data, columns=headers)

    print(f"✓ 「{sheet_name}」から {len(df)} 行を読み込みました")
    return df

def build_school_dict(df):
    """学校名の辞書を構築"""
    school_dict = {}

    for _, row in df.iterrows():
        # 列名は「元の学校名」「統一後（現在の辞書）」と想定
        if pd.isna(row.get('元の学校名')) or pd.isna(row.get('統一後（現在の辞書）')):
            continue

        original = str(row['元の学校名']).strip()
        unified = str(row['統一後（現在の辞書）']).strip()

        if original and unified:
            school_dict[original] = unified

    return school_dict

def build_major_dict(df):
    """専攻・副専攻の辞書を構築"""
    major_dict = {}

    for _, row in df.iterrows():
        # 列名は「統一後（現在の辞書）」と「表記揺れ1」「表記揺れ2」... と想定
        unified_name = str(row.get('統一後（現在の辞書）', '')).strip()

        if not unified_name or pd.isna(row.get('統一後（現在の辞書）')):
            continue

        # 表記揺れを集める
        variants = []
        for col in df.columns:
            if col.startswith('表記揺れ') or col == '統一後（現在の辞書）':
                val = str(row.get(col, '')).strip()
                if val and not pd.isna(row.get(col)):
                    variants.append(val)

        if variants:
            major_dict[unified_name] = variants

    return major_dict

def generate_rulebook_code(school_dict, major_dict_専攻, major_dict_副専攻):
    """rulebook.py の Python コードを生成"""

    code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unicodedata
import re
import pandas as pd

# 学校名の辞書（シートから自動生成）
SCHOOL_DICT = {
    'JP': {
'''

    # 日本の学校名を追加（国別マッピング無しで）
    for original, unified in school_dict.items():
        code += f"        '{original}': '{unified}',\n"

    code += '''    },
    'Other': {
'''

    for original, unified in school_dict.items():
        code += f"        '{original}': '{unified}',\n"

    code += '''    }
}

# 専攻・副専攻の辞書（シートから自動生成）
MAJOR_DICT = {
'''

    for unified_name, variants in major_dict_専攻.items():
        code += f"    '{unified_name}': {variants},\n"

    code += '''}

# 副専攻の辞書
MINOR_MAJOR_DICT = {
'''

    for unified_name, variants in major_dict_副専攻.items():
        code += f"    '{unified_name}': {variants},\n"

    code += '''}}

# ... 残りのコードは既存の rulebook.py と同じ
'''

    return code

def main():
    """メイン処理"""
    print("=" * 60)
    print("Google Sheets から辞書データを読み込み中...")
    print("=" * 60)

    # 学校名を読み込み
    df_school = fetch_sheet_data('学校名', SHEETS_INFO['学校名'])
    if df_school is None:
        return

    school_dict = build_school_dict(df_school)
    print(f"✓ 学校名辞書：{len(school_dict)} 件\n")

    # 専攻を読み込み
    df_major = fetch_sheet_data('専攻', SHEETS_INFO['専攻'])
    if df_major is None:
        return

    major_dict_専攻 = build_major_dict(df_major)
    print(f"✓ 専攻辞書：{len(major_dict_専攻)} 件\n")

    # 副専攻を読み込み
    df_minor = fetch_sheet_data('副専攻', SHEETS_INFO['副専攻'])
    if df_minor is None:
        return

    major_dict_副専攻 = build_major_dict(df_minor)
    print(f"✓ 副専攻辞書：{len(major_dict_副専攻)} 件\n")

    # コード生成
    print("=" * 60)
    print("rulebook.py コード生成:")
    print("=" * 60)

    code = generate_rulebook_code(school_dict, major_dict_専攻, major_dict_副専攻)
    print(code)

    print("\n✓ コード生成完了")
    print("このコードを rulebook.py にコピーしてください")

if __name__ == '__main__':
    main()
