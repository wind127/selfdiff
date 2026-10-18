"""Local HTTP fixture. Never imported by the installed application."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        try:
            body=json.loads(data['messages'][-1]['content'])
            material=body.get('untrusted_material',[])
            refs=[{'message_id':m['id'],'version':m['version'],'quote':m['text'],'relation':'support'} for m in material[:2]]
            comparison=body.get('mode')=='comparison'
            draft={'pattern_key':'test-periods' if comparison else 'test-small-start','dimension':'change' if comparison else 'action_results',
                   'kind':'period_change' if comparison else 'success_condition','title':'两个时期的选择需要结合情境' if comparison else '小规模验证让你开始行动',
                   'observation':'这两次自述提到了先做小版本；不能推广到其他经历。','context':'测试资料中的两个项目',
                   'alternatives':['项目难度可能不同。'],'question':'这适用于其他项目吗？','evidence':refs}
            content={'insights':[draft] if refs else [],'summary':'只比较所选合成资料；未检索到反例。','classification':'uncertain'}
        except (ValueError,KeyError):
            content={'ok':True}
        response=json.dumps({'choices':[{'message':{'role':'assistant','content':json.dumps(content,ensure_ascii=False)}}]}).encode()
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(response)))
        self.end_headers()
        self.wfile.write(response)


def start():
    server=ThreadingHTTPServer(('127.0.0.1',8771),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server
