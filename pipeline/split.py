# pipeline/split.py

def split_submission(context):

    print("3.✂️ Split")

    df = context["clean"]

    # TODO: logique réelle plus tard
    context["patients"] = df
    context["answers"] = df
    context["comments"] = df

    return context