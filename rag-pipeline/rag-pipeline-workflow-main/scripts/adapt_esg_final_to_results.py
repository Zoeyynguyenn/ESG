import zipfile, io, sys, re, openpyxl, logging
logging.disable(logging.CRITICAL)
zpath, xin, out = sys.argv[1], sys.argv[2], sys.argv[3]
wb=openpyxl.load_workbook(io.BytesIO(zipfile.ZipFile(zpath).read(xin)), read_only=True, data_only=True)
ws=wb['정량 데이터']; data=list(ws.iter_rows(values_only=True)); hdr=data[0]; ix={h:i for i,h in enumerate(hdr)}
HEAD=["영역","카테고리","서브카테고리","항목","기준 및 설명","단위","단위_설명","GRI","GRI_설명","SASB","KBIZ","K-ESG",
      "Value","Year","Answer unit","Disclosure status","Reporting boundary","Source document/page","Source URL",
      "Link check","Source detail / calculation note","Confidence","File URL","Evidence"]
out_wb=openpyxl.Workbook(); o=out_wb.active; o.title="ESG Results"; o.append(HEAD)
area=cat=sub=None; nrow=0

_STRUCT_PATTERNS = [
    (re.compile(r'empSttus',re.I),       lambda y: f'{y}_empSttus.json'),
    (re.compile(r'exctvSttus',re.I),     lambda y: f'{y}_exctvSttus.json'),
    (re.compile(r'outcmpnyDrctrNdChangeSttus',re.I), lambda y: f'{y}_outcmpnyDrctrNdChangeSttus.json'),
    (re.compile(r'재무.*OFS|OFS.*재무',re.I), lambda y: f'{y}_재무_OFS.json'),
    (re.compile(r'재무.*CFS|CFS.*재무',re.I), lambda y: f'{y}_재무_CFS.json'),
    (re.compile(r'indvdlByPay',re.I),    lambda y: f'{y}_indvdlByPay.json'),
]
def _canonical_doc(basis, year):
    if not basis: return ""
    t = str(basis)
    for pat, fn in _STRUCT_PATTERNS:
        if pat.search(t):
            return fn(year)
    return ""  # non-structured → leave empty; URL matching handles it

def g(r,k):
    i=ix.get(k);
    return r[i] if (i is not None and i<len(r)) else None
for r in data[1:]:
    if g(r,'영역'): area=g(r,'영역')
    if g(r,'카테고리'): cat=g(r,'카테고리')
    if g(r,'서브카테고리'): sub=g(r,'서브카테고리')
    item=g(r,'항목') or sub
    unit=g(r,'단위')
    for y in ('2023','2024','2025'):
        val=g(r,f'{y}년 값'); src=g(r,f'{y}년 출처'); basis=g(r,f'{y}년 기준')
        if val is None and src is None and basis is None: continue
        nd = (val is None) or str(val).strip()=='' or str(val).strip().lower().startswith('not disclos')
        sdp = _canonical_doc(basis, y)
        row={"영역":area,"카테고리":cat,"서브카테고리":sub,"항목":item,"단위":unit,
             "Value":("" if nd else val),"Year":int(y),
             "Disclosure status":("Not disclosed" if nd else "matched"),
             "Source document/page":sdp,"Source URL":src}
        o.append([row.get(h,"") if row.get(h) is not None else "" for h in HEAD]); nrow+=1
out_wb.save(out); print("adapted rows:",nrow,"->",out)
