"""
perf is a tool included in the linux kernel tree that
supports functionality similar to oprofile and more.

@see: http://lwn.net/Articles/310260/
"""

import time, os, stat, subprocess, signal
import logging
from autotest_lib.client.bin import profiler, os_dep, utils


class perf(profiler.profiler):
    version = 1

    def initialize(self, events="cycles,instructions"):
        self.events = events
        self.perf_bin = os_dep.command('perf')
        perf_help = utils.run('%s report help' % self.perf_bin,
                              ignore_status=True).stderr
        self.sort_keys = None
        for line in perf_help.split('\n'):
            a = "sort by key(s):"
            if a in line:
                line = line.strip(a)
                self.sort_keys = [k.rstrip(",") for k in line.split() if
                                  k.rstrip(",") != 'dso']
        if not self.sort_keys:
            self.sort_keys = ['comm', 'cpu']


    def start(self, test):
        self.logfile = os.path.join(test.profdir, "perf")
        cmd = ("%s record -a -o %s -e %s" %
               (self.perf_bin, self.logfile, self.events))
        self._process = subprocess.Popen(cmd, shell=True,
                                         stderr=subprocess.STDOUT)


    def stop(self, test):
        os.kill(self._process.pid, signal.SIGINT)
        self._process.wait()


    def report(self, test):
        for key in self.sort_keys:
            reportfile = os.path.join(test.profdir, '%s.comm' % key)
            cmd = ("%s report -i %s --sort %s,dso" % (self.perf_bin,
                                                      self.logfile,
                                                      key))
            outfile = open(reportfile, 'w')
            p = subprocess.Popen(cmd, shell=True, stdout=outfile,
                                 stderr=subprocess.STDOUT)
            p.wait()
        # The raw detailed perf output is HUGE.  We cannot store it by default.
        perf_log_size = os.stat(self.logfile)[stat.ST_SIZE]
        logging.info('Removing %s after generating reports (saving %s bytes).',
                     self.logfile, perf_log_size)
        os.unlink(self.logfile)
