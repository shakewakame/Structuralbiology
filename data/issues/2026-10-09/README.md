# 構造生物学デイリー（仮） 2026-10-09

Europe PMC に 2026-10-07 に登録されたオープンアクセス論文 33 本のうち、新しい構造を報告した論文は 4 本。そこから 3 本を紹介する。

> この号は AI が論文本文から作成した**レビュー用の下書き**です。数値・ID・リガンドは PDB / UniProt から取得し、AI の記述には本文からの引用を付けています。

## 1. 抗ファージ防御系QatBCの結晶構造：QatBのN末端がQatC活性部位に挿入され、防御に必須だった

![グラフィカルアブストラクト](ga/PMC13639016.svg)

**Structural and functional insights into QueC-family protein in QatABCD anti-phage system**  
*Nature Communications*（2026-01-01） · [論文](https://doi.org/10.1038/s41467-026-77369-4) · ライセンス: cc by-nc-nd

### 3行要約

- **背景**：QatABCDは広く分布する抗ファージ防御系で、QueC型タンパク質QatCが特徴的な構成要素だが、作用機構もQatCの機能も不明だった。
- **やったこと**：QatBCD複合体を共発現で調製し、QatBC複合体のapo型とATP結合型を結晶構造解析した。変異体はファージプラークアッセイで防御能を評価した。
- **分かったこと**：QatBのN末端ループがQatCの活性部位に挿入される。活性中心、亜鉛結合部位、QatB N末端、QatB-QatC界面の変異はいずれも防御能を下げた。QatDは柔軟に結合する。

### ここが面白い

**［機構の解明］** QatBのN末端ループがQatCの推定活性部位に挿入され、CBASSのCap9–CdnDと同様の配置をとる。QatBがQatCの基質である可能性を示唆し、ペプチド解析ではQatB N末端のNDG修飾も検出された（修飾効率は低いとみられる）。

<details><summary>根拠（論文本文）</summary>

> The most notable feature of the interaction is that the QatB N-terminal loop is inserted into the putative active site of QatC  
> — Results

> identified an NDG-modified N-terminal peptide (GTSKAY) from QatB  
> — Results

</details>

**［機構の解明］** ATP結合型（2.66 Å）ではF235がアデニンとπ–πスタッキングし、SXGXDSモチーフがβ・γリン酸を配位する。CDGの密度はなく、ATPピロホスファターゼ活性も検出できず、QatCの本来の基質は未解明のままだ。

<details><summary>根拠（論文本文）</summary>

> QatC F235 displays a marked conformational change compared with its apo state, to form π-π stacking with the adenine base of the ATP molecule.  
> — Results

> EcQatC does not exhibit obvious ATP pyrophosphatase activity either in the presence or absence of CDG  
> — Results

</details>

**［手法の工夫］** QatBのN末端を天然のまま得るため、Gly2のコドンをUlp1切断部位に直結した。N末端へのHisタグ付加は防御活性を著しく下げることが分かっており、この工夫が必要な理由になる。

<details><summary>根拠（論文本文）</summary>

> we directly linked the codon corresponding to the second glycine residue of QatB to the codon corresponding to the cleavage site of Ulp1  
> — Methods

> adding an N-terminal His-tag before QatB M1 all severely decreased the anti-phage activity of the Qat system  
> — Results

</details>

### 構造データ

| PDB | 手法 | 分解能 | 公開 | 生物種 | リガンド |
|---|---|---|---|---|---|
| [9WVJ](https://www.rcsb.org/structure/9WVJ) | X線結晶構造解析 | 2.09 Å | 2026-09-16 | Escherichia coli | — |
| [9X6C](https://www.rcsb.org/structure/9X6C) | X線結晶構造解析 | 2.66 Å | 2026-09-16 | Escherichia coli | ATP |

- [A0A4Q0WMG2](https://www.uniprot.org/uniprotkb/A0A4Q0WMG2)  Uncharacterized protein — *Escherichia coli* （既存の PDB 構造 2 件）
- [A0A6N2XJ30](https://www.uniprot.org/uniprotkb/A0A6N2XJ30)  Uncharacterized protein — *Citrobacter amalonaticus* （既存の PDB 構造 1 件）

### 実験メモ

- **発現系**：大腸菌BL21(DE3)。OD600 0.8で0.2 mM IPTG、18 ℃で12時間誘導
- **コンストラクト**：N末端His6-SUMO融合（Ulp1切断）。QatBはGly2から始まる天然のN末端を再現
- **精製**：Ni-NTAでUlp1切断後、Superdex 200 increase 10/300 GLでゲルろ過
- **結晶化／グリッド作製**：15 mg/mL、シッティングドロップ蒸気拡散、18 ℃。ATP型は1 mM ATP・1 mM CDG・2 mM MgCl2を氷上1時間プレインキュベート
- **データ収集・解析**：SSRF BL02U1、0.979 Å、EIGER2 X 9M。AlphaFold2予測モデルで分子置換、PHENIXで精密化

<details><summary>根拠（論文本文）</summary>

> The cells were grown at 37 °C until OD600 nm reached 0.8 and then induced at 18 °C for 12 h.  
> — Methods

> Both crystal forms of protein complexes were obtained using the sitting-drop vapor diffusion method at 18 °C by mixing 0.8 μL of protein solution with 0.8 μL of reservoir solution.  
> — Methods

> All diffraction data were collected at the SSRF beamlines BL02U1 using a wavelength of 0.979 Å and a DECTRIS EIGER2 X 9M detector.  
> — Methods

> The initial model was solved by molecular replacement with a structure predicted by AlphaFold2  
> — Methods

</details>

> 📝 編集者への確認事項：本文によれば同時期に別グループもQatBC構造を報告している（本文の引用31, 32）。初構造とは書いていない。QatCの触媒反応は未再構成で、N末端修飾はペプチドレベルのMSのみ。

---

## 2. FlhA(A489E)抑制変異体の結晶構造：Arg-386周辺の塩橋網の組み換えが鞭毛輸送装置の基質切り替えを助ける

![グラフィカルアブストラクト](ga/PMC13639345.svg)

**Structural basis for substrate specificity switching revealed by the FlhA(A489E) suppressor mutation**  
*Biophysics and Physicobiology*（2026-01-01） · [論文](https://doi.org/10.2142/biophysico.bppb-v23.0030) · ライセンス: cc by-nc-sa

### 3行要約

- **背景**：鞭毛のIII型分泌装置はフック完成時に基質特異性を切り替える。FlhB(P270A)の切り替え不全を部分的に回復するFlhA(A489E)の機構は不明だった。
- **やったこと**：FlhAC(A489E)の結晶構造を半閉型（2.90 Å）と開型（3.28 Å）の2状態で決定し、AlphaFold3によるFlhAC–FlhB複合体予測と運動性・分泌アッセイを組み合わせた。
- **分かったこと**：A489EはArg-386・Glu-483周辺の塩橋網を組み換え、α2ヘリックス周辺の配置を変える。FlhBのC末端尾部がα2–β2の溝を占めるという予測モデルと合わせ、状態遷移の障壁を下げると考えられる。

### ここが面白い

**［機構の解明］** 野生型ではArg-386がGlu-483と塩橋を作る。A489Eの半閉型ではArg-386がGlu-489側に引かれてGlu-483から離れ、開型ではGlu-489とGlu-483の両方と塩橋を作る。野生型にない静電ネットワークが現れた。

<details><summary>根拠（論文本文）</summary>

> Thus, the introduced Glu-489 establishes a new electrostatic interaction with Arg-386, altering the orientation of the Arg-386 side chain and disrupting its original interaction with Glu-483.  
> — Results

> These interactions generate an alternative electrostatic network that is not observed in the wild-type structure  
> — Results

</details>

**［機構の解明］** AlphaFold3の5モデルすべてで、FlhBのC末端尾部がFlhA D1ドメインのα2–β2の溝に置かれた。この溝はフィラメント型リングでの隣接サブユニットのリンカー結合部位と重なる。ただし結合は予測であり、実験では示していない。

<details><summary>根拠（論文本文）</summary>

> all five independently generated models consistently positioned FlhBCCT at a groove formed between the α2 helix and β2 strand of the D1 domain of FlhAC  
> — Results

> the α2–β2 groove overlaps with the binding site for the flexible linker region of FlhAC  
> — Results

</details>

**［実験Tips］** Arg-386をAlaに置換した変異体は、FliH・FliIがあれば運動性と分泌が正常だが、FliH・FliIを欠くと両方が阻害された。ATPase複合体が働かない条件でこの塩橋網が重要になることを示唆する。

<details><summary>根拠（論文本文）</summary>

> the flhA(R386A) substitution inhibited both motility (Figure 5A, middle panel) and protein export (Figure 5B, middle panel) in the absence of FliH and FliI.  
> — Results

</details>

### 構造データ

| PDB | 手法 | 分解能 | 公開 | 生物種 | リガンド |
|---|---|---|---|---|---|
| [23TM](https://www.rcsb.org/structure/23TM) | X線結晶構造解析 | 3.28 Å | 2026-10-07 | Salmonella enterica subsp. enterica serovar Typhimurium | — |
| [23TK](https://www.rcsb.org/structure/23TK) | X線結晶構造解析 | 2.90 Å | 2026-10-07 | Salmonella enterica subsp. enterica serovar Typhimurium | — |

- [P40729](https://www.uniprot.org/uniprotkb/P40729) flhA Flagellar biosynthesis protein FlhA — *Salmonella typhimurium (strain LT2 / SGSC1412 / ATCC 700720)* （既存の PDB 構造 12 件）

### 実験メモ

- **発現系**：大腸菌BL21(DE3)、LB培地、30 ℃で一晩培養
- **コンストラクト**：N末端His-tag付きFlhAC(A489E)（pYI104-SP3）
- **精製**：HisTrap HP 5 mL、続いてSuperdex 75 10/300 GL。10 mg/mLに濃縮
- **結晶化／グリッド作製**：シッティングドロップ蒸気拡散。形態1はPEG 3000・リン酸pH 6.2・グリセロール、形態2はPEG 3000・HEPES pH 7.5・NaCl、いずれも20 ℃
- **データ収集・解析**：SPring-8 BL41XU・BL45XU。MOSFLM・AIMLESSで処理し、6AI0と3A5Iを鋳型に分子置換

<details><summary>根拠（論文本文）</summary>

> His-FlhAC(A489E) was purified by affinity chromatography using a HisTrap HP 5 mL column (Cytiva), followed by size-exclusion chromatography on a Superdex 75 10/300 GL column (Cytiva)  
> — Materials and methods

> Form 1 crystals were grown at 20°C using a reservoir solution containing 0.1 M K2HPO4/Na2HPO4 (pH 6.2), 10% (w/v) polyethylene glycol 3000, and 10% (w/v) glycerol.  
> — Materials and methods

> X-ray diffraction data were collected at beamlines BL41XU and BL45XU at SPring-8  
> — Materials and methods

> Initial phases for Form 1 and Form 2 crystals were obtained by molecular replacement using Phaser-MR [20] in Phenix [21] with PDB entries 6AI0 and 3A5I, respectively.  
> — Materials and methods

</details>

> 📝 編集者への確認事項：FlhBとの相互作用はAlphaFold3予測のみで、実験的には未検証。本文の記載どおり「予測」「考えられる」で書いた。

---

## 3. ダルナビル耐性HIVプロテアーゼ（14置換）の複合体構造：離れた置換も活性部位の拡張に寄与する

![グラフィカルアブストラクト](ga/PMC13638461.svg)

**Distal amino-acid substitutions contribute to HIV protease inhibitor resistance as directly as proximal amino-acid substitutions**  
*Scientific Reports*（2026-01-01） · [論文](https://doi.org/10.1038/s41598-026-64620-7) · ライセンス: cc by

### 3行要約

- **背景**：耐性置換は活性部位近傍の主要置換と離れた副次置換に分けられるが、離れた置換が阻害剤結合にどう効くかは不明確だった。
- **やったこと**：ダルナビル耐性株由来の14置換プロテアーゼ（PRp51）とダルナビルの複合体を1.55 Åで結晶構造解析し、GRL142との比較を1500 nsの分子動力学（MD）計算で行った。
- **分かったこと**：結晶構造では相互作用に大きな差はなかった。MDではダルナビル複合体でフラップが開く集団と活性部位の拡張が大きく、GRL142では小さかった。主要・副次の二分類は単純すぎる可能性がある。

### ここが面白い

**［創薬・モダリティ］** PRp51はダルナビルに対しKiで大きく低下するが、GRL142では低下が小さい。抗ウイルス活性（EC50）の低下はダルナビルが353倍、GRL142が88倍だった。構造に基づく設計で耐性変異に強い阻害剤を作れる余地を示す。

<details><summary>根拠（論文本文）</summary>

> In summary, DRV had significant reductions in enzymatic and antiviral activities against PRp51 and HIVp51, respectively.  
> — Results

> GRL142 maintained good potency and had much smaller fold reductions in its Ki and EC50 values  
> — Results

</details>

**［機構の解明］** 結晶構造だけでは耐性を説明できなかった。14置換のうち活性部位に直接接するのは主にVal82とIle84で、残り11個は直接結合しない。MDで初めて、フラップの開閉と活性部位容積の差として違いが現れた。

<details><summary>根拠（論文本文）</summary>

> in their respective crystal structures, there were no noteworthy differences in polar and van der Waals interactions of DRV-PRwt over DRV-PRp51.  
> — Results

> The other eleven residues that underwent substitutions did not have a direct binding interaction with DRV.  
> — Results

</details>

**［機構の解明］** MDでは、活性部位容積が結晶構造の値から100 Å3以内に収まる集団がダルナビル–PRwtで61%、ダルナビル–PRp51で29%だった。GRL142では84%と61%。著者は離れた置換が拡張に寄与すると解釈している。

<details><summary>根拠（論文本文）</summary>

> only 29% of the DRV-PRp51 population has an active site volume within 100 Å3 of the DRV- PRwt active site volume  
> — Results

> The results suggest that the minor substitutions have a more direct impact on the loss of binding of DRV and in causing HIV’s drug resistance against DRV.  
> — Discussion

</details>

### 構造データ

| PDB | 手法 | 分解能 | 公開 | 生物種 | リガンド |
|---|---|---|---|---|---|
| [9CTX](https://www.rcsb.org/structure/9CTX) | X線結晶構造解析 | 1.55 Å | 2024-08-07 | Human immunodeficiency virus 1 | 017 |

- [O38893](https://www.uniprot.org/uniprotkb/O38893) pol HIV-1 retropepsin — *Human immunodeficiency virus type 1* （既存の PDB 構造 1 件）

### 実験メモ

- **発現系**：大腸菌Rosetta (DE3) pLysS、ZYM-5052系の自己誘導培地、37 ℃で20〜22時間。封入体として回収
- **精製**：封入体を尿素で洗浄後、ギ酸で変性。逆相クロマトグラフィー（RESOURCE RPC）後に脱塩し、中和バッファーでリフォールド
- **結晶化／グリッド作製**：ハンギングドロップ蒸気拡散。ダルナビル複合体は0.15 M 硫酸アンモニウム、0.1 M HEPES pH 7.0、20% PEG 4000。30%グリセロールで凍結保護
- **データ収集・解析**：ダルナビル複合体はSPring-8 BL44XU（0.9 Å）。既報の別のプロテアーゼ構造を探索モデルに分子置換、Refmacで精密化

<details><summary>根拠（論文本文）</summary>

> Rosetta (DE3) pLysS strain (Novagen) was transformed with PRDRVRp51 expression vector  
> — Materials and methods

> The unfolded PRDRVRp51 was refolded with the addition of a neutralizing buffer A  
> — Crystallization of Darunavir-PRp51 and GRL142-PRp51 complexes

> PRDRVRp51-DRV complexes were formed in 0.15 M (NH4)2SO4, 0.1 M HEPES pH 7.0, 20% (w/v) PEG 4000.  
> — Crystallization of Darunavir-PRp51 and GRL142-PRp51 complexes

> were collected under cryogenic temperatures at SPring-8 BL44XU using X-rays of 0.9 Å wavelength  
> — Materials and methods

> the structure 6OGL was used as the search model for molecular replacement using Molrep  
> — Materials and methods

</details>

> 📝 編集者への確認事項：GRL142複合体(6MKL)も本論文の構造だが、今回の候補一覧にはダルナビル複合体9CTXのみが載る。結論の多くは著者のMD解析に基づく。本文中でKi倍率が1,432倍（本文）と1,438（表）で食い違うため数値は引用していない。

---

## その他の新着

- [Quasi-continuous cotranslational compaction and folding of a multidomain protein](https://doi.org/10.1038/s41467-026-78090-y) — *Nat Commun*（新しいマップ（EMDB））
