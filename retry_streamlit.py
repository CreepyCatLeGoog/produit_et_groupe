import streamlit as st
import pandas as pd
import os
import tempfile
from lxml import etree
from retry_cleaned import (
    traiter_produit,
    traiter_attribut_produit,
    charger_produit_associe,
    charger_groupe_option,
    charger_lien_produit_option,
    charger_groupe_option_definition,
    export_stepxml,
    build_step_groupe_option_file,
    charger_rattachement
)
import retry_cleaned
print(retry_cleaned.__file__)

st.set_page_config(page_title="Générateur STEPXML", layout="wide")
st.title("🔧 Générateur de fichiers STEPXML UGAP")

st.markdown("""
Chargez ici tous vos fichiers CSV nécessaires :
- `produit_...csv`
- `attribut_produit_...csv`
- `produit_associe_...csv`
- `produit_groupe_option_...csv`
- `groupe_option.csv`
- `FICHIER_DE_RATTACHEMENT_5_MARCHCES.xlsx`
""")

uploaded_files = st.file_uploader(
    "📁 Déposez tous les fichiers ici (CTRL + clic pour en sélectionner plusieurs)",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

if uploaded_files:
    with tempfile.TemporaryDirectory() as tmpdir:
        st.info("📦 Traitement des fichiers en cours...")

        # Sauvegarde locale des fichiers
        filenames = []
        for uploaded_file in uploaded_files:
            path = os.path.join(tmpdir, uploaded_file.name)
            with open(path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            filenames.append(uploaded_file.name)
        try:
            # Chargement des fichiers nécessaires
            df_produit, base_name = traiter_produit(folder=tmpdir, return_df=True)
            df_attribut = traiter_attribut_produit(folder=tmpdir, return_df=True)
            df_associe = charger_produit_associe(folder=tmpdir)
            df_groupe_option, base_name = charger_groupe_option(folder=tmpdir)
            #st.write("df_groupe_option type:", type(df_groupe_option))
            # 🔍 DEBUG : Afficher les colonnes disponibles
            #st.write("🔍 Colonnes de df_groupe_option :", df_groupe_option.columns.tolist())

            if "Reference" not in df_groupe_option.columns:
                raise ValueError("❌ La colonne 'Reference' est manquante dans le fichier groupe_option")

            df_lien_produit_option, lien_base_name = charger_lien_produit_option(folder=tmpdir)
            df_groupes_option_definitions, groupe_base_name = charger_groupe_option_definition(folder=tmpdir)

            rattachement_dict = charger_rattachement(
                path=os.path.join(tmpdir, "FICHIER_DE_RATTACHEMENT_5_MARCHCES.xlsx")
            )

            # Génération des XML
            xml_path = export_stepxml(
                df_produit,
                df_attribut,
                base_name,
                df_associe,
                df_groupe_option,
                output_dir=tmpdir
            )

            build_step_groupe_option_file(
                df_lien_produit_option,
                df_groupes_option_definitions,
                rattachement_dict,
                groupe_base_name,
                output_dir=tmpdir
            )

            st.success("✅ Fichiers XML générés avec succès !")

            # Bouton de téléchargement - produit.xml
            with open(xml_path, "rb") as f:
                st.download_button(
                    "📥 Télécharger produit.xml",
                    f,
                    file_name=os.path.basename(xml_path)
                )

            # Bouton de téléchargement - groupe_option.xml
            groupe_option_path = os.path.join(tmpdir, f"{groupe_base_name}.xml")
            if os.path.exists(groupe_option_path):
                with open(groupe_option_path, "rb") as f:
                    st.download_button(
                        "📥 Télécharger groupe_option.xml",
                        f,
                        file_name=os.path.basename(groupe_option_path)
                    )
            else:
                st.warning("⚠️ Le fichier groupe_option.xml n’a pas été généré.")

        except Exception as e:
            st.error(f"❌ Une erreur est survenue : {e}")
