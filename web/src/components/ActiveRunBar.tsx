import {useEffect,useState} from 'react';
import {api,query,errorText} from '../api';
import type {Run} from '../types';
export default function ActiveRunBar({wid,onOpen}:{wid:string;onOpen:(mode:string)=>void}){
 const [run,setRun]=useState<Run|null>(null),[error,setError]=useState('');
 useEffect(()=>{let live=true,timer:ReturnType<typeof setTimeout>;async function poll(){try{const runs=await api<Run[]>('/runs'+query({workspace_id:wid}));if(live)setRun(runs.find(r=>['queued','running'].includes(r.status))||null);}catch(e){if(live)setError(errorText(e));}if(live)timer=setTimeout(()=>void poll(),1000);}void poll();return()=>{live=false;clearTimeout(timer);};},[wid]);
 return <>{error&&<p className="error global-error" role="alert">{error}</p>}{run&&<div className="notice global-error" role="status">此空间有分析任务正在后台运行。<button onClick={()=>onOpen(run.mode)}>查看后台任务</button><button onClick={()=>void api('/runs/'+run.id+'/cancel',{method:'POST',json:{workspace_id:wid}}).then(()=>setRun(null)).catch(e=>setError(errorText(e)))}>取消后台任务</button><span className="hint">取消会停止后续请求；已发出的请求仍可能计费。</span></div>}</>;
}
