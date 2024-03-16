class a:
    x = "foo"

    @staticmethod
    def f():
        return a.x


class a(a):
    x = "bruh"


print(a.f())
