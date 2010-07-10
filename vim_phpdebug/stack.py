

class StackMan:
    def __init__(self):
        self.stack = []

    def update(self, node):
        stack = node.getElementsByTagName('stack')
        self.stack = list(map(item.getAttribute, ('level', 'where', 'filename', 'lineno')) for item in stack)

# vim: et sw=4 sts=4
