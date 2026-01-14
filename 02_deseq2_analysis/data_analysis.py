import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. Leer el CSV full ---
csv_file = "metadata_full.csv"
df = pd.read_csv(csv_file)

# --- 2. Filtrar variables categóricas que tengan más de un valor único ---
categorical_cols = ['library_strategy', 'library_layout', 'instrument_model', 'scientific_name',
                    'project_name', 'local_environmental_context', 'environmental_medium']

# Mantener solo columnas con más de 1 valor único
categorical_cols = [col for col in categorical_cols if col in df.columns and df[col].nunique() > 1]

print(f"Columnas categóricas con más de un valor único: {categorical_cols}")

# --- 3. Conteo de reads/archivos fastq ---
df['num_fastq_files'] = df[['fastq_1', 'fastq_2']].notnull().sum(axis=1)
print("\nResumen de archivos fastq por run:")
print(df[['run_accession', 'num_fastq_files']])

# --- 4. Gráficos de barras solo para variables categóricas válidas ---
for col in categorical_cols:
    plt.figure(figsize=(8,4))
    sns.countplot(data=df, x=col, order=df[col].value_counts().index)
    plt.title(f'Conteo por {col}')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

# --- 5. Imprimir conteos ---
print("\nConteos de categorías:")
for col in categorical_cols:
    print(f"\n{col}:")
    print(df[col].value_counts())

