import {useState,useEffect} from 'react';
import {api,query,errorText} from '../api';
import {date,type Workspace} from '../types';
import RunStatus from '../components/RunStatus';
import type {Insight} from '../types';
import EvidencePanel from '../components/EvidencePanel';
export default function Explore({workspace,mode}:{workspace:Workspace;mode:'challenge'|'comparison'}){
 const [claim,setClaim]=useState('我是不是经常换方向'),[theme,setTheme]=useState('项目启动方式'),[a1,setA1]=useState('2026-01-01'),[a2,setA2]=useState('2026-02-01'),[b1,setB1]=useState('2026-09-01'),[b2,setB2]=useState('2026-10-01'),[rid,setRid]=useState(''),[error,setError]=useState(''),[note,setNote]=useState(''),[busy,setBusy]=useState(false),[approved,setApproved]=useState(false),[insights,setInsights]=useState<Insight[]>([]),[selected,setSelected]=useState(''),[snapshots,setSnapshots]=useState<{id:string;created_at:string;invalidated:boolean;result?:{summary?:string}}[]>([]);
 const wid=workspace.id,isCompare=mode==='comparison';
 async function load(){setInsights(await api<Insight[]>('/insights'+query({workspace_id:wid})));setSnapshots(await api('/snapshots'+query({workspace_id:wid})));}
 useEffect(()=>{void load().catch(e=>setError(errorText(e)));},[wid]);
 async function start(){setError('');setNote('');setBusy(true);try{const data={scope:{workspace_id:wid},claim,theme,period_a:{start:a1+'T00:00:00Z',end:a2+'T00:00:00Z'},period_b:{start:b1+'T00:00:00Z',end:b2+'T00:00:00Z'}};const result=await api<{id:string}>(isCompare?'/comparisons':'/challenges',{method:'POST',json:data});setRid(result.id);}catch(e){setError(errorText(e));}finally{setBusy(false);}}
 const active=insights.find(i=>i.id===selected);
 return <section className="explore"><div className="page-head"><p className="quiet">{isCompare?'给变化留一份依据':'让自我判断，遇见具体的证据'}</p><h1>{isCompare?'哪些想法，慢慢不同了':'我以为的自己，也许还有另一面'}</h1><p>{isCompare?'比较两个时期的表达和选择。观点改变、情境补充与模型误解，需要分开看。':'输入一个具体判断，找支持它的原话，也找相反的经历。结果由你决定如何理解。'}</p></div>
 {workspace.demo&&<p className="demo-note">合成示例只演示预设情境；不会为任意输入生成虚构结论。自己的资料空间可配置模型自由分析。</p>}
 <div className="explore-form">{isCompare?<><label>比较主题<input value={theme} readOnly={!!workspace.demo} onChange={e=>setTheme(e.target.value)} maxLength={500}/></label><div className="periods"><fieldset><legend>时期 A</legend><label>时期 A 开始<input type="date" value={a1} readOnly={!!workspace.demo} onChange={e=>setA1(e.target.value)}/></label><label>时期 A 结束（不含当天）<input type="date" value={a2} readOnly={!!workspace.demo} onChange={e=>setA2(e.target.value)}/></label></fieldset><fieldset><legend>时期 B</legend><label>时期 B 开始<input type="date" value={b1} readOnly={!!workspace.demo} onChange={e=>setB1(e.target.value)}/></label><label>时期 B 结束（不含当天）<input type="date" value={b2} readOnly={!!workspace.demo} onChange={e=>setB2(e.target.value)}/></label></fieldset></div><p className="hint">没有时间信息的会话不参与比较；资料不足时会明确说明。</p></>:<label>关于自己的具体判断<textarea value={claim} readOnly={!!workspace.demo} onChange={e=>setClaim(e.target.value)} maxLength={1500}/></label>}
 {!workspace.demo&&<label className="check-row"><input type="checkbox" checked={approved} onChange={e=>setApproved(e.target.checked)}/>我同意将{isCompare?'两个时期内':'当前资料空间内'}的用户发言发送到已配置的模型进行分析</label>}<button className="primary" disabled={busy||(!workspace.demo&&!approved)} onClick={()=>void start()}>{isCompare?'比较两个时期':'寻找支持与反例'}</button></div>
 {error&&<p className="error" role="alert">{error}</p>}{rid&&<><RunStatus key={rid} id={rid} wid={wid} onComplete={()=>void load()}/>{isCompare&&<button onClick={()=>void api('/snapshots',{method:'POST',json:{workspace_id:wid,run_id:rid}}).then(()=>{setNote('快照已保存');void load();}).catch(e=>setError(errorText(e)))}>保存这次比较</button>}</>}{note&&<p className="notice" role="status">{note}</p>}
 {insights.length>0&&<section className="related-evidence"><h2>相关的可回查发现</h2>{insights.filter(i=>isCompare?i.dimension==='change':['interests','thinking_decisions'].includes(i.dimension)).map(i=><button className="related-row" key={i.id} onClick={()=>setSelected(i.id)}><span>{i.title}</span><small>{i.evidence.length} 条原文</small></button>)}</section>}
 {isCompare&&snapshots.length>0&&<section className="related-evidence"><h2>留下的比较快照</h2>{snapshots.map(s=><article className="snapshot" key={s.id}><span className="small quiet">{date(s.created_at)} / {s.invalidated?'来源已删除':'分析当时的资料范围'}</span><p>{s.invalidated?'内容已清除，可用剩余资料重新分析。':s.result?.summary}</p></article>)}</section>}
 {active&&<EvidencePanel insight={active} workspace={workspace} onClose={()=>setSelected('')} onRefresh={load}/>}
 </section>;
}
