import ssl
import socket
import logging
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

HSTEP: int = 8
VSTEP: int = 19
logger = logging.getLogger('webrowser')


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


def layout(text: str) -> List[Tuple[int, int, str]]:
    max_line_length: int = Browser.width - HSTEP
    cursor_x: int = HSTEP
    cursor_y: int = VSTEP
    display_list: List[Tuple[int, int, str]] = []
    c: str
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= max_line_length:
            cursor_x = HSTEP
            cursor_y += VSTEP
    return display_list


class Browser:

    width: int = 1300
    height: int = 700  # do not exceed display height else scrolling wont work
    scroll_step: int = 30

    def __init__(self):
        logger.debug('browser height: %d', self.height)
        self.window: tkinter.Tk = tkinter.Tk()
        self.canvas: tkinter.Canvas = tkinter.Canvas(
            self.window, width=self.width, height=self.height
        )
        self.canvas.pack()
        self.scroll: int = 0
        self.last_line_y_coord: int = self.height
        self.display_list: List[Tuple[int, int, str]] = []
        self.window.bind("<MouseWheel>", self.scroll_towards)

    def load(self, url: str) -> None:
        headers: Dict[str, str]
        body: str
        headers, body = request(url)
        text: str = lex(body)
        self.display_list = layout(text)
        logger.debug(
            'display_list[0] = %s display_list[-1] = %s',
            self.display_list[0],
            self.display_list[-1],
        )
        self.draw(self.display_list)

    def draw(self, display_list: List[Tuple[int, int, str]]):
        x: int
        y: int = (
            self.last_line_y_coord + self.scroll
        )  # to revert value of self.last_line_y_coord on empty display_list
        c: str
        for x, y, c in display_list:
            scrolled_y: int = y - self.scroll
            if scrolled_y < VSTEP:
                continue
            if scrolled_y > self.height - VSTEP:
                continue
            self.canvas.create_text(x, scrolled_y, text=c)
        self.last_line_y_coord = y - self.scroll

    def scroll_towards(self, e: tkinter.Event):
        logger.debug('last_line_y_coord = %d', self.last_line_y_coord)
        if self.scroll < 0:  # stop scrolling past the top
            logger.debug('not scrolling. SOL')
            self.scroll = 0
            return
        if e.delta == 0:
            return
        if e.delta > 0:
            # scroll up
            logger.debug('scrolling up..')
            self.scroll -= self.scroll_step
        else:
            # scroll down
            # stop scrolling past the bottom
            if self.last_line_y_coord <= self.height - VSTEP:
                logger.debug('height - vstep = %d', self.height - VSTEP)
                logger.debug('not scrolling. EOL')
                return
            logger.debug('scrolling down..')
            self.scroll += self.scroll_step
        self.canvas.delete('all')
        self.draw(self.display_list)


if __name__ == '__main__':
    stream_handler = logging.StreamHandler()
    stream_handler.formatter = logging.Formatter()
    stream_handler.setLevel(10)
    logger.setLevel(10)
    logger.addHandler(stream_handler)
    logging.disable()

    url: str = 'https://example.org'
    url = 'https://danluu.com/math-bias/'
    browser: Browser = Browser()
    browser.load(url)
    tkinter.mainloop()
