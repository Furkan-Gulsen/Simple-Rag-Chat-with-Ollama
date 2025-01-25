import streamlit.web.cli as stcli
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.argv = [
        "streamlit",
        "run",
        str(Path(__file__).parent / "src" / "frontend" / "streamlit_app.py"),
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ]
    sys.exit(stcli.main())
