#!/usr/bin/env python

import re
import sys
import argparse


def main():
    if sys.argv[1:] == []:
        sys.argv.append('-h')
    args = parse_commandline()
    strips = {}
    for i, strip in enumerate(args.pipatterns):
        strips[strip] = {'intercept': args.intercepts[i],
                         'fr_width': args.fr_width[i]}
    with open(args.outpeptable, 'w') as fp:
        for outline in annotate_peptable(args.pipeps, args.peptable,
                                         args.pepcol, args.frac_col,
                                         args.stripcol, strips,
                                         args.ignoremods):
            fp.write('\t'.join([str(x) for x in outline]))
            fp.write('\n')


def get_first_matching_pattern(patterns, string):
    for pattern in patterns:
        if re.search(pattern, string):
            return pattern
    return False


def annotate_peptable(predicted_peps_fn, peptable, seqcol, frac_col, stripcol,
                      strips, ignoremods):
    if frac_col > 0:
        frac_col -= 1
    predicted_peps = {}
    with open(predicted_peps_fn) as fp:
        for line in fp:
            line = line.strip('\n').split('\t')
            predicted_peps[line[0]] = line[1]
    not_predicted_count, predicted_count = 0, 0
    with open(peptable) as fp:
        header = next(fp).strip('\n').split('\t')
        yield header + ['Experimental pI', 'Predicted pI', 'Delta pI']
        for line in fp:
            line = line.strip('\n').split('\t')
            strip = strips[get_first_matching_pattern(strips.keys(),
                                                      line[stripcol - 1])]
            exp_pi = (strip['fr_width'] * int(line[frac_col]) +
                      strip['intercept'])

            sequence = line[seqcol - 1]
            for weight in ignoremods:
                if weight == '*':
                    regex = '[+-]\d*\.\d*'
                else:
                    regex = '[+-]{}'.format(weight)
                sequence = re.sub(regex, '', sequence)
            try:
                pred_pi = float(predicted_peps[sequence])
            except KeyError:
                print('CANNOT PREDICT', sequence)
                not_predicted_count += 1
                pred_pi, delta_pi = 'NA', 'NA'
            else:
                delta_pi = exp_pi - pred_pi
                predicted_count += 1
            yield line + [exp_pi, pred_pi, delta_pi]
    print('Number of peptides without pI prediction: {}\n'
          'Number of peptides with predicion: {}\n'.format(not_predicted_count,
                                                           predicted_count))


def parse_commandline():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--out', dest='outpeptable', help='Output peptide '
                        'table')
    parser.add_argument('-p', dest='peptable', help='Peptide/PSM table with '
                        'peptides, FDR, fraction numbers. Used to calculate'
                        'pI shift.')
    parser.add_argument('-i', dest='pipeps', help='A tab-separated txt file '
                        'with peptide seq, pI value')
    parser.add_argument('--pepcol', dest='pepcol', help='Peptide sequence '
                        'column number in peptide table. First column is 1.',
                        default=False, type=int)
    parser.add_argument('--fraccol', dest='frac_col', help='Fraction number '
                        'column number in peptide table. First column is 1.',
                        type=int)
    parser.add_argument('--ignoremods', dest='ignoremods', help='Regex to '
                        'identify modification weights to be ignored.',
                        default=[], nargs='+', type=str)
    parser.add_argument('--stripcol', dest='stripcol', help='Strip name '
                        'column number in peptide table. Will be used to '
                        'detect strips if multiple are present using pattern '
                        'passed with --strippatterns. First column is nr. 1.',
                        default=False, type=int)
    parser.add_argument('--strippatterns', dest='pipatterns',
                        help='Patterns to detect different pI ranges from e.g.'
                        ' file name in peptide table', nargs='+')
    parser.add_argument('--intercepts', dest='intercepts',
                        help='pI Intercept of strips', nargs='+', type=float)
    parser.add_argument('--widths', dest='fr_width', nargs='+',
                        help='Strip fraction widths in pI', type=float)
    return parser.parse_args(sys.argv[1:])


if __name__ == '__main__':
    main()
