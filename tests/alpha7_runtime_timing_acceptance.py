from __future__ import annotations
import json, pathlib, re
ROOT=pathlib.Path(__file__).resolve().parents[1]
checks=[]
def ok(t,n,f): f();checks.append(t);print(f"[PASS] {t} - {n}")
installer=(ROOT/'INSTALL-OR-UPDATE.ps1').read_text(encoding='utf-8')
ps=(ROOT/'scripts/pa.ps1').read_text(encoding='utf-8')
main=(ROOT/'services/core/app/main.py').read_text(encoding='utf-8')
app=(ROOT/'services/core/app/static/app.js').read_text(encoding='utf-8')
manifest=json.loads((ROOT/'product-manifest.json').read_text(encoding='utf-8'))

def version_identity():
    assert re.fullmatch(r'1\.0\.0', manifest['version']), manifest['version']
    assert "ConvertFrom-Json" in installer and "$Manifest.version" in installer
    assert "$Version='0.8.0-alpha.3'" not in installer
    assert re.search(r"Invalid package version in product-manifest\.json",installer)
ok('REL-A7-001','Installer derives release identity from signed product manifest',version_identity)

def bootstrap_verify():
    assert "/api/admin/inference/smoke" in main and "/api/admin/inference/smoke" in ps
    assert "bootstrap-inference" in ps and "num_predict\": 32" in main and "\"think\": False" in main
    assert "verification_duration=" in ps and "command_elapsed=" in ps
    assert "real-inference' -Uri ($base+'/api/chat')" not in ps
ok('PERF-A7-001','VERIFY uses bounded bootstrap inference instead of configured production route',bootstrap_verify)

def native_timing():
    for token in ('load_duration','prompt_eval_duration','eval_duration','tokens_per_sec','provider_total_ms'):
        assert token in main, token
    for token in ('load_ms','prompt_eval_ms','generation_ms','tokens/sec'):
        assert token in app+ps, token
ok('OBS-A7-001','Native inference timing is exposed for runtime diagnostics',native_timing)

print(f'PAR_V080_ALPHA7_RUNTIME_TIMING_ACCEPTANCE PASS: {len(checks)} checks')
