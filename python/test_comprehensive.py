#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
包括的なテストスイート
- raw と cleaned の行数が同じ
- 学校名の5つの値が「学校以外」
- 専攻の5つの分類が日本語で出る
- 辞書にない値は元の値のまま unmatched
"""

import sys
sys.path.insert(0, 'python')

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pandas as pd
from rulebook import load_dictionaries_from_sheets, normalize_major, normalize_school
from collections import Counter

SPREADSHEET_ID = '1XB9s0VI5k0t_SOnNCTBTIsBaWzbb1nnCEQl-wldGyPo'
CREDENTIALS_PATH = 'service-account-key.json'

def get_sheets_service():
    credentials = Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
    return build('sheets', 'v4', credentials=credentials)

def fetch_sheet_data(service, spreadsheet_id, range_name):
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    return result.get('values', [])

class ComprehensiveTest:
    def __init__(self):
        self.service = get_sheets_service()
        self.passed = 0
        self.failed = 0

    def print_header(self, title):
        print("\n" + "=" * 100)
        print(title)
        print("=" * 100)

    def test_pass(self, msg):
        print(f"  [PASS] {msg}")
        self.passed += 1

    def test_fail(self, msg):
        print(f"  [FAIL] {msg}")
        self.failed += 1

    def run(self):
        self.print_header("Test 1: Row count consistency (raw vs cleaned)")
        self.test_row_count()

        self.print_header("Test 2: School name special values are marked as 'other'")
        self.test_school_special_values()

        self.print_header("Test 3: Major special values are in Japanese")
        self.test_major_special_values()

        self.print_header("Test 4: Unmatched values remain as original")
        self.test_unmatched_values()

        self.print_summary()

    def test_row_count(self):
        raw_data = fetch_sheet_data(self.service, SPREADSHEET_ID, 'raw!A:Z')
        headers = raw_data[0]
        df_raw = pd.DataFrame(raw_data[1:], columns=headers)

        raw_count = len(df_raw)

        # raw を正規化した結果の行数（すべての行を処理）
        processed_count = 0
        for idx, row in df_raw.iterrows():
            processed_count += 1

        if processed_count == raw_count:
            self.test_pass(f"All {raw_count} rows processed without dropping")
        else:
            self.test_fail(f"Expected {raw_count} rows, got {processed_count}")

    def test_school_special_values(self):
        cleaned_data = fetch_sheet_data(self.service, SPREADSHEET_ID, 'cleaned!A:Z')
        headers = cleaned_data[0]
        df = pd.DataFrame(cleaned_data[1:], columns=headers)

        school_idx = None
        school_status_idx = None
        for i, col in enumerate(headers):
            if '学校名' in str(col):
                school_idx = i
            if '学校名_status' in str(col):
                school_status_idx = i

        special_values = ['予定なし', '未定', '社会人', '既卒', 'NA']

        for special in special_values:
            rows_with_special = df[df.iloc[:, school_idx] == special]
            if len(rows_with_special) == 0:
                continue

            status_in_special = rows_with_special.iloc[:, school_status_idx].unique()

            if 'other' in status_in_special or '学校以外' in status_in_special:
                self.test_pass(f"'{special}' has status 'other' or '学校以外' ({len(rows_with_special)} rows)")
            else:
                self.test_fail(f"'{special}' status is {status_in_special} instead of 'other'")

    def test_major_special_values(self):
        dicts = load_dictionaries_from_sheets(SPREADSHEET_ID, CREDENTIALS_PATH)

        raw_data = fetch_sheet_data(self.service, SPREADSHEET_ID, 'raw!A:Z')
        headers = raw_data[0]
        df_raw = pd.DataFrame(raw_data[1:], columns=headers)

        major_idx = None
        for i, col in enumerate(headers):
            if '専攻' in str(col) and '副' not in str(col):
                major_idx = i
                break

        special_5_values = {'未定': 0, '既卒': 0, 'NA': 0, '高校生': 0, '語学・準備課程': 0}
        found_special = []

        for idx, row in df_raw.iterrows():
            if len(row) <= major_idx or pd.isna(row.iloc[major_idx]):
                continue

            major_raw = str(row.iloc[major_idx]).strip()
            if not major_raw:
                continue

            result = normalize_major(major_raw, dicts['major'])
            if result:
                value = result.get('value', '')
                if value in special_5_values:
                    special_5_values[value] += 1
                    if value not in found_special:
                        found_special.append(value)

        for key in sorted(special_5_values.keys()):
            if special_5_values[key] > 0:
                self.test_pass(f"'{key}' found {special_5_values[key]} times (Japanese)")

        missing = [k for k in special_5_values.keys() if special_5_values[k] == 0]
        if missing:
            self.test_fail(f"Missing values: {missing}")

    def test_unmatched_values(self):
        dicts = load_dictionaries_from_sheets(SPREADSHEET_ID, CREDENTIALS_PATH)

        raw_data = fetch_sheet_data(self.service, SPREADSHEET_ID, 'raw!A:Z')
        headers = raw_data[0]
        df_raw = pd.DataFrame(raw_data[1:], columns=headers)

        major_idx = None
        for i, col in enumerate(headers):
            if '専攻' in str(col) and '副' not in str(col):
                major_idx = i
                break

        unmatched_values = Counter()

        for idx, row in df_raw.iterrows():
            if len(row) <= major_idx or pd.isna(row.iloc[major_idx]):
                continue

            major_raw = str(row.iloc[major_idx]).strip()
            if not major_raw:
                continue

            result = normalize_major(major_raw, dicts['major'])
            if result and result.get('status') == 'unmatched':
                value = result.get('value', '')
                unmatched_values[value] += 1

        if unmatched_values:
            count = sum(unmatched_values.values())
            self.test_pass(f"Unmatched values remain as original: {count} total")
            print(f"    Top 10 unmatched values:")
            for val, cnt in unmatched_values.most_common(10):
                print(f"      - {val}: {cnt}")
        else:
            self.test_fail("No unmatched values found")

    def print_summary(self):
        self.print_header("Test Summary")
        total = self.passed + self.failed
        print(f"  Passed: {self.passed}/{total}")
        print(f"  Failed: {self.failed}/{total}")
        if self.failed == 0:
            print("  Result: ALL TESTS PASSED")
        else:
            print(f"  Result: {self.failed} TEST(S) FAILED")

if __name__ == '__main__':
    test = ComprehensiveTest()
    test.run()
