import pandas as pd


df = pd.read_pickle("df_housing_features.pickle")
df_new_list = []
for index, row in df.iterrows():
    new_row = {}
    for k, v in row.items():
        if k == "neighborhood_features":
            new_row[k] = ", ".join(v)
        else:
            new_row[k] = v
    df_new_list.append(new_row)
df = pd.DataFrame(df_new_list)
print(df.head())

df.to_csv("housing_features.csv", sep="\t", encoding="utf-8")
