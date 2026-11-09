/** Build an immutable old app against today's data for an apples-to-apples comparison. */
import {execFileSync} from 'node:child_process'
import {mkdtemp, mkdir, cp, rm, writeFile} from 'node:fs/promises'
import {resolve, dirname} from 'node:path'
import {fileURLToPath} from 'node:url'
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..')
const revision=process.argv[2] ?? '4d37f65'
const commit=execFileSync('git',['rev-parse',revision+'^{commit}'],{cwd:root,encoding:'utf8'}).trim()
await mkdir(resolve(root,'.cache'),{recursive:true})
const source=await mkdtemp(resolve(root,'.cache/baseline-source-'))
try {
  const archive=execFileSync('git',['archive',commit,'app','tools','data'],{cwd:root,maxBuffer:100*1024*1024})
  execFileSync('tar',['-x','-C',source],{input:archive})
  await rm(resolve(source,'data'),{recursive:true,force:true})
  await cp(resolve(root,'data'),resolve(source,'data'),{recursive:true})
  execFileSync('npm',['ci'],{cwd:resolve(source,'app'),stdio:'inherit'})
  execFileSync('npm',['run','build'],{cwd:resolve(source,'app'),stdio:'inherit'})
  await mkdir(resolve(root,'.cache/baseline'),{recursive:true})
  await cp(resolve(source,'app/dist'),resolve(root,'.cache/baseline'),{recursive:true})
  await writeFile(resolve(root,'.cache/baseline/baseline.json'),JSON.stringify({app_commit:commit,data_commit:execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),data_note:'Current data files copied into historical app, including any uncommitted data edits.'},null,2)+'\n')
} finally {
  await rm(source,{recursive:true,force:true})
}
