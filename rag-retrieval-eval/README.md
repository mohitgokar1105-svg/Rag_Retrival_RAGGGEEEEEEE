# RAG retrieval evaluation

Most RAG write-ups report an answer-quality score and stop. That number can't
tell you whether a bad answer came from the retriever missing the chunk or the
model ignoring it, so this measures retrieval on its own.

Corpus is 25 pages of FastAPI documentation, ~35,000 words. The eval set is 52
questions written against it, grouped by difficulty. BM25 and TF-IDF are
implemented in the notebook. Dense retrieval uses `all-MiniLM-L6-v2` from
sentence-transformers, run locally. No vector database, no API calls.

## Run

```bash
pip install -r requirements.txt
python fetch_corpus.py
jupyter notebook rag_eval.ipynb
```

`fetch_corpus.py` pulls the docs into `corpus/`, which is gitignored, so no
third-party content is committed here. The first run downloads the embedding
model (about 90 MB).

## Results

All rows use sentence-60 chunks unless stated.

| Config | chunks | recall@5 | MRR | hit@1 |
|---|---|---|---|---|
| fixed-60/15 + BM25 (baseline) | 787 | 71.7% | 0.575 | 50.0% |
| sentence-60 + BM25 | 723 | 67.4% | 0.568 | 50.0% |
| sentence-100 + BM25 | 419 | 71.7% | 0.513 | 39.1% |
| sentence-60 + TF-IDF | 723 | 73.9% | 0.627 | 56.5% |
| sentence-60 + hybrid RRF (BM25 + TF-IDF) | 723 | 76.1% | 0.632 | 54.3% |
| **sentence-60 + dense (MiniLM)** | 723 | **87.0%** | **0.766** | **69.6%** |
| sentence-60 + hybrid RRF (BM25 + dense) | 723 | 84.8% | 0.712 | 60.9% |
| sentence-60 + hybrid RRF (all three) | 723 | 82.6% | 0.710 | 63.0% |

### Dense retrieval beat every lexical configuration

87.0% recall@5 against 76.1% for the best lexical setup (+10.9 points) and 67.4%
for plain BM25 on the same chunks (+19.6 points). MRR and hit@1 move the same way
(0.766 and 69.6%).

Fusing BM25 into the dense ranker did not help: 84.8% against 87.0%. That is one
question's difference at n=46, so it is not evidence that fusion hurts, only that
it did not help here.

### Hybrid retrieval beat BM25 among the lexical methods

67.4% to 76.1% recall@5 via reciprocal rank fusion. The same configuration lost
by 6.7 points on a smaller six-document sample corpus, which isolates corpus
scale rather than the method as the reason. Stopping at the small corpus would
have produced the opposite conclusion.

### Dense retrieval closes about half of the paraphrase gap

| Retriever | overlap (n=16) | paraphrased (n=19) | indirect (n=11) |
|---|---|---|---|
| BM25 | 100% | 32% | 82% |
| TF-IDF | 100% | 58% | 64% |
| hybrid BM25 + TF-IDF | 100% | 53% | 82% |
| dense | 100% | 74% | 91% |
| hybrid BM25 + dense | 100% | 74% | 82% |
| hybrid all three | 100% | 68% | 82% |

The lexical hybrid fell from 100% to 53% when questions stopped reusing the
document's vocabulary, a 47-point gap. Dense retrieval held 74%, recovering about
21 of those points. It still misses 5 of the 19 paraphrased questions, and the
paraphrased group is the one that resembles real user queries.

### No score threshold separates unanswerable questions

Six questions have no answer in the corpus. Every retriever returns its top 5
for all of them.

```
BM25    answerable   top score   mean 14.67   min 8.55
        unanswerable top score   mean 12.79   max 20.16

dense   answerable   top cosine  mean 0.558   min 0.346
        unanswerable top cosine  mean 0.414   max 0.488
```

BM25 is clearly unusable for this: one unanswerable question outscored the
answerable mean. Dense is closer, since the highest unanswerable score (0.488)
sits below the answerable mean (0.558), but the lowest answerable score (0.346)
sits below that, so no single cutoff gets both groups right. Abstention needs a
reranker or a sufficiency check, not a cutoff.

## Metrics

- `recall@k`: is the right document in the top k. Caps everything downstream: an
  unretrieved chunk can't be used regardless of model quality.
- `MRR`: how high it ranked. Context windows are finite and models weight early
  context more heavily.
- `hit@1`: was the top result right.

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
- There are 46 answerable questions, so one question moves recall by 2.2 points.
  Differences of a question or two, such as dense (87.0%) against BM25 + dense
  (84.8%), are within noise.
- One small embedding model, one run. Larger embedding models and fine-tuning
  were not tested.
- No reranking stage. A cross-encoder over the top 20 is the most likely next
  improvement, particularly for the paraphrased questions dense still misses.

---

Corpus fetched from [FastAPI](https://github.com/fastapi/fastapi) documentation, MIT licensed.
