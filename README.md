rtmovedir
=========
Change paths of [rTorrent](http://libtorrent.rakshasa.no/) entries via its XML-RPC interface based on regular expression matching and substitution.

Requirements
------------
* rTorrent configured with XML-RPC — [official instructions](http://libtorrent.rakshasa.no/wiki/RTorrentXMLRPCGuide)
* Python 2 (not too archaic)

Usage
-----
    usage: rtmovedir.py [-h] [-s SEARCH] [--hashlist HASH [HASH ...]] [-x]
                        [--silent] [--no-colors] [--debug]
                        url match replace
    
    Change directories of rTorrent downloads via regexp replacement.
    
    positional arguments:
      url                   XML-RPC URL
      match                 regexp match pattern
      replace               regexp replace pattern
    
    optional arguments:
      -h, --help            show this help message and exit
      -s SEARCH, --search SEARCH
                            update paths only for items matching this pattern
      --hashlist HASH [HASH ...]
                            hash IDs to consider
      -x, --execute         execute query
      --silent              disable standard output
      --no-colors           disable color output
      --debug               enable debug messages

Examples
--------
Add `-x` to actually execute commands; without this switch only dry runs are performed.

Using `http://localhost/RPC2` as placeholder XML-RPC server path.

### Globally change all `/media/foo/…` paths to `/media/bar/…`
    rtmovedir.py http://localhost/RPC2 /media/foo /media/bar

### Change all `/media/foo/…` paths to `/media/bar/…` where the path contains `baz`
    rtmovedir.py -s baz http://localhost/RPC2 /media/foo /media/bar

### Change `/media/foo/…` to `/media/bar/…` in paths for certain hash IDs
    rtmovedir.py --hashlist HASH1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA HASH2BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB -- http://localhost/RPC2 /media/foo /media/bar

Note the `--` construct that is needed to stop `--hashlist` from consuming arguments because of [some](http://bugs.python.org/issue9182) [quirks](http://bugs.python.org/issue9338) with the Python standard library. Compare with:

    rtmovedir.py --hashlist HASH1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA HASH2BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB http://localhost/RPC2 /media/foo /media/bar
    usage: rtmovedir.py [-h] [-s SEARCH] [--hashlist HASH [HASH ...]] [-x]
                        [--silent] [--no-colors] [--debug]
                        url match replace
    rtmovedir.py: error: too few arguments

A standard library enhancement to allocate mandatory positional arguments would be nice and backwards compatible, so perhaps this will change in the future (or at least become clearly documented).

### Change the leading path to `/media/foo` for all torrents whose names match `bar` or `baz`
    rtmovedir.py -s 'ba[rz]' http://localhost/RPC2 '.*/' '/media/foo/'

…and more expected regular expression functionality.

Upstream
--------
The project lives at <https://github.com/dandersson/rtmovedir>.
