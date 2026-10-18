# lstep-data — LINE Step アンケート正規化パイプライン

LINE Step の「友達追加時アンケート」回答データを正規化し、学校名・専攻・副専攻の表記揺れを統一して Google Sheets に出力するツール。

## 📊 機能

- **学校名の正規化**：日本語表記揺れ → 英語正式名（472個の対応ルール）
- **専攻の統一**：表記揺れを統一（149個の対応ルール）
- **副専攻の統一**：同上（38個の対応ルール）
- **ステータス追跡**：`processing_status` で「統一済み」「要確認」「未定」を識別
- **Google Sheets 連携**：Google Sheets の「cleaned」シートへ直接書き込み

## 📈 辞書管理

**辞書の正本：Google Sheets**（3シート）
- 「辞書_学校名」：472行の学校名対応表
- 「辞書_専攻」：149行の専攻対応表
- 「辞書_副専攻」：38行の副専攻対応表

**CSV について**：
- `data/` ディレクトリ配下の CSV は移行元として保持
- 直接編集しない（修正は Google Sheets で行う）

## 🚀 セットアップ

### 必要要件

- Python 3.7 以上
- pip

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/YUji29476666/lstep-data.git
cd lstep-data

# 依存パッケージをインストール
pip install -r requirements.txt

# Google API 認証ファイルを配置
# → service-account-key.json をプロジェクトルートに置く
```

### Google Sheets API 認証

1. Google Cloud Console で Sheets API を有効化
2. サービスアカウント を作成
3. サービスアカウントキー（JSON）をダウンロード
4. ファイルをプロジェクトルートに `service-account-key.json` として配置
5. Google Sheets を共有：サービスアカウントメールに編集権限を付与

## 💻 使用方法

### ローカル CSV → ローカル CSV

```bash
python python/normalize_csv.py --input data_raw.csv --output data_cleaned.csv
```

### ローカル CSV → Google Sheets

```bash
python python/normalize_csv.py \
  --spreadsheet-id "YOUR_SPREADSHEET_ID" \
  --input data_raw.csv \
  --cleaned-sheet cleaned
```

### コマンドラインオプション

```
--input FILE              入力 CSV ファイル（Shift_JIS または UTF-8）
--output FILE             出力 CSV ファイル（オプション）
--spreadsheet-id ID       Google Sheets ID（Google Sheets モードで使用）
--cleaned-sheet NAME      出力先シート名（デフォルト: cleaned）
--credentials FILE        Google API 認証ファイル（デフォルト: service-account-key.json）
```

## 📋 入出力フォーマット

### 入力 CSV の列

最小限の列：
```
回答ID, 回答日時, 回答者ID, 国, 学校名, 専攻, 副専攻
```

※ L-step からエクスポートした完全なフォーマットにも対応。長い列名も自動検出。

### 出力の列（Google Sheets「cleaned」シート）

```
回答者ID, 性別, 学位, 国, 学校名, 専攻, 副専攻, 卒業年度, processing_status
```

**各列の説明：**
- `回答者ID`：元データから変更なし
- `性別`：元データから変更なし
- `学位`：元データから変更なし
- `国`：「その他（国）」の値があればそれを優先
- `学校名`：対応表で統一。英語正式名に変換
- `専攻`：対応表で統一。「なし」は「未定」に統一
- `副専攻`：対応表で統一。「なし」はそのまま保持
- `卒業年度`：「YYYY年M月」形式で出力
- `processing_status`：統一済み / 要確認 / 未定
```

### Google Sheets API 設定

1. [Google Cloud Console](https://console.cloud.google.com/) で Sheets API を有効化
2. サービスアカウントを作成し、秘密鍵を JSON で取得
3. 対象の Google Spreadsheet をサービスアカウントのメールアドレスで共有
4. `service-account-key.json` を保存

GitHub Actions で使用する場合は、秘密鍵を GitHub Secrets (`GOOGLE_CREDENTIALS`) に登録してください。

## 使い方

### ローカルテスト（CSV ファイル）

```bash
python python/normalize_csv.py --input tests/sample_raw.csv --output output.csv
```

### Google Sheets への書き込み

```bash
python python/normalize_csv.py --spreadsheet-id "YOUR_SHEET_ID" --sheet "cleaned"
```

## ファイル構成

```
project/
├── python/
│   ├── normalize_csv.py     # メイン処理
│   └── rulebook.py          # 辞書管理
├── tests/
│   └── sample_raw.csv       # テストデータ
├── requirements.txt         # 依存ライブラリ
├── .github/
│   └── workflows/
│       └── run.yml          # GitHub Actions ワークフロー
├── README.md                # このファイル
└── .gitignore              # Git 除外設定
```

## 実装フロー

1. **Step 1**: ローカルで CSV を正規化（Google Sheets 非接続）
2. **Step 2**: Google Sheets API を追加
3. **Step 3**: GitHub Actions で手動実行
4. **Step 4**: ログ・スケジュール実行を追加

## ルール

正規化ルールは [RULEBOOK.md](../RULEBOOK.md) を参照。

- **学校名**：英語の正式名称にそろえる
- **専攻・副専攻**：日本語に統一
- **国**：選択肢値はそのまま、「その他（記述）」は辞書で統一
- **未登録値**：推測せず、`processing_status` に「要確認」と記録

## 注意事項

- 実データ（CSV）は Git にコミットしない（`.gitignore` で除外）
- 認証情報（`service-account-key.json`）は絶対にコミットしない
- テスト時は架空データ使用
