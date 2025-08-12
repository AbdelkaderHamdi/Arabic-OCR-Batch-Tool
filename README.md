# 📖 Arabic OCR Batch Tool – Powered by Mistral AI

### **Description**

Cet outil Python extrait automatiquement le texte arabe de fichiers PDF scannés, tout en conservant la mise en page. Il utilise **Mistral OCR** pour une précision optimale et un traitement rapide, même sur des documents volumineux.

### **Fonctionnalités principales**

* 📂 Traitement par lot : convertit tous les PDFs d’un dossier
* 🖋 Reconnaissance précise du texte arabe et de la structure
* 📝 Sortie au format Markdown, prêt à convertir en Word
* ♻️ Reprise automatique après une interruption
* 📊 Journalisation complète des erreurs et réussites

### **Installation**

```bash
git clone https://github.com/AbdelkaderHamdi/Arabic-OCR-Batch-Tool.git
cd <Arabic-OCR-Batch-Tool >
pip install -r requirements.txt
```

Créer un fichier `.env` :

```env
MISTRAL_API_KEY="votre_cle_api"
```

### **Utilisation**

1. Placer vos PDFs dans le dossier `doc/`
2. Lancer :

```bash
python BatchPdfConv.py
```

```bash
streamlit run streamlit_app.py
```

3. Les résultats sont générés en `.md`


