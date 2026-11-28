"""index.html + 건물 모델(.glb)을 하나의 HTML(artifact.html)로 묶는다.
Claude 아티팩트처럼 .glb 파일을 따로 올릴 수 없는 곳에 올릴 때 쓴다.
사용: python3 tools/build_artifact.py  (저장소 루트에서 실행) -> artifact.html 생성
"""
import base64, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
src = (root/'index.html').read_text(encoding='utf-8')
emb = []
for sid, name in [('bkdata','bonkwan.glb'), ('nddata','saenghwal.glb'), ('sddata','namdong.glb')]:
    b64 = base64.b64encode((root/name).read_bytes()).decode()
    emb.append(f'<script id="{sid}" type="application/octet-stream">{b64}</script>')
i = src.index('<body>') + len('<body>')
out = src[:i] + '\n' + '\n'.join(emb) + src[i:]
(root/'artifact.html').write_text(out, encoding='utf-8')
print('artifact.html', len(out)//1024, 'KB')
