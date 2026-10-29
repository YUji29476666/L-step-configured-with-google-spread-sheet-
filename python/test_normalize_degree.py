#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from rulebook import normalize_degree

class TestNormalizeDegree(unittest.TestCase):
    def setUp(self):
        """テスト用辞書を準備"""
        self.degree_dict = {
            ('選択肢', '学士号(4年制の学位)'): '学士号(4年制の学位)',
            ('選択肢', '修士号'): '修士号',
            ('その他(記述)', 'Bachelor of Science'): '学士号(4年制の学位)',
            ('その他(記述)', 'Master of Arts'): '修士号',
            ('その他(記述)', '無職'): 'NA',
        }

    def test_case_1_matched_selection(self):
        """テストケース1：選択肢が「その他」以外 → 選択肢をそのまま返す（NFKC正規化後の値）"""
        result = normalize_degree('学士号（4年制の学位）', '', self.degree_dict)
        self.assertEqual(result['status'], 'matched')
        # normalize_text() により全角括弧が半角括弧に変換される
        self.assertEqual(result['value'], '学士号(4年制の学位)')

    def test_case_2_selection_priority_over_description(self):
        """テストケース2：修士号 + 記述「無職」 → 修士号（選択肢優先）"""
        result = normalize_degree('修士号', '無職', self.degree_dict)
        self.assertEqual(result['status'], 'matched')
        self.assertEqual(result['value'], '修士号')

    def test_case_3_other_with_matched_description_1(self):
        """テストケース3：その他 + Bachelor of Science → 学士号...（辞書マッチ）"""
        result = normalize_degree('その他', 'Bachelor of Science', self.degree_dict)
        self.assertEqual(result['status'], 'matched')
        self.assertEqual(result['value'], '学士号(4年制の学位)')

    def test_case_4_other_with_matched_description_2(self):
        """テストケース4：その他 + Master of Arts → 修士号（辞書マッチ）"""
        result = normalize_degree('その他', 'Master of Arts', self.degree_dict)
        self.assertEqual(result['status'], 'matched')
        self.assertEqual(result['value'], '修士号')

    def test_case_5_other_no_description(self):
        """テストケース5：その他 + 空欄 → NA（matched）"""
        result = normalize_degree('その他', '', self.degree_dict)
        self.assertEqual(result['status'], 'matched')
        self.assertEqual(result['value'], 'NA')

    def test_case_6_other_unmatched_description(self):
        """テストケース6：その他 + 辞書にない値 → その他（unmatched）"""
        result = normalize_degree('その他', '(辞書にない新しい値)', self.degree_dict)
        self.assertEqual(result['status'], 'unmatched')
        self.assertEqual(result['value'], 'その他')
        self.assertIn('辞書にない値', result.get('error', ''))

    def test_case_7_empty_degree(self):
        """テストケース7：空欄学位 → unmatched"""
        result = normalize_degree('', '記述', self.degree_dict)
        self.assertEqual(result['status'], 'unmatched')
        self.assertEqual(result['value'], '')

if __name__ == '__main__':
    unittest.main()
