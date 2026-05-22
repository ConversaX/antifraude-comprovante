# 🛡️ Anti-Fraude de Comprovantes

Sistema inteligente de detecção de fraudes em comprovantes de entrega logística, combinando **IA generativa**, **visão computacional** e **análise de metadados GPS**.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.38-red?logo=streamlit)
![Claude](https://img.shields.io/badge/Claude-Haiku_4.5-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## O problema

Empresas de logística sofrem diariamente com motoristas que enviam comprovantes falsos, reutilizados ou fotografados no lugar errado — sem que ninguém perceba. Este sistema automatiza a verificação.

---

## Como funciona

Cada imagem enviada passa por **5 camadas de análise simultâneas**:

| Camada | O que verifica |
|---|---|
| 🤖 **IA (Claude Haiku)** | A foto mostra uma entrega real? Pacote, local, pessoa recebendo? |
| 📍 **GPS EXIF** | Coordenadas da foto batem com o endereço informado? |
| 🔍 **OpenCV Canny** | Há sinais de edição digital ou manipulação? |
| 🔑 **Hash MD5** | Essa imagem já foi enviada antes? |
| 👁️ **Hash Visual (pHash)** | Imagem visualmente idêntica a outra já analisada? |

**Score final:** soma ponderada das 5 camadas → **Aprovado** (≤ 70) ou **Suspeito** (> 70)

---

## Stack

- **Backend:** FastAPI + Uvicorn
- **Frontend:** Streamlit
- **IA:** Anthropic Claude Haiku 4.5 (visão computacional)
- **OCR:** EasyOCR (português + inglês, CPU)
- **Imagem:** OpenCV, Pillow, imagehash
- **GPS:** EXIF + Google Maps Geocoding API
- **Banco:** SQLite
- **Gerenciador de pacotes:** uv

---

## Pré-requisitos

- Python 3.11
- [`uv`](https://docs.astral.sh/uv/) instalado
- Chave de API da [Anthropic](https://console.anthropic.com/)
- Chave de API do [Google Maps](https://console.cloud.google.com/) *(opcional — para validação GPS)*

---

## Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/antifraude-comprovante.git
cd antifraude-comprovante

# 2. Crie o ambiente virtual com Python 3.11
uv venv --python 3.11

# 3. Instale as dependências
uv pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env e adicione suas chaves
```

> ⚠️ **PyTorch no Windows:** se ocorrer erro de DLL ao iniciar, instale a versão CPU:
> ```bash
> uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu --force-reinstall
> ```

---

## Configuração

Edite o arquivo `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...        # Obrigatório
GOOGLE_MAPS_API_KEY=AIza...         # Opcional (validação GPS)
```

---

## Rodando o projeto

**Windows — clique duas vezes em `start.bat`**, ou manualmente:

```bash
# Terminal 1 — API
.venv\Scripts\uvicorn.exe main:app --host 127.0.0.1 --port 8000

# Terminal 2 — Interface
.venv\Scripts\streamlit.exe run app.py
```

Acesse: **http://localhost:8501**

API Swagger: **http://localhost:8000/docs**

---

## Estrutura

```
antifraude-comprovante/
├── main.py            # API FastAPI — lógica de análise híbrida
├── app.py             # Interface Streamlit — 2 abas
├── database.py        # SQLite — persistência das análises
├── fraud_detector.py  # OpenCV + imagehash
├── requirements.txt
├── start.bat          # Inicialização rápida (Windows)
├── .env.example
└── .gitignore
```

---

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/analisar` | Analisa comprovante (`multipart/form-data`) |
| `GET` | `/historico` | Últimas 100 análises |
| `GET` | `/health` | Status da API |
| `GET` | `/docs` | Swagger interativo |

---

## O que reprova automaticamente

- Foto do baú, moto ou veículo sem evidência de entrega
- Selfie do entregador sem local nem pacote
- Imagem duplicada (já enviada antes)
- GPS da foto a mais de 2 km do endereço informado
- Sinais de edição digital (OpenCV)

---

## ⚠️ Aviso Legal e Isenção de Responsabilidade

Este projeto é um **MVP experimental** disponibilizado "como está", sem garantias de qualquer tipo.

**Pontos importantes:**

1. **Não é produto final:** Requer testes extensivos, validações de segurança, tratamento de edge cases e adaptação às regras de negócio específicas antes de qualquer uso em produção.

2. **Falsos positivos/negativos:** Sistemas de IA podem errar. Esta ferramenta é um auxílio à decisão, não substitui auditoria humana. Decisões críticas devem sempre ter revisão manual.

3. **Sem garantia:** O autor não se responsabiliza por perdas financeiras, decisões equivocadas ou qualquer dano direto/indireto decorrente do uso deste código.

4. **LGPD/Dados:** Ao usar com fotos reais de clientes, garanta conformidade com LGPD. Dados EXIF podem conter localização precisa.

5. **Use por sua conta e risco:** Ao fazer fork/clone deste repositório, você concorda que testará e validará tudo por conta própria.

Para uso comercial, recomenda-se consultoria jurídica e técnica especializada.

---

## Licença

MIT © 2026 — sinta-se livre para usar, modificar e contribuir.
