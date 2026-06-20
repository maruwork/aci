# Multi-language taint fixture pack (G3)

Each file encodes one **source -> sink** flow that a taint engine should catch
but a single-pattern matcher would miss without taint tracking:

- `app.js` — JavaScript: untrusted `req.query` flows through a local variable
  into `eval` (code injection).
- `svc.py` — Python: untrusted `request.args.get(...)` flows through a local
  variable into `eval` (code injection).

The orchestrated `semgrep` lane carries taint-mode rules
(`aci.ci14.taint-*-code-injection` in
`shared/python/package_assets/analyzers/aci-semgrep-rules.yml`) that detect
these cross-statement flows. `test_semgrep_lane_detects_multilang_taint_flow`
asserts a normalized source->sink finding for **both** JS and Python through the
external-analyzer lane — the G3 closure gate.
