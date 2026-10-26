// Console Be Safe: interface do plantao (sem dependencias externas, funciona offline)
const $ = (s, el = document) => el.querySelector(s);
const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const hora = (iso) => (iso ? new Date(iso).toLocaleTimeString("pt-BR") : "-");
const NOMES = { vp: "Verdadeiro positivo", fp: "Falso positivo", vpb: "VP benigno" };
const SEV = { baixa: "baixa", media: "média", alta: "alta", critica: "crítica" };

async function api(caminho, opcoes = {}) {
  const r = await fetch(caminho, { headers: { "Content-Type": "application/json" }, ...opcoes });
  const dados = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(dados.detail?.[0]?.msg || dados.detail || `erro ${r.status}`);
  return dados;
}

// ---------------------------------------------------------------- abas
function abrirAba(nome) {
  const b = document.querySelector(`.abas button[data-aba="${nome}"]`);
  if (!b) return;
  document.querySelectorAll(".abas button").forEach((x) => x.classList.toggle("ativa", x === b));
  document.querySelectorAll(".painel").forEach((p) => p.classList.toggle("ativo", p.id === nome));
  if (location.hash !== "#" + nome) history.replaceState(null, "", "#" + nome);
  carregar(nome);
}
$("#abas").addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (b) abrirAba(b.dataset.aba);
});
window.addEventListener("hashchange", () => abrirAba(location.hash.slice(1)));

function tabela(colunas, linhas) {
  return `<table><thead><tr>${colunas.map(([, t]) => `<th>${t}</th>`).join("")}</tr></thead><tbody>${
    linhas.map((l) => `<tr>${colunas.map(([k, , f]) => `<td>${f ? f(l[k], l) : esc(l[k])}</td>`).join("")}</tr>`).join("")
  }</tbody></table>`;
}

document.querySelectorAll(".filtro").forEach((inp) =>
  inp.addEventListener("input", () => {
    const termo = inp.value.toLowerCase();
    document.querySelectorAll(`#${inp.dataset.alvo} tbody tr`).forEach((tr) => {
      tr.style.display = tr.textContent.toLowerCase().includes(termo) ? "" : "none";
    });
  })
);

