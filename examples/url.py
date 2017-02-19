from collections import namedtuple, OrderedDict
from ipaddress import IPv4Address, IPv6Address

from parsita import *

# This covers a typical URL schema, not the crazy one specified by https://tools.ietf.org/html/rfc3986
# In particular, this doesn't handle Unicode at the moment

UserInfo = namedtuple('Userinfo', ['username', 'password'])
DomainName = namedtuple('DomainName', ['domains'])
Url = namedtuple('Uri', ['scheme', 'user_info', 'host', 'port', 'path', 'query', 'fragment'])


class TypicalUrlParsers(TextParsers, whitespace=None):
    encoded = '%' >> reg(r'[0-9A-F]{2}') > (lambda x: chr(int(x, 16)))

    scheme = reg(r'[A-Za-z][-+.A-Za-z0-9]*') > str.lower

    username = reg(r'[A-Za-z][-_+A-Za-z0-9]*([.][-_+A-Za-z0-9]+)*') > str.lower
    password = rep(reg(r'[-_.+A-Za-z0-9]+') | encoded) > ''.join
    userinfo = username << ':' & password > (lambda x: UserInfo(*x))

    domain_name = rep1sep(reg('[A-Za-z0-9]+([-][A-Za-z0-9])*') > str.lower, '.') << opt('.') > (
        lambda x: DomainName(list(reversed(x))))
    ipv4_address = reg(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}') > IPv4Address
    ipv6_address = reg(r'\[([A-Fa-f0-9]{1,4}(:[A-Fa-f0-9]{1,4}){1,7})\]'
                       r'|\[(([A-Fa-f0-9]{1,4}:){1,7})(:[A-Fa-f0-9]{1,4}){1,6}\]'
                       r'|\[:(:[A-Fa-f0-9]{1,4}){0,7}\]'
                       r'|\[([A-Fa-f0-9]{1,4}:){0,7}:\]') > IPv6Address
    host = ipv4_address | ipv6_address | domain_name

    port = ':' >> reg(r'[0-9]+') > int

    path = rep('/' >> (reg(r'[-._~A-Za-z0-9]*') | encoded))

    query_as_is = reg(r'[*-._A-Za-z0-9]+')
    query_space = lit('+') > (lambda _: ' ')
    query_string = rep1(query_as_is | query_space | encoded) > ''.join
    query = '?' >> repsep(query_string << '=' & query_string, '&') > OrderedDict

    fragment = '#' >> reg(r'[-._~/?A-Za-z0-9]*')

    url = scheme << '://' & opt(userinfo << '@') & host & opt(port) & path & opt(query) & opt(fragment) > (
        lambda x: Url(*x))


if __name__ == '__main__':
    strings = [
        'http://drhagen.com/blog/the-missing-11th-of-the-month/',
        'git://drhagen:password1@github.com/drhagen/parsita.git',
        'https://pypi.python.org/pypi?%3Aaction=search&term=parser+combinator&submit=search',
        'http://128.30.2.155/',
        'https://docs.python.org/3/reference/expressions.html#operator-precedence',
    ]

    for string in strings:
        print('source: {}\nvalue: {}'.format(string, TypicalUrlParsers.url.parse(string)))
