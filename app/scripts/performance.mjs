/** Repeatable real-browser measurements. Run after npm run build. No simulation. */
import {chromium} from 'playwright'
import {spawn, execFileSync} from 'node:child_process'
import {readFile, writeFile, mkdir, mkdtemp, cp, rm} from 'node:fs/promises'
import {resolve, dirname} from 'node:path'
import {tmpdir, cpus, platform, release} from 'node:os'
import {fileURLToPath} from 'node:url'
import assert from 'node:assert/strict'
import {createHash} from 'node:crypto'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..')
const args = process.argv.slice(2)
const value = (key, fallback) => args.includes(key) ? args[args.indexOf(key)+1] : fallback
const repetitions = Number(value('--runs', '7'))
const output = resolve(root, value('--out', '.cache/performance/browser.json'))
const baseline = resolve(root, value('--baseline', '.cache/baseline'))
const candidate = resolve(root, value('--candidate', 'app/dist'))
const processes = []
async function serve(directory) {
  const child = spawn('python3',[resolve(root,'tools/serve.py'),'--directory',directory,'--port','0'],{cwd:root,stdio:['ignore','pipe','pipe']})
  processes.push(child)
  return await new Promise((resolvePromise,reject) => {
    child.stdout.on('data',data=>{const url=data.toString().match(/http:\/\/127\.0\.0\.1:\d+/)?.[0];if(url) resolvePromise(url)})
    child.stderr.on('data', data=>process.stderr.write(data))
    child.once('exit',code=>{if(code) reject(new Error(`Server exited ${code}`))})
  })
}
function observer() {
  window.__longTasks=[]
  new PerformanceObserver(list=>window.__longTasks.push(...list.getEntries().map(e=>({start:e.startTime,duration:e.duration})))).observe({type:'longtask',buffered:true})
  const fill=CanvasRenderingContext2D.prototype.fill
  CanvasRenderingContext2D.prototype.fill=function(...params) {
    const result=fill.apply(this,params)
    if(!window.__drawing && this.canvas.closest('main .canvas-frame, .timeline')) {
      window.__drawing=performance.now()
      requestAnimationFrame(()=>{window.__ready=performance.now()})
    }
    return result
  }
}
async function metrics(page) {
  await page.waitForFunction(()=>window.__ready>0)
  await page.evaluate(() => document.fonts.ready)
  return page.evaluate(()=>({
    ready_ms:window.__ready,
    draw_ms:window.__drawing,
    fcp_ms:performance.getEntriesByName('first-contentful-paint')[0]?.startTime ?? null,
    resources:performance.getEntriesByType('resource').map(e=>({path:new URL(e.name).pathname,bytes:e.transferSize,encoded:e.encodedBodySize,decoded:e.decodedBodySize,start:e.startTime,end:e.responseEnd})),
    document_bytes:performance.getEntriesByType('navigation')[0].transferSize,
    long_tasks:window.__longTasks.filter(e=>e.start<=window.__ready),
  }))
}
const profiles=[{name:'local',latency:0,throughput:-1,cpu:1},{name:'10mbps-40ms-4x',latency:40,throughput:1250000,cpu:4}]
const results={metadata:{date:new Date().toISOString(),commit:execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),hardware:cpus()[0].model,platform:platform()+' '+release(),runs:repetitions,metric:'Navigation to first data canvas draw plus the next animation frame. Not LCP or field INP.'},measurements:[],checks:{}}
const browser=await chromium.launch({channel:'chrome',headless:true})
try {
  const manifest=JSON.parse(await readFile(resolve(candidate,'data/manifest.json'),'utf8'))
  results.metadata.working_tree_dirty=execFileSync('git',['status','--porcelain'],{cwd:root,encoding:'utf8'}).length>0
  results.metadata.core_version=manifest.version
  results.metadata.index_sha256=createHash('sha256').update(await readFile(resolve(candidate,'index.html'))).digest('hex')
  results.metadata.baseline_atlas_sha256=createHash('sha256').update(await readFile(resolve(baseline,'data/atlas.json'))).digest('hex')
  const core=JSON.parse(await readFile(resolve(candidate,'data',manifest.core),'utf8'))
  // Optimistic control: same real core and a useful canvas of every dated record,
  // but no framework, labels, filtering, tooltips or layout collision handling.
  const control=await mkdtemp(resolve(tmpdir(),'interwoven-control-'))
  await cp(resolve(candidate,'data'),resolve(control,'data'),{recursive:true})
  await writeFile(resolve(control,'index.html'),`<!doctype html><html><head><link rel="preload" as="fetch" crossorigin="anonymous" href="/data/${manifest.core}"></head><body><div class="timeline"><canvas width="1200" height="700"></canvas></div><script>fetch('/data/${manifest.core}').then(r=>r.json()).then(data=>{const ctx=document.querySelector('canvas').getContext('2d');for(const [i,d] of data.discoveries.entries()){if(d.t===undefined)continue;ctx.beginPath();ctx.rect(10+((d.t+4000)/6026)*1170,10+(i%80)*8,4,4);ctx.fill();}})</script></body></html>`)
  const urls={baseline:await serve(baseline),candidate:await serve(candidate),control:await serve(control)}
  results.metadata.browser=browser.version()
  for(const profile of profiles) for(const [variant,url] of Object.entries(urls)) {
    for(let run=0;run<repetitions;run++) {
      const context=await browser.newContext({viewport:{width:1440,height:900}})
      await context.addInitScript(observer)
      const page=await context.newPage()
      const errors=[];page.on('pageerror',e=>errors.push(e.message))
      const cdp=await context.newCDPSession(page)
      await cdp.send('Network.enable')
      await cdp.send('Network.clearBrowserCache')
      await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:profile.latency,downloadThroughput:profile.throughput,uploadThroughput:profile.throughput})
      await cdp.send('Emulation.setCPUThrottlingRate',{rate:profile.cpu})
      for(const cache of ['cold','warm']) {
        await page.goto(url,{waitUntil:'load'})
        const measurement=await metrics(page)
        results.measurements.push({profile:profile.name,variant,cache,run,...measurement})
        if(variant==='candidate') {
          assert(!measurement.resources.some(r=>/MapView|land-|details\/|population\//.test(r.path)), 'Startup fetched deferred data or views')
          assert.equal(measurement.resources.filter(r=>/\/core\//.test(r.path)).length,1)
          if(cache==='warm') assert.equal(measurement.resources.filter(r=>/\/core\/|\/assets\//.test(r.path)).reduce((sum,r)=>sum+r.bytes,0),0,'Warm assets must be served from cache')
        }
      }
      assert.deepEqual(errors,[])
      await context.close()
    }
    console.log(`Measured ${variant}, ${profile.name}`)
  }
  results.checks.startup_lazy_loading=true
  results.checks.warm_immutable_assets_no_network=true
  // Functional tests, first/repeated detail requests and failures.
  const context=await browser.newContext({viewport:{width:1440,height:900}})
  const page=await context.newPage()
  const errors=[];page.on('pageerror',e=>errors.push(e.message))
  const detailRequests=[];page.on('request',r=>{if(r.url().includes('/details/'))detailRequests.push(r.url())})
  await page.goto(urls.candidate)
  const first=core.discoveries.find(d=>d.t>0&&d.t<1900&&d.summary)
  const file=core.details[first.id]
  const full=JSON.parse(await readFile(resolve(candidate,'data',file),'utf8'))
  const latencies=[]
  for(let i=0;i<2;i++) {
    await page.evaluate(id=>{
      window.__detailStart=performance.now()
      window.__detailReady=null
      const observer=new MutationObserver(()=>{
        if(document.querySelector('.detail h2')) {
          observer.disconnect()
          requestAnimationFrame(()=>window.__detailReady=performance.now()-window.__detailStart)
        }
      })
      observer.observe(document.body,{childList:true,subtree:true})
      location.hash += '&id='+encodeURIComponent(id)
    },first.id)
    await page.getByRole('complementary',{name:first.name,exact:true}).waitFor()
    await page.waitForFunction(()=>window.__detailReady!==null)
    latencies.push(await page.evaluate(()=>window.__detailReady))
    assert.equal(await page.locator('.detail h2').textContent(),full.entry.name)
    await page.getByRole('button',{name:'Close',exact:true}).click()
  }
  assert.equal(detailRequests.length,1,'Repeated open must reuse the same detail promise')
  results.detail={id:first.id,first_ms:latencies[0],repeat_ms:latencies[1],requests:detailRequests.length}
  for(const [view,selector] of [['map','.zoom-buttons'],['trends','.trends'],['index','.index'],['timeline','main .canvas-frame']]) {
    await page.getByRole('tab',{name:view[0].toUpperCase()+view.slice(1),exact:true}).click()
    await page.locator(selector).waitFor()
  }
  assert.deepEqual(errors,[])
  // Search is functional and keyboard dismissal leaves the app usable.
  await page.getByRole('searchbox').fill('steam')
  await page.waitForFunction(()=>document.querySelectorAll('.search-result').length>0 || document.querySelector('.search-results')?.textContent.toLowerCase().includes('steam'))
  await page.getByRole('searchbox').fill('')
  await page.keyboard.press('Escape')
  await page.screenshot({path:resolve(dirname(output),'timeline.png')})
  results.checks.all_views=true
  // Deep links directly into a lazy-loaded detail must resolve.
  await page.goto(urls.candidate+'/#view=map&id='+encodeURIComponent(first.id))
  await page.getByRole('complementary',{name:first.name,exact:true}).waitFor()
  results.checks.deep_link=true
  await context.close()
  // Missing lazy assets surface an actionable error instead of an endless spinner.
  const failContext=await browser.newContext()
  const failPage=await failContext.newPage()
  await failPage.route('**/data/details/**',r=>r.fulfill({status:404,body:'missing'}))
  await failPage.goto(urls.candidate+'/#id='+encodeURIComponent(first.id))
  await failPage.getByRole('alert').waitFor()
  assert(await failPage.getByRole('button',{name:'Reload',exact:true}).isVisible())
  await failContext.close()
  results.checks.failed_detail_has_recovery=true
  // Browser restart: retain only the on-disk browser profile, not JS/in-memory state.
  const diskProfile=await mkdtemp(resolve(tmpdir(),'interwoven-browser-cache-'))
  let persistent=await chromium.launchPersistentContext(diskProfile,{channel:'chrome',headless:true})
  let diskPage=await persistent.newPage()
  await diskPage.goto(urls.candidate)
  await diskPage.evaluate(()=>document.fonts.ready)
  await persistent.close()
  persistent=await chromium.launchPersistentContext(diskProfile,{channel:'chrome',headless:true})
  await persistent.addInitScript(observer)
  diskPage=await persistent.newPage()
  const diskCDP=await persistent.newCDPSession(diskPage)
  await diskCDP.send('Network.enable')
  const diskHits=[]
  diskCDP.on('Network.responseReceived',e=>{if(e.response.fromDiskCache) diskHits.push(new URL(e.response.url).pathname)})
  await diskPage.goto(urls.candidate)
  results.disk_restart=await metrics(diskPage)
  results.disk_restart.hits=diskHits
  assert(diskHits.some(path=>path.includes('/core/')),'Core did not survive browser restart in disk cache')
  await persistent.close()
  await rm(diskProfile,{recursive:true,force:true})
  results.checks.disk_cache_survives_restart=true
  // Keep an old tab open across publication; a new navigation must get the new core,
  // while an old tab still resolves its old immutable details. Source JSON is untouched.
  const fixture=await mkdtemp(resolve(tmpdir(),'interwoven-cache-edit-'))
  await cp(candidate,fixture,{recursive:true})
  const fixtureURL=await serve(fixture)
  const editContext=await browser.newContext()
  const oldPage=await editContext.newPage()
  await oldPage.goto(fixtureURL)
  await oldPage.getByRole('tab',{name:'Timeline',exact:true}).waitFor()
  const changed=JSON.parse(execFileSync('python3',[resolve(root,'tools/cache_fixture.py'),fixture,first.id],{cwd:root,encoding:'utf8'}))
  assert.notEqual(changed.before.version,changed.after.version)
  await oldPage.evaluate(id=>{location.hash += '&id='+encodeURIComponent(id)},first.id)
  await oldPage.getByRole('complementary',{name:first.name,exact:true}).waitFor()
  assert(!(await oldPage.locator('.detail .summary').textContent()).includes('Cache invalidation fixture.'))
  const editPage=await editContext.newPage()
  await editPage.addInitScript(observer)
  const invalidationStart=performance.now()
  await editPage.goto(fixtureURL+'/#id='+encodeURIComponent(first.id))
  await editPage.getByRole('complementary',{name:first.name,exact:true}).waitFor()
  assert((await editPage.locator('.detail .summary').textContent()).includes('Cache invalidation fixture.'))
  results.invalidation={...(await metrics(editPage)),old_version:changed.before.version,new_version:changed.after.version,total_harness_ms:performance.now()-invalidationStart}
  assert(results.invalidation.resources.some(r=>r.path.endsWith(changed.after.core)&&r.bytes>0),'Changed core was not fetched')
  assert(results.invalidation.resources.filter(r=>r.path.startsWith('/assets/')).every(r=>r.bytes===0),'Dataset update invalidated code cache')
  await editContext.close()
  results.checks.new_version_and_old_tab_coexist=true
  results.checks.invalidation_preserves_code_cache=true
  await rm(fixture,{recursive:true,force:true})
  await rm(control,{recursive:true,force:true})
} finally {
  await browser.close()
  for(const child of processes) child.kill('SIGTERM')
  await mkdir(dirname(output),{recursive:true})
  await writeFile(output,JSON.stringify(results,null,2)+'\n')
  console.log(`Saved ${output}`)
}
