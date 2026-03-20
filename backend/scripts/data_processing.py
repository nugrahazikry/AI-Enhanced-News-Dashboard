import pandas as pd
import json
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed


######################################################
# Prompt to get sentiment, NER, and topic analysis
######################################################

def analisa_prompt(df, model_generative, language='id'):
    judul_artikel = {row["index"]: row["headline_title"] for _, row in df.iterrows()}

    prompt = f"""Anda adalah seorang ahli dengan pengalaman 10 tahun yang dapat mengkategorikan sentimen, entitas, dan menganalisa topik yang muncul dari suatu kalimat dan judul_artikel.
    Tugas anda sekarang adalah tolong analisa sentimen, entitas (Named Entity Recognition), topik, dan validasi berita yang muncul dalam judul_artikel yang ditandai dengan (###).

    Instruksi:
    1. Berikan 4 output sebagai berikut: id, sentimen, NER, dan topik.
    2. Dalam menentukan id, pastikan nomornya sesuai dengan index input yang diberikan pada judul_artikel yang ditandai dengan (###).
    3. Dalam menentukan sentimen, pastikan anda hanya dapat menampilkan hasil output "positive", "negative", dan "neutral". Jangan menampilkan hasil output yang lain dibanding ketiga output tersebut.
    4. Dalam menentukan NER, ekstrak SEMUA entitas nama yang muncul dalam judul_artikel, termasuk:
       - Nama lengkap maupun singkatan/akronim (contoh: IHSG, OJK, BI, BEI, DPR, KPK, dll.)
       - Nama yang ditulis dengan huruf kapital semua tetap harus diekstrak sebagai entitas
       - Jangan lewatkan entitas hanya karena berbentuk akronim atau singkatan
       Berikan hasilnya dalam bentuk list string.
    5. Dalam menentukan NER, masukkan entitas dalam lingkup berikut:
       - Perusahaan dan korporasi (termasuk BUMN, startup, tbk)
       - Tokoh publik (politisi, pejabat, CEO, tokoh masyarakat)
       - Lembaga pemerintahan dan regulator (termasuk akronim seperti OJK, BI, BEI, BKPM)
       - Indeks dan instrumen pasar keuangan (contoh: IHSG, LQ45, S&P500)
       - Organisasi, asosiasi, dan lembaga internasional
       - Entitas politik seperti partai dan koalisi
    6. Dalam menentukan NER, apabila anda tidak menemukan entitas apapun, anda dapat menulis output ["tidak ada"].
    7. Dalam menentukan topik, untuk setiap judul artikel yang ditandai dengan simbol (###), tentukan kategori topiknya sesuai dengan daftar label topik yang diberikan ($$$), jangan berikan topik selain dari topik yang sudah ditentukan.
    8. Dalam menentukan topik, jika suatu berita tidak sesuai dengan kategori mana pun dalam daftar, gunakan label "other".

    topik yang sudah ditentukan dan scopenya adalah sebagai berikut:
    ($$$)
    topik_berita:
    1. ekonomi dan keuangan: Makroekonomi, perbankan, pasar modal, investasi, perdagangan.
    2. bisnis dan industri: Kinerja perusahaan, manufaktur, UMKM, ritel.
    3. politik dan pemerintahan: Pemilu, partai, hubungan luar negeri, birokrasi, kebijakan publik.
    4. hukum dan kriminal: Korupsi, peradilan, kepolisian, keamanan nasional.
    5. infrastruktur dan transportasi: Pembangunan jalan, tol, pelabuhan, tata kota, logistik.
    6. energi dan lingkungan: Pertambangan, migas, energi terbarukan, isu iklim, bencana alam.
    7. teknologi dan inovasi: Digitalisasi, startup, riset ilmiah, pendidikan, gadget.
    8. sosial dan kesejahteraan: Kesehatan, agama, tenaga kerja, kependudukan, budaya.
    9. lifestyle dan olahraga: Hiburan, hobi, wisata, kompetisi olahraga.
    10. other: Berita yang benar-benar tidak masuk kategori di atas.
    ($$$)

    (###)
    judul_artikel:
    {judul_artikel}
    (###)

    Berikan output HANYA dalam format JSON array yang valid, tanpa penjelasan tambahan, sebagai berikut:
    [
      {{"id": <index>, "sentimen": "<positive|negative|neutral>", "NER": ["<entitas1>", "<entitas2>"], "topik": "<topik>"}},
      ...
    ]
    Pastikan jumlah elemen dalam array sama dengan jumlah judul_artikel yang diberikan."""

    if language == 'en':
        prompt = f"""You are an expert analyst with 10 years of experience in sentiment analysis, named entity recognition (NER), and topic classification for news headlines.

Your task: analyze the sentiment, named entities (NER), and topic of each news headline marked with (###).

Instructions:
1. Provide 4 outputs per headline: id, sentimen, NER, and topik.
2. For id: use the exact index number provided in the input.
3. For sentimen: output ONLY one of "positive", "negative", or "neutral". Never use any other value.
4. For NER: extract ALL named entities from the headline, including:
   - Full names and abbreviations/acronyms (e.g., FBI, SEC, Fed, NYSE, GOP, NATO)
   - Names written entirely in caps must still be extracted
   - Do not skip entities just because they are acronyms or abbreviations
   Return as a list of strings.
5. For NER, include entities in these categories:
   - Companies and corporations (publicly traded, private, startups)
   - Public figures (politicians, executives, celebrities, public officials)
   - Government bodies and regulators (e.g., SEC, Fed, DOJ, EPA, FTC, White House)
   - Market indices and financial instruments (e.g., S&P 500, Dow Jones, NASDAQ)
   - Organizations, associations, and international bodies
   - Political parties and coalitions
6. If no entities are found, output ["tidak ada"].
7. For topik: assign exactly one category from the list below ($$$). Do not use any label outside this list.
8. If no category fits, use "other".

Available topics:
($$$)
topik_berita:
1. economy and finance: Macroeconomics, banking, capital markets, investment, trade.
2. business and industry: Company performance, manufacturing, startups, retail.
3. politics and government: Elections, political parties, foreign affairs, bureaucracy, public policy.
4. law and crime: Corruption, judiciary, law enforcement, national security.
5. infrastructure and transportation: Roads, highways, ports, urban planning, logistics.
6. energy and environment: Mining, oil & gas, renewable energy, climate issues, natural disasters.
7. technology and innovation: Digitalization, startups, scientific research, education, gadgets.
8. social and welfare: Healthcare, religion, labor, demographics, culture.
9. lifestyle and sports: Entertainment, hobbies, travel, sports competitions.
10. other: News that does not fit any category above.
($$$)

(###)
news_headlines:
{judul_artikel}
(###)

Return ONLY a valid JSON array with no additional explanation:
[
  {{"id": <index>, "sentimen": "<positive|negative|neutral>", "NER": ["<entity1>", "<entity2>"], "topik": "<topic>"}},
  ...
]
The array must contain exactly as many elements as there are headlines provided."""

    response = model_generative.generate_content(prompt)
    response_text = response.text

    # Extract JSON robustly (handle code blocks or raw JSON)
    if '```json' in response_text:
        start = response_text.find('```json') + len('```json')
        end = response_text.find('```', start)
        json_part = response_text[start:end].strip()
    elif '```' in response_text:
        start = response_text.find('```') + len('```')
        end = response_text.find('```', start)
        json_part = response_text[start:end].strip()
    else:
        json_part = response_text.strip()

    # Parse JSON and convert to DataFrame
    json_data = json.loads(json_part)
    df_result = pd.DataFrame(json_data)

    return df_result

