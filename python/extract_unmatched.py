#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import os
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pandas as pd

def get_sheets_service(credentials_path=None):
    try:
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        if creds_json:
            import json as json_module
            creds_dict = json_module.loads(creds_json)
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
    except FileNotFoundError:
        print(f"[ERROR] 認証ファイルが見つかりません: {credentials_path}")
        sys.exit(1)

def read_cleaned_sheet(spreadsheet_id, sheet_name='cleaned', credentials_path=None):
    try:
        service = get_sheets_service(credentials_path)
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A:N"
        ).execute()

        values = result.get('values', [])
        if not values:
            print(f"[ERROR] シート「{sheet_name}」にデータがありません")
            sys.exit(1)

        headers = values[0]
        data = values[1:]
        df = pd.DataFrame(data, columns=headers)
        print(f"[OK] {len(df)} 行を読み込みました")
        return df

    except Exception as e:
        print(f"[ERROR] Spreadsheet 読み込みエラー: {e}")
        sys.exit(1)

def extract_unmatched(df):
    unmatched_schools = {}

    for idx, row in df.iterrows():
        try:
            school_val = row.get('学校名', '')
            school_status = row.get('学校名_status', '')

            if school_status == 'unmatched' and school_val and str(school_val).strip():
                school_key = str(school_val).strip()
                unmatched_schools[school_key] = unmatched_schools.get(school_key, 0) + 1

        except Exception as e:
            pass

    return unmatched_schools

def aggregate_unmatched(unmatched_dict, min_count=1):
    aggregated = []
    for school, count in sorted(unmatched_dict.items(), key=lambda x: x[1], reverse=True):
        if count >= min_count:
            aggregated.append({
                'school_name': school,
                'count': count
            })
    return aggregated

def save_json(data, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] {output_path} に保存しました")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Unmatched schools を抽出')
    parser.add_argument('--spreadsheet-id', required=True, help='Google Spreadsheet ID')
    parser.add_argument('--sheet-name', default='cleaned', help='入力シート名（デフォルト: cleaned）')
    parser.add_argument('--output', default='output/unmatched_schools.json', help='出力ファイル')
    parser.add_argument('--credentials', default='service-account-key.json', help='認証ファイル')
    parser.add_argument('--min-count', type=int, default=1, help='最小出現回数（デフォルト: 1）')

    args = parser.parse_args()

    print("=" * 60)
    print("Unmatched schools 抽出")
    print("=" * 60)

    df = read_cleaned_sheet(args.spreadsheet_id, args.sheet_name, args.credentials)
    unmatched_dict = extract_unmatched(df)
    aggregated = aggregate_unmatched(unmatched_dict, args.min_count)

    output_data = {
        'extracted_at': datetime.now().isoformat(),
        'total_unmatched': len(aggregated),
        'schools': aggregated
    }

    save_json(output_data, args.output)

    print(f"\n=== 抽出結果 ===")
    print(f"Unmatched schools: {len(aggregated)} 件")
    for item in aggregated[:10]:
        print(f"  {item['school_name']}: {item['count']} 件")
    if len(aggregated) > 10:
        print(f"  ... ほか {len(aggregated) - 10} 件")

if __name__ == '__main__':
    main()
