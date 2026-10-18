let csrf='';
type Options=RequestInit & {json?:unknown};
export async function request(path:string,options:Options={}){
  const {json,...init}=options;
  const headers=new Headers(init.headers);
  if(json!==undefined){headers.set('Content-Type','application/json');init.body=JSON.stringify(json);}
  if(init.method && !['GET','HEAD'].includes(init.method))headers.set('X-CSRF-Token',csrf);
  const response=await fetch('/api'+path,{...init,headers,credentials:'same-origin'});
  if(!response.ok){let message='操作未完成，请检查本地服务后重试。';try{message=(await response.json()).message||message;}catch{}throw new Error(message);}
  return response;
}
export async function api<T>(path:string,options:Options={}):Promise<T>{return (await request(path,options)).json();}
export async function bootstrap(){
  const token=new URLSearchParams(location.hash.slice(1)).get('token');
  history.replaceState(null,'',location.pathname+location.search);
  const response=token?await api<{csrf:string}>('/session/bootstrap',{method:'POST',json:{token}}):await api<{csrf:string}>('/session');
  csrf=response.csrf;
}
export function query(data:Record<string,string|number>){return '?'+new URLSearchParams(Object.entries(data).map(([k,v])=>[k,String(v)]));}
export function saveBlob(blob:Blob,name:string){const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
export const errorText=(e:unknown)=>e instanceof Error?e.message:'操作未完成，请重试。';
