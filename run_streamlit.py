import os
import sys

# Configurar para evitar el prompt de email
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

# Ejecutar Streamlit
os.system('streamlit run Fruits_Vegetable_Classification.py --server.headless true')
