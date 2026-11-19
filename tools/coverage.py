import json,re,collections,sys
d=json.load(open(sys.argv[1])); mp=json.load(open(sys.argv[2]))
cls=mp['classes'];mem=mp['members']
txt=''
for o in d['ops']:
    for k in ('anchor','code','old','new'):
        v=o.get(k)
        if isinstance(v,str): txt+=v+'\n'
refs=collections.Counter()
for m in re.finditer(r'L([a-z][a-z0-9]{0,3});->([\w$<>]+)(:[^\s`]+|\([^)]*\)\S+)',txt):
    c,n,s=m.groups()
    if c=='h1' or n.startswith('mod'): continue
    refs[(c,n,s)]+=1
ok=0;miss=[];nocls=[]
for (c,n,s),k in refs.items():
    if c not in cls: nocls.append((c,n,s));continue
    mm=mem.get(c,{}); key=n+s
    if key in mm.get('fields' if s.startswith(':') else 'methods',{}): ok+=1
    else: miss.append((c,n,s))
print('member unik:',len(refs),'terpetakan:',ok,'gagal:',len(miss),'kelas belum ada:',sorted(set(x[0] for x in nocls)))
if len(sys.argv)>3:
    for x in miss: print('MISS',x,'->',cls.get(x[0]))
