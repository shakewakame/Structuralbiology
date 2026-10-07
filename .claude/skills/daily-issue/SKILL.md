---
name: daily-issue
description: 構造生物学デイリーの毎日の号を作る。前日に Europe PMC に登録されたオープンアクセス論文を集め、新しい構造を報告した論文から 3 本を選んで記事を書き、検証・描画して Pull Request を出す。毎朝のルーティンや「今日の号を作って」「YYYY-MM-DD の号を作って」と頼まれたときに使う。
---

# 毎日の号を作る

構造生物学者向けのニュースレター。毎日、査読済みのオープンアクセス論文から新しい構造を報告した論文を選び、
要約・面白い点・実験メモ・グラフィカルアブストラクトを付けて紹介する。

**原則：数値・ID・リガンド・生物種は PDB / UniProt から機械的に取得し、手で書かない。
AI が書く文章の主張には、論文本文からの逐語引用を必ず付ける。**

## 手順

日付は特に指定がなければ、号の日付＝今日（日本時間）、対象＝昨日（UTC）に Europe PMC に登録された論文。

1. **ブランチを作る**
   ```bash
   ISSUE=$(TZ=Asia/Tokyo date +%F)
   git checkout -b claude/issue-$ISSUE
   ```

2. **候補を集める**（2〜5 分）
   ```bash
   python3 -m pipeline.collect            # 日付を指定する場合: --index-date 2026-10-06 --issue-date 2026-10-07
   ```
   `data/issues/$ISSUE/candidates.md` に候補一覧、`.cache/packets/<PMCID>.md` に各論文の本文ができる。

3. **編集者のフィードバックを読む**：`docs/style-notes.md` を読み、そこに書かれた方針に従う。
   GitHub のツールが使える場合は、直近の号の Pull Request に付いたオーナーのコメントも読み、
   今後も守るべき指摘があれば `docs/style-notes.md` に追記する（この号の PR に含める）。

4. **3 本選ぶ**：`candidates.md` を読み、下の「選び方」に従って選ぶ。特に目覚ましい論文があれば
   最大 5 本まで増やしてよい（`config/editorial.json` の `max_picks_per_day`）。
   新しい構造の候補が 3 本に満たない日は、ある分だけでよい。0 本なら記事は書かず、手順 7 へ。

5. **記事を書く**：選んだ論文ごとに `.cache/packets/<PMCID>.md` を**全体に目を通して**から
   `data/issues/$ISSUE/picks/<PMCID>.json` を書く。形式は `pipeline/schema.py` の `EXAMPLE`、
   書き方は下の「書き方」。既存の例：`data/issues/2026-10-07/picks/`。
   本文を読んで「実は既存構造を使っただけ」と分かった論文は選ばず、PR の本文にそう書く。

6. **検証する**
   ```bash
   python3 -m pipeline.verify $ISSUE
   ```
   `[NG]` が出たら直して、全部 `[OK]` になるまで繰り返す。引用が見つからないときは、
   packet から一字一句コピーし直す（言い換え・省略・つなぎ合わせは不可）。

7. **描画する**
   ```bash
   python3 -m pipeline.render $ISSUE
   ```
   `data/issues/$ISSUE/README.md`（号のページ）と `ga/<PMCID>.svg`（グラフィカルアブストラクト）ができる。

8. **コミットして PR を出す**
   ```bash
   git add data/issues/$ISSUE docs/style-notes.md
   git commit -m "Add issue $ISSUE"
   git push -u origin claude/issue-$ISSUE
   ```
   PR はリポジトリのデフォルトブランチに向けて作る。タイトル：`構造生物学デイリー $ISSUE 号`。
   本文には、選んだ論文の見出し、号のページへのリンク、候補数（`candidates.json` の `counts`）、
   選ばなかった有力候補とその理由、`editor_notes` の要約を書く。
   `config/editorial.json` の `review_required` が `true` の間は**マージしない**（編集者が確認してマージする）。
   `false` なら、検証が通っていればマージする。

## 選び方

