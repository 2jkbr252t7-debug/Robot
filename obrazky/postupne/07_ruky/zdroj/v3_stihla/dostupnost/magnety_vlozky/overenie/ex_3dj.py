import re,sys,html,json
def T(s): return html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',s))).strip()
for fn in sys.argv[1:]:
    f=open(fn,encoding='utf-8',errors='replace').read()
    title=re.search(r'<title>(.*?)</title>',f,re.S)
    h1=re.search(r'<h1[^>]*>(.*?)</h1>',f,re.S)
    var=re.search(r'<p class="p-variants[^"]*">(.*?)</p>',f,re.S)
    st=re.search(r'<p class="p-delivery__stock[^"]*">(.*?)</p>',f,re.S)
    lim=re.search(r'<p class="p-stock[^"]*" data-limit="(\d+)">(.*?)</p>',f,re.S)
    ld=None
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>',f,re.S):
        try:
            j=json.loads(m.group(1))
            if j.get('@type')=='Product': ld=j
        except Exception: pass
    price=re.search(r'class="price[^"]*"[^>]*>(.*?)</',f,re.S)
    # visible price block
    pb=re.search(r'<div class="p-price[^"]*"[^>]*>(.*?)</div>\s*</div>',f,re.S)
    print('==',fn)
    print(' title:',T(title.group(1)) if title else None)
    print(' h1:',T(h1.group(1)) if h1 else None)
    print(' variant:',T(var.group(1)) if var else None)
    print(' stock:',T(st.group(1)) if st else None,'| hidden:',(lim.group(1),T(lim.group(2))[:60]) if lim else None)
    if ld: print(' ld:',ld.get('name'),ld['offers'].get('price'),ld['offers'].get('availability'),ld.get('sku'))
    print(' priceblock:',T(pb.group(1))[:200] if pb else None)
