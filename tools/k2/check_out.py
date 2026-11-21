"""python3 check_out.py IN OUT [sec|quiz] — validate a cleaned 2級 chapter bundle (optionally only one part)."""
import json,re,sys
JP=re.compile(r'[　-ヿ㐀-鿿！-｠]')
BAD=re.compile(r'Day\s*\d|p\.\s*\d|本で|教科書|正誤表|明日|昨日|今日の|レッスン|ノート|復習タブ')
I=json.load(open(sys.argv[1])); O=json.load(open(sys.argv[2])); bad=0
PART=sys.argv[3] if len(sys.argv)>3 else 'all'
O.setdefault('sections',[]); O.setdefault('quiz',[])
if PART=='quiz': I['sections']=[]
if PART=='sec': I['quiz']=[]
si={s['key'] for s in I['sections']}; so={s['key']:s for s in O['sections']}
qi={q['id'] for q in I['quiz']}; qo={q['id']:q for q in O['quiz']}; drop=set(O.get('drop',[]))
for k in si-set(so): print('thiếu section',k); bad+=1
for k in qi-set(qo)-drop: print('thiếu quiz',k); bad+=1
for k,s in so.items():
    for f in ('heading_vi','body_vi'):
        if JP.search(s.get(f,'')): print('JP',k,f,JP.findall(s[f])[:8]); bad+=1
    for f in ('heading_ja','body_ja','body_vi'):
        m=BAD.search(s.get(f,'') or '')
        if m: print('ref',k,f,m.group(0)); bad+=1
for k,q in qo.items():
    for f in ('q_vi','exp_vi'):
        if JP.search(q.get(f,'')): print('JP',k,f,JP.findall(q[f])[:8]); bad+=1
    for f in ('exp_ja','exp_vi'):
        m=BAD.search(q.get(f,'')); 
        if m: print('ref',k,f,m.group(0)); bad+=1
print(f"{len(so)} sections, {len(qo)} quiz, {len(drop)} drop, {bad} lỗi")
