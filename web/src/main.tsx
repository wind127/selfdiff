import {createRoot} from 'react-dom/client';
import {bootstrap} from './api';
import App from './App';
import './styles.css';
bootstrap().then(()=>createRoot(document.getElementById('root')!).render(<App/>)).catch(e=>{
 const root=document.getElementById('root')!;root.className='startup-error';
 const heading=document.createElement('h1');heading.textContent='SelfDiff · 见己';
 const text=document.createElement('p');text.textContent=e.message;
 root.append(heading,text);
});
