import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict, List
from datetime import datetime, timedelta

# Farbdefinitionen
DARKORANGE1 = "#FF7F00"
WHITE = "#FFFFFF"

PERFORMANCE_ZUSATZINFOS = [
                        'OK',
                        'SOMMERGARTEN',
                        'NACHGEFRAGT',
                        'LETZTER_STOCK',
                        'SACKGASSE',
                        'FALSCHE_ABGABESTELLE',
                        'NICHT_GANZ_IN_ABGABESTELLE',
                        'SENDUNG_BESCHAEDIGT',
                        'IN_EU_HBFA_VERTEILT',
                        'IN_ZEITUNGSROLLE_VERTEILT',
                        'WERBEVERZICHT_UEBERSEHEN',
                        'PROSPEKTE_FEHLEN',
                        'PROSPEKTE_MEHRFACH',
                        'PROSPEKTE_EINGELEGT',
                        'PROSPEKTE_ZU_FRUEH_VERTEILT',
                        'PROSPEKTE_ZU_SPAET_VERTEILT',
                        'PROSPEKTE_NICHT_BEAUFTRAGT',
                        'LETZTES_STOCKWERK_AUSGELASSEN',
                        'STOCKWERK_AUSGELASSEN',
                        'HBFA_FAECHER_AUSGELASSEN',
                    ]

VERTEILER_ZUSATZINFOS = [
                        'FALSCHE_ABGABESTELLE',
                        'NICHT_GANZ_IN_ABGABESTELLE',
                        'SENDUNG_BESCHAEDIGT',
                        'IN_EU_HBFA_VERTEILT',
                        'IN_ZEITUNGSROLLE_VERTEILT',
                        'WERBEVERZICHT_UEBERSEHEN',
                        'PROSPEKTE_FEHLEN',
                        'PROSPEKTE_MEHRFACH',
                        'PROSPEKTE_EINGELEGT',
                        'PROSPEKTE_ZU_FRUEH_VERTEILT',
                        'PROSPEKTE_ZU_SPAET_VERTEILT',
                        'PROSPEKTE_NICHT_BEAUFTRAGT',
                        'LETZTES_STOCKWERK_AUSGELASSEN',
                        'STOCKWERK_AUSGELASSEN',
                        'HBFA_FAECHER_AUSGELASSEN',
                    ]


INCLUDE_ZUSATZINFOS = [
                    'BG_SCHLOSS_DEFEKT',
                    'Z_SCHLOSS_DEFEKT',
                    'VERTEILER_NICHT_BEGONNEN',
                    'HBFA_NICHT_EINSEHBAR',
                    'KEIN_ZUTRITT_MOEGLICH',
                    'ANSCHRIFT_UNGENUEGEND',
                    'ABGABESTELLE_UNZUREICHEND_BESCHRIFTET',
                    'KEINE_ABGABESTELLE',
                    'ALTES_PROSPEKT_NICHT_ENTFERNT',
                    'ABGABESTELLE_UEBERFUELLT',
                    'ZUSTELLHINDERNIS',
                    'ABGABESTELLE_LEER',
                    'ADRESSEN_NICHT_ZUGESTELLT',
                    'EU_HBFA',
                    'EMPFAENGER_UNBEKANNT',
                    'ZEITUNGSROLLE',
                    'KEIN_BG_Z_SCHLOSS',
                    'FALSCH_VERTEILT',
                    'ZUTRITT_NUR_DURCH_ANLAEUTEN_MOEGLICH',
                    'WURF_BESCHAEDIGT',
                    'TUEREINWURF',
                    'PROSPEKTE_NICHT_BEAUFTRAGT',
                    'PROSPEKTE_EINGELEGT',
                    'IN_EU_HBFA_VERTEILT',
                    'NOTES_TUERHAENGER',
                    'SACKERL_NICHT_VERWENDET',
                ]
# Funktion zum Laden der Daten (XLSX)
@st.cache_data
def load_data(files, special_column, monthly_columns):
    regular_dataframes = []
    special_dataframes = []
    # Dictionary für die verschiedenen monthly DataFrames
    monthly_dataframes_dict = {col: [] for col in monthly_columns}
    
    for file in files:
        try:
            if file.name.endswith(('.xlsx', '.XLSX')):
                df = pd.read_excel(file)
                
                # Überprüfen, ob die Spalte vorhanden ist
                if special_column in df.columns:
                    special_dataframes.append(df)

                # Überprüfen für jede Spalte
                monthly_found = False
                for col in monthly_columns:
                    if col in df.columns:
                        monthly_dataframes_dict[col].append(df)
                        monthly_found = True

                # Nur wenn keine monatliche Spalte gefunden wurde, als reguläres DataFrame behandeln
                if not monthly_found and special_column not in df.columns:
                    # Debugging-Ausgabe für Spaltennamen
                    
                    # Konvertiere die 'ERFASST' Spalte in datetime
                    if 'ERFASST' in df.columns:
                        df['ERFASST'] = pd.to_datetime(df['ERFASST'], format='%d.%m.%Y %H:%M:%S', errors='coerce')
                    else:
                        ' '
                    
                    if 'GEBIET' in df.columns:
                        df['PLZ'] = df['GEBIET'].str[:4]
                    else:
                         ' '
                    
                    if 'FILIALE' in df.columns:
                        df = df[df['FILIALE'] != 'Fil12']
                    else:
                        ' '
                    
                    def check_zusatzinfo(row):
                        if pd.isna(row['ZUSATZINFO']):
                            return row['KONTROLLE']
                        
                        zusatzinfos = str(row['ZUSATZINFO']).split()
                        if any(info in VERTEILER_ZUSATZINFOS for info in zusatzinfos):
                            return 'PERF. NICHT_OK'
                        return row['KONTROLLE']
                    
                    df['KONTROLLE'] = df.apply(check_zusatzinfo, axis=1)
                    
                    regular_dataframes.append(df)
            else:
                st.error(f"{file.name} ist keine Excel-Datei!")
        except Exception as e:
            ' '
    
    # Zusammenführen der regulären DataFrames
    regular_df = pd.concat(regular_dataframes, ignore_index=True) if regular_dataframes else None
    
    return regular_df, special_dataframes, monthly_dataframes_dict



# Funktion zur Vorverarbeitung der Daten
def preprocess_data_zusatzinfos(df):
    # Zählen der Einträge für TYPE
    type_counts= df['TYPE'].value_counts()

    # Extrahieren der PLZ aus GEBIET
    df['PLZ'] = df['GEBIET'].str[:4]

    # Aufteilen der ZUSATZINFO
    zusatzinfo_split = df['ZUSATZINFO'].str.split(expand=True).melt()
    zusatzinfo_split = zusatzinfo_split.dropna().drop('variable', axis=1)
    zusatzinfo_split = zusatzinfo_split.merge(df, left_index=True, right_index=True)

    # Zählen der Einträge für KONTROLLE
    kontrolle_counts = df['KONTROLLE'].value_counts()

    return df, type_counts, zusatzinfo_split, kontrolle_counts

# Neue Funktion speziell für Verteilerperformance
def preprocess_data_verteilerperformance(df):
    # Liste der erlaubten Zusatzinfos für Verteilerperformance
    VERTEILER_ZUSATZINFOS = [
        'FALSCHE_ABGABESTELLE',
        'NICHT_GANZ_IN_ABGABESTELLE',
        'SENDUNG_BESCHAEDIGT',
        'IN_EU_HBFA_VERTEILT',
        'IN_ZEITUNGSROLLE_VERTEILT',
        'WERBEVERZICHT_UEBERSEHEN',
        'PROSPEKTE_FEHLEN',
        'PROSPEKTE_MEHRFACH',
        'PROSPEKTE_EINGELEGT',
        'PROSPEKTE_ZU_FRUEH_VERTEILT',
        'PROSPEKTE_ZU_SPAET_VERTEILT',
        'PROSPEKTE_NICHT_BEAUFTRAGT',
        'LETZTES_STOCKWERK_AUSGELASSEN',
        'STOCKWERK_AUSGELASSEN',
        'HBFA_FAECHER_AUSGELASSEN',
    ]
    
    df['NAME/VT/ABNEHMER'] = df['NAME/VT/ABNEHMER'].replace('', None).fillna('Verteiler unbekannt')
    type_counts = df['TYPE'].value_counts()
    df['PLZ'] = df['GEBIET'].str[:4]
    verteiler_split = df['ZUSATZINFO'].str.split(expand=True).melt()
    verteiler_split = verteiler_split.dropna().drop('variable', axis=1)
    verteiler_split = verteiler_split[verteiler_split['value'].isin(VERTEILER_ZUSATZINFOS)]
    verteiler_counts = verteiler_split['value'].value_counts().reset_index()
    verteiler_counts.columns = ['ZUSATZINFO', 'Anzahl']
    verteiler_counts = verteiler_counts.sort_values('Anzahl', ascending=False)
    kontrolle_counts = df['KONTROLLE'].value_counts()

    
    return df, type_counts, verteiler_split, kontrolle_counts, verteiler_counts,VERTEILER_ZUSATZINFOS





