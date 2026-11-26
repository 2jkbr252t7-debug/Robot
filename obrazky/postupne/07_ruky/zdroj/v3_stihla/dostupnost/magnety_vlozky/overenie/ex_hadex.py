import re,sys,html
for fn in sys.argv[1:]:
    f=open(fn,encoding='utf-8',errors='replace').read()
    h1=re.search(r'<h1>(.*?)<div',f,re.S)
    av=re.search(r'class="[^"]*availability">\s*(.*?)\s*</div>',f,re.S)
    q=re.search(r'quantity">\s*(.*?)\s*</div>',f,re.S)
    pr=re.search(r'class="with-vat">\s*(.*?)\s*</div>',f,re.S)
    pw=re.search(r'class="without-vat">\s*(.*?)\s*</div>',f,re.S)
    # quantity price tiers
    tiers=re.findall(r'(\d+\s*-\s*\d+\s*ks|\d+\+?\s*ks a v[ií]ce|od \d+ ks)[^<]{0,5}</[^>]+>\s*<[^>]+>\s*([\d,]+\s*Kč[^<]*)',f)
    br=re.search(r'class="branches">(.*?)</div>\s*</div>\s*</div>\s*</div>',f,re.S)
    brt=re.sub(r'<[^>]+>',' ',br.group(1)) if br else ''
    print(fn, '|', html.unescape(re.sub(r'\s+',' ',h1.group(1)).strip()) if h1 else None, '|', av.group(1).strip() if av else None, '|', q.group(1).strip() if q else None,'|',pr.group(1) if pr else None,'|',pw.group(1) if pw else None,'| branches:',re.sub(r'\s+',' ',brt).strip()[:200], '| tiers', tiers[:5])
