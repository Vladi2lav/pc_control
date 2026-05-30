import sys
import os
sys.path.append(os.path.dirname(__file__))
from form_ff.form_ff import MainForm

if __name__ == '__main__':
    app = MainForm()
    app.run()
