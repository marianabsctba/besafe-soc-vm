"""O "mundo" da Pantera Logistica: colaboradores e maquinas, gerados a partir da semente.

Cada copia da VM tem uma semente propria, entao cada aluno ve pessoas, maquinas e IPs
diferentes. A mesma semente sempre gera o mesmo mundo (deterministico).
"""
import random
from dataclasses import dataclass, field, asdict

NOMES = [
    "Ana", "Bruno", "Carla", "Diego", "Eduarda", "Felipe", "Gabriela", "Henrique", "Isabela", "João",
    "Juliana", "Leonardo", "Larissa", "Marcos", "Mariana", "Natália", "Otávio", "Paula", "Rafael", "Renata",
    "Sérgio", "Tatiane", "Vinícius", "Yasmin", "Thiago", "Camila", "Lucas", "Fernanda", "Rodrigo", "Patrícia",
]
SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Lima", "Pereira", "Costa", "Rodrigues", "Almeida", "Nascimento",
    "Ferreira", "Carvalho", "Gomes", "Martins", "Rocha", "Ribeiro", "Alves", "Barbosa", "Cardoso", "Teixeira",
]

# setor: (sigla para o nome da maquina, cargos, criticidade das estacoes)
SETORES = {
    "Financeiro": ("FIN", ["Analista financeiro", "Assistente de contas a pagar", "Tesoureira"], "alta"),
    "RH": ("RH", ["Analista de RH", "Assistente de departamento pessoal"], "alta"),
    "Operações": ("OPS", ["Coordenador de frota", "Analista de rotas", "Despachante"], "media"),
    "Comercial": ("COM", ["Executivo de contas", "Analista comercial"], "media"),
    "TI": ("TI", ["Analista de suporte", "Administrador de sistemas"], "alta"),
    "Logística": ("LOG", ["Conferente", "Analista de logística"], "baixa"),
}

SERVIDORES = [
    ("SRV-DC01", "Controlador de domínio (Active Directory)", "critica", "TI"),
    ("SRV-ERP01", "ERP: financeiro, faturamento e folha", "critica", "TI"),
    ("SRV-ARQ01", "Servidor de arquivos (inclui pastas do RH e do Financeiro)", "critica", "TI"),
    ("SRV-WEB01", "Site de rastreamento de cargas (exposto na internet)", "alta", "TI"),
    ("SRV-MAIL01", "Gateway de e-mail", "alta", "TI"),
    ("SRV-SCAN01", "Scanner de vulnerabilidades autorizado (roda às terças, 10h)", "media", "TI"),
]

HORARIOS = ["08h às 17h", "09h às 18h", "07h às 16h", "13h às 22h"]


@dataclass
class Colaborador:
    login: str
    nome: str
    setor: str
    cargo: str
    gestor: str
    horario: str
    ferias: bool
    maquina: str
    email: str


@dataclass
class Maquina:
    nome: str
    ip: str
    funcao: str
    setor: str
    criticidade: str
    responsavel: str


@dataclass
class Mundo:
    semente: int
    colaboradores: list = field(default_factory=list)
    maquinas: list = field(default_factory=list)
    dominio: str = "pantera-logistica.example"

    def colaborador(self, login):
        return next((c for c in self.colaboradores if c.login == login), None)

    def maquina(self, nome):
        return next((m for m in self.maquinas if m.nome == nome), None)

    def como_dict(self):
        return {"colaboradores": [asdict(c) for c in self.colaboradores],
                "maquinas": [asdict(m) for m in self.maquinas]}


def _login(nome, sobrenome, usados):
    base = f"{nome}.{sobrenome}".lower()
    base = (base.replace("á", "a").replace("ã", "a").replace("é", "e").replace("í", "i")
                .replace("ó", "o").replace("ú", "u").replace("ç", "c").replace("â", "a").replace("ê", "e"))
    login, n = base, 2
    while login in usados:
        login, n = f"{base}{n}", n + 1
    usados.add(login)
    return login


def gerar_mundo(semente: int) -> Mundo:
    r = random.Random(f"mundo-{semente}")
    mundo = Mundo(semente=semente)
    usados = set()
    ips_usados = {"10.10.1.50"}  # reservado para o scanner autorizado
    redes = r.sample(range(10, 61), len(SETORES))
    rede_por_setor = dict(zip(SETORES, redes))

    def ip_unico(prefixo):
        while True:
            ip = f"{prefixo}.{r.randint(10, 230)}"
            if ip not in ips_usados:
                ips_usados.add(ip)
                return ip

    for setor, (sigla, cargos, crit) in SETORES.items():
        quantos = r.randint(4, 7)
        pessoas = []
        for i in range(quantos):
            nome, sobrenome = r.choice(NOMES), r.choice(SOBRENOMES)
            login = _login(nome, sobrenome, usados)
            maquina = f"PL-{sigla}-{i + 1:02d}"
            pessoas.append(Colaborador(
                login=login, nome=f"{nome} {sobrenome}", setor=setor, cargo=r.choice(cargos),
                gestor="", horario=r.choice(HORARIOS), ferias=r.random() < 0.12,
                maquina=maquina, email=f"{login}@{mundo.dominio}"))
            mundo.maquinas.append(Maquina(
                nome=maquina, ip=ip_unico(f"10.10.{rede_por_setor[setor]}"),
                funcao=f"Estação de trabalho do {setor}", setor=setor, criticidade=crit, responsavel=login))
        gestor = pessoas[0]
        gestor.cargo = f"Gerente de {setor}"
        gestor.ferias = False
        for p in pessoas[1:]:
            p.gestor = gestor.login
        mundo.colaboradores.extend(pessoas)

    admins = [c.login for c in mundo.colaboradores if c.setor == "TI"]
    for nome, funcao, crit, setor in SERVIDORES:
        mundo.maquinas.append(Maquina(
            nome=nome, ip="10.10.1.50" if nome == "SRV-SCAN01" else ip_unico("10.10.1"),
            funcao=funcao, setor=setor, criticidade=crit, responsavel=r.choice(admins)))
    return mundo


def ip_externo(r: random.Random) -> str:
    """IPs de fora sempre nas faixas reservadas para documentacao (RFC 5737)."""
    faixa = r.choice(["203.0.113", "198.51.100", "192.0.2"])
    return f"{faixa}.{r.randint(2, 254)}"
