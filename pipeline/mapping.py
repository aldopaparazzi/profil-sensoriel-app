# pipeline/mapping.py

def map_questions(context):

    print("4.🧠 Mapping")

    df = context["answers"]

    # TODO: merge avec reference CSV
    context["mapped"] = df

    return context