import os
import datetime

import numpy as np

from flask import Flask, render_template
from astropy.table import Table, Column

app = Flask(__name__)

table = Table([Column(data=[i % 2 for i in range(10)], name='One'),
               Column(data=range(10), name='Two')])

table = Table.read('all_enrollments.csv', format='ascii.csv')

timestamp = datetime.datetime.fromtimestamp(os.path.getmtime('all_enrollments.csv'))


@app.route('/')
def index():
    return '<h1>Hello world</h1>'


@app.route('/all')
def user():
    return render_template('course_info.html', table=table,
                           timestamp=timestamp)


@app.route('/<subject>')
def subtable(subject):
    keep = table['Subj'] == subject.upper()
    render_me = table[keep]
    return render_template('course_info.html', table=render_me,
                           timestamp=timestamp)

if __name__ == '__main__':
    app.run(debug=True)
