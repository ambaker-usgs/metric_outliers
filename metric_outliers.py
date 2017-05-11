import commands
import numpy

from obspy.core import UTCDateTime

dead_channels_threshhold = 1.0
pegged_masses_threshhold = 95.0
timing_quality_threshhold = 60.0
gaps_threshhold = 5.0
gain_problems_threshhold = 1.0
availability_threshhold = 10.0

networks_blacklist = ['GT','II']

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
    results += commands.getstatusoutput('/APPS/bin/dqa4h.py -w dqags -m %s -b %s -e %s' % (metric_name, date, date))[1]
    results = results.strip().split('\n')
    outliers = []
    for result in results:
        date, net, sta, loc, chan, metric, value = result.split()
        if eval('float(value) %s %s' % (inequality, threshhold)):
            outliers.append('%2s_%-5s %s-%s' % (net, sta, loc, chan))
    return outliers

def metric_availability(metric_name, date, inequality, threshhold):
    'Identify outlying stations for given metric'
    results = commands.getstatusoutput('/APPS/bin/dqa4h.py -w prod -m %s -b %s -e %s' % (metric_name, date, date))[1]
    results += commands.getstatusoutput('/APPS/bin/dqa4h.py -w dqags -m %s -b %s -e %s' % (metric_name, date, date))[1]
    results = results.strip().split('\n')
    outliers = []
    stations = {}
    for result in results:
        date, net, sta, loc, chan, metric, value = result.split()
        if net not in networks_blacklist:
            if '_'.join([net,sta]) not in stations.keys():
                stations['_'.join([net,sta])] = [[],[]]
            stations['_'.join([net,sta])][0].append('-'.join([loc,chan]))
            stations['_'.join([net,sta])][1].append(float(value))
    for netsta in stations.keys():
        average = numpy.mean(stations[netsta][1])
        for index in range(len(stations[netsta][0])):
            if not (average - threshhold) <= stations[netsta][1][index] <= (average + threshhold):
                outliers.append('%2s_%-5s %s-%s' % (net, sta, loc, chan))
                # print netsta, stations[netsta][0][index], stations[netsta][1][index], average
    return outliers

def make_readable(header, outliers):
    header = ' %s:' % header
    for outlier in outliers:
        netsta, locchan = outlier.split()
        if netsta not in header:
            header += '\n  %-7s' % netsta
        header += ' %s' % locchan
    return header + '\n'

def sort_problems(outliers_newer, outliers_older):
    'Sort the issues into new, ongoing, and resolved'
    new = ''
    ongoing = ''
    resolved = ''
    if set(outliers_newer).difference(outliers_older):
        new = make_readable(nickname, list(sorted(set(outliers_newer).difference(outliers_older))))
    if set(outliers_newer).intersection(outliers_older):
        ongoing = make_readable(nickname, list(sorted(set(outliers_newer).intersection(outliers_older))))
    if set(outliers_older).difference(outliers_newer):
        resolved = make_readable(nickname, list(sorted(set(outliers_older).difference(outliers_newer))))
    return new, ongoing, resolved

if __name__ == '__main__':
    current_time = UTCDateTime.now()
    window_of_time = [current_time - 2*24*60*60, current_time - 3*24*60*60]
    problems_new = '== New Issues ==\n'
    problems_ongoing = '\n== Ongoing Issues ==\n'
    problems_resolved = '\n== Resolved Issues ==\n'
    # Metrics to look at; nickname, metric name, threshhold inequality, threshhold
    metrics = [['Dead Channels', 'DeadChannelMetric:4-8', '<', dead_channels_threshhold],
               ['Pegged Masses', 'MassPositionMetric', '>=', pegged_masses_threshhold],
               ['Timing Probs', 'TimingQualityMetric', '<', timing_quality_threshhold],
               ['Gaps', 'GapCountMetric', '>=', gaps_threshhold],
               ['Gain Problems', 'DifferencePBM:4-8', '>=', gain_problems_threshhold]]
    for metric in metrics:
        nickname, metric_name, inequality, threshhold = metric
        outliers_newer = metric_outliers(metric_name, window_of_time[0].strftime('%Y-%m-%d'), inequality, threshhold)
        outliers_older = metric_outliers(metric_name, window_of_time[1].strftime('%Y-%m-%d'), inequality, threshhold)
        issues_new, issues_ongoing, issues_resolved = sort_problems(outliers_newer, outliers_older)
        problems_new += issues_new
        problems_ongoing += issues_ongoing
        problems_resolved += issues_resolved
    #availability
    outliers_newer = metric_availability('AvailabilityMetric', window_of_time[0].strftime('%Y-%m-%d'), '>=', availability_threshhold)
    outliers_older = metric_availability('AvailabilityMetric', window_of_time[1].strftime('%Y-%m-%d'), '>=', availability_threshhold)
    avail_new, avail_ongoing, avail_resolved = sort_problems(outliers_newer, outliers_older)
    problems_new += avail_new
    problems_ongoing += avail_ongoing
    problems_resolved += avail_resolved
    print 'Comparing %s to %s' % (window_of_time[0].strftime('%Y-%m-%d'), window_of_time[1].strftime('%Y-%m-%d'))
    print problems_new, problems_ongoing, problems_resolved