"""Interface web para visualizar e interagir com as vagas. Rode: python app.py -> http://localhost:5000"""
from flask import Flask, request, jsonify, render_template_string, Response
from importlib.util import spec_from_file_location, module_from_spec
import os
import json
import time
try:
    import match as match_cv
except Exception:
    match_cv = None

BASE = os.path.dirname(os.path.abspath(__file__))
spec = spec_from_file_location("vagas", os.path.join(BASE, "busca.py"))
vagas = module_from_spec(spec)
spec.loader.exec_module(vagas)

app = Flask(__name__)

HTML = r"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Jobs Radar — Vagas em tempo real</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#F9F7F7;--bg2:#DBE2EF;--card:#ffffff;--card2:#DBE2EF;--line:#c3cede;--txt:#112D4E;--mut:#5a7186;--acc:#3F72AF;--acc2:#3F72AF;--danger:#ef4444;--amber:#b45309}
*{box-sizing:border-box}body{margin:0;font-family:Inter,Segoe UI,Arial;background:var(--bg);color:var(--txt);min-height:100vh}
.topbar{display:flex;align-items:center;gap:12px;padding:16px 24px;border-bottom:1px solid var(--line);background:var(--txt);color:#F9F7F7;position:sticky;top:0;z-index:10}
.logo{width:38px;height:38px;border-radius:11px;background:var(--acc);display:grid;place-items:center;font-weight:800;font-size:18px;color:#fff}
.topbar h1{margin:0;font-size:17px;letter-spacing:.2px}.topbar small{color:#DBE2EF}
.live{margin-left:auto;display:flex;align-items:center;gap:8px;font-size:13px;color:#DBE2EF}
.dot{width:9px;height:9px;border-radius:50%;background:#8aa0b8}.dot.on{background:#4ade80;box-shadow:0 0 10px #4ade80;animation:pulse 1.2s infinite}
@keyframes pulse{50%{opacity:.4}}
.layout{display:grid;grid-template-columns:360px 1fr;gap:18px;max-width:1400px;margin:0 auto;padding:18px 20px 40px;align-items:start}
aside{position:sticky;top:76px;display:flex;flex-direction:column;gap:14px;max-height:calc(100vh - 96px);overflow:auto;padding-right:2px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;box-shadow:0 1px 3px #112D4E14}
.panel h3{margin:0 0 4px;font-size:13px;text-transform:uppercase;letter-spacing:1px;color:var(--mut)}
.panel .hint{font-size:12px;color:var(--mut);margin:0 0 10px}
.chips{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:10px;max-height:150px;overflow:auto}
.chip{background:#DBE2EF;border:1px solid #3F72AF;border-radius:999px;padding:5px 6px 5px 12px;display:flex;gap:7px;align-items:center;font-size:13px;color:#112D4E}
.chip button{background:#112D4E;color:#fff;border:0;border-radius:50%;width:19px;height:19px;cursor:pointer;font-size:11px}
.addrow{display:flex;gap:8px}input,select{background:#fff;border:1px solid var(--line);color:var(--txt);padding:10px;border-radius:10px;font-size:14px}
.addrow input{flex:1;min-width:0}.addrow button,.go{background:#3F72AF;color:#fff;border:0;padding:10px 16px;border-radius:10px;cursor:pointer;font-weight:700;white-space:nowrap}
.go.big{padding:14px;font-size:15px;width:100%;box-shadow:0 6px 18px #3F72AF44}button:disabled{opacity:.55;cursor:wait}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}.grid2 input,.grid2 select{width:100%}
.check{display:flex;gap:8px;align-items:center;font-size:14px;padding-top:22px}
main{min-width:0}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:14px}
.stat{background:#fff;border:1px solid var(--line);border-radius:14px;padding:12px 14px}
.stat b{font-size:22px;display:block;color:#112D4E}.stat span{font-size:12px;color:var(--mut)}
.progress{height:8px;background:#DBE2EF;border-radius:99px;overflow:hidden;border:1px solid var(--line);margin:10px 0}
.progress i{display:block;height:100%;width:0;background:#3F72AF;transition:width .4s}
#status{font-size:13px;color:var(--mut);min-height:20px}
.toolbar{display:flex;gap:10px;margin:12px 0}.toolbar input{flex:1}
.job{background:#fff;border:1px solid var(--line);border-radius:16px;padding:16px 18px;margin-bottom:12px;box-shadow:0 1px 3px #112D4E14;animation:in .35s ease}
@keyframes in{from{opacity:0;transform:translateY(8px)}}
.job h3{margin:0 0 2px;font-size:16px;color:#112D4E}.tags{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}
.tag{font-size:11.5px;padding:3px 10px;border-radius:999px;background:#DBE2EF;border:1px solid #3F72AF;color:#112D4E}
.tag.loc{background:#112D4E;border-color:#112D4E;color:#F9F7F7}
.desc{white-space:pre-wrap;background:#F9F7F7;border:1px solid var(--line);border-radius:10px;padding:11px;font-size:13.5px;line-height:1.55;max-height:230px;overflow:auto;color:#112D4E}
.desc.loading{color:var(--amber)}.row{display:flex;gap:8px;margin-top:11px;flex-wrap:wrap}
.row button{padding:9px 15px;border-radius:9px;border:0;cursor:pointer;font-weight:600;font-size:13.5px}
.apply{background:#112D4E;color:#F9F7F7}
.ghost{background:#DBE2EF;color:#112D4E;border:1px solid #3F72AF!important}
.danger{background:#F9F7F7;color:#b91c1c;border:1px solid #b91c1c!important}
.empty{border:1.5px dashed var(--line);border-radius:16px;padding:44px;text-align:center;color:var(--mut)}
@media(max-width:960px){.layout{grid-template-columns:1fr}aside{position:static;max-height:none}.stats{grid-template-columns:repeat(2,1fr)}}
</style></head><body>
<div class="topbar"><div class="logo">JR</div><div><h1>Jobs Radar</h1><small>Monitor de vagas em tempo real</small></div>
<div class="live"><span class="dot" id="dot"></span><span id="liveTxt">pronto</span></div></div>
<div class="layout">
<aside>
<div class="panel"><h3>🎯 Cargos (<span id="nC"></span>)</h3><p class="hint">Adicione e remova livremente</p><div class="chips" id="chipsC"></div>
<div class="addrow"><input id="inC" placeholder="Ex: DevOps" list="sug"><button onclick="addC()">+ Add</button></div>
<datalist id="sug"><option>Analista de dados</option><option>Analista de BI</option><option>DevOps</option><option>Desenvolvedor Python</option><option>Suporte TI</option></datalist></div>
<div class="panel"><h3>📍 Locais (<span id="nL"></span>)</h3><p class="hint">Busca todas as combinações cargo × local</p><div class="chips" id="chipsL"></div>
<div class="addrow"><input id="inL" placeholder="Ex: Remote, Brazil"><button onclick="addL()">+ Add</button></div></div>
<div class="panel"><h3>⚙️ Filtros</h3>
<div class="grid2"><div>Excluir títulos<input id="exc" value="senior, sênior, sr., sr, master, lead, head, gerente, coordenador, diretor, manager, especialista, estagio, estágio, analista de marketing, vendedor, consultor de vendas, analista de processos, product operations analyst, analista jr de processos, assistente de operações jr, assistente de operacoes jr, gestor de tráfego, gestor de trafego, analista de gestão, analista de gestao, people analytics, fundador, estatístico, estatistico, sap, crm, sales, seguro, e-commerce, ecommerce, marketplace, administrativo, assistente administrativo, logísticas, logisticas, mídia online, media online, financeiro, líder, lider, crédito, credito, comercial, .net, jurídico, juridico, recursos humanos" placeholder="senior, estagio" style="width:100%;margin-top:6px"></div>
<div>Período<select id="per" style="width:100%;margin-top:6px"><option value="r86400">Últimas 24h</option><option value="r604800">Última semana</option><option value="r2592000">Último mês</option><option value="">Sem filtro</option></select></div>
<div>Vagas / combinação<input id="max" type="number" value="5" min="1" max="30" style="width:100%;margin-top:6px"></div>
<div class="check"><label><input type="checkbox" id="desc" checked> Com descrição</label></div></div></div>
<button class="go big" id="btn" onclick="buscar()">▶ Iniciar monitoramento</button>
<button class="go big ghost" style="background:#DBE2EF;color:#112D4E" onclick="parar()">⏹ Parar</button>
<div class="panel"><h3>📄 Aderência ao meu CV</h3><p class="hint" id="cvInfo">Nenhum CV enviado.</p>
<div class="addrow"><input type="file" id="cvFile" accept="application/pdf"><button onclick="enviarCV()">Enviar</button></div>
<div class="check"><label><input type="checkbox" id="match"> Calcular aderência (LLM)</label></div>
<div style="margin-top:8px">Nota mínima <input id="minMatch" type="number" value="0" min="0" max="100" style="width:80px"> %</div>
<p class="hint">LLM em rodízio (1 análise por modelo), resposta JSON curta, com pausa anti rate-limit.</p></div>
</aside>
<main>
<div class="stats"><div class="stat"><b id="sV">0</b><span>vagas</span></div><div class="stat"><b id="sC">0/0</b><span>combinações</span></div><div class="stat"><b id="sT">0s</b><span>tempo</span></div><div class="stat"><b id="sL">4</b><span>locais ativos</span></div></div>
<div class="progress"><i id="bar"></i></div>
<div id="status">Configure à esquerda e inicie o monitoramento.</div>
<div class="toolbar"><input id="buscaLocal" placeholder="🔎 Filtrar vagas na tela (título, empresa, descrição)..." oninput="render()"><select id="fLocal" onchange="render()"><option value="">📍 Todos os locais</option></select><select id="ord" onchange="render()"><option value="recente">Mais recentes</option><option value="match">Maior aderência</option><option value="az">A–Z</option></select></div>
<div id="lista"><div class="empty">Nenhuma vaga ainda.<br>As vagas aparecem aqui <b>ao vivo</b>, uma a uma, como no terminal.</div></div>
</main>
</div>
<script>
let cargos=["Analista de Dados","Analista de Dados Junior","Analista de BI","Business Data Analyst","Data Analyst","Analista ETL","Analista de Banco de Dados","Analista de Cloud","Analista de Automacao","Engenheiro de Dados Junior","Desenvolvedor Python","Analista Power BI","Analytics Engineer","Engenheiro de Integracao de Dados"],locais=['Campinas','Curitiba','Sao Paulo','Florianopolis'],vagas=[],t0=0,feitas=0,timer=null;
function draw(){
 document.getElementById('chipsC').innerHTML=cargos.map((c,i)=>`<span class="chip">${esc(c)}<button onclick="cargos.splice(${i},1);draw()">×</button></span>`).join('');
 document.getElementById('chipsL').innerHTML=locais.map((c,i)=>`<span class="chip">${esc(c)}<button onclick="locais.splice(${i},1);draw()">×</button></span>`).join('');
 document.getElementById('nC').textContent=cargos.length;document.getElementById('nL').textContent=locais.length;
 document.getElementById('sL').textContent=locais.length;
}
function addC(){const v=document.getElementById('inC').value.trim();if(v&&!cargos.includes(v))cargos.push(v);document.getElementById('inC').value='';draw();}
function addL(){const v=document.getElementById('inL').value.trim();if(v&&!locais.includes(v))locais.push(v);document.getElementById('inL').value='';draw();}
document.getElementById('inC').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();addC();}};
document.getElementById('inL').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();addL();}};
function setLive(on,txt){document.getElementById('dot').className='dot'+(on?' on':'');document.getElementById('liveTxt').textContent=txt;}
async function cvStatus(){
 try{const r=await fetch('/api/cvstatus');const j=await r.json();
 document.getElementById('cvInfo').textContent=j.tem_cv?`CV carregado (${j.chars} chars) • LLM ${j.llm_ok?'ok':'sem chave'}`:'Nenhum CV enviado.';
 if(j.tem_cv)document.getElementById('match').checked=true;}catch(e){}
}
async function enviarCV(){
 const f=document.getElementById('cvFile').files[0];if(!f){alert('Escolha o PDF');return;}
 const fd=new FormData();fd.append('pdf',f);
 document.getElementById('cvInfo').textContent='Enviando...';
 const r=await fetch('/api/curriculo',{method:'POST',body:fd});const j=await r.json();
 document.getElementById('cvInfo').textContent=r.ok?`CV ok (${j.chars} chars, ${j.paginas} pág.) • LLM ${j.llm_ok?'ok':'sem chave'}`:'Erro: '+(j.erro||r.status);
 if(r.ok)document.getElementById('match').checked=true;
}
function badge(s){
 if(s==null||s<0)return '';
 const c=s>=70?'background:#112D4E;color:#F9F7F7':s>=40?'background:#DBE2EF;color:#112D4E;border:1px solid #3F72AF':'background:#F9F7F7;color:#b91c1c;border:1px solid #b91c1c';
 return `<span style="padding:4px 12px;border-radius:999px;font-weight:800;font-size:13px;${c}">${s}% match</span>`;
}
function parar(){if(window._es){window._es.close();window._es=null;}clearInterval(timer);setLive(false,'parado');document.getElementById('btn').disabled=false;document.getElementById('status').textContent+=' — parado pelo usuário.';}
async function buscar(){
 if(!cargos.length||!locais.length){alert('Adicione ao menos 1 cargo e 1 local');return;}
 document.getElementById('btn').disabled=true;vagas=[];feitas=0;t0=Date.now();render();
 const n=cargos.length*locais.length;setLive(true,'buscando...');clearInterval(timer);
 timer=setInterval(()=>{document.getElementById('sT').textContent=Math.round((Date.now()-t0)/1000)+'s';},1000);
 if(window._es)window._es.close();
 const p=new URLSearchParams({cargos:cargos.join(','),locais:locais.join('|'),excluir:document.getElementById('exc').value,periodo:document.getElementById('per').value,max:document.getElementById('max').value||5,desc:document.getElementById('desc').checked?'1':'0',match:document.getElementById('match').checked?'1':'0'});
 document.getElementById('status').textContent='Conectando ao stream...';
 window._es=new EventSource('/api/stream?'+p);
 window._es.onmessage=e=>{
  const m=JSON.parse(e.data);
  if(m.tipo==='status'){document.getElementById('status').textContent='⚡ '+m.msg;}
  else if(m.tipo==='vaga'){vagas.unshift(m.vaga);upd(n);}
  else if(m.tipo==='vaga_desc'){const v=vagas.find(x=>x.link===m.link);if(v){v.descricao=m.descricao;}render();}
  else if(m.tipo==='vaga_match'){const v=vagas.find(x=>x.link===m.link);if(v){v.match=m.match;}render();}
  else if(m.tipo==='combo_ok'){feitas++;upd(n);}
  else if(m.tipo==='fim'){clearInterval(timer);setLive(false,'concluído');document.getElementById('btn').disabled=false;document.getElementById('status').textContent=`✅ Concluído: ${vagas.length} vaga(s) em ${n} combinações.`;render();}
  else if(m.tipo==='erro'){document.getElementById('status').textContent='Erro: '+m.msg;}
 };
 window._es.onerror=()=>{clearInterval(timer);setLive(false,'erro/desconectado');document.getElementById('btn').disabled=false;};
}
function upd(n){document.getElementById('sV').textContent=vagas.length;document.getElementById('sC').textContent=feitas+'/'+n;document.getElementById('bar').style.width=Math.round(feitas/n*100)+'%';render();}
function render(){
 const q=document.getElementById('buscaLocal').value.toLowerCase(),ord=document.getElementById('ord').value,fl=document.getElementById('fLocal').value;
 const minM=parseInt(document.getElementById('minMatch').value||'0');
 // atualiza opcoes de local a partir do que chegou
 const locs=[...new Set(vagas.map(v=>v.local).filter(Boolean))].sort();
 const sel=document.getElementById('fLocal'),atual=sel.value;
 sel.innerHTML='<option value="">📍 Todos os locais ('+locs.length+')</option>'+locs.map(l=>`<option ${l===atual?'selected':''}>${esc(l)}</option>`).join('');
 let vis=vagas.filter(v=>(v.titulo+' '+v.empresa+' '+(v.descricao||'')).toLowerCase().includes(q));
 if(fl)vis=vis.filter(v=>v.local===fl);
 if(minM>0)vis=vis.filter(v=>v.match&&v.match.score>=minM);
 if(ord==='az')vis=[...vis].sort((a,b)=>a.titulo.localeCompare(b.titulo));
 if(ord==='match')vis=[...vis].sort((a,b)=>((b.match&&b.match.score>=0?b.match.score:-1))-((a.match&&a.match.score>=0?a.match.score:-1)));
 document.getElementById('sV').textContent=vagas.length;
 if(!vis.length){document.getElementById('lista').innerHTML='<div class="empty">Nenhuma vaga ainda.<br>As vagas aparecem aqui <b>ao vivo</b>, uma a uma.</div>';return;}
 document.getElementById('lista').innerHTML=vis.map(v=>{const ld=!v.descricao;const mt=v.match&&v.match.score>=0?v.match:null;const bar=mt?`<div style="height:7px;background:#DBE2EF;border-radius:99px;margin:8px 0"><i style="display:block;height:100%;width:${mt.score}%;background:${mt.score>=70?'#112D4E':'#3F72AF'};border-radius:99px"></i></div>`:'';const tf=mt?`<div style="font-size:12.5px;margin-top:6px;color:#112D4E">✅ ${esc((mt.tem||[]).join(', ')||'—')}<br>❌ ${esc((mt.falta||[]).join(', ')||'—')}<br><i>${esc(mt.motivo||'')}</i></div>`:'';return `<div class="job"><h3>${esc(v.titulo)} ${badge(mt?mt.score:null)}</h3>
 <div class="tags"><span class="tag">🏢 ${esc(v.empresa||'—')}</span><span class="tag loc">📍 ${esc(v.local||'')}</span><span class="tag">🔎 ${esc(v.cargo_busca||'')} → ${esc(v.local_busca||'')}</span></div>${bar}
 <div class="desc${ld?' loading':''}">${esc(ld?'⏳ buscando descrição...':v.descricao)}</div>${tf}
 <div class="row"><a href="${v.link}" target="_blank"><button class="apply">Candidatar-se ↗</button></a>
 <button class="ghost" onclick="navigator.clipboard.writeText('${v.link}')">Copiar link</button>
 <button class="danger" onclick="vagas=vagas.filter(x=>x.link!=='${v.link}');render()">Descartar</button></div></div>`}).join('');
}
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
draw();cvStatus();
</script></body></html>"""

@app.get("/")
def index():
    return render_template_string(HTML)

@app.post("/api/curriculo")
def api_curriculo():
    """Upload do CV em PDF -> extrai texto e salva (invalida perfil em cache)."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return jsonify({"erro": "pypdf nao instalado. Rode: pip install pypdf"}), 500
    f = request.files.get("pdf")
    if not f:
        return jsonify({"erro": "Envie o PDF no campo 'pdf'."}), 400
    try:
        rdr = PdfReader(f.stream)
        texto = "\n".join([(p.extract_text() or "") for p in rdr.pages])
    except Exception as e:
        return jsonify({"erro": f"PDF invalido: {e}"}), 400
    texto = texto.strip()
    if len(texto) < 50:
        return jsonify({"erro": "Nao consegui extrair texto do PDF (imagem escaneada?)."}), 400
    with open(os.path.join(BASE, "cv_text.txt"), "w", encoding="utf-8") as fh:
        fh.write(texto)
    pf = os.path.join(BASE, "perfil_cv.txt")
    if os.path.exists(pf):
        os.remove(pf)  # forca regenerar perfil do novo CV
    tem_chave = bool((match_cv.get_key() if match_cv else ""))
    return jsonify({"ok": True, "chars": len(texto), "paginas": len(rdr.pages), "llm_ok": tem_chave})

@app.get("/api/cvstatus")
def api_cvstatus():
    cv = os.path.join(BASE, "cv_text.txt")
    return jsonify({"tem_cv": os.path.exists(cv),
                    "chars": os.path.getsize(cv) if os.path.exists(cv) else 0,
                    "llm_ok": bool((match_cv.get_key() if match_cv else ""))})

@app.get("/api/stream")
def api_stream():
    cargos = [c.strip() for c in request.args.get("cargos", "Analista de dados").split(",") if c.strip()]
    raw = request.args.get("locais") or request.args.get("regiao", "Campinas")
    locais = [x.strip() for x in raw.split("|") if x.strip()]
    excluir = [e.strip() for e in request.args.get("excluir", "").split(",") if e.strip()]
    periodo = request.args.get("periodo", "r86400") or None
    try:
        maxv = min(max(1, int(request.args.get("max", "10"))), 30)
    except ValueError:
        maxv = 10
    com_desc = request.args.get("desc", "1") == "1"
    com_match = request.args.get("match", "0") == "1"
    cv_texto = ""
    if com_match:
        if not match_cv or not match_cv.get_key():
            def gen_err():
                yield f"data: {json.dumps({'tipo': 'erro', 'msg': 'Sem chave Groq. Configure env GROQ_API_KEY ou groq_key.txt.'})}\n\n"
            return Response(gen_err(), mimetype="text/event-stream")
        try:
            with open(os.path.join(BASE, "cv_text.txt"), encoding="utf-8") as fh:
                cv_texto = fh.read()
        except FileNotFoundError:
            def gen_err2():
                yield f"data: {json.dumps({'tipo': 'erro', 'msg': 'Envie seu CV em PDF primeiro (painel Aderencia).'})}\n\n"
            return Response(gen_err2(), mimetype="text/event-stream")

    def gen():
        vistos = set()
        total = len(cargos) * len(locais)
        yield f"data: {json.dumps({'tipo': 'status', 'msg': f'Iniciando {total} combinacoes cargo x local...'})}\n\n"
        for c in cargos:
            for loc in locais:
                yield f"data: {json.dumps({'tipo': 'status', 'msg': f'Buscando {c} em {loc}...'})}\n\n"
                try:
                    # 1) cards rapido (sem descricao) -> aparece na hora
                    lista = vagas.buscar_vagas_lista(c, loc, excluir=excluir, periodo=periodo,
                                                     max_vagas=maxv, com_descricao=False)
                    for v in lista:
                        if v["link"] in vistos:
                            continue
                        vistos.add(v["link"])
                        v["local_busca"] = loc
                        v["descricao"] = "" if com_desc else "(descricao desativada)"
                        yield f"data: {json.dumps({'tipo': 'vaga', 'vaga': v})}\n\n"
                        # 2) descricao logo em seguida -> atualiza o card ja exibido
                        if com_desc:
                            try:
                                d = vagas.extrair_descricao_linkedin(v["link"])
                            except Exception as e:
                                d = f"Erro descricao: {e}"
                            yield f"data: {json.dumps({'tipo': 'vaga_desc', 'link': v['link'], 'descricao': d})}\n\n"
                            v_desc = d
                        else:
                            v_desc = ""
                        # 3) aderencia LLM (usa a descricao recem-buscada; sem descricao usa titulo)
                        if com_match:
                            try:
                                m = match_cv.analisar(v["titulo"], v.get("empresa", ""),
                                                      v.get("local", ""), v_desc or v["titulo"], cv_texto)
                                yield f"data: {json.dumps({'tipo': 'vaga_match', 'link': v['link'], 'match': m})}\n\n"
                            except Exception as e:
                                yield f"data: {json.dumps({'tipo': 'vaga_match', 'link': v['link'], 'match': {'score': -1, 'tem': [], 'falta': [], 'motivo': f'Falha LLM (rate-limit?), seguindo: {str(e)[:120]}'}})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'tipo': 'status', 'msg': f'Falha {c}/{loc}: {e}. Seguindo...'})}\n\n"
                yield f"data: {json.dumps({'tipo': 'combo_ok'})}\n\n"
        yield f"data: {json.dumps({'tipo': 'fim'})}\n\n"

    return Response(gen(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.get("/api/buscar")
def api_buscar():
    cargos = [c.strip() for c in request.args.get("cargos", "Analista de dados").split(",") if c.strip()]
    # locais separados por | (podem conter virgula: "Sao Paulo, Brazil")
    raw = request.args.get("locais") or request.args.get("regiao", "Campinas")
    locais = [x.strip() for x in raw.split("|") if x.strip()]
    excluir = [e.strip() for e in request.args.get("excluir", "").split(",") if e.strip()]
    periodo = request.args.get("periodo", "r86400") or None
    try:
        maxv = min(max(1, int(request.args.get("max", "10"))), 30)
    except ValueError:
        maxv = 10
    com_desc = request.args.get("desc", "1") == "1"
    try:
        out = []
        for c in cargos:
            for loc in locais:
                for v in vagas.buscar_vagas_lista(c, loc, excluir=excluir, periodo=periodo,
                                                 max_vagas=maxv, com_descricao=com_desc):
                    v["local_busca"] = loc
                    out.append(v)
        # remove duplicadas (mesmo link em 2 buscas)
        unicas, seen = [], set()
        for v in out:
            if v["link"] not in seen:
                seen.add(v["link"])
                unicas.append(v)
        return jsonify(unicas)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
