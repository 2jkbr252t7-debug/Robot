import re,sys,html
def T(s): return html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',s))).strip()
for fn in sys.argv[1:]:
    f=open(fn,encoding='utf-8',errors='replace').read()
    rows=re.findall(r'<tr[^>]*>(.*?)</tr>',f,re.S)
    out=[]
    for r in rows:
        if 'tooltip_title' in r or 'specification' in r:
            cells=[T(c) for c in re.findall(r'<td[^>]*>(.*?)</td>',r,re.S)]
            cells=[c for c in cells if c]
            if cells: out.append(' = '.join(cells[:2]))
    print(fn.split('/')[-1],':: ', ' ; '.join(out)[:900])
