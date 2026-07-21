# 🤝 Contribuindo

Obrigado por considerar contribuir para este projeto! Adoraríamos sua ajuda.

## 🐛 Encontrou um bug?

Abra uma [issue](https://github.com/ConversaX/antifraude-comprovante/issues) com:
- Descrição clara do problema
- Passos para reproduzir
- Comportamento esperado vs. atual
- Screenshots/logs se aplicável
- Seu ambiente (OS, Python version, etc)

## 💡 Tem uma sugestão de melhoria?

Abra uma [discussion](https://github.com/ConversaX/antifraude-comprovante/discussions) para conversar sobre a ideia primeiro!

## 🔧 Quer contribuir com código?

1. **Fork o repositório**
2. **Crie uma branch**: `git checkout -b feature/sua-feature`
3. **Configure o ambiente**:
   ```bash
   git clone https://github.com/seu-usuario/antifraude-comprovante.git
   cd antifraude-comprovante
   uv venv --python 3.11
   uv pip install -r requirements.txt
   ```
4. **Faça suas alterações**
   - Use type hints
   - Adicione docstrings
   - Escreva testes
5. **Teste localmente**:
   ```bash
   python -m pytest
   streamlit run app.py
   ```
6. **Commit com mensagem clara**:
   ```bash
   git commit -m "feat: adiciona detecção por hash visual"
   ```
7. **Push e abra um Pull Request**

## 📋 Padrões de Código

- **Type hints**: Sempre use (PEP 484)
- **Docstrings**: Google style para todas as funções públicas
- **Testes**: Mínimo 80% de coverage
- **Formatação**: Black + isort
- **Linting**: Flake8

## 📚 Documentação

Se adicionar uma feature:
- Atualize o README.md
- Adicione ao CHANGELOG.md
- Documente no `docs/` se necessário

## 🚀 Processo de Review

1. Um mantenedor revisará seu PR
2. Pode pedir ajustes
3. Uma vez aprovado, será mergeado
4. Seu nome vai para os créditos!

## ❓ Dúvidas?

Abra uma discussion ou envie um email: evertonponciano@hotmail.com

**Obrigado por contribuir!** 🎉