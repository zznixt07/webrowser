import ssl
import socket
from tkinter.constants import W
from typing import Dict, List, Literal, Optional, TextIO, Tuple
import tkinter

HTTP_VER: str = '1.1'
SUPPORTED_URLS: Tuple[str, ...] = (
    'http',
    'https',
    'file',
)  # keep tuple for typing.Literal
Scheme = Literal[SUPPORTED_URLS]
CTX: ssl.SSLContext = ssl.create_default_context()


def url_parse(url: str) -> Tuple[Scheme, int, str, str]:
    scheme: Scheme
    port: int
    host: str
    path: str
    scheme, url = url.split('://', 1)
    assert scheme in SUPPORTED_URLS, f'Unknown scheme {scheme}'
    splitted: List[str] = url.split('/', 1)
    host_and_port: List[str] = splitted[0].split(':', 1)
    if len(host_and_port) == 2:
        # say if splitted=['example.org:666', 'path.html'], remove port from 0th index
        splitted[0] = host_and_port[0]
        port = int(host_and_port[1])
    else:
        port = 80 if scheme == 'http' else 443
    if len(splitted) == 1:
        host = splitted[0]
        path = ''
    else:
        host, path = splitted
    if scheme == 'file':
        port = -1
    else:
        path = '/' + path
    return scheme, port, host, path


def request(
    url: str, headers: Optional[Dict[str, str]] = None
) -> Tuple[Dict[str, str], str]:
    scheme: Scheme
    port: int
    host: str
    path: str
    scheme, port, host, path = url_parse(url)
    if headers is None:
        headers = {}
    headers.update(
        {'Host': host, 'Connection': 'close', 'User-Agent': 'pybrowser, like Chrome'}
    )
    sock: socket.socket
    response: TextIO
    with socket.socket(
        family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP
    ) as sock:
        sock.connect((host, port))
        reqs: str = (
            f'GET {path} HTTP/{HTTP_VER}\r\n'
            + '\r\n'.join([f'{k}: {v}' for k, v in headers.items()])
            + '\r\n'
            + '\r\n'
        )
        if scheme == 'https':
            with CTX.wrap_socket(sock, server_hostname=host) as ssock:
                ssock.sendall(reqs.encode('utf-8'))
                response = ssock.makefile('r', encoding='UTF-8', newline='\r\n')
        else:
            sock.sendall(reqs.encode('utf-8'))
            response = sock.makefile('r', encoding='UTF-8', newline='\r\n')

    status_line: str = response.readline()
    version: str
    status: str
    explanation: str
    version, status, explanation = status_line.split(' ', 2)
    assert status == '200', f'{status}: {explanation}'
    resp_headers: Dict[str, str] = {}
    while True:
        line: str = response.readline()
        if line == '\r\n':
            break
        header: str
        value: str
        header, value = line.split(':', 1)
        resp_headers[header.lower()] = value.strip()

    body: str = response.read()
    return resp_headers, body


def lex(body: str) -> str:
    text: str = ""
    in_angle: bool = False
    c: str
    for c in body:
        if c == '<':
            in_angle = True
        elif c == '>':
            in_angle = False
        elif not in_angle:
            text += c
    return text


class Browser:

    width: int = 1000
    height: int = 800

    def __init__(self):
        self.window: tkinter.Tk = tkinter.Tk()
        self.canvas: tkinter.Canvas = tkinter.Canvas(
            self.window, width=self.width, height=self.height
        )
        self.canvas.pack()

    def load(self, url: str) -> None:
        self.canvas.create_rectangle(10, 20, 400, 500)
        self.canvas.create_oval(100, 100, 150, 150)
        headers: Dict[str, str]
        body: str
        headers, body = request(url)
        text: str = lex(body)
        max_line_length: int = 79
        hstep: int = 8
        vstep: int = 19
        cursor_x: int = hstep
        cursor_y: int = vstep
        i: int = 0
        for c in text:
            self.canvas.create_text(cursor_x, cursor_y, text=c)
            if i < max_line_length:
                i += 1
                cursor_x += hstep
            else:
                i = 0
                cursor_x = hstep
                cursor_y += vstep
            # print(i, end=' ')


if __name__ == '__main__':
    url: str = 'https://example.org'
    # url = 'https://www.zggdwx.com/xiyou/1.html'
    browser: Browser = Browser()
    browser.load(url)
    tkinter.mainloop()
