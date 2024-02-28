def plain():
    return "ORIGINAL"


def generic(a, *args, b="b", **kwargs):
    return a + "ORIGINAL" + b + str((args, kwargs))


def pair(somefn):
    def ret(*_, **__):
        return somefn(*_, **__) + somefn(*_, **__)

    return ret


pairgeneric = pair(generic)

async def asyncplain():
    return "ORIGINAL"
