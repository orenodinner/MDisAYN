# MDisAYN

Windows 11 / Python 3.11+ 向けの「ローカル情報 → LLM整形 → Obsidianへ自動記録」ツール。現状は P0 として、Windowsフォルダ監視 → 抽出 → LM Studio 正規化 → Obsidian Source Card 出力まで実装しています。

## 特徴（P0）
- 複数フォルダ監視（再帰） + デバウンス + 定期スキャン
- 主要なテキスト拡張子の抽出
- LM Studio の OpenAI互換API（`chat/completions`）で正規化
- Obsidian Vault へ Source Card を書き込み
- Data Lake（raw/・extracted/・meta.db）

## セットアップ
```powershell

.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`.env.example` を `.env` にコピーしてパスなどを編集:
```powershell
copy .env.example .env
```

LM Studio の OpenAI互換サーバーを起動しておく必要があります:
- `http://127.0.0.1:1234/v1`

## 実行（P0）
```powershell
python -m app.cli run
```

一括取り込み:
```powershell
python -m app.cli backfill
```

ステータス:
```powershell
python -m app.cli status
```

## Data Lake 構成
```
./data_lake/
  raw/file/
  extracted/file/
  meta.db
```

## Obsidian 出力
Source Card は以下に出力されます:
```
./vault/90_Sources/file/
```

## 注意点
- P0 ではテキスト系ファイルのみ対象です。
- Obsidian に書き込む内容は日本語（`LLM_LANGUAGE=ja`）をデフォルトとします。
- 同一内容はハッシュで重複排除し、強制指定がない限り再処理しません。　