def aktualisierte_fil(df):

    # Dictionary mit PLZ-Mapping für alle Filialen
    filial_mapping = {
        'Fil01': [1070, 1080, 1090, 1150, 1160, 1170, 1180, 1190, 1200],
        
        'Fil02': [1050, 1130, 1140, 1230],
        
        'Fil03': [1040, 1060, 1100, 1110, 1120],
        
        'Fil05': [1010, 1020, 1030, 1210, 1220],
        
        'Fil06': [6020],
        
        'Fil07': [3071, 3100, 3104, 3105, 3107, 3110, 3121, 3123, 3124, 3125, 
                 3130, 3131, 3133, 3134, 3140, 3141, 3142, 3143, 3150, 3151, 3200, 
                 3205, 3384, 3385, 3388],
        
        'Fil08': [1300, 2320, 2322, 2325, 2326, 2331, 2333, 2334, 2340, 2344, 
                 2345, 2351, 2352, 2353, 2361, 2362, 2371, 2372, 2380, 2381, 
                 2384, 2391, 2401, 2402, 2403, 2404, 2405, 2410, 2412, 2413, 
                 2431, 2432, 2433, 2434, 2435, 2440, 2441, 2442, 2443, 2444, 
                 2451, 2452, 2453, 2454, 2460, 2462, 2463, 2464, 2465, 2471, 
                 2472, 2481, 2482, 2483, 2485, 2486, 2491, 2531, 2532, 7000, 
                 7011, 7012, 7013, 7034, 7035, 7041, 7042, 7051, 7052, 7061, 
                 7062, 7063, 7064, 7071, 7072, 7081, 7082, 7083, 7091],
        
        'Fil09': [4020, 4030, 4040, 4048, 4050, 4052, 4053, 4055, 4060, 4061, 
                 4063, 4073, 4600, 4614],
        
        'Fil10': [8010, 8020, 8036, 8041, 8042, 8043, 8044, 8045, 8046, 8047, 
                 8051, 8052, 8053, 8054, 8055],
        
        'Fil13': [2504, 2511, 2512, 2514, 2521, 2522, 2523, 2524, 2525, 2540, 2542, 
                 2544, 2551, 2552, 2602, 2700, 7020, 7021, 7022, 7023, 7024, 
                 7025, 7031, 7032, 7033, 7201, 7202, 7203, 7210, 7212, 7221, 
                 7222, 7223],
        
        'Fil15': [5020, 5026]
    }
    
    try:
        # Konvertiere PLZ zu Integer, mit Fehlerbehandlung
        df['PLZ'] = pd.to_numeric(df['PLZ'], errors='coerce')
        
        # Neue Spalte mit bestehenden Filialwerten
        neue_filialen = df['FILIALE'].copy()
        
        # Aktualisiere Filialen basierend auf PLZ-Mapping
        for filiale, plz_list in filial_mapping.items():
            # Maske für alle PLZs die zur aktuellen Filiale gehören
            maske = df['PLZ'].isin(plz_list)
            # Update nur die Zeilen wo die PLZ matched
            neue_filialen.loc[maske] = filiale
            
        return neue_filialen
        
    except Exception as e:
        print(f"Fehler bei der Filialzuordnung: {str(e)}")
        return df['FILIALE']  # Im Fehlerfall original Werte zurückgeben
    

def get_target_value(name: str, target_values: Dict[int, List[str]]) -> int:
    for value, names in target_values.items():
        if name in names:
            return value
    return 0

def process_data(special_dataframes, fixed_branches, target_values, names_to_remove):
    processed_data = []
    for special_df in special_dataframes:
        special_df = special_df[~special_df['ERFASSER'].isin(names_to_remove)]

        # Fill in missing 'SOLL WERT' with 0
        special_df['SOLL WERT'].fillna(0, inplace=True)

        # Remove fixed 'SOLL WERT' values from rows that don't match the fixed branch
        for branch, names in fixed_branches.items():
            for name in names:
                mask = (special_df['ERFASSER'] == name)
                if mask.sum() > 1:
                    indices_to_keep = mask & (special_df['FILIALE'] == branch)
                    indices_to_remove = mask & ~indices_to_keep
                    special_df.loc[indices_to_remove, 'SOLL WERT'] = 0

                if (mask.sum() == 1 and not any(special_df.loc[mask, 'FILIALE'] == branch)) or mask.sum() == 0:
                    new_entry = pd.DataFrame({
                        'FILIALE': [branch],
                        'ERFASSER': [name],
                        'SOLL WERT': [get_target_value(name, target_values)]
                    })
                    special_df = pd.concat([special_df, new_entry], ignore_index=True)

        # Fill in missing values with 0
        special_df.fillna(0, inplace=True)

        special_df['%Änderung'] = (special_df['IST'] / special_df['SOLL WERT']) * 100
        special_df['%Änderung'] = special_df['%Änderung'].map(lambda x: f"{x:.2f}%")

        special_df['100%']= 100
        special_df['100%'] = special_df['100%'].map(lambda x: f"{x:.2f}%")



        special_df['⌀Kontrollen'] = (special_df['IST'] / 16)
        special_df['⌀Kontrollen'] = special_df['⌀Kontrollen'].map(lambda x: f"{x:.0f}")

        special_df['DIFF'] = special_df['IST'] - special_df['SOLL WERT']
        processed_data.append(special_df)
        

        
    return pd.concat(processed_data, ignore_index=True)

    


AKTUALISIERTE_GB = {
        'Fil01' : ['AKRAP Ivica', 'FRATRIK Anton', 'JURACKA MIROSLAV', 'KUBES PAVEL', 'NAGY ZSOLT', 'ÖZTÜRK TOLGA', 'PALAGIC SORIN-MIRCEA', 'VIASZ-KADI IMRE'],
        'Fil02' : ['HINTERWALLNER PATRICK', 'IZER PETER', 'KLARIC SASA', 'Lastro Marko', 'MORAR Catalin', 'SALA STANISLAV'],
        'Fil03' : ['AMBRUS DOREL', 'BATISTA ', 'DANIHEL Norbert', 'GHOTRA GURVINDER SINGH', 'LAPOSA MIKLOS', 'MAYER ', 'RISTIC ', 'TOTH ', 'VIRAG ADAM'] ,
        'Fil05' : ['ADAMOVIC LUBOMIR', 'KAJDIC Muhamed', 'KRUK Maciej', 'LOBODAS MAREK', 'Lubinski Stanislaw', 'PETRANEK IVAN', 'RACZ LASZLO BALINT'] ,
        'Fil06' : ['MÜLLNER MARIO', 'PAYR FLORIAN', 'Vergeiner Fabian'],
        'Fil07' : ['HABERL GERALD', 'JOZSA ROLAND', 'SEBÖK ROBERT', 'STAUDINGER FRIEDRICH'] ,
        'Fil08' : ['Klavik Kurt', 'LIPKA ZOLTAN', 'NIEFERGALL GERALD', 'Saibl Klaus', 'SCHÖPF OTMAR', 'STEIDL ANDREAS', 'Weidinger Christian'] ,
        'Fil09' : ['DUSEK Petr', 'HUMER Sven Sebastian', 'IVANIC Roman', 'KOBIDA ROMAN', 'NAIRZ MICHAEL', 'PODMAJERSKY Viktor', 'REICH Roland', 'SIMKO RADEK', 'VYBOH Jaroslav', 'WEIDINGER THOMAS', 'WINKLER Christian', 'ZSAKOVICS Adrian'] ,
        'Fil10' : ['BOGAR ADAM', 'GALAVITS PATRIK', 'KÄFFER Dietmar', 'Neger Helmut', 'VIDA ÁDÁM'] ,
        'Fil13' : ['GAZICA Ivica', 'KARL ELISABETH', 'KLAMBAUER Erwin', 'KONDOR', 'REBEKIC Vlatko', 'SZUPPIN Bianca', 'VARGA ARPAD'] ,
        'Fil15' : ['PICHLER Maximilian', 'RISTIC Sretko', 'ZICKBAUER Gerald', 'BAYER SIEGFRIED']  
        }
ERFASSER_FILIALE_MAPPING = {
        gb : filiale
        for filiale, gb_liste in AKTUALISIERTE_GB.items()
        for gb in gb_liste
    }
    
