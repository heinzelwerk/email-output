#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import datetime
import os
import socket
import subprocess
import sys
import tempfile
import time
from email.mime.text import MIMEText

PROG_NAME = os.path.basename(__file__)
VERSION = '1.2'


class Program:
    def __init__(self):
        self._argparser = self._setup_argparser()

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    @staticmethod
    def _setup_argparser():
        kwargs = {
            'prog': PROG_NAME,
            'formatter_class': argparse.RawDescriptionHelpFormatter,
            'description': 'Execute a command and send its output via email',
            'usage': '%(prog)s [OPTIONS] [--] COMMAND [ARGS ...]',
            'epilog': """To prevent ARGS to be interpreted as OPTIONS to %(prog)s,
 add two dashes (--) before the COMMAND.

Using the option --not-on-success will prevent sending an email if the command
 returns zero (i.e. command succeed) no matter if output were produced or not.
 Use this option if you want emails only if the command fails.

Using the option --not-on-silence will prevent sending an email if the command
 does not produce output no matter of the return code.
 Use this option if you want emails only if the command produces output.
 
If both options --not-on-silence and --not-on-success are given, an email will
 only be sent if the command fails AND produce output.
 This is likely not to be the behaviour you want.

To get an email if the command fails OR produce output use the option
 --not-on-silent-success
"""
        }
        parser = argparse.ArgumentParser(**kwargs)
        parser.add_argument('--version', '-V',
                            action='version', version='%(prog)s {}'.format(VERSION))
        parser.add_argument('--no-combined', '-C',
                            action='store_true',
                            help='do not combine stdout and stderr')

        parser.add_argument('--not-on-silence',
                            action='store_true',
                            help='only send email if command produce output')
        parser.add_argument('--not-on-success',
                            action='store_true',
                            help='only send email if command exit with non-zero'
                                 ' return code (i.e. command fails)')
        parser.add_argument('--not-on-silent-success',
                            action='store_true',
                            help='only send email if command exit with non-zero'
                                 ' return code or produce any output')

        parser.add_argument('--recipient', '-r', nargs=1, metavar='ADDR',
                            action='append',
                            help='the email address, that the command output will be sent to'
                                 ' (can be used multiple times)')
        parser.add_argument('--subject', '-s', nargs=1, metavar='TEXT',
                            help='the email subject')
        parser.add_argument('command', nargs=1, metavar='COMMAND',
                            help='the command, that will be executed')
        parser.add_argument('argv', nargs='*', metavar='ARGS',
                            help='arguments to COMMAND')
        return parser

    def _parse_args(self, argv=None):
        if argv is None:
            argv = sys.argv[1:]

        return self._argparser.parse_args(argv)

    @staticmethod
    def _get_local_timezone():
        localtime = time.localtime()
        tz_name = localtime.tm_zone
        tz_offset = localtime.tm_gmtoff
        return datetime.timezone(datetime.timedelta(seconds=tz_offset), name=tz_name)

    @staticmethod
    def _write_to_stdout(fp):  # pylint: disable=invalid-name
        fp.seek(0)
        sys.stdout.write(fp.read().decode(sys.stdout.encoding))

    @staticmethod
    def _write_to_stderr(fp):  # pylint: disable=invalid-name
        fp.seek(0)
        sys.stderr.write(fp.read().decode(sys.stderr.encoding))

    @staticmethod
    def _send_email(body, subject=None, to_hdr=None, from_hdr=None):
        hostname = socket.getfqdn()
        user = os.getenv('USER', os.getenv('LOGNAME', 'root'))

        if subject is None:
            subject = 'Command output'
        if to_hdr is None:
            to_hdr = '<{user}>'.format(user=user)
        if from_hdr is None:
            from_hdr = '"{user} @ {hostname}" <{user}>'.format(user=user, hostname=hostname)

        msg = MIMEText(body)
        msg['From'] = from_hdr
        msg['To'] = to_hdr
        msg['Subject'] = subject
        sendmail_cmd = 'sendmail -t -oi'
        ret = subprocess.run(sendmail_cmd, shell=True, check=False, input=msg.as_bytes())
        if ret.returncode:
            sys.stderr.write('Sending email failed (\'{cmd}\' returned {ret})\n'.format(cmd=sendmail_cmd,
                                                                                        ret=ret.returncode))

    def run(self, *args, **kwargs):
        if 'argv' in kwargs:
            argv = kwargs.get('argv', None)
        elif args:
            argv = args
        else:
            argv = None
        prog_args = self._parse_args(argv)

        command = prog_args.command + prog_args.argv
        combine_output = not prog_args.no_combined
        if prog_args.subject:
            mail_subject = prog_args.subject[0]
        else:
            mail_subject = ' '.join(command)

        # Create one or two temporary files to buffer output from the command
        # (depending if we should combine stdout and stderr or not)
        stdout_buf = tempfile.TemporaryFile()
        if combine_output:
            stderr_buf = subprocess.STDOUT
        else:
            stderr_buf = tempfile.TemporaryFile()

        # Run the command and store time before and after
        timezone = self._get_local_timezone()
        command_started_at = datetime.datetime.now(timezone)
        try:
            ret = subprocess.run(command, check=True, stdout=stdout_buf, stderr=stderr_buf)
            command_returncode = ret.returncode
        except FileNotFoundError as e:
            error_msg = '{}: {}\n'.format(e.filename, e.strerror)
            if combine_output:
                stdout_buf.write(error_msg.encode('utf-8'))
            else:
                stderr_buf.write(error_msg)
            command_returncode = e.errno
        except subprocess.CalledProcessError as e:
            command_returncode = e.returncode
        command_finished_at = datetime.datetime.now(timezone)

        # Write the command output to our output
        has_output = False
        if stdout_buf.tell():
            has_output = True
            self._write_to_stdout(stdout_buf)

        if not combine_output and stderr_buf.tell():
            has_output = True
            self._write_to_stderr(stderr_buf)

        # Send an email if command returned non-zero (or user want it anyways)
        # DNF
        #if (has_output and command_returncode) or \
        #        (has_output and not prog_args.not_on_success) or \
        #        (command_returncode and prog_args.not_on_silence) or \
        #        (prog_args.not_on_success and prog_args.not_on_silence and prog_args.not_on_silent_success):
        # KNF
        if (has_output or not prog_args.not_on_silence) and \
                (command_returncode or not prog_args.not_on_success) and \
                (has_output or command_returncode or not prog_args.not_on_silent_success):
            mail_body = ''

            # Add some information about the command to the mail
            timestamp_format = '%a, %d.%m.%Y %H:%M:%S.%f %Z (%z)'
            mail_intro = """Host:        {hostname}
Command:     {command}
Started at:  {started}
Finished at: {finished}
Return code: {returncode}

""".format(
                hostname=socket.getfqdn(),
                command=' '.join(command),
                started=command_started_at.strftime(timestamp_format),
                finished=command_finished_at.strftime(timestamp_format),
                returncode=command_returncode
            )

            mail_body += mail_intro

            # Add the command output to the mail
            if combine_output:
                mail_body += 'Output:\n'
            else:
                mail_body += '----- stdout -----\n'

            stdout_buf.seek(0)
            for line in stdout_buf:
                mail_body += line.decode('utf-8')

            if not combine_output:
                mail_body += '----- stderr -----\n'
                stderr_buf.seek(0)
                for line in stderr_buf:
                    mail_body += line.decode('utf-8')

            # Who should receive a mail
            if prog_args.recipient:
                # Flatten two dimensional list from argparse
                recipients = []
                for recipient_list in prog_args.recipient:
                    for recipient in recipient_list:
                        recipients.append(recipient)
            else:
                recipients = [None]

            # Send mails to all recipients
            for recipient in recipients:
                self._send_email(mail_body, subject=mail_subject, to_hdr=recipient)

        # Close our buffers -> the temporary files will be deleted automatically
        stdout_buf.close()
        if stderr_buf != subprocess.STDOUT:
            stderr_buf.close()

        exitval = command_returncode
        return exitval


def main(*args, **kwargs):
    program = Program()
    exitval = program(*args, **kwargs)
    sys.exit(exitval)


if __name__ == '__main__':
    main()
