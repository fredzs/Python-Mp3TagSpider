#


class Statistic(object):
    def __init__(self):
        self._search_result = {'DONE': int(0), 'CHECK': int(0), 'NOT_FOUND': int(0), 'UPDATE': int(0)}

    def get_search_result(self, key):
        return self._search_result.get(key)

    def set_search_result(self, key):
        count = self._search_result.get(key)
        if count is None:
            self._search_result[key] = 1
        else:
            self._search_result[key] = self._search_result.get(key) + 1

    def get_sum(self):
        sum = 0
        for key in self._search_result.keys():
            sum += self.get_search_result(key)
        return sum
