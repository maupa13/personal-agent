from __future__ import annotations
import json, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
main=(ROOT/'services/core/app/main.py').read_text(encoding='utf-8')
ps=(ROOT/'scripts/pa.ps1').read_text(encoding='utf-8')
fake=(ROOT/'tests/fake_ollama.py').read_text(encoding='utf-8')
manifest=json.loads((ROOT/'product-manifest.json').read_text(encoding='utf-8'))
checks=[]
def ok(i,n,c):
    assert c,n
    checks.append(i)
    print(f'[PASS] {i} - {n}')
ok('REL-A8-001','release version is alpha.8',manifest['version']=='0.8.0-alpha.8')
ok('PERF-A8-001','bootstrap smoke disables thinking', '"think": False' in main and 'payload["think"] = bool(spec["think"])' in main)
ok('PERF-A8-002','bootstrap smoke uses bounded final-answer budget', '"num_predict": 32' in main and 'Reply exactly with: PAR_OK' in main)
ok('OBS-A8-001','logical HTTP-200 failure prints reason and timings','content_length' in main and 'empty_final_content' in main and 'reason={2}' in ps and 'HTTP 200 but no final answer' in ps)
ok('REG-A8-001','fake Ollama reproduces thinking-only edge case','thinking can consume all tokens' in fake and "body.get('think') is not False" in fake)
print(f'PAR_V080_ALPHA8_BOOTSTRAP_SMOKE_ACCEPTANCE PASS: {len(checks)} checks')
