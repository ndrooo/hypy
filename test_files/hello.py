hello_element = document.getById("hello")
hello_element.children = [TextElement("Hello HyperPy!")]
button_element = document.getById("increment")
counter_element = document.getById("counter")
counter = 0


def increment_counter():
    counter += 1
    counter_element.children = [TextElement(str(counter))]


button_element.on_click(increment_counter)
