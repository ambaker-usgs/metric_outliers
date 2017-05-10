import commands

from obspy.core import UTCDateTime

# def metric_outliers(header, metric_name, date, inequality, threshhold):
#     'Identify outlying stations for given metric'
#     results = commands.getstatusoutput('/APPS/bin/dqa4h.py -w prod -m %s -b %s -e %s' % (metric_name, date, date))[1]
#     results = results.strip().split('\n')
#     outliers = {}
#     for result in results:
#         date, net, sta, loc, chan, metric, value = result.split()
#         if eval('float(value) %s %s' % (inequality, threshhold)):
#             if '_'.join([net, sta]) not in outliers.keys():
#                 outliers['_'.join([net, sta])] = []
#             outliers['_'.join([net, sta])].append('-'.join([loc, chan]))
#     return outliers
    # return make_readable(header, outliers)

def metric_outliers(metric_name, date, inequality, threshhold):
    'Identify outlying stations for given metric'
    results = commands.getstatusoutput('/APPS/bin/dqa4h.py -w prod -m %s -b %s -e %s' % (metric_name, date, date))[1]
    results = results.strip().split('\n')
    outliers = []
    for result in results:
        date, net, sta, loc, chan, metric, value = result.split()
        if eval('float(value) %s %s' % (inequality, threshhold)):
            outliers.append('%2s_%-5s %s-%s' % (net, sta, loc, chan))
    return outliers

def make_readable(header, outliers):
    header = ' %s:' % header
    for outlier in outliers:
        netsta, locchan = outlier.split()
        if netsta not in header:
            header += '\n  %-7s' % netsta
        header += ' %s' % locchan
    return header + '\n'

if __name__ == '__main__':
    current_time = UTCDateTime.now()
    window_of_time = [current_time - 2*24*60*60, current_time - 3*24*60*60]
    problems_new = '== New Issues ==\n'
    problems_ongoing = '\n== Ongoing Issues ==\n'
    problems_resolved = '\n== Resolved Issues ==\n'
    # Metrics to look at; nickname, metric name, threshhold inequality, threshhold
    metrics = [['Dead Channels', 'DeadChannelMetric:4-8', '<', 1.0],
               ['Pegged Masses', 'MassPositionMetric', '>=', 95.0],
               ['Timing Probs', 'TimingQualityMetric', '<', 60.0],
               ['Gaps', 'GapCountMetric', '>=', 5.0],
               ['Gain Problems', 'DifferencePBM:4-8', '>=', 1.0]]
    for metric in metrics:
        nickname, metric_name, inequality, threshhold = metric
        outliers_newer = metric_outliers(metric_name, window_of_time[0].strftime('%Y-%m-%d'), inequality, threshhold)
        outliers_older = metric_outliers(metric_name, window_of_time[1].strftime('%Y-%m-%d'), inequality, threshhold)
        if set(outliers_newer).difference(outliers_older):
            problems_new += make_readable(nickname, list(sorted(set(outliers_newer).difference(outliers_older))))
            # problems_new += '\n' + nickname + ':\n  ' + '\n  '.join(sorted(set(outliers_newer).difference(outliers_older)))
            # print 'New %s:' % nickname
            # print '\n  '.join(set(outliers_newer).difference(outliers_older))
        if set(outliers_newer).intersection(outliers_older):
            problems_ongoing += make_readable(nickname, list(sorted(set(outliers_newer).intersection(outliers_older))))
            # problems_ongoing += '\n' + nickname + ':\n  ' + '\n  '.join(sorted(set(outliers_newer).intersection(outliers_older)))
            # print 'Ongoing %s:' % nickname
            # print '\n  '.join(set(outliers_newer).intersection(outliers_older))
        if set(outliers_older).difference(outliers_newer):
            problems_resolved += make_readable(nickname, list(sorted(set(outliers_older).difference(outliers_newer))))
            # problems_resolved += '\n' + nickname + ':\n  ' + '\n  '.join(sorted(set(outliers_older).difference(outliers_newer)))
            # print 'Resolved %s:' % nickname
            # print '\n  '.join(set(outliers_older).difference(outliers_newer))
    #availability
    # outliers_newer = metric_availability()
    print 'Comparing %s to %s' % (window_of_time[0].strftime('%Y-%m-%d'), window_of_time[1].strftime('%Y-%m-%d'))
    print problems_new, problems_ongoing, problems_resolved
        
        # outliers_new = set(dict_newer) - set(dict_older)
        # outliers_ongoing = set(dict_newer)
        # if outliers_new:
        #     print 'New', nickname + ':'
        #     while outliers_new
        # print compare_dictionaries(dict_newer, dict_older)
        # for time in window_of_time:
        #     nickname, metric_name, inequality, threshhold = metric
        #     result_dict = metric_outliers(nickname, metric_name, time.strftime('%Y-%m-%d'), inequality, threshhold)
        #     print make_readable(nickname.upper(), result_dict)
        # print commands.getstatusoutput('python /home/ambaker/adamr/availChecker.py -b %s'  % time.strftime('%Y-%j'))[1]