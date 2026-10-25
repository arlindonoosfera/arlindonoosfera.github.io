---
titulo: Ferramentas (sites/software)
estado: planejamento
ano: Todos os anos
recurso: material
disciplina: Biologia
nivel: Ensino Médio
tags: tecnologia-educacional
---

Possíveis: QGIS, [https://ugene.net/](https://ugene.net/), Avogadro

## 0. Genética

| Ferramenta | Para que serve | Tipo |
| --- | --- | --- |
| [NCBI BLAST](https://blast.ncbi.nlm.nih.gov/Blast.cgi?utm_source=chatgpt.com) | Comparar sequências de DNA/proteínas, identificação de sequências, homologia | 🌐 Web/software |
| [NCBI](https://www.ncbi.nlm.nih.gov/?utm_source=chatgpt.com) | Genes, genomas, SNPs, artigos, sequências, proteínas | 🌐 Banco de dados |
| [Ensembl](https://www.ensembl.org/?utm_source=chatgpt.com) | Explorar genomas, genes, variantes e anotações | 🌐 Web |
| [UCSC Genome Browser](https://genome.ucsc.edu/?utm_source=chatgpt.com) | Visualizar genomas e comparar regiões genômicas | 🌐 Web |
| [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/?utm_source=chatgpt.com) | Variantes genéticas associadas a doenças e resposta a medicamentos | 🌐 Banco |
| [Primer-BLAST](https://www.ncbi.nlm.nih.gov/tools/primer-blast/?utm_source=chatgpt.com) | Verificar/desenhar primers para PCR | 🌐 Web |
| [UniProt](https://www.uniprot.org/?utm_source=chatgpt.com) | Proteínas, funções, sequências e anotações | 🌐 Banco |
| [InterPro](https://www.ebi.ac.uk/interpro/?utm_source=chatgpt.com) | Domínios e famílias de proteínas | 🌐 Banco |
| [NCBI Variation](https://www.ncbi.nlm.nih.gov/snp/?utm_source=chatgpt.com) | SNPs e variação genética | 🌐 Banco |

O **BLAST** é especialmente importante: compara sequências de nucleotídeos ou proteínas com bancos de sequências e permite investigar similaridade, relações evolutivas e famílias gênicas. ([BLAST](https://blast.ncbi.nlm.nih.gov/blast/Blast.cgi?CMD=Web&utm_source=chatgpt.com))

O **Ensembl** é excelente para passar de “tenho uma sequência/gene” para “onde isso está no genoma, quais são os transcritos, variantes etc.”. A versão atual também está expandindo a cobertura para muitos organismos além dos modelos tradicionais. ([Ensembl](https://www.ensembl.org/genome/aa67a6ec-fa98-4051-b3cb-35ac263df95d?utm_source=chatgpt.com))

---

# 1. Ecologia

 **dados reais de biodiversidade + estatística + GIS**.

### 🌎 Bancos e plataformas

- [GBIF](https://www.gbif.org/pt/?utm_source=chatgpt.com) — ocorrências de espécies, distribuição geográfica e dados de biodiversidade.
- [iNaturalist](https://www.inaturalist.org/?utm_source=chatgpt.com) — observações e identificação de organismos.
- [OBIS](https://obis.org/?utm_source=chatgpt.com) — biodiversidade marinha.
- [eBird](https://ebird.org/?utm_source=chatgpt.com) — excelente para ecologia de aves.
- [Movebank](https://www.movebank.org/?utm_source=chatgpt.com) — movimentação e rastreamento de animais.
- [NASA Earthdata](https://www.earthdata.nasa.gov/?utm_source=chatgpt.com) — dados ambientais, clima, vegetação, sensoriamento remoto.

O **GBIF** é particularmente importante: fornece acesso aberto a grandes conjuntos de dados de biodiversidade e possui ferramentas/API para consultar registros de ocorrência. ([GBIF](https://www.gbif.org/pt?utm_source=chatgpt.com))

### 📊 Para analisar

- [R Project](https://www.r-project.org/?utm_source=chatgpt.com)
- [RStudio / Posit](https://posit.co/?utm_source=chatgpt.com)
- [QGIS](https://qgis.org/?utm_source=chatgpt.com)
- [ArcGIS](https://www.arcgis.com/?utm_source=chatgpt.com)

**R + QGIS + GBIF** é uma combinação extremamente boa para ecologia.

---

# 2. Microbiologia

### 🦠 Bancos e identificação

- [BacDive](https://bacdive.dsmz.de/?utm_source=chatgpt.com) — informações fenotípicas, taxonômicas e genômicas de bactérias.
- [NCBI Pathogen Detection](https://www.ncbi.nlm.nih.gov/pathogens/?utm_source=chatgpt.com) — genomas de patógenos e vigilância genômica.
- [NCBI BLAST](https://blast.ncbi.nlm.nih.gov/Blast.cgi?utm_source=chatgpt.com) — identificação/comparação de sequências.
- [SILVA](https://www.arb-silva.de/?utm_source=chatgpt.com) — rRNA e taxonomia microbiana.
- [RDP](https://rdp.cme.msu.edu/?utm_source=chatgpt.com) — classificação de sequências de rRNA.
- [MGnify](https://www.ebi.ac.uk/metagenomics/?utm_source=chatgpt.com) — metagenômica.

### 🧬 Para microbiologia moderna

Vale aprender:

**16S rRNA → BLAST → classificação taxonômica → filogenia → metagenômica.**

E, posteriormente:

**QIIME 2 → microbioma → diversidade α/β → composição microbiana.**

---

# 3. Virologia

Aqui há um conjunto muito bom de ferramentas específicas.

- [NCBI Virus](https://www.ncbi.nlm.nih.gov/labs/virus/?utm_source=chatgpt.com) — sequências virais e metadados.
- [ICTV](https://ictv.global/?utm_source=chatgpt.com) — **taxonomia oficial dos vírus**.
- [Nextstrain](https://nextstrain.org/?utm_source=chatgpt.com) — evolução e epidemiologia genômica de vírus.
- [GISAID](https://gisaid.org/?utm_source=chatgpt.com) — compartilhamento de dados genômicos, especialmente importante para influenza e coronavírus.
- [NCBI BLAST](https://blast.ncbi.nlm.nih.gov/Blast.cgi?utm_source=chatgpt.com) — comparação de genomas/proteínas virais.

O **NCBI Virus** permite buscar, filtrar, visualizar e baixar sequências virais, inclusive utilizando metadados e painéis de acompanhamento de sequências de surtos. ([NCBI](https://www.ncbi.nlm.nih.gov/labs/virus/vssi/docs/help/?utm_source=chatgpt.com))

E o **ICTV** deve entrar obrigatoriamente na sua lista: é a referência oficial para taxonomia viral; a versão atual disponibiliza a Master Species List e o navegador taxonômico. ([ICTV](https://ictv.global/?utm_source=chatgpt.com))

---

# 4. Bioquímica / metabolismo

Aqui eu montaria uma “tríade”:

### 🧪 Reações e metabolismo

- [KEGG](https://www.genome.jp/kegg/?utm_source=chatgpt.com) — vias metabólicas, genes e sistemas biológicos.
- [MetaCyc](https://metacyc.org/?utm_source=chatgpt.com) — vias metabólicas.
- [BRENDA](https://www.brenda-enzymes.org/?utm_source=chatgpt.com) — enzimas, propriedades e cinética.
- [Rhea](https://www.rhea-db.org/?utm_source=chatgpt.com) — reações bioquímicas.
- [UniProt](https://www.uniprot.org/?utm_source=chatgpt.com) — proteínas e funções.
- [PDB](https://www.rcsb.org/?utm_source=chatgpt.com) — estruturas 3D de proteínas e outras macromoléculas.

### 🧬 Estrutura molecular

- [RCSB Protein Data Bank](https://www.rcsb.org/?utm_source=chatgpt.com)
- [AlphaFold Protein Structure Database](https://alphafold.ebi.ac.uk/?utm_source=chatgpt.com)
- [PyMOL](https://pymol.org/?utm_source=chatgpt.com)
- [UCSF ChimeraX](https://www.cgl.ucsf.edu/chimerax/?utm_source=chatgpt.com)

Para entender metabolismo de verdade, eu colocaria **KEGG + MetaCyc + BRENDA + Rhea** no núcleo.

---

# 5. Evolução como eixo estruturante

Aqui muda um pouco: evolução não deveria ser apenas mais uma matéria. Ela pode conectar praticamente todas as outras.

### 🧬 Ferramentas

- [MEGA](https://www.megasoftware.net/?utm_source=chatgpt.com) — alinhamento, distância genética e filogenia.
- [IQ-TREE](https://iqtree.org/?utm_source=chatgpt.com) — filogenia por máxima verossimilhança.
- [BEAST 2](https://www.beast2.org/?utm_source=chatgpt.com) — filogenia bayesiana e análises temporais.
- [HyPhy](https://hyphy.org/?utm_source=chatgpt.com) — seleção natural e evolução molecular.
- [PAML](https://github.com/abacus-gene/paml?utm_source=chatgpt.com) — evolução molecular.
- [BLAST](https://blast.ncbi.nlm.nih.gov/Blast.cgi?utm_source=chatgpt.com) — homologia.
- [Open Tree of Life](https://tree.opentreeoflife.org/?utm_source=chatgpt.com) — árvore da vida.

O **IQ-TREE**, por exemplo, atualmente está na versão 3.1.3 e oferece tanto software local quanto serviços web para análises filogenéticas. ([IQ-TREE](https://iqtree.org/?utm_source=chatgpt.com))

### 🌳 Para visualizar

[iTOL — Interactive Tree of Life](https://itol.embl.de/?utm_source=chatgpt.com)

É uma das ferramentas que eu mais recomendo aprender.

---

# 6. Biotecnologia

Aqui eu separaria **bioinformática** de **desenho molecular/laboratorial**.

### 🧬 DNA / plasmídeos / clonagem

- [Benchling](https://www.benchling.com/?utm_source=chatgpt.com)
- [SnapGene](https://www.snapgene.com/?utm_source=chatgpt.com)
- [Addgene](https://www.addgene.org/?utm_source=chatgpt.com)
- [NEBcutter](https://nc3.neb.com/NEBcutter/?utm_source=chatgpt.com)
- [NCBI Primer-BLAST](https://www.ncbi.nlm.nih.gov/tools/primer-blast/?utm_source=chatgpt.com)

### 🧪 Para engenharia genética

Depois entrariam:

- desenho de primers;
- restrição/ligação;
- plasmídeos;
- PCR;
- CRISPR;
- expressão gênica;
- proteínas recombinantes;
- análise de sequências;
- desenho de construções.

**Benchling + SnapGene + NCBI + Addgene** já formam uma excelente base digital.

---

# 7. Saúde pública / epidemiologia

### 📊 Epidemiologia

- [WHO Data](https://data.who.int/?utm_source=chatgpt.com)
- [PAHO/OPAS](https://www.paho.org/pt?utm_source=chatgpt.com)
- [DATASUS](https://datasus.saude.gov.br/?utm_source=chatgpt.com)
- [SINAN](https://www.gov.br/saude/pt-br/composicao/svsa/sistemas-de-informacao/sinan?utm_source=chatgpt.com)
- [Our World in Data](https://ourworldindata.org/?utm_source=chatgpt.com)
- [CDC Data](https://data.cdc.gov/?utm_source=chatgpt.com)

### 📈 Análise

- [R](https://www.r-project.org/?utm_source=chatgpt.com)
- [RStudio/Posit](https://posit.co/?utm_source=chatgpt.com)
- [Python](https://www.python.org/?utm_source=chatgpt.com)
- [Jupyter](https://jupyter.org/?utm_source=chatgpt.com)

**Importante:** eu não colocaria mais o Epi Info como ferramenta principal para aprender epidemiologia hoje. O CDC encerrou o desenvolvimento e a assistência técnica do produto em setembro de 2025, embora a versão desktop continue operacional em determinados ambientes. ([CDC](https://www.cdc.gov/epiinfo/?utm_source=chatgpt.com))

Para aprender epidemiologia moderna, eu priorizaria **R + Python + dados públicos + estatística**.

---

# 8. Sistemática / filogenia moderna

Essa área merece um arsenal próprio.

### 🌳 Taxonomia

- [Catalogue of Life](https://www.catalogueoflife.org/?utm_source=chatgpt.com)
- [GBIF](https://www.gbif.org/?utm_source=chatgpt.com)
- [NCBI Taxonomy](https://www.ncbi.nlm.nih.gov/taxonomy?utm_source=chatgpt.com)
- [Open Tree of Life](https://tree.opentreeoflife.org/?utm_source=chatgpt.com)

### 🧬 Filogenia

- [IQ-TREE](https://iqtree.org/?utm_source=chatgpt.com)
- [MEGA](https://www.megasoftware.net/?utm_source=chatgpt.com)
- [RAxML-NG](https://github.com/amkozlov/raxml-ng?utm_source=chatgpt.com)
- [MrBayes](https://nbisweden.github.io/MrBayes/?utm_source=chatgpt.com)
- [BEAST 2](https://www.beast2.org/?utm_source=chatgpt.com)
- [iTOL](https://itol.embl.de/?utm_source=chatgpt.com)

### 📚 Dados publicados

[TreeBASE](https://www.treebase.org/?utm_source=chatgpt.com)

O TreeBASE é especificamente um repositório de árvores filogenéticas e das matrizes/dados usados para produzi-las. ([treebase.org](https://www.treebase.org/?utm_source=chatgpt.com))

---

# 9. Fungos 🍄

Aqui dá para fazer uma coleção muito boa.

- [MycoBank](https://www.mycobank.org/?utm_source=chatgpt.com)
- [Index Fungorum](https://www.indexfungorum.org/?utm_source=chatgpt.com)
- [Species Fungorum](https://www.speciesfungorum.org/?utm_source=chatgpt.com)
- [UNITE](https://unite.ut.ee/?utm_source=chatgpt.com)
- [GBIF](https://www.gbif.org/?utm_source=chatgpt.com)
- [iNaturalist](https://www.inaturalist.org/?utm_source=chatgpt.com)
- [NCBI](https://www.ncbi.nlm.nih.gov/?utm_source=chatgpt.com)

O **Index Fungorum** é especialmente útil para nomenclatura: mantém dados dos nomes científicos de fungos e grupos relacionados, enquanto o próprio site direciona a informação taxonômica para o Species Fungorum. ([Index Fungorum](https://www.indexfungorum.org/?utm_source=chatgpt.com))

Para **micologia molecular**, eu acrescentaria:

**UNITE → ITS → BLAST → filogenia → iTOL.**

---

# 10. Zoologia — mais completa 🐙🦎🦅

Eu faria essa área muito mais ampla do que simplesmente “decorar filos”.

### 🐾 Taxonomia + diversidade

- [Animal Diversity Web](https://animaldiversity.org/?utm_source=chatgpt.com)
- [GBIF](https://www.gbif.org/?utm_source=chatgpt.com)
- [Catalogue of Life](https://www.catalogueoflife.org/?utm_source=chatgpt.com)
- [iNaturalist](https://www.inaturalist.org/?utm_source=chatgpt.com)
- [Open Tree of Life](https://tree.opentreeoflife.org/?utm_source=chatgpt.com)

O **Animal Diversity Web** é particularmente interessante para estudo: possui milhares de contas de espécies, classificação, distribuição, conservação, imagens, sons e informações de história natural. ([Animal Diversity Web](https://www.animaldiversity.org/?utm_source=chatgpt.com))

### 🐦 Por grupos

**Aves**

- [eBird](https://ebird.org/?utm_source=chatgpt.com)
- [BirdLife International](https://datazone.birdlife.org/?utm_source=chatgpt.com)

**Mamíferos**

- [Mammal Diversity Database](https://www.mammaldiversity.org/?utm_source=chatgpt.com)

**Peixes**

- [FishBase](https://www.fishbase.se/?utm_source=chatgpt.com)

**Répteis e anfíbios**

- [Amphibian Species of the World](https://amphibiansoftheworld.amnh.org/?utm_source=chatgpt.com)
- [The Reptile Database](https://reptile-database.reptarium.cz/?utm_source=chatgpt.com)

**Invertebrados**

- [WoRMS](https://www.marinespecies.org/?utm_source=chatgpt.com) — especialmente importante para organismos marinhos.
- [AntWeb](https://www.antweb.org/?utm_source=chatgpt.com) — formigas.
- [iNaturalist](https://www.inaturalist.org/?utm_source=chatgpt.com) — excelente para observações e identificação.

---

# 🧠 O mais importante: não aprender 100 sites isoladamente

 **kit principal de Biologia** em camadas:

### 🔵 Camada 1 — indispensáveis

1. **NCBI**
2. **BLAST**
3. **Ensembl**
4. **UniProt**
5. **GBIF**
6. **iNaturalist**
7. **R + RStudio**
8. **QGIS**
9. **IQ-TREE**
10. **iTOL**
11. **Open Tree of Life**
12. **KEGG**

### 🟢 Camada 2 — especialização

**Genética:** ClinVar, UCSC, Primer-BLAST

**Microbiologia:** BacDive, SILVA, RDP, MGnify

**Virologia:** NCBI Virus, ICTV, Nextstrain

**Bioquímica:** BRENDA, Rhea, PDB, AlphaFold DB

**Evolução:** MEGA, IQ-TREE, BEAST, HyPhy

**Biotecnologia:** Benchling, SnapGene, Addgene

**Epidemiologia:** DATASUS, WHO, OPAS, R, Python

**Sistemática:** Catalogue of Life, TreeBASE, Open Tree, iTOL

**Fungos:** MycoBank, Index Fungorum, Species Fungorum, UNITE

**Zoologia:** ADW, FishBase, MDD, WoRMS, BirdLife etc.

### 🔴 Camada 3 — programação

(somente pra mim)

**Python → R → Bash/Linux → Git/GitHub → Jupyter → APIs → análise de grandes datasets.**
