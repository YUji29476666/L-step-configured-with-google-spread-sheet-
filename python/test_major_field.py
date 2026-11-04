#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from rulebook import load_dictionaries
from normalize_csv import get_major_field

class TestMajorField(unittest.TestCase):
    """Test major field assignment"""

    @classmethod
    def setUpClass(cls):
        # Load dictionaries
        cls.dicts = load_dictionaries(use_sheets=False)
        cls.major_field = cls.dicts.get('major_field', {})

    def test_accounting_to_business(self):
        """Accounting should map to ビジネス"""
        result = get_major_field('Accounting', self.major_field)
        self.assertEqual(result, 'ビジネス')

    def test_accounting_finance_to_business(self):
        """Accounting / Finance should map to ビジネス"""
        result = get_major_field('Accounting / Finance', self.major_field)
        self.assertEqual(result, 'ビジネス')

    def test_economics_computer_science_to_multiple(self):
        """Economics / Computer Science should map to 複数分野"""
        result = get_major_field('Economics / Computer Science', self.major_field)
        self.assertEqual(result, '複数分野')

    def test_undefined_to_non_major(self):
        """未定 should map to 専攻以外"""
        result = get_major_field('未定', self.major_field)
        self.assertEqual(result, '専攻以外')

if __name__ == '__main__':
    unittest.main()
