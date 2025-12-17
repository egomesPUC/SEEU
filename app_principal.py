import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(
    page_title="Dashboard - Processos / Partes Moradores de Rua",
    layout="wide"
)

# ==========================
# Carregamento de dados
# ==========================
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path,sep=",")

    # Normalização de tipos
    if "datarecebimento" in df.columns:
        df["datarecebimento"] = pd.to_datetime(
            df["datarecebimento"], errors="coerce"
        )
        # Mês/ano (como data no 1º dia do mês) para o slider
        df["data_mes"] = df["datarecebimento"].dt.to_period("M").dt.to_timestamp().dt.date

    # Egresso -> boolean
    if "Egresso" in df.columns:
        df["Egresso_bool"] = (
            df["Egresso"]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(["true", "t", "1", "sim", "s"])
        )
    else:
        df["Egresso_bool"] = False

    # Capital -> boolean
    if "Capital" in df.columns:
        df["capital_bool"] = (
            df["Capital"]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(["true", "t", "1", "sim", "s"])
        )
    else:
        df["capital_bool"] = False

    return df


# AJUSTE o caminho conforme seu arquivo
def main():

    DATA_PATH = "SEEU_DASH.csv"
    df = load_data(DATA_PATH)

    # ==========================
    # SIDEBAR - FILTROS GERAIS
    # (valem para todas as abas)
    # ==========================
    st.sidebar.header("Filtros")

    filtered_df = df.copy()

    # --- 1) Filtro Egressos (radio) ---
    if "Egresso_bool" in filtered_df.columns:
        egresso_opt = st.sidebar.radio(
            "PARTES (NO PROCESSO)",
            options=["Todos", "Somente egressos"],
            index=0,
        )
        if egresso_opt == "Somente egressos":
            filtered_df = filtered_df[filtered_df["Egresso_bool"] == True]

    # --- 2) Filtro Capital (checkbox) ---
    if "capital_bool" in filtered_df.columns:
        only_capital = st.sidebar.checkbox(
            "Capital (apenas capital de UF e Brasília)",
            value=False,
        )
        if only_capital:
            filtered_df = filtered_df[filtered_df["capital_bool"] == True]

    # --- 3) Filtro MUNICÍPIO (campo varacidade) ---
    if "varacidade" in filtered_df.columns:
        municipios_disp = (
            filtered_df["varacidade"]
            .dropna()
            .astype(str)
            .sort_values()
            .unique()
            .tolist()
        )

        selected_municipios = st.sidebar.multiselect(
            "Município (varacidade)",
            options=municipios_disp,
            default=municipios_disp,  # começa com todos
        )

        if selected_municipios:
            filtered_df = filtered_df[
                filtered_df["varacidade"].astype(str).isin(selected_municipios)
            ]

    # --- 4) Filtro TIPO DE DOCUMENTO (campo tipodocumento) ---
    if "tipodocumento" in filtered_df.columns:
        tipos_disp = (
            filtered_df["tipodocumento"]
            .dropna()
            .astype(str)
            .sort_values()
            .unique()
            .tolist()
        )

        selected_tipos = st.sidebar.multiselect(
            "Tipo de Documento",
            options=tipos_disp,
            default=tipos_disp,  # começa com todos
        )

        if selected_tipos:
            filtered_df = filtered_df[
                filtered_df["tipodocumento"].astype(str).isin(selected_tipos)
            ]

    # ==========================
    # LAYOUT PRINCIPAL - ABAS
    # ==========================
    st.title("Dashboard - Processos / Partes Moradores de Rua")

    tab1, tab2, tab3 = st.tabs(
        [
            "ABA 1 - Processos por Partes (Visão Geral)",
            "ABA 2 - Partes por Tipo de Documento",
            "ABA 3 - Processos por Município",
        ]
    )

    # ============================================================
    # ABA 1 - PROCESSO POR PARTES MORADORES DE RUA
    # ============================================================
    with tab1:
        st.subheader("ABA 1 - Processos por Partes Moradores de Rua")

        if filtered_df.empty:
            st.warning("Nenhum registro encontrado com os filtros selecionados.")
        else:
            df_tab1 = filtered_df.copy()

            # Slider por data de recebimento (mês/ano)
            if "data_mes" in df_tab1.columns and df_tab1["data_mes"].notna().any():
                min_mes = df_tab1["data_mes"].min()
                max_mes = df_tab1["data_mes"].max()

                data_ini, data_fim = st.slider(
                    "Período por Data de Recebimento (Mês/Ano)",
                    min_value=min_mes,
                    max_value=max_mes,
                    value=(min_mes, max_mes),
                    format="M/Y",  # mês/ano no slider
                )

                df_tab1 = df_tab1[
                    (df_tab1["data_mes"] >= data_ini)
                    & (df_tab1["data_mes"] <= data_fim)
                ]

            if df_tab1.empty:
                st.warning("Nenhum registro dentro do período selecionado.")
            else:
                # Tabela de dados
                st.markdown("### Tabela de dados (após filtros e período)")
                st.dataframe(df_tab1, use_container_width=True)

                # ===== MÉTRICAS RESUMO =====
                # 1) Qtde de cumprimento de cartório (cada linha = 1 cumprimento)
                qt_cumprimento = len(df_tab1)
                # 2) Qtde de processos sem repetição (campo numeroprocesso)
                if "numeroprocesso" in df_tab1.columns:
                    qt_proc_unicos = df_tab1["numeroprocesso"].nunique()
                else:
                    qt_proc_unicos = 0

                # 3) Qtde de partes sem repetição (campo codparte)
                if "codparte" in df_tab1.columns:
                    qt_partes_unicas = df_tab1["codparte"].nunique()
                else:
                    qt_partes_unicas=0

                
                # 4) Qtde de partes com flag de morador de rua (campo codparte)
                qt_morador_de_rua_identificado = 0
                if "pessoaemsituacaoderua" in df_tab1.columns:
                    dfAux=df.query("pessoaemsituacaoderua==True")
                    qt_morador_de_rua_identificadoGeral = dfAux["codparte"].nunique()
                    dfAux=df_tab1.query("pessoaemsituacaoderua==True")
                    qt_morador_de_rua_identificadoFiltrado = dfAux["codparte"].nunique()
                

                st.markdown("### Quadro Resumo")
                c1, c2, c3 = st.columns(3)
                c1.metric("Qtde de cumprimento de cartório", int(qt_cumprimento))
                c2.metric("Qtde de processos (sem repetição)", int(qt_proc_unicos))
                c3.metric("Qtde de partes (sem repetição)", int(qt_partes_unicas))

                c4, c5 = st.columns(2)
                c4.metric("Qtde de Moradores de Rua com Flag de Identificação Geral", int(qt_morador_de_rua_identificadoGeral))
                c5.metric("Qtde de Moradores de Rua com Flag de Identificação Filtrado", int(qt_morador_de_rua_identificadoFiltrado))

                # ===== GRÁFICO DE BARRAS POR ESTADO =====
                # Queremos: para cada estado,
                # - qtde de cumprimento de cartório (linhas)
                # - qtde de processos únicos
                # - qtde de partes únicas
                if "estado" not in df_tab1.columns:
                    st.error("Coluna 'estado' não encontrada para o gráfico por estado.")
                else:
                    df_est = df_tab1.copy()
                    df_est["estado"] = df_est["estado"].fillna("Sem estado")

                    estados = []

                    for est, grupo in df_est.groupby("estado"):
                        total_cumprimento = len(grupo)
                        if "numero" in grupo.columns:
                            proc_unicos_est = grupo["numero"].nunique()
                        else:
                            proc_unicos_est = 0
                        if "codparte" in grupo.columns:
                            partes_unicas_est = grupo["codparte"].nunique()
                        else:
                            partes_unicas_est = 0

                        estados.append(
                            {
                                "estado": est,
                                "Métrica": "Cumprimento de cartório",
                                "Quantidade": total_cumprimento,
                            }
                        )
                        estados.append(
                            {
                                "estado": est,
                                "Métrica": "Processos (sem repetição)",
                                "Quantidade": proc_unicos_est,
                            }
                        )
                        estados.append(
                            {
                                "estado": est,
                                "Métrica": "Partes (sem repetição)",
                                "Quantidade": partes_unicas_est,
                            }
                        )

                    df_est_melt = pd.DataFrame(estados)

                    st.markdown(
                        "### Gráfico de barras - Cumprimentos, Processos e Partes por Estado"
                    )

                    chart_est = (
                        alt.Chart(df_est_melt)
                        .mark_bar()
                        .encode(
                            x=alt.X("estado:N", title="Estado"),
                            y=alt.Y("Quantidade:Q", title="Quantidade"),
                            color=alt.Color("Métrica:N", title="Métrica"),
                            column=alt.Column("Métrica:N", title=None, spacing=10),
                            tooltip=["estado", "Métrica", "Quantidade"],
                        )
                        .resolve_scale(y="independent")
                    )

                    st.altair_chart(chart_est, use_container_width=True)

    # ============================================================
    # ABA 2 - QTDE DE PARTES MORADORES DE RUA POR TIPO DE DOCUMENTO
    # ============================================================
    with tab2:
        st.subheader("ABA 2 - Qtde de Partes por Tipo de Documento")

        if filtered_df.empty:
            st.warning("Nenhum registro encontrado com os filtros selecionados.")
        else:
            df_tab2 = filtered_df.copy()

            if "tipodocumento" not in df_tab2.columns:
                st.error("Coluna 'tipodocumento' não encontrada.")
            else:
                # Quantidade de partes por tipo de documento
                df_tab2["tipodocumento"] = df_tab2["tipodocumento"].fillna("Não informado")

                if "codparte" in df_tab2.columns:
                    partes_por_doc = (
                        df_tab2.groupby("tipodocumento")["codparte"]
                        .nunique()
                        .reset_index(name="qtd_partes")
                    )
                else:
                    partes_por_doc = (
                        df_tab2.groupby("tipodocumento")
                        .size()
                        .reset_index(name="qtd_partes")
                    )

                partes_por_doc = partes_por_doc.sort_values(
                    "qtd_partes", ascending=False
                )

                c1, c2 = st.columns(2)
                total_partes = int(partes_por_doc["qtd_partes"].sum())
                c1.metric("Total de partes (soma por tipo de documento)", total_partes)
                c2.metric("Nº de tipos de documento", int(len(partes_por_doc)))

                st.markdown("### Gráfico de barras - Partes por Tipo de Documento")

                chart_doc = (
                    alt.Chart(partes_por_doc)
                    .mark_bar()
                    .encode(
                        x=alt.X(
                            "tipodocumento:N",
                            sort="-y",
                            title="Tipo de Documento",
                        ),
                        y=alt.Y("qtd_partes:Q", title="Quantidade de partes"),
                        tooltip=[
                            alt.Tooltip(
                                "tipodocumento:N", title="Tipo de Documento"
                            ),
                            alt.Tooltip(
                                "qtd_partes:Q", title="Quantidade de partes"
                            ),
                        ],
                    )
                    .properties(height=500)
                )

                st.altair_chart(chart_doc, use_container_width=True)

                st.markdown("### Tabela de apoio (Tipo de Documento x Qtde de Partes)")
                st.dataframe(partes_por_doc, use_container_width=True)

    # ============================================================
    # ABA 3 - QTDE DE PROCESSOS POR MUNICÍPIO (varacidade)
    # ============================================================
    with tab3:
        st.subheader("ABA 3 - Qtde de Processos por Município (varacidade)")

        if filtered_df.empty:
            st.warning("Nenhum registro encontrado com os filtros selecionados.")
        else:
            df_tab3 = filtered_df.copy()

            if ("varacidade" not in df_tab3.columns) or (
                "numero" not in df_tab3.columns
            ):
                st.error(
                    "Colunas 'varacidade' e/ou 'numeroprocesso' não encontradas."
                )
            else:
                df_tab3["varacidade"] = df_tab3["varacidade"].fillna("Sem município")

                procs_por_muni = (
                    df_tab3.groupby("varacidade")["numero"]
                    .nunique()
                    .reset_index(name="qtd_processos")
                )

                procs_por_muni = procs_por_muni.sort_values(
                    "qtd_processos", ascending=False
                )

                total_proc = int(procs_por_muni["qtd_processos"].sum())
                num_munis = int(len(procs_por_muni))

                c1, c2 = st.columns(2)
                c1.metric("Total de processos (soma por município)", total_proc)
                c2.metric("Nº de municípios", num_munis)

                st.markdown("### Gráfico de barras - Processos por Município")

                chart_muni = (
                    alt.Chart(procs_por_muni)
                    .mark_bar()
                    .encode(
                        x=alt.X(
                            "varacidade:N",
                            sort="-y",
                            title="Município (varacidade)",
                        ),
                        y=alt.Y("qtd_processos:Q", title="Quantidade de processos"),
                        tooltip=[
                            alt.Tooltip(
                                "varacidade:N", title="Município (varacidade)"
                            ),
                            alt.Tooltip(
                                "qtd_processos:Q",
                                title="Quantidade de processos",
                            ),
                        ],
                    )
                    .properties(height=500)
                )

                st.altair_chart(chart_muni, use_container_width=True)

                st.markdown("### Tabela de apoio (Município x Qtde de Processos)")
                st.dataframe(procs_por_muni, use_container_width=True)
