import logging
import platform
import sys

from sarge import Capture, Pipeline

__author__ = 'Sungho Park'
_logger = logging.getLogger(__name__)


class CliCommand:
    """
    This class represents command line program. You can run program with this like the below:

        >>> import cliproc
        >>>
        >>> lscmd = cliproc.CliCommand("/usr/bin/ls")
        >>> lscmd.run("-l")

    This class use Pipeline class of sarge project.
    Please refer to `sarge's documentation <http://sarge.readthedocs.org/en/latest/index.html>`_.

    :param cmd: command line program full path
    :type cmd: str
    :param posix: Whether the source will be parsed using Posix conventions.
    :type posix: bool
    :param silence: Run command in slience. Default is True.
    :type silence: bool
    :param capture: Capture child process' output. Default is True.
    :type capture: bool
    :param kwargs: Whatever you might pass to `subprocess.Popen <https://docs.python.org/3/library/subprocess.html?highlight=subprocess#subprocess.Popen>`_.
    """

    def __init__(self, cmd, posix=None, silence=True, capture=True, **kwargs):
        self.cmd = cmd
        self.posix = posix
        self.process = None
        self.kwargs = kwargs

        #: standard out data of program
        self.stdout = None
        self.stderr = None

        #: standard error data of program
        if "encoding" in kwargs:
            encoding = kwargs.pop("encoding")
            self.stdout_encoding = encoding
            self.stderr_encoding = encoding
        elif sys.stdout.encoding is not None and sys.stderr.encoding is not None:
            self.stdout_encoding = sys.stdout.encoding
            self.stderr_encoding = sys.stderr.encoding
        else:
            self.stdout_encoding = "utf-8"
            self.stderr_encoding = "utf-8"

        self._silence = silence
        self._capture = capture

    def run(self, param=None, msg=None, input=None, async=False):
        """
        Run command line program with parameters.

        :rtype: Pipeline
        :param param: command line program's arguments. eg) ``-l``, ``list native-project``
        """

        self.terminate()

        _logger.debug("Run command on slience mode %s" % str(self._silence))

        if self._capture is True:
            self.stdout = Capture(encoding=self.stdout_encoding)
            self.stderr = Capture(encoding=self.stderr_encoding)

        command = self.cmd

        if param:
            command = self.cmd + " " + param

        shell = None

        if platform.system() == "Windows":
            command += " & exit"
            shell = True

        _logger.debug("Creating Pipeline object.")
        self.process = Pipeline(source=command, shell=shell, posix=self.posix, stdout=self.stdout, stderr=self.stderr,
                                **self.kwargs)

        self.process.run(input=input, async_=async)

        if not self._silence:
            self._printResult()

        return self.get_process()

    def _printResult(self):
        """
        Print execution log
        """
        print("[] ** START **")
        print("[] Command   : %s" % self.process.source)
        print("[] Exit Code : %d" % self.process.returncode)
        print("[] STDOUT    :", end=" ")

        data = self.stdout.text.split("\n")
        if len(data) > 0:
            print("%s" % data.pop(0))
        else:
            print("")

        for i in data:
            print("[]           : %s" % i)

        print("[] STDERR    :", end=" ")

        data = self.stderr.text.split("\n")
        if len(data) > 0:
            print("%s" % data.pop(0))
        else:
            print("")

        for i in data:
            print("[]           : %s" % i)

        print("[] ** E N D **")
        print()

    def get_process(self):
        """
        Get program process information. The value is equal to return value of run() method.

        :rtype: Pipeline
        :return: :class:`Pipeline <Pipeline>` object. None if not run by run() method.
        """
        return self.process

    def get_output(self):
        """
        Get stdout and stderr data.

        :return: Instance of Capture class.
        """
        return self.stdout

    def terminate(self):
        """
        Terminate process of tool. But you can run it again with run() method.
        This method just closes process and std out&err stream.
        """
        _logger.debug("Terminating Program %s" % self.cmd)

        if self.stdout is not None:
            self.stdout.close(stop_threads=True)
            self.stdout = None

        if self.stderr is not None:
            self.stderr.close(stop_threads=True)
            self.stderr = None

        if self.process is not None:
            self.process.close()
            self.process = None
