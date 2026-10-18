#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unicodedata
import re
import pandas as pd
import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def normalize_text(text):
    """テキストを正規化（Unicode NFKC + 空白整理）"""
    if not text or pd.isna(text):
        return ''

    text = str(text).strip()
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def load_dictionaries_from_csv():
    """CSV ファイルから辞書を読み込む"""
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    dicts = {
        'country': {
            '日本': 'JP',
            'アメリカ': 'US',
            'カナダ': 'CA',
            'オーストラリア': 'AU',
            'マレーシア': 'MY',
            'シンガポール': 'SG',
            'タイ': 'TH',
            'インド': 'IN',
            '中国': 'CN',
            '韓国': 'KR',
            'イギリス': 'GB',
            'フランス': 'FR',
            'ドイツ': 'DE',
            'オランダ': 'NL',
            'スイス': 'CH',
            'ニュージーランド': 'NZ',
            '南アフリカ': 'ZA',
        },
        'school': {'JP': {}, 'CA': {}, 'US': {}, 'MY': {}, 'AU': {}, 'Other': {}},
        'major': {}
    }

    # 学校名の辞書を読み込み
    school_csv = os.path.join(base_path, 'data', 'school_mapping.csv')
    if os.path.exists(school_csv):
        df = pd.read_csv(school_csv, encoding='utf-8')
        for _, row in df.iterrows():
            unified = normalize_text(row.get('統一後の値', ''))
            variants_str = str(row.get('まとめられる元の値(すべて)', ''))

            if unified and variants_str and not pd.isna(variants_str):
                # 括弧内の数字を削除して表記揺れを抽出
                # 例：「早稲田大学(19)、慶應大学」 → 「早稲田大学」「慶應大学」
                variants = re.sub(r'\(\d+\)', '', variants_str)
                for variant in variants.split('、'):
                    variant = normalize_text(variant)
                    if variant:
                        # キー: 日本語の表記揺れ, 値: 統一後の英語名
                        dicts['school']['Other'][variant] = unified

    # 専攻の辞書を読み込み
    major_csv = os.path.join(base_path, 'data', 'major_mapping.csv')
    if os.path.exists(major_csv):
        df = pd.read_csv(major_csv, encoding='utf-8')
        for _, row in df.iterrows():
            unified = normalize_text(row.get('統一後の値', ''))
            variants_str = str(row.get('まとめられる元の値(すべて)', ''))

            if unified and variants_str and not pd.isna(variants_str):
                # 括弧内の数字を削除して表記揺れを抽出
                variants = re.sub(r'\(\d+\)', '', variants_str)
                variant_list = []
                for variant in variants.split('、'):
                    variant = normalize_text(variant)
                    if variant:
                        variant_list.append(variant)

                if variant_list:
                    dicts['major'][unified] = variant_list

    # 副専攻の辞書を読み込み
    minor_csv = os.path.join(base_path, 'data', 'minor_major_mapping.csv')
    if os.path.exists(minor_csv):
        df = pd.read_csv(minor_csv, encoding='utf-8')
        for _, row in df.iterrows():
            unified = normalize_text(row.get('統一後の値', ''))
            variants_str = str(row.get('まとめられる元の値(すべて)', ''))

            # 副専攻は major_dict と同じ構造を使用
            if pd.isna(unified) or unified == '':
                unified = ''  # 空欄を保持

            if variants_str and not pd.isna(variants_str):
                # 括弧内の数字を削除して表記揺れを抽出
                variants = re.sub(r'\(\d+\)', '', variants_str)
                variant_list = []
                for variant in variants.split('、'):
                    variant = normalize_text(variant)
                    if variant:
                        variant_list.append(variant)

                if variant_list:
                    if unified not in dicts['major']:
                        dicts['major'][unified] = variant_list

    return dicts

