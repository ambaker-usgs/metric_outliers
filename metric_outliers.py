import commands
import numpy
import os

from obspy.core import UTCDateTime

path_to_dqa = '/home/ambaker/asl-dqa-tools/'
master_blacklist = ['GS_OK031']
availability_blacklist = ['GT','II']

#threshholds
dead_chan_threshhold = 1.0
mass_pos_threshhold = 95.0
timing_qual_threshhold = 60.0
gaps_threshhold = 5.0
gain_threshhold = 1.0
availability_threshhold = 10.0

debug = False

class Issue(object):
    def __init__(self, nickname, newer_issues, older_issues):
        #filter out the blacklisted networks and stations
        for netsta in master_blacklist:
            for nissue in newer_issues:
                if netsta in nissue:
                    newer_issues.pop(newer_issues.index(nissue))
            for oissue in older_issues:
                if netsta in oissue:
                    older_issues.pop(older_issues.index(oissue))
        self.nickname = nickname
        self.newer = newer_issues
        self.older = older_issues

def query_dqa(metric, date):
    'Queries DQA for the given metric and time frame'
    date = date.strftime('%Y-%m-%d')
    results = ''
    for server in ['prod','dqags']:
        results += commands.getstatusoutput(path_to_dqa + 'dqa4h.py -w %s -m %s -b %s -e %s' % (server, metric, date, date))[1]
    return results.strip().split('\n')

def metric_outliers(results, inequality, threshhold):
    'Reports any outlying stations for given metric and threshhold'
    outliers = []
    for result in results:
        date, net, sta, loc, chan, metric, value = result.split()
        if eval('float(value) %s %s' % (inequality, threshhold)):
            outliers.append('%-2s_%-5s %-2s-%-3s' % (net, sta, loc, chan))
    return outliers

def timing_outliers(results, inequality, threshhold):
    'Reports any outyling stations based on timing quality'
    outliers = []
    for result in results:
        date, net, sta, loc, chan, metric, value = result.split()
        if eval('float(value) %s %s' % (inequality, threshhold)):
            outliers.append('%-2s_%-5s %-2s-%-2s*' % (net, sta, loc, chan[:2]))
    return outliers

def gap_outliers(results, inequality, threshhold):
    'Reports any outlying stations based on gaps'
    outlier_counts = {}
    for result in results:
        date, net, sta, loc, chan, metric, value = result.split()
        if eval('float(value) %s %s' % (inequality, threshhold)):
            netsta = '_'.join([net,sta])
            if netsta not in outlier_counts.keys():
                outlier_counts[netsta] = 0
            outlier_counts[netsta] += 1
    outliers = []
    for netsta, count in outlier_counts.items():
        outliers.append('%-2s_%-5s %s channels' % (net, sta, count))
    return outliers

def gain_outliers(results, inequality, threshhold):
    'Reports any outlying stations based on gain differences'
    outliers = []
    for result in results:
        date, net, sta, loc, chan, metric, value = result.split()
        if eval('float(value) %s %s' % (inequality, threshhold)):
            outliers.append('%-2s_%-5s %-5s-%-9s %-5.2f' % (net, sta, loc, chan, float(value)))
    return outliers

def availability_outliers(results, inequality, threshhold):
    'Reports any outlying stations based on per-channel differences in availability'
    outliers = []
    stations = {}
    for result in results:
        date, net, sta, loc, chan, metric, value = result.split()
        if net not in availability_blacklist:
            netsta = '_'.join([net,sta])
            if netsta not in stations.keys():
                stations[netsta] = [[],[]]
            stations[netsta][0].append('-'.join([loc,chan]))
            stations[netsta][1].append(float(value))
    for netsta, vals in stations.items():
        average = numpy.average(vals[1])
        if (min(vals[1]) + threshhold) <= average <= (max(vals[1]) - threshhold):
            outliers.append('%-8s %6.2f min  %6.2f avg  %6.2f max' % (netsta, min(vals[1]), average, max(vals[1])))
    return outliers

def make_readable(nickname, outliers):
    'Prints the outlying stations in a legible format'
    for outlier in set(outliers):
        print '%s: %s' % (nickname, outlier)

