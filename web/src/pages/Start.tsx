import type {Workspace} from '../types';
export default function Start({onDemo,onPersonal,onOpen,workspaces,busy}:{onDemo:()=>void;onPersonal:()=>void;onOpen:(id:string)=>void;workspaces:Workspace[];busy:boolean}){
 return <main className="start">
  <section className="intro"><div className="intro-copy"><p className="quiet">从你与 AI 说过的话，重新认识自己</p><h1>有些自己，<br/>藏在反复说过的话里。</h1><p className="lead">把散落在不同 AI 工具里的会话放在一起。<br/>看见反复出现的选择、卡点，以及慢慢发生的变化。</p><div className="actions"><button className="primary" onClick={onDemo} disabled={busy}>体验示例</button><button onClick={onPersonal} disabled={busy}>导入我的会话</button></div><p className="hint">示例完全虚构，无需密钥。你的资料单独保存。</p></div>
  <div className="specimen" aria-label="一项洞察如何形成"><div className="sheet-head"><span>一项发现的来处</span><span className="pill">合成示例</span></div><blockquote>“我总想把方案比较完再动手，<br/>结果这一周还没有开始。”</blockquote><p className="quiet small">来自两段不同的项目讨论</p><div className="interpretation"><span className="small">放在一起看</span><p>也许让你卡住的，<br/>是还没有一个验证标准。</p></div><div className="correction"><span className="small">本人补充</span><p>“不是所有项目都这样。<br/>需求明确的时候，我开始得很快。”</p></div><div className="sheet-foot">原话有出处，结论可以改。</div></div></section>
  <section className="principles"><div><h3>看见反复出现的模式</h3><p>哪些问题让你绕远路，什么条件让你更容易开始。</p></div><div><h3>每个判断，都能回到原话</h3><p>同时查看支持和反例，让理解保持具体、有边界。</p></div><div><h3>为自己的变化留一份记录</h3><p>比较两个时期，分清观点改变与情境不同。</p></div></section>
  {workspaces.length>0&&<section className="previous"><h2>继续阅读你的档案</h2>{workspaces.map(w=><button key={w.id} onClick={()=>onOpen(w.id)}>{w.name}{w.demo?'（示例）':''}</button>)}</section>}
  <footer>资料保存在本机。分析时，所选内容会发送到你配置的模型。<a href="https://github.com/wind127/selfdiff" target="_blank" rel="noreferrer">GitHub 开源项目</a></footer>
 </main>;
}