def load_dictionaries_from_sheets(spreadsheet_id, credentials_path=None):
    """Google Sheets から辞書を読み込む"""
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

        dicts = {
            'country': {
                '日本': 'JP', 'アメリカ': 'US', 'カナダ': 'CA', 'オーストラリア': 'AU',
                'マレーシア': 'MY', 'シンガポール': 'SG', 'タイ': 'TH', 'インド': 'IN',
                '中国': 'CN', '韓国': 'KR', 'イギリス': 'GB', 'フランス': 'FR',
                'ドイツ': 'DE', 'オランダ': 'NL', 'スイス': 'CH', 'ニュージーランド': 'NZ',
                '南アフリカ': 'ZA', '台湾': 'TW',
                'スウェーデン': 'SE', 'ノルウェー': 'NO', 'フィリピン': 'PH',
            },
            'school': {'JP': {}, 'CA': {}, 'US': {}, 'MY': {}, 'AU': {}, 'Other': {}},
            'major': {}
        }

        # Google Sheets から学校名対応表を読み込む（国コード対応）
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='辞書_学校名!A2:C'
            ).execute()
            values = result.get('values', [])

            for row in values:
                if len(row) >= 2:
                    variant = normalize_text(row[0])
                    unified = normalize_text(row[1])
                    country_code = normalize_text(row[2]) if len(row) >= 3 else ''

                    if variant and unified:
                        # キー: (元の値, 国コード) → 値: 統一後の名前
                        key = (variant, country_code)
                        dicts['school']['Other'][key] = unified

            print(f"[OK] Google Sheets から {len(values)} 件の学校名対応表を読み込みました")
        except Exception as e:
            print(f"[WARN] 学校名対応表の読み込みエラー: {e}")

        # Google Sheets から専攻対応表を読み込む
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='辞書_専攻!A2:B'
            ).execute()
            values = result.get('values', [])

            for row in values:
                if len(row) >= 2:
                    variant = normalize_text(row[0])
                    unified = normalize_text(row[1])
                    if variant and unified:
                        if unified not in dicts['major']:
                            dicts['major'][unified] = []
                        dicts['major'][unified].append(variant)

            print(f"[OK] Google Sheets から {len(values)} 件の専攻対応表を読み込みました")
        except Exception as e:
            print(f"[WARN] 専攻対応表の読み込みエラー: {e}")

        return dicts

    except Exception as e:
        print(f"[ERROR] Google Sheets 読み込みエラー: {e}")
        raise

def load_dictionaries(use_sheets=False, spreadsheet_id=None, credentials_path=None):
    """辞書を読み込む

    Args:
        use_sheets: True の場合 Google Sheets から、False の場合 CSV から読み込む
        spreadsheet_id: Google Sheets を使う場合の Spreadsheet ID
        credentials_path: Google Cloud 認証ファイルのパス
    """
    if use_sheets and spreadsheet_id:
        return load_dictionaries_from_sheets(spreadsheet_id, credentials_path)
    else:
        return load_dictionaries_from_csv()

def normalize_country(value, country_dict):
    """国を正規化"""
    value = normalize_text(value)

    if not value or value == '':
        return {'status': 'unmatched', 'value': value, 'error': '空欄'}

    # 特殊値：「留学の予定なし」はそのまま返す
    if value == '留学の予定なし':
        return {'status': 'matched', 'value': '留学の予定なし'}

    # 直接マッチ
    if value in country_dict:
        return {'status': 'matched', 'value': country_dict[value]}

    # 複合フォーマット：「その他 + 国名」形式から国名を抽出
    # 例：「その他 + チェコ共和国」→ 「チェコ」と抽出して辞書で検索
    if value.startswith('その他'):
        # 「その他」を削除して残りの部分を抽出
        remaining = re.sub(r'^その他[\s+]*', '', value).strip()

        if remaining:
            # 残りの文字列が「XX共和国」「XX王国」など長い形式の場合、短い形式を抽出
            # 例：「チェコ共和国」→ 「チェコ」
            short_name = re.sub(r'(共和国|王国|合衆国|連邦)$', '', remaining)

            # 短い名前で辞書検索
            if short_name in country_dict:
                return {'status': 'matched', 'value': country_dict[short_name]}

            # 元の名前で辞書検索
            if remaining in country_dict:
                return {'status': 'matched', 'value': country_dict[remaining]}

            # どちらもマッチしないなら、抽出した名前をそのまま返す
            return {'status': 'unmatched', 'value': short_name, 'error': '辞書にない値'}

    # 複数の国が書かれている場合（カンマ区切り）
    if '、' in value or ',' in value:
        return {'status': 'matched', 'value': value}

    # マッチなし — 日本語のまま返す（国名を出力値として使用）
    return {'status': 'unmatched', 'value': value, 'error': '辞書にない値'}

