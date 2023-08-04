class BaserowRuntimeFormulaArgumentType:
    def test(self, value):
        return True

    def parse(self, value):
        return value


class NumberBaserowRuntimeFormulaArgumentType(BaserowRuntimeFormulaArgumentType):
    def test(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def parse(self, value):
        return float(value)


class TextBaserowRuntimeFormulaArgumentType(BaserowRuntimeFormulaArgumentType):
    def test(self, value):
        try:
            str(value)
            return True
        except TypeError:
            return False

    def parse(self, value):
        return str(value)
