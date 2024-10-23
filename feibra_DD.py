import streamlit as st
import pandas as pd

# Farbdefinitionen
DARKORANGE1 = "#FF7F00"
WHITE = "#FFFFFF"


# Funktion zum Laden der Daten (XLSX)
@st.cache_data
def load_data(file):
    try:
        if file.name.endswith('.xlsx'):
            df = pd.read_excel(file)
        else:
            st.error("Bitte nur Excel-Dateien hochladen!")
            return None

        # Konvertiere die 'ERFASST' Spalte in datetime
        df['ERFASST'] = pd.to_datetime(df['ERFASST'], format='%d.%m.%Y %H:%M:%S', errors='coerce')

        return df
    except Exception as e:
        st.error(f"Ein Fehler ist beim Laden der Datei aufgetreten: {str(e)}")
        return None


# Funktion zur Vorverarbeitung der Daten für "Zusatzinfos gesamt"
def preprocess_data_zusatzinfos(df):
    # Zählen der Einträge für TYPE
    type_counts = df['TYPE'].value_counts()

    # Extrahieren der PLZ aus GEBIET
    df['PLZ'] = df['GEBIET'].str[:4]

    # Aufteilen der ZUSATZINFO
    zusatzinfo_split = df['ZUSATZINFO'].str.split(expand=True).melt()
    zusatzinfo_split = zusatzinfo_split.dropna().drop('variable', axis=1)
    zusatzinfo_split = zusatzinfo_split.merge(df, left_index=True, right_index=True)

    # Zählen der Einträge für KONTROLLE
    kontrolle_counts = df['KONTROLLE'].value_counts()

    return df, type_counts, zusatzinfo_split, kontrolle_counts


# Funktion zum Erstellen des Balkendiagramms
def create_bar_chart(df, x, y, title):
    fig = px.bar(df, x=x, y=y, title=title)
    fig.update_traces(marker_color=DARKORANGE1)  # Alle Balken haben dieselbe Farbe
    fig.update_layout(
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        font_color=DARKORANGE1
    )
    return fig


# Streamlit-App-Konfiguration
st.set_page_config(layout="wide", page_title="Datenanalyse Tool")

# CSS für das Farbschema
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {WHITE};
    }}
    [data-testid="stSidebar"] {{
        background-image: url('https://www.feibra.at/wp-content/uploads/2018/12/feibra-logo-small.png');
        background-size: 80% auto;
        background-repeat: no-repeat;
        background-position: 20px 20px;
        padding-top: 120px;
    }}
     .sidebar .sidebar-content {{
        padding: 0 !important;
    }}
    div[role="radiogroup"] {{
        padding: 0 !important;
        margin: 0 -1rem;  /* Negative margin to extend beyond sidebar padding */
    }}
    div[role="radiogroup"] > label > div:first-of-type {{
        display: none;
    }}
    div[role="radiogroup"] label {{
        border: none;
        border-bottom: 1px solid rgba(49, 51, 63, 0.2);
        border-radius: 0;
        padding: 1rem;
        margin: 0;
        display: block;
        cursor: pointer;
        width: calc(100%);
        box-sizing: border-box;
        font-size:20px;
    }}
    div[role="radiogroup"] label:last-child {{
        border-bottom: none;
    }}
    div[role="radiogroup"] label:hover {{
        background-color: rgba(255, 75, 75, 0.1);
    }}
    div[role="radiogroup"] label[data-baseweb="radio"] {{
        background-color: transparent;
        transition: background-color 0.3s, color 0.3s;
    }}
    div[role="radiogroup"] label[data-baseweb="radio"] input:checked + div {{
        background-color: {DARKORANGE1};
        color: white;
        padding: 1rem;
        margin: -1rem;
        width: calc(100% + 2rem);
    }}
    .stMultiSelect [data-baseweb="tag"] {{
        background-color: #FF7F00 !important;
        color: white !important;
    }}
    .stMultiSelect [data-baseweb="tag"]:hover {{
        background-color: #E67300 !important;
    }}
    .stMultiSelect [data-baseweb="tag"] span[role="img"] {{
        color: white !important;
    }}
