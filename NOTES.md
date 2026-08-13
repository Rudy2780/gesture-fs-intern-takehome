# Implementation Notes

## Approach

`ask_question()` is a simple RAG flow: retrieval of the top 3 chunks
using FAISS similarity search, creation of context string from them, 
formatting of prompt using the prompt template given and generation 
using flan-t5-base. The main() function creates an interactive loop 
that loads the knowledge base and the model once and keeps answering 
queries till `quit`. I kept both functions simple, at the scale the 
assignment asked for, plus one small print helper shared by the two 
CLI modes.

## Design decisions

**Context length cap.** The flan-t5 tokenizer limits the prompt size to 512 tokens,
and the question is put *last* in the template provided, so in case the prompt 
exceeds the limit, the question gets silently cut, the model sees context but 
no question and answers blind. Based on my measurements of this repository's actual data, 
the corpus can be divided into 38 pieces, with the three longest chunks together totaling 
about 1,490 characters (or 430 tokens with the template). This is enough for 
short questions but too tight for long questions typed into an interactive CLI. 
I set the maximum size of the concatenated context to 1,300 characters (375 tokens), 
ensuring the space for the question. When the limit is exceeded, it cuts off the 
end of the *last* piece, which is the least relevant one, since similarity search 
returns results sorted by relevance.

The 1,300 character cap only applies to the context string sent to the LLM. The
`sources` list returned to the caller is always the full chunk text, since
showing the user where an answer came from and fitting a prompt into the model
are two different jobs.

Chunks are joined with blank lines (`\n\n`) rather than
spaces, keeping the three retrieved passages distinct in the prompt instead of
running together.

## Observations about the data

`data/` contains two files outside the marketing agency's domain: an employee
handbook and a product FAQ for an unrelated SaaS product ("AcmeCloud") whose
pricing-tier language could plausibly compete with the agency's pricing docs in
embedding space. Retrieval precision against these is not just assumed, 
`tests/test_bonus.py::test_pricing_question_avoids_product_faq` asserts that
agency pricing queries don't pull AcmeCloud content.


## Bonus items

- **Error handling** — Input for whitespace or empty will be skipped, missing 
  data exits with a clear message, Ctrl+C/D exit fine
- **`--query` argument** — single-question mode: answers once and exits
- **Additional tests** — `tests/test_bonus.py` adds three cases: exact k=3 source
  count, decoy-file rejection, and structural validity on whitespace-only input.
- **Type hints** — `ask_question` returns `dict[str, str | list[str]]`; helper
  and `main` are hinted. The `vector_store`/`llm` params were not done, reason 
  being because FAISS/Callable imports are needed and docstrings already describe 
  parameters

The base `main()` was made with 12 lines originally but with the guard clauses 
and interrupt handling from the bonus criteria pushed it past that.

## Things I would improve next

- **Persist the FAISS index** — rebuilding embeddings on every launch costs
  15–20s of startup; serializing the index to disk and invalidating on data
  changes would make the CLI feel instant.
- **Filter the knowledge base** — the off-topic files currently rely
  on embedding distance to stay out of results, production would filter by
  source metadata or maintain separate indices per domain.
- **Larger model behind the same interface** — flan-t5-base gives terse,
  extractive answers ("$5,500/month"). The pipeline is model-agnostic, so
  swapping in a stronger local model would improve answer
  quality without touching retrieval.
