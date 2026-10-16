#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import pandas as pd
import sys
import json
import os
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from rulebook import load_dictionaries, normalize_country, normalize_school, normalize_major

def read_csv(filepath, encoding='shift_jis'):
    """CSV ファイルを読み込む（複数エンコーディング対応）"""
    encodings = [encoding, 'utf-8', 'cp932', 'iso-8859-1', 'utf-16']

    for enc in encodings:
        try:
            df = pd.read_csv(filepath, encoding=enc)
            print(f"[OK] CSV を読み込みました（エンコーディング: {enc}）")
            return df
        except (UnicodeDecodeError, LookupError):
            continue

    print(f"[ERROR] CSV 読み込みエラー: 対応するエンコーディングが見つかりません")
    sys.exit(1)

def format_graduation_date(year, month):
    """卒業年月を YYYY年M月 形式に統一"""
    year = str(year).strip()
    month = str(month).strip()

    if not year or year == '':
        return ''

    if not month or month == '':
        return f"{year}年"

    return f"{year}年{month}月"

def normalize_row(row, dicts):
    """1行分のデータを正規化"""
    # DEBUG: 最初の行だけ列名と性別を確認（デバッグ用）
    if row.name == 0:
        print("=" * 60)
        print("DEBUG: row の全列名と値（最初の行）")
        print("=" * 60)
        for col in row.index[:15]:
            print(f"  {repr(col)}: {repr(row.get(col, 'NOT FOUND'))}")
        print()

    # L-step の列名対応（複数の形式に対応）
    school_value_raw = get_value_from_row(row, [
        '学校名',
        '10. 現在、在学中/在学予定/在学希望の学校名（例：ハーバード大学）',
    ])

    major_value_raw = get_value_from_row(row, [
        '専攻',
        '11. 現在、在学している学校での専攻（例：会計学）',
    ])

    minor_major_value_raw = get_value_from_row(row, [
        '副専攻',
        '12. 現在、在学している学校での副専攻（例：言語学）',
    ])

    country_value_raw = get_value_from_row(row, [
        '国',
        '9. 現在、在学中/在学予定/在学希望の国（例：アメリカ）',
    ])

    # 性別、学位、卒業年月を取得（複数のパターンに対応）
    gender_raw = get_value_from_row(row, [
        '性別',
        '3. 性別',
        '3.',  # 「3. 性別」の「3.」で検索
    ])

    # DEBUG: 最初の行だけ性別の抽出結果を表示
    if row.name == 0:
        print(f"DEBUG: gender_raw = {repr(gender_raw)}")

    degree_raw = get_value_from_row(row, [
        '学位',
        '取得予定/済み学位',
        '8. 現在の取得予定/取得済みの学位',
    ])

    graduation_year_raw = get_value_from_row(row, [
        '卒業年度',
        '13. 最終学歴となる大学・大学院の卒業予定年 / 既卒年',
    ])

    graduation_month_raw = get_value_from_row(row, [
        '卒業月',
        '14. 最終学歴となる大学・大学院の卒業予定月 / 既卒月',
    ])

    # 現在のステータスを取得
    current_status_raw = get_value_from_row(row, [
        '現在のステータス',
        '7. 現在のステータス',
    ])

    graduation_date = format_graduation_date(graduation_year_raw, graduation_month_raw)

    result = {
        'gender': gender_raw,
        'degree': degree_raw,
        'current_status': current_status_raw,
        'graduation_date': graduation_date,
        'country_result': normalize_country(str(country_value_raw), dicts['country']),
        'school_result': None,
        'major_result': None,
        'minor_major_result': None,
        'status': None
    }

    country_code = result['country_result'].get('value', '')

    result['school_result'] = normalize_school(
        str(school_value_raw),
        dicts['school']['Other'],
        country_code
    )

    result['major_result'] = normalize_major(str(major_value_raw), dicts['major'])
    result['minor_major_result'] = normalize_major(str(minor_major_value_raw), dicts['major'])

    result['status'] = determine_status(result)

    return result

def get_value_from_row(row, column_names):
    """複数の列名候補から値を取得（完全一致・部分一致対応）"""
    # 完全一致を試す
    for col_name in column_names:
        if col_name in row.index and pd.notna(row[col_name]):
            return row[col_name]

    # 部分一致を試す（キーワードを含む列を検索）
    for col_name in column_names:
        for idx_col in row.index:
            if col_name in str(idx_col) and pd.notna(row[idx_col]):
                return row[idx_col]

    return ''

