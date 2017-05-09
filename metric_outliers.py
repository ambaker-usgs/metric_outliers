import commands

from obspy.core import UTCDateTime

# def metric_dead_channels(ws, we):
#     header = 'Dead Channels:\n'
#     results = commands.getstatusoutput('/APPS/bin/dqa4h.py -w prod -m DeadChannelMetric:4-8 -b %s -e %s' % (ws, we))[1].strip().split('\n')
#     dead_channels = {}
#     for result in results:
#         date, net, sta, loc, chan, metric_name, value = result.split()
#         if float(value) < dead_channel_threshhold:
#             if '_'.join([net,sta]) not in dead_channels.keys():
#                 dead_channels['_'.join([net, sta])] = []
#             dead_channels['_'.join([net, sta])].append('-'.join([loc, chan]))
#     return make_readable(header, dead_channels)
#
# def metric_pegged_mass_positions(ws, we):
#     'Identify stations with pegged mass positions'
#     header = 'Pegged:\n'
#     results = commands.getstatusoutput('/APPS/bin/dqa4h.py -w prod -m MassPositionMetric -b %s -e %s' % (ws, we))[1].strip().split('\n')
#     pegged_masses = {}
#     for result in results:
#         date, net, sta, loc, chan, metric, value = result.split()
#         if float(value) >= mass_position_threshhold:
#             if '_'.join([net, sta]) not in pegged_masses.keys():
#                 pegged_masses['_'.join([net, sta])] = []
#             pegged_masses['_'.join([net, sta])].append('-'.join([loc, chan]))
#     return make_readable(header, pegged_masses)

def metric_outliers(header, metric_name, window_start, window_end, inequality, threshhold):
    'Identify outlying stations for given metric'
    results = commands.getstatusoutput('/APPS/bin/dqa4h.py -w prod -m %s -b %s -e %s' % (metric_name, window_start, window_end))[1]
    results = results.strip().split('\n')
    outliers = {}
    for result in results:
        date, net, sta, loc, chan, metric, value = result.split()
        if eval('float(value) %s %s' % (inequality, threshhold)):
            if '_'.join([net, sta]) not in outliers.keys():
                outliers['_'.join([net, sta])] = []
            outliers['_'.join([net, sta])].append('-'.join([loc, chan]))
    return outliers
    # return make_readable(header, outliers)

def make_readable(header, dictionary):
    header += ':\n'
    for netsta in dictionary.keys():
        header += '  %-8s %s\n' % (netsta, ' '.join(dictionary[netsta]))
    return header

def compare_dictionaries(dict_old, dict_new):
    'Compare dictionaries for different times to identify resolved, new, and ongoing problems'
    print 'ONGOING PROBLEMS (in old and in new):'
    for netsta in dict_old.keys():
        if netsta in dict_new.keys():
            for locchan in dict_old[netsta]:
                if locchan in dict_new[netsta]:
                    print netsta, locchan
    print 'NEW PROBLEMS (not in old but in new):'
    for netsta in dict_new.keys():
        if netsta not in dict_old.keys():
            for locchan in dict_new[netsta]:
                if netsta in dict_old.keys():
                    if locchan not in dict_old[netsta]:
                        print netsta, locchan
                else:
                    print netsta, locchan
    print 'RESOLVED PROBLEMS (in old but not in new):'
    for netsta in dict_old.keys():
        if netsta not in dict_new.keys():
            for locchan in dict_old[netsta]:
                if netsta in dict_new.keys():
                    if locchan not in dict_old[netsta]:
                        print netsta, locchan
                else:
                    print netsta, locchan

if __name__ == '__main__':
    current_time = UTCDateTime.now()
    window_end = current_time - 1*24*60*60
    window_start = current_time - 2*24*60*60
    # Metrics to look at; nickname, metric name, threshhold inequality, threshhold
    metrics = [['Dead Channels', 'DeadChannelMetric:4-8', '<', 1.0],
               ['Pegged Masses', 'MassPositionMetric', '>=', 95.0],
               ['Timing Probs', 'TimingQualityMetric', '<', 60.0],
               ['Gaps', 'GapCountMetric', '>=', 5.0],
               ['Gain Problems', 'DifferencePBM:4-8', '>=', 1.0]]
    for metric in metrics:
        nickname, metric_name, inequality, threshhold = metric
        result_dict = metric_outliers(nickname, metric_name, window_start.strftime('%Y-%m-%d'), window_end.strftime('%Y-%m-%d'), inequality, threshhold)
        print make_readable(nickname.upper(), result_dict)
    print commands.getstatusoutput('python /home/ambaker/adamr/availChecker.py -b %s'  % (str(window_start.year) + str(window_start.julday).zfill(3)))[1]