######################################################
# Prompt to normalize the NER values
######################################################

def normalize_ner_agent(df, model_generative, ner_col="NER", language='id', progress_cb=None):
    """
    Agentic NER normalization using a 3-step multi-turn reasoning chain:
      Turn 1 — Classify each entity by type AND identify alias groups
      Turn 2 — Generate initial mapping with alias group consolidation
      Turn 3 — Self-verify and correct inconsistencies, output final JSON
    """

    def _to_list(val):
        """Safely coerce a NER cell value to a plain Python list."""
        if isinstance(val, list):
            return val
        if hasattr(val, 'tolist'):          # numpy / pandas array
            return val.tolist()
        if isinstance(val, str):
            import ast
            try:
                parsed = ast.literal_eval(val)
                return parsed if isinstance(parsed, list) else [parsed]
            except Exception:
                return [val] if val else []
        return []

    def _dedupe(lst):
        """Remove duplicates while preserving insertion order."""
        seen = set()
        return [x for x in lst if not (x in seen or seen.add(x))]

    # ── Collect unique NER values ──────────────────────────────────────────
    all_ner_values = set()
    for ner_list in df[ner_col]:
        all_ner_values.update(_to_list(ner_list))
    all_ner_values.discard("tidak ada")
    unique_ner_list = sorted(all_ner_values)
    print(f"Unique NER values: {len(unique_ner_list)}")

    entities_str = "\n".join(f"- {e}" for e in unique_ner_list)

    def extract_json(text):
        if '```json' in text:
            s = text.find('```json') + 7
            return text[s:text.rfind('```')].strip()
        elif '```' in text:
            s = text.find('```') + 3
            return text[s:text.rfind('```')].strip()
        s, e = text.find('{'), text.rfind('}') + 1
        return text[s:e].strip() if s != -1 and e > s else text.strip()

    def _cb_ner(msg):
        print(msg)
        if progress_cb:
            progress_cb(msg)

    # ── Start multi-turn chat session ──────────────────────────────────────
    chat = model_generative.start_chat(history=[])

    if language == 'en':
        _t1 = f"""You are an expert news entity analysis agent working in a multi-step session.

The following {len(unique_ner_list)} entities were extracted from English-language news headlines:
{entities_str}

Step 1 consists of TWO parts:

Part A — Classify each entity into one of the following categories with a brief reason:
- PERSON       : Individual names (politicians, executives, officials, public figures)
- ORG_ACRONYM  : Organizations/institutions already in common abbreviated form (FBI, SEC, Fed, NYSE, GOP)
- ORG_FULL     : Organizations with full names that have a widely-used official abbreviation
- ORG_NOABB    : Companies/organizations that do not have a widely-recognized abbreviation
- STOCK_CODE   : Official stock ticker symbols listed on exchanges (e.g., AAPL, TSLA, GOOGL)
- FINANCIAL    : Market indices or financial instruments (not individual stock tickers)
- OTHER        : Entities that do not fit any category above

Format for Part A (one line per entity):
<entity> → <category>: <reason>

Part B — Identify "alias groups": sets of entities that refer to ONE real-world entity but appear in different forms:
- Official full name vs common short name
- Parent company vs subsidiary/division sharing the same brand
- Company name (in various forms) vs its stock ticker
- Abbreviation vs its full expansion

Format for Part B (one line per group, members separated by " | "):
ALIAS_GROUP: <entity_1> | <entity_2> | <entity_3> | ...
Entities with no alias in the list do not need to be listed in Part B."""
        _t2 = f"""Based on the classification and alias groups above, create a normalization mapping dictionary.

General rules per category:
- PERSON       → use the most publicly recognized name
- ORG_ACRONYM  → keep the abbreviation as-is
- ORG_FULL     → convert to the most widely used official abbreviation in English-language media
- ORG_NOABB    → keep the original name
- STOCK_CODE   → keep the ticker as-is
- FINANCIAL    → keep the code/ticker used in media

MANDATORY rules for alias groups (highest priority, overrides category rules):
1. All entities in one alias group MUST map to ONE identical value (canonical name).
2. Choose the canonical name using this priority:
   a. Official stock ticker (if publicly listed), as it is the most unique and unambiguous.
   b. Official abbreviation/acronym most commonly used in English-language media.
   c. The short name most widely recognized by the general public.
3. Long names, subdivision names, and partial names in an alias group must map to the chosen canonical name — NOT kept in their original form.

All {len(unique_ner_list)} entities MUST appear in the output.
Return ONLY a valid JSON dictionary, no explanation:
{{
  "<original_entity>": "<normalized_entity>",
  ...
}}"""
        _t3 = """Verify the mapping you just created. Check critically:

1. ALIAS GROUP CHECK — Do all members of each alias group (identified in Step 1 Part B) map to the EXACT SAME value? If any differ, standardize to one canonical name following the priority rules (stock ticker > official abbreviation > popular short name).
2. Are there entities outside alias groups that actually refer to the same entity but were not detected? If so, standardize them.
3. Are all abbreviations correct and consistent with English-language media standards?
4. Are there any inconsistent formatting or typos in the normalized values?
5. Ensure no entity from the original input is missing.

After verification, return the corrected output ONLY as a valid JSON dictionary:
{
  "<original_entity>": "<normalized_entity>",
  ...
}"""
    else:
        _t1 = f"""Anda adalah agen ahli analisis entitas berita Indonesia dalam sesi kerja multi-langkah.

Berikut {len(unique_ner_list)} entitas yang diekstrak dari judul berita:
{entities_str}

Langkah 1 terdiri dari DUA bagian:

Bagian A — Klasifikasikan setiap entitas ke salah satu kategori berikut dan berikan alasan singkat:
- PERSON       : Nama orang (politisi, pejabat, CEO, tokoh publik)
- ORG_ACRONYM  : Organisasi/lembaga yang sudah dalam bentuk singkatan umum (OJK, BI, KPK, BEI, DPR)
- ORG_FULL     : Organisasi/lembaga dengan nama panjang yang memiliki singkatan resmi dan umum dipakai
- ORG_NOABB    : Perusahaan/organisasi yang tidak memiliki singkatan umum yang dikenal luas
- STOCK_CODE   : Kode saham / ticker resmi perusahaan di bursa efek (4 huruf kapital atau kombinasi huruf-angka)
- FINANCIAL    : Indeks pasar modal atau instrumen keuangan (bukan kode saham individual)
- OTHER        : Entitas yang tidak masuk kategori di atas

Format Bagian A (satu baris per entitas):
<entitas> → <kategori>: <alasan>

Bagian B — Identifikasi "alias group": kumpulan entitas yang merujuk pada SATU entitas nyata yang sama, meskipun ditulis dalam bentuk berbeda. Bentuk berbeda yang harus dideteksi meliputi:
- Nama lengkap resmi vs nama pendek/populer
- Nama induk perusahaan vs nama anak perusahaan / divisi / unit bisnis yang berbagi merek yang sama
- Nama perusahaan (dalam berbagai bentuk) vs kode sahamnya di bursa efek
- Singkatan vs kepanjangannya

Format Bagian B (satu baris per grup, pisahkan anggota dengan " | "):
ALIAS_GROUP: <entitas_1> | <entitas_2> | <entitas_3> | ...
Jika suatu entitas tidak memiliki alias dalam daftar, tidak perlu dituliskan di Bagian B."""
        _t2 = f"""Berdasarkan klasifikasi dan alias group di atas, buat mapping dictionary normalisasi.

Aturan umum per kategori:
- PERSON       → gunakan nama yang paling dikenal publik
- ORG_ACRONYM  → pertahankan singkatan apa adanya
- ORG_FULL     → ubah ke singkatan resmi yang paling umum digunakan di media Indonesia
- ORG_NOABB    → pertahankan nama asli
- STOCK_CODE   → pertahankan kode saham apa adanya
- FINANCIAL    → pertahankan kode/ticker yang digunakan di media

Aturan WAJIB untuk alias group (prioritas tertinggi, menggantikan aturan kategori di atas):
1. Semua entitas dalam satu alias group HARUS di-map ke SATU nilai yang sama (canonical name).
2. Pilih canonical name menggunakan urutan prioritas berikut:
   a. Kode saham resmi di bursa efek (jika perusahaan tbk / listed), karena paling unik dan tidak ambigu.
   b. Singkatan/akronim resmi yang paling umum digunakan di media nasional Indonesia.
   c. Nama pendek yang paling dikenal masyarakat luas.
3. Nama panjang, nama subdivisi, dan nama parsial yang masuk alias group harus di-map ke canonical name yang dipilih — BUKAN dipertahankan dalam bentuk aslinya.

Semua {len(unique_ner_list)} entitas HARUS ada dalam output.
Berikan HANYA JSON dictionary yang valid, tanpa penjelasan:
{{
  "<entitas_asli>": "<entitas_normalized>",
  ...
}}"""
        _t3 = """Verifikasi mapping yang baru saja kamu buat. Periksa secara kritis:

1. ALIAS GROUP CHECK — Apakah semua anggota dari setiap alias group (yang diidentifikasi di Langkah 1 Bagian B) sudah di-map ke nilai yang PERSIS SAMA? Jika ada yang berbeda, seragamkan ke satu canonical name yang paling tepat sesuai aturan prioritas (kode saham > singkatan resmi > nama pendek populer).
2. Apakah ada entitas di luar alias group yang sebenarnya masih merujuk entitas yang sama tapi belum terdeteksi? Jika ada, seragamkan.
3. Apakah semua singkatan sudah tepat dan sesuai standar media Indonesia?
4. Apakah ada format yang tidak konsisten atau kesalahan pengetikan dalam nilai normalized?
5. Pastikan tidak ada entitas dari input awal yang hilang.

Setelah verifikasi, berikan output terkoreksi HANYA dalam format JSON dictionary yang valid:
{
  "<entitas_asli>": "<entitas_normalized>",
  ...
}"""

    # Turn 1 — Entity Classification + Alias Group Detection
    _cb_ner("NER normalization [1/3]: classifying entities and detecting alias groups...")
    chat.send_message(_t1)

    # Turn 2 — Generate Initial Mapping with Alias Consolidation
    _cb_ner("NER normalization [2/3]: generating mapping dictionary...")
    chat.send_message(_t2)

    # Turn 3 — Self-Verification and Final Output
    _cb_ner("NER normalization [3/3]: verifying and finalizing...")
    final = chat.send_message(_t3)

    ner_alias_map = json.loads(extract_json(final.text))
    _cb_ner(f"NER normalization done: {len(ner_alias_map)} entities mapped")

    # ── Apply mapping (with deduplication) ────────────────────────────────
    df["NER_normalized"] = df[ner_col].apply(
        lambda ner_list: _dedupe([ner_alias_map.get(e, e) for e in _to_list(ner_list)])
    )

    return df, ner_alias_map


