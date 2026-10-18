import {useState} from 'react';
import {request,saveBlob,errorText} from '../api';
import type {Insight,Workspace} from '../types';
import Dialog from './Dialog';
export default function SharePreview({workspace,insights,onClose}:{workspace:Workspace;insights:Insight[];onClose:()=>void}){
 const [ids,setIds]=useState<string[]>([]),[text,setText]=useState(''),[checked,setChecked]=useState(false),[error,setError]=useState('');
 async function download(){try{const response=await request('/exports/share',{method:'POST',json:{workspace_id:workspace.id,insight_ids:ids,text}});saveBlob(await response.blob(),'selfdiff-card.html');}catch(e){setError(errorText(e));}}
 return <Dialog title="分享由你确认的部分" onClose={onClose}><h2>留下一点新的认识</h2><p className="quiet">卡片只包含你填写的公开摘要，不附原话、会话链接、来源路径或项目名称。</p><fieldset><legend>选择本次分享涉及的发现</legend>{insights.filter(i=>i.status!=='rejected').map(i=><label className="check-row" key={i.id}><input type="checkbox" checked={ids.includes(i.id)} onChange={e=>setIds(e.target.checked?[...ids,i.id]:ids.filter(x=>x!==i.id))}/>{i.title}</label>)}</fieldset><label>准备公开的文字<textarea value={text} maxLength={4000} onChange={e=>{setText(e.target.value);setChecked(false);}} placeholder="用你自己的话，写下愿意公开的部分。"/></label><div className="share-preview"><span className="small quiet">SelfDiff · 见己 {workspace.demo?' / 合成示例':''}</span><p>{text||'这里将显示你的公开摘要。'}</p></div><label className="check-row"><input type="checkbox" checked={checked} onChange={e=>setChecked(e.target.checked)}/>我已检查这些文字，愿意导出分享</label>{error&&<p className="error" role="alert">{error}</p>}<button className="primary" disabled={!checked||!ids.length||!text.trim()} onClick={()=>void download()}>下载分享卡</button><p className="hint">下载后由你决定如何分享；应用不会自动发布。</p></Dialog>;
}
