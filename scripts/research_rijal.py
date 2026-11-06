#!/usr/bin/env python3
"""Read-only, cached Shamela research. No model calls or automatic narrator grades."""
import argparse
import hashlib
import json
import urllib.request
from datetime import UTC,datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LIBRARY=ROOT/'backend/app/research/rijal-library.json'
CACHE=ROOT/'data/research/rijal-sources/lookups'


def call(name,arguments):
    request={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':arguments}}
    encoded=json.dumps(request,ensure_ascii=False,sort_keys=True).encode();key=hashlib.sha256(encoded).hexdigest()
    CACHE.mkdir(parents=True,exist_ok=True);pointer=CACHE/f'{key}.request.json'
    if pointer.exists():
        reference=json.loads(pointer.read_text());body=(CACHE/reference['response_file']).read_bytes()
        if hashlib.sha256(body).hexdigest()!=reference['sha256']:raise ValueError('Cache checksum mismatch')
    else:
        req=urllib.request.Request('https://mcp.shamela.ws',data=encoded,headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'})
        with urllib.request.urlopen(req,timeout=90) as response:body=response.read()
        payload=json.loads(body)
        if 'error' in payload or payload.get('result',{}).get('isError'):raise RuntimeError('Shamela retrieval failed; no evidence recorded')
        sha=hashlib.sha256(body).hexdigest();filename=f'{sha}.response.json';(CACHE/filename).write_bytes(body)
        pointer.write_text(json.dumps({'request':request,'retrieved_at':datetime.now(UTC).isoformat(),'response_file':filename,'sha256':sha},ensure_ascii=False,indent=2))
    result=json.loads(body)['result']
    if result.get('structuredContent') is not None:return result['structuredContent']
    return {'content':result.get('content',[])}


def validate_candidate(candidate,page):
    required=['narrator_name','critic_name','exact_quote','source_url','printed_locator','identity_status','review_state','entry_context']
    if any(not candidate.get(key) for key in required):raise ValueError('Missing evidence fields')
    if candidate['entry_context'] not in page['text']:raise ValueError('Narrator entry is not verbatim in retrieved source')
    if candidate['exact_quote'] not in candidate['entry_context']:raise ValueError('Quote falls outside the selected narrator entry')
    if candidate['narrator_name'] not in candidate['entry_context']:raise ValueError('Narrator name is missing from selected entry')
    if candidate['review_state']!='unreviewed':raise ValueError('Retrieval alone cannot claim scholarly review')
    if candidate['source_url']!=f"https://shamela.ws/book/{page['book_id']}/{page['page_id']}":raise ValueError('Wrong source page')


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('books')
    find=sub.add_parser('find');find.add_argument('--query',action='append',required=True);find.add_argument('--book-id',type=int,action='append',default=[])
    opened=sub.add_parser('open');opened.add_argument('--book-id',required=True,type=int);opened.add_argument('--page-id',required=True,type=int)
    args=parser.parse_args();library=json.loads(LIBRARY.read_text());books={b['id']:b for b in library['books']}
    if args.command=='books':print(json.dumps(library,ensure_ascii=False,indent=2));return
    if args.command=='open':
        if args.book_id<1 or args.page_id<1:parser.error('Book and page IDs must be positive')
        result=call('shamela_open',{'book_id':args.book_id,'page_id':args.page_id,'max_chars':16000})
    else:
        if any(i not in books for i in args.book_id):parser.error('Add and verify the requested book in rijal-library.json first')
        first=call('shamela_find',{'keywords':args.query,'book_queries':[books[i]['title'] for i in args.book_id],'difficulty':'medium'})
        result=call('shamela_find_scoped',{'queries':args.query,'book_ids':args.book_id,'difficulty':'medium','limit':10}) if args.book_id else first
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
