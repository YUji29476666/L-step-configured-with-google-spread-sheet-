#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Google Sheets に「辞書_ステータス」タブを作成し、CSV データを貼り込む"""

import pandas as pd
import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def setup_status_dictionary_sheet(spreadsheet_id, csv_path, credentials_path=None):
    """「辞書_ステータス」タブを作成し、CSV データを貼り込む"""

    # 認証
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

    service = build('sheets', 'v4', credentials=credentials)

    # 1. CSV ファイルを読み込む
    print(f"[*] CSV ファイルを読み込んでいます: {csv_path}")
    df = pd.read_csv(csv_path, encoding='utf-8')
    print(f"[OK] {len(df)} 行のデータを読み込みました")

    # 2. 既存のシート一覧を確認
    print(f"[*] Google Sheets のシート一覧を確認しています...")
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_names = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
    print(f"[INFO] 既存のシート: {sheet_names}")

    # 3. 「辞書_ステータス」タブが存在するか確認
    if '辞書_ステータス' in sheet_names:
        print(f"[!] 「辞書_ステータス」タブは既に存在します。削除します...")
        sheet_id = None
        for sheet in spreadsheet['sheets']:
            if sheet['properties']['title'] == '辞書_ステータス':
                sheet_id = sheet['properties']['sheetId']
                break

        if sheet_id is not None:
            # シートを削除
            request = {
                'deleteSheet': {'sheetId': sheet_id}
            }
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': [request]}
            ).execute()
            print(f"[OK] 既存の「辞書_ステータス」タブを削除しました")

    # 4. 新しい「辞書_ステータス」タブを作成
    print(f"[*] 新しい「辞書_ステータス」タブを作成しています...")
    request = {
        'addSheet': {
            'properties': {
                'title': '辞書_ステータス',
                'index': 4  # 5番目のタブ（0-indexed）
            }
        }
    }
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={'requests': [request]}
    ).execute()
    print(f"[OK] 「辞書_ステータス」タブを作成しました")

    # 5. CSV データを Google Sheets に書き込む
    print(f"[*] CSV データを Google Sheets に書き込んでいます...")

    # ヘッダ行と データ行を準備
    values = [df.columns.tolist()] + df.values.tolist()

    # 値を文字列に変換（NaN は空欄に）
    values_str = []
    for row in values:
        row_str = []
        for val in row:
            if pd.isna(val):
                row_str.append('')
            else:
                row_str.append(str(val))
        values_str.append(row_str)

    # Google Sheets に書き込み
    body = {
        'values': values_str
    }

    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range='辞書_ステータス!A1',
        valueInputOption='RAW',
        body=body
    ).execute()

    print(f"[OK] {result['updatedRows']} 行、{result['updatedColumns']} 列を書き込みました")

    print(f"\n[SUCCESS] 「辞書_ステータス」タブのセットアップが完了しました！")
    print(f"  - タブ名: 辞書_ステータス")
    print(f"  - データ行数: {len(values_str)} 行（ヘッダ含む）")

if __name__ == '__main__':
    # Spreadsheet ID と CSV ファイルパス
    SPREADSHEET_ID = '1XB9s0VI5k0t_SOnNCTBTIsBaWzbb1nnCEQl-wldGyPo'
    CSV_PATH = '../../lstep-data-updates/辞書_ステータス_1023.csv'
    CREDENTIALS_PATH = '../service-account-key.json'

    setup_status_dictionary_sheet(SPREADSHEET_ID, CSV_PATH, CREDENTIALS_PATH)