// ---------------------------------------------------------------- plantao
async function carregarPlantao() {
  const e = await api("/api/estado");
  $("#aviso-ia").textContent = e.ia
    ? "IA local disponível. A primeira resposta demora alguns segundos (o modelo é carregado sob demanda)."
    : "IA local indisponível nesta VM: os assistentes mostram as dicas escritas.";
  const p = e.plantao;
  if (!p) {
    $("#plantao-estado").innerHTML = `
      <div class="cartao estreito">
        <h3>Nenhum plantão em andamento</h3>
        <p>Ao iniciar, os casos vão chegar ao Wazuh ao longo do tempo, misturando ataques e ruído.
        Trabalhe a fila no Wazuh (Threat Hunting) e registre um ticket por caso aqui no Console.
        A nota sai quando você encerrar o plantão.</p>
        <label>Tipo <select id="tipo">
          <option value="treino" selected>Plantão de treino (assistentes ligados)</option>
          <option value="prova">Prova final (60 minutos, sem assistentes, vale certificado)</option></select></label>
        <label id="rotulo-duracao">Duração <select id="duracao"><option value="30">30 minutos</option><option value="60" selected>60 minutos</option><option value="120">2 horas</option></select></label>
        <p class="ajuda">Na prova final, nota ${e.nota_minima} ou mais libera o certificado em PNG.</p>
        <button id="btn-iniciar">Iniciar plantão</button>
      </div>`;
    $("#tipo").onchange = () => { $("#rotulo-duracao").style.display = $("#tipo").value === "prova" ? "none" : ""; };
    $("#btn-iniciar").onclick = async () => {
      const prova = $("#tipo").value === "prova";
      if (prova && !confirm("Iniciar a prova final? São 60 minutos e o mentor, a entrevista e o copiloto ficam desligados.")) return;
      await api("/api/plantao/iniciar", { method: "POST",
        body: JSON.stringify({ duracao_min: +$("#duracao").value, modo_prova: prova }) });
      $("#plantao-resultado").innerHTML = "";
      carregarPlantao();
    };
  } else {
    const fim = new Date(p.fim_previsto), ini = new Date(p.inicio);
    const pct = Math.min(100, Math.round(((Date.now() - ini) / (fim - ini)) * 100));
    $("#plantao-estado").innerHTML = `
      <div class="cartao estreito">
        <h3>${p.modo_prova ? '<span class="selo-prova">Prova final</span> ' : ""}Plantão ${p.numero} em andamento</h3>
        ${p.modo_prova ? '<p class="ajuda">Assistentes desligados. Nota mínima para o certificado: ' + e.nota_minima + "/100.</p>" : ""}
        <p>Início ${hora(p.inicio)} · término previsto ${hora(p.fim_previsto)}</p>
        <div class="barra"><div style="width:${pct}%"></div></div>
        <p><b>${p.casos_chegaram}</b> de ${p.casos_total} casos já chegaram ao Wazuh · <b>${p.tickets}</b> com ticket</p>
        <p class="ajuda">Dica: no Wazuh, filtre por <code>rule.groups:besafe</code> para ver só os alertas do plantão.</p>
        <button id="btn-encerrar" class="secundario">Encerrar plantão e ver a nota</button>
      </div>`;
    $("#btn-encerrar").onclick = async () => {
      if (!confirm("Encerrar o plantão? Casos sem ticket valem zero.")) return;
      const r = await api("/api/plantao/encerrar", { method: "POST" });
      mostrarResultado(r);
      carregarPlantao();
    };
  }
  // sem plantao ativo, mostra o resultado do ultimo plantao encerrado
  if (!p && e.historico.length && !$("#plantao-resultado").innerHTML.trim()) {
    const h = e.historico[0];
    mostrarResultado({ ...h.resultado, numero: h.numero, modo_prova: h.modo_prova, aprovado: h.aprovado,
                       nota_minima: e.nota_minima }, h.certificado);
  }
  $("#historico").innerHTML = e.historico.length
    ? tabela([["numero", "Plantão"], ["modo_prova", "Tipo", (v) => (v ? "Prova final" : "Treino")],
              ["inicio", "Início", hora], ["resultado", "Nota", (r) => `${r.media ?? "-"}/100`],
              ["resultado", "Casos", (r) => `${r.com_ticket ?? 0} de ${r.casos ?? 0} com ticket`],
              ["certificado", "Certificado", (c) => (c ? `<a href="/api/certificado/${c.plantao}.png" download>baixar</a>` : "-")]],
             e.historico)
    : '<p class="ajuda">Nenhum plantão encerrado ainda.</p>';
}

function blocoCertificado(r, emitido) {
  if (!r.modo_prova) return "";
  if (!r.aprovado)
    return `<p class="msg erro">Prova final abaixo de ${r.nota_minima}/100. Revise o gabarito abaixo e faça uma nova prova quando quiser.</p>`;
  return `
    <div class="certificado">
      <p><b>Prova final aprovada!</b> Escreva seu nome como deve aparecer no certificado.</p>
      <div class="linha-cert">
        <input id="cert-nome" maxlength="60" placeholder="Seu nome completo" value="${esc(emitido?.nome || "")}">
        <button id="cert-gerar">${emitido ? "Gerar de novo" : "Gerar certificado"}</button>
      </div>
      <p id="cert-msg" class="msg"></p>
      <div id="cert-saida">${emitido ? imagemCertificado(r.numero, emitido.hash) : ""}</div>
    </div>`;
}

function imagemCertificado(numero, hash) {
  const url = `/api/certificado/${numero}.png?v=${hash.slice(0, 8)}`;
  return `<a href="${url}" download="certificado-besafe-soc-lab.png"><img src="${url}" alt="Certificado"></a>
    <p class="ajuda">SHA-256: <code>${esc(hash)}</code> · <a href="${url}" download="certificado-besafe-soc-lab.png">Baixar PNG</a></p>`;
}