def apply_fixed_filiale(df):
    # Neue Spalte erstellen mit den festen Filialen-Zuordnungen
    df['FILIALE'] = df['ERFASSER'].map(ERFASSER_FILIALE_MAPPING)

    return df
    


    


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
        margin: 0 -1rem;  
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
# Beispielaufruf der Funktion
files = st.file_uploader("Lade deine Excel-Dateien hoch", accept_multiple_files=True)
special_column = 'IST'
monthly_column = 'AUSZAHLBEMERKUNG','STUECK','ZUSATZAUFWAND', 'Kostenstelle', 'dbStueck'
if files:
    regular_df, special_dataframes, monthly_dfs = load_data(files, special_column, monthly_column)
    
    
    # Sidebar
    st.sidebar.title("Auswertungen")
    menu = st.sidebar.radio("",
                                    ["Performance", "Benchmark", "Monatsbericht"])
    if menu == "Performance":
        st.subheader("Performance")

        if regular_df is not None:
                
            regular_df['ERFASST'] = pd.to_datetime(regular_df['ERFASST'], format='%d.%m.%Y %H:%M:%S', errors='coerce')
            min_date = regular_df['ERFASST'].min()
            max_date = regular_df['ERFASST'].max()

                
                
            # Liste der zu löschenden Zusatzinfos
            def remove_info(row, info_to_remove):
                infos = row.split()
                infos = [info for info in infos if info not in info_to_remove]
                return ' '.join(infos)

            # Infos, die entfernt werden sollen
            info_to_remove = ['NICHT_ZUGESTELLT',
                                    'AUFTRAG',
                                    'ZUSTELLUNG_NICHT_MOEGLICH',
                                    'FALSCHE_VERTEILART',
                                    'ABZUG'
                                    ]
                
                # Anwenden der Funktion auf die Spalte 'zusatzinfo'
            regular_df['ZUSATZINFO'] = regular_df['ZUSATZINFO'].apply(lambda x: remove_info(x, info_to_remove))
                
                # Aktualisiere die Filialzuordnung basierend auf PLZ-Bereichen
            df = apply_fixed_filiale(regular_df)

                # Layout für die Filter nebeneinander
            col1, col2, col3, col4, col5, col6 = st.columns(6)

            with col1:
                filiale_filter = sorted(df[df['FILIALE'].isin(['Fil01', 'Fil02', 'Fil03', 'Fil05', 
                                                             'Fil06', 'Fil07', 'Fil08', 'Fil09', 
                                                             'Fil10', 'Fil13', 'Fil15'])]['FILIALE'].unique())
                filiale_filter = st.multiselect("Filiale:", options=filiale_filter)
            with col2:
                    view_type = st.selectbox("Ansicht:", ["Filiale", "Gebietsbetreuer", "Zusteller"])
            with col3:
                    status_filter = st.selectbox("Status:", ["Alle", "Performance"])
            with col4:
                type_filter = st.multiselect('Type:', sorted(df['TYPE'].unique()))
            with col5:
                view_mode = st.selectbox("Werte:", ["Prozentual", "Numerisch"])
            with col6:
                start_date = st.date_input('Startdatum', value=max_date, min_value=min_date, max_value=max_date)
                end_date = st.date_input('Enddatum', value=max_date, min_value=min_date, max_value=max_date)

            if filiale_filter:
                df = df[df['FILIALE'].isin(filiale_filter)]

            # Filter auf das Datum anwenden
            df['ERFASST'] = df['ERFASST'].dt.date
            df = df[(df['ERFASST'] >= start_date) & (df['ERFASST'] <= end_date)]

            if type_filter:
                df = df[df['TYPE'].isin(type_filter)]

            # Vorbereitung der Daten basierend auf der Ansicht
            if view_type == "Filiale":
                group_by_field = 'FILIALE'
            elif view_type == "Gebietsbetreuer":
                df['combined_label'] = df['FILIALE'] + ' - ' + df['ERFASSER']
                group_by_field = 'combined_label'
            else:  # VT
                df['combined_label'] = df['FILIALE'] + ' - ' + df['NAME/VT/ABNEHMER']
                group_by_field = 'combined_label'

            if status_filter == "Performance":
                # Nur PERF. NICHT_OK für Performance
                df = df[df['KONTROLLE'].isin(['PERF. NICHT_OK', 'OK'])]
                    
            else:
                # PERF. NICHT_OK und NICHT_OK für Alle
                df = df[df['KONTROLLE'].isin(['PERF. NICHT_OK', 'NICHT_OK', 'OK'])]

            # Gruppierung ohne Zusatzinfo
            group_stats = df.groupby([group_by_field, 'KONTROLLE']).size().unstack(fill_value=0)

            # Berechne Gesamtzahl der Kontrollen
            total_controls = df.groupby(group_by_field)[group_by_field].count()

            # Prozentualer Modus für Kontrollen
            if view_mode == "Prozentual":
                for idx in group_stats.index:
                    total = total_controls[idx]
                    if total > 0:  # Verhindere Division durch Null
                        group_stats.loc[idx] = (group_stats.loc[idx] / total) * 100

            # Sortierung basierend auf Status Filter
            if status_filter == "Performance" and 'PERF. NICHT_OK' in group_stats.columns:
                # Sortiere absteigend nach PERF. NICHT_OK wenn Status = Performance
                group_stats = group_stats.sort_values(by='PERF. NICHT_OK', ascending=True)
            elif 'PERF. NICHT_OK' in group_stats.columns and 'NICHT_OK' in group_stats.columns:
                # Originale Sortierung für "Alle"
                sort_cols = ['PERF. NICHT_OK', 'NICHT_OK']
                group_stats = group_stats.sort_values(by=sort_cols, ascending=[True] * len(sort_cols))

            # Spaltenreihenfolge festlegen
            if 'PERF. NICHT_OK' in group_stats.columns:
                sorted_columns = ['PERF. NICHT_OK'] + [col for col in group_stats.columns if col != 'PERF. NICHT_OK']
                group_stats = group_stats[sorted_columns]

            # Vorbereitung für Plotly
            plot_data = group_stats.reset_index()

            # Farben definieren
            color_discrete_map = {
                'PERF. NICHT_OK': '#C63D2F',
                'NICHT_OK': 'darkorange',
                'OK': '#F3E2A9',
            }

            # Erstelle Zusammenfassungs-Plot
            summary_data = df.groupby('KONTROLLE')['KONTROLLE'].count().reset_index(name='count')
            total_sum = summary_data['count'].sum()
            
            if view_mode == "Prozentual":
                summary_data['count'] = (summary_data['count'] / total_sum * 100)

            kontrolle_order = ['PERF. NICHT_OK', 'NICHT_OK', 'OK']
            summary_data['order'] = summary_data['KONTROLLE'].apply(lambda x: kontrolle_order.index(x) if x in kontrolle_order else len(kontrolle_order))
            
            if len(filiale_filter) == 0:
                y_label = "Gesamt"
            else:
                y_label = "    ".join(filiale_filter)

            summary_fig = px.bar(
                summary_data,
                y=[y_label] * len(summary_data),
                x='count',
                color='KONTROLLE',
                orientation='h',
                title=f'Zusammenfassung {y_label} von {start_date} - {end_date}',
                color_discrete_map=color_discrete_map,
                category_orders={'KONTROLLE': kontrolle_order},
                labels={
                    'count': 'Prozent (%)' if view_mode == "Prozentual" else 'Anzahl',
                    'KONTROLLE': 'Kontrollergebnis'
                }
            )

            # Layout für Zusammenfassungs-Plot mit fixer Breite und Höhe
            summary_fig.update_layout(
                barmode='stack',
                plot_bgcolor='white',
                paper_bgcolor='white',
                font_color='darkorange',
                showlegend=False,
                xaxis_title='Prozent (%)' if view_mode == "Prozentual" else 'Anzahl',
                yaxis_title='',
                bargap=0.05,
                bargroupgap=0.02,
                height=200,  # Fixe Höhe
                width=1700,  # Fixe Breite
                margin=dict(l=60, r=150, t=40, b=40)  # Angepasste Margins
            )

            # Verbesserte Annotationen für Zusammenfassungs-Plot
            total_controls_summary = df[group_by_field].count()

                # Gesamtzahl der Kontrollen links vom Balken
            summary_fig.add_annotation(
                y=y_label,
                x=-3,
                text=f"Kontr.: {'{:,.0f}'.format(int(total_controls_summary)).replace(',', '.')}",
                showarrow=False,
                font=dict(color='black', size=13),
                xanchor='right',
                xshift=-5
            )

            # Sortiere die Daten entsprechend der vordefinierten Reihenfolge
            kontrolle_order = ['PERF. NICHT_OK', 'NICHT_OK', 'OK']
            sorted_summary_data = summary_data.sort_values(
                by='KONTROLLE',
                key=lambda x: pd.Categorical(x, categories=kontrolle_order, ordered=True)
            )

            # Berechne die kumulativen Positionen in der korrekten Reihenfolge
            cumulative_positions = {}
            current_position = 0
            
            for _, row in sorted_summary_data.iterrows():
                value = row['count']
                kontrolle = row['KONTROLLE']
                
                # Speichere die Mitte des aktuellen Balkens
                cumulative_positions[kontrolle] = current_position + (value / 2)
                current_position += value

            # Füge Annotationen in der sortierten Reihenfolge hinzu
            for kontrolle in kontrolle_order:
                if kontrolle in cumulative_positions:
                    value = sorted_summary_data[sorted_summary_data['KONTROLLE'] == kontrolle]['count'].iloc[0]
                    x_pos = cumulative_positions[kontrolle]
                    
                    if value > 0:
                        if view_mode == "Prozentual":
                            formatted_value = f"{value:.1f}%"
                        else:
                            formatted_value = f"{'{:,.0f}'.format(value).replace(',', '.')}"
                        
                        summary_fig.add_annotation(
                            y=y_label,
                            x=x_pos,
                            text=formatted_value,
                            showarrow=False,
                            font=dict(color='black', size=13),
                            xanchor='center',
                            yanchor='middle'
                        )
            # Zeige Zusammenfassungs-Plot
            st.plotly_chart(summary_fig, use_container_width=False)

            st.markdown("---")

            # Daten für den Plot vorbereiten
            melted_data = pd.melt(
                plot_data,
                id_vars=[group_by_field],
                value_vars=[col for col in plot_data.columns if col != group_by_field],
                var_name='category',  
                value_name='value'    
            )

            # Füge die Farbkategorie hinzu
            melted_data['color_category'] = melted_data['category']
            
            # Erstelle den Hauptplot
            fig = px.bar(
                melted_data,
                y=group_by_field,
                x='value',
                color='color_category',
                title=f'Verteilung der Kontrollergebnisse pro {view_type} von {start_date} - {end_date}',
                labels={
                    'value': 'Prozent (%)' if view_mode == "Prozentual" else 'Anzahl',
                    'color_category': 'Kontrollergebnis',
                    group_by_field: view_type
                },
                height=max(600, len(group_stats) * 30),
                orientation='h',
                color_discrete_map=color_discrete_map,
                barmode='relative'
            )

            # Layout aktualisieren mit fixer Breite
            fig.update_layout(
                barmode='stack',
                plot_bgcolor='white',
                paper_bgcolor='white',
                font_color='darkorange',
                showlegend=True,
                legend_title_text='Kontrollergebnis',
                xaxis_title='Prozent (%)' if view_mode == "Prozentual" else 'Anzahl',
                yaxis_title=view_type,
                bargap=0.2,
                bargroupgap=0.1,
                width=1500,  # Fixe Breite für das Hauptdiagramm
                margin=dict(l=0, r=0, t=22, b=0),
            )

            # Annotationen für Hauptplot
            for idx in group_stats.index:
                # Gesamtzahl der Kontrollen links vom Balken
                fig.add_annotation(
                    y=idx,
                    x=-2,
                    text=f"Kontr.: {'{:,.0f}'.format(int(total_controls[idx])).replace(',', '.')}",
                    showarrow=False,
                    font=dict(color='black', size=13),
                    xanchor='right',
                    xshift=-5 
                )

                # Werte auf den Balken
                cumulative_x = 0
                for col in group_stats.columns:
                    value = group_stats.loc[idx, col]
                    if value > 0:
                        if view_mode == "Prozentual":
                            formatted_value = f"{value:.1f}%"
                        else:
                            formatted_value = f"{'{:,.0f}'.format(value).replace(',', '.')}"
                        
                        fig.add_annotation(
                            y=idx,
                            x=cumulative_x + (value/2),
                            text=formatted_value,
                            showarrow=False,
                            font=dict(color='black', size=13),
                            xanchor='center'
                        )
                    cumulative_x += value


            # For the DataFrame display
            def format_numbers(x):
                if isinstance(x, (int, float)):
                    if isinstance(x, int) or x.is_integer():
                        return '{:,.0f}'.format(x).replace(',', '.')
                return x

            # Explodiere die Zusatzinfo-Spalte
            df = df.assign(ZUSATZINFO=df['ZUSATZINFO'].str.split()).explode('ZUSATZINFO')

            # Gruppiere die Daten nach ZUSATZINFO und TYPE und berechne die Anzahl
            grouped_df = df.groupby(['ZUSATZINFO', 'TYPE']).size().reset_index(name='COUNT')

            # Erstelle eine Pivot-Tabelle
            pivot_df = grouped_df.pivot(index='ZUSATZINFO', columns='TYPE', values='COUNT').fillna(0)

            # Berechne die Gesamtanzahl basierend auf dem "Werte:"-Filter
            pivot_df['Gesamt'] = pivot_df.sum(axis=1)

            
            
            if status_filter=='Performance':
                    pivot_df = pivot_df[pivot_df.index.isin(PERFORMANCE_ZUSATZINFOS)]

            pivot_df = pivot_df.sort_values(by='Gesamt', ascending=False)
            # Setze den Index zurück, damit ZUSATZINFO eine Spalte wird
            pivot_df = pivot_df.reset_index()

            
            # Funktion zum Färben der Zellen in der ZUSATZINFO-Spalte
            def color_zusatzinfo(val):
                if val in VERTEILER_ZUSATZINFOS:
                    border_color = "rgb(255, 25, 0)"
                    background_color = "rgba(198, 62, 47, 0.5)"  # Weniger transparentes Rot
                elif val in INCLUDE_ZUSATZINFOS:
                    border_color = "rgb(255, 128, 0)"
                    background_color = "rgba(255, 128, 0, 0.5)"  # Weniger transparentes Orange
                else:
                    border_color = "rgb(255, 196, 0)"
                    background_color = "rgba(243, 226, 169, 0.64)"  # Weniger transparentes Gelb
                return f'border: 2px solid {border_color}; background-color: {background_color}'
            
            
            
            col1, col2 = st.columns([2.5, 2])
            with col1:
                st.plotly_chart(fig, use_container_width=False)
            with col2:
                if view_type != "Filiale":
                    # Erstelle eine Liste der Optionen aus dem group_by_field
                    filter_options = list(plot_data[group_by_field].unique())
                    filter_options.reverse()
                    filter_options.insert(0, '')
                    dataframe_filter = st.selectbox(f"Zusatzinfos filtern nach {view_type}:", options=filter_options)

                    # Filtere das DataFrame basierend auf der Auswahl und dem view_type
                    if dataframe_filter:
                        filtered_df = df.copy()  # Create a copy of the original dataframe
                        if view_type == "Gebietsbetreuer":
                            # Extrahiere den ERFASSER-Teil aus combined_label
                            erfasser = dataframe_filter.split(' - ')[1]
                            filtered_df = filtered_df[filtered_df['ERFASSER'] == erfasser]
                        else:  # Zusteller
                            # Extrahiere den NAME/VT/ABNEHMER-Teil aus combined_label
                            vt_name = dataframe_filter.split(' - ')[1]
                            filtered_df = filtered_df[filtered_df['NAME/VT/ABNEHMER'] == vt_name]

                        # Explodiere die Zusatzinfo-Spalte für das gefilterte DataFrame
                        filtered_df = filtered_df.assign(ZUSATZINFO=filtered_df['ZUSATZINFO'].str.split()).explode('ZUSATZINFO')
                        
                        # Gruppiere die gefilterten Daten
                        grouped_filtered = filtered_df.groupby(['ZUSATZINFO', 'TYPE']).size().reset_index(name='COUNT')
                        
                        # Erstelle die Pivot-Tabelle für die gefilterten Daten
                        filtered_pivot = grouped_filtered.pivot(index='ZUSATZINFO', columns='TYPE', values='COUNT').fillna(0)
                        filtered_pivot = filtered_pivot.reset_index()
                        
                        # Berechne die Gesamtanzahl
                        if 'Gesamt' not in filtered_pivot.columns:
                            numeric_cols = filtered_pivot.select_dtypes(include=['int64', 'float64']).columns
                            filtered_pivot['Gesamt'] = filtered_pivot[numeric_cols].sum(axis=1)
                        
                        if status_filter == 'Performance':
                            filtered_pivot = filtered_pivot[filtered_pivot['ZUSATZINFO'].isin(PERFORMANCE_ZUSATZINFOS)]
                        
                        filtered_pivot = filtered_pivot.sort_values(by='Gesamt', ascending=False)
                    else:
                        filtered_pivot = pivot_df
                else:
                    filtered_pivot = pivot_df

                # Formatierung der Pivot-Tabelle
                styled_pivot_df = filtered_pivot.style.map(color_zusatzinfo, subset=['ZUSATZINFO'])
                styled_pivot_df = styled_pivot_df.format(precision=0)

                if view_mode == "Prozentual":
                    filtered_pivot['Gesamt'] = (filtered_pivot['Gesamt'] / filtered_pivot['Gesamt'].sum()) * 100
                    filtered_pivot['Gesamt'] = filtered_pivot['Gesamt'].map(lambda x: f"{x:.2f}%")
                    numeric_columns = filtered_pivot.select_dtypes(include=['int64', 'float64']).columns
                    filtered_pivot[numeric_columns] = filtered_pivot[numeric_columns].applymap(format_numbers)
                else:
                    numeric_columns = filtered_pivot.select_dtypes(include=['int64', 'float64']).columns
                    filtered_pivot[numeric_columns] = filtered_pivot[numeric_columns].applymap(format_numbers)

                st.dataframe(styled_pivot_df, 
                            height=500,
                            use_container_width=True)
    
    elif menu == "Benchmark":
        st.subheader("Benchmark")

        if special_dataframes is not None:

             

            names_to_remove = ['BEHABETZ THOMAS', 'JARNIG JOACHIM', 'Dujkovic David', 'TRAUM SIMON', 'KROKER THOMAS']

            fixed_branches  = {
                    'Fil01' : ['AKRAP Ivica', 'FRATRIK Anton', 'JURACKA MIROSLAV', 'KUBES PAVEL', 'NAGY ZSOLT', 'ÖZTÜRK TOLGA', 'PALAGIC SORIN-MIRCEA', 'VIASZ-KADI IMRE'],

                    'Fil02' : ['HINTERWALLNER PATRICK', 'IZER PETER', 'KLARIC SASA', 'Lastro Marko', 'MORAR Catalin', 'SALA STANISLAV'],
                    
                    'Fil03' : ['AMBRUS DOREL', 'BATISTA ', 'DANIHEL Norbert', 'GHOTRA GURVINDER SINGH', 'LAPOSA MIKLOS', 'MAYER ', 'RISTIC ', 'TOTH ', 'VIRAG ADAM'] ,

                    'Fil05' : ['ADAMOVIC LUBOMIR', 'KAJDIC Muhamed', 'KRUK Maciej', 'LOBODAS MAREK', 'Lubinski Stanislaw', 'PETRANEK IVAN', 'RACZ LASZLO BALINT'] ,

                    'Fil06' : ['MÜLLNER MARIO', 'PAYR FLORIAN', 'Vergeiner Fabian'],

                    'Fil07' : ['HABERL GERALD', 'JOZSA ROLAND', 'SEBÖK ROBERT', 'STAUDINGER FRIEDRICH'] ,

                    'Fil08' : ['Klavik Kurt', 'LIPKA ZOLTAN', 'NIEFERGALL GERALD', 'Saibl Klaus', 'SCHÖPF OTMAR', 'STEIDL ANDREAS', 'Weidinger Christian'] ,

                    'Fil09' : ['DUSEK Petr', 'HUMER Sven Sebastian', 'IVANIC Roman', 'KOBIDA ROMAN', 'NAIRZ MICHAEL', 'PODMAJERSKY Viktor', 'REICH Roland', 
                    'SIMKO RADEK', 'VYBOH Jaroslav', 'WEIDINGER THOMAS', 'WINKLER Christian', 'ZSAKOVICS Adrian'] ,
                    
                    'Fil10' : ['BOGAR ADAM', 'GALAVITS PATRIK', 'KÄFFER Dietmar', 'Neger Helmut', 'VIDA ÁDÁM'] ,

                    'Fil13' : ['GAZICA Ivica', 'KARL ELISABETH', 'KLAMBAUER Erwin', 'KONDOR', 'REBEKIC Vlatko', 'SZUPPIN Bianca', 'VARGA ARPAD'] ,

                    'Fil15' : ['PICHLER Maximilian', 'RISTIC Sretko', 'ZICKBAUER Gerald', 'BAYER SIEGFRIED']  
                    }

            target_values  = {

                444 : ['BAYER SIEGFRIED', 'KLAMBAUER Erwin', 'SCHÖPF OTMAR'],

                518 : ['KARL Elisabeth'],

                777 : ['SZUPPIN Bianca'],

                806 : ['PODMAJERSKY Viktor'],

                884 : ['IVANIC Roman'],

                995 : ['DUSEK Petr'],

                997 : ['PAYR FLORIAN', 'Vergeiner Fabian'],

                1036 : ['HINTERWALLNER PATRICK', 'KAJDIC Muhamed', 'Neger Helmut', 'ÖZTÜRK TOLGA', 
                'RISTIC ', 'STAUDINGER FRIEDRICH', 'STEIDL ANDREAS', 'WINKLER Christian',],

                1106 : ['ADAMOVIC LUBOMIR', 'AKRAP Ivica', 'AMBRUS DOREL', 'BATISTA ', 'BOGAR ADAM', 'FRATRIK Anton', 'GALAVITS PATRIK',
                'GAZICA Ivica', 'GHOTRA GURVINDER SINGH', 'HUMER Sven Sebastian', 'IZER PETER', 'JOZSA ROLAND', 'JURACKA MIROSLAV', 'KÄFFER Dietmar',
                'Klavik Kurt', 'KOBIDA ROMAN', 'KRUK Maciej', 'KUBES PAVEL', 'LAPOSA MIKLOS', 'Lastro Marko', 'LIPKA ZOLTAN', 
                'LOBODAS MAREK', 'Lubinski Stanislaw', 'MAYER ', 'MORAR Catalin', 'MÜLLNER MARIO', 'NAGY ZSOLT', 'NAIRZ MICHAEL',
                'NIEFERGALL GERALD', 'PALAGIC SORIN-MIRCEA', 'PETRANEK IVAN', 'PICHLER Maximilian', 'RACZ LASZLO BALINT', 'REBEKIC Vlatko', 
                'RISTIC Sretko', 'Saibl Klaus', 'SALA STANISLAV', 'SEBÖK ROBERT', 'SIMKO RADEK', 'VARGA ARPAD', 'VIASZ-KADI IMRE',
                'VIDA ÁDÁM', 'VYBOH Jaroslav', 'Weidinger Christian', 'WEIDINGER THOMAS', 'ZICKBAUER Gerald', 'ZSAKOVICS Adrian',],
                }
            

            info_gb = {
                'Gebietsbetreuer' : ['ADAMOVIC LUBOMIR', 'AKRAP Ivica', 'AMBRUS DOREL', 'BATISTA ', 'BOGAR ADAM', 'FRATRIK Anton', 'GALAVITS PATRIK',
                'GAZICA Ivica', 'GHOTRA GURVINDER SINGH', 'HUMER Sven Sebastian', 'IZER PETER', 'JOZSA ROLAND', 'JURACKA MIROSLAV', 'KÄFFER Dietmar',
                'Klavik Kurt', 'KOBIDA ROMAN', 'KRUK Maciej', 'KUBES PAVEL', 'LAPOSA MIKLOS', 'Lastro Marko', 'LIPKA ZOLTAN', 
                'LOBODAS MAREK', 'Lubinski Stanislaw', 'MAYER ', 'MORAR Catalin', 'MÜLLNER MARIO', 'NAGY ZSOLT', 'NAIRZ MICHAEL',
                    'NIEFERGALL GERALD', 'PALAGIC SORIN-MIRCEA', 'PETRANEK IVAN', 'PICHLER Maximilian', 'RACZ LASZLO BALINT', 'REBEKIC Vlatko', 
                'RISTIC Sretko', 'Saibl Klaus', 'SALA STANISLAV', 'SEBÖK ROBERT', 'SIMKO RADEK', 'VARGA ARPAD', 'VIASZ-KADI IMRE',
                'VIDA ÁDÁM', 'VYBOH Jaroslav', 'Weidinger Christian', 'WEIDINGER THOMAS', 'ZICKBAUER Gerald', 'ZSAKOVICS Adrian', 'KARL Elisabeth', 'SZUPPIN Bianca',
                'PODMAJERSKY Viktor', 'IVANIC Roman', 'DUSEK Petr', 'PAYR FLORIAN', 'Vergeiner Fabian'],

                'Filialleiter' : ['HINTERWALLNER PATRICK', 'KAJDIC Muhamed', 'Neger Helmut', 'ÖZTÜRK TOLGA', 
                'RISTIC ', 'STAUDINGER FRIEDRICH', 'STEIDL ANDREAS', 'WINKLER Christian', 'Vergeiner Fabian'],

                'Regionalleiter' : ['BAYER SIEGFRIED', 'KLAMBAUER Erwin', 'SCHÖPF OTMAR'],
                }
            
            data = process_data(special_dataframes, fixed_branches, target_values, names_to_remove)

            col1, col2 = st.columns(2)
            with col1:
                filial_filter = sorted(data[data['FILIALE'].isin(['Fil01', 'Fil02', 'Fil03', 'Fil05', 
                                                                'Fil06', 'Fil07', 'Fil08', 'Fil09', 
                                                                'Fil10', 'Fil13', 'Fil15'])]['FILIALE'].unique())
                selected_branches = st.multiselect("Filiale:", options=filial_filter)
                if selected_branches:
                    data = data[data['FILIALE'].isin(selected_branches)]
            with col2:
                value_filter = st.selectbox('Werte:', ['Numerisch', 'Prozentual'])

            # die Chartdaten
            chart_data = data.groupby('FILIALE')[['IST', 'DIFF', 'SOLL WERT']].sum().reset_index()
            chart_data['DIFF'] = chart_data['DIFF'].abs().round(0)

            chart_data['100%'] = 100

            # Berechnung der prozentualen Abweichung
            chart_data['DIFF_prozent'] = (chart_data['DIFF'] / chart_data['SOLL WERT']) * 100
            
            # Berechnung der beiden Balken
            chart_data['Abweichung'] = chart_data['DIFF_prozent']
            chart_data['Basis'] = chart_data.apply(
                lambda row: 100 - row['DIFF_prozent'] if row['IST'] < row['SOLL WERT'] else 100,
                axis=1
            ).round(1)
            chart_data['Basis'] = chart_data['Basis'].apply(lambda x: f"{x}%").round(1)
            
            chart_data['Zusatz'] = chart_data.apply(
                lambda row: row['DIFF_prozent'],
                axis=1
            )
            # Gesamtübersicht erstellen
            overview_data = data.groupby('FILIALE').agg({
                'IST': 'sum',
                'SOLL WERT': 'sum',
                'DIFF': lambda x: abs(sum(x))
            }).reset_index()

            # Berechnung für das Gesamtdiagramm
            total_ist = overview_data['IST'].sum()
            total_soll = overview_data['SOLL WERT'].sum()
            total_diff = abs(total_ist - total_soll)

            overview_chart_data = pd.DataFrame({
                'FILIALE': ['Gesamt'],
                'IST': [total_ist],
                'SOLL WERT': [total_soll],
                'DIFF': [total_diff]
            })

            overview_chart_data['DIFF_prozent'] = (overview_chart_data['DIFF'] / overview_chart_data['SOLL WERT']) * 100
            overview_chart_data['Abweichung'] = overview_chart_data['DIFF_prozent']
            overview_chart_data['100%'] = 100

            # Berechnung der Basis für das Gesamtdiagramm
            overview_chart_data['Basis'] = overview_chart_data.apply(
                lambda row: 100 - row['DIFF_prozent'] if row['IST'] < row['SOLL WERT'] else 100,
                axis=1
            ).round(1)
            overview_chart_data['Basis'] = overview_chart_data['Basis'].apply(lambda x: f"{x}%")

            overview_chart_data['Zusatz'] = overview_chart_data['DIFF_prozent']

            # Gesamtübersicht Figure erstellen
            overview_fig = go.Figure()

            if value_filter == 'Prozentual':
                overview_chart_data['label'] = ((overview_chart_data['IST'] - overview_chart_data['SOLL WERT']) / overview_chart_data['SOLL WERT'] * 100).round(1)
                overview_chart_data['label'] = overview_chart_data['label'].apply(lambda x: f"{'+' if x > 0 else ''}{x}%")
                
                overview_chart_data['y_labels'] = overview_chart_data.apply(
                    lambda row: f"{row['FILIALE']} - Soll: {row['SOLL WERT']:,.0f}".replace(',', '.'),
                    axis=1
                )
                
                # Basis-Balken für Gesamtübersicht
                overview_basis_bar = go.Bar(
                    x=overview_chart_data['Basis'],
                    y=overview_chart_data['y_labels'],
                    name='Basis',
                    orientation='h',
                    showlegend=False,
                    marker_color=overview_chart_data.apply(
                        lambda row: '#2E8B09' if row['IST'] > row['SOLL WERT'] else '#D20103',
                        axis=1,
                    ),
                    text=overview_chart_data.apply(
                        lambda row: row['Basis'] if row['IST'] < row['SOLL WERT'] else '',
                        axis=1
                    ),
                    textposition='auto',
                    textfont=dict(
                        color='white',
                        size=15
                    )
                )
                
                # Zusatz-Balken für Gesamtübersicht
                overview_zusatz_bar = go.Bar(
                    x=overview_chart_data['Zusatz'],
                    y=overview_chart_data['y_labels'],
                    name='Zusatz',
                    orientation='h',
                    showlegend=False,
                    marker_color=overview_chart_data.apply(
                        lambda row: '#9CD884' if row['IST'] >= row['SOLL WERT'] else '#E49D9D',
                        axis=1
                    ),
                    text=overview_chart_data.apply(
                        lambda row: row['label'],
                        axis=1
                    ),
                    textposition='outside',
                    textfont=dict(
                        color=overview_chart_data.apply(
                            lambda row: 'red' if row['IST'] <= row['SOLL WERT'] else 'green',
                            axis=1,
                        ),
                        size=15,
                    ),
                    cliponaxis=True
                )
                
                overview_fig.add_trace(overview_basis_bar)
                overview_fig.add_trace(overview_zusatz_bar)
                
            else:
                overview_chart_data['IST_bereinigt'] = overview_chart_data.apply(
                    lambda row: row['IST'] - row['DIFF'] if row['IST'] > row['SOLL WERT'] else row['IST'],
                    axis=1
                )
                
                overview_chart_data['y_labels'] = overview_chart_data.apply(
                    lambda row: f"{row['FILIALE']} - Soll: {row['SOLL WERT']:,.0f}".replace(',', '.'),
                    axis=1
                )
                
                # IST-Balken für Gesamtübersicht
                overview_ist_bar = go.Bar(
                    x=overview_chart_data['IST_bereinigt'],
                    y=overview_chart_data['y_labels'],
                    name='IST',
                    orientation='h',
                    showlegend=False,
                    marker_color=overview_chart_data.apply(
                        lambda row: '#2E8B09' if row['IST'] > row['SOLL WERT'] else '#D20103',
                        axis=1
                    ),
                    text=overview_chart_data.apply(
                        lambda row: '{:,.0f}'.format(row['IST']).replace(',', '.') if row['IST'] < row['SOLL WERT'] else '',
                        axis=1
                    ),
                    textposition='auto',
                    textfont=dict(
                        color='white',
                        size=15
                    )
                )
                
                # DIFF-Balken für Gesamtübersicht
                overview_diff_bar = go.Bar(
                    x=overview_chart_data['DIFF'],
                    y=overview_chart_data['y_labels'],
                    name='SOLL',
                    orientation='h',
                    showlegend=False,
                    marker_color=overview_chart_data.apply(
                        lambda row: '#9CD884' if row['IST'] >= row['SOLL WERT'] else '#E49D9D',
                        axis=1
                    ),
                    text=overview_chart_data.apply(
                        lambda row: f"{int(row['IST']):,}   (+ <span style='color:green'>{int(row['DIFF']):,}</span> Abw.)" if row['IST'] >= row['SOLL WERT'] else f"- <span style='color:red'>{int(row['DIFF']):,}</span> Abw.",
                        axis=1
                    ),
                    textposition='outside',
                    textfont=dict(
                        color=overview_chart_data.apply(
                            lambda row: 'black' if row['IST'] >= row['SOLL WERT'] else 'red',
                            axis=1,
                        ),
                        size=15
                    ),
                    cliponaxis=False
                )
                
                overview_fig.add_trace(overview_ist_bar)
                overview_fig.add_trace(overview_diff_bar)
                
                # Vertikale Linie für SOLL WERT
                for idx, row in overview_chart_data.iterrows():
                    overview_fig.add_shape(
                        type='line',
                        x0=row['SOLL WERT'],
                        x1=row['SOLL WERT'],
                        y0=idx-0.4,
                        y1=idx+0.4,
                        line=dict(
                            color='red',
                            width=2,
                            dash='dash'
                        )
                    )

            # Layout für Gesamtübersicht
            overview_fig.update_layout(
                barmode='stack',
                yaxis_tickangle=0,
                title='Benchmark Gesamt',
                xaxis_title='Kontrollen',
                yaxis_title='Gesamt',
                height=250,
                width=1400,
                margin=dict(
                    l=0,
                    r=150,
                    t=70,
                    b=25
                ),
                xaxis=dict(
                    automargin=True,
                ),
                yaxis=dict(
                    automargin=True
                )
            )

            # Horizontale Linie bei 100% für prozentuale Ansicht
            if value_filter == 'Prozentual':
                overview_fig.add_shape(
                    type='line',
                    x0=100,
                    x1=100,
                    y0=-0.5,
                    y1=len(overview_chart_data['FILIALE'])-0.5,
                    line=dict(
                        color='red',
                        width=2,
                        dash='dash'
                    )
                )

            # Anzeigen der Gesamtübersicht
            st.plotly_chart(overview_fig, use_container_width=False)


            st.markdown('---')

            fig = go.Figure()

            if value_filter == 'Prozentual':
                chart_data['label'] = ((chart_data['IST'] - chart_data['SOLL WERT']) / chart_data['SOLL WERT'] * 100).round(1)
                chart_data['label'] = chart_data['label'].apply(lambda x: f"{'+' if x > 0 else ''}{x}%")

                chart_data['y_labels'] = chart_data.apply(
                    lambda row: f"{row['FILIALE']} - Soll: {row['SOLL WERT']:,.0f}".replace(',', '.'),
                    axis=1
                )
                # Basis-Balken (100% oder weniger)
                basis_bar = go.Bar(
                    x=chart_data['Basis'],
                    y=chart_data['y_labels'],
                    name='Basis',
                    orientation='h',
                    showlegend=False,
                    marker_color=chart_data.apply(
                        lambda row: '#2E8B09' if row['IST'] > row['SOLL WERT'] else '#D20103',
                        axis=1,
                    ),
                    # Text nur anzeigen, wenn IST < SOLL WERT
                    text=chart_data.apply(
                        lambda row: row['Basis'] if row['IST'] < row['SOLL WERT'] else '',
                        axis=1
                    ),
                    textposition='auto',
                    textfont=dict(
                        color='white',
                        size=15
                    )
                )
                
                # Zusatz-Balken (nur bei positiver Abweichung)
                zusatz_bar = go.Bar(
                    x=chart_data['Zusatz'],
                    y=chart_data['y_labels'],
                    name='Zusatz',
                    orientation='h',
                    showlegend=False,
                    marker_color=chart_data.apply(
                        lambda row: '#9CD884' if row['IST'] >= row['SOLL WERT'] else '#E49D9D',
                        axis=1
                    ),
                    text=chart_data.apply(
                        lambda row: row['label'] if row['IST'] >= row['SOLL WERT'] else row['label'],
                        axis=1
                    ),
                    textposition='outside',
                    textfont=dict(
                        color=chart_data.apply(
                        lambda row: 'red' if row['IST'] <= row['SOLL WERT'] else 'green',
                        axis=1,
                        ),
                        size=15,
                    ),
                    cliponaxis=True
                )
                
                fig.add_trace(basis_bar)
                fig.add_trace(zusatz_bar)

                fig.update_layout(
                    barmode='stack',
                    yaxis_tickangle=0,
                    title='Benchmark Visualisierung',
                    xaxis_title='Kontrollen',
                    yaxis_title='Filiale',
                    height=600,
                    width=1200,  
                    margin=dict(
                        l=0,  
                        r=50,  
                        t=70,  
                        b=25   
                    ),
                    xaxis=dict(
                        automargin=True,
                        
                    ),
                    yaxis=dict(
                        automargin=True
                    )
                )


                # Fügen Sie eine horizontale Linie bei 100% hinzu
                fig.add_shape(
                    type='line',
                    x0=100,
                    x1=100,
                    y0=-0.5,
                    y1=len(chart_data['FILIALE'])-0.5,
                    line=dict(
                        color='red',
                        width=2,
                        dash='dash'
                    )
                )

                col1, col2 = st.columns([2.5,2])
                with col1:
                    st.plotly_chart(fig, use_container_width=False)
                with col2:
                    
                    
                    table_display = data[['FILIALE', 'ERFASSER', 'IST', 'SOLL WERT']].copy()
                    
                    # Berechne %Änderung
                    table_display['%Änderung'] = ((table_display['IST'] - table_display['SOLL WERT']) / table_display['SOLL WERT'] * 100).round(1)
                    table_display['%Änderung'] = table_display['%Änderung'].apply(lambda x: f"{'+' if x > 0 else ''}{x}%")
                    
                    
                    
                    table_display['⌀Kontrollen'] = (data['IST'] / 16).round(0)
                    
                    # Formatiere die numerischen Spalten
                    table_display['IST'] = table_display['IST'].round(0).apply(lambda x: '{:,.0f}'.format(x).replace(',', '.'))
                    table_display['SOLL WERT'] = table_display['SOLL WERT'].round(0).apply(lambda x: '{:,.0f}'.format(x).replace(',', '.'))

                    def filter_data(table_filter, excluded_names):
                        if table_filter == 'RL&FL':
                            filtered = table_display[table_display['ERFASSER'].isin(info_gb['Filialleiter'] + info_gb['Regionalleiter'])]
                            filtered = filtered.sort_values(by='⌀Kontrollen', ascending=False)
                        elif table_filter == 'Top 10':
                            # Filtere erst die Gebietsbetreuer und schließe dann die ausgewählten Namen aus
                            filtered = table_display[
                                (table_display['ERFASSER'].isin(info_gb['Gebietsbetreuer'])) & 
                                (~table_display['ERFASSER'].isin(excluded_names)) & 
                                (data['SOLL WERT'] != 0)
                            ]
                            filtered = filtered.nlargest(10, '⌀Kontrollen')
                        elif table_filter == 'Low 10':
                            # Filtere erst die Gebietsbetreuer und schließe dann die ausgewählten Namen aus
                            filtered = table_display[
                                (table_display['ERFASSER'].isin(info_gb['Gebietsbetreuer'])) & 
                                (~table_display['ERFASSER'].isin(excluded_names)) & 
                                (data['SOLL WERT'] != 0)
                            ]
                            filtered = filtered.nsmallest(10, '⌀Kontrollen')
                        else:
                            filtered = table_display
                        
                        # Index zurücksetzen
                        filtered = filtered.reset_index(drop=True)
                        return filtered

                    # Erstelle zwei Spalten für die Filter
                    col1, col2 = st.columns(2)

                    with col1:
                        table_filter = st.selectbox(
                            'Tabellen Filter:', 
                            ['Alle', 'RL&FL', 'Top 10', 'Low 10'],
                            key='value_filter_key'  # Eindeutiger Key hinzugefügt
                        )

                    with col2:
                        # Hole alle Namen aus der ERFASSER Spalte
                        all_names = sorted(table_display['ERFASSER'].unique())
                        excluded_names = st.multiselect(
                            'Namen ausschließen (für Top/Low 10):', 
                            options=all_names,
                            help='Diese Namen werden bei Top 10 und Low 10 nicht berücksichtigt'
                        )

                    # Gefilterte Daten basierend auf der Auswahl
                    table_display = filter_data(table_filter, excluded_names)

                     # Berechne die Höhe basierend auf der Anzahl der Zeilen
                    row_height = 35
                    max_height = 500 
                    num_rows = len(table_display)
                    table_height = min(row_height * (num_rows + 1), max_height)

                    # Zeige die Tabelle an
                    st.dataframe(table_display, use_container_width=True, height=table_height)
                
            else:
                chart_data['IST_bereinigt'] = chart_data.apply(
                    lambda row: row['IST'] - row['DIFF'] if row['IST'] > row['SOLL WERT'] else row['IST'],
                    axis=1
                )
                chart_data['y_labels'] = chart_data.apply(
                    lambda row: f"{row['FILIALE']} - Soll: {row['SOLL WERT']:,.0f}".replace(',', '.'),
                    axis=1
                )
                # numerische Darstellung bleibt unverändert
                ist_bar = go.Bar(
                    x=chart_data['IST_bereinigt'],
                    y=chart_data['y_labels'],
                    name='IST',
                    orientation='h',
                    showlegend=False,
                    marker_color=chart_data.apply(
                        lambda row: '#2E8B09' if row['IST'] > row['SOLL WERT'] else '#D20103',
                        axis=1
                    ),
                    text=chart_data.apply(
                        lambda row: '{:,.0f}'.format(row['IST']).replace(',', '.') if row['IST'] < row['SOLL WERT'] else '',
                        axis=1
                    ),
                    textposition='auto',
                    textfont=dict(
                        color='white',
                        size=15
                    )
                )
                
                diff_bar = go.Bar(
                    x=chart_data['DIFF'],
                    y=chart_data['y_labels'],
                    name='SOLL',
                    orientation='h',
                    showlegend=False,
                    marker_color=chart_data.apply(
                        lambda row: '#9CD884' if row['IST'] >= row['SOLL WERT'] else '#E49D9D',
                        axis=1
                    ),
                    text=chart_data.apply(
                        lambda row: f"{int(row['IST']):,}   (+ <span style='color:green'>{int(row['DIFF']):,}</span> Abw.)" if row['IST'] >= row['SOLL WERT'] else f"- <span style='color:red'>{int(row['DIFF']):,}</span> Abw.",
                        axis=1
                    ),
                    textposition='outside',
                    textfont=dict(
                        color=chart_data.apply(
                            lambda row: 'black' if row['IST'] >= row['SOLL WERT'] else 'red',
                            axis=1,  
                        ),
                        size=15
                    ),
                    cliponaxis=False
                )
                
                fig.add_trace(ist_bar)
                fig.add_trace(diff_bar)
                

                for idx, row in chart_data.iterrows():
                    fig.add_shape(
                        type='line',
                        x0=row['SOLL WERT'],
                        x1=row['SOLL WERT'],
                        y0=idx-0.4,
                        y1=idx+0.4,
                        line=dict(
                            color='red',
                            width=2,
                            dash='dash'
                        )
                    )
                    
                    
                fig.update_layout(
                    barmode='stack',
                    yaxis_tickangle=0,
                    title='Benchmark Visualisierung',
                    xaxis_title='Kontrollen',
                    yaxis_title='Filiale',
                    height=600,
                    width=1400,
                    margin=dict(
                        l=0,  # linker Rand
                        r=200,  # rechter Rand
                        t=70,  # oberer Rand
                        b=50   # unterer Rand
                    ),
                    xaxis=dict(
                        automargin=True,
                        
                    ),
                    yaxis=dict(
                        automargin=True
                    )
                )
                                
                
                col1, col2 = st.columns([2.5,1.6])
                with col1:
                    st.plotly_chart(fig, use_container_width=False)
                with col2:
                    
                    table_display = data[['FILIALE', 'ERFASSER', 'IST', 'SOLL WERT']].copy()
                    table_display['%Änderung'] = ((table_display['IST'] - table_display['SOLL WERT']) / table_display['SOLL WERT'] * 100).round(1)
                    table_display['%Änderung'] = table_display['%Änderung'].apply(lambda x: f"{'+' if x > 0 else ''}{x}%")
                    
                    table_display['⌀Kontrollen'] = (data['IST'] / 16).round(0)
                    
                    table_display['IST'] = table_display['IST'].round(1).apply(lambda x: '{:,.0f}'.format(x).replace(',', '.'))
                    table_display['SOLL WERT'] = table_display['SOLL WERT'].round(1).apply(lambda x: '{:,.0f}'.format(x).replace(',', '.'))

                    def filter_data(table_filter, excluded_names):
                        if table_filter == 'RL&FL':
                            filtered = table_display[table_display['ERFASSER'].isin(info_gb['Filialleiter'] + info_gb['Regionalleiter'])]
                            filtered = filtered.sort_values(by='⌀Kontrollen', ascending=False)
                        elif table_filter == 'Top 10':
                            filtered = table_display[
                                (table_display['ERFASSER'].isin(info_gb['Gebietsbetreuer'])) & 
                                (~table_display['ERFASSER'].isin(excluded_names)) & 
                                (data['SOLL WERT'] != 0)
                            ]
                            filtered = filtered.nlargest(10, '⌀Kontrollen')
                        elif table_filter == 'Low 10':
                            filtered = table_display[
                                (table_display['ERFASSER'].isin(info_gb['Gebietsbetreuer'])) & 
                                (~table_display['ERFASSER'].isin(excluded_names)) & 
                                (data['SOLL WERT'] != 0)
                            ]
                            filtered = filtered.nsmallest(10, '⌀Kontrollen')
                        else:
                            filtered = table_display
                        
                        filtered = filtered.reset_index(drop=True)
                        return filtered

                    # zwei Spalten für die Filter
                    col1, col2 = st.columns(2)

                    with col1:
                        table_filter = st.selectbox(
                            'Tabellen Filter:', 
                            ['Alle', 'RL&FL', 'Top 10', 'Low 10'],
                            key='table_filter_key'
                        )

                    with col2:
                        all_names = sorted(table_display['ERFASSER'].unique())
                        excluded_names = st.multiselect(
                            'Namen ausschließen (für Top/Low 10):', 
                            options=all_names,
                            help='Diese Namen werden bei Top 10 und Low 10 nicht berücksichtigt',
                            key='excluded_names_key'
                        )

                    # Gefilterte Daten
                    table_display_filtered = filter_data(table_filter, excluded_names)

                    # Berechne die Höhe basierend auf der Anzahl der Zeilen
                    row_height = 35
                    max_height = 500
                    num_rows = len(table_display_filtered)
                    table_height = min(row_height * (num_rows + 1), max_height)

                    # Zeige die Tabelle an
                    st.dataframe(table_display_filtered, use_container_width=True, height=table_height)

                    def export_rl_fl_data(data):
                        """
                        Exports the data for Regionalleiter and Filialleiter to an Excel file.
                        
                        Parameters:
                        data (pandas.DataFrame): The original data DataFrame.
                        """
                        filtered_df = data[data['ERFASSER'].isin(info_gb['Filialleiter'] + info_gb['Regionalleiter'])]
                        
                        # Spalte "100%" löschen
                        filtered_df = filtered_df.drop('100%', axis=1)
                        
                        excel_data = convert_df_to_excel(filtered_df)
                        prev_month = (datetime.now() - timedelta(days=30)).strftime("%m%Y")
                        st.download_button(
                            label="Rohdaten RL&FL",
                            data=excel_data,
                            file_name=f'Filialbenchmark_RL_FL_{prev_month}.xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            key='download_button_rl_fl'
                        )

                    def export_complete_data(data):
                        """
                        Exports the complete, unfiltered data to an Excel file.
                        
                        Parameters:
                        data (pandas.DataFrame): The original data DataFrame.
                        """
                        # Spalte "100%" löschen
                        data = data.drop('100%', axis=1)
                        
                        excel_data = convert_df_to_excel(data)
                        prev_month = (datetime.now() - timedelta(days=30)).strftime("%m%Y")
                        st.download_button(
                            label="Rohdaten Export",
                            data=excel_data,
                            file_name=f'Filialbenchmark_{prev_month}.xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            key='download_button_complete'
                        )

                    def convert_df_to_excel(df):
                        """
                        Converts a DataFrame to an Excel file in-memory.
                        
                        Parameters:
                        df (pandas.DataFrame): The DataFrame to be exported.
                        
                        Returns:
                        bytes: The Excel file data in bytes.
                        """
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df.to_excel(writer, sheet_name='Rohdaten', index=False)
                            
                            # Automatische Spaltenbreiten-Anpassung
                            worksheet = writer.sheets['Rohdaten']
                            for idx, col in enumerate(df.columns):
                                series = df[col]
                                max_len = max(
                                    series.astype(str).map(len).max(),  # Länge der Daten
                                    len(str(series.name))  # Länge der Überschrift
                                ) + 1  # extra Platz
                                worksheet.set_column(idx, idx, max_len)
                        
                        processed_data = output.getvalue()
                        return processed_data

                    # Annahme: 'data' ist das ursprüngliche DataFrame
                    col1, col2 = st.columns(2)

                    with col1:
                        export_rl_fl_data(data)

                    with col2:
                        export_complete_data(data)

    elif menu=="Monatsbericht":
        st.header("Monatsbericht")

        st.markdown("---")

        

        if monthly_dfs is not None:

            # Zugriff auf die einzelnen DataFrames
            abzüge_df = monthly_dfs['AUSZAHLBEMERKUNG']
            verteilung_df = monthly_dfs['STUECK']
            sondercodes_df = monthly_dfs['ZUSATZAUFWAND']
            transporte_df = monthly_dfs['Kostenstelle']
            spitze_df = monthly_dfs['dbStueck']


            col1, col2 = st.columns(2)
            with col2:
                if abzüge_df:
                    for i, df in enumerate(abzüge_df):
                        st.subheader("Abzüge:")

                        pivot_table_abzug = df.pivot_table(index='FILIALNAME',values=['ABZUG', 'AUSZAHLBEMERKUNG'], aggfunc={'ABZUG': 'sum', 'AUSZAHLBEMERKUNG' : 'count'}).reset_index()

                        st.write(pivot_table_abzug)
                
                
            with col1:
                def convert_df_to_excel(filtered_df, pivot_table_all):
                    """
                    Converts a DataFrame and a pivot table DataFrame to a multi-sheet Excel file with a pivot table.
                    
                    Parameters:
                    filtered_df (pandas.DataFrame): The main DataFrame to be exported.
                    pivot_table_all (pandas.DataFrame): The pivot table DataFrame to be exported.
                    
                    Returns:
                    bytes: The Excel file as a byte stream.
                    """
                    # Create a new Excel file in memory
                    excel_bytes = BytesIO()
                    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
                        # Write the main DataFrame to the first sheet
                        filtered_df.to_excel(writer, sheet_name='Sondercodes', index=False)
                        
                        # Create the pivot table on the second sheet
                        worksheet = writer.sheets['Sondercodes']
                        pivot_table = worksheet.add_pivot_table('A1', pivot_table_all)
                        pivot_table.add_field('FILIALENR', pivot_field_type='row')
                        pivot_table.add_field('ZUSATZAUFWAND', pivot_field_type='data', function='sum')
                        
                        # Save the Excel file
                        writer.save()
                        
                    # Return the Excel file as a byte stream
                    return excel_bytes
                
                def add_excel_export(sondercodes_df):
                    if sondercodes_df:
                        for i, df in enumerate(sondercodes_df):
                            st.subheader("Sondercodes:")

                            filtered_df = df[~df['SONDERTYP'].between(700,799)]

                            filtered_df['DATE'] = pd.to_datetime(df[['JAHR', 'MONAT']].assign(TAGE=1).rename(columns={'JAHR': 'year', 'MONAT': 'month', 'TAGE': 'day'}))

                            # Keep the most recent entries based on the date
                            max_date = filtered_df['DATE'].max()
                            filtered_df = filtered_df[filtered_df['DATE'] == max_date]

                            # Drop the DATE column
                            filtered_df = filtered_df.drop(columns=['DATE'])

                            # Create the pivot table
                            pivot_table_all = filtered_df.pivot_table(index='FILIALENR', values='ZUSATZAUFWAND', aggfunc='sum').reset_index()

                            # Add the Excel export button
                            
                            st.download_button(
                                label="Download Excel file",
                                data=excel_file,
                                file_name="sondercodes_data.xlsx",
                                mime="application/vnd.ms-excel"
                            )

                            if st.download_button(f"Export Sondercodes to Excel (Sheet 1: Data, Sheet 2: Pivot Table)"):
                                excel_file = convert_df_to_excel(filtered_df, pivot_table_all)

                        # Pivot-Tabelle für FILIALENR 1-15 erstellen
                        pivot_table_uad = filtered_df[filtered_df['FILIALENR'].between(1, 15)].pivot_table(index='FILIALENR', values='ZUSATZAUFWAND', aggfunc='sum').reset_index()

                        # Pivot-Tabelle für FILIALENR 51-65 erstellen
                        pivot_table_adr = filtered_df[filtered_df['FILIALENR'].between(51, 65)].pivot_table(index='FILIALENR', values='ZUSATZAUFWAND', aggfunc='sum').reset_index()

                        # Funktion zum Umbenennen der FILIALENR
                        def rename_filialenr(filialenr):
                            if filialenr <= 15:
                                return f"Fil{filialenr:02d}"
                            elif 51 <= filialenr <= 65:
                                return f"Fil{(filialenr - 50):02d}"
                            else:
                                return f"Fil{filialenr:02d}"

                        # Umbenennen der FILIALENR in den Pivot-Tabellen
                        pivot_table_uad['FILIALENR'] = pivot_table_uad['FILIALENR'].apply(rename_filialenr)
                        pivot_table_adr['FILIALENR'] = pivot_table_adr['FILIALENR'].apply(rename_filialenr)

                        pivot_table_uad['ZUSATZAUFWAND'] = pivot_table_uad['ZUSATZAUFWAND'].apply(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                        pivot_table_adr['ZUSATZAUFWAND'] = pivot_table_adr['ZUSATZAUFWAND'].apply(lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))


                        col1, col2 = st.columns(2)

                        with col1:
                            st.write("Unadressiert:")
                            st.write(pivot_table_uad)
                        with col2:
                            st.write("Adressiert:")
                            st.write(pivot_table_adr)

            if verteilung_df:
                for i, df in enumerate(verteilung_df):
                    st.write(f"Verteilung {i+1}:")
                    st.write(df)
            if transporte_df:
                for i, df in enumerate(transporte_df):
                    st.write(f"Transporte {i+1}:")
                    st.write(df)

            if spitze_df:
                for i, df in enumerate(spitze_df):
                    st.write(f"Spitze {i+1}:")


                    st.write(df)

            
           

      




        
else:                    
    st.info("Bitte lade eine XLSX hoch, um zu beginnen.")
