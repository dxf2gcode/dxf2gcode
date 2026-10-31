"""Source messages carrying translation context without importing a UI toolkit."""


class SourceMessage(str):
    def __new__(cls, source, context="", args=()):
        value = super().__new__(cls, source % args if args else source)
        value.source, value.context, value.args = source, context, args
        return value

    def __mod__(self, args):
        return SourceMessage(self.source, self.context,
                             args if isinstance(args, tuple) else (args,))

    def __getnewargs_ex__(self):
        return (self.source, self.context, self.args), {}


def QT_TRANSLATE_NOOP(context, text):
    return SourceMessage(text, context)
