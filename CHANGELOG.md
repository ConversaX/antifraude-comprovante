# Changelog

Todas as mudanças significativas neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2026-07-21

### ✨ Added
- Sistema completo de detecção de fraudes em comprovantes de entrega
- Integração com Claude API para análise inteligente de imagens
- Validação de GPS com Google Maps API
- Detecção de manipulação digital com OpenCV (Canny Edge Detection)
- Hash MD5 para identificar duplicatas exatas
- Hash Visual (pHash) para imagens visualmente idênticas
- Interface Streamlit com 2 abas (Single Analysis + Historical)
- API FastAPI com Swagger documentado
- Banco SQLite para persistência de análises
- Suporte para OCR em português e inglês (EasyOCR)

### 🔐 Security
- Credenciais protegidas com .env (não commitadas)
- Validação de entrada em todos os endpoints
- Rate limiting implícito
- Isenção de responsabilidade em produção

### 📖 Docs
- README em português com 170+ linhas
- Documentação de instalação completa
- Guia de configuração
- Exemplos de uso
- Aviso legal de responsabilidade

---

## [Unreleased]

### 🔄 Planned
- [ ] Dashboard de analytics em tempo real
- [ ] Integração com sistemas CRM (Salesforce, HubSpot)
- [ ] Webhooks customizáveis
- [ ] Suporte a batch processing
- [ ] Model fine-tuning com dados históricos
- [ ] API GraphQL
- [ ] Mobile app para análise rápida
- [ ] Exportar relatórios em PDF/Excel

### 🎨 Improvements
- [ ] Performance: cache de análises
- [ ] UX: melhorar interface do Streamlit
- [ ] Testes: aumentar cobertura para 90%+
- [ ] CI/CD: adicionar GitHub Actions

---

[1.0.0]: https://github.com/ConversaX/antifraude-comprovante/releases/tag/v1.0.0