import streamlit as st
import pandas as pd
import plotly.express as px
from io import StringIO
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# aggiorno per forzare deploy


st.set_page_config(page_title="Finanza Intelligente", layout="wide")
st.title("\U0001F4B8 Finanza Intelligente – Analisi Spese Personali")

uploaded_file = st.file_uploader("Carica il tuo file CSV bancario", type=["csv"])

if uploaded_file:
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    df = pd.read_csv(stringio, delimiter=';')

    df.columns = ['data_registrazione', 'data_valuta', 'descrizione', 'importo']
    df['data'] = pd.to_datetime(df['data_valuta'], format='%d.%m.%Y')
    df['importo'] = df['importo'].str.replace('.', '', regex=False)
    df['importo'] = df['importo'].str.replace(',', '.', regex=False).astype(float)
    df['descrizione'] = df['descrizione'].str.upper().str.strip().str.replace('  ', ' ', regex=False)

    st.success(f"File caricato con {len(df)} transazioni")

    categorie_keywords = {
        'ABBONAMENTO': ['NETFLIX', 'SPOTIFY', 'DISNEY', 'NOWTV'],
        'UTENZE': ['ENEL', 'HERA', 'LUCE', 'GAS', 'FASTWEB'],
        'SPESA': ['ESSELUNGA', 'CARREFOUR', 'IPER', 'COOP'],
        'TRASPORTI': ['BENZINA', 'Q8', 'IP', 'AUTOSTRADE'],
        'RICARICHE': ['RICARICA', 'BONIFICO', 'ACCREDITO'],
        'ALTRO': []
    }

    def assegna_categoria(desc):
        for cat, keys in categorie_keywords.items():
            if any(k in desc for k in keys):
                return cat
        return 'ALTRO'

    df['categoria'] = df['descrizione'].apply(assegna_categoria)

    st.markdown("## ✏️ Modifica categoria direttamente nella tabella")

    editable_df = df[['data', 'descrizione', 'importo', 'categoria']].copy()
    gb = GridOptionsBuilder.from_dataframe(editable_df)
    gb.configure_column("categoria", editable=True, cellEditor="agSelectCellEditor", 
                        cellEditorParams={"values": list(categorie_keywords.keys())})
    gb.configure_grid_options(domLayout='normal')
    grid_options = gb.build()

    grid_response = AgGrid(
        editable_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MANUAL,
        height=400,
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        theme='alpine'
    )

    modified_df = grid_response['data']
    df['categoria'] = modified_df['categoria']

    st.markdown("## 📊 Grafico spese per categoria")
    cat_summary = df.groupby('categoria')['importo'].sum().reset_index()
    fig1 = px.bar(cat_summary, x='categoria', y='importo', title="Totale spese per categoria")
    st.plotly_chart(fig1)

    st.markdown("## 📅 Spese mensili")
    df['mese'] = df['data'].dt.to_period('M').astype(str)
    spese_mensili = df.groupby('mese')['importo'].sum().reset_index()
    fig2 = px.line(spese_mensili, x='mese', y='importo', markers=True, title="Andamento mensile delle spese")
    st.plotly_chart(fig2)

    st.markdown("## \U0001F501 Spese ricorrenti")
    df['descrizione_base'] = df['descrizione'].str.extract(r'([A-Z ]{4,})')[0].fillna(df['descrizione'])
    ricorrenti = df.groupby('descrizione_base').filter(lambda x: len(x) >= 3)

    def calcola_prossima_data(gruppo):
        date_sorted = gruppo['data'].sort_values()
        diff = date_sorted.diff().dt.days.dropna()
        if len(diff) < 1:
            return pd.NaT
        media_giorni = diff.mean()
        ultima_data = date_sorted.max()
        prossima = ultima_data + pd.Timedelta(days=round(media_giorni))
        while prossima <= pd.Timestamp.today():
            prossima += pd.Timedelta(days=round(media_giorni))
        return prossima

    ricap = ricorrenti.groupby('descrizione_base').agg(
        transazioni=('importo', 'count'),
        spesa_totale=('importo', 'sum'),
        ultima_data=('data', 'max')
    )
    ricap['prossimo_pagamento'] = ricorrenti.groupby('descrizione_base').apply(calcola_prossima_data).values
    st.dataframe(ricap.reset_index()[['descrizione_base', 'transazioni', 'spesa_totale', 'ultima_data', 'prossimo_pagamento']].sort_values(by='prossimo_pagamento'))

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica file categorizzato", csv, "spese_categorizzate.csv", "text/csv")

else:
    st.info("Carica un file CSV per iniziare")
