# 🛡️ Anti-Fraude de Comprovantes

Sistema inteligente de detecção de fraudes em comprovantes de entrega logística, combinando **IA generativa**, **visão computacional** e **análise de metadados GPS**.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.38-red?logo=streamlit)
![Claude](https://img.shields.io/badge/Claude-Haiku_4.5-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## O que é (resposta curta)
Um MVP que automatiza a detecção de fraudes em comprovantes de entrega usando Claude (IA), OCR (EasyOCR), OpenCV (detecção de edição), hashes (MD5 + pHash) e validação de GPS — pensado para equipes de logística e operações que querem reduzir fraudes por comprovantes falsos ou reutilizados.

---

## Por que ainda não publicar globalmente
Resumo rápido: o projeto é executável e útil como MVP, mas precisa de hardening (autenticação, rate limiting distribuído), compliance (LGPD, política de retenção), infraestrutura (DB escalável, worker assíncrono) e testes/CI completos antes de um lançamento público.

---

## Como funciona (resumo técnico)
Cada imagem passa por 5 camadas:
- 🤖 Claude Haiku: avaliação semântica/visão (imagem embutida em base64);
- 📍 EXIF GPS: extração e comparação com endereço via Google Geocoding (opcional);
- 🔍 OpenCV (Canny): heurística de edição (edge density);
- 🔑 MD5: bloqueio de duplicatas exatas;
- 👁️ pHash (imagehash): detecção de duplicatas visuais (Hamming threshold configurável).

O score final é composto pela IA + heurísticas; veredito: Aprovado (≤ 70) ou Suspeito (> 70).

---

## Rápido — como rodar (Docker recomendado)
1) Copie as variáveis de ambiente do `.env.example` e configure as chaves (ANTHROPIC_API_KEY obrigatório).
2) Inicie com Docker Compose (recomendado para dev):

```bash
# constrói e sobe API + Streamlit (dev)
docker-compose up --build
```

A API estará em: http://localhost:8000
Streamlit: http://localhost:8501

Variáveis essenciais no `.env` (exemplos):
```
ANTHROPIC_API_KEY=sk-ant-...
API_KEY=sua-chave-secreta
GOOGLE_MAPS_API_KEY=...
DATABASE_URL=fraudes.db
PHASH_THRESHOLD=10
MAX_UPLOAD_MB=10
RATE_LIMIT=20
RATE_PERIOD=60
```

---

## Modo demo (para demonstrações públicas)
Se quiser disponibilizar uma demo pública sem custos/risco de dados:
- execute com `DEMO_MODE=1` (a branch contém suporte para modo demo) — o modo demo pula chamadas à Anthropic e não persiste imagens.
- limite o tráfego com um proxy (ex.: Cloud Run) e monitore quotas.

---

## Exemplos de API (cURL)
POST /analisar — enviar imagem + endereço:

```bash
curl -X POST "http://localhost:8000/analisar" \
  -H "X-API-KEY: sua-chave-secreta" \
  -F "file=@/caminho/para/comprovante.jpg" \
  -F "endereco=Rua das Flores, 123, São Paulo, SP"
```

GET /historico — últimas 100 análises:

```bash
curl -H "X-API-KEY: sua-chave-secreta" http://localhost:8000/historico
```

GET /health
```bash
curl http://localhost:8000/health
```

---

## Recomendações para produção (essenciais)
- Autenticação & autorização: use API keys rotativas ou OAuth; não exponha endpoints sem proteção.
- TLS: coloque a API atrás de um reverse-proxy (NGINX, Cloud Run, ALB) com HTTPS.
- Rate limiting distribuído: não confie em in-memory para produção — use Redis/Proxy para limites globais.
- Worker assíncrono: mova chamadas à IA para uma fila (Redis + RQ/Celery) para reduzir latência e controlar retries/custos.
- Banco: migrar para Postgres (ou managed DB) com Alembic para migrations.
- Segurança de upload: validar MIME, tamanho, e sanitizar nomes; escanear arquivos suspeitos.
- Privacidade/LGPD: criar política de retenção, consentimento explícito e ferramentas de anonimização/exclusão.

---

## Testes, CI e infra incluídos nesta branch
- `.github/workflows/ci.yml` — workflow básico (lint + pytest).
- `Dockerfile` + `docker-compose.yml` — ambiente local reproducível.
- Tests iniciais em `tests/` (fraud_detector, database).

---

## Troubleshooting rápido
- PyTorch/Windows: se houver erro de DLL, instale a versão CPU do torch conforme o README original.
- EasyOCR/CI: runners podem falhar sem libs de sistema (instale dependências do sistema no Dockerfile ou use runners self-hosted).
- Timeouts com Anthropic: verifique quota e tempo limite do request; prefira worker para chamadas longas.

---

## Próximos passos sugeridos (eu posso implementar)
- 1) Worker assíncrono (Redis + RQ) e atualização do docker-compose — recomendado próximo PR.
- 2) Migrar para Postgres + Alembic (migrations) e testes de integração.
- 3) Cobertura de testes e GH Actions com coverage/report.
- 4) Revisão legal/PRIVACY.md para conformidade LGPD.

Se quiser, eu aplico essas alterações automaticamente na branch `feat/production-ready` (já está atualizada) e abro um PR — ou posso abrir PRs menores para cada bloco (infra, DB, worker).

---

## Licença
MIT © 2026 — sinta-se livre para usar, modificar e contribuir.
