import {useEffect,useRef,type ReactNode} from 'react';
export default function Dialog({title,onClose,children}:{title:string;onClose:()=>void;children:ReactNode}){
 const ref=useRef<HTMLDialogElement>(null);
 useEffect(()=>{const dialog=ref.current!;dialog.showModal();return()=>dialog.close();},[]);
 return <dialog ref={ref} className="detail-dialog" aria-label={title} onCancel={e=>{e.preventDefault();onClose();}}><div className="dialog-bar"><span className="quiet small">{title}</span><button onClick={onClose} aria-label="关闭详情">关闭</button></div>{children}</dialog>;
}
