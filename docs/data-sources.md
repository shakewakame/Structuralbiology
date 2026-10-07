# データソースと接続確認の結果

## 接続確認（2026-10-07、開発環境から）

| ホスト | 用途 | 結果 |
|---|---|---|
| `www.ebi.ac.uk` | Europe PMC（論文検索・全文XML・ライセンス）、PDBe API | OK |
| `data.rcsb.org` | RCSB PDB Data API（手法・分解能・リガンド・UniProt対応） | OK |
| `files.rcsb.org` | PDB 座標ファイル（構造図の描画用） | OK |
| `rest.uniprot.org` | UniProt（遺伝子名・別名・機能） | OK（一時的な 503 が出ることがあるので再試行を入れる） |
| `api.crossref.org` | Crossref（公開当日の論文検出・ライセンス） | OK |
| `search.rcsb.org` | RCSB Search API | 接続不可（必須ではない。PDBe の UniProt→PDB 対応表で代用できる） |
| `cdn.rcsb.org` | RCSB の構造画像 | 接続不可（不要。構造図は座標から自前で描く） |
| `api.biorxiv.org` | bioRxiv | 接続不可（bioRxiv 対応時に許可する） |

本番の毎日の実行は GitHub Actions 上で行うため、上の制限は開発環境だけの話。

## 論文数の実測（Europe PMC、査読済み・オープンアクセス）

### 2026年9月の1ヶ月

| 条件 | 件数 |
|---|---|
| 構造キーワード（cryo-EM / crystal structure など） | 1,694 |
| 構造キーワード＋本文に PDB ID（Europe PMC の自動抽出） | 385 |

- 385 件のライセンス：CC BY 293 件（76%）、CC BY-NC 41 件、CC BY-NC-ND 50 件、なし 1 件
- 主なジャーナル：IJMS、Protein Science、Science Advances、NAR、Nature Communications、PNAS、Advanced Science など
- 化学・材料系の「crystal structure」や、既存の PDB 構造を使ったドッキング研究も多く含まれる。新しい構造を報告した論文を見分ける判定が必要。

### 毎日の候補数（索引日 `FIRST_IDATE` 基準、2026-09-21〜10-06）

構造キーワード＋「Protein Data Bank / PDB ID / accession code / EMDB」を含む論文は **1日あたり 0〜95 件、多くの日は 10〜40 件**。ピックアップ 3 本には十分な母数がある。

## 運用上の注意点（実測から分かったこと）

1. **Europe PMC の PDB ID 自動抽出は数週間遅れる。** 直近数日の論文は抽出結果が空なので、毎日の処理では本文 XML から自前で PDB / EMDB ID を抜き出す。
2. **公開日ではなく索引日で取得する。** 公開日で検索すると、Europe PMC への登録が遅れた論文を取りこぼす。
3. **Europe PMC への登録の遅れはジャーナルによって違う。** 中央値は 3 日。Nature Communications・Science Advances・eLife・PNAS は約 1 日、NAR は約 17 日。遅いジャーナルは Crossref で公開当日に見つけて補う（NAR は Crossref でライセンス情報付きで取得できることを確認）。
4. **同じジャーナルでもライセンスが論文ごとに違う**（例：Nature Communications にも CC BY-NC-ND の論文がある）。ライセンスは論文ごとに判定する。
