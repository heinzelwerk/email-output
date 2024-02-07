#!/usr/bin/env python
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
VERSION = '1.0'


class Program:
    def __init__(self):
        self._argparser = self._setup_argparser()

    def __call__(self, *args, **kwargs):
        return self.run(**kwargs)

    @staticmethod
    def _setup_argparser():
        kwargs = {
            'prog': PROG_NAME,
            'description': 'Execute a command and send its output via email',
            'usage': 'usage: %(prog)s [OPTIONS] [--] COMMAND [ARGS ...]',
            'epilog': 'To prevent ARGS to be interpreted as OPTIONS to %(prog)s,'
                      ' add two dashes (--) before the COMMAND.'
        }
        parser = argparse.ArgumentParser(**kwargs)
        parser.add_argument('-V', '--version', action='version', version='%(prog)s {}'.format(VERSION))
        parser.add_argument('-C', '--no-combined',
                            action='store_true',
                            help='do not combine stdout and stderr')
        parser.add_argument('-E', '--no-empty',
                            action='store_true',
                            help='do not send an email, if command returns zero and no output was produced')
        parser.add_argument('-r', '--recipient', nargs=1, metavar='ADDR',
                            action='append',
                            help='the email address, that the command output will be sent to'
                                 ' (can be used multiple times)')
        parser.add_argument('-s', '--subject', nargs=1, metavar='TEXT',
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

    def run(self, **kwargs):
        argv = kwargs.get('argv', None)
        prog_args = self._parse_args(argv)

        command = prog_args.command + prog_args.argv
        combine_output = not prog_args.no_combined
        send_mail = not prog_args.no_empty
        if prog_args.subject:
            mail_subject = prog_args.subject[0]
        else:
            mail_subject = ' '.join(command)

        stdout_buf = tempfile.TemporaryFile()
        if combine_output:
            stderr_buf = subprocess.STDOUT
        else:
            stderr_buf = tempfile.TemporaryFile()

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

        if command_returncode:
            send_mail = True

        if stdout_buf.tell():
            send_mail = True
            stdout_buf.seek(0)
            sys.stdout.write(stdout_buf.read().decode(sys.stdout.encoding))

        if not combine_output and stderr_buf.tell():
            send_mail = True
            stderr_buf.seek(0)
            sys.stderr.write(stderr_buf.read().decode(sys.stderr.encoding))

        if send_mail:
            mail_body = ''

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

            if prog_args.recipient:
                # Flatten two dimensional list from argparse
                recipients = []
                for recipient_list in prog_args.recipient:
                    for recipient in recipient_list:
                        recipients.append(recipient)
            else:
                recipients = [None]

            for recipient in recipients:
                self._send_email(mail_body, subject=mail_subject, to_hdr=recipient)

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
