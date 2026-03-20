import threading


def generate_insight(df, model_generative, language='id'):
    # ============================================================
    # Source News Analysis
    # ============================================================
    df_news_source = df[["headline_title", "sentimen", "normalized_source_news"]]

    df_positif = df_news_source[df_news_source["sentimen"] == "positive"].copy()
    source_counts_pos = df_positif["normalized_source_news"].value_counts()
    _threshold_src_pos = source_counts_pos.nlargest(3).min()
    top_sources_pos = source_counts_pos[source_counts_pos >= _threshold_src_pos].index
    df_positif["source_count"] = df_positif["normalized_source_news"].map(source_counts_pos)
    df_positif = df_positif.sort_values(["source_count", "normalized_source_news"], ascending=False).drop(columns="source_count").reset_index(drop=True)
    df_positif = df_positif[df_positif["normalized_source_news"].isin(top_sources_pos)]

    df_negatif = df_news_source[df_news_source["sentimen"] == "negative"].copy()
    source_counts_neg = df_negatif["normalized_source_news"].value_counts()
    _threshold_src_neg = source_counts_neg.nlargest(3).min()
    top_sources_neg = source_counts_neg[source_counts_neg >= _threshold_src_neg].index
    df_negatif["source_count"] = df_negatif["normalized_source_news"].map(source_counts_neg)
    df_negatif = df_negatif.sort_values(["source_count", "normalized_source_news"], ascending=False).drop(columns="source_count").reset_index(drop=True)
    df_negatif = df_negatif[df_negatif["normalized_source_news"].isin(top_sources_neg)]

    positive_data = df_positif.drop(columns="sentimen").to_string(index=False)
    negative_data = df_negatif.drop(columns="sentimen").to_string(index=False)

    # Build dynamic bullet templates with actual source names and counts
    pos_header = ", ".join([f"{s} ({source_counts_pos[s]} berita)" for s in top_sources_pos])
    neg_header = ", ".join([f"{s} ({source_counts_neg[s]} berita)" for s in top_sources_neg])

    pos_bullets = "\n".join([f"- **{s} ({source_counts_pos[s]} berita):** ..." for s in top_sources_pos])
    neg_bullets = "\n".join([f"- **{s} ({source_counts_neg[s]} berita):** ..." for s in top_sources_neg])

    n_pos = len(top_sources_pos)
    n_neg = len(top_sources_neg)
    total_pos = source_counts_pos[top_sources_pos].sum()
    total_neg = source_counts_neg[top_sources_neg].sum()

    if language == 'en':
        pos_bullets_en = "\n".join([f"- **{s} ({source_counts_pos[s]} article{'s' if source_counts_pos[s] != 1 else ''}):** ..." for s in top_sources_pos])
        neg_bullets_en = "\n".join([f"- **{s} ({source_counts_neg[s]} article{'s' if source_counts_neg[s] != 1 else ''}):** ..." for s in top_sources_neg])
        prompt = f"""You are a news analyst. Below are news headlines from the top news sources, separated by sentiment.

    Your task:
    1. Summarize each sentiment section by news source.
    2. For each source, identify the main themes or topics discussed based on the headlines.
    3. Write one concise paragraph per source under each sentiment section.
    4. Note the volume of articles from each source. If some sources have significantly more or fewer articles than others, explicitly mention this (e.g., "with a dominant volume of coverage" or "despite relatively few articles").
    5. DO NOT add any introduction, conclusion, or closing remarks. Start your response directly from the **Positive:** section.
    6. MANDATORY: Create exactly {n_pos} bullet points for the Positive section and exactly {n_neg} bullet points for the Negative section, using the source names listed — no additions, removals, or substitutions.
    7. For the **Dominant:** section, write one paragraph concluding whether coverage from these sources overall leans positive or negative, based on total positive articles ({total_pos}) versus negative articles ({total_neg}), and explain what is driving that lean.
    8. Structure your response exactly as follows (replace ... with your analysis):

    **Positive:**
    {pos_bullets_en}

    **Negative:**
    {neg_bullets_en}

    **Dominant:** ...

    ---

    Positive data:
    {positive_data}

    Negative data:
    {negative_data}
    """
    else:
        prompt = f"""Kamu adalah seorang analis berita. Berikut adalah judul-judul berita dari sumber berita teratas, dipisahkan berdasarkan sentimen.

    Tugasmu:
    1. Rangkum setiap bagian sentimen berdasarkan sumber berita.
    2. Untuk setiap sumber, identifikasi tema atau topik utama yang dibahas berdasarkan judul-judul berita.
    3. Tulis satu paragraf ringkas per sumber di bawah setiap bagian sentimen.
    4. Perhatikan jumlah berita dari masing-masing sumber. Jika jumlah berita positif atau negatif dari suatu sumber tergolong sangat sedikit atau sangat banyak dibandingkan sumber lainnya, sebutkan hal ini secara eksplisit dalam insight-mu (contoh: "dengan jumlah berita yang sangat dominan" atau "meskipun jumlah beritanya relatif sedikit").
    5. JANGAN tambahkan kalimat pengantar, penutup, atau kesimpulan apapun. Mulai respons langsung dari bagian **Positif:**.
    6. WAJIB: Buat tepat {n_pos} bullet point untuk bagian Positif dan tepat {n_neg} bullet point untuk bagian Negatif, sesuai dengan nama sumber yang sudah tercantum — tidak boleh ditambah, dikurangi, atau diganti.
    7. Untuk bagian **Dominan:**, tulis satu paragraf kesimpulan yang menjelaskan apakah pemberitaan dari sumber-sumber ini secara keseluruhan lebih condong ke sentimen positif atau negatif, berdasarkan total jumlah berita positif ({total_pos} berita) dibandingkan negatif ({total_neg} berita) dan jelaskan apa yang menyebabkannya lebih condong.
    8. Susun responmu persis seperti ini (ganti ... dengan analisis yang sesuai):

    **Positif:**
    {pos_bullets}

    **Negatif:**
    {neg_bullets}

    **Dominan:** ...

    ---

    Data positif:
    {positive_data}

    Data negatif:
    {negative_data}
    """

    # Use NER_normalized if available (consistent with charts), fall back to NER
    ner_col = "NER_normalized" if "NER_normalized" in df.columns else "NER"

    # ============================================================
    # NER Analysis
    # ============================================================
    df_ner = df[["headline_title", "sentimen", ner_col]].copy()
    df_ner = df_ner.explode(ner_col)
    df_ner = df_ner.rename(columns={ner_col: "NER"})
    df_ner = df_ner[df_ner["NER"].notna() & (df_ner["NER"] != "tidak ada") & (df_ner["NER"] != "")]

    df_ner_positif = df_ner[df_ner["sentimen"] == "positive"].copy()
    ner_counts_positif = df_ner_positif["NER"].value_counts()
    _threshold_ner_pos = ner_counts_positif.nlargest(3).min()
    top_ner_positif = ner_counts_positif[ner_counts_positif >= _threshold_ner_pos].index
    df_ner_positif["ner_count"] = df_ner_positif["NER"].map(ner_counts_positif)
    df_ner_positif = df_ner_positif[df_ner_positif["NER"].isin(top_ner_positif)]
    df_ner_positif = df_ner_positif.sort_values(["ner_count", "NER"], ascending=False).drop(columns="ner_count").reset_index(drop=True)

    df_ner_negatif = df_ner[df_ner["sentimen"] == "negative"].copy()
    ner_counts_negatif = df_ner_negatif["NER"].value_counts()
    _threshold_ner_neg = ner_counts_negatif.nlargest(3).min()
    top_ner_negatif = ner_counts_negatif[ner_counts_negatif >= _threshold_ner_neg].index
    df_ner_negatif["ner_count"] = df_ner_negatif["NER"].map(ner_counts_negatif)
    df_ner_negatif = df_ner_negatif[df_ner_negatif["NER"].isin(top_ner_negatif)]
    df_ner_negatif = df_ner_negatif.sort_values(["ner_count", "NER"], ascending=False).drop(columns="ner_count").reset_index(drop=True)

    positive_ner_data = df_ner_positif.drop(columns="sentimen").to_string(index=False)
    negative_ner_data = df_ner_negatif.drop(columns="sentimen").to_string(index=False)

    # Build dynamic bullet templates with actual entity names and counts
    ner_pos_header = ", ".join([f"{e} ({ner_counts_positif[e]} sebutan)" for e in top_ner_positif])
    ner_neg_header = ", ".join([f"{e} ({ner_counts_negatif[e]} sebutan)" for e in top_ner_negatif])

    ner_pos_bullets = "\n".join([f"- **{e} ({ner_counts_positif[e]} sebutan):** ..." for e in top_ner_positif])
    ner_neg_bullets = "\n".join([f"- **{e} ({ner_counts_negatif[e]} sebutan):** ..." for e in top_ner_negatif])

    n_ner_pos = len(top_ner_positif)
    n_ner_neg = len(top_ner_negatif)
    total_ner_pos = ner_counts_positif[top_ner_positif].sum()
    total_ner_neg = ner_counts_negatif[top_ner_negatif].sum()

    if language == 'en':
        ner_pos_bullets_en = "\n".join([f"- **{e} ({ner_counts_positif[e]} mention{'s' if ner_counts_positif[e] != 1 else ''}):** ..." for e in top_ner_positif])
        ner_neg_bullets_en = "\n".join([f"- **{e} ({ner_counts_negatif[e]} mention{'s' if ner_counts_negatif[e] != 1 else ''}):** ..." for e in top_ner_negatif])
        prompt_ner = f"""You are a news analyst. Below are news headlines grouped by the most frequently mentioned named entities (NER), separated by sentiment.

    Your task:
    1. Summarize each sentiment section by the most frequently mentioned entities.
    2. For each entity, identify the context or main issues discussed in the related headlines.
    3. Write one concise paragraph per entity under each sentiment section.
    4. Note the mention frequency of each entity. If an entity appears significantly more or less often than others, explicitly mention this (e.g., "with a dominant frequency of mentions" or "despite relatively few mentions").
    5. DO NOT add any introduction, conclusion, or closing remarks. Start your response directly from the **Positive:** section.
    6. MANDATORY: Create exactly {n_ner_pos} bullet points for the Positive section and exactly {n_ner_neg} bullet points for the Negative section, using the entity names listed — no additions, removals, or substitutions.
    7. For the **Dominant:** section, write one paragraph concluding whether these entities overall appear more in positive or negative contexts, based on total positive mentions ({total_ner_pos}) versus negative mentions ({total_ner_neg}), and explain what is driving that direction.
    8. Structure your response exactly as follows (replace ... with your analysis):

    **Positive:**
    {ner_pos_bullets_en}

    **Negative:**
    {ner_neg_bullets_en}

    **Dominant:** ...

    ---

    Positive data (entities & headlines):
    {positive_ner_data}

    Negative data (entities & headlines):
    {negative_ner_data}
    """
    else:
        prompt_ner = f"""Kamu adalah seorang analis berita. Berikut adalah judul-judul berita yang dikelompokkan berdasarkan entitas (NER) yang paling sering disebutkan, dipisahkan berdasarkan sentimen.

    Tugasmu:
    1. Rangkum setiap bagian sentimen berdasarkan entitas yang paling sering muncul.
    2. Untuk setiap entitas, identifikasi konteks atau isu utama yang dibahas dalam berita terkait entitas tersebut.
    3. Tulis satu paragraf ringkas per entitas di bawah setiap bagian sentimen.
    4. Perhatikan jumlah kemunculan setiap entitas. Jika suatu entitas muncul jauh lebih sering atau lebih jarang dibandingkan entitas lainnya, sebutkan hal ini secara eksplisit dalam insight-mu (contoh: "dengan frekuensi kemunculan yang sangat dominan" atau "meskipun kemunculannya relatif sedikit").
    5. JANGAN tambahkan kalimat pengantar, penutup, atau kesimpulan apapun. Mulai respons langsung dari bagian **Positif:**.
    6. WAJIB: Buat tepat {n_ner_pos} bullet point untuk bagian Positif dan tepat {n_ner_neg} bullet point untuk bagian Negatif, sesuai dengan nama entitas yang sudah tercantum — tidak boleh ditambah, dikurangi, atau diganti.
    7. Untuk bagian **Dominan:**, tulis satu paragraf kesimpulan yang menjelaskan apakah entitas-entitas ini secara keseluruhan lebih sering muncul dalam konteks positif atau negatif, berdasarkan total sebutan positif ({total_ner_pos} sebutan) dibandingkan negatif ({total_ner_neg} sebutan), dan jelaskan apa yang menyebabkannya lebih condong ke arah tersebut.
    8. Susun responmu persis seperti ini (ganti ... dengan analisis yang sesuai):

    **Positif:**
    {ner_pos_bullets}

    **Negatif:**
    {ner_neg_bullets}

    **Dominan:** ...

    ---

    Data positif (entitas & judul berita):
    {positive_ner_data}

    Data negatif (entitas & judul berita):
    {negative_ner_data}
    """

    # ============================================================
    # Topic Analysis
    # ============================================================
    df_topik = df[["headline_title", "sentimen", "topik_berita"]]

    df_topik_positif = df_topik[df_topik["sentimen"] == "positive"].copy()
    topik_counts_positif = df_topik_positif["topik_berita"].value_counts()
    _threshold_topik_pos = topik_counts_positif.nlargest(3).min()
    top_topik_positif = topik_counts_positif[topik_counts_positif >= _threshold_topik_pos].index
    df_topik_positif["topik_count"] = df_topik_positif["topik_berita"].map(topik_counts_positif)
    df_topik_positif = df_topik_positif[df_topik_positif["topik_berita"].isin(top_topik_positif)]
    df_topik_positif = df_topik_positif.sort_values(["topik_count", "topik_berita"], ascending=False).drop(columns="topik_count").reset_index(drop=True)

    df_topik_negatif = df_topik[df_topik["sentimen"] == "negative"].copy()
    topik_counts_negatif = df_topik_negatif["topik_berita"].value_counts()
    _threshold_topik_neg = topik_counts_negatif.nlargest(3).min()
    top_topik_negatif = topik_counts_negatif[topik_counts_negatif >= _threshold_topik_neg].index
    df_topik_negatif["topik_count"] = df_topik_negatif["topik_berita"].map(topik_counts_negatif)
    df_topik_negatif = df_topik_negatif[df_topik_negatif["topik_berita"].isin(top_topik_negatif)]
    df_topik_negatif = df_topik_negatif.sort_values(["topik_count", "topik_berita"], ascending=False).drop(columns="topik_count").reset_index(drop=True)

    positive_topik_data = df_topik_positif.drop(columns="sentimen").to_string(index=False)
    negative_topik_data = df_topik_negatif.drop(columns="sentimen").to_string(index=False)

    # Build dynamic bullet templates with actual topic names and counts
    topik_pos_header = ", ".join([f"{t} ({topik_counts_positif[t]} berita)" for t in top_topik_positif])
    topik_neg_header = ", ".join([f"{t} ({topik_counts_negatif[t]} berita)" for t in top_topik_negatif])

    topik_pos_bullets = "\n".join([f"- **{t} ({topik_counts_positif[t]} berita):** ..." for t in top_topik_positif])
    topik_neg_bullets = "\n".join([f"- **{t} ({topik_counts_negatif[t]} berita):** ..." for t in top_topik_negatif])

    n_topik_pos = len(top_topik_positif)
    n_topik_neg = len(top_topik_negatif)
    total_topik_pos = topik_counts_positif[top_topik_positif].sum()
    total_topik_neg = topik_counts_negatif[top_topik_negatif].sum()

    if language == 'en':
        topik_pos_bullets_en = "\n".join([f"- **{t} ({topik_counts_positif[t]} article{'s' if topik_counts_positif[t] != 1 else ''}):** ..." for t in top_topik_positif])
        topik_neg_bullets_en = "\n".join([f"- **{t} ({topik_counts_negatif[t]} article{'s' if topik_counts_negatif[t] != 1 else ''}):** ..." for t in top_topik_negatif])
        prompt_topik = f"""You are a news analyst. Below are news headlines grouped by the most frequently occurring topics, separated by sentiment.

    Your task:
    1. Summarize each sentiment section by the most frequently occurring topics.
    2. For each topic, identify the specific sub-themes or issues most discussed based on the headlines.
    3. Write one concise paragraph per topic under each sentiment section.
    4. Note the article volume for each topic. If a topic has significantly more or fewer articles than others, explicitly mention this (e.g., "with a dominant volume of coverage" or "despite relatively few articles").
    5. DO NOT add any introduction, conclusion, or closing remarks. Start your response directly from the **Positive:** section.
    6. MANDATORY: Create exactly {n_topik_pos} bullet points for the Positive section and exactly {n_topik_neg} bullet points for the Negative section, using the topic names listed — no additions, removals, or substitutions.
    7. For the **Dominant:** section, write one paragraph concluding whether coverage across these topics overall leans positive or negative, based on total positive articles ({total_topik_pos}) versus negative articles ({total_topik_neg}), and explain what is driving that lean.
    8. Structure your response exactly as follows (replace ... with your analysis):

    **Positive:**
    {topik_pos_bullets_en}

    **Negative:**
    {topik_neg_bullets_en}

    **Dominant:** ...

    ---

    Positive data (topics & headlines):
    {positive_topik_data}

    Negative data (topics & headlines):
    {negative_topik_data}
    """
    else:
        prompt_topik = f"""Kamu adalah seorang analis berita. Berikut adalah judul-judul berita yang dikelompokkan berdasarkan topik yang paling sering muncul, dipisahkan berdasarkan sentimen.

    Tugasmu:
    1. Rangkum setiap bagian sentimen berdasarkan topik yang paling sering muncul.
    2. Untuk setiap topik, identifikasi subtema atau isu spesifik yang paling banyak dibahas berdasarkan judul-judul berita.
    3. Tulis satu paragraf ringkas per topik di bawah setiap bagian sentimen.
    4. Perhatikan jumlah berita di setiap topik. Jika suatu topik memiliki jumlah berita yang jauh lebih banyak atau lebih sedikit dibandingkan topik lainnya, sebutkan hal ini secara eksplisit dalam insight-mu (contoh: "dengan volume berita yang sangat dominan" atau "meskipun jumlah beritanya relatif sedikit").
    5. JANGAN tambahkan kalimat pengantar, penutup, atau kesimpulan apapun. Mulai respons langsung dari bagian **Positif:**.
    6. WAJIB: Buat tepat {n_topik_pos} bullet point untuk bagian Positif dan tepat {n_topik_neg} bullet point untuk bagian Negatif, sesuai dengan nama topik yang sudah tercantum — tidak boleh ditambah, dikurangi, atau diganti.
    7. Untuk bagian **Dominan:**, tulis satu paragraf kesimpulan yang menjelaskan apakah pemberitaan berdasarkan topik-topik ini secara keseluruhan lebih condong ke sentimen positif atau negatif, berdasarkan total berita positif ({total_topik_pos} berita) dibandingkan negatif ({total_topik_neg} berita), dan jelaskan apa yang menyebabkannya lebih condong ke arah tersebut.
    8. Susun responmu persis seperti ini (ganti ... dengan analisis yang sesuai):

    **Positif:**
    {topik_pos_bullets}

    **Negatif:**
    {topik_neg_bullets}

    **Dominan:** ...

    ---

    Data positif (topik & judul berita):
    {positive_topik_data}

    Data negatif (topik & judul berita):
    {negative_topik_data}
    """

    # Run all 3 prompts concurrently via threading
    results = {"source": None, "ner": None, "topik": None}

    def run_source():
        results["source"] = model_generative.generate_content(prompt).text

    def run_ner():
        results["ner"] = model_generative.generate_content(prompt_ner).text

    def run_topik():
        results["topik"] = model_generative.generate_content(prompt_topik).text

    threads = [
        threading.Thread(target=run_source),
        threading.Thread(target=run_ner),
        threading.Thread(target=run_topik),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Kesimpulan prompt — runs after the three above since it depends on their outputs
    if language == 'en':
        prompt_kesimpulan = """You are a senior news analyst. Below are three analysis results covering news sources, topics, and named entities (NER), separated by positive and negative sentiment. Each analysis has a **Dominant** section summarizing the overall tendency.

Your task:
1. Write ONE concise paragraph each for positive and negative news. Focus on: who the main actors are, what issues are raised, and why they carry a positive or negative tone — all qualitatively with no numbers.
2. For **Overall Conclusion**, synthesize the **Dominant** sections from all three analyses and write one concise paragraph that decisively states whether overall coverage leans positive or negative, with a causal explanation.
3. DO NOT use numbers, percentages, or statistics. Focus on qualitative narrative — who, what, and why.
4. DO NOT add any introduction or closing remarks. Start directly from the heading.
5. Use EXACTLY this format:

**Positive News Summary:**
[One concise paragraph: key actors, issues raised, and why it carries a positive tone]

**Negative News Summary:**
[One concise paragraph: key actors, issues raised, and why it carries a negative tone]

**Overall Conclusion:**
[One paragraph decisively stating the overall lean and explaining the cause qualitatively]

---
## Source Analysis
""" + results["source"] + """

## Topic Analysis
""" + results["topik"] + """

## Entity (NER) Analysis
""" + results["ner"]
    else:
        prompt_kesimpulan = """Kamu adalah seorang analis berita senior. Berikut adalah tiga hasil analisis berita mencakup sumber berita, topik, dan entitas (NER), dipisahkan berdasarkan sentimen positif dan negatif. Setiap analisis memiliki bagian **Dominan** yang menggambarkan kecenderungan keseluruhan.

Tugasmu:
1. Buat SATU kalimat pembuka lalu SATU paragraf ringkas untuk berita positif dan satu untuk berita negatif. Fokus pada: siapa aktor utamanya, isu apa yang diangkat, dan mengapa hal itu terjadi — semua secara kualitatif tanpa angka.
2. Untuk **Kesimpulan Dominan**, sintesiskan bagian **Dominan** dari ketiga analisis dan buat satu paragraf ringkas yang memutuskan secara tegas apakah pemberitaan secara keseluruhan lebih condong positif atau negatif, disertai penjelasan kausal mengapa kecenderungan itu terjadi.
3. JANGAN gunakan angka, persentase, atau statistik apapun. Fokus pada narasi kualitatif — siapa, apa, dan mengapa.
4. JANGAN tambahkan kalimat pengantar atau penutup. Mulai langsung dari heading.
5. Gunakan format berikut PERSIS:

**Kesimpulan Berita Positif:**
[Satu paragraf ringkas: aktor utama, isu yang diangkat, dan mengapa bernuansa positif]

**Kesimpulan Berita Negatif:**
[Satu paragraf ringkas: aktor utama, isu yang diangkat, dan mengapa bernuansa negatif]

**Kesimpulan Dominan:**
[Satu paragraf yang memutuskan kecenderungan keseluruhan dan menjelaskan penyebabnya secara kualitatif]

---
## Analisis Sumber Berita
""" + results["source"] + """

## Analisis Topik
""" + results["topik"] + """

## Analisis Entitas (NER)
""" + results["ner"]

    results["kesimpulan"] = model_generative.generate_content(prompt_kesimpulan).text

    if language == 'en':
        combined_output = (
            "## Source Insight\n\n"
            + results["source"]
            + "\n\n---\n\n"
            + "## Topic Insight\n\n"
            + results["topik"]
            + "\n\n---\n\n"
            + "## Entity (NER) Insight\n\n"
            + results["ner"]
            + "\n\n---\n\n"
            + "## Summary\n\n"
            + results["kesimpulan"]
        )
    else:
        combined_output = (
            "## Sumber Berita Insight\n\n"
            + results["source"]
            + "\n\n---\n\n"
            + "## Topik Insight\n\n"
            + results["topik"]
            + "\n\n---\n\n"
            + "## Entitas (NER) Insight\n\n"
            + results["ner"]
            + "\n\n---\n\n"
            + "## Kesimpulan\n\n"
            + results["kesimpulan"]
        )

    return combined_output
