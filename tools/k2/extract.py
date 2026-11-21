"""python3 tools/k2/extract.py LESSONS_DIR OUT_DIR CHAPTER — bundle the 2級 lessons of one chapter (e.g. B4) into OUT_DIR/<ch>.json.
LESSONS_DIR holds the lesson JSON files downloaded from the study artifact (collection "lessons")."""
import json,glob,sys
from difflib import SequenceMatcher
LD,OD=sys.argv[1],sys.argv[2]
def ckey(c):
    a,b=c[1:].split('.'); return (c[0],int(a),int(b))
for ch in sys.argv[3:]:
    secs=[];quiz=[];terms={};keys=[]
    for f in sorted(glob.glob(LD+'/**/*.json',recursive=True)):
        d=json.load(open(f)); d=d.get('data',d)
        if d['kind']=='learn':
            for i,s in enumerate(d.get('sections',[])):
                if s['code'].split('.')[0]==ch:
                    secs.append({"key":f"{d['date']}#{i}","code":s['code'],"heading_ja":s.get('heading_ja',''),"body_ja":s['body_ja'],"body_vi":s.get('body_vi','')})
            for t in d.get('terms',[]):
                pass
        if any(c.split('.')[0]==ch for c in d.get('codes',[])):
            for t in d.get('terms',[]): terms.setdefault(t['ja'],{k:t.get(k) for k in ('ja','yomi','vi','note')})
        for q in d.get('quiz',[]):
            if q.get('code','').split('.')[0]!=ch: continue
            k=q['q_ja']+'|'.join(q['options'])
            if any(SequenceMatcher(None,k,u).ratio()>0.85 for u in keys): continue
            keys.append(k)
            quiz.append({"id":f"{ch}-{len(quiz)+1:03d}","code":q['code'],"q_ja":q['q_ja'],"q_vi":q.get('q_vi',''),"options":q['options'],"answer":q['answer'],"exp_ja":q.get('exp_ja',''),"exp_vi":q.get('exp_vi','')})
    secs.sort(key=lambda s:(ckey(s['code']),s['key']))
    json.dump({"chapter":ch,"sections":secs,"quiz":quiz,"terms":list(terms.values())},open(f'{OD}/{ch}.json','w'),ensure_ascii=False,indent=1)
    print(ch,len(secs),'sections',len(quiz),'quiz',len(terms),'terms',sum(len(s['body_ja'])+len(s['body_vi']) for s in secs),'chars')
