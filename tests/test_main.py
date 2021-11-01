from src.bowser.main import url_parse


def test_url_parse_scheme():
    index: int = 0
    assert url_parse('http://example.org')[index] == 'http'
    assert url_parse('https://example.org')[index] == 'https'
    assert (
        url_parse(
            'file:///C:\\Users\\zznixt\\OneDrive\\innit_perhaps\\2nd time\\browser-engineering\\bowser\\home.html'
        )[index]
        == 'file'
    )
    # assert url_parse('data://example.org')[index] == 'data'


def test_url_parse_port():
    index: int = 1
    assert url_parse('http://example.org')[index] == 80
    assert url_parse('https://example.org')[index] == 443
    assert url_parse('https://api.example.org:5645')[index] == 5645
    assert (
        url_parse(
            'file:///C:\\Users\\zznixt\\OneDrive\\innit_perhaps\\2nd time\\browser-engineering\\bowser\\home.html'
        )[index]
        == -1
    )


def test_url_parse_host():
    index: int = 2
    assert url_parse('http://example.org')[index] == 'example.org'
    assert url_parse('https://example.org')[index] == 'example.org'
    assert url_parse('https://api.example.org')[index] == 'api.example.org'
    assert url_parse('https://example.org/home.html')[index] == 'example.org'
    assert (
        url_parse(
            'file:///C:\\Users\\zznixt\\OneDrive\\innit_perhaps\\2nd time\\browser-engineering\\bowser\\home.html'
        )[index]
        == ''
    )


def test_url_parse_path():
    index: int = -1
    assert url_parse('http://example.org')[index] == '/'
    assert url_parse('https://api.example.org')[index] == '/'
    assert url_parse('https://example.org/home.html')[index] == '/home.html'
    assert (
        url_parse('https://example.org/home.html?k1=v#i54')[index]
        == '/home.html?k1=v#i54'
    )
    assert (
        url_parse(
            'file:///C:\\Users\\zznixt\\OneDrive\\innit_perhaps\\2nd time\\browser-engineering\\bowser\\home.html'
        )[index]
        == 'C:\\Users\\zznixt\\OneDrive\\innit_perhaps\\2nd time\\browser-engineering\\bowser\\home.html'
    )


def test_url_parse():
    assert url_parse('http://example.org') == ('http', 80, 'example.org', '/')
    assert url_parse('https://example.org') == ('https', 443, 'example.org', '/')
    assert url_parse('https://api.example.org') == (
        'https',
        443,
        'api.example.org',
        '/',
    )
    assert url_parse('https://example.org/page.html?k=v#id1') == (
        'https',
        443,
        'example.org',
        '/page.html?k=v#id1',
    )
    assert url_parse(
        'file:///C:\\Users\\zznixt\\OneDrive\\innit_perhaps\\2nd time\\browser-engineering\\bowser\\home.html'
    ) == (
        'file',
        -1,
        '',
        'C:\\Users\\zznixt\\OneDrive\\innit_perhaps\\2nd time\\browser-engineering\\bowser\\home.html',
    )
