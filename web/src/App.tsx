import {useEffect,useState} from 'react';
import {api,errorText} from './api';
import type {Workspace} from './types';
import Start from './pages/Start';
import Library from './pages/Library';
import Settings from './pages/Settings';

type View='home'|'profile'|'library'|'challenge'|'timeline'|'settings';
export default function App(){
 const [workspaces,setWorkspaces]=useState<Workspace[]>([]),[wid,setWid]=useState(''),[view,setView]=useState<View>('home'),[error,setError]=useState(''),[busy,setBusy]=useState(false),[version,setVersion]=useState(0);
 const workspace=workspaces.find(w=>w.id===wid);
 const refresh=()=>{setVersion(v=>v+1);};
 useEffect(()=>{api<Workspace[]>('/workspaces').then(setWorkspaces).catch(e=>setError(errorText(e)));},[version]);
 async function start(demo:boolean){setBusy(true);setError('');try{let id:string;if(demo){id=(await api<{id:string}>('/demo',{method:'POST'})).id;}else{const existing=workspaces.find(w=>!w.demo);id=existing?.id||(await api<Workspace>('/workspaces',{method:'POST',json:{name:'我的个人档案'}})).id;}setWorkspaces(await api<Workspace[]>('/workspaces'));setWid(id);setView(demo?'profile':'library');}catch(e){setError(errorText(e));}finally{setBusy(false);}}
 return <><header className="topbar"><button className="brand" onClick={()=>setView('home')} aria-label="SelfDiff 首页"><span className="brand-symbol">见</span><span>SelfDiff <small>见己</small></span></button><span className="top-note">对自己的理解，也值得有版本记录。</span><span className="local-status"><span/>本地档案</span></header>
 {error&&<p className="error global-error" role="alert">{error}</p>}
 {view==='home'||!workspace?<Start onDemo={()=>void start(true)} onPersonal={()=>void start(false)} onOpen={id=>{setWid(id);setView('profile');}} workspaces={workspaces} busy={busy}/>:<div className="app-layout"><aside className="sidebar"><div className="workspace-label">正在阅读</div><select aria-label="切换资料空间" value={wid} onChange={e=>{setWid(e.target.value);setView('profile');}}>{workspaces.map(w=><option key={w.id} value={w.id}>{w.name}</option>)}</select>{workspace.demo&&<div className="demo-badge">合成示例 / 虚构人物</div>}<nav aria-label="档案导航">{([['profile','个人档案'],['library','会话资料'],['challenge','判断对照'],['timeline','时间比较'],['settings','模型设置']] as [View,string][]).map(([key,label])=><button key={key} aria-current={view===key?'page':undefined} className={view===key?'active':''} onClick={()=>setView(key)}>{label}</button>)}</nav><div className="sidebar-foot"><p>从原话开始。<br/>让理解保持可修正。</p><button className="text-button" onClick={()=>setView('home')}>返回开始页</button></div></aside><main className="content" key={wid}>{view==='library'?<Library workspace={workspace} onChanged={refresh}/>:view==='settings'?<Settings workspace={workspace}/>:<section className="empty-profile"><h1>还没有关于你的结论</h1><p>导入资料后配置模型，即可生成有原文依据、等待你确认的个人洞察。</p><button onClick={()=>setView('settings')}>配置分析模型</button></section>}</main></div>}
 </>;
}