######################################################
# Prompt to normalize source_news title
######################################################

def normalize_source_agent(df, model_generative, source_col="source_news", language='id', progress_cb=None):
    """
    Agentic source normalization using a 3-step multi-turn reasoning chain:
      Turn 1 — Classify each source by media type and parent brand
      Turn 2 — Generate initial mapping to canonical brand names
      Turn 3 — Self-verify consistency (subdomains, vertical brands → same parent)
    """

    # ── Collect unique source values ───────────────────────────────────────
    unique_sources = sorted(df[source_col].dropna().unique().tolist())
    print(f"Unique source values: {len(unique_sources)}")

    sources_str = "\n".join(f"- {s}" for s in unique_sources)

    def extract_json(text):
        if '```json' in text:
            s = text.find('```json') + 7
            return text[s:text.rfind('```')].strip()
        elif '```' in text:
            s = text.find('```') + 3
            return text[s:text.rfind('```')].strip()
        s, e = text.find('{'), text.rfind('}') + 1
        return text[s:e].strip() if s != -1 and e > s else text.strip()

    def _cb_src(msg):
        print(msg)
        if progress_cb:
            progress_cb(msg)

    # ── Start multi-turn chat session ──────────────────────────────────────
    chat = model_generative.start_chat(history=[])

    if language == 'en':
        _s1 = f"""You are an expert in English-language media and journalism operating in a multi-step session.

The following {len(unique_sources)} news source names were found in the dataset:
{sources_str}

Step 1 — Classify each source into one of the following categories and identify its parent brand:
- NATIONAL_PRINT  : National print newspapers (New York Times, Washington Post, Wall Street Journal, etc.)
- DIGITAL_NATIVE  : Digital-only news portals (Axios, BuzzFeed News, The Atlantic online, etc.)
- TV_ONLINE       : TV news channels with online presence (CNN, Fox News, MSNBC, BBC, etc.)
- WIRE_SERVICE    : News wire services (AP, Reuters, Bloomberg, AFP, etc.)
- REGIONAL        : Local or regional media
- FOREIGN         : Non-English or international media
- UNKNOWN         : Cannot be identified

Format (one line per source):
<original_source> → <category> | parent_brand: <main_brand_name>"""
        _s2 = f"""Based on the classification and parent brands above, create a normalization mapping.

Rules:
1. All variants of the same brand (subdomains, divisions, different formats) must map to ONE consistent parent brand name.
   Example: "cnn.com", "CNN International", "CNN Business", "Cable News Network" → all become "CNN"
2. Use the most publicly recognized brand name (not a URL or domain).
3. Remove domain extensions (.com, .co.uk, etc.) from normalized names.
4. For international media, keep the widely recognized international name.
5. All {len(unique_sources)} sources MUST appear in the output.

Return ONLY a valid JSON dictionary, no explanation:
{{
  "<original_source>": "<normalized_brand>",
  ...
}}"""
        _s3 = """Verify the mapping you just created. Check critically:
1. Are there still brand variants that map to different values? Standardize them to one name.
2. Are there any normalized names still containing domain extensions (.com, .co.uk)? Remove them.
3. Is the capitalization of normalized names consistent and conventional?
4. Are all sources from the original input represented in the output?

After verification, return the corrected output ONLY as a valid JSON dictionary:
{
  "<original_source>": "<normalized_brand>",
  ...
}"""
    else:
        _s1 = f"""Anda adalah agen ahli media dan jurnalisme Indonesia dalam sesi kerja multi-langkah.

Berikut {len(unique_sources)} nama sumber berita yang ditemukan dalam dataset:
{sources_str}

Langkah 1 — Klasifikasikan setiap sumber ke salah satu kategori berikut dan identifikasi brand induknya:
- NATIONAL_PRINT : Media cetak/koran nasional (Kompas, Tempo, Republika, dsb.)
- DIGITAL_NATIVE : Portal berita digital-only (Detik, Tirto, The Conversation, dsb.)
- TV_ONLINE      : Kanal berita TV yang memiliki situs online (KompasTV, MetroTV, CNNIndonesia, dsb.)
- WIRE_SERVICE   : Kantor berita / wire service (Antara, Reuters, Bloomberg, dsb.)
- REGIONAL       : Media lokal / daerah
- FOREIGN        : Media internasional berbahasa asing
- UNKNOWN        : Tidak dapat diidentifikasi

Format output (satu baris per sumber):
<sumber_asli> → <kategori> | brand_induk: <nama_brand_utama>"""
        _s2 = f"""Berdasarkan klasifikasi dan brand induk di atas, buat mapping normalisasi.

Aturan:
1. Semua varian dari brand yang sama (subdomain, divisi, format berbeda) harus di-map ke SATU nama brand utama yang konsisten.
   Contoh: "finance.detik.com", "Detik Finance", "detikFinance", "detik.com" → semua menjadi "Detik"
2. Gunakan nama brand yang paling umum dan dikenal publik Indonesia (bukan URL/domain).
3. Buang ekstensi domain (.com, .co.id, dll.) dari nama normalized.
4. Untuk media asing, pertahankan nama internasional yang lazim.
5. Semua {len(unique_sources)} sumber HARUS ada dalam output.

Berikan HANYA JSON dictionary yang valid, tanpa penjelasan:
{{
  "<sumber_asli>": "<nama_brand_normalized>",
  ...
}}"""
        _s3 = """Verifikasi mapping yang baru saja kamu buat. Periksa secara kritis:
1. Apakah masih ada varian dari brand yang sama yang di-map ke nilai berbeda? Seragamkan semua ke satu nama.
2. Apakah ada nama normalized yang masih mengandung ekstensi domain (.com, .co.id)? Hapus.
3. Apakah nama normalized sudah menggunakan kapitalisasi yang konsisten dan lazim?
4. Apakah semua sumber dari input awal sudah terwakili dalam output?

Setelah verifikasi, berikan output terkoreksi HANYA dalam format JSON dictionary yang valid:
{
  "<sumber_asli>": "<nama_brand_normalized>",
  ...
}"""

    # Turn 1 — Source Classification
    _cb_src("Source normalization [1/3]: classifying media sources...")
    chat.send_message(_s1)

    # Turn 2 — Generate Initial Mapping
    _cb_src("Source normalization [2/3]: generating brand mapping...")
    chat.send_message(_s2)

    # Turn 3 — Self-Verification
    _cb_src("Source normalization [3/3]: verifying consistency...")
    final = chat.send_message(_s3)

    source_alias_map = json.loads(extract_json(final.text))
    _cb_src(f"Source normalization done: {len(source_alias_map)} sources mapped")

    # ── Apply mapping ──────────────────────────────────────────────────────
    df["normalized_source_news"] = df[source_col].map(
        lambda s: source_alias_map.get(s, s) if pd.notna(s) else s
    )

    return df, source_alias_map


