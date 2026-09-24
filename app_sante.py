import folium
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Tableau de Bord Santé Publique",
    page_icon="🏥",
    layout="wide",
)

st.title("🏥 Tableau de Bord d'Analyse Épidémiologique Avancé")
st.markdown(
    "Plateforme de suivi d'incidence, de létalité et de répartition spatiale."
)

# Coordonnées GPS des 13 régions du Burkina Faso
COORDONNEES_BURKINA = {
    "Centre": [12.3714, -1.5197],
    "Hauts-Bassins": [11.1772, -4.2979],
    "Centre-Ouest": [12.2526, -2.3627],
    "Boucle du Mouhoun": [12.4632, -3.4607],
    "Cascades": [10.6333, -4.7500],
    "Plateau-Central": [12.5833, -1.3000],
    "Centre-Nord": [13.0917, -1.0833],
    "Centre-Sud": [11.6631, -1.0731],
    "Nord": [13.5833, -2.4167],
    "Centre-Est": [11.7800, -0.3700],
    "Est": [12.0616, 0.3582],
    "Sud-Ouest": [10.3300, -3.1800],
    "Sahel": [14.0333, -0.0333],
}

# -----------------------------------------------------------------------------
# 1. Barre latérale : Choix de la source de données
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Source des Données")
source_donnees = st.sidebar.radio(
    "Sélectionnez le mode d'alimentation :",
    ["Données Web (COVID-19)", "Importer un fichier local (CSV/Excel)"],
)

df = None

if source_donnees == "Importer un fichier local (CSV/Excel)":
  fichier_uploade = st.sidebar.file_uploader(
      "Téléverser votre registre de santé", type=["csv", "xlsx"]
  )
  if fichier_uploade is not None:
    try:
      if fichier_uploade.name.endswith(".csv"):
        df = pd.read_csv(fichier_uploade)
      else:
        df = pd.read_excel(fichier_uploade)
      st.sidebar.success("Fichier chargé avec succès !")
    except Exception as e:
      st.sidebar.error(f"Erreur lors de la lecture du fichier : {e}")
  else:
    st.info(
        "Veuillez importer un fichier CSV ou Excel dans le menu latéral pour"
        " commencer."
    )
else:
  url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"

  @st.cache_data
  def charger_donnees_web():
    return pd.read_csv(url)

  df = charger_donnees_web()

# -----------------------------------------------------------------------------
# 2. Traitement et Affichage des Données
# -----------------------------------------------------------------------------
if df is not None:
  if source_donnees == "Données Web (COVID-19)":
    pays_selectionne = st.sidebar.selectbox(
        "Sélectionnez un pays :",
        ["Burkina Faso", "Senegal", "Cote d'Ivoire", "Mali", "France"],
    )

    df_pays = df[df["Country/Region"] == pays_selectionne]
    cas_cumules = df_pays.iloc[:, 4:].sum(axis=0)
    cas_cumules.index = pd.to_datetime(cas_cumules.index, format="%m/%d/%y")

    nouveaux_cas = cas_cumules.diff().fillna(0)
    moyenne_7j = nouveaux_cas.rolling(window=7).mean()

    total_cas = int(cas_cumules.iloc[-1])
    nouveaux_cas_dernier_jour = int(nouveaux_cas.iloc[-1])
    taux_croissance = (
        (nouveaux_cas_dernier_jour / total_cas) * 100 if total_cas > 0 else 0
    )

    st.subheader(f"📊 Indicateurs Clés - {pays_selectionne}")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Cumul Total des Cas", f"{total_cas:,}")
    kpi2.metric("Nouveaux Cas (Dernier Jour)", f"{nouveaux_cas_dernier_jour:,}")
    kpi3.metric(
        "Taux de Croissance Quotidien", f"{taux_croissance:.2f}%"
    )

    st.subheader("📈 Courbe d'Incidence & Lissage Épidémiologique")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(
        nouveaux_cas.index,
        nouveaux_cas.values,
        color="lightblue",
        alpha=0.5,
        label="Nouveaux cas / jour",
    )
    ax.plot(
        moyenne_7j.index,
        moyenne_7j.values,
        color="crimson",
        linewidth=2,
        label="Moyenne mobile (7j)",
    )
    ax.set_ylabel("Nombre de cas")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()
    st.pyplot(fig)

    st.subheader("🗺️ Carte de Surveillance des Foyers Sanitaires")
    carte = folium.Map(location=[12.2383, -1.5616], zoom_start=6)
    folium.CircleMarker(
        location=[12.2383, -1.5616],
        radius=12,
        color="crimson",
        fill=True,
        popup="Burkina Faso",
    ).add_to(carte)
    st_folium(carte, width=900, height=450)

  else:
    # Mode Fichier Local (Dengue, Registres, etc.)
    st.subheader("📋 Aperçu de vos Données Importées")
    st.dataframe(df)

    st.subheader("📈 Visualisation par Région")
    colonnes_numeriques = df.select_dtypes(include=["number"]).columns.tolist()

    col_y = None
    if colonnes_numeriques:
      col_y = st.selectbox(
          "Choisissez l'indicateur à analyser sur la carte et le graphique :",
          colonnes_numeriques,
      )

      # Graphique à barres par région
      fig, ax = plt.subplots(figsize=(10, 4))
      if "Region" in df.columns:
        ax.bar(df["Region"], df[col_y], color="teal", alpha=0.85)
        plt.xticks(rotation=45, ha="right")
      else:
        ax.plot(df[col_y], color="teal", linewidth=2)
      ax.set_ylabel(col_y)
      ax.grid(True, linestyle="--", alpha=0.5)
      st.pyplot(fig)

    # Carte interactive dynamique basée sur les régions
    st.subheader("🗺️ Carte Régionale Dynamique de la Dengue")
    carte = folium.Map(location=[12.2383, -1.5616], zoom_start=6)

    if "Region" in df.columns and col_y:
      valeur_max = df[col_y].max() if df[col_y].max() > 0 else 1
      for _, ligne in df.iterrows():
        nom_region = ligne["Region"]
        valeur = ligne[col_y]

        if nom_region in COORDONNEES_BURKINA:
          coords = COORDONNEES_BURKINA[nom_region]
          # Calcul d'un rayon proportionnel (entre 6 et 35 pixels)
          rayon = max(6, min(35, (valeur / valeur_max) * 35))

          popup_html = f"""
                    <div style="font-family: Arial; font-size: 12px;">
                        <b>Région :</b> {nom_region}<br>
                        <b>{col_y} :</b> {valeur:,}
                    </div>
                    """

          folium.CircleMarker(
              location=coords,
              radius=rayon,
              popup=folium.Popup(popup_html, max_width=200),
              color="crimson",
              fill=True,
              fill_color="crimson",
              fill_opacity=0.6,
          ).add_to(carte)

    st_folium(carte, width=900, height=450)
