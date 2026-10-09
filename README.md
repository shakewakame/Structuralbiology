# FoldFeed（構造生物学デイリー）

構造生物学者向けのニュースレターサイト。
毎日、オープンアクセスの査読済み論文から新しい構造を報告した論文を選び、要約・グラフィカルアブストラクト・面白いポイントを紹介する。

将来は、登録したタンパク質の論文が出たらメールで知らせるアラート機能を加え、
「タンパク質を起点に研究全体が見える情報基盤」へ発展させる。

## 毎日の号

- 号の一覧：[data/issues/](data/issues/)（最初のサンプル：[2026-10-07](data/issues/2026-10-07/README.md)）
- 作り方：[.claude/skills/daily-issue/SKILL.md](.claude/skills/daily-issue/SKILL.md)（毎朝のルーティンがこの手順で号を作り、Pull Request を出す）

```bash
python3 -m pipeline.collect                 # 候補を集める（前日に Europe PMC に登録された論文）
# data/issues/<日付>/picks/<PMCID>.json を書く
python3 -m pipeline.verify 2026-10-07       # 引用・数値・文字数を検証する
python3 -m pipeline.render 2026-10-07       # 号のページとグラフィカルアブストラクトを作る
python3 -m pipeline.site                    # 全号から静的サイト site/ を生成（Qiita 風レイアウト）
```

ロゴと配色は `pipeline/brand.py`（紺＋エメラルド）。`python3 -m pipeline.brand` で `assets/logo*.svg` を再生成する。

Python 3.11 以上、標準ライブラリのみ。外部 API：Europe PMC、RCSB PDB、PDBe、UniProt。

## ドキュメント

- [決定事項](docs/decisions.md)
- [やることリスト](TODO.md)
- [編集方針メモ](docs/style-notes.md)
- [データソースと判定方法](docs/data-sources.md)