def determine_status(result):
    """processing_status を判定"""
    statuses = []

    if result['country_result'].get('status') in ['error', 'unmatched']:
        statuses.append('要確認')
    if result['school_result'].get('status') in ['error', 'unmatched']:
        statuses.append('要確認')
    if result['major_result'].get('status') == 'unmatched':
        statuses.append('未定')

    if '要確認' in statuses:
        return '要確認'
    if '未定' in statuses:
        return '未定'
    return '統一済み'

def get_value(val):
    """値を処理：nan を空文字列に変換"""
    if pd.isna(val) or val == 'nan' or val is None:
        return ''
    return str(val)

def process_csv(input_filepath, output_filepath=None):
    """CSV を読み込み → 正規化 → 出力"""
    print("=" * 60)
    print("L-step データ正規化処理")
    print("=" * 60)

    # 1. CSV 読み込み
    df = read_csv(input_filepath)
    print(f"処理対象: {len(df)} 行\n")

    # DEBUG: 実際の列名を表示
    print("=" * 60)
    print("DEBUG: 実際の列名（最初の10列）")
    print("=" * 60)
    for i, col in enumerate(df.columns[:10]):
        print(f"  列{i}: {repr(col)}")
    print()

    # 2. 辞書を読み込み
    print("正規化ルール（辞書）を読み込み中...")
    dicts = load_dictionaries()
    print(f"[OK] 辞書ロード完了\n")

    # 3. 行ごとに正規化
    print("正規化処理を実行中...")
    results = []
    errors = []

    for idx, row in df.iterrows():
        try:
            normalized = normalize_row(row, dicts)

            # 出力列のみを抽出
            result_row = {
                '現在のステータス': get_value(normalized['current_status']),
                '性別': get_value(normalized['gender']),
                '取得予定/済み学位': get_value(normalized['degree']),
                '国': get_value(normalized['country_result'].get('value', '')),
                '学校名': get_value(normalized['school_result'].get('value', '')),
                '専攻': get_value(normalized['major_result'].get('value', '')),
                '副専攻': get_value(normalized['minor_major_result'].get('value', '')),
                '卒業年度': get_value(normalized['graduation_date']),
                'processing_status': get_value(normalized['status'])
            }
            results.append(result_row)
        except Exception as e:
            errors.append({'row': idx + 2, 'error': str(e)})

    # 4. 結果を DataFrame に
    result_df = pd.DataFrame(results)

    # 出力列の順序を固定
    output_columns = [
        '現在のステータス', '性別', '取得予定/済み学位',
        '国', '学校名', '専攻', '副専攻', '卒業年度', 'processing_status'
    ]
    result_df = result_df[output_columns]

    # nan を空文字列に置換
    result_df = result_df.fillna('')

    print(f"[OK] 正規化完了: {len(results)} 行\n")

    # DEBUG: 出力 DataFrame の列を確認
    print("DEBUG: 出力列名:")
    print(list(result_df.columns))
    print(f"DEBUG: 最初の行のデータ:")
    if len(result_df) > 0:
        print(result_df.iloc[0].to_dict())
    print()

    # DEBUG: DataFrame の列順序と値を詳しく確認
    print("=" * 60)
    print("DEBUG: DataFrame columns order（詳細）")
    print("=" * 60)
    for i, col in enumerate(result_df.columns):
        print(f"  {i}: {repr(col)}")

    if len(result_df) > 0:
        print("\nDEBUG: DataFrame values (first row) - detailed")
        first_row_values = result_df.iloc[0].tolist()
        for i, val in enumerate(first_row_values):
            print(f"  {i}: {repr(val)}")
    print()

    # 5. 統計情報を表示
    status_counts = result_df['processing_status'].value_counts()
    print("=== 処理結果統計 ===")
    for status, count in status_counts.items():
        print(f"{status}: {count} 件")

    if errors:
        print(f"エラー: {len(errors)} 件")
        for error in errors[:5]:  # 最初の5件だけ表示
            print(f"  行 {error['row']}: {error['error']}")

    print()

    # 6. 出力ファイルに書き込み
    if output_filepath:
        result_df.to_csv(output_filepath, index=False, encoding='utf-8', na_rep='')
        print(f"[OK] 出力ファイルに書き込みました: {output_filepath}")

    return result_df

