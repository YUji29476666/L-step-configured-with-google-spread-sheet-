#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Sheets に 6 行の辞書行を追加
前回の失敗（header=None, keep_default_na）を修正
"""

import sys
import os
import json
import subprocess
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

import pandas as pd

SPREADSHEET_ID = '1XB9s0VI5k0t_SOnNCTBTIsBaWzbb1nnCEQl-wldGyPo'
UPDATES_DIR = Path(__file__).parent.parent / 'lstep-data-updates'

def get_sheets_service():
    """Google Sheets API のサービスを取得"""
    try:
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')

        if creds_json:
            creds_dict = json.loads(creds_json)
            credentials = Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
        else:
            credentials_path = 'service-account-key.json'
            credentials = Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )

        return build('sheets', 'v4', credentials=credentials)
    except Exception as e:
        print(f"[ERROR] 認証失敗：{e}")
        sys.exit(1)

def get_sheet_id(service, sheet_name):
    """シート名からシートIDを取得"""
    try:
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID
        ).execute()

        for sheet in spreadsheet.get('sheets', []):
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']

        return None
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def main():
    """メイン処理"""
    print("\n" + "="*80)
    print("6行の辞書行を Google Sheets に追加")
    print("="*80)

    service = get_sheets_service()

    # Step 1: バックアップ作成
    print("\n【Step 1: バックアップ作成】")
    backup_sheet_id = get_sheet_id(service, '辞書_学校名_バックアップ1019c')
    if backup_sheet_id is not None:
        request = {'deleteSheet': {'sheetId': backup_sheet_id}}
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': [request]}
        ).execute()
        print("  既存バックアップを削除")

    dict_sheet_id = get_sheet_id(service, '辞書_学校名')
    request = {
        'duplicateSheet': {
            'sourceSheetId': dict_sheet_id,
            'newSheetName': '辞書_学校名_バックアップ1019c'
        }
    }
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={'requests': [request]}
    ).execute()
    print("  バックアップ「辞書_学校名_バックアップ1019c」を作成")

    # Step 2: 追加前に「NA」の行数をカウント
    print("\n【Step 2: 追加前の確認】")
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='辞書_学校名!A:G'
    ).execute()

    values = result.get('values', [])
    current_rows = len(values) - 1  # ヘッダー除く

    df = pd.DataFrame(values[1:], columns=values[0])
    na_count_before = (df['統一後の名前'].astype(str) == 'NA').sum()

    print(f"  現在の行数（ヘッダー除く）：{current_rows}")
    print(f"  統一後の名前が「NA」の行数：{na_count_before}行")

    # Step 3: 6行を追加
    print("\n【Step 3: 6行を追加】")
    csv_file = UPDATES_DIR / '辞書_学校名_貼り付け用_1019c.csv'

    # CSV を header=None で読み込む（見出しなし）
    append_df = pd.read_csv(csv_file, encoding='utf-8', header=None, keep_default_na=False)
    print(f"  追加ファイルの行数：{len(append_df)}")

    # NaN を空文字列に置き換え
    append_df_filled = append_df.fillna('')

    values_to_append = []
    for idx, row in append_df_filled.iterrows():
        values_to_append.append([str(x) if x != '' else '' for x in row.tolist()])

    body = {
        'values': values_to_append
    }

    # 末尾に追加（ヘッダー + 現在の行数 + 1）
    append_range = f'辞書_学校名!A{current_rows + 2}'

    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=append_range,
        valueInputOption='RAW',
        body=body
    ).execute()
    print(f"  {len(append_df)}行を末尾に追加")

    # Step 4: 追加後の確認
    print("\n【Step 4: 追加後の確認】")
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='辞書_学校名!A:G'
    ).execute()

    values = result.get('values', [])
    final_rows = len(values) - 1  # ヘッダー除く

    df_after = pd.DataFrame(values[1:], columns=values[0])
    na_count_after = (df_after['統一後の名前'].astype(str) == 'NA').sum()
    empty_count = (df_after['統一後の名前'].astype(str).str.strip() == '').sum()

    print(f"  最終行数（ヘッダー除く）：{final_rows}")
    print(f"  増加行数：{final_rows - current_rows}（期待：6）")
    print(f"  統一後の名前が「NA」の行数：{na_count_after}（期待：{na_count_before}）")
    print(f"  統一後の名前が空欄の行数：{empty_count}（期待：0）")

    # 確認
    if final_rows - current_rows != 6:
        print("\n[ERROR] 増加行数が6ではありません")
        return False

    if na_count_after != na_count_before:
        print("\n[ERROR] NAの行数が変わりました")
        return False

    if empty_count != 0:
        print("\n[ERROR] 空欄の統一後の名前が見つかりました")
        return False

    print("\n  ✓ すべての確認項目が OK")

    # Step 5: 本番実行
    print("\n【Step 5: 本番実行】")

    try:
        result = subprocess.run(
            [sys.executable, 'python/normalize_csv.py',
             '--spreadsheet-id', SPREADSHEET_ID,
             '--use-sheets-dict'],
            cwd=str(Path(__file__).parent),
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            print(f"  [ERROR] 実行失敗")
            return False

        print(f"  [OK] 実行完了")

        # 出力から件数を抽出
        output = result.stdout

        print(f"\n【結果】")
        for line in output.split('\n'):
            if 'matched' in line or 'unmatched' in line or 'partial' in line or '件' in line:
                if '====' not in line and line.strip():
                    print(f"  {line.strip()}")

        return True

    except Exception as e:
        print(f"  [ERROR] {e}")
        return False

if __name__ == '__main__':
    success = main()

    print("\n" + "="*80)
    if success:
        print("[OK] 処理完了")
    else:
        print("[ERROR] 処理失敗 - 本番は実行していません")
    print("="*80)
