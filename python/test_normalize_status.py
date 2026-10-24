#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from rulebook import normalize_status

class TestNormalizeStatus(unittest.TestCase):
    def setUp(self):
        """テスト用辞書を準備"""
        self.status_dict = {
            ('その他(記述)', '交換留学中'): '短期留学（日本の大学に在籍中）',
            ('その他(記述)', 'アメリカの大学に在学中'): '正規留学（学位取得中）',
            ('その他(記述)', 'ワーホリ中'): '語学留学・ワーホリ・Co-op など(学位なし)',
            ('その他(記述)', '留学予定なし'): '国内の学生(留学なし・検討中)',
            ('その他(記述)', '帰国子女'): '帰国子女・海外育ち',
            ('その他(記述)', '無職'): 'NA',
        }

    def test_case_1_matched_selection(self):
        """テストケース1：選択肢が「その他」以外 → 選択肢をそのまま返す（NFKC正規化後の値）"""
        result = normalize_status('正規留学（学位取得中）', '', self.status_dict)
        self.assertEqual(result['status'], 'matched')
        # normalize_text() により全角括弧が半角括弧に変換される
        self.assertEqual(result['value'], '正規留学(学位取得中)')

    def test_case_2_selection_priority_over_description(self):
        """テストケース2：既に社会人 + 記述「無職」 → 既に社会人（選択肢優先）"""
        result = normalize_status('既に社会人', '無職', self.status_dict)
        self.assertEqual(result['status'], 'matched')
        self.assertEqual(result['value'], '既に社会人')

    def test_case_3_other_with_matched_description_1(self):
        """テストケース3：その他 + 交換留学中 → 短期留学...（辞書マッチ）"""
        result = normalize_status('その他', '交換留学中', self.status_dict)
        self.assertEqual(result['status'], 'matched')
        self.assertEqual(result['value'], '短期留学（日本の大学に在籍中）')

    def test_case_4_other_with_matched_description_2(self):
        """テストケース4：その他 + アメリカの大学に在学中 → 正規留学...（辞書マッチ）"""
        result = normalize_status('その他', 'アメリカの大学に在学中', self.status_dict)
        self.assertEqual(result['status'], 'matched')
        self.assertEqual(result['value'], '正規留学（学位取得中）')

    def test_case_5_other_with_matched_description_3(self):
        """テストケース5：その他 + ワーホリ中 → 語学留学・ワーホリ...（辞書マッチ）"""
        result = normalize_status('その他', 'ワーホリ中', self.status_dict)
        self.assertEqual(result['status'], 'matched')
        self.assertEqual(result['value'], '語学留学・ワーホリ・Co-op など(学位なし)')

    def test_case_6_other_no_description(self):
        """テストケース6：その他 + 空欄 → NA（matched）"""
        result = normalize_status('その他', '', self.status_dict)
        self.assertEqual(result['status'], 'matched')
        self.assertEqual(result['value'], 'NA')

    def test_case_7_other_unmatched_description(self):
        """テストケース7：その他 + 辞書にない値 → その他（unmatched）"""
        result = normalize_status('その他', '(辞書にない新しい値)', self.status_dict)
        self.assertEqual(result['status'], 'unmatched')
        self.assertEqual(result['value'], 'その他')
        self.assertIn('辞書にない値', result.get('error', ''))

    def test_case_8_empty_status(self):
        """テストケース8：空欄ステータス → unmatched"""
        result = normalize_status('', '記述', self.status_dict)
        self.assertEqual(result['status'], 'unmatched')
        self.assertEqual(result['value'], '')

if __name__ == '__main__':
    unittest.main()