def get_sheets_service(credentials_path=None):
    """Google Sheets API のサービスを取得"""
    try:
        # 環境変数から認証情報を読み込む（GitHub Actions用）
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')

        if creds_json:
            # 環境変数から JSON をパース
            creds_dict = json.loads(creds_json)
            credentials = Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
        else:
            # ファイルから読み込む（ローカル開発用）
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
    except json.JSONDecodeError:
        print("[ERROR] GOOGLE_CREDENTIALS が無効な JSON です")
        sys.exit(1)

def read_from_spreadsheet(spreadsheet_id, sheet_name, credentials_path):
    """Google Spreadsheet から「raw」シートを読み込む"""
    try:
        service = get_sheets_service(credentials_path)
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A:Z"
        ).execute()

        values = result.get('values', [])
        if not values:
            print(f"[ERROR] シート「{sheet_name}」にデータがありません")
            sys.exit(1)

        # ヘッダーとデータを分離
        headers = values[0]
        data = values[1:]

        # DataFrame に変換
        df = pd.DataFrame(data, columns=headers)
        print(f"[OK] Spreadsheet から {len(df)} 行を読み込みました")
        return df

    except Exception as e:
        print(f"[ERROR] Spreadsheet 読み込みエラー: {e}")
        sys.exit(1)

def get_sheet_id(service, spreadsheet_id, sheet_name):
    """シート名からシートIDを取得"""
    try:
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()

        for sheet in spreadsheet.get('sheets', []):
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']

        print(f"[ERROR] シート「{sheet_name}」が見つかりません")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] シートID取得エラー: {e}")
        sys.exit(1)

