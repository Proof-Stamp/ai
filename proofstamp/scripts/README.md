# ProofStamp helper scripts

For a normal verified ProofStamp run, prefer the one-command finalizer after the final session artifact has been written:

```bash
python scripts/finalize_proofstamp.py path/to/session.proofstamp.json
```

It validates the session against the bundled v1 JSON Schema using only the Python standard library, creates the detached receipt, validates the receipt schema, independently re-verifies exact artifact bytes, and emits both the `mailto:` URI and fallback email text.

The lower-level scripts remain available for debugging and independent use:

- `validate_proofstamp.py`
- `create_receipt.py`
- `verify_proofstamp.py`
- `create_mailto.py`
