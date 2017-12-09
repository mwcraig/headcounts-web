import datetime
import os
import logging
import sys

import numpy as np
from flask import Flask, render_template, request, send_from_directory
from astropy.table import Table, Column

from flask.ext.bootstrap import Bootstrap

app = Flask(__name__)

bootstrap = Bootstrap(app)

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

table = Table.read('all_enrollments.csv', format='ascii.csv')

avg_time = int(table['timestamp'].mean())
timestamp = datetime.datetime.fromtimestamp(avg_time)

CACHE_DIR = 'viewed-csvs'
COURSE_DETAIL_URL = 'https://webproc.mnscu.edu/registration/search/detail.html?campusid=072&courseid={course_id}&yrtr={year_term}&rcid=0072&localrcid=0072&partnered=false&parent=search'

try:
    os.mkdir(CACHE_DIR)
except OSError:
    pass


def parse_year_term(year_term_str):
    """
    Given a year/term code as a string return a human-readable
    year and term.
    """
    if year_term_str[-1] == '1':
        year_term = year_term_str[:-1]
        year_term = int(year_term)
        year_term = year_term - 1
        year_term_2 = 'Summer'
    elif year_term_str[-1] == '3':
        year_term = year_term_str[:-1]
        year_term = int(year_term)
        year_term = year_term - 1
        year_term_2 = 'Fall'
    elif year_term_str[-1] == '5':
        year_term = year_term_str[:-1]
        year_term_2 = 'Spring'
    else:
        year_term = 'Unknown'
        year_term_2 = 'Unknown'
    return ' '.join((year_term_2, str(year_term)))


# Compute and add a human-readable year-term column
human_yrtr = [parse_year_term(str(yrtr)) for yrtr in table['year_term']]
human_yrtr = Column(data=human_yrtr, name='Term')
table.add_column(human_yrtr, index=0)


def filled_credits(credit_column, variable_credits=1):
    vari_rows = credit_column == 'Vari.'
    crds = credit_column.copy()
    crds.mask[vari_rows] = True
    crds.fill_value = variable_credits
    crds = np.round(crds.filled().astype(np.float)).astype(np.int)
    return crds


def calc_sch(table, vari_credits=1):
    """
    Calculate total student credit hours generated by courses in this table.
    """
    crds = filled_credits(table['Crds'], variable_credits=vari_credits)
    sch = (table['Enrolled'] * crds).sum()
    return sch


def calc_seats(table):
    """
    Calculate the number of seats that are available, filled, empty, for
    classes that are not canceled.
    """
    not_canceled = table['Status'] != 'Cancelled'
    empty = table['Size:'] - table['Enrolled']
    positive = empty > 0
    empty *= positive
    empty = empty[not_canceled].sum()
    available = table['Size:'][not_canceled].sum()
    filled = table['Enrolled'][not_canceled].sum()
    return {'empty': empty, 'filled': filled, 'available': available}


def calc_tuition(table, variable_credits=1):
    """
    Calculate the tuition revenue generated by the courses in the
    table.
    """
    by_credit = table['Tuition unit'] == 'credit'
    credits = filled_credits(table['Crds'],
                             variable_credits=variable_credits)
    tuition_nas = table['Tuition -resident'] == 'n/a'
    table['Tuition -resident'].mask |= tuition_nas
    # parse tuition as a string into a number
    money = [float(m.replace('$', '').replace(',', '')) for m in table['Tuition -resident'].filled(fill_value='0')]
    money *= table['Enrolled']
    money[by_credit] *= credits[by_credit]
    return money.sum()


def gen_cache_file(path, table):
    """
    Generate a name for a cache of a view of the data based on
    the URL path to the view
    """
    # path always starts with a leading /, remove it
    rel_path = path[1:]
    parts = rel_path.split('/')
    parts.extend([str(avg_time)])
    name = '-'.join(parts) + '.csv'
    file_path = os.path.join(CACHE_DIR, name)
    if not os.path.isfile(file_path):
        table.write(file_path)
    return name


def match_subject(subject, tbl):
    if subject == 'lasc':
        render_me = tbl[~tbl['LASC/WI'].mask]
        really_lasc = np.array([len(lasc.strip('WI')) > 0 for lasc in render_me['LASC/WI']])
        render_me = render_me[really_lasc]
    elif subject == 'wi':
        render_me = tbl[~tbl['LASC/WI'].mask]
        really_wi = np.array(['WI' in lasc for lasc in render_me['LASC/WI']])
        render_me = render_me[really_wi]
    elif subject == '18online':
        keep = tbl['18online'] == 'True'
        render_me = tbl[keep]
    elif subject == 'all':
        render_me = tbl.copy()
    else:
        # Regular academic subject...
        keep = tbl['Subj'] == subject.upper()
        render_me = tbl[keep]
    return render_me


def common_response(render_me, path):
    """
    Most of what we are returning is the same for all views,
    we just have a bunch of routes for getting there.

    Parameters
    ----------

    render_me : astropy Table
        The table to be rendered in the view.

    path : str
        The URL path that got the user here.
    """
    terms = sorted(set(render_me['year_term']))
    year_terms = ', '.join([parse_year_term(str(t)) for t in terms])
    file_name = gen_cache_file(path, render_me)
    return render_template('course_info.html', table=render_me,
                           timestamp=timestamp,
                           year_term=year_terms,
                           sch=calc_sch(render_me),
                           filename=file_name,
                           seats=calc_seats(render_me),
                           revenue=calc_tuition(render_me),
                           base_detail_url=COURSE_DETAIL_URL)


@app.route('/')
def index():
    return render_template('instructions.html', )


@app.route('/<subject>')
@app.route('/<subject>/<spec1>')
@app.route('/<subject>/<spec1>/<spec2>')
def subtable_spec(subject, spec1=None, spec2=None):
    if subject == 'favicon.ico':
        return ''
    render_me = match_subject(subject, table)
    specs = [spec1, spec2]
    specs = [s for s in specs if s is not None]
    if not specs and subject != 'all':
        terms = sorted(set(render_me['year_term']))
        most_recent = terms[-1]
        keep = render_me['year_term'] == most_recent
        render_me = render_me[keep]
    else:
        for spec in specs:
            if spec != 'all':
                if len(spec) == 5 and spec[-1] in ['1', '3', '5']:
                    # spec probably a year/term, filter by it
                    keep = render_me['year_term'] == int(spec)
                else:
                    # Assume it was a course number or LASC area
                    if subject == 'lasc':
                        keep = np.array([spec in l for l in render_me['LASC/WI']])
                    else:
                        keep = render_me['#'] == str(spec)

                render_me = render_me[keep]

    return common_response(render_me, request.path)


@app.route('/download/<filename>')
def download(filename):
    # https://stackoverflow.com/questions/34009980/return-a-download-and-rendered-page-in-one-flask-response
    return send_from_directory(CACHE_DIR, filename)


if __name__ == '__main__':
    app.run(debug=True)