def write_to_spreadsheet(spreadsheet_id, sheet_name, result_df, credentials_path):
    """Google Spreadsheet の「cleaned」シートに書き込む"""
    try:
        service = get_sheets_service(credentials_path)

        # シートIDを取得
        sheet_id = get_sheet_id(service, spreadsheet_id, sheet_name)

        # 1. シートをクリア（古いデータを削除）
        clear_request = {
            'updateCells': {
                'range': {
                    'sheetId': sheet_id,
                },
                'fields': '*'
            }
        }
        clear_body = {'requests': [clear_request]}
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=clear_body
        ).execute()
        print("[OK] シートをクリアしました")

        # 2. 新しいデータを書き込む
        values = [result_df.columns.tolist()] + result_df.values.tolist()
        body = {'values': values}

        # DEBUG: Google Sheets に書き込む values の構造を確認
        print("=" * 60)
        print("DEBUG: values to write to Sheets")
        print("=" * 60)
        print(f"Header row: {values[0]}")
        if len(values) > 1:
            print(f"First data row: {values[1]}")
        print()

        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption='RAW',
            body=body
        ).execute()

        print(f"[OK] Spreadsheet「{sheet_name}」シートに {len(result_df)} 行を書き込みました")
        return result

    except Exception as e:
        print(f"[ERROR] Spreadsheet 書き込みエラー: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='LINE Step データを正規化')
    parser.add_argument(
        '--input',
        help='入力 CSV ファイル（Shift_JIS または UTF-8）'
    )
    parser.add_argument(
        '--output',
        help='出力 CSV ファイル（指定なしの場合は出力しない）'
    )
    parser.add_argument(
        '--spreadsheet-id',
        help='Google Spreadsheet ID'
    )
    parser.add_argument(
        '--raw-sheet',
        default='raw',
        help='入力シート名（デフォルト: raw）'
    )
    parser.add_argument(
        '--cleaned-sheet',
        default='cleaned',
        help='出力シート名（デフォルト: cleaned）'
    )
    parser.add_argument(
        '--credentials',
        default='service-account-key.json',
        help='Google Cloud サービスアカウント認証ファイル'
    )

    args = parser.parse_args()

    # モード判定
    if args.spreadsheet_id:
        # モード: Google Sheets
        print("=" * 60)
        print("Google Sheets モード")
        print("=" * 60)

        # --input が指定されている場合はローカル CSV を使用、そうでなければ Google Sheets から読み込む
        if args.input:
            print("ローカル CSV を読み込んでいます...")
            df = read_csv(args.input)
        else:
            df = read_from_spreadsheet(args.spreadsheet_id, args.raw_sheet, args.credentials)

        print("\n正規化ルール（辞書）を読み込み中...")
        dicts = load_dictionaries()
        print(f"[OK] 辞書ロード完了\n")

        print("正規化処理を実行中...")
        results = []
        unmatched_schools = {}  # 未正規化の学校名を記録
        unmatched_majors = {}   # 未正規化の専攻を記録

        for idx, row in df.iterrows():
            try:
                normalized = normalize_row(row, dicts)

                # 未正規化のデータを記録（デバッグ用）
                if normalized['school_result'].get('status') == 'unmatched':
                    school_val = get_value_from_row(row, ['学校名', '10. 現在、在学中/在学予定/在学希望の学校名（例：ハーバード大学）'])
                    if school_val:
                        unmatched_schools[school_val] = unmatched_schools.get(school_val, 0) + 1

                if normalized['major_result'].get('status') == 'unmatched':
                    major_val = get_value_from_row(row, ['専攻', '11. 現在、在学している学校での専攻（例：会計学）'])
                    if major_val:
                        unmatched_majors[major_val] = unmatched_majors.get(major_val, 0) + 1
                # 国を日本語で表示（元の入力値を使用）
                country_original = get_value_from_row(row, [
                    '国',
                    '9. 現在、在学中/在学予定/在学希望の国（例：アメリカ）',
                ])

                # 「その他（国）」がある場合はそれを優先
                country_other = get_value_from_row(row, [
                    'その他(記述).3',
                    'その他(記述).2',
                ])
                if country_other and country_other != '':
                    country_original = country_other

                # 学位を取得
                gakui = get_value_from_row(row, [
                    '学位',
                    '8. 現在の取得予定/取得済みの学位',
                ])

                # 卒業年度を取得（年と月を組み合わせて「YYYY年M月」形式）
                grad_year = get_value_from_row(row, [
                    '卒業年度',
                    '13. 最終学歴となる大学・大学院の卒業予定年 / 既卒年',
                ])
                grad_month = get_value_from_row(row, [
                    '卒業月度',
                    '14. 最終学歴となる大学・大学院の卒業予定月 / 既卒月',
                ])
                grad_date = ''
                if grad_year and grad_year != '':
                    if grad_month and grad_month != '':
                        grad_date = f"{grad_year}年{grad_month}"
                    else:
                        grad_date = f"{grad_year}年"

                # 専攻で「なし」を「未定」に統一
                major_val = get_value(normalized['major_result'].get('value', row.get('専攻', '')))
                if major_val in ['なし', '']:
                    major_val = '未定'

                # 副専攻は「なし」をそのまま保持
                minor_val = get_value(normalized['minor_major_result'].get('value', row.get('副専攻', '')))

                results.append({
                    '回答ID': get_value(row.get('回答ID', '')),
                    '回答日時': get_value(row.get('回答日時', '')),
                    '回答者ID': get_value(row.get('回答者ID', '')),
                    '性別': get_value(normalized['gender']),
                    '学位': gakui,
                    '国': country_original,
                    '学校名': get_value(normalized['school_result'].get('value', row.get('学校名', ''))),
                    '専攻': major_val,
                    '副専攻': minor_val,
                    '卒業年度': grad_date,
                    'processing_status': get_value(normalized['status'])
                })
            except Exception as e:
                print(f"  行 {idx + 2} でエラー: {e}")

        result_df = pd.DataFrame(results)
        result_df = result_df.fillna('')
        print(f"[OK] 正規化完了: {len(results)} 行\n")

        # 統計情報を表示
        status_counts = result_df['processing_status'].value_counts()
        print("=== 処理結果統計 ===")
        for status, count in status_counts.items():
            print(f"{status}: {count} 件")

        # 未正規化データの上位を表示
        if unmatched_schools:
            print("\n=== 未正規化の学校名（上位5件） ===")
            for school, count in sorted(unmatched_schools.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {school}: {count} 件")

        if unmatched_majors:
            print("\n=== 未正規化の専攻（上位5件） ===")
            for major, count in sorted(unmatched_majors.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {major}: {count} 件")

        print()

        # Google Sheets に書き込む
        write_to_spreadsheet(args.spreadsheet_id, args.cleaned_sheet, result_df, args.credentials)

    elif args.input:
        # モード: ローカル CSV
        print("=" * 60)
        print("ローカル CSV モード")
        print("=" * 60)

        result_df = process_csv(args.input, args.output)

    else:
        print("[ERROR] --input または --spreadsheet-id を指定してください")
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
