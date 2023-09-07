#from logparser.Drain import LogParser
#from logparser.LogMine import LogParser
#from logparser.AEL import LogParser
from logparser.LogSig  import LogParser

input_dir = './' # The input directory of log file
output_dir = 'result/'  # The output directory of parsing results
log_file = 'dnf.log'  # The input log file name
log_format = '<Date> <Level> <Component>: <Content>'



####### USING DRAIN
# Regular expression list for optional preprocessing (default: [])
#regex = []
#st = 0.5  # Similarity threshold
#depth = 4  # Depth of all leaf nodes
#parser = LogParser(log_format, indir=input_dir, outdir=output_dir,  depth=depth, st=st, rex=regex)
#parser.parse(f"drain_{log_file}")


######## USING LOgmine
#levels     = 2 # The levels of hierarchy of patterns
#max_dist   = 0.001 # The maximum distance between any log message in a cluster and the cluster representative
#k          = 1 # The message distance weight (default: 1)
#regex      = []  # Regular expression list for optional preprocessing (default: [])

#parser = LogParser(input_dir, output_dir, log_format, rex=regex, levels=levels, max_dist=max_dist, k=k)
#parser.parse(log_file)

####### USING AEL
#minEventCount = 2 # The minimum number of events in a bin
#merge_percent = 0.5 # The percentage of different tokens
#regex         = [] # Regular expression list for optional preprocessing (default: [])

#parser = LogParser(input_dir, output_dir, log_format, rex=regex,#
#                   minEventCount=minEventCount, merge_percent=merge_percent)
#parser.parse(log_file)


####### USING LogSig 
regex        = []  # Regular expression list for optional preprocessing (default: [])
group_number = 14 # The number of message groups to partition

parser = LogParser(input_dir, output_dir, group_number, log_format, rex=regex)
parser.parse(log_file)