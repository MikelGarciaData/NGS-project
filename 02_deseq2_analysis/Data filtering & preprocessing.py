# Data filtering & preprocessing
import pandas as pd

df = pd.read_csv("metadata_full.csv", sep=";")
df = df[["sample_accession", "alias", "run_accession", "experiment_accession"]].copy()
df["alias"] = df["alias"].str.replace("non_ssoil", "non-soil")
df[["_", "code", "codeID"]] = df["alias"].str.split("_", expand=True)
df["part1"] = df["code"].str[:2]
df["part2"] = df["code"].str[2:]
print(df["part1"].value_counts())
print(df["part2"].value_counts())
print(df["code"].value_counts())
print(df["codeID"].value_counts())
df.to_csv("process_metadata_full.csv", index=False)
print(df)

