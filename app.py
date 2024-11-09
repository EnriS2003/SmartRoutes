from flask import Flask, render_template
import pandas as pd


output_df = pd.read_csv('resources/trasporti_ottimizzati.csv')




app = Flask(__name__)


@app.route('/')
def display_output():
    # Convert DataFrame to HTML table format for easy rendering
    table_html = output_df.to_html(classes='table table-striped', index=False)
    return render_template('map.jinja2', table_html=table_html)


if __name__ == "__main__":
    app.run(debug=True)
