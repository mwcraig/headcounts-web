from astropy.table import Table, join, vstack, Column


def add_index_col(table):
    """
    Given a table, construct a column for indexing then create the
    index.

    No return value, all the action is the changes made to table.
    """
    index_data = [str(yrtr) + str(id) for yrtr, id in
                  zip(table['year_term'], table['ID #'])]
    table.add_column(Column(index_data, name='index'))
    table.add_index('index')


def main(new_data_file):
    current_data = Table.read('all_enrollments.csv', format='ascii.csv')

    new_data = Table.read(new_data_file, format='ascii.csv')
    add_index_col(new_data)
    add_index_col(current_data)

    # Switch things up a bit, maybe. Do an outer join that includes all
    # of the new data.

    # Include everything and the new data and the matching rows of the
    # current data set.
    data_match = join(new_data, current_data,
                      keys='index', join_type='left')

    # Identify updates

    common_entries = ~ data_match['year_term_2'].mask
    # Deal with any updates first, then append everything else (which
    # may actually be everything)

    common_data = data_match[common_entries]

    data_to_append = data_match[~common_entries]

    if common_data:
        # Check that ALL new data is present in old data
        # if len(new_data) != len(common_data):
        #     raise RuntimeError('Shit be whack!')
        # Ugh. There is no great way to update this...
        # Well, working is better than not working, so here we go.
        for idx in common_data['index']:
            current_loc = current_data.loc[idx].index
            current_data[current_loc] = new_data.loc[idx]
        result = current_data

    if 'Cr/Hr' in new_data.colnames:
        new_data.rename_column('Cr/Hr', 'Crds')

    if data_to_append:
        # locs = [new_data.loc[idx] for idx in ]
        result = vstack([current_data, new_data.loc[data_to_append['index']]],
                        join_type='exact')

    # Clean up after ourselves...
    result.remove_column('index')
    result.write('all_enrollments.csv', format='ascii.csv', overwrite=True)
    return result


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('new_data', help='New data in csv format')
    args = parser.parse_args()
    print(main(args.new_data))
