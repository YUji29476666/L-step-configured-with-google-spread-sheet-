#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV データを Google Sheets に移行するスクリプト

学校名、専攻、副専攻の対応表を Google Sheets に移行
- 括弧内の数字を削除
- 複数の表記揺れを複数行に展開
- Google Sheets に一括書き込み
"""

import os
import sys
import json
import pandas as pd
import re
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


def get_sheet_id(service, spreadsheet_id, sheet_name):
    """シート ID を取得"""
    try:
        response = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        for sheet in response.get('sheets', []):
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']
    except Exception as e:
        print(f"[ERROR] シート ID 取得エラー: {e}")
    return None


def get_sheets_service(credentials_path=None):
    """Google Sheets サービスを取得"""
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    if creds_json:
        creds_dict = json.loads(creds_json)
        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
    else:
        if not credentials_path:
            credentials_path = 'service-account-key.json'
        credentials = Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )

    return build('sheets', 'v4', credentials=credentials)


def expand_variants(unified_value, variants_str):
    """表記揺れを複数行に展開

    Args:
        unified_value: 統一後の値（例："Waseda University"）
        variants_str: 表記揺れ（例："早稲田大学(19)、早大、Waseda U"）

    Returns:
        [(variant, unified_value), ...] のリスト
    """
    if not variants_str or pd.isna(variants_str):
        return []

    variants_str = str(variants_str)

    # 括弧内の数字を削除（例："早稲田大学(19)" → "早稲田大学"）
    variants_str = re.sub(r'\(\d+\)', '', variants_str)

    # 「、」だけで分割（他の区切り文字では誤った分割が発生するため）
    variants = re.split(r'[、]', variants_str)

    rows = []
    for variant in variants:
        variant = variant.strip()
        if variant and variant != unified_value:
            rows.append((variant, unified_value))

    return rows


def migrate_school_names(service, spreadsheet_id, credentials_path=None):
    """学校名対応表を Google Sheets に移行"""
    print("\n=== 学校名対応表を処理中 ===")

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_path, 'data', 'school_mapping.csv')

    if not os.path.exists(csv_path):
        print(f"[ERROR] ファイルが見つかりません: {csv_path}")
        return 0

    # CSV を読み込み
    df = pd.read_csv(csv_path, encoding='utf-8')
    print(f"✓ {csv_path} から {len(df)} 行を読み込みました")

    rows_to_write = [['表記揺れ（入力値）', '統一後の名前', '国コード', 'カテゴリ', 'メモ', '優先度', '確認済み']]

    for _, row in df.iterrows():
        unified = str(row.get('統一後の値', '')).strip()
        variants_str = str(row.get('まとめられる元の値(すべて)', ''))

        if unified and variants_str and not pd.isna(variants_str):
            expanded = expand_variants(unified, variants_str)
            for variant, unified_val in expanded:
                rows_to_write.append([
                    variant,  # 表記揺れ
                    unified_val,  # 統一後の値
                    '',  # 国コード（オプション）
                    '',  # カテゴリ
                    '',  # メモ
                    '高',  # 優先度（デフォルト）
                    '✓'  # 確認済み（自動チェック）
                ])

    print(f"✓ {len(rows_to_write) - 1} 行に展開しました")

    # Google Sheets に書き込み
    sheet_name = '辞書_学校名'
    _write_to_sheet(service, spreadsheet_id, sheet_name, rows_to_write)

    return len(rows_to_write) - 1


def migrate_majors(service, spreadsheet_id, credentials_path=None):
    """専攻対応表を Google Sheets に移行"""
    print("\n=== 専攻対応表を処理中 ===")

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_path, 'data', 'major_mapping.csv')

    if not os.path.exists(csv_path):
        print(f"[ERROR] ファイルが見つかりません: {csv_path}")
        return 0

    # CSV を読み込み
    df = pd.read_csv(csv_path, encoding='utf-8')
    print(f"✓ {csv_path} から {len(df)} 行を読み込みました")

    rows_to_write = [['表記揺れ（入力値）', '統一後の名前', 'カテゴリ', 'メモ', '優先度', '確認済み', '']]

    for _, row in df.iterrows():
        unified = str(row.get('統一後の値', '')).strip()
        variants_str = str(row.get('まとめられる元の値(すべて)', ''))

        if unified and variants_str and not pd.isna(variants_str):
            expanded = expand_variants(unified, variants_str)
            for variant, unified_val in expanded:
                rows_to_write.append([
                    variant,  # 表記揺れ
                    unified_val,  # 統一後の値
                    '',  # カテゴリ
                    '',  # メモ
                    '高',  # 優先度
                    '✓',  # 確認済み
                    ''  # 予備列
                ])

    print(f"✓ {len(rows_to_write) - 1} 行に展開しました")

    # Google Sheets に書き込み
    sheet_name = '辞書_専攻'
    _write_to_sheet(service, spreadsheet_id, sheet_name, rows_to_write)

    return len(rows_to_write) - 1


def migrate_minors(service, spreadsheet_id, credentials_path=None):
    """副専攻対応表を Google Sheets に移行"""
    print("\n=== 副専攻対応表を処理中 ===")

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_path, 'data', 'minor_major_mapping.csv')

    if not os.path.exists(csv_path):
        print(f"[ERROR] ファイルが見つかりません: {csv_path}")
        return 0

    # CSV を読み込み
    df = pd.read_csv(csv_path, encoding='utf-8')
    print(f"✓ {csv_path} から {len(df)} 行を読み込みました")

    rows_to_write = [['表記揺れ（入力値）', '統一後の名前', 'カテゴリ', 'メモ', '優先度', '確認済み', '']]

    for _, row in df.iterrows():
        unified = str(row.get('統一後の値', '')).strip()
        variants_str = str(row.get('まとめられる元の値(すべて)', ''))

        if unified and variants_str and not pd.isna(variants_str):
            expanded = expand_variants(unified, variants_str)
            for variant, unified_val in expanded:
                rows_to_write.append([
                    variant,  # 表記揺れ
                    unified_val,  # 統一後の値
                    '',  # カテゴリ
                    '',  # メモ
                    '高',  # 優先度
                    '✓',  # 確認済み
                    ''  # 予備列
                ])

    print(f"✓ {len(rows_to_write) - 1} 行に展開しました")

    # Google Sheets に書き込み
    sheet_name = '辞書_副専攻'
    _write_to_sheet(service, spreadsheet_id, sheet_name, rows_to_write)

    return len(rows_to_write) - 1


def _write_to_sheet(service, spreadsheet_id, sheet_name, rows):
    """Google Sheets にデータを書き込み"""
    try:
        # シート ID を取得
        sheet_id = get_sheet_id(service, spreadsheet_id, sheet_name)
        if sheet_id is None:
            print(f"[WARN] シート「{sheet_name}」が見つかりません（スキップ）")
            return

        # シートをクリア
        requests = [{
            'updateCells': {
                'range': {'sheetId': sheet_id},
                'fields': '*'
            }
        }]
        body = {'requests': requests}
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

        # データを書き込み
        body = {'values': rows}
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption='RAW',
            body=body
        ).execute()

        print(f"✓ Google Sheets「{sheet_name}」に {len(rows) - 1} 行を書き込みました")

    except Exception as e:
        print(f"[ERROR] Google Sheets 書き込みエラー: {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='CSV データを Google Sheets に移行')
    parser.add_argument(
        '--spreadsheet-id',
        required=True,
        help='Google Spreadsheet ID'
    )
    parser.add_argument(
        '--credentials',
        default='service-account-key.json',
        help='Google Cloud サービスアカウント認証ファイル'
    )

    args = parser.parse_args()

    try:
        service = get_sheets_service(args.credentials)

        school_count = migrate_school_names(service, args.spreadsheet_id, args.credentials)
        major_count = migrate_majors(service, args.spreadsheet_id, args.credentials)
        minor_count = migrate_minors(service, args.spreadsheet_id, args.credentials)

        total = school_count + major_count + minor_count
        print(f"\n✅ 完了！合計 {total} 行を Google Sheets に移行しました")
        print(f"  - 学校名：{school_count} 行")
        print(f"  - 専攻：{major_count} 行")
        print(f"  - 副専攻：{minor_count} 行")

    except Exception as e:
        print(f"[ERROR] エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
