You are answering a factual question about Acme Corp company policy using the
provided document excerpts. Each excerpt is labeled with a chunk_id and an
effective_date. Company policies are sometimes revised; a later document may
explicitly supersede an earlier one, or simply carry a later effective_date for
the same fact. When multiple excerpts address the same entity, identify the
CURRENT (most recent, non-superseded) value before answering — do not assume
the first excerpt you see is authoritative. Some questions require combining
two or three excerpts (e.g. a base amount plus a bonus) — read carefully
before deciding whether one excerpt answers the question fully.

Question: {question}

Document excerpts:
{excerpts}

Respond with ONLY this JSON object, no other text before or after it:
{{"value": "<the current value, as a bare number or short phrase with no units or extra words -- e.g. \"4\" not \"4 hours\", \"750\" not \"$750 USD\">", "chunk_id": "<id(s) of the excerpt(s) that support this, joined with '+' if more than one was needed>"}}
