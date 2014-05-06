# -*- coding: utf-8 -*-
"""
Created on Tue May  6 15:13:59 2014

@author: pacificoadrien
"""

from sas7bdat import SAS7BDAT


def extract_from_sas(file_to_import):
#if options.debug:
#    logLevel = logging.DEBUG
#else:
#    logLevel = logging.INFO
#inFiles = [args[0]]
#if len(args) == 1:
#    outFiles = ['%s.csv' % os.path.splitext(args[0])[0]]
#elif len(args) == 2 and (args[1] == '-' or
#                         args[1].lower().endswith('.csv')):
#    outFiles = [args[1]]
#else:
#    assert all(x.lower().endswith('.sas7bdat') for x in args)
#    inFiles = args
#    outFiles = ['%s.csv' % os.path.splitext(x)[0] for x in inFiles]
#assert len(inFiles) == len(outFiles)
#for i in xrange(len(inFiles)):
    f = SAS7BDAT(file_to_import)
#    if options.header:
#        f.logger.info(str(f.header))
#        continue
#    f.convertFile(outFiles[i],
#                  delimiter=options.delimiter,
#                  stepSize=options.progress_step)
    return f

if __name__ == '__main__':


    extract = extract_from_sas("/Users/pacificoadrien/Downloads/help.sas7bdat")
    print(extract.__dict__)




#parser = optparse.OptionParser()
#parser.set_usage("""%prog [options] <infile> [outfile]
#
#  Convert sas7bdat files to csv. <infile> is the path to a sas7bdat file and
#  [outfile] is the optional path to the output csv file. If omitted, [outfile]
#  defaults to the name of the input file with a csv extension. <infile> can
#  also be a glob expression in which case the [outfile] argument is ignored.
#
#  Use --help for more details""")
#parser.add_option('-d', '--debug', action='store_true', default=False,
#                  help="Turn on debug logging")
#parser.add_option('--header', action='store_true', default=False,
#                  help="Print out header information and exit.")
#parser.add_option('--delimiter', action='store', default=',',
#                  help="Set the delimiter in the output csv file. "
#                       "Defaults to '%default'.")
#parser.add_option('--progress-step', action='store', default=100000,
#                  metavar='N', type='int',
#                  help="Set the progress step size. Progress will be "
#                       "displayed every N steps. Defaults to %default.")
#options, args = parser.parse_args()
#if len(args) < 1:
#    parser.print_help()
#    sys.exit(1)
#main(options, args)