######################################################
# Full post-scrape processing pipeline
######################################################

def run_processing_pipeline(df, model_generative, language='id', progress_cb=None):
    """
    Runs the full AI processing pipeline on a scraped DataFrame:
      1. Batch labeling (sentiment, NER, topic) with concurrent execution
      2. NER alias normalization
      3. Source brand normalization
    Returns the fully processed DataFrame.
    """

    def _progress(msg):
        print(msg)
        if progress_cb:
            progress_cb(msg)

    df = df.copy()
    df['index'] = range(len(df))

    # ── Step 1: Batch AI labeling ─────────────────────────────────────────
    chunk_size = 20
    chunks = [
        (batch_num + 1, i, df.iloc[i:i + chunk_size].copy())
        for batch_num, i in enumerate(range(0, len(df), chunk_size))
    ]
    total_batches = len(chunks)
    _progress(f"Labeling articles: batch 0/{total_batches}")

    all_responses = [None] * len(chunks)

    def process_chunk(batch_num, i, df_chunk):
        try:
            response_df = analisa_prompt(df_chunk, model_generative, language=language)
            return i, response_df
        except Exception:
            traceback.print_exc()
            return i, None

    completed = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(process_chunk, batch_num, i, chunk): idx
            for idx, (batch_num, i, chunk) in enumerate(chunks)
        }
        for future in as_completed(futures):
            idx = futures[future]
            _, result = future.result()
            if result is not None:
                all_responses[idx] = result
            completed += 1
            _progress(f"Labeling articles: batch {completed}/{total_batches}")

    valid_responses = [r for r in all_responses if r is not None]
    if valid_responses:
        result_df = pd.concat(valid_responses, ignore_index=True)
        df = pd.merge(df, result_df, left_on='index', right_on='id', how='left')
        # Resolve merge column name conflicts
        if 'sentimen_y' in df.columns:
            df['sentimen'] = df['sentimen_y']
            df = df.drop(columns=['sentimen_x', 'sentimen_y'], errors='ignore')
        if 'NER_y' in df.columns:
            df['NER'] = df['NER_y']
            df = df.drop(columns=['NER_x', 'NER_y'], errors='ignore')
        if 'topik' in df.columns:
            df['topik_berita'] = df['topik']
            df = df.drop(columns=['topik'], errors='ignore')
        df = df.drop(columns=['id', 'index'], errors='ignore')

    _progress(f"Labeling complete: {len(df)} articles processed")

    # ── Enforce English sentiment labels (catch any AI inconsistency) ─────
    _SENTIMENT_VALID = {'positive', 'negative', 'neutral'}
    _SENTIMENT_FALLBACK = {
        'positif': 'positive', 'positiv': 'positive', 'pos': 'positive',
        'negatif': 'negative', 'negativ': 'negative', 'neg': 'negative',
        'netral': 'neutral', 'nettral': 'neutral',
    }
    if 'sentimen' in df.columns:
        def _normalize_sentiment(x):
            if not pd.notna(x):
                return x
            v = str(x).lower().strip()
            if v in _SENTIMENT_VALID:
                return v
            return _SENTIMENT_FALLBACK.get(v, 'neutral')
        df['sentimen'] = df['sentimen'].map(_normalize_sentiment)

    # ── Normalize topics to the canonical 10 English labels ─────────────────
    # Canonical set
    _CANONICAL_TOPICS = {
        'economy and finance',
        'business and industry',
        'politics and government',
        'law and crime',
        'infrastructure and transportation',
        'energy and environment',
        'technology and innovation',
        'social and welfare',
        'lifestyle and sports',
        'other',
    }
    # Map Indonesian labels + common AI-generated variants → canonical English
    _TOPIC_MAP = {
        # ── Indonesian labels (from the ID-language AI prompt) ───────────
        'ekonomi dan keuangan':          'economy and finance',
        'bisnis dan industri':           'business and industry',
        'politik dan pemerintahan':      'politics and government',
        'hukum dan kriminal':            'law and crime',
        'infrastruktur dan transportasi':'infrastructure and transportation',
        'energi dan lingkungan':         'energy and environment',
        'teknologi dan inovasi':         'technology and innovation',
        'sosial dan kesejahteraan':      'social and welfare',
        'lifestyle dan olahraga':        'lifestyle and sports',
        # common AI short-forms in Indonesian
        'ekonomi':                       'economy and finance',
        'keuangan':                      'economy and finance',
        'bisnis':                        'business and industry',
        'industri':                      'business and industry',
        'politik':                       'politics and government',
        'pemerintahan':                  'politics and government',
        'hukum':                         'law and crime',
        'kriminal':                      'law and crime',
        'infrastruktur':                 'infrastructure and transportation',
        'transportasi':                  'infrastructure and transportation',
        'energi':                        'energy and environment',
        'lingkungan':                    'energy and environment',
        'teknologi':                     'technology and innovation',
        'inovasi':                       'technology and innovation',
        'sosial':                        'social and welfare',
        'kesejahteraan':                 'social and welfare',
        'olahraga':                      'lifestyle and sports',
        'hiburan':                       'lifestyle and sports',
        'gaya hidup':                    'lifestyle and sports',

        # English variant → canonical
        'economics and finance': 'economy and finance',
        'finance and economy': 'economy and finance',
        'finance': 'economy and finance',
        'economics': 'economy and finance',
        'business and economics': 'economy and finance',
        'business': 'business and industry',
        'industry': 'business and industry',
        'business and technology': 'business and industry',
        'politics': 'politics and government',
        'government': 'politics and government',
        'politics and governance': 'politics and government',
        'law': 'law and crime',
        'crime': 'law and crime',
        'law and justice': 'law and crime',
        'law and order': 'law and crime',
        'justice': 'law and crime',
        'infrastructure': 'infrastructure and transportation',
        'transportation': 'infrastructure and transportation',
        'transport': 'infrastructure and transportation',
        'energy': 'energy and environment',
        'environment': 'energy and environment',
        'energy and climate': 'energy and environment',
        'climate': 'energy and environment',
        'technology': 'technology and innovation',
        'innovation': 'technology and innovation',
        'technology and education': 'technology and innovation',
        'education and innovation': 'technology and innovation',
        'education and research': 'technology and innovation',
        'science and technology': 'technology and innovation',
        'science': 'technology and innovation',
        'education': 'social and welfare',
        'social': 'social and welfare',
        'welfare': 'social and welfare',
        'health': 'social and welfare',
        'healthcare': 'social and welfare',
        'culture': 'social and welfare',
        'education and culture': 'social and welfare',
        'religion': 'social and welfare',
        'social and culture': 'social and welfare',
        'society': 'social and welfare',
        'lifestyle': 'lifestyle and sports',
        'sports': 'lifestyle and sports',
        'sports and lifestyle': 'lifestyle and sports',
        'entertainment': 'lifestyle and sports',
        'entertainment and sports': 'lifestyle and sports',
        'sports and entertainment': 'lifestyle and sports',
        'travel': 'lifestyle and sports',
    }
    if 'topik_berita' in df.columns:
        def _normalize_topic(x):
            if not pd.notna(x):
                return x
            lowered = str(x).lower().strip()
            mapped = _TOPIC_MAP.get(lowered, lowered)
            # Any topic still not in the canonical set falls back to 'other'
            return mapped if mapped in _CANONICAL_TOPICS else 'other'
        df['topik_berita'] = df['topik_berita'].map(_normalize_topic)

    # ── Step 2: NER normalization ─────────────────────────────────────────
    if 'NER' in df.columns:
        df, _ = normalize_ner_agent(df, model_generative, language=language, progress_cb=_progress)
    else:
        df['NER'] = [[] for _ in range(len(df))]
        df['NER_normalized'] = [[] for _ in range(len(df))]

    # ── Step 3: Source normalization ──────────────────────────────────────
    if 'source_news' in df.columns:
        df, _ = normalize_source_agent(df, model_generative, language=language, progress_cb=_progress)
    else:
        df['normalized_source_news'] = ''

    _progress("Processing complete. Saving results...")
    return df