""", unsafe_allow_html=True)

# Hauptbereich
st.title("Datenanalyse Tool")

# Datei-Upload
uploaded_file = st.file_uploader("Wähle bitte eine XLSX-Datei aus", type=['xlsx'])

if uploaded_file is not None:
    df = load_data(uploaded_file)

    if df is not None:
        # Daten vorverarbeiten
        df, type_counts, zusatzinfo_split, kontrolle_counts = preprocess_data_zusatzinfos(df)

        # Sidebar
        st.sidebar.title("Auswertungen")
        menu = st.sidebar.radio("",
                                    ["Zusatzinfo gesamt", "Verteilerperformance", "Kontrollen pro Verteiler"])


        # Inhalt basierend auf Menüauswahl
        if menu == "Zusatzinfo gesamt":
            st.subheader("Zusatzinfo gesamt")

            # Filter
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                selected_filialen = st.multiselect("FILIALE", options=sorted(df['FILIALE'].unique()))
            with col2:
                selected_types = st.multiselect("TYPE", options=sorted(type_counts.index))
            with col3:
                selected_plz = st.multiselect("PLZ", options=sorted(df['PLZ'].unique()))
            with col4:
                selected_kontrolle = st.multiselect("KONTROLLE", options=sorted(kontrolle_counts.index))
            with col5:
                selected_zusatzinfo = st.multiselect("ZUSATZINFO", options=sorted(zusatzinfo_split['value'].unique()))

                # Daten filtern
                filtered_df = df.copy()
                if selected_filialen:
                    filtered_df = filtered_df[filtered_df['FILIALE'].isin(selected_filialen)]
                if selected_types:
                    filtered_df = filtered_df[filtered_df['TYPE'].isin(selected_types)]
                if selected_plz:
                    filtered_df = filtered_df[filtered_df['PLZ'].isin(selected_plz)]
                if selected_kontrolle:
                    filtered_df = filtered_df[filtered_df['KONTROLLE'].isin(selected_kontrolle)]
                if selected_zusatzinfo:
                    filtered_df = filtered_df[
                        filtered_df['ZUSATZINFO'].apply(lambda x: any(info in str(x) for info in selected_zusatzinfo))]

                # Metriken
            col1, = st.columns(1)
            with col1:
                st.metric("Kontrollen gesamt", f"{len(filtered_df):,}")


            # Zusatzinfo aufteilen und zählen
            zusatzinfo_split = filtered_df['ZUSATZINFO'].str.split(expand=True).melt()
            zusatzinfo_split = zusatzinfo_split.dropna().drop('variable', axis=1)
            zusatzinfo_counts = zusatzinfo_split['value'].value_counts().reset_index()
            zusatzinfo_counts.columns = ['ZUSATZINFO', 'Anzahl']
            zusatzinfo_counts = zusatzinfo_counts.sort_values('Anzahl', ascending=False)

            # Balkendiagramm erstellen
            fig = create_bar_chart(
                zusatzinfo_counts,
                x='ZUSATZINFO',
                y='Anzahl',
                title='Anzahl der Zusatzinfos'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Zusatzinfo Tabelle
            st.subheader("Bereinigte Datei")
            st.dataframe(zusatzinfo_split.merge(filtered_df, left_index=True, right_index=True)[
                             ['value', 'FILIALE', 'TYPE', 'GEBIET', 'KONTROLLE', 'ERFASST']])

        elif menu == "Verteilerperformance":
            st.subheader("Verteilerperformance")


            # Funktion zur Vorverarbeitung der Daten für "Verteilerperformance"
            def preprocess_data_zusatzinfos(df):

                #leere Zellen in Spalte NAME/VT/ABNEHMER durch "Verteiler unbekannt" ersetzen
                df['NAME/VT/ABNEHMER'] = df['NAME/VT/ABNEHMER'].replace('', None).fillna('Verteiler unbekannt')

                # Zählen der Einträge für TYPE
                type_counts = df['TYPE'].value_counts()

                # Extrahieren der PLZ aus GEBIET
                df['PLZ'] = df['GEBIET'].str[:4]

                # Aufteilen der ZUSATZINFO
                zusatzinfo_split = df['ZUSATZINFO'].str.split(expand=True).melt()
                zusatzinfo_split = zusatzinfo_split.dropna().drop('variable', axis=1)
                zusatzinfo_split = zusatzinfo_split.merge(df, left_index=True, right_index=True)

                # Zählen der Einträge für KONTROLLE
                kontrolle_counts = df['KONTROLLE'].value_counts()

                return df, type_counts, zusatzinfo_split, kontrolle_counts


            if df is not None:
                # Daten vorverarbeiten
                df, type_counts, zusatzinfo_split, kontrolle_counts = preprocess_data_zusatzinfos(df)

                # Filter
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                        selected_filialen = st.multiselect("FILIALE", options=sorted(df['FILIALE'].unique()))
                with col2:
                        selected_types = st.multiselect("TYPE", options=sorted(type_counts.index))
                with col3:
                        selected_plz = st.multiselect("PLZ", options=sorted(df['PLZ'].unique()))
                with col4:
                        selected_kontrolle = st.multiselect("KONTROLLE", options=sorted(kontrolle_counts.index))
                with col5:
                        selected_verteiler = st.multiselect("VERTEILER", options=sorted(df['NAME/VT/ABNEHMER'].astype(str).unique()))


                # Daten filtern
                filtered_df = df.copy()
                if selected_types:
                        filtered_df = filtered_df[filtered_df['TYPE'].isin(selected_types)]
                if selected_plz:
                        filtered_df = filtered_df[filtered_df['PLZ'].isin(selected_plz)]
                if selected_kontrolle:
                        filtered_df = filtered_df[filtered_df['KONTROLLE'].isin(selected_kontrolle)]
                if selected_filialen:
                        filtered_df = filtered_df[filtered_df['FILIALE'].isin(selected_filialen)]
                if selected_verteiler:
                        filtered_df= filtered_df[filtered_df['NAME/VT/ABNEHMER'].isin(selected_verteiler)]

                # Metriken
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Kontrollen gesamt", f"{len(filtered_df):,}")
                with col2:
                    st.metric("Durchschnittl. Kontrollen pro Tag",
                            f"{len(filtered_df) / df['ERFASST'].dt.date.nunique():.2f}")

                # Zusatzinfo aufteilen und zählen
                zusatzinfo_split = filtered_df['ZUSATZINFO'].str.split(expand=True).melt()
                zusatzinfo_split = zusatzinfo_split.dropna().drop('variable', axis=1)
                zusatzinfo_counts = zusatzinfo_split['value'].value_counts().reset_index()
                zusatzinfo_counts.columns = ['ZUSATZINFO', 'Anzahl']
                zusatzinfo_counts = zusatzinfo_counts.sort_values('Anzahl', ascending=False)


                # Funktion zum Erstellen des Balkendiagramms
                def create_bar_chart(df, x, y, title):
                    fig = px.bar(df, x=x, y=y, title=title)
                    fig.update_traces(marker_color=DARKORANGE1)  # Alle Balken haben dieselbe Farbe
                    fig.update_layout(
                        plot_bgcolor=WHITE,
                        paper_bgcolor=WHITE,
                        font_color=DARKORANGE1
                    )
                    return fig

                # Balkendiagramm erstellen
                fig = create_bar_chart(
                    zusatzinfo_counts,
                    x='ZUSATZINFO',
                    y='Anzahl',
                    title='Anzahl der Zusatzinfos'
                )
                st.plotly_chart(fig, use_container_width=True)

                # Zusatzinfo Tabelle
                st.subheader("Bereinigte Datei")
                st.dataframe(zusatzinfo_split.merge(filtered_df, left_index=True, right_index=True)[
                                     ['value', 'FILIALE', 'TYPE', 'GEBIET', 'KONTROLLE', 'ERFASST', 'NAME/VT/ABNEHMER']])

        elif menu == "Kontrollen pro Verteiler":
            st.subheader("Kontrollen pro Verteiler")

            # Datenbereinigung
            df['PLZ'] = df['GEBIET'].str[:4]
            df['ERFASST_DATUM'] = pd.to_datetime(df['ERFASST']).dt.date

            # Berechnung der durchschnittlichen Kontrollen pro Tag für jeden Verteiler
            verteiler_stats = df.groupby('NAME/VT/ABNEHMER').agg({
                'ERFASST_DATUM': 'nunique',
                'KONTROLLE': 'count'
            }).reset_index()
            verteiler_stats['AVG_KONTROLLEN_PRO_TAG'] = verteiler_stats['KONTROLLE'] / verteiler_stats['ERFASST_DATUM']
            verteiler_stats['VERTEILER_WERT'] = verteiler_stats['NAME/VT/ABNEHMER'] + ' - ' + verteiler_stats[
                'AVG_KONTROLLEN_PRO_TAG'].round(0).astype(str)

            # Dynamische Filter
            filtered_df = df.copy()

            # FILIALE Filter
            selected_filialen = st.multiselect("FILIALE", options=sorted(filtered_df['FILIALE'].unique()))
            if selected_filialen:
                filtered_df = filtered_df[filtered_df['FILIALE'].isin(selected_filialen)]

            # VERTEILER Filter
            verteiler_options = sorted(verteiler_stats['NAME/VT/ABNEHMER'].unique())
            selected_verteiler = st.multiselect("VERTEILER", options=verteiler_options)
            if selected_verteiler:
                filtered_df = filtered_df[filtered_df['NAME/VT/ABNEHMER'].isin(selected_verteiler)]

            # TYPE Filter
            type_options = sorted(filtered_df['TYPE'].unique())
            selected_types = st.multiselect("TYPE", options=type_options)
            if selected_types:
                filtered_df = filtered_df[filtered_df['TYPE'].isin(selected_types)]

            # Metriken
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Kontrollen gesamt", f"{len(filtered_df):,}")
            with col2:
                st.metric("Durchschnittl. Kontrollen pro Tag",
                          f"{len(filtered_df) / filtered_df['ERFASST_DATUM'].nunique():.2f}")

            # Daten für das Stacked Bar Chart vorbereiten
            chart_data = filtered_df.groupby(['NAME/VT/ABNEHMER', 'KONTROLLE']).size().unstack(
                fill_value=0).reset_index()
            chart_data = chart_data.merge(verteiler_stats[['NAME/VT/ABNEHMER', 'VERTEILER_WERT']],
                                          on='NAME/VT/ABNEHMER')
            chart_data = chart_data.sort_values('NICHT_OK', ascending=False)

            # Stacked Bar Chart erstellen
            fig = px.bar(chart_data, x='VERTEILER_WERT', y=['NICHT_OK', 'OK'],
                         title='Kontrollen pro Verteiler',
                         labels={'value': 'Anzahl Kontrollen', 'VERTEILER_WERT': 'Verteiler'},
                         height=600,
                         color_discrete_sequence=[DARKORANGE1, '#F3E2A9'])
            fig.update_layout(barmode='stack')

            # Chart anzeigen
            st.plotly_chart(fig, use_container_width=True)

            # Dropdown für Verteiler-Auswahl
            selected_verteiler_detail = st.selectbox("Wähle einen Verteiler für detaillierte Ansicht:",
                                                     options=[''] + list(chart_data['NAME/VT/ABNEHMER']))

            if selected_verteiler_detail:
                st.subheader(f"Tägliche Kontrollen für {selected_verteiler_detail}")

                # Daten für den ausgewählten Verteiler filtern
                verteiler_df = filtered_df[filtered_df['NAME/VT/ABNEHMER'] == selected_verteiler_detail]

                # Metriken für den ausgewählten Verteiler
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Kontrollen gesamt", f"{len(verteiler_df):,}")
                with col2:
                    st.metric("Anzahl OK", f"{verteiler_df['KONTROLLE'].value_counts().get('OK', 0):,}")
                with col3:
                    st.metric("Anzahl NICHT_OK", f"{verteiler_df['KONTROLLE'].value_counts().get('NICHT_OK', 0):,}")

                # Tägliche Daten vorbereiten
                daily_data = verteiler_df.groupby(['ERFASST_DATUM', 'KONTROLLE']).size().unstack(
                    fill_value=0).reset_index()

                # Tägliches Chart erstellen
                daily_fig = px.bar(daily_data, x='ERFASST_DATUM', y=['NICHT_OK', 'OK'],
                                   title=f'',
                                   labels={'value': 'Anzahl Kontrollen', 'ERFASST_DATUM': 'Datum'},
                                   height=400,
                                   color_discrete_sequence=[DARKORANGE1, '#F3E2A9'])
                daily_fig.update_layout(barmode='stack')

                # Tägliches Chart anzeigen
                st.plotly_chart(daily_fig, use_container_width=True)

            # Tabelle mit bereinigten Daten
            st.subheader("Bereinigte Daten")
            st.dataframe(filtered_df[['NAME/VT/ABNEHMER', 'FILIALE', 'TYPE', 'PLZ', 'KONTROLLE', 'ERFASST_DATUM']])

else:
    st.info("Bitte lade eine XLSX hoch, um zu beginnen.")
