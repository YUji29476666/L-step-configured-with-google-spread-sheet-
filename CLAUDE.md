# lstep-data — プロジェクト背景・技術方針

## プロジェクト背景

LINE Step の「友達追加時アンケート」には、以下の問題がある：
- 同じ学校・専攻が複数の表記で入力されている（「東京大学」「東大」「The University of Tokyo」など）
- データ分析・統計処理の精度低下
- ユーザー情報管理が煩雑

**目的**：正規化パイプラインを構築し、自動的に表記揺れを統一する。

## 現在の状態（2026年10月16日）

✅ **Python版が完成・稼働中**
- 561行のアンケートデータを処理
- 処理結果：統一済み280件（49.9%）、要確認179件（31.9%）、未定102件（18.2%）
- Google Sheets へのリアルタイム書き込み機能搭載
- Google Sheets からの動的辞書読み込み機能実装済み

✅ **Step 4 完了**
- CSV → Google Sheets 移行スクリプト実装（migrate_csv_to_sheets.py）
- 494行のデータを Google Sheets にアップロード
- 学校名対応表：297行、専攻対応表：153行、副専攻対応表：44行

✅ **GitHub 公開完了**
- リポジトリ：https://github.com/YUji29476666/L-step-configured-with-google-spread-sheet-

🔄 **進行中**
- GAS版（Google Apps Script）実装（時間あれば実施予定）

## 技術方針

### Python版（現行）

**採用理由**：
- 柔軟な処理フロー（エンコーディング自動判定、複数入出力形式対応）
- 対応表を Google Sheets で一元管理（動的に更新可能）
- Google Sheets API を直接使用

**構成**：
- `normalize_csv.py`：メイン処理
- `rulebook.py`：正規化ロジック（言語非依存設計）
- **辞書の正本は Google Sheets** - 3シートで管理
  - 「辞書_学校名」：学校名対応表
  - 「辞書_専攻」：専攻対応表
  - 「辞書_副専攻」：副専攻対応表
- **CSV データについて**：
  - `data/` 配下の CSV は移行元として保持
  - 直接編集しない（Google Sheets に反映してから読み込み）

### GAS版（拡張予定）

**採点理由**（実装時）：
- Spreadsheet内で完結（Pythonなど環境不要）
- ユーザー（非技術者）向けに UI を提供（「実行」ボタン）
- 自動実行トリガー（定期実行）

## 実装上の重要な判断

1. **対応表の構成**
   - CSV ベース（Excel で編集可能）
   - 「統一後の値」と「表記揺れ」をカンマ区切りで記録
   - 括弧内の数字（「東京大学(19)」）は自動的に削除

2. **正規化の方針**
   - 推測・fuzzy matching は行わない
   - 対応表にない値は「要確認」として識別
   - ユーザーが後から確認・修正できる構造

3. **Google Sheets 連携**
   - サービスアカウント認証で自動化
   - 元のデータは削除せず、「cleaned」シートに出力
   - 実行ログも記録

4. **エンコーディング対応**
   - ローカル CSV：Shift_JIS / UTF-8 自動判定
   - Google Sheets：UTF-8 で統一

## データの流れ

```
L-step CSV（Shift_JIS）
   ↓
Python normalize_csv.py（エンコーディング自動判定）
   ↓
rulebook.py（対応表 CSV から辞書読み込み）
   ↓
行ごと正規化
   - 国：「その他（国）」優先
   - 学校名：対応表で統一
   - 専攻：「なし」→「未定」に統一
   - 副専攻：「なし」はそのまま保持
   - 卒業年度：YYYY年M月形式
   - processing_status：判定
   ↓
Google Sheets「cleaned」シートに書き込み
```

## 既知の課題・今後の改善

### **未対応：国別対応の学校名**

以下の学校は国によって異なる統一名を持つが、rulebook.py が「国」を使用していないため未対応：
- **モナッシュ大学**：マレーシアなら「Monash University Malaysia」、オーストラリアなら「Monash University」
- **テンプル大学**：日本なら「Temple University, Japan Campus」、アメリカなら「Temple University」
- **アジアパシフィック大学**：日本の回答でも「Asia Pacific University」に変換される（正式英語名が必要）

**対応方法**：
- rulebook.py で `normalize_school()` が country パラメータを活用するよう修正
- Google Sheets「辞書_学校名」の「国コード」列を利用した照合ロジック実装

---

## 今後の展開

### 短期（完成予定）
- ✅ Python版を GitHub に push
- ✅ Google Sheets を辞書の正本に
- 🔄 GAS版を実装
- 🔄 国別対応の学校名に対応

### 中期
- Looker Studio で可視化ダッシュボード
- 自動実行スケジューラ
- Slack 通知（処理結果）

### 長期
- 独自の正規化辞書ライブラリとしてパッケージ化
- 他のアンケートツール（Google Forms など）対応

## チーム・責任

- **実装者**：Claude Haiku 4.5 (AI Assistant)
- **ユーザー**：takebe0326@gmail.com（データ正規化責任者）
- **データソース**：LINE Step アンケートシステム

## プロジェクト参照

- **Google Sheets URL**：https://docs.google.com/spreadsheets/d/1XB9s0VI5k0t_SOnNCTBTIsBaWzbb1nnCEQl-wldGyPo/
- **GitHub リポジトリ**：https://github.com/YUji29476666/lstep-data
- **Spreadsheet ID**：`1XB9s0VI5k0t_SOnNCTBTIsBaWzbb1nnCEQl-wldGyPo`

## ライセンス

プライベートプロジェクト。本社内でのみ使用。

---

Last updated: 2026年10月15日
