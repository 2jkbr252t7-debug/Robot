import re,sys,html,json
for fn in sys.argv[1:]:
    f=open(fn,encoding='utf-8',errors='replace').read()
    title=re.search(r'<title>(.*?)</title>',f,re.S)
    st=re.search(r'<span class="u-sr-only">([^<]*na sklade[^<]*)</span>',f) or re.search(r'<span class="u-sr-only">([^<]*(?:sklad|dostup)[^<]*)</span>',f)
    seo=re.search(r'seoStock\\":(\d+)',f)
    pr=re.search(r'\\"prices\\":\[(.*?)\]',f)
    tiers=[]
    if pr:
        for m in re.finditer(r'grossPrice\\":([\d.]+),\\"priceQuantity\\":(\d+)',pr.group(1)): tiers.append(f"{m.group(2)}ks:{m.group(1)}")
    mult=re.search(r'Mnohonásobnosť: (\d+)',f)
    pack=re.search(r'(Druh balenia|Balenie)[^<]{0,5}</[^>]+>\s*<[^>]+>([^<]{1,60})',f)
    print(fn.split('/')[-1],'|',html.unescape(title.group(1)) if title else None,'|',st.group(1) if st else None,'| seoStock',seo.group(1) if seo else None,'| gross',tiers,'| mult',mult.group(1) if mult else None)
