import sys, json
import os
PAGE = os.environ.get('PAGE','index.html')
from playwright.sync_api import sync_playwright
shots = json.loads(sys.argv[1])
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--no-sandbox'])
    for s in shots:
        pg = b.new_page(viewport={'width': s.get('w',390), 'height': s.get('h',760)})
        errs = []
        pg.on('console', lambda m: errs.append(m.text) if m.type in ('error','warning') else None)
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto('http://127.0.0.1:8765/' + PAGE + '')
        pg.wait_for_timeout(4500)
        if s.get('js'): pg.evaluate(s['js'])
        if s.get('enter', True): pg.evaluate("document.getElementById('gate').style.display='none'")
        pg.wait_for_timeout(s.get('wait',1500))
        pg.screenshot(path=s['out'])
        print(s['out'], pg.title(), 'sun', pg.evaluate("window.sansa?window.sansa.sun():null"), errs[:6])
        pg.close()
    b.close()
