import {useEffect,useState} from 'react';
import {api,query,errorText} from '../api';
import type {Run} from '../types';
const statuses:Record<string,string>={queued:'等待分析',running:'正在分析',succeeded:'分析完成',partial:'分析不完整',failed:'分析未完成',insufficient:'资料不足',cancelled:'任务已取消',interrupted:'任务已中断'};
export default function RunStatus({id,wid,onComplete}:{id:string;wid:string;onComplete?:()=>void}){
 const [run,setRun]=useState<Run|null>(null),[error,setError]=useState('');
 useEffect(()=>{let active=true,timer:ReturnType<typeof setTimeout>;async function poll(){try{const r=await api<Run>('/runs/'+id+query({workspace_id:wid}));if(!active)return;setRun(r);if(['queued','running'].includes(r.status))timer=setTimeout(()=>void poll(),900);else onComplete?.();}catch(e){if(active)setError(errorText(e));}}void poll();return()=>{active=false;clearTimeout(timer);};},[id,wid]);
 return <div className="run-status" role="status">{error?<p className="error">{error}</p>:run?<><strong>{statuses[run.status]||run.status}</strong><p className="small">已完成 {run.completed_batches} / {run.total_batches} 个批次；拒绝 {run.rejected_candidates} 项无有效依据或需保留本人修订的候选。</p>{run.result?.summary&&<p>{run.result.summary}</p>}{run.result?.note&&<p className="hint">{run.result.note}</p>}{run.result?.demo&&<p className="hint">合成情境的预创作演示，没有调用模型。</p>}{['queued','running'].includes(run.status)&&<button onClick={()=>void api('/runs/'+id+'/cancel',{method:'POST',json:{workspace_id:wid}}).catch(e=>setError(errorText(e)))}>取消任务</button>}</>:<p>读取任务状态…</p>}</div>;
}
