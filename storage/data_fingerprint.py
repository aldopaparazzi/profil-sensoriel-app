import hashlib
import pandas as pd

def dataframe_hash(df: pd.DataFrame) -> str:
    """
    Génère une empreinte stable du contenu du DataFrame.
    """
    # normalisation pour éviter faux positifs
    df_normalized = df.copy()
    df_normalized = df_normalized.fillna("NULL")
    df_normalized = df_normalized.astype(str)

    content = df_normalized.to_csv(index=False)

    return hashlib.md5(content.encode("utf-8")).hexdigest()