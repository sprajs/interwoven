import {afterEach, describe, expect, it, vi} from 'vitest'

const minimal = {format:1,taxonomy:{domains:[]},discoveries:[],links:[],world_person_years:null,details:{},population_file:'population/'+'a'.repeat(24)+'.json',people:{},places:{},organizations:{},concepts:{},societies:{}}
const path = 'core/'+'b'.repeat(24)+'.json'
afterEach(()=>{vi.unstubAllGlobals();vi.resetModules()})

describe('versioned loading',()=>{
  it('deduplicates simultaneous startup requests, including StrictMode',async()=>{
    vi.stubGlobal('document',{getElementById:()=>({textContent:JSON.stringify({format:1,version:'b'.repeat(24),core:path})})})
    const fetch=vi.fn().mockResolvedValue({ok:true,json:async()=>minimal})
    vi.stubGlobal('fetch',fetch)
    const {loadModel}=await import('./load.ts')
    const [a,b]=await Promise.all([loadModel(),loadModel()])
    expect(a).toBe(b);expect(fetch).toHaveBeenCalledTimes(1)
    expect(fetch.mock.calls[0]?.[0]).toBe('/data/'+path)
  })
  it('revalidates a manifest only when no HTML bootstrap exists',async()=>{
    vi.stubGlobal('document',{getElementById:()=>null})
    const fetch=vi.fn().mockResolvedValueOnce({ok:true,json:async()=>({format:1,core:path})}).mockResolvedValueOnce({ok:true,json:async()=>minimal})
    vi.stubGlobal('fetch',fetch)
    const {loadModel}=await import('./load.ts');await loadModel()
    expect(fetch.mock.calls[0]).toEqual(['/data/manifest.json',{cache:'no-cache'}])
  })
  it('allows startup retry after a network failure and rejects incompatible formats',async()=>{
    vi.stubGlobal('document',{getElementById:()=>({textContent:JSON.stringify({format:1,core:path})})})
    vi.stubGlobal('fetch',vi.fn().mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({ok:true,json:async()=>minimal}))
    const {loadModel}=await import('./load.ts')
    await expect(loadModel()).rejects.toThrow('offline')
    await expect(loadModel()).resolves.toHaveProperty('entries',[])
    vi.resetModules()
    vi.stubGlobal('document',{getElementById:()=>({textContent:'{"format":99}'})})
    await expect((await import('./load.ts')).loadModel()).rejects.toThrow('newer app')
  })
  it('scopes detail cache to its model version, preserves rejection for the error boundary',async()=>{
    const {buildModel}=await import('./model.ts')
    const {loadDetail}=await import('./load.ts')
    const payload={...minimal,details:{one:'details/'+'c'.repeat(24)+'.json'}}
    const model=buildModel(payload as never)
    const next=buildModel({...payload,details:{one:'details/'+'d'.repeat(24)+'.json'}} as never)
    const fetch=vi.fn().mockResolvedValue({ok:false,status:404})
    vi.stubGlobal('fetch',fetch)
    const first=loadDetail(model,'one')
    await expect(first).rejects.toThrow('404')
    expect(loadDetail(model,'one')).toBe(first)
    await expect(loadDetail(next,'one')).rejects.toThrow('404')
    expect(fetch).toHaveBeenCalledTimes(2)
    await expect(loadDetail(model,'missing')).rejects.toThrow('Unknown')
  })
})
