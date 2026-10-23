import os
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(GOC, "server"))
sys.path.insert(0, os.path.join(GOC, "device"))
os.environ.setdefault("JWT_SECRET", "bi-mat-kiem-thu-dai-toi-thieu-32-byte!")
