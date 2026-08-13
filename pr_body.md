Resumo
- Hardenings e melhorias para tornar o projeto mais “production-ready”:
  - Autenticação por API key (header X-API-KEY) e rate limiting (in-memory configurável).
  - Validação de upload (extensão, tamanho), remoção segura de arquivos temporários.
  - Persistência de hash visual (pHash) em DB e busca por similares (Hamming threshold configurável).
  - Reprovação automática se imagem visualmente semelhante (pHash) já existe.
  - Parsing mais robusto da resposta da IA (sanitização do JSON).
  - Dockerfile + docker-compose (API + Streamlit) para desenvolvimento.
  - GitHub Actions (CI): lint + pytest.
  - Rascunhos de PRIVACY.md, SECURITY.md, CODE_OF_CONDUCT.md.
  - .env.example com novas variáveis (API_KEY, PHASH_THRESHOLD, MAX_UPLOAD_MB, RATE_LIMIT, etc).
  - Testes iniciais (fraud_detector, database).
  - Pequenos ajustes em fraud_detector.py e database.py (pHash helpers, busca por similares, timestamps UTC).

Arquivos principais adicionados/alterados
- Added: Dockerfile, docker-compose.yml, .github/workflows/ci.yml, PRIVACY.md, SECURITY.md, CODE_OF_CONDUCT.md, tests/
- Updated: main.py (auth, rate limit, validation, pHash checks), database.py (hash_visual persistence + buscar_hash_visual_similar), fraud_detector.py (hamming_distance helper), .env.example (novas variáveis)

Motivação técnica
- Melhorar segurança inicial (autenticação, limites);
- Tornar duplicatas visuais detectáveis (pHash);
- Facilitar reprodução local usando Docker;
- Preparar base para worker assíncrono e migração para DB escalável.

Checklist antes do merge (recomendado)
- [ ] Validar secrets em Settings → Secrets: ANTHROPIC_API_KEY, API_KEY, GOOGLE_MAPS_API_KEY.
- [ ] Rodar CI localmente (especial atenção a EasyOCR/OpenCV/torch).
- [ ] Revisão de segurança/LGPD (PRIVACY.md rascunho).
- [ ] Decidir DB de produção: Postgres + Alembic (recomendado) ou manter SQLite (dev).
- [ ] Planejar worker assíncrono (Redis) em PR seguinte, se desejado.
- [ ] Atualizar README com instruções Docker e modo demo (se for publicar demo público).

Como criar o PR (1 clique)
- Link direto para criar PR:  
  https://github.com/ConversaX/antifraude-comprovante/compare/main...feat/production-ready?expand=1

Próximos passos recomendados (após abrir PR)
1. Rodar CI, corrigir pequenos problemas de dependências (EasyOCR/torch em runners).
2. Abrir PR separado para:
   - Implementar worker assíncrono (Redis + RQ/Celery) e atualizar docker-compose.
   - Migrar para Postgres e adicionar Alembic (migrations).
   - Expandir testes (mocks para IA, integração).
3. Revisão legal da PRIVACY.md / LGPD.
4. Preparar demo mode (sem persistir imagens e sem chamar Anthropic) para divulgação pública.
