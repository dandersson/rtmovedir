#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import codecs
import locale
import logging
import argparse
import re
import socket

import xmlrpclib

import rtmovedirlib.rtmovedirlib


class Printer(object):
    """Helper functions for printing."""
    def __init__(self, silent=False):
        self.silent = silent

    def out(self, message=''):
        if not self.silent:
            print message

    def error(self, message='Unknown error.', exit_status=1):
        print >> sys.stderr, '{}: error: {}'.format(sys.argv[0], message)
        sys.exit(exit_status)

    def regexp_error(self, regexp):
        self.error(u'Invalid regular expression:\n'
                   u'   {}\n'
                   u'Watch out for unbalanced parentheses.'.format(regexp), 2)


class Colors(object):
    """ANSI sequences for colored output."""
    __colors = dict(red    = '\033[91m',
                    green  = '\033[92m',
                    yellow = '\033[93m',
                    blue   = '\033[94m',
                    pink   = '\033[95m',
                    end    = '\033[0m')

    @property
    def colors(self):
        return self.__colors
    @colors.setter
    def colors(self, state):
        self.__colors = Colors.__colors if state else {k: '' for k in
                                                       Colors.__colors}


def main():
    # Some magic to allow Python printing UTF-8 according to the recipient's
    # reported capabilities; see <http://stackoverflow.com/a/4546129/445621>
    sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)

    argparser = argparse.ArgumentParser(
            description='Change directories of rTorrent downloads via regexp '
                        'replacement.')

    argparser.add_argument('url', help='XML-RPC URL')
    argparser.add_argument('match', help='regexp match pattern')
    argparser.add_argument('replace', help='regexp replace pattern')
    argparser.add_argument('-s', '--search',
            help='update paths only for items matching this pattern')
    argparser.add_argument('--hashlist', metavar='HASH', nargs='+',
            help='hash IDs to consider')
    argparser.add_argument('-x', '--execute', action='store_true',
            help='execute query')
    argparser.add_argument('--silent', action='store_true',
            help='disable standard output')
    argparser.add_argument('--no-colors', action='store_true',
            help='disable color output')
    argparser.add_argument('--debug', action='store_true',
            help='enable debug messages')

    args = argparser.parse_args()

    loglevel = 'DEBUG' if args.debug else 'INFO'
    # Right now only debug=True/False is used. Boiler plate code below to allow
    # for more fine-grained user control in the improbable future.
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('invalid log level: {}'.format(loglevel))
    logging.basicConfig(format=u'%(levelname)s:%(message)s',
                        level=numeric_level)

    SERVERURL = args.url

    # rTorrent works in UTF-8 internally, and all data from XML-RPC is in that
    # encoding. Make sure everything takes this into account.
    MATCH    = args.match.decode('utf-8')
    REPLACE  = args.replace.decode('utf-8')
    HASHLIST = args.hashlist
    EXECUTE  = args.execute
    SILENT   = args.silent
    COLORS   = not args.no_colors

    try:
        SEARCH = args.search.decode('utf-8')
    except AttributeError:
        SEARCH = None

    c = Colors()
    c.colors = COLORS

    p = Printer(SILENT)

    try:
        r = re.compile(MATCH)
    except re.error:
        p.regexp_error(MATCH)

    rt = xmlrpclib.ServerProxy(SERVERURL)

    try:
        tg = rtmovedirlib.rtmovedirlib.TorrentEntryGenerator(
                rt, search=SEARCH, hashlist=HASHLIST)
    except re.error:
        p.regexp_error(SEARCH)
    except ValueError as msg:
        p.error(msg)
    except KeyError as msg:
        p.error('hash ID {} is not registered in rTorrent session.'.format(
            msg))
        p.error(msg)
    except xmlrpclib.ProtocolError:
        p.error('XML-RPC server timed out. Check connection.')
    except socket.gaierror as msg:
        p.error('Could not connect to XML-RPC server:\n   {}'.format(msg))

    errors = []
    for t in tg:
        logging.debug(t.hash_id)
        try:
            cur_dir = t.directory
        except xmlrpclib.Fault as msg:
            p.out(u'rTorrent error for hash ID {}:\n'
                  u'   {}\n'
                  u'Continuing...\n'.format(t.hash_id, unicode(msg)))
            errors.append(t.hash_id)
            continue

        (new_dir, subn) = r.subn(REPLACE, cur_dir, count=1)

        if subn == 0:
            logging.debug(u'No match: {}\n'.format(cur_dir))
        elif new_dir == cur_dir:
            logging.debug(u'Match, but no change: {}\n'.format(cur_dir))
        else:
            p.out(u'{blue}{}{end}:{pink}{}{end}\n'
                  u'   {red}{}{end}\n'
                  u' → {green}{}{end}'.format(
                      t.hash_id,
                      t.base_filename,
                      cur_dir,
                      new_dir,
                      **c.colors))

            if EXECUTE:
                t.move(new_dir)
            p.out()

    if errors:
        p.out()
        p.out(u'{red}Errors were encountered{end} for these hash IDs:'.format(
            **c.colors))
        for error in errors:
            p.out(u'   {pink}{}{end}'.format(error, **c.colors))
        p.out(u'as per earlier error messages.')


    if not EXECUTE:
        p.out(u'\n--This was a {red}dry run{end}. '
              u'Use switch {green}-x to execute queries{end}.--'.format(
                   **c.colors))


if __name__ == '__main__':
    main()