def normalize_school(value, school_dict, country=None):
    """学校名を英語正式名に正規化（国別対応）"""
    value = normalize_text(value)

    if not value or value == '':
        return {'status': 'unmatched', 'value': value, 'error': '空欄'}

    # ルール2：正式名がそのまま入力された場合を matched に
    # 辞書の統一後の値と完全一致する場合、そのまま返す
    for key, unified in school_dict.items():
        if isinstance(key, tuple):
            # (variant, country) タプルの場合
            variant, key_country = key
            if unified == value:
                return {'status': 'matched', 'value': value}
        else:
            # 古い形式の場合（互換性のため）
            if unified == value:
                return {'status': 'matched', 'value': value}

    # 大学名ではないもの
    if value in ['大学', '留学済み', '卒業後', 'なし']:
        return {'status': 'matched', 'value': 'なし'}

    if value in ['未定', '考え中']:
        return {'status': 'matched', 'value': '未定'}

    # 複数学校が書かれている場合
    if '、' in value or '/' in value or '→' in value or '・' in value:
        schools = re.split(r'[、/→・]', value)
        schools = [s.strip() for s in schools if s.strip()]

        unified_schools = []
        all_matched = True

        for school in schools:
            school = normalize_text(school)

            # 説明を削除
            school = re.sub(r'[（(].*?[）)]', '', school).strip()
            school = re.sub(r'(留学|交換|在学|編入|卒業|に|国内|現在|予定)', '', school).strip()

            matched = False

            # Step 1: (学校名, country_code) で検索 ← 国別ルール優先
            if country:
                key_with_country = (school, country)
                if key_with_country in school_dict:
                    unified_schools.append(school_dict[key_with_country])
                    matched = True

            # Step 2: (学校名, '') で検索 ← 共通ルール
            if not matched:
                key_without_country = (school, '')
                if key_without_country in school_dict:
                    unified_schools.append(school_dict[key_without_country])
                    matched = True

            if not matched and school not in ['大学', '留学済み', 'なし']:
                all_matched = False

        if unified_schools:
            return {
                'status': 'matched' if all_matched else 'partial',
                'value': ' / '.join(unified_schools)
            }

    # 単一学校の場合
    matched = False
    unified_value = None

    # Step 1: (学校名, country_code) で検索 ← 国別ルール優先
    if country:
        key_with_country = (value, country)
        if key_with_country in school_dict:
            unified_value = school_dict[key_with_country]
            matched = True

    # Step 2: (学校名, '') で検索 ← 共通ルール
    if not matched:
        key_without_country = (value, '')
        if key_without_country in school_dict:
            unified_value = school_dict[key_without_country]
            matched = True

    if matched:
        return {'status': 'matched', 'value': unified_value}

    # マッチなし
    return {'status': 'unmatched', 'value': value, 'error': '辞書にない値'}

