# Prints the Kaggle API error BODY instead of just the status line.
import sys, os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
import kaggle
from kaggle.rest import ApiException
api = kaggle.KaggleApi(kaggle.ApiClient())
api.authenticate()
try:
    r = api.competition_submit(sys.argv[1], sys.argv[2], "gemma-4-developer-agent")
    print("OK:", r)
except ApiException as e:
    print("STATUS:", e.status)
    print("BODY:", e.body)
except Exception as e:
    print("TYPE:", type(e).__name__)
    print("REPR:", repr(e)[:2000])
    for attr in ("body", "response", "text"):
        v = getattr(e, attr, None)
        if v: print(attr.upper() + ":", str(v)[:2000])