def sort_issues(*issues):
    'Sorts the issues into new, ongoing, and resolved'
    issues_new = []
    issues_ongoing = []
    issues_resolved = []
    for issue in issues:
        new = sorted(set(issue.newer).difference(issue.older))
        ongoing = sorted(set(issue.newer).intersection(issue.older))
        resolved = sorted(set(issue.older).difference(issue.newer))
        if new:
            for iss in new:
                # print '+%12s: %s' % (issue.nickname, iss)
                issues_new.append('%6s: %s' % (issue.nickname, iss))
        if ongoing:
            for iss in ongoing:
                # print ' %12s: %s' % (issue.nickname, iss)
                issues_ongoing.append('%6s: %s' % (issue.nickname, iss))
        if resolved:
            for iss in resolved:
                # print '-%12s: %s' % (issue.nickname, iss)
                issues_resolved.append('%6s: %s' % (issue.nickname, iss))
    return issues_new, issues_ongoing, issues_resolved

def write_to_file(date, new, ongoing, resolved, mailto=False):
    'Writes the issues to a file, optionally mails'
    output = []
    header = 'Report generated comparing days %s to %s' % (date.strftime('%Y-%m-%d (%j)'), (date - 86400).strftime('%Y-%m-%d (%j)'))
    output.append(header)
    output.append('\n == NEW ISSUES ==')
    output.extend(new)
    output.append('\n == ONGOING ISSUES ==')
    output.extend(ongoing)
    output.append('\n == RESOLVED ISSUES ==')
    output.extend(resolved)
    fob = open('/home/ambaker/metric_outliers/metric_outliers.txt','w')
    fob.write('\n'.join(output))
    fob.close()
    # print '\n'.join(output)
    if mailto:
        command = 'mutt -s \"Metric Outliers for %s\" ' % date.strftime('%Y-%m-%d (%j)')
        command += '-a /home/ambaker/metric_outliers/metric_outliers.txt -- '
        if not debug:
            command += 'tstorm@usgs.gov,aringler@usgs.gov,dwilson@usgs.gov,aaholland@usgs.gov, met@iris.washington.edu, lsandoval@usgs.gov, kschramm@usgs.gov,'
        command += 'ambaker@usgs.gov </dev/null'
        commands.getstatusoutput(command)
    commands.getstatusoutput('rm /home/ambaker/metric_outliers/metric_outliers.txt')

if __name__ == '__main__':
    date = UTCDateTime.now() - 2*24*60*60
    #dead channels
    dead_channel_new = metric_outliers(query_dqa('DeadChannelMetric:4-8', date), '<', dead_chan_threshhold)
    dead_channel_old = metric_outliers(query_dqa('DeadChannelMetric:4-8', date - 86400), '<', dead_chan_threshhold)
    dead_channel = Issue('DeadCh', dead_channel_new, dead_channel_old)
    #pegged masses
    pegged_masses_new = metric_outliers(query_dqa('MassPositionMetric', date), '>=', mass_pos_threshhold)
    pegged_masses_old = metric_outliers(query_dqa('MassPositionMetric', date - 86400), '>=', mass_pos_threshhold)
    pegged_masses = Issue('Pegged', pegged_masses_new, pegged_masses_old)
    #timing problems
    timing_problems_new = timing_outliers(query_dqa('TimingQualityMetric', date), '<', timing_qual_threshhold)
    timing_problems_old = timing_outliers(query_dqa('TimingQualityMetric', date - 86400), '<', timing_qual_threshhold)
    timing = Issue('Timing', timing_problems_new, timing_problems_old)
    #gaps
    gaps_new = gap_outliers(query_dqa('GapCountMetric', date), '>=', gaps_threshhold)
    gaps_old = gap_outliers(query_dqa('GapCountMetric', date - 86400), '>=', gaps_threshhold)
    gaps = Issue('GapsCt', gaps_new, gaps_old)
    #gain problems
    gain_new = gain_outliers(query_dqa('DifferencePBM:4-8', date), '>=', gain_threshhold)
    gain_old = gain_outliers(query_dqa('DifferencePBM:4-8', date - 86400), '>=', gain_threshhold)
    gain = Issue('Gain', gain_new, gain_old)
    #availability
    avail_new = availability_outliers(query_dqa('AvailabilityMetric', date), '>=', availability_threshhold)
    avail_old = availability_outliers(query_dqa('AvailabilityMetric', date - 86400), '>=', availability_threshhold)
    avail = Issue('Avail%', avail_new, avail_old)
    #sort and write a file
    new, ongoing, old = sort_issues(dead_channel, pegged_masses, timing, gaps, gain, avail)
    write_to_file(date, new, ongoing, old, True)