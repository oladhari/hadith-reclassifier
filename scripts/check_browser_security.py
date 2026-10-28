#!/usr/bin/env python3
"""Optional real-browser security checks; uses local Chrome and Playwright.
No writes, account access, AI calls, or playback of audio are performed.
"""
import asyncio,json,os,re
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]

async def main():
 base=os.environ.get('RESEARCH_TEST_URL','http://127.0.0.1:3110')
 report={'base':base,'checks':{},'page_errors':[]}
 catalogue=json.loads((ROOT/'frontend/src/content/media-catalogue.json').read_text())
 hidden=json.loads((ROOT/'frontend/src/content/video-visibility.json').read_text())['hidden']
 archive=json.loads((ROOT/'frontend/src/content/archive-index.json').read_text())
 video=next(item for item in archive if item['kind']=='video' and catalogue[str(item['id'])].get('visible') and catalogue[str(item['id'])]['canonical_id']==item['id'] and item['id'] not in hidden)
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox'])
  context=await browser.new_context(viewport={'width':420,'height':900},bypass_csp=False)
  page=await context.new_page();console=[]
  page.on('pageerror',lambda error:report['page_errors'].append(str(error)[:250]))
  page.on('console',lambda message:console.append(message.text))
  payload='<img src=x onerror="window.__audit_xss=1">'
  response=await page.goto(base+'/explore?q='+quote(payload),wait_until='networkidle',timeout=60000)
  assert response.status==200
  assert await page.locator('input[name=q]').input_value()==payload
  assert await page.evaluate('typeof window.__audit_xss')=='undefined'
  report['checks']['reflected_markup_does_not_execute']=True
  await page.get_by_role('button',name='فتح القائمة',exact=True).click()
  await page.wait_for_function("document.querySelector('.menu-toggle').getAttribute('aria-expanded')==='true'")
  report['checks']['trusted_hydration_mobile_navigation_works']=True
  await page.get_by_role('link',name='المكتبة',exact=True).click()
  await page.wait_for_url(base+'/library',timeout=30000)
  await page.get_by_role('heading',name='الكتب والبحوث الكاملة',exact=True).wait_for()
  report['checks']['client_side_navigation_works_under_csp']=True
  # Inject only into this test browser's intercepted HTML response. Parser-
  # inserted scripts model markup injection; DevTools-created scripts can be
  # trusted by strict-dynamic and are not a valid negative CSP test.
  async def injected_fixture(route):
   original=await route.fetch()
   html=await original.text()
   nonce=re.search(r"'nonce-([^']+)'",original.headers['content-security-policy']).group(1)
   inserted='<script>window.__audit_parser_blocked=1</script><script nonce="'+nonce+'">window.__audit_nonce_allowed=1</script>'
   await route.fulfill(response=original,body=html.replace('</body>',inserted+'</body>'))
  await page.route('**/?audit_fixture=1',injected_fixture)
  await page.goto(base+'/?audit_fixture=1',wait_until='networkidle',timeout=60000)
  assert await page.evaluate('typeof window.__audit_parser_blocked')=='undefined'
  assert await page.evaluate('window.__audit_nonce_allowed')==1
  await page.unroute('**/?audit_fixture=1',injected_fixture)
  report['checks']['csp_blocks_unnonced_parser_script_and_allows_matching_nonce']=True
  frame_responses=[]
  def record_response(r):
   if '/documents/' in r.url:frame_responses.append({'status':r.status,'content_type':r.headers.get('content-type','')})
  page.on('response',record_response)
  await page.goto(base+'/library/1078',wait_until='networkidle',timeout=60000)
  await page.locator('iframe').wait_for()
  assert await page.locator('iframe').count()==1
  assert any(r['status']==200 and 'application/pdf' in r['content_type'] for r in frame_responses)
  report['checks']['pdf_iframe_loads_with_correct_mime']=True
  await page.goto(base+'/library/'+str(video['id']),wait_until='networkidle',timeout=60000)
  result=await page.locator('video').evaluate("""el=>new Promise(resolve=>{
   if(el.readyState>=1){resolve({loaded:true,duration:el.duration});return;}
   const timer=setTimeout(()=>resolve({loaded:false,timeout:true}),30000);
   el.addEventListener('loadedmetadata',()=>{clearTimeout(timer);resolve({loaded:true,duration:el.duration})},{once:true});
   el.addEventListener('error',()=>{clearTimeout(timer);resolve({loaded:false,error:el.error?.code})},{once:true});
   el.preload='metadata';el.load();
  })""")
  assert result.get('loaded'),result
  report['checks']['kept_video_metadata_loads_under_csp']={'id':video['id'],'duration':result['duration']}
  report['expected_inline_csp_violation_observed']=any('Content Security Policy' in s or 'violates' in s for s in console)
  assert not report['page_errors'],report['page_errors']
  await browser.close()
 report['passed']=True
 out=Path(os.environ.get('AUDIT_OUTPUT',ROOT/'output/security/browser-local.json'));out.write_text(json.dumps(report,indent=2)+'\n')
 print('Browser security checks passed:',json.dumps(report['checks']))

asyncio.run(main())