function mostrarResultado(r, emitido) {
  $("#plantao-resultado").innerHTML = `
    <div class="cartao">
      <h3>Resultado ${r.modo_prova ? "da prova final" : "do plantão"}</h3>
      <div class="grande">${r.media}/100</div>
      ${blocoCertificado(r, emitido)}
      <p>${r.com_ticket} de ${r.casos} casos com ticket.${r.perdidos.length ? ` Sem ticket (alertas perdidos): <b>${r.perdidos.join(", ")}</b>.` : ""}</p>
      ${r.detalhes.map((d) => `
        <div class="item-ticket">
          <b>${esc(d.caso)}</b> · ${esc(d.titulo)}<br>
          Gabarito: ${NOMES[d.verdade.classificacao]}, severidade ${SEV[d.verdade.severidade]},
          escalar: ${d.verdade.escalar ? "sim" : "não"}${d.verdade.iocs.length ? `, indicadores: ${esc(d.verdade.iocs.join(", "))}` : ""}<br>
          ${d.avaliacao ? `<b>${d.avaliacao.total}/100</b><ul>${d.avaliacao.itens.map((i) => `<li>${esc(i.comentario)} (${i.pontos})</li>`).join("")}</ul>` : "<b>0/100</b> · sem ticket"}
        </div>`).join("")}
    </div>`;
  const gerar = $("#cert-gerar");
  if (gerar) gerar.onclick = async () => {
    const msg = $("#cert-msg");
    gerar.disabled = true; msg.className = "msg"; msg.textContent = "Gerando o certificado...";
    try {
      const c = await api("/api/certificado", { method: "POST",
        body: JSON.stringify({ plantao: r.numero, nome: $("#cert-nome").value }) });
      msg.className = "msg ok"; msg.textContent = `Certificado emitido: ${c.conceito}.`;
      $("#cert-saida").innerHTML = imagemCertificado(r.numero, c.hash);
      carregarPlantao();
    } catch (e) { msg.className = "msg erro"; msg.textContent = e.message; }
    gerar.disabled = false;
  };
}

// ---------------------------------------------------------------- tickets
$("#form-ticket").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const f = new FormData(ev.target);
  const corpo = {
    caso: f.get("caso").trim().toUpperCase(), classificacao: f.get("classificacao"), severidade: f.get("severidade"),
    escalar: !!f.get("escalar"), iocs: f.get("iocs").split("\n").map((s) => s.trim()).filter(Boolean), resumo: f.get("resumo"),
  };
  const msg = $("#ticket-msg");
  try {
    const r = await api("/api/tickets", { method: "POST", body: JSON.stringify(corpo) });
    msg.className = "msg ok"; msg.textContent = r.mensagem;
    ev.target.reset();
    carregarTickets();
  } catch (e) { msg.className = "msg erro"; msg.textContent = e.message; }
});

async function carregarTickets() {
  const t = await api("/api/tickets");
  $("#lista-tickets").innerHTML = t.length
    ? t.map((x) => `<div class="item-ticket"><b>${esc(x.caso)}</b> · ${NOMES[x.classificacao]} · ${SEV[x.severidade]} ·
        escalar <span class="etiqueta ${x.escalar ? "sim" : "nao"}">${x.escalar ? "sim" : "não"}</span><br>
        <small>${esc(x.resumo).slice(0, 220)}</small></div>`).join("")
    : '<p class="ajuda">Nenhum ticket ainda. Registrar de novo o mesmo caso substitui o anterior.</p>';
}

// ---------------------------------------------------------------- servicos simulados
const simNao = (v) => `<span class="etiqueta ${v ? "sim" : "nao"}">${v ? "sim" : "não"}</span>`;