def normalize_major(value, major_dict):
    """専攻・副専攻を日本語に統一"""
    value = normalize_text(value)

    if not value or value == '':
        return {'status': 'unmatched', 'value': '', 'error': '空欄'}

    # 「なし」「未定」などの特殊値
    if value in ['なし', '無し']:
        import pandas as pd
        return {'status': 'matched', 'value': pd.NA}

    if value in ['未定', 'わからない', '分からない', '考え中', '勉強']:
        return {'status': 'matched', 'value': '未定'}

    # ルール2：正式名がそのまま入力された場合を matched に
    # 辞書の統一後の値と完全一致する場合、そのまま返す
    if value in major_dict:
        return {'status': 'matched', 'value': value}

    # 複数値が書かれている場合
    if any(sep in value for sep in ['、', ',', '/', '・', 'and', '&']):
        parts = re.split(r'[、,/・&]|and', value)
        parts = [p.strip() for p in parts if p.strip()]

        unified_majors = []
        all_matched = True

        for part in parts:
            part = normalize_text(part)

            # 学部と学科が両方含まれている場合は自動変換しない（要確認のままにする）
            if '学部' in part and '学科' in part:
                all_matched = False
                if part:
                    unified_majors.append(part)
                continue

            # 「学部」「学科」を「学」に置き換え（例：商学部 → 商学）
            part = re.sub(r'学部$', '学', part).strip()
            part = re.sub(r'学科$', '学', part).strip()
            # 末尾の「専攻」を削除
            part = re.sub(r'専攻$', '', part).strip()

            # 括弧内を削除
            part = re.sub(r'[（(].*?[）)]', '', part).strip()

            # 直接マッチ
            if part in major_dict:
                unified_majors.append(part)
            else:
                # 表記揺れマッチ
                matched = False
                for unified_name, variants in major_dict.items():
                    if part in variants:
                        unified_majors.append(unified_name)
                        matched = True
                        break

                if not matched and part:
                    all_matched = False

        if unified_majors:
            return {
                'status': 'matched' if all_matched else 'partial',
                'value': ' / '.join(unified_majors)
            }

    # 単一値
    # 学部と学科が両方含まれている場合は自動変換しない
    if '学部' in value and '学科' in value:
        return {'status': 'unmatched', 'value': value, 'error': '学部と学科の複合形'}

    # 「学部」「学科」を「学」に置き換え（例：商学部 → 商学 → 辞書で「商学」に統一）
    clean_value = re.sub(r'学部$', '学', value).strip()
    clean_value = re.sub(r'学科$', '学', clean_value).strip()
    # 末尾の「専攻」を削除（例：電気工学専攻 → 電気工学）
    clean_value = re.sub(r'専攻$', '', clean_value).strip()

    # 直接マッチ
    if clean_value in major_dict:
        return {'status': 'matched', 'value': clean_value}

    # 表記揺れマッチ
    for unified_name, variants in major_dict.items():
        if clean_value in variants:
            return {'status': 'matched', 'value': unified_name}

    # マッチなし
    return {'status': 'unmatched', 'value': value, 'error': '辞書にない値'}

def get_value_from_row(row, column_names):
    """複数の列名候補から値を取得"""
    for col_name in column_names:
        if col_name in row.index and pd.notna(row[col_name]):
            return row[col_name]
    return ''

def determine_status(result):
    """processing_status を判定（項目別）"""
    # 1 つでも要確認があれば「要確認」
    confirm_items = [
        result.get('country_result', {}).get('status'),
        result.get('school_result', {}).get('status'),
        result.get('major_result', {}).get('status'),
        result.get('minor_major_result', {}).get('status'),
    ]

    if 'unmatched' in confirm_items or 'error' in confirm_items:
        return '要確認'

    # 1 つでも「未定」の値があれば「未定」
    undefined_items = [
        result.get('major_result', {}).get('value'),
        result.get('minor_major_result', {}).get('value'),
    ]

    if '未定' in undefined_items:
        return '未定'

    # それ以外は統一済み
    return '統一済み'