- 対象は `kind` が `new_structure`・`new_structure_ids_unlisted`・`new_map_only` の論文だけ。
  `uses_existing`（既存構造を使ったドッキングなど）と `no_ids` は選ばない。
- 優先する順：
  1. **初構造**：そのタンパク質・複合体で初めての構造（`first_structure` が true、または論文が明言）
  2. **機構の解明**：構造変化・複数状態・触媒機構など、構造から「なぜ・どうやって」が分かる
  3. **創薬・モダリティ**：阻害剤・抗体・ペプチド・分解誘導剤などとの複合体
  4. **手法の工夫**：時分割、in situ、新しい安定化法など、他の研究者がまねできる工夫
  5. 生物学的に広く関心を集めるテーマ（病原体、ヒトの疾患関連、大型複合体）
- 3 本のテーマが偏らないようにする（同じタンパク質ファミリーばかり、手法がすべて同じ、を避ける）。
- 本文が途中で切れている（`[... truncated ...]`）論文は、必要な部分が読めているときだけ選ぶ。

## 書き方

- **常体（だ・である調）**で簡潔に。体言止めも可。読者は構造生物学者なので、基本用語は説明しない。
- 用語は日本語の定訳＋必要なら略称（クライオ電顕、副溝、膜貫通ヘリックス）。タンパク質名・遺伝子名・
  残基番号・化合物名は論文の表記に従う。
- **数値**は論文本文か PDB にあるものだけ書く。分解能を書くときは PDB の値を優先する。
- **誇張しない**。「初めて」は `first_structure` が true か論文が明言している場合だけ。
  著者の解釈・推測は「〜と考えられる」「〜を示唆する」と書き分ける。著者自身が書いている限界
  （人工コンストラクトである、分解能が低い部分がある等）は省かない。
- 各フィールドの役割と上限文字数（`pipeline/schema.py` の `LIMITS`）：
  - `headline`（60 字）：何の構造が出て、何が分かったか
  - `takeaway`（48 字）：グラフィカルアブストラクトに大きく載る一番の発見。主語と発見を 1 文で
  - `target_label`（30 字）：標的の短い表記（例：`SpNanR（肺炎球菌）`）
  - `summary.background / approach / findings`（140 / 140 / 160 字）：3 行要約
  - `highlights`（1〜3 個、各 200 字）：タグは `初構造・新しい結合部位・機構の解明・創薬・モダリティ・手法の工夫・実験Tips`
  - `lab_notes`（各 160 字）：Methods に書いてあることだけ。書いていない項目は `null`
- **evidence（根拠の引用）**：highlights の各項目に 1〜2 個、lab_notes に必要な数だけ。
  packet から**英語のまま一字一句**コピーした 20 字以上の連続した文（1〜2 文）。`section` には見出し名を書く。
- グラフィカルアブストラクト用の任意項目：
  - `ligand_label`：結合分子を略号（BMX など）ではなく分かる名前で（例：`ManNAc-6-P（BMX）`）
  - `method_label`：PDB 情報がない論文（ID が補足資料のみ）で、本文にある手法と分解能（例：`クライオ電顕・全体 2.8 Å`）
  - `ga_pdb_id`：構造図に使う PDB ID（省略時は最高分解能の構造）。論文の主張を一番よく表す構造を選ぶ
  - `legend_labels`：構造図の色の凡例名を entity の順に上書き
- `editor_notes`：確信が持てない点、分類の判断、編集者に見てほしい点。

## ファイル

| パス | 内容 | 書くのは |
|---|---|---|
| `data/issues/<日付>/candidates.json` / `.md` | 候補と PDB・UniProt の事実 | `pipeline.collect` |
| `data/issues/<日付>/picks/<PMCID>.json` | 記事の文章 | 執筆者（Claude） |
| `data/issues/<日付>/README.md`、`ga/*.svg` | 号のページと図 | `pipeline.render` |
| `.cache/` | 本文 XML・packet・座標（コミットしない） | パイプライン |
| `docs/style-notes.md` | 編集者からの方針・フィードバックの蓄積 | 執筆者が追記 |
