import os
import datetime

import numpy as np

from flask import Flask, render_template
from astropy.table import Table

from flask.ext.bootstrap import Bootstrap

app = Flask(__name__)
bootstrap = Bootstrap(app)

table = Table.read('all_enrollments.csv', format='ascii.csv')

avg_time = int(table['timestamp'].mean())
timestamp = datetime.datetime.fromtimestamp(avg_time)
year_term = str(table['year_term'][0])
year_term_2 = '0'

if year_term[-1] == '3':
    year_term = year_term[:-1]
    year_term = int(year_term)
    year_term = year_term - 1
    year_term_2 = 'Fall'
else:
    year_term = year_term[:-1]
    year_term_2 = 'Spring'


# We are done with the timestamp column, so nuke it
table.remove_column('timestamp')

@app.route('/')
def index():
    return render_template('instructions.html')


@app.route('/all')
def user():
    return render_template('course_info.html', table=table,
                           timestamp=timestamp)


@app.route('/<subject>')
def subtable(subject):
    keep = table['Subj'] == subject.upper()
    render_me = table[keep]
    return render_template('course_info.html', table=render_me,
                           timestamp=timestamp, year_term=year_term, year_term_2=year_term_2)

if __name__ == '__main__':
    app.run(debug=True)
