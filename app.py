import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Anti-Fraude de Comprovantes",
    page_icon="🚚",
    layout="wide",
)

st.title("🚚 Anti-Fraude de Comprovantes")
st.markdown("Sistema de detecção de fraudes em comprovantes de entrega logística com IA")

aba1, aba2 = st.tabs(["🔍 Análise", "📊 Histórico"])


with aba1:
    col_esq, col_dir = st.columns([1, 1], gap="large")

    with col_esq:
        st.subheader("Upload do Comprovante")
        arquivo = st.file_uploader(
            "Selecione a imagem do comprovante",
            type=["jpg", "jpeg", "png", "webp"],
            help="Formatos aceitos: JPG, JPEG, PNG, WEBP",
        )
        if arquivo:
            st.image(arquivo, caption="Pré-visualização", width=220)

        endereco = st.text_input(
            "Endereço de entrega",
            placeholder="Ex: Rua das Flores, 123, São Paulo, SP",
        )
        horario = st.text_input(
            "Horário limite de entrega (opcional)",
            placeholder="Ex: 18:00",
        )
        analisar_btn = st.button(
            "🔎 Analisar Comprovante",
            type="primary",
            use_container_width=True,
            disabled=(arquivo is None or not endereco),
        )

    with col_dir:
        st.subheader("Resultado da Análise")

        if analisar_btn:
            if not arquivo or not endereco:
                st.warning("Selecione uma imagem e preencha o endereço antes de analisar.")
            else:
                with st.spinner("Analisando comprovante com IA..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/analisar",
                            files={"file": (arquivo.name, arquivo.getvalue(), arquivo.type)},
                            data={"endereco": endereco, "horario_limite": horario},
                            timeout=180,
                        )

                        if response.status_code == 200:
                            resultado = response.json()
                            score = resultado["score_risco"]
                            veredito = resultado["veredito"]
                            motivos = resultado.get("motivos", [])
                            distancia = resultado.get("distancia_km")
                            ocr_texto = resultado.get("ocr", "")

                            if veredito == "Suspeito":
                                st.markdown("""
<style>
@keyframes perigo {
    0%,100% { box-shadow: 0 0 0px #ff0000; background: rgba(220,30,30,0.18); }
    50%      { box-shadow: 0 0 32px #ff0000; background: rgba(220,30,30,0.38); }
}
.alerta-perigo {
    animation: perigo 0.7s infinite;
    border: 3px solid #ff3333;
    border-radius: 10px;
    padding: 18px;
    text-align: center;
    color: #ff3333;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 1px;
}
</style>
<div class="alerta-perigo">🚨 FRAUDE DETECTADA — SUSPEITO 🚨</div>
""", unsafe_allow_html=True)
                            else:
                                st.success(f"✅  COMPROVANTE APROVADO — {veredito.upper()}")
                                st.balloons()

                            st.divider()

                            col_score, col_dist = st.columns(2)
                            with col_score:
                                st.metric(
                                    label="Score de Risco",
                                    value=f"{score} / 100",
                                    delta=f"{score - 50:+d} vs baseline 50",
                                    delta_color="inverse",
                                )
                            with col_dist:
                                if distancia is not None:
                                    st.metric(
                                        label="Distância GPS",
                                        value=f"{distancia} km",
                                        delta="suspeito" if distancia > 2 else "ok",
                                        delta_color="inverse" if distancia > 2 else "normal",
                                    )
                                else:
                                    st.metric(
                                        label="Distância GPS",
                                        value="N/A",
                                        help="Imagem sem dados EXIF de GPS",
                                    )

                            st.progress(score / 100, text=f"Risco: {score}%")

                            if motivos:
                                st.subheader("📋 Motivos identificados")
                                for motivo in motivos:
                                    if veredito == "Suspeito":
                                        st.warning(f"• {motivo}")
                                    else:
                                        st.info(f"• {motivo}")

                            with st.expander("📝 Texto extraído pelo OCR"):
                                st.text(
                                    ocr_texto.strip() if ocr_texto.strip() else "Nenhum texto extraído da imagem."
                                )

                            with st.expander("🔑 Metadados técnicos"):
                                st.json({
                                    "hash_md5": resultado.get("hash_imagem"),
                                    "hash_visual": resultado.get("hash_visual"),
                                    "distancia_km": distancia,
                                    "score_risco": score,
                                    "veredito": veredito,
                                })
                        else:
                            st.error(f"Erro na API ({response.status_code}): {response.text}")

                    except requests.exceptions.ConnectionError:
                        st.error(
                            "❌ Não foi possível conectar à API.\n\n"
                            "Certifique-se de que o servidor FastAPI está rodando:\n"
                            "`.venv\\Scripts\\uvicorn.exe main:app --port 8000`"
                        )
                    except requests.exceptions.Timeout:
                        st.error("⏱️ A análise demorou mais que o esperado. Tente novamente.")
                    except Exception as e:
                        st.error(f"❌ Erro inesperado: {str(e)}")


with aba2:
    st.subheader("📊 Histórico de Análises")

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        if st.button("🔄 Atualizar", use_container_width=True):
            st.rerun()

    try:
        response = requests.get(f"{API_URL}/historico", timeout=10)

        if response.status_code == 200:
            dados = response.json()

            if dados:
                df = pd.DataFrame(dados)

                total = len(df)
                suspeitos = int((df["veredito"] == "Suspeito").sum())
                aprovados = total - suspeitos
                score_medio = round(df["score_risco"].mean(), 1)
                pct_fraude = round(suspeitos / total * 100, 1) if total > 0 else 0.0

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Analisados", total)
                col2.metric("Suspeitos 🚨", suspeitos, delta=f"{pct_fraude}%", delta_color="inverse")
                col3.metric("Aprovados ✅", aprovados)
                col4.metric("Score Médio", score_medio)

                st.divider()

                colunas_exibir = ["id", "endereco", "score_risco", "veredito", "distancia_km", "data_criacao"]
                df_exibir = df[colunas_exibir].copy()
                df_exibir.columns = ["ID", "Endereço", "Score", "Veredito", "Distância (km)", "Data/Hora"]

                def colorir_veredito(val):
                    if val == "Suspeito":
                        return "background-color: #ffcccc; color: #8b0000; font-weight: bold"
                    if val == "Aprovado":
                        return "background-color: #ccffcc; color: #006400; font-weight: bold"
                    return ""

                st.dataframe(
                    df_exibir.style.map(colorir_veredito, subset=["Veredito"]),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Nenhuma análise realizada ainda. Use a aba 🔍 Análise para começar.")

        else:
            st.error(f"Erro ao buscar histórico: {response.status_code}")

    except requests.exceptions.ConnectionError:
        st.error(
            "❌ Não foi possível conectar à API.\n\n"
            "Certifique-se de que o servidor FastAPI está rodando:\n"
            "`.venv\\Scripts\\uvicorn.exe main:app --port 8000`"
        )
    except Exception as e:
        st.error(f"❌ Erro ao carregar histórico: {str(e)}")
