import socket
import sys
from typing import List

INTERACTABLE_TAGS = ["link", "button"]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "hypy://localhost/index.hypy"
    url = URL(path)
    document = Document(url)
    document.parse(url, url.request())
    for script in document.scripts:
        exec(script)
    print(document.root)
    while True:
        cmd = input("> ")
        if not cmd:
            break
        if cmd.startswith("click "):
            document.click(int(cmd.removeprefix("click ")))
        for script in document.scripts:
            exec(script)
        print(document.root)


class URL:
    def __init__(self, url: str, relative_to: URL | None = None) -> None:
        if "://" in url:
            self.scheme, url = url.split("://", 1)
        elif relative_to:
            self.scheme = relative_to.scheme
        if "/" not in url:
            url = url + "/"
        if url.startswith("/") and relative_to:
            self.host = relative_to.host
            self.path = url
        else:
            self.host, url = url.split("/", 1)
            self.path = "/" + url

    def request(self) -> str:
        sock = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        sock.connect((self.host, 8155))
        request = "GET {} HTTP/1.0\r\n".format(self.path)
        request += "Host: {}\r\n".format(self.host)
        request += "\r\n"
        sock.send(request.encode("utf8"))
        response = sock.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
        content = response.read()
        sock.close()
        return content


class Document:
    def __init__(self, base_url: URL) -> None:
        self.root = Element(self)
        self.base_url = base_url
        self.scripts: List[str] = []
        self.id_map = {}
        self.interactable_index = 0
        self.interactables = []
        self.element_stack = [self.root]

    def parse(self, base_url: URL, content: str) -> None:
        self.root = Element(self)
        self.base_url = base_url
        self.scripts = []
        self.id_map = {}
        self.interactable_index = 0
        self.interactables = []
        self.element_stack = [self.root]
        last_text_node: TextElement | None = None

        for line in content.splitlines():
            if line.startswith("~~< "):
                script_url = URL(line.removeprefix("~~< "))
                self.scripts.append(script_url.request())
            elif line.strip():
                indent = (len(line) - len(line.lstrip(" "))) // 4
                new_element = element_from_line(self, line.strip())

                self.element_stack = self.element_stack[0 : indent + 1]
                if isinstance(new_element, Element):
                    self.element_stack[-1].children.append(new_element)
                    self.element_stack.append(new_element)
                    self.register(new_element)
                    last_text_node = None
                elif isinstance(new_element, TextElement) and last_text_node:
                    last_text_node.text += new_element.text
                elif isinstance(new_element, TextElement):
                    last_text_node = new_element
                    self.element_stack[-1].children.append(new_element)
            else:
                last_text_node = None

    def register(self, element: Element) -> None:
        if "id" in element.attributes:
            self.id_map[element.attributes["id"]] = element
        if element.tag in INTERACTABLE_TAGS:
            element.attributes["interact_index"] = self.interactable_index
            self.interactable_index += 1
            self.interactables.append(element)

    def click(self, index: int) -> None:
        if index < 0 or index >= len(self.interactables):
            return
        element = self.interactables[index]
        element.click()

    def navigate(self, url_str: str):
        url = URL(url_str, self.base_url)
        self.parse(url, url.request())

    def __repr__(self) -> str:
        return "\n".join([child.__repr__() for child in self.root.children])

    def getById(self, target: str) -> Element:
        return self.id_map[target]


def element_from_line(document: Document, line: str) -> Element | TextElement:
    if line.startswith("@"):
        line = line.lstrip("@")
        tag, attribute_str = line.removesuffix(":").split(" ", 1)
        new_element = Element(document, tag, attribute_str)
        return new_element
    else:
        return TextElement(line.strip())


class Element:
    def __init__(self, document: Document, tag="root", attribute_str="") -> None:
        self.document = document
        self.tag = tag
        self.children: List[Element | TextElement] = []
        self.attributes = {}
        for pair in attribute_str.split(" "):
            pair_tuple = pair.split("=", 1)
            match len(pair_tuple):
                case 1:
                    self.attributes[pair_tuple[0]] = True
                case 2:
                    self.attributes[pair_tuple[0]] = pair_tuple[1]

    def click(self):
        if self.tag not in INTERACTABLE_TAGS:
            return
        if self.tag == "link" and "url" in self.attributes:
            self.document.navigate(self.attributes["url"])

    def __repr__(self) -> str:
        repr_lines = []
        if self.tag == "root":
            repr_lines.extend(["root"])
        else:
            repr_lines.extend(
                [
                    self.tag
                    + " "
                    + ",".join(
                        [
                            key + ":" + str(value)
                            for key, value in self.attributes.items()
                        ]
                    )
                ]
            )
        for child in self.children:
            child_lines = child.__repr__().splitlines()
            child_lines = map(lambda line: "|   " + line, child_lines)
            repr_lines.extend(child_lines)
        if self.children:
            repr_lines.extend(["|_______"])
        return "\n".join(repr_lines)


class TextElement:
    def __init__(self, content: str) -> None:
        self.text = content.rstrip("|")

    def __repr__(self) -> str:
        return "text: " + self.text


document = None

if __name__ == "__main__":
    main()
