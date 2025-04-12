import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

st.set_page_config(page_title="Finanza Intelligente", layout="centered")
st.title("\U0001F4B8 Finanza Intelligente - MVP")

uploaded_file = st.file_uploader("Carica il tuo file CSV bancario", type=["csv"])

if uploaded_file:
    try:
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        df = pd.read_csv(stringio, delimiter=';')

        df.columns = ['data_registrazione', 'data_valuta', 'descrizione', 'importo']
        df['data'] = pd.to_datetime(df['data_valuta'], format='%d.%m.%Y')
        df['importo'] = df['importo'].str.replace('.', '', regex=False)
        df['importo'] = df['importo'].str.replace(',', '.', regex=False).astype(float)
        df['descrizione'] = df['descrizione'].str.upper().str.strip().str.replace('  ', ' ', regex=False)

        st.success(f"File caricato correttamente: {len(df)} transazioni")

        if st.checkbox("Mostra anteprima dati"):
            st.dataframe(df.head(10))

        if st.button("Categorizza spese (base)"):
            categorie_keywords = {
                'ABBONAMENTO': ['NETFLIX', 'SPOTIFY', 'DISNEY', 'NOWTV'],
                'UTENZE': ['ENEL', 'HERA', 'LUCE', 'GAS', 'FASTWEB'],
                'SPESA': ['ESSELUNGA', 'CARREFOUR', 'IPER', 'COOP'],
                'TRASPORTI': ['BENZINA', 'Q8', 'IP', 'AUTOSTRADE'],
                'RICARICHE': ['RICARICA', 'BONIFICO', 'ACCREDITO'],
                'ALTRO': []
            }

            def assegna_categoria(descrizione):
                for categoria, parole_chiave in categorie_keywords.items():
                    if any(keyword in descrizione for keyword in parole_chiave):
                        return categoria
                return 'ALTRO'

            df['categoria'] = df['descrizione'].apply(assegna_categoria)
            st.success("Categorizzazione completata!")
            st.dataframe(df[['data', 'descrizione', 'importo', 'categoria']].head(20))

            # Riepilogo per categoria
            st.subheader("\U0001F4CA Riepilogo per Categoria")
            riepilogo = df.groupby('categoria')['importo'].sum().sort_values()
            st.bar_chart(riepilogo)

            # Spese mensili
            st.subheader("\U0001F4C5 Spese mensili")
            df['mese'] = df['data'].dt.to_period('M').astype(str)
            spese_mensili = df.groupby('mese')['importo'].sum()
            fig, ax = plt.subplots()
            spese_mensili.plot(kind='bar', ax=ax)
            ax.set_ylabel("Totale speso (€)")
            st.pyplot(fig)

            # Riconoscimento spese ricorrenti
            st.subheader("\U0001F501 Spese ricorrenti")
            df['descrizione_base'] = df['descrizione'].str.extract(r'([A-Z ]{4,})')[0].fillna(df['descrizione'])
            ricorrenti = df.groupby('descrizione_base').filter(lambda x: len(x) >= 3)

            def calcola_prossima_data(gruppo):
                date_sorted = gruppo['data'].sort_values()
                if len(date_sorted) < 2:
                    return pd.NaT
                diff = date_sorted.diff().dt.days.dropna()
                media_giorni = diff.mean()
                ultima_data = date_sorted.max()
                return ultima_data + pd.Timedelta(days=round(media_giorni))

            ricap = ricorrenti.groupby('descrizione_base').agg(
                transazioni=('importo', 'count'),
                spesa_totale=('importo', 'sum'),
                ultima_data=('data', 'max')
            )
            ricap['prossimo_pagamento'] = ricorrenti.groupby('descrizione_base').apply(calcola_prossima_data).values
            st.dataframe(ricap.reset_index()[['descrizione_base', 'transazioni', 'spesa_totale', 'ultima_data', 'prossimo_pagamento']].head(10))

            # Download finale
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Scarica file categorizzato", csv, "spese_categorizzate.csv", "text/csv")

    except Exception as e:
        st.error(f"Errore nel caricamento: {e}")
else:
    st.info("Carica un file CSV per iniziare")