async function carregarDiretorio() {
  $("#tabela-diretorio").innerHTML = tabela([["nome", "Nome"], ["login", "Login"], ["setor", "Setor"], ["cargo", "Cargo"],
    ["gestor", "Gestor"], ["horario", "Horário"], ["ferias", "Férias", simNao], ["maquina", "Máquina"]], await api("/api/diretorio"));
}
async function carregarInventario() {
  $("#tabela-inventario").innerHTML = tabela([["nome", "Máquina"], ["ip", "IP"], ["funcao", "Função"], ["setor", "Setor"],
    ["criticidade", "Criticidade"], ["responsavel", "Responsável"]], await api("/api/inventario"));
}
async function carregarMudancas() {
  const m = await api("/api/mudancas");
  $("#lista-mudancas").innerHTML = m.length
    ? m.map((x) => `<div class="item-ticket"><b>${esc(x.numero)}</b> · ${esc(x.titulo)}<br>Janela: ${esc(x.janela)} · Origem: ${esc(x.origem)} · Responsável: ${esc(x.responsavel)}</div>`).join("")
    : '<p class="ajuda">Nenhuma mudança aprovada para o período.</p>';
}
async function carregarPhishing() {
  const m = await api("/api/phishing");
  $("#lista-phishing").innerHTML = m.length
    ? m.map((x) => `<div class="cartao" style="margin-bottom:12px"><b>${esc(x.assunto)}</b><br>
        <small>De: ${esc(x.de)} · Para: ${esc(x.para)} · Reportado por ${esc(x.reportado_por)} · Caso ${esc(x.caso)}</small>
        <p>${esc(x.corpo)}</p></div>`).join("")
    : '<p class="ajuda">Nenhum e-mail reportado até agora.</p>';
}

$("#form-intel").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  try {
    const r = await api("/api/intel?valor=" + encodeURIComponent(new FormData(ev.target).get("valor")));
    $("#resultado-intel").innerHTML = `<div class="cartao estreito" style="margin-top:12px">
      <h3 class="veredito-${esc(r.veredito.split(" ")[0])}">${esc(r.veredito.toUpperCase())}</h3>
      <p><b>${esc(r.valor)}</b> · detecções: ${esc(r.deteccoes)}${r.primeira_vez_visto ? ` · visto pela primeira vez ${esc(r.primeira_vez_visto)}` : ""}</p>
      <p class="ajuda">${esc(r.comentario)}</p></div>`;
  } catch (e) { $("#resultado-intel").textContent = e.message; }
});

// ---------------------------------------------------------------- assistentes
async function chamar(botao, saida, fn) {
  botao.disabled = true; saida.textContent = "pensando...";
  try { saida.textContent = await fn(); } catch (e) { saida.textContent = e.message; }
  botao.disabled = false;
}
const mentor = (nova) => chamar(nova ? $("#mentor-dica") : $("#mentor-perguntar"), $("#mentor-saida"), async () => {
  const r = await api("/api/mentor", { method: "POST", body: JSON.stringify({ caso: $("#mentor-caso").value, texto: $("#mentor-texto").value, nova_dica: nova }) });
  return r.nivel ? `[dica ${r.nivel}] ${r.resposta}` : r.resposta;
});
$("#mentor-perguntar").onclick = () => mentor(false);
$("#mentor-dica").onclick = () => mentor(true);
$("#pessoa-perguntar").onclick = () => chamar($("#pessoa-perguntar"), $("#pessoa-saida"), async () => {
  const r = await api("/api/pessoa", { method: "POST", body: JSON.stringify({ caso: $("#pessoa-caso").value, texto: $("#pessoa-texto").value }) });
  return `${r.nome}: ${r.resposta}`;
});
$("#copiloto-resumir").onclick = () => chamar($("#copiloto-resumir"), $("#copiloto-saida"), async () => {
  const r = await api("/api/copiloto/" + encodeURIComponent($("#copiloto-caso").value));
  return r.ia ? `${r.resumo}\n\n⚠ ${r.aviso}` : "Copiloto indisponível (IA local desligada). Analise os eventos no Wazuh.";
});

// ---------------------------------------------------------------- inicio
function carregar(aba) {
  ({ plantao: carregarPlantao, tickets: carregarTickets, diretorio: carregarDiretorio, inventario: carregarInventario,
     mudancas: carregarMudancas, phishing: carregarPhishing }[aba] || (() => {}))();
}
setInterval(() => { $("#relogio").textContent = new Date().toLocaleTimeString("pt-BR"); }, 1000);
setInterval(() => { if ($("#plantao").classList.contains("ativo")) carregarPlantao(); }, 15000);
if (location.hash.length > 1) abrirAba(location.hash.slice(1)); else carregarPlantao();
