# TITANOS 2099 BACKBONE — 750 PACK

This package is a runnable offline-first control-plane skeleton plus a
machine-readable 0..750 artifact frontload.

Run:
    python -m titanos.cli doctor
    python -m titanos.cli run

The runtime owns state, queue, receipts, checkpoints and bounded worker
dispatch. YAML contracts are inputs to the runtime; YAML existence alone
does not imply a capability is implemented.
