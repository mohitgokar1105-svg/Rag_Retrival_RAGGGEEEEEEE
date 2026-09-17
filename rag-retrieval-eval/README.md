# RAG retrieval evaluation

Most RAG write-ups report an answer-quality score and stop. That number can't
tell you whether a bad answer came from the retriever missing the chunk or the
model ignoring it, so this measures retrieval on its own.

Corpus is 25 pages of FastAPI documentation, ~35,000 words. The eval set is 52
questions written against it, grouped by difficulty. BM25 and TF-IDF are
implemented in the notebook — no vector database, no API calls.

## Run

```bash
pip install -r requirements.txt
python fetch_corpus.py
jupyter notebook rag_eval.ipynb
```

`fetch_corpus.py` pulls the docs into `corpus/`, which is gitignored, so no
third-party content is committed here.

## Results

| Config | chunks | recall@5 | MRR | hit@1 |
|---|---|---|---|---|
| fixed-60/15 + BM25 (baseline) | 787 | 71.7% | 0.575 | 50.0% |
| sentence-60 + BM25 | 723 | 67.4% | 0.568 | 50.0% |
| sentence-100 + BM25 | 419 | 71.7% | 0.513 | 39.1% |
| sentence-60 + TF-IDF | 723 | 73.9% | 0.627 | 56.5% |
| **sentence-60 + hybrid RRF** | 723 | **76.1%** | **0.632** | 54.3% |

### Hybrid retrieval beat the baseline by 8.7 points

67.4% to 76.1% recall@5 via reciprocal rank fusion. The same configuration lost
by 6.7 points on a smaller six-document sample corpus, which isolates corpus
scale rather than the method as the reason — stopping at the small corpus would
have produced the opposite conclusion.

### Lexical retrieval collapses on paraphrase

| Question group | n | recall@5 |
|---|---|---|
| wording overlaps the source | 16 | 100% |
| indirect | 11 | 82% |
| paraphrased | 19 | **53%** |

A 47-point gap between questions that reuse the document's vocabulary and
questions that don't. The paraphrased group is the one that resembles real user
queries.

### No score threshold separates unanswerable questions

Six questions have no answer in the corpus. The retriever returns its top 5 for
every one.

```
answerable    top BM25 score  mean 14.67  min  8.55
unanswerable  top BM25 score  mean 12.79  max 20.16
```

The ranges overlap — one unanswerable question outscored the mean answerable one.
Abstention needs a reranker or a sufficiency check, not a cutoff.

## Metrics

- `recall@k` — is the right document in the top k. Caps everything downstream: an
  unretrieved chunk can't be used regardless of model quality.
- `MRR` — how high it ranked. Context windows are finite and models weight early
  context more heavily.
- `hit@1` — was the top result right.

## Eval set

| Group | n | What it tests |
|---|---|---|
| overlap | 16 | wording matches the source document |
| paraphrased | 19 | same question, user's vocabulary |
| indirect | 11 | needs two ideas connected |
| unanswerable | 6 | nothing in the corpus covers it |

The grouping is what surfaced the paraphrase gap. A single aggregate recall number
hides it completely.

## Limitations

- Labels are document-level, so recall measures whether the right document came
  back, not the right passage. Chunk-level labels would be more precise and
  considerably more work.
- The eval set is hand-written and carries a bias toward questions its author
  thought to ask. Real query logs would be messier.
- No reranking stage. A cross-encoder over the top 20 is likely the largest single
  improvement available here.
- Lexical retrieval only. Dense embeddings would probably close much of the
  47-point paraphrase gap.

---

Corpus fetched from [FastAPI](https://github.com/fastapi/fastapi) documentation, MIT licensed.
