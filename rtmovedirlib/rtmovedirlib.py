#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

import xmlrpclib


class TorrentEntryGenerator(object):
    """Create generator of TorrentEntry instances.

    Args:
        rpcserver: An xmlrpclib.ServerProxy instance.
        search: Optional regexp matching on torrents full path.
        hashlist: Optional list of hash IDs to consider.

    Returns:
        A generator of matching TorrentEntry instances.

    Raises:
        TypeError on invalid server handle.
    """
    def __init__(self, rpcserver, search=None, hashlist=None):
        if isinstance(rpcserver, xmlrpclib.ServerProxy):
            self._server = rpcserver
        else:
            raise TypeError('given server handle is not a valid XML-RPC '
                    'server handle.')

        if hashlist is None:
            self.hashlist = self.full_torrent_list
        else:
            self.hashlist = [h for h in hashlist
                             if TorrentEntry.validate_hash_id(h, self._server)]

        try:
            self.rsearch = re.compile(search)
        except TypeError:
            self.rsearch = None

    def __iter__(self):
        if self.rsearch is not None:
            for th in self.hashlist:
                t = TorrentEntry(self._server, th)
                if self.rsearch.search(t.full_path):
                    yield t
        else:
            for th in self.hashlist:
                yield TorrentEntry(self._server, th)

    def __repr__(self):
        return '<TorrentEntryGenerator({!r}, {!r})>'.format(
                self._server,
                self.hashlist)

    def __str__(self):
        return 'Hash IDs: {}'.format(', '.join(self.hashlist))

    def __len__(self):
        return len(self.hashlist)

    @property
    def full_torrent_list(self):
        """Full list of available torrent hash IDs."""
        return self._server.download_list()


class TorrentEntry(object):
    """Return rTorrent entry object communicating via XML-RPC.

    Args:
        rpcserver: An xmlrpclib.ServerProxy instance.
        hash_id: A torrent hash identifier.

    Returns:
        An rTorrent entry object.

    Raises:
        TypeError on invalid server handle.
        TypeError on malformed hash ID.
        ValueError on non-existent hash ID.
    """
    def __init__(self, rpcserver, hash_id):
        if isinstance(rpcserver, xmlrpclib.ServerProxy):
            self._server = rpcserver
        else:
            raise TypeError('given server handle is not a valid XML-RPC '
                    'server handle.')

        if isinstance(hash_id, str):
            self.hash_id = hash_id
            self._validate_hash_id()
        else:
            raise TypeError('given hash ID must be a string.')

    def __repr__(self):
        return '<TorrentEntry({!r}, {!r})>'.format(self._server, self.hash_id)

    def __str__(self):
        return 'Server: {!r}, hash ID: {}, file: {}'.format(
                self._server,
                self.hash_id,
                self.base_filename)

    @staticmethod
    def validate_hash_id(hash_id, rpcserver=None):
        """Check for valid hash ID formatting, and optionally existence in
        rTorrent session.

        Args:
            hash_id: string to validate.
            rpcserver: optional XML-RPC server for rTorrent session to check
                existence of hash ID.

        Returns:
            True.

        Raises:
            ValueError on invalid string form.
            KeyError if hash ID missing in rTorrent session."""
        try:
            int(hash_id, 16)
        except ValueError as msg:
            raise ValueError(
                    'hash ID "{}"\n'
                    '   {}\n'
                    'Characters allowed in hexadecimal string: '
                    '[0-9a-fA-F]'.format(hash_id, msg))

        if not len(hash_id) == 40:
            raise ValueError(
                    'hash ID "{}": hash ID must be 40 character hexadecimal '
                    'string'.format(hash_id))

        if rpcserver is not None:
            try:
                rpcserver.d.hash(hash_id)
            except xmlrpclib.Fault as msg:
                if msg.faultCode == -501:
                    raise KeyError(hash_id)
                else:
                    raise

        return True

    def _validate_hash_id(self):
        self.validate_hash_id(self.hash_id, self._server)

    @property
    def base_filename(self):
        """File name of torrent entry."""
        return self._server.d.base_filename(self.hash_id)

    @property
    def multi_file(self):
        """Boolean denoting the multi file property."""
        return self._server.d.is_multi_file(self.hash_id) == 1

    @property
    def open(self):
        """Boolean representing open state."""
        return self._server.d.is_open(self.hash_id) == 1
    @open.setter
    def open(self, state):
        if state:
            self._server.d.open(self.hash_id)
        else:
            self._server.d.close(self.hash_id)

    @property
    def active(self):
        """Boolean representing active state."""
        return self._server.d.is_active(self.hash_id) == 1
    @active.setter
    def active(self, state):
        if state:
            self._server.d.start(self.hash_id)
        else:
            self._server.d.stop(self.hash_id)

    @property
    def full_path(self):
        """Full path of torrent entry material."""
        return self._server.d.base_path(self.hash_id)

    @property
    def directory(self):
        """'directory' attribute."""
        return self._server.d.directory(self.hash_id)
    @directory.setter
    def directory(self, path):
        self._server.d.directory.set(self.hash_id, path)


    @property
    def directory_base(self):
        """'directory_base' attribute."""
        return self._server.d.directory_base(self.hash_id)
    @directory_base.setter
    def directory_base(self, path):
        self._server.d.directory_base.set(self.hash_id, path)

    def move(self, path):
        """Set new torrent path (no moving of physical files).

        Args:
            path: New path to set.

        Returns:
            Nothing.
        """
        pre_active = self.active
        pre_open = self.open

        if pre_active:
            self.active = False
        if pre_open:
            self.open = False

        self.directory = self.directory_base = path

        # Need to open even if it was closed to refresh directory info.
        self.open = True
        if pre_active:
            self.active = True
        elif not pre_open:
            self.open = False
