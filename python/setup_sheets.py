#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google Sheets に辞書管理用のシートを作成するスクリプト
"""

import os
import json
import sys
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def setup_dictionary_sheets(spreadsheet_id, credentials_path=None):
    """Google Sheets に辞書シートを作成"""

    try:
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

        # シート作成リクエスト
        requests = []

        sheet_names = ['辞書_学校名', '辞書_専攻', '辞書_副専攻']

        for sheet_name in sheet_names:
            requests.append({
                'addSheet': {
                    'properties': {
                        'title': sheet_name,
                        'gridProperties': {
                            'rowCount': 2000,
                            'columnCount': 7
                        }
                    }
                }
            })

        body = {'requests': requests}
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()

        print("✅ シート作成完了:")
        for sheet_name in sheet_names:
            print(f"  - {sheet_name}")

        # ヘッダー行を追加
        add_headers(service, spreadsheet_id, sheet_names)

        return True

    except Exception as e:
        print(f"[ERROR] シート作成エラー: {e}")
        return False

def add_headers(service, spreadsheet_id, sheet_names):
    """ヘッダー行を追加"""

    headers = {
        '辞書_学校名': ['表記揺れ（入力値）', '統一後の名前', '国コード', 'カテゴリ', 'メモ', '優先度', '確認済み'],
        '辞書_専攻': ['表記揺れ（入力値）', '統一後の名前', 'カテゴリ', 'メモ', '優先度', '確認済み', ''],
        '辞書_副専攻': ['表記揺れ（入力値）', '統一後の名前', 'カテゴリ', 'メモ', '優先度', '確認済み', '']
    }

    for sheet_name in sheet_names:
        try:
            values = [headers.get(sheet_name, [])]
            body = {'values': values}
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f'{sheet_name}!A1:G1',
                valueInputOption='RAW',
                body=body
            ).execute()
            print(f"✅ {sheet_name} のヘッダーを追加しました")
        except Exception as e:
            print(f"[WARN] {sheet_name} のヘッダー追加エラー: {e}")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Google Sheets に辞書シートを作成')
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

    success = setup_dictionary_sheets(args.spreadsheet_id, args.credentials)
    sys.exit(0 if success else 1)
