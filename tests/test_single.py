from single import singleton_decorator, Singleton



def test_single_decorator():
    @singleton_decorator
    class A:
        def __init__(self):
            self.a = 10

    @singleton_decorator
    class B:
        def __init__(self):
            self.b = 10

    a = A()
    b = A()
    assert a is b

    c = B()
    assert a is not c


def test_singleton_class():
    class A(Singleton):
        def __init__(self):
            self.a = 10

    class B(Singleton):
        def __init__(self):
            self.b = 10

    a = A()
    b = A()
    assert a is b

    c = B()
    assert a is